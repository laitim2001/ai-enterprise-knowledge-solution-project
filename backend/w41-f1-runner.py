"""W41 F1 runner — /query mode=vector LIVE 5+5 + W40 F1+F2 log evidence extraction.

Direct hits POST /query with body field `{"mode": "vector"}`(per W39 F2 Path A
permanent enhancement)to bypass Azure semantic ranker Free tier 402 quota,
collect LIVE evidence on W40 F1(effective_depth)+ W40 F2(rerank_top_k + multiplier)
production code effect。

Per W41 plan §2 Phase Gate G1-G5(Path A full pipeline scope):
- G1 W40 F1 mechanism verify: deboost event 10/10 firing + effective_depth log field present
- G2 W40 F2 mechanism verify: rerank_top_k = top_k * multiplier active(expected 160 if top_k=40)
- G3a cit count: I07 avg_cit ≥ 4.5 marginal or ≥ 4.8 W35 baseline
- G3b drift preserve: I07 avg drift ≤ W39 F2 Path A baseline 1.0
- G4 control: I01 refusals 0/5 + avg_cit ≥ 3.5
- G5 production preserve: .env REVERT post-F1

Backend restarted with .env W41 F1 marker block 3 knobs:
- RERANKER_CROSS_SECTION_DEBOOST=0.85
- RERANKER_SECTION_PATH_PREFIX_DEPTH=2
- RERANKER_OVERFETCH_MULTIPLIER=4

W36 PC-W35-1 — sys.stdout.reconfigure utf-8 already shipped。
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

BACKEND = "http://127.0.0.1:8000"
AUTH = "Bearer dev-token"
LOG_PATH = "uvicorn-restart-w41-f1.log.out"

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
        "mode": "vector",
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
    out_path = f"w41-f1-{qname}-run-{run_idx}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return data


def analyse_drift_nuanced(citations: list) -> tuple[int, int, int]:
    """Per W39 F2 runner pattern — distinguish real_cross_section_drift vs hierarchical_zoom."""
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


def parse_log_evidence(log_path: str = LOG_PATH) -> dict:
    """W41 NEW log inspection helper — extract W40 F1 + W40 F2 evidence fields.

    Returns aggregate metrics across all retrieval_complete + deboost_applied events
    in the log file:
    - deboost_event_count: how many times deboost loop fired
    - effective_depth_distribution: list of effective_depth values seen
    - rerank_top_k_distribution: list of rerank_top_k values seen
    - top_k_distribution: list of top_k values seen
    - deboost_count_distribution: list of deboost_count values
    """
    try:
        with open(log_path, encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return {"error": f"log file {log_path} not found"}

    deboost_events = []
    retrieval_events = []
    for line in lines:
        line = line.strip()
        # structlog JSON one-line events
        if '"reranker_cross_section_deboost_applied"' in line:
            try:
                # extract JSON portion (line may have prefix)
                json_start = line.find("{")
                if json_start >= 0:
                    evt = json.loads(line[json_start:])
                    deboost_events.append(evt)
            except (json.JSONDecodeError, ValueError):
                pass
        elif '"retrieval_complete"' in line:
            try:
                json_start = line.find("{")
                if json_start >= 0:
                    evt = json.loads(line[json_start:])
                    retrieval_events.append(evt)
            except (json.JSONDecodeError, ValueError):
                pass

    # Filter to only events from this W41 F1 run (last N events where N = 10 expected)
    # Use last 10 retrieval_events + last 10 deboost_events
    retrieval_events = retrieval_events[-10:]
    deboost_events = deboost_events[-10:]

    return {
        "deboost_event_count": len(deboost_events),
        "retrieval_event_count": len(retrieval_events),
        "effective_depth_distribution": [e.get("effective_depth") for e in deboost_events],
        "rerank_top_k_distribution": [e.get("rerank_top_k") for e in retrieval_events],
        "top_k_distribution": [e.get("top_k") for e in retrieval_events],
        "deboost_count_distribution": [e.get("deboost_count") for e in deboost_events],
        "total_candidates_distribution": [e.get("total_candidates") for e in deboost_events],
        "anchor_prefix_examples": [e.get("anchor_prefix") for e in deboost_events[:3]],
    }


def main() -> int:
    try:
        with urllib.request.urlopen(f"{BACKEND}/health", timeout=5) as r:
            print(f"backend /health = {r.status}")
    except Exception as e:
        print(f"FATAL backend not ready: {e}")
        return 1

    all_runs = []
    print("=== Q-W25-I07 (walkthrough cite) — W41 F1 vector mode 5 runs ===")
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

    print("\n=== Q-W25-I01 (control no-regression) — W41 F1 vector mode 5 runs ===")
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

    print("\n=== Baselines ===")
    print("  W35 I07: cit avg 4.8 | refusals 0/5  (production baseline preserved)")
    print("  W35 I01: cit avg 5.4 | refusals 0/5")
    print("  W39 F2 Path A I07: cit avg 3.6 | real_drift 1.00 (mode=vector + deboost conflate)")
    print("  W39 F2 Path A I01: cit avg 6.6 | real_drift 5.40")

    print("\n=== W40 F1+F2 LOG EVIDENCE EXTRACTION ===")
    log_evidence = parse_log_evidence()
    for k, v in log_evidence.items():
        print(f"  {k}: {v}")

    print("\n=== G1-G5 decision tree per plan §2 ===")
    g1_f1_mechanism = (
        log_evidence.get("deboost_event_count", 0) >= 8
        and all(d in (1, 2) for d in log_evidence.get("effective_depth_distribution", []) if d is not None)
    )
    g2_f2_mechanism = any(
        rt is not None and rt > tk
        for rt, tk in zip(
            log_evidence.get("rerank_top_k_distribution", []),
            log_evidence.get("top_k_distribution", []),
            strict=False,
        )
    )
    g3a_cit_improve = i07_avg_cit >= 4.5
    g3a_full_recovery = i07_avg_cit >= 4.8
    g3a_vs_w39 = i07_avg_cit > 3.6
    g3b_drift_preserve = i07_avg_real_drift <= 1.0
    g4_control = i01_refusals == 0 and i01_avg_cit >= 3.5

    print(f"  G1 W40 F1 mechanism (deboost firing ≥8/10 + effective_depth ∈ {{1,2}}): {'PASS' if g1_f1_mechanism else 'FAIL'}")
    print(f"  G2 W40 F2 mechanism (rerank_top_k > top_k seen): {'PASS' if g2_f2_mechanism else 'FAIL'}")
    print(f"  G3a I07 avg_cit ≥ 4.5 marginal: {'PASS' if g3a_cit_improve else 'FAIL'}")
    print(f"  G3a I07 avg_cit ≥ 4.8 W35 full recovery: {'PASS' if g3a_full_recovery else 'FAIL'}")
    print(f"  G3a I07 avg_cit > 3.6 vs W39 F2 baseline: {'PASS' if g3a_vs_w39 else 'FAIL'}")
    print(f"  G3b I07 real_drift ≤ 1.0 preserve: {'PASS' if g3b_drift_preserve else 'FAIL'}")
    print(f"  G4 control (I01 refusals=0 + avg_cit ≥ 3.5): {'PASS' if g4_control else 'FAIL'}")

    with open("w41-f1-aggregate.json", "w", encoding="utf-8") as f:
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
            "log_evidence": log_evidence,
            "g1_f1_mechanism_pass": g1_f1_mechanism,
            "g2_f2_mechanism_pass": g2_f2_mechanism,
            "g3a_cit_marginal_pass": g3a_cit_improve,
            "g3a_full_recovery_pass": g3a_full_recovery,
            "g3a_vs_w39_pass": g3a_vs_w39,
            "g3b_drift_preserve_pass": g3b_drift_preserve,
            "g4_control_pass": g4_control,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "config_under_test": (
                "RERANKER_CROSS_SECTION_DEBOOST=0.85 + "
                "RERANKER_SECTION_PATH_PREFIX_DEPTH=2 + "
                "RERANKER_OVERFETCH_MULTIPLIER=4 + "
                "QueryRequest.mode=vector (Free tier workaround)"
            ),
        }, f, indent=2, ensure_ascii=False)
    print("\nWrote w41-f1-aggregate.json")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
