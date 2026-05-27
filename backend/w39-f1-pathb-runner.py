"""W39 F1 Path B runner — /retrieval_test mode=vector LIVE 5+5(Free tier workaround).

Direct hits POST /kb/{kb_id}/retrieval-test with mode=vector skip Azure semantic
ranker monthly quota(Free tier 402 root cause)— Cohere rerank + W38 F2 cross-section
deboost loop fire regardless of search mode(per W39 F0.2 catch 3).

Per W39 plan §3 Phase Gate G1+G2+G3(Path B retrieval-only scope):
- G1a strict: I07 returned chunks ≥ 3
- G1b real_cross_section_drift_count avg ≤ 1 (goal) / = 0 across runs (stretch)
- G2 control I01 chunks ≥ 3 + multi-section preserved
- G3 latency retrieval avg ≤ 5s (no synthesizer)

Backend must be restarted with .env override:
- RERANKER_CROSS_SECTION_DEBOOST=0.85
- RERANKER_SECTION_PATH_PREFIX_DEPTH=2

W36 PC-W35-1 — unicode print 修正 already shipped:utf-8 reconfigure + ASCII fallback。
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

BACKEND = "http://127.0.0.1:8000"
AUTH = "Bearer dev-token"
KB_ID = "sample-document-with-image-1"

QUERIES = {
    "i07": "show me all the Integration scenarios",
    "i01": "what is the high level architecture",
}


def run_query(qname: str, run_idx: int) -> dict:
    body = json.dumps({
        "query": QUERIES[qname],
        "mode": "vector",  # F0.2 catch 1+3 — vector mode skip semantic + deboost fire
        "top_k": 5,
        "rerank": True,
    }).encode()
    req = urllib.request.Request(
        f"{BACKEND}/kb/{KB_ID}/retrieval-test",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": AUTH},
        method="POST",
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    data["_wall_latency_s"] = round(time.time() - t0, 3)
    out_path = f"w39-f1-pathb-{qname}-run-{run_idx}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return data


def analyse_drift_nuanced(chunks: list) -> tuple[int, int, int]:
    """Per W38 F3 runner pattern — distinguish real_cross_section_drift vs hierarchical_zoom.

    Returns (real_drift, zoom, unique_top_level).
    """
    if not chunks:
        return 0, 0, 0

    def top_level(c):
        sp = c.get("section_path") or []
        return sp[0] if isinstance(sp, list) and sp else None

    def second_level(c):
        sp = c.get("section_path") or []
        return sp[1] if isinstance(sp, list) and len(sp) >= 2 else None

    anchor_top = top_level(chunks[0])
    anchor_second = second_level(chunks[0])
    real_drift = 0
    zoom = 0
    tops = set()
    if anchor_top is not None:
        tops.add(anchor_top)
    for c in chunks[1:]:
        cand_top = top_level(c)
        cand_second = second_level(c)
        if cand_top is not None:
            tops.add(cand_top)
        if cand_top != anchor_top:
            real_drift += 1
        elif cand_second != anchor_second:
            zoom += 1
    return real_drift, zoom, len(tops)


def main() -> int:
    try:
        with urllib.request.urlopen(f"{BACKEND}/health", timeout=5) as r:
            print(f"backend /health = {r.status}")
    except Exception as e:
        print(f"FATAL backend not ready: {e}")
        return 1

    all_runs = []
    print("=== Q-W25-I07 (walkthrough cite) — Path B vector mode 5 runs ===")
    for i in range(1, 6):
        try:
            r = run_query("i07", i)
            chunks = r.get("chunks", []) or []
            real_drift, zoom, tops = analyse_drift_nuanced(chunks)
            print(f"  Run {i}: {len(chunks)} chunks, real_drift={real_drift}, "
                  f"zoom={zoom}, tops={tops}, rerank={r.get('rerank_latency_ms', 0)}ms, "
                  f"total={r['_wall_latency_s']}s")
            for c in chunks[:5]:
                sp = c.get("section_path") or []
                print(f"    - rank={c.get('rank',0)} {c.get('chunk_id','')[:50]} | "
                      f"score={c.get('score',0):.3f} | sp={sp}")
            all_runs.append({
                "query": "i07", "run": i,
                "wall_latency_s": r['_wall_latency_s'],
                "total_latency_ms": r.get('total_latency_ms', 0),
                "rerank_latency_ms": r.get('rerank_latency_ms', 0),
                "chunk_count": len(chunks),
                "real_cross_section_drift_count": real_drift,
                "valid_hierarchical_zoom_count": zoom,
                "unique_top_level_count": tops,
            })
        except Exception as e:
            print(f"  Run {i} FAILED: {e}")
            all_runs.append({"query": "i07", "run": i, "error": str(e)})

    print("\n=== Q-W25-I01 (control no-regression) — Path B vector mode 5 runs ===")
    for i in range(1, 6):
        try:
            r = run_query("i01", i)
            chunks = r.get("chunks", []) or []
            real_drift, zoom, tops = analyse_drift_nuanced(chunks)
            print(f"  Run {i}: {len(chunks)} chunks, real_drift={real_drift}, "
                  f"zoom={zoom}, tops={tops}, rerank={r.get('rerank_latency_ms', 0)}ms, "
                  f"total={r['_wall_latency_s']}s")
            for c in chunks[:5]:
                sp = c.get("section_path") or []
                print(f"    - rank={c.get('rank',0)} {c.get('chunk_id','')[:50]} | "
                      f"score={c.get('score',0):.3f} | sp={sp}")
            all_runs.append({
                "query": "i01", "run": i,
                "wall_latency_s": r['_wall_latency_s'],
                "total_latency_ms": r.get('total_latency_ms', 0),
                "rerank_latency_ms": r.get('rerank_latency_ms', 0),
                "chunk_count": len(chunks),
                "real_cross_section_drift_count": real_drift,
                "valid_hierarchical_zoom_count": zoom,
                "unique_top_level_count": tops,
            })
        except Exception as e:
            print(f"  Run {i} FAILED: {e}")
            all_runs.append({"query": "i01", "run": i, "error": str(e)})

    print("\n=== Aggregate ===")
    i07 = [r for r in all_runs if r.get("query") == "i07" and "chunk_count" in r]
    i01 = [r for r in all_runs if r.get("query") == "i01" and "chunk_count" in r]

    def avg(xs, key):
        vs = [x.get(key, 0) for x in xs]
        return sum(vs) / max(len(vs), 1)
    i07_avg_lat = avg(i07, "wall_latency_s")
    i01_avg_lat = avg(i01, "wall_latency_s")
    i07_avg_chunks = avg(i07, "chunk_count")
    i01_avg_chunks = avg(i01, "chunk_count")
    i07_avg_real_drift = avg(i07, "real_cross_section_drift_count")
    i01_avg_real_drift = avg(i01, "real_cross_section_drift_count")
    i07_avg_rerank = avg(i07, "rerank_latency_ms")
    i01_avg_rerank = avg(i01, "rerank_latency_ms")
    print(f"  I07: chunks {i07_avg_chunks:.1f} | real_drift {i07_avg_real_drift:.2f} | "
          f"rerank {i07_avg_rerank:.0f}ms | wall {i07_avg_lat:.2f}s")
    print(f"  I01: chunks {i01_avg_chunks:.1f} | real_drift {i01_avg_real_drift:.2f} | "
          f"rerank {i01_avg_rerank:.0f}ms | wall {i01_avg_lat:.2f}s")

    print("\n=== G1a + G1b + G2 + G3 decision tree per plan §3 (Path B scope) ===")
    g1a_strict = i07_avg_chunks >= 3
    g1b_goal = i07_avg_real_drift <= 1.0
    g1b_stretch = all(r.get("real_cross_section_drift_count", 99) == 0 for r in i07)
    g2_control = i01_avg_chunks >= 3
    g3_latency = i07_avg_lat <= 5.0
    print(f"  G1a strict (I07 chunks >= 3): {'PASS' if g1a_strict else 'FAIL'}")
    print(f"  G1b goal (I07 real_drift <= 1.0): {'PASS' if g1b_goal else 'FAIL'}")
    print(f"  G1b stretch (I07 real_drift = 0 across all runs): {'PASS' if g1b_stretch else 'FAIL'}")
    print(f"  G2 control (I01 chunks >= 3): {'PASS' if g2_control else 'FAIL'}")
    print(f"  G3 latency (I07 wall <= 5.0s): {'PASS' if g3_latency else 'FAIL'}")

    with open("w39-f1-pathb-aggregate.json", "w", encoding="utf-8") as f:
        json.dump({
            "runs": all_runs,
            "i07_avg_wall_s": round(i07_avg_lat, 2),
            "i01_avg_wall_s": round(i01_avg_lat, 2),
            "i07_avg_chunks": round(i07_avg_chunks, 1),
            "i01_avg_chunks": round(i01_avg_chunks, 1),
            "i07_avg_real_drift": round(i07_avg_real_drift, 2),
            "i01_avg_real_drift": round(i01_avg_real_drift, 2),
            "i07_avg_rerank_ms": round(i07_avg_rerank, 0),
            "i01_avg_rerank_ms": round(i01_avg_rerank, 0),
            "g1a_strict_pass": g1a_strict,
            "g1b_goal_pass": g1b_goal,
            "g1b_stretch_pass": g1b_stretch,
            "g2_control_pass": g2_control,
            "g3_latency_pass": g3_latency,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "config_under_test": (
                "RERANKER_CROSS_SECTION_DEBOOST=0.85 + "
                "RERANKER_SECTION_PATH_PREFIX_DEPTH=2 + "
                "mode=vector (skip Azure semantic Free tier quota)"
            ),
        }, f, indent=2, ensure_ascii=False)
    print("\nWrote w39-f1-pathb-aggregate.json")
    print("\nLangfuse trace events to inspect:")
    print("  - reranker_cross_section_deboost_applied (anchor_prefix + deboost_count fields)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
