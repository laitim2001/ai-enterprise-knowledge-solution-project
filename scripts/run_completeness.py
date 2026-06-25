"""W96 F3 — answer-completeness driver: run GT queries through the live /query pipeline
and score nugget coverage (乙類 over-summarisation detector).

For each query in an eval-set (any set with ``metadata.kb_id`` + ``queries[].query_text``
— no ``ground_truth`` needed; nuggets are auto-extracted), POST the FULL ``/query``
pipeline, then:
  1. take the answer + the retrieved context (``retrieved_chunks[].chunk_text`` — the
     chunks the synthesiser actually saw, so dropping a whole chunk shows up here);
  2. judge (gpt-5.4-mini) extracts query-conditioned nuggets from that context and marks
     which survive into the answer;
  3. report answer_coverage = covered/total + the MISSED nuggets per query + aggregate.

Why retrieved-context as the denominator (not the answer's own citations): a dropped
chunk would not be cited, so a citation denominator would hide the drop. The retrieved
context is what the synthesiser HAD — coverage over it isolates the synthesis layer
(CRUX "retrieved but not answered"). Per source-fidelity research; see W96 plan.

CAVEAT: this metric is a reliable RUN/SYSTEM-level A/B signal but UNRELIABLE per-answer
— compare bands across configs / multiple runs, never debug a single answer by it.

Prerequisites (F4 live run):
- backend up (backend/.venv/Scripts/python.exe -m api.server) — START WITH
  HYBRID_USE_SEMANTIC_RANKER=false to dodge the Free-tier semantic 402 (memory).
- azurite + the target index populated; Azure OpenAI creds in .env (judge).
- mock auth: Bearer dev-token.

Usage (from project root):
    backend/.venv/Scripts/python.exe -m scripts.run_completeness \
        --eval-set docs/eval-set-image-recall-ar.yaml \
        --base-url http://localhost:8000 --out reports/completeness_ar.yaml
"""

from __future__ import annotations

# OS trust store for corp-proxy TLS — must run before httpx import.
import truststore

truststore.inject_into_ssl()

import argparse  # noqa: E402
import asyncio  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

import httpx  # noqa: E402
import yaml  # noqa: E402

from eval.completeness_coverage import (  # noqa: E402
    CompletenessQueryResult,
    aggregate,
    compute_metrics,
    report_to_dict,
)
from eval.completeness_judge import make_completeness_judge  # noqa: E402
from storage.settings import get_settings  # noqa: E402

_DEFAULT_EVAL_SET = Path("docs/eval-set-image-recall-ar.yaml")
_DEFAULT_BASE_URL = "http://localhost:8000"
_DEFAULT_TOKEN = "dev-token"  # mock auth (per memory)
# Generous cap on the concatenated retrieved context fed to the extract judge. The
# synthesiser context is rerank-bounded so this rarely bites; it just guards cost.
_MAX_CONTEXT_CHARS = 24000


def _default_out(eval_set_path: Path) -> Path:
    return Path("reports") / f"{eval_set_path.stem}_completeness.yaml"


def _build_context(retrieved_chunks: list[dict]) -> str:
    """Concatenate retrieved chunk text (the synthesiser's input) into one context."""
    parts: list[str] = []
    total = 0
    for c in retrieved_chunks:
        text = str(c.get("chunk_text") or "").strip()
        if not text:
            continue
        title = str(c.get("chunk_title") or "").strip()
        block = f"[{title}]\n{text}" if title else text
        parts.append(block)
        total += len(block)
        if total >= _MAX_CONTEXT_CHARS:
            break
    return "\n\n---\n\n".join(parts)


async def _amain(eval_set_path: Path, base_url: str, token: str, out_path: Path) -> int:
    if not eval_set_path.is_file():
        print(f"eval-set not found: {eval_set_path}", file=sys.stderr)
        return 1
    eval_set = yaml.safe_load(eval_set_path.read_text(encoding="utf-8"))
    meta = eval_set.get("metadata", {})
    kb_id = str(meta.get("kb_id", ""))
    queries = eval_set.get("queries", [])
    if not kb_id or not queries:
        print("eval-set missing metadata.kb_id or queries", file=sys.stderr)
        return 1

    judge = make_completeness_judge(get_settings())
    if judge is None:
        print(
            "no Azure OpenAI credential (AZURE_OPENAI_API_KEY) — completeness judge "
            "unavailable; cannot score. Set creds in .env and retry.",
            file=sys.stderr,
        )
        return 1

    per_query: list[CompletenessQueryResult] = []
    async with httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=300.0,  # full pipeline + 2 judge calls — loaded machine can be slow
    ) as client:
        for q in queries:
            qid = str(q.get("query_id", ""))
            qtext = str(q.get("query_text", ""))
            q_kb_id = str(q.get("kb_id") or kb_id)

            error: str | None = None
            try:
                resp = await client.post(
                    "/query", json={"query": qtext, "kb_id": q_kb_id}
                )
                resp.raise_for_status()
                body = resp.json()
            except httpx.HTTPStatusError as exc:
                error = f"HTTP {exc.response.status_code}: {exc.response.text[:160]}"
                body = {}
            except Exception as exc:  # noqa: BLE001 — surface per query
                error = f"{type(exc).__name__}: {exc}"
                body = {}

            judgements = None
            if error is None:
                context = _build_context(body.get("retrieved_chunks", []) or [])
                answer = str(body.get("answer") or "")
                judgements = await judge(qtext, context, answer)
                if judgements is None:
                    error = "judge returned no result (extract/presence failed)"

            metrics = compute_metrics(judgements or [])
            if error is not None:
                print(f"  {qid}: ERROR {error}")
            else:
                print(
                    f"  {qid}: coverage={metrics.answer_coverage:.2f} "
                    f"(covered {metrics.covered_nuggets}/{metrics.total_nuggets}; "
                    f"missed {len(metrics.missed)})"
                )
                for m in metrics.missed:
                    print(f"        - MISSED: {m}")
            per_query.append(
                CompletenessQueryResult(
                    query_id=qid,
                    query_text=qtext,
                    metrics=metrics,
                    error=error,
                )
            )

    report = aggregate(eval_set_path.name, kb_id, per_query)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        yaml.safe_dump(report_to_dict(report), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"\nCompleteness report written: {out_path}")
    print(
        f"mean answer-coverage = {report.mean_answer_coverage:.3f} | "
        f"scored {report.scored_queries}/{report.total_queries}",
    )
    print("CAVEAT: run/system-level A/B signal only - per-answer unreliable.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", type=Path, default=_DEFAULT_EVAL_SET)
    parser.add_argument("--base-url", default=_DEFAULT_BASE_URL)
    parser.add_argument("--token", default=_DEFAULT_TOKEN)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    out_path = args.out if args.out is not None else _default_out(args.eval_set)
    return asyncio.run(_amain(args.eval_set, args.base_url, args.token, out_path))


if __name__ == "__main__":
    raise SystemExit(main())
