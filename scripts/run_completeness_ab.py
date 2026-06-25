"""W96 DD-15 (F7) — completeness paired A/B harness with fixed nuggets + K-run averaging.

F4 proved per-answer coverage is noisy (synthesiser + judge stochasticity), so the bare
`run_completeness.py` is a per-answer-unreliable signal. This harness makes it a usable
config A/B gate by attacking the three variance sources:
  1. FIXED nugget set — extract the query-conditioned nuggets ONCE (``--build-nuggets``)
     and reuse them for every arm/run (research-backed: AutoNuggetizer "fix nugget
     creation, automate only assignment"). Removes nugget-creation variance.
  2. K-RUN averaging — generate the answer K times per arm and average coverage
     (``--runs K``). Smooths synthesiser + presence-judge noise.
  3. PAIRED comparison — score config A and config B on the SAME query + SAME fixed
     nuggets and read the per-query delta (B-A). Query-level / nugget-level offset
     cancels, so the delta sign is stable even when absolute coverage is noisy. Mirrors
     the shared-frozen-set design of ``controlled_comparison.py``.

Retrieval is deterministic on a static index (BM25 + vector + Cohere rerank), so both
arms hit the same retrieved context; only the synthesis config (``--config-a/-b``, a
JSON of QueryRequest overrides — default ``llm_model`` gpt-5.4-mini vs gpt-5.5) differs.
No direct synthesiser call / no new endpoint.

Usage (from project root):
    # 1. build the fixed nugget set once (uses default config to retrieve context)
    backend/.venv/Scripts/python.exe -m scripts.run_completeness_ab \
        --eval-set docs/eval-set-completeness-w96.yaml --build-nuggets
    # 2. paired A/B (default: gpt-5.4-mini vs gpt-5.5), K=3 runs/arm
    backend/.venv/Scripts/python.exe -m scripts.run_completeness_ab \
        --eval-set docs/eval-set-completeness-w96.yaml --runs 3 \
        --out reports/completeness_w96_ab.yaml

Prereqs: backend up (HYBRID_USE_SEMANTIC_RANKER=false to dodge Free-tier 402), azurite +
index populated, Azure OpenAI creds in .env, mock auth Bearer dev-token.
"""

from __future__ import annotations

# OS trust store for corp-proxy TLS — must run before httpx import.
import truststore

truststore.inject_into_ssl()

import argparse  # noqa: E402
import asyncio  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# Windows consoles default to cp1252 → never crash the whole run on a stray unicode
# char in a print (the run does real LLM work we must not lose). ASCII symbols below
# are the primary guard; this is the backstop.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

import httpx  # noqa: E402
import yaml  # noqa: E402

from eval.completeness_coverage import (  # noqa: E402
    NuggetJudgement,
    aggregate_paired,
    build_paired_query_result,
    compute_metrics,
    paired_report_to_dict,
)
from eval.completeness_judge import (  # noqa: E402
    make_nugget_extractor,
    make_presence_judge,
)
from storage.settings import get_settings  # noqa: E402

_DEFAULT_EVAL_SET = Path("docs/eval-set-completeness-w96.yaml")
_DEFAULT_BASE_URL = "http://localhost:8000"
_DEFAULT_TOKEN = "dev-token"
_MAX_CONTEXT_CHARS = 24000
# Default A/B lever: synthesiser model (QueryRequest field — per-request, no config mutation).
_DEFAULT_CONFIG_A = '{"llm_model": "gpt-5.4-mini"}'
_DEFAULT_CONFIG_B = '{"llm_model": "gpt-5.5"}'


def _nuggets_path(eval_set_path: Path) -> Path:
    return eval_set_path.with_suffix(".nuggets.yaml")


def _build_context(retrieved_chunks: list[dict]) -> str:
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


