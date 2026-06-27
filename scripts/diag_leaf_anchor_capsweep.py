"""W98 F3 — cap-interaction sweep for the doc_order-nearest section anchor.

Offline (no backend): re-uses the captures persisted by ``diag_leaf_anchor.py``
(``reports/leaf_anchor_captures.json``, 18 raw answers + citations) and applies the
PRODUCTION ``inject_section_anchored_markers`` (now carrying ``nearest``) across
``{chapter-last, nearest} × cap ∈ {0,3,5,8}`` to pick the drive-images-1 config.

The question: nearest spreads aux across a chapter's cited steps, so does it let us
RELAX the per-anchor cap (W75 chose cap=5 as a clump↔trailing slider)? For each
config we report the clump (max consecutive marker run), the placed count (aux given
a marker), and the trailing residue (anchorable aux left in the end pile).

Run: backend/.venv/Scripts/python.exe -m scripts.diag_leaf_anchor_capsweep
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

from generation.section_anchor_markers import inject_section_anchored_markers  # noqa: E402

from scripts.diag_leaf_anchor import (  # noqa: E402
    _citations_from_payload,
    marker_count,
    max_consecutive_run,
)

_CAPTURES = Path("reports/leaf_anchor_captures.json")
_OUT = Path("reports/leaf_anchor_capsweep.json")
_DEPTH = 1
_CAPS = [0, 3, 5, 8]


def main() -> int:
    if not _CAPTURES.is_file():
        print(f"captures not found: {_CAPTURES} — run diag_leaf_anchor first", file=sys.stderr)
        return 1
    captures = json.loads(_CAPTURES.read_text(encoding="utf-8"))

    # config key → per-capture rows
    configs = [(mode, cap) for mode in ("last", "nearest") for cap in _CAPS]
    agg: dict[str, dict[str, float]] = {
        f"{mode}_cap{cap}": {
            "maxrun_sum": 0, "maxrun_max": 0, "placed": 0, "trailing": 0,
        }
        for mode, cap in configs
    }

    n = 0
    for cap_data in captures:
        raw = cap_data["answer"]
        cits = _citations_from_payload(cap_data["citations"])
        raw_n = marker_count(raw)
        # total anchorable (same-chapter aux) = nocap injected (mode-independent)
        anchorable = (
            marker_count(
                inject_section_anchored_markers(
                    raw, cits, section_prefix_depth=_DEPTH, max_per_anchor=0, nearest=False
                )
            )
            - raw_n
        )
        if anchorable == 0:
            continue  # no aux to place — config-independent, skip from the trade aggregate
        n += 1
        for mode, cap in configs:
            out = inject_section_anchored_markers(
                raw, cits, section_prefix_depth=_DEPTH, max_per_anchor=cap,
                nearest=(mode == "nearest"),
            )
            placed = marker_count(out) - raw_n
            mr = max_consecutive_run(out)
            key = f"{mode}_cap{cap}"
            agg[key]["maxrun_sum"] += mr
            agg[key]["maxrun_max"] = max(agg[key]["maxrun_max"], mr)
            agg[key]["placed"] += placed
            agg[key]["trailing"] += anchorable - placed

    print(f"captures with aux: {n}\n")
    print(f"{'config':<16} {'clump_mean':>10} {'clump_max':>9} {'placed':>7} {'trailing':>9}")
    summary = {}
    for mode, cap in configs:
        key = f"{mode}_cap{cap}"
        a = agg[key]
        clump_mean = round(a["maxrun_sum"] / n, 2) if n else 0
        summary[key] = {
            "clump_mean": clump_mean,
            "clump_max": int(a["maxrun_max"]),
            "placed": int(a["placed"]),
            "trailing": int(a["trailing"]),
        }
        print(
            f"{key:<16} {clump_mean:>10} {int(a['maxrun_max']):>9} "
            f"{int(a['placed']):>7} {int(a['trailing']):>9}"
        )

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(
        json.dumps({"captures_with_aux": n, "summary": summary}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nreport -> {_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
