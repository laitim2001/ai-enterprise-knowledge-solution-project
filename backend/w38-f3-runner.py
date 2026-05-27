"""W38 F3 5-run reproducibility runner — reranker cross-section deboost LIVE test.

Triggers /query 5x Q-W25-I07 + 5x Q-W25-I01 (W37 F2 pattern preserved).
Backend must be restarted with W38 F2 code loaded AND `.env` override
`RERANKER_CROSS_SECTION_DEBOOST=0.85` + `RERANKER_SECTION_PATH_PREFIX_DEPTH=2` active.

Per W38 plan §3 Phase Gate G1a/G1b/G2/G3:
- G1a MAINTAIN W35 baseline: I07 strict 5/5 cited + refusals 0/5 + avg_cit >= 4.8
- G1b NEW real_cross_section_drift_count avg <= 1 (goal) / = 0 across all runs (stretch)
- G2 control I01 non-regression: refusals 0/5 + avg_cit >= 3.5
- G3 latency within W35 +20% budget

Nuanced drift metric per W37 retro Karpathy §1.1 catch:
- real_cross_section_drift_count = top-level section[0] differs from anchor
  (hierarchical zoom-in NOT counted as drift)
- valid_hierarchical_zoom_count = same top-level section[0] but deeper level
  (e.g. anchor §8 + candidate §8.4 → counted as valid zoom)

W36 PC-W35-1 — unicode print 修正 already shipped:
- sys.stdout.reconfigure(encoding="utf-8")
- ASCII fallback for math operators avoid Windows cp1252 crash
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
    body = json.dumps({"query": payload["query"], "kb_id": payload["kb_id"]}).encode()
    req = urllib.request.Request(
        f"{BACKEND}/query",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": AUTH},
        method="POST",
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode())
    data["_total_latency_s"] = round(time.time() - t0, 3)
    out_path = f"w38-f3-{qname}-run-{run_idx}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return data


def analyse_drift_nuanced(citations: list) -> tuple[int, int, int]:
    """Compute nuanced drift metrics per W37 retro catch.

    Returns (real_cross_section_drift_count, valid_hierarchical_zoom_count,
             unique_top_level_count).

    - real_cross_section_drift_count = citations whose section_path[0] differs
      from anchor's section_path[0] (TRUE cross-section bug)
    - valid_hierarchical_zoom_count = citations whose section_path[0] matches
      anchor's but section_path[1] differs (valid same-section zoom-in)
    - unique_top_level_count = total distinct section_path[0] values

    If section_path is empty/malformed, counted as drift defensively.
    """
    if not citations:
        return 0, 0, 0

    def top_level(c):
        sp = c.get("section_path") or []
        if not isinstance(sp, list) or not sp:
            return None
        return sp[0]

    def second_level(c):
        sp = c.get("section_path") or []
        if not isinstance(sp, list) or len(sp) < 2:
            return None
        return sp[1]

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
            # same top-level,different second-level = hierarchical zoom-in
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
    print("=== Q-W25-I07 (walkthrough cite) - 5 runs back-to-back ===")
    for i in range(1, 6):
        try:
            r = run_query("i07", i)
            cits = r.get("citations", []) or []
            real_drift, zoom, tops = analyse_drift_nuanced(cits)
            print(f"  Run {i}: {len(cits)} cit, real_drift={real_drift}, "
                  f"zoom={zoom}, tops={tops}, total {r['_total_latency_s']}s")
            for c in cits:
                sp = c.get("section_path") or []
                print(f"    - {c.get('chunk_id','')[:50]} | sp={sp}")
            all_runs.append({
                "query": "i07", "run": i,
                "total_latency_s": r['_total_latency_s'],
                "citation_count": len(cits),
                "real_cross_section_drift_count": real_drift,
                "valid_hierarchical_zoom_count": zoom,
                "unique_top_level_count": tops,
            })
        except Exception as e:
            print(f"  Run {i} FAILED: {e}")
            all_runs.append({"query": "i07", "run": i, "error": str(e)})

    print("\n=== Q-W25-I01 (control no-regression) - 5 runs back-to-back ===")
    for i in range(1, 6):
        try:
            r = run_query("i01", i)
            cits = r.get("citations", []) or []
            real_drift, zoom, tops = analyse_drift_nuanced(cits)
            print(f"  Run {i}: {len(cits)} cit, real_drift={real_drift}, "
                  f"zoom={zoom}, tops={tops}, total {r['_total_latency_s']}s")
            for c in cits:
                sp = c.get("section_path") or []
                print(f"    - {c.get('chunk_id','')[:50]} | sp={sp}")
            all_runs.append({
                "query": "i01", "run": i,
                "total_latency_s": r['_total_latency_s'],
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
    i07_avg_zoom = avg(i07, "valid_hierarchical_zoom_count")
    i01_avg_zoom = avg(i01, "valid_hierarchical_zoom_count")
    i07_refusals = sum(1 for r in i07 if r.get("citation_count", 0) == 0)
    i01_refusals = sum(1 for r in i01 if r.get("citation_count", 0) == 0)
    print(f"  I07: avg_lat {i07_avg_lat:.2f}s | avg_cit {i07_avg_cit:.1f} | "
          f"real_drift {i07_avg_real_drift:.2f} | zoom {i07_avg_zoom:.2f} | refusals {i07_refusals}/5")
    print(f"  I01: avg_lat {i01_avg_lat:.2f}s | avg_cit {i01_avg_cit:.1f} | "
          f"real_drift {i01_avg_real_drift:.2f} | zoom {i01_avg_zoom:.2f} | refusals {i01_refusals}/5")

    print("\n=== vs W35 F1 Option C + W37 F2 baseline ===")
    print("  W35 I07 baseline: faith 0.9876 | cit avg 4.8 | refusals 0/5")
    print("  W35 I01 baseline: cit avg 5.4 | refusals 0/5")
    print("  W37 F2 I07 (depth=2 hard filter): cit avg 1.8 (-63%) | refusals 0/5 — FAIL")
    print("  W37 F2 I01 (depth=2 hard filter): cit avg 2.8 (-48%) | refusals 0/5 — FAIL")

    print("\n=== G1a + G1b + G2 + G3 decision tree per plan §3 ===")
    g1a_strict = i07_refusals == 0 and i07_avg_cit >= 4.8
    g1b_goal = i07_avg_real_drift <= 1.0
    g1b_stretch = all(r.get("real_cross_section_drift_count", 99) == 0 for r in i07)
    g2_control = i01_refusals == 0 and i01_avg_cit >= 3.5
    g3_latency = i07_avg_lat <= 14.0  # W35 ~11.5s * 1.2 = 13.8s budget
    print(f"  G1a strict (refusals=0 + avg_cit >= 4.8): {'PASS' if g1a_strict else 'FAIL'}")
    print(f"  G1b goal (I07 real_drift <= 1.0): {'PASS' if g1b_goal else 'FAIL'}")
    print(f"  G1b stretch (I07 real_drift = 0 across all runs): {'PASS' if g1b_stretch else 'FAIL'}")
    print(f"  G2 control (I01 refusals=0 + avg_cit >= 3.5): {'PASS' if g2_control else 'FAIL'}")
    print(f"  G3 latency (I07 avg <= 14.0s): {'PASS' if g3_latency else 'FAIL'}")

    with open("w38-f3-aggregate.json", "w", encoding="utf-8") as f:
        json.dump({
            "runs": all_runs,
            "i07_avg_latency_s": round(i07_avg_lat, 2),
            "i01_avg_latency_s": round(i01_avg_lat, 2),
            "i07_avg_cit": round(i07_avg_cit, 1),
            "i01_avg_cit": round(i01_avg_cit, 1),
            "i07_avg_real_drift": round(i07_avg_real_drift, 2),
            "i01_avg_real_drift": round(i01_avg_real_drift, 2),
            "i07_avg_zoom": round(i07_avg_zoom, 2),
            "i01_avg_zoom": round(i01_avg_zoom, 2),
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
                "RERANKER_SECTION_PATH_PREFIX_DEPTH=2"
            ),
        }, f, indent=2, ensure_ascii=False)
    print("\nWrote w38-f3-aggregate.json")
    print("\nLangfuse trace events to inspect:")
    print("  - reranker_cross_section_deboost_applied (anchor_prefix + deboost_count fields)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
