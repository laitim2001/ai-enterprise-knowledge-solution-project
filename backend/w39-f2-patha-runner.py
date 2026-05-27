"""W39 F2 Path A runner — /query mode=vector LIVE 5+5 full pipeline(Free tier workaround).

Direct hits POST /query with body field `{"mode": "vector"}`(W39 F2 Path A
additive enhancement)to bypass Azure semantic ranker Free tier 402 quota.
Full pipeline:retrieve → rerank → W38 F2 deboost → synthesize → cite。

Per W39 plan §3 Phase Gate G1+G2+G3(Path A full pipeline scope):
- G1a strict: I07 refusals 0/5 + avg_cit >= 4.8
- G1b real_cross_section_drift_count avg <= 1 (goal) / = 0 (stretch)
- G2 control I01 refusals 0/5 + avg_cit >= 3.5
- G3 latency I07 wall <= 14s (W35 +20% budget)

Backend must be restarted with .env override + F2 Path A code:
- RERANKER_CROSS_SECTION_DEBOOST=0.85
- RERANKER_SECTION_PATH_PREFIX_DEPTH=2

W36 PC-W35-1 — unicode print 修正 already shipped。
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

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
    body = json.dumps({
        "query": payload["query"],
        "kb_id": payload["kb_id"],
        "mode": "vector",  # W39 F2 Path A — bypass Azure semantic Free tier quota
    }).encode()
    req = urllib.request.Request(
        f"{BACKEND}/query",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": AUTH},
        method="POST",
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode())
    data["_wall_latency_s"] = round(time.time() - t0, 3)
    out_path = f"w39-f2-patha-{qname}-run-{run_idx}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return data


def analyse_drift_nuanced(citations: list) -> tuple[int, int, int]:
    """Per W38 F3 runner pattern — distinguish real_cross_section_drift vs hierarchical_zoom."""
    if not citations:
        return 0, 0, 0

    def top_level(c):
        sp = c.get("section_path") or []
        return sp[0] if isinstance(sp, list) and sp else None

    def second_level(c):
        sp = c.get("section_path") or []
        return sp[1] if isinstance(sp, list) and len(sp) >= 2 else None

    anchor_top = top_level(citations[0])
    anchor_second = second_level(citations[0])
    real_drift = 0
    zoom = 0
    tops = set()
    if anchor_top is not None:
        tops.add(anchor_top)
    for c in citations[1:]:
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
    print("=== Q-W25-I07 (walkthrough cite) — Path A vector mode 5 runs ===")
    for i in range(1, 6):
        try:
            r = run_query("i07", i)
            cits = r.get("citations", []) or []
            real_drift, zoom, tops = analyse_drift_nuanced(cits)
            print(f"  Run {i}: {len(cits)} cits, real_drift={real_drift}, "
                  f"zoom={zoom}, tops={tops}, total={r['_wall_latency_s']}s")
            for c in cits:
                sp = c.get("section_path") or []
                print(f"    - {c.get('chunk_id','')[:50]} | sp={sp}")
            all_runs.append({
                "query": "i07", "run": i,
                "total_latency_s": r['_wall_latency_s'],
                "citation_count": len(cits),
                "real_cross_section_drift_count": real_drift,
                "valid_hierarchical_zoom_count": zoom,
                "unique_top_level_count": tops,
            })
        except Exception as e:
            print(f"  Run {i} FAILED: {e}")
            all_runs.append({"query": "i07", "run": i, "error": str(e)})

    print("\n=== Q-W25-I01 (control no-regression) — Path A vector mode 5 runs ===")
    for i in range(1, 6):
        try:
            r = run_query("i01", i)
            cits = r.get("citations", []) or []
            real_drift, zoom, tops = analyse_drift_nuanced(cits)
            print(f"  Run {i}: {len(cits)} cits, real_drift={real_drift}, "
                  f"zoom={zoom}, tops={tops}, total={r['_wall_latency_s']}s")
            for c in cits:
                sp = c.get("section_path") or []
                print(f"    - {c.get('chunk_id','')[:50]} | sp={sp}")
            all_runs.append({
                "query": "i01", "run": i,
                "total_latency_s": r['_wall_latency_s'],
                "citation_count": len(cits),
                "real_cross_section_drift_count": real_drift,
                "valid_hierarchical_zoom_count": zoom,
                "unique_top_level_count": tops,
            })
        except Exception as e:
            print(f"  Run {i} FAILED: {e}")
            all_runs.append({"query": "i01", "run": i, "error": str(e)})

    print("\n=== Aggregate ===")
    i07 = [r for r in all_runs if r.get("query") == "i07" and "citation_count" in r]
    i01 = [r for r in all_runs if r.get("query") == "i01" and "citation_count" in r]

    def avg(xs, key):
        vs = [x.get(key, 0) for x in xs]
        return sum(vs) / max(len(vs), 1)
    i07_avg_lat = avg(i07, "total_latency_s")
    i01_avg_lat = avg(i01, "total_latency_s")
    i07_avg_cit = avg(i07, "citation_count")
    i01_avg_cit = avg(i01, "citation_count")
    i07_avg_real_drift = avg(i07, "real_cross_section_drift_count")
    i01_avg_real_drift = avg(i01, "real_cross_section_drift_count")
    i07_refusals = sum(1 for r in i07 if r.get("citation_count", 0) == 0)
    i01_refusals = sum(1 for r in i01 if r.get("citation_count", 0) == 0)
    print(f"  I07: avg_lat {i07_avg_lat:.2f}s | avg_cit {i07_avg_cit:.1f} | "
          f"real_drift {i07_avg_real_drift:.2f} | refusals {i07_refusals}/5")
    print(f"  I01: avg_lat {i01_avg_lat:.2f}s | avg_cit {i01_avg_cit:.1f} | "
          f"real_drift {i01_avg_real_drift:.2f} | refusals {i01_refusals}/5")

    print("\n=== vs W35 baseline ===")
    print("  W35 I07: faith 0.9876 | cit avg 4.8 | refusals 0/5")
    print("  W35 I01: cit avg 5.4 | refusals 0/5")

    print("\n=== G1a + G1b + G2 + G3 decision tree per plan §3 (Path A full pipeline scope) ===")
    g1a_strict = i07_refusals == 0 and i07_avg_cit >= 4.8
    g1b_goal = i07_avg_real_drift <= 1.0
    g1b_stretch = all(r.get("real_cross_section_drift_count", 99) == 0 for r in i07)
    g2_control = i01_refusals == 0 and i01_avg_cit >= 3.5
    g3_latency = i07_avg_lat <= 14.0
    print(f"  G1a strict (refusals=0 + avg_cit >= 4.8): {'PASS' if g1a_strict else 'FAIL'}")
    print(f"  G1b goal (I07 real_drift <= 1.0): {'PASS' if g1b_goal else 'FAIL'}")
    print(f"  G1b stretch (I07 real_drift = 0 across all runs): {'PASS' if g1b_stretch else 'FAIL'}")
    print(f"  G2 control (I01 refusals=0 + avg_cit >= 3.5): {'PASS' if g2_control else 'FAIL'}")
    print(f"  G3 latency (I07 wall <= 14.0s): {'PASS' if g3_latency else 'FAIL'}")

    with open("w39-f2-patha-aggregate.json", "w", encoding="utf-8") as f:
        json.dump({
            "runs": all_runs,
            "i07_avg_latency_s": round(i07_avg_lat, 2),
            "i01_avg_latency_s": round(i01_avg_lat, 2),
            "i07_avg_cit": round(i07_avg_cit, 1),
            "i01_avg_cit": round(i01_avg_cit, 1),
            "i07_avg_real_drift": round(i07_avg_real_drift, 2),
            "i01_avg_real_drift": round(i01_avg_real_drift, 2),
            "i07_refusals": i07_refusals,
            "i01_refusals": i01_refusals,
            "g1a_strict_pass": g1a_strict,
            "g1b_goal_pass": g1b_goal,
            "g1b_stretch_pass": g1b_stretch,
            "g2_control_pass": g2_control,
            "g3_latency_pass": g3_latency,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "config_under_test": (
                "RERANKER_CROSS_SECTION_DEBOOST=0.85 + "
                "RERANKER_SECTION_PATH_PREFIX_DEPTH=2 + "
                "QueryRequest.mode=vector (Free tier workaround)"
            ),
        }, f, indent=2, ensure_ascii=False)
    print("\nWrote w39-f2-patha-aggregate.json")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
