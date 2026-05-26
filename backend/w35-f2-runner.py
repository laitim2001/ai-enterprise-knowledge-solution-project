"""W35 F2.1 5-run latency profile measurement Option C — Q-W25-I07 + Q-W25-I01.

Triggers /query 5x I07 + 5x I01 (W34 F2 pattern preserved). Backend must be
restarted with W35 F1.7 Option C wording loaded (prompt_builder.py:30) —
re-uses W34 F2.1 structlog stage timing instrumentation (synth_overall /
synth_prompt_build / synth_llm_completion / synth_expand_citations).

Aggregates per-stage mean latency vs W34 F2 baseline:
- W34 baseline: I07 avg 62.2s / I01 avg 53.4s
- W34 synth_overall 16974ms / synth_llm_completion 15665ms (92%) /
  synth_expand_citations 1308ms (8%) / synth_prompt_build 0ms
- W34 I07 avg_cit 6 / I01 avg_cit 10.2

W35 Option C expected (per plan §3 G2 + G3):
- I07 avg_cit ≤ 5 AND I01 avg_cit ≤ 8 → G2 drop
- synth_llm_completion ≤ 14098ms (-10% W34) → G3 drop
"""
from __future__ import annotations

import json
import time
import urllib.request

BACKEND = "http://127.0.0.1:8000"
AUTH = "Bearer dev-token"

QUERIES = {
    "i07": {
        "query": "show me all the Integration scenarios",
        "kb_id": "sample-document-with-image-1",
    },
    "i01": {
        "query": "what is the high level architecture",
        "kb_id": "sample-document-with-image-1",
    },
}


def run_query(qname: str, run_idx: int) -> dict:
    payload = QUERIES[qname]
    body = json.dumps({"query": payload["query"], "kb_id": payload["kb_id"]}).encode()
    req = urllib.request.Request(
        f"{BACKEND}/query",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": AUTH},
        method="POST",
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
    data["_total_latency_s"] = round(time.time() - t0, 3)
    out_path = f"w35-f2-{qname}-run-{run_idx}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return data


def main() -> int:
    try:
        with urllib.request.urlopen(f"{BACKEND}/health", timeout=5) as r:
            print(f"backend /health = {r.status}")
    except Exception as e:
        print(f"FATAL backend not ready: {e}")
        return 1

    all_runs = []
    print("=== Q-W25-I07 (walkthrough cite) - 5 runs back-to-back ===")
    for i in range(1, 6):
        try:
            r = run_query("i07", i)
            cits = r.get("citations", []) or []
            print(f"  Run {i}: {len(cits)} citations, total {r['_total_latency_s']}s")
            all_runs.append({"query": "i07", "run": i, "total_latency_s": r['_total_latency_s'],
                             "citation_count": len(cits)})
        except Exception as e:
            print(f"  Run {i} FAILED: {e}")
            all_runs.append({"query": "i07", "run": i, "error": str(e)})

    print("\n=== Q-W25-I01 (control no-regression) - 5 runs back-to-back ===")
    for i in range(1, 6):
        try:
            r = run_query("i01", i)
            cits = r.get("citations", []) or []
            print(f"  Run {i}: {len(cits)} citations, total {r['_total_latency_s']}s")
            all_runs.append({"query": "i01", "run": i, "total_latency_s": r['_total_latency_s'],
                             "citation_count": len(cits)})
        except Exception as e:
            print(f"  Run {i} FAILED: {e}")
            all_runs.append({"query": "i01", "run": i, "error": str(e)})

    print("\n=== Aggregate ===")
    i07_lat = [r["total_latency_s"] for r in all_runs if r.get("query") == "i07" and "total_latency_s" in r]
    i01_lat = [r["total_latency_s"] for r in all_runs if r.get("query") == "i01" and "total_latency_s" in r]
    i07_cit = [r["citation_count"] for r in all_runs if r.get("query") == "i07" and "citation_count" in r]
    i01_cit = [r["citation_count"] for r in all_runs if r.get("query") == "i01" and "citation_count" in r]
    i07_avg_lat = sum(i07_lat) / max(len(i07_lat), 1)
    i01_avg_lat = sum(i01_lat) / max(len(i01_lat), 1)
    i07_avg_cit = sum(i07_cit) / max(len(i07_cit), 1)
    i01_avg_cit = sum(i01_cit) / max(len(i01_cit), 1)
    print(f"  I07 avg total latency: {i07_avg_lat:.2f}s | avg citations: {i07_avg_cit:.1f}")
    print(f"  I01 avg total latency: {i01_avg_lat:.2f}s | avg citations: {i01_avg_cit:.1f}")

    print(f"\n=== vs W34 F2 baseline ===")
    print(f"  W34 I07 baseline: 62.2s / 6.0 cit | I01: 53.4s / 10.2 cit")
    print(f"  W35 I07: {i07_avg_lat:.2f}s ({(i07_avg_lat - 62.2) / 62.2 * 100:+.1f}%) / {i07_avg_cit:.1f} cit ({i07_avg_cit - 6.0:+.1f})")
    print(f"  W35 I01: {i01_avg_lat:.2f}s ({(i01_avg_lat - 53.4) / 53.4 * 100:+.1f}%) / {i01_avg_cit:.1f} cit ({i01_avg_cit - 10.2:+.1f})")

    print(f"\n=== G2 + G3 decision tree per plan §3 ===")
    g2_pass = i07_avg_cit <= 5 and i01_avg_cit <= 8
    print(f"  G2 cit count drop (I07 ≤ 5 AND I01 ≤ 8): {'PASS' if g2_pass else 'inconclusive/null'}")

    with open("w35-f2-aggregate.json", "w", encoding="utf-8") as f:
        json.dump({
            "runs": all_runs,
            "i07_avg_latency_s": round(i07_avg_lat, 2),
            "i01_avg_latency_s": round(i01_avg_lat, 2),
            "i07_avg_cit": round(i07_avg_cit, 1),
            "i01_avg_cit": round(i01_avg_cit, 1),
            "g2_cit_count_pass": g2_pass,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, f, indent=2, ensure_ascii=False)
    print("\nWrote w35-f2-aggregate.json")
    print("\nStage-level timings: see backend w35-uvicorn-restart-optc.log for structlog JSON events")
    print("  synthesizer_call -> synth_overall_latency_ms / synth_prompt_build_latency_ms / synth_llm_completion_latency_ms / synth_expand_citations_latency_ms")
    print("  expand_citations_list_chunks_batch -> unique_docs_count / expand_list_chunks_batch_latency_ms")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