async def _query(
    client: httpx.AsyncClient, query: str, kb_id: str, overrides: dict
) -> tuple[dict, str | None]:
    """POST /query (base request + arm overrides). Returns (body, error)."""
    try:
        resp = await client.post(
            "/query", json={"query": query, "kb_id": kb_id, **overrides}
        )
        resp.raise_for_status()
        return resp.json(), None
    except httpx.HTTPStatusError as exc:
        return {}, f"HTTP {exc.response.status_code}: {exc.response.text[:160]}"
    except Exception as exc:  # noqa: BLE001 — surface per query
        return {}, f"{type(exc).__name__}: {exc}"


def _load_queries(eval_set_path: Path) -> tuple[str, list[dict]]:
    eval_set = yaml.safe_load(eval_set_path.read_text(encoding="utf-8"))
    meta = eval_set.get("metadata", {})
    return str(meta.get("kb_id", "")), eval_set.get("queries", [])


async def _build_nuggets(eval_set_path: Path, base_url: str, token: str) -> int:
    """Extract + persist a FIXED nugget set per query (one /query at default config)."""
    kb_id, queries = _load_queries(eval_set_path)
    if not kb_id or not queries:
        print("eval-set missing metadata.kb_id or queries", file=sys.stderr)
        return 1
    extractor = make_nugget_extractor(get_settings())
    if extractor is None:
        print("no Azure OpenAI credential — cannot extract nuggets", file=sys.stderr)
        return 1

    out_queries: list[dict] = []
    async with httpx.AsyncClient(
        base_url=base_url, headers={"Authorization": f"Bearer {token}"}, timeout=300.0
    ) as client:
        for q in queries:
            qid, qtext = str(q.get("query_id", "")), str(q.get("query_text", ""))
            kb = str(q.get("kb_id") or kb_id)
            body, error = await _query(client, qtext, kb, {})
            if error is not None:
                print(f"  {qid}: ERROR {error}")
                out_queries.append(
                    {
                        "query_id": qid,
                        "query_text": qtext,
                        "nuggets": [],
                        "error": error,
                    }
                )
                continue
            context = _build_context(body.get("retrieved_chunks", []) or [])
            nuggets = await extractor(qtext, context)
            nuggets = nuggets or []
            print(f"  {qid}: {len(nuggets)} nuggets")
            out_queries.append(
                {
                    "query_id": qid,
                    "query_text": qtext,
                    "total_nuggets": len(nuggets),
                    "nuggets": nuggets,
                }
            )

    out_path = _nuggets_path(eval_set_path)
    out_path.write_text(
        yaml.safe_dump(
            {
                "metadata": {"eval_set": eval_set_path.name, "kb_id": kb_id},
                "queries": out_queries,
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    print(f"\nFixed nugget set written: {out_path}")
    return 0


async def _score_arm(
    client: httpx.AsyncClient,
    presence,
    qtext: str,
    kb_id: str,
    overrides: dict,
    nuggets: list[str],
    runs: int,
) -> tuple[list[float], str | None]:
    """K generations under one arm's config → K coverages vs the FIXED nuggets."""
    coverages: list[float] = []
    last_error: str | None = None
    for _ in range(runs):
        body, error = await _query(client, qtext, kb_id, overrides)
        if error is not None:
            last_error = error
            continue
        flags = await presence(qtext, str(body.get("answer") or ""), nuggets)
        if flags is None:
            last_error = "presence judge failed"
            continue
        judgements = [
            NuggetJudgement(text=n, present=p)
            for n, p in zip(nuggets, flags, strict=True)
        ]
        coverages.append(compute_metrics(judgements).answer_coverage)
    return coverages, (None if coverages else (last_error or "no successful run"))


async def _run_ab(
    eval_set_path: Path,
    base_url: str,
    token: str,
    config_a: dict,
    config_b: dict,
    runs: int,
    out_path: Path,
) -> int:
    kb_id, queries = _load_queries(eval_set_path)
    nuggets_path = _nuggets_path(eval_set_path)
    if not nuggets_path.is_file():
        print(
            f"fixed nugget set not found: {nuggets_path} — run --build-nuggets first",
            file=sys.stderr,
        )
        return 1
    nug_data = yaml.safe_load(nuggets_path.read_text(encoding="utf-8"))
    nuggets_by_qid = {
        str(q.get("query_id", "")): [str(n) for n in (q.get("nuggets") or [])]
        for q in nug_data.get("queries", [])
    }

    presence = make_presence_judge(get_settings())
    if presence is None:
        print("no Azure OpenAI credential — cannot score", file=sys.stderr)
        return 1

    label_a = config_a.get("llm_model") or json.dumps(config_a)
    label_b = config_b.get("llm_model") or json.dumps(config_b)
    per_query = []
    async with httpx.AsyncClient(
        base_url=base_url, headers={"Authorization": f"Bearer {token}"}, timeout=300.0
    ) as client:
        for q in queries:
            qid, qtext = str(q.get("query_id", "")), str(q.get("query_text", ""))
            kb = str(q.get("kb_id") or kb_id)
            nuggets = nuggets_by_qid.get(qid, [])
            if not nuggets:
                print(f"  {qid}: SKIP (no fixed nuggets)")
                per_query.append(
                    build_paired_query_result(
                        qid, qtext, 0, [], [], error="no fixed nuggets"
                    )
                )
                continue
            a_runs, err_a = await _score_arm(
                client, presence, qtext, kb, config_a, nuggets, runs
            )
            b_runs, err_b = await _score_arm(
                client, presence, qtext, kb, config_b, nuggets, runs
            )
            error = err_a or err_b
            r = build_paired_query_result(
                qid, qtext, len(nuggets), a_runs, b_runs, error=error
            )
            mark = (
                f"ERROR {error}"
                if error
                else (
                    f"A({label_a})={r.mean_a:.2f}+/-{r.std_a:.2f}  "
                    f"B({label_b})={r.mean_b:.2f}+/-{r.std_b:.2f}  delta={r.delta:+.2f}"
                )
            )
            print(f"  {qid}: {mark}")
            per_query.append(r)

    report = aggregate_paired(
        eval_set_path.name, kb_id, label_a, label_b, runs, per_query
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        yaml.safe_dump(
            paired_report_to_dict(report), sort_keys=False, allow_unicode=True
        ),
        encoding="utf-8",
    )
    print(f"\nPaired A/B report written: {out_path}")
    print(
        f"mean A({label_a})={report.mean_coverage_a:.3f}  "
        f"mean B({label_b})={report.mean_coverage_b:.3f}  "
        f"mean delta={report.mean_delta:+.3f}  "
        f"sign[B>A/A>B/tie]={report.delta_positive}/{report.delta_negative}/{report.delta_zero}  "
        f"avg residual std={report.mean_per_query_std:.3f}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", type=Path, default=_DEFAULT_EVAL_SET)
    parser.add_argument(
        "--build-nuggets", action="store_true", help="extract + persist fixed nuggets"
    )
    parser.add_argument(
        "--config-a",
        default=_DEFAULT_CONFIG_A,
        help="JSON QueryRequest overrides for arm A",
    )
    parser.add_argument(
        "--config-b",
        default=_DEFAULT_CONFIG_B,
        help="JSON QueryRequest overrides for arm B",
    )
    parser.add_argument(
        "--runs", type=int, default=3, help="generations per arm per query"
    )
    parser.add_argument("--base-url", default=_DEFAULT_BASE_URL)
    parser.add_argument("--token", default=_DEFAULT_TOKEN)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    if not args.eval_set.is_file():
        print(f"eval-set not found: {args.eval_set}", file=sys.stderr)
        return 1
    if args.build_nuggets:
        return asyncio.run(_build_nuggets(args.eval_set, args.base_url, args.token))

    out_path = args.out or (Path("reports") / f"{args.eval_set.stem}_ab.yaml")
    return asyncio.run(
        _run_ab(
            args.eval_set,
            args.base_url,
            args.token,
            json.loads(args.config_a),
            json.loads(args.config_b),
            args.runs,
            out_path,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
