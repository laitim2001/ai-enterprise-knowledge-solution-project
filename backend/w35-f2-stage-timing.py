"""W35 F2 stage timing aggregate from backend structlog log.

Extracts 10 F2 synthesizer_call events (5x I07 + 5x I01 timestamps 14:46-14:49Z
2026-05-26) + computes per-stage mean latency vs W34 F2 baseline.

W34 F2 baseline:
- synth_overall 16974ms
- synth_llm_completion 15665ms (92% of overall)
- synth_expand_citations 1308ms (8%)
- synth_prompt_build 0ms
- output_tokens avg 701 / citations_count avg 7.5
"""
from __future__ import annotations

import json

LOG_PATH = "w35-uvicorn-restart-optc.log"
F2_TIMESTAMP_PREFIX = "2026-05-26T14:4"  # 14:46-14:49Z F2 events

events: list[dict] = []
with open(LOG_PATH, encoding="utf-16-le") as f:  # PowerShell *> creates UTF-16 LE
    for line in f:
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("event") != "synthesizer_call":
            continue
        ts = ev.get("timestamp", "")
        if not ts.startswith(F2_TIMESTAMP_PREFIX):
            continue
        events.append(ev)

print(f"Extracted {len(events)} F2 synthesizer_call events")
assert len(events) == 10, f"Expected 10 F2 events (5x I07 + 5x I01), got {len(events)}"

# I07 = first 5 events, I01 = last 5 (back-to-back per runner)
i07_events = events[:5]
i01_events = events[5:]


def avg(records: list[dict], key: str) -> float:
    return round(sum(r[key] for r in records) / len(records), 1)


agg = {
    "all10_avg": {
        "synth_overall_ms": avg(events, "synth_overall_latency_ms"),
        "synth_llm_completion_ms": avg(events, "synth_llm_completion_latency_ms"),
        "synth_expand_citations_ms": avg(events, "synth_expand_citations_latency_ms"),
        "synth_prompt_build_ms": avg(events, "synth_prompt_build_latency_ms"),
        "output_tokens": avg(events, "output_tokens"),
        "input_tokens": avg(events, "input_tokens"),
        "citations_count": avg(events, "citations_count"),
    },
    "i07_avg": {
        "synth_overall_ms": avg(i07_events, "synth_overall_latency_ms"),
        "synth_llm_completion_ms": avg(i07_events, "synth_llm_completion_latency_ms"),
        "synth_expand_citations_ms": avg(i07_events, "synth_expand_citations_latency_ms"),
        "output_tokens": avg(i07_events, "output_tokens"),
        "citations_count": avg(i07_events, "citations_count"),
    },
    "i01_avg": {
        "synth_overall_ms": avg(i01_events, "synth_overall_latency_ms"),
        "synth_llm_completion_ms": avg(i01_events, "synth_llm_completion_latency_ms"),
        "synth_expand_citations_ms": avg(i01_events, "synth_expand_citations_latency_ms"),
        "output_tokens": avg(i01_events, "output_tokens"),
        "citations_count": avg(i01_events, "citations_count"),
    },
    "w34_baseline": {
        "synth_overall_ms": 16974,
        "synth_llm_completion_ms": 15665,
        "synth_expand_citations_ms": 1308,
        "synth_prompt_build_ms": 0,
        "output_tokens": 701,
        "citations_count": 7.5,
    },
}

# Compute deltas vs W34 F2 baseline
def pct_delta(w35: float, w34: float) -> str:
    if w34 == 0:
        return "n/a (W34=0)"
    pct = (w35 - w34) / w34 * 100
    return f"{pct:+.1f}%"


agg["vs_w34_baseline_pct"] = {
    "synth_overall": pct_delta(agg["all10_avg"]["synth_overall_ms"], 16974),
    "synth_llm_completion": pct_delta(agg["all10_avg"]["synth_llm_completion_ms"], 15665),
    "synth_expand_citations": pct_delta(agg["all10_avg"]["synth_expand_citations_ms"], 1308),
    "output_tokens": pct_delta(agg["all10_avg"]["output_tokens"], 701),
    "citations_count": pct_delta(agg["all10_avg"]["citations_count"], 7.5),
}

# G3 decision tree per plan §3
g3_threshold_ms = 14098  # -10% W34 baseline 15665ms
g3_pass = agg["all10_avg"]["synth_llm_completion_ms"] <= g3_threshold_ms
agg["g3_llm_emit_pass"] = g3_pass
agg["g3_threshold_ms"] = g3_threshold_ms

with open("w35-f2-stage-timing-aggregate.json", "w", encoding="utf-8") as f:
    json.dump(agg, f, indent=2, ensure_ascii=False)

print(json.dumps(agg, indent=2, ensure_ascii=False))
