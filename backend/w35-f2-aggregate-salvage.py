"""W35 F2 aggregate salvage from per-run JSONs (runner crashed on cp1252 print)."""
from __future__ import annotations

import glob
import json
import os

i07_files = sorted(glob.glob("w35-f2-i07-run-*.json"))
i01_files = sorted(glob.glob("w35-f2-i01-run-*.json"))
runs = []
for f in i07_files:
    d = json.load(open(f, encoding="utf-8"))
    runs.append({
        "query": "i07",
        "run": int(os.path.basename(f).split("-")[-1].replace(".json", "")),
        "total_latency_s": d["_total_latency_s"],
        "citation_count": len(d.get("citations", []) or []),
    })
for f in i01_files:
    d = json.load(open(f, encoding="utf-8"))
    runs.append({
        "query": "i01",
        "run": int(os.path.basename(f).split("-")[-1].replace(".json", "")),
        "total_latency_s": d["_total_latency_s"],
        "citation_count": len(d.get("citations", []) or []),
    })

i07_lat = [r["total_latency_s"] for r in runs if r["query"] == "i07"]
i01_lat = [r["total_latency_s"] for r in runs if r["query"] == "i01"]
i07_cit = [r["citation_count"] for r in runs if r["query"] == "i07"]
i01_cit = [r["citation_count"] for r in runs if r["query"] == "i01"]

agg = {
    "runs": runs,
    "i07_avg_latency_s": round(sum(i07_lat) / 5, 2),
    "i01_avg_latency_s": round(sum(i01_lat) / 5, 2),
    "i07_avg_cit": round(sum(i07_cit) / 5, 1),
    "i01_avg_cit": round(sum(i01_cit) / 5, 1),
    "g2_cit_count_pass": (sum(i07_cit) / 5 <= 5) and (sum(i01_cit) / 5 <= 8),
    "vs_w34_baseline": {
        "w34_i07_latency_s": 62.2,
        "w34_i01_latency_s": 53.4,
        "w34_i07_avg_cit": 6.0,
        "w34_i01_avg_cit": 10.2,
        "i07_latency_delta_pct": round((sum(i07_lat) / 5 - 62.2) / 62.2 * 100, 1),
        "i01_latency_delta_pct": round((sum(i01_lat) / 5 - 53.4) / 53.4 * 100, 1),
        "i07_cit_delta": round(sum(i07_cit) / 5 - 6.0, 1),
        "i01_cit_delta": round(sum(i01_cit) / 5 - 10.2, 1),
    },
    "note": "salvaged from per-run JSONs after w35-f2-runner.py crashed on cp1252 print encoding of U+2264",
    "timestamp": "2026-05-26",
}
json.dump(agg, open("w35-f2-aggregate.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("Wrote w35-f2-aggregate.json")
print(json.dumps(agg, indent=2, ensure_ascii=False))
