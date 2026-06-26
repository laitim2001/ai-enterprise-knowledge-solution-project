"""甲類 leaf-anchor offline diagnostic (W97 follow-up / ADR-0056 段②d leaf 級).

NOT production code — a zero-production-change diagnostic that asks ONE question:
does anchoring each un-anchored aux image to its ``doc_order``-NEAREST anchored
marker (instead of the chapter's LAST anchored marker, the current W75 behaviour)
meaningfully reduce the章節內 clump (max consecutive image-card run)?

The current ``inject_section_anchored_markers`` (section_anchor_markers.py) groups
ALL same-chapter aux images into ONE marker run after the chapter's LAST anchored
marker → DD-1 measured maxRun=39 (a step followed by 39 image cards ≈ a relocated
trailing pile). The leaf-level idea uses the ``doc_order`` signal (already in the
index, currently only used to SORT) to pick the NEAREST anchor → spread the aux
images across the chapter's distinct cited steps.

Why a knob flip is needed: the live ``/query`` answer (drive-images-1 knob ON) is
POST-injection — synthesiser markers and injected markers are indistinguishable in
the final text. To run both inject variants offline we need the PRE-injection raw
answer (synthesiser's own ``[IMG#]`` anchors) + the full citations (aux still
attached via the separate ``enable_citation_neighbour_images`` knob, left ON). So:
flip ``enable_section_anchored_aux_images`` OFF, capture, RESTORE (try/finally).

Caveat (per W75 教訓 6/7): the synthesiser is stochastic + the nearest variant can
only spread when the synthesiser cited MULTIPLE steps in a chapter. If it cited one
step, nearest == last (no improvement) — the diagnostic reveals how often that is.

Prereqs: backend up; mock auth Bearer dev-token. Output → reports/ (gitignored).
Run: backend/.venv/Scripts/python.exe -m scripts.diag_leaf_anchor
"""

from __future__ import annotations

import truststore

truststore.inject_into_ssl()

import json  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

import httpx  # noqa: E402
import yaml  # noqa: E402

from generation.section_anchor_markers import _MARKER_RE  # noqa: E402
from generation.section_anchor_markers import (  # noqa: E402
    inject_section_anchored_markers,
)

_BASE_URL = "http://localhost:8000"
_TOKEN = "dev-token"
_KB_ID = "drive-images-1"
_DEPTH = 1
_CAP = 5  # drive-images-1 production section_anchor_max_per_anchor
_OUT = Path("reports/leaf_anchor_diag.json")
_EVAL_SET = Path("docs/eval-set-image-recall-ar.yaml")
_RUNS = 2  # captures per query (synthesiser is stochastic — gauge how robust the win is)


def _load_queries(path: Path) -> list[tuple[str, str]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [
        (str(q.get("query_id", "")), str(q.get("query_text", "")))
        for q in data.get("queries", [])
    ]


# ── lightweight image / citation shims (avoid importing pydantic Citation) ──────
class _Img:
    def __init__(self, checksum_sha256: str, source_section: list[str], doc_order: int):
        self.checksum_sha256 = checksum_sha256
        self.source_section = source_section
        self.doc_order = doc_order


class _Cit:
    def __init__(self, embedded_images: list[_Img]):
        self.embedded_images = embedded_images


def _citations_from_payload(payload: list[dict]) -> list[_Cit]:
    cits: list[_Cit] = []
    for c in payload:
        imgs = [
            _Img(
                str(im.get("checksum_sha256") or ""),
                [str(p) for p in (im.get("source_section") or [])],
                int(im.get("doc_order") or 0),
            )
            for im in (c.get("embedded_images") or [])
        ]
        cits.append(_Cit(imgs))
    return cits


# ── nearest-doc_order variant (the only thing under test) ───────────────────────
def inject_nearest(
    answer: str, citations: list, *, section_prefix_depth: int = 1, max_per_anchor: int = 0
) -> str:
    """Variant of inject_section_anchored_markers: anchor each un-anchored aux image
    after the SAME-CHAPTER anchored marker whose image's doc_order is NEAREST to the
    aux image's doc_order (vs current = the chapter's LAST anchored marker)."""
    if not answer or "[IMG#" not in answer:
        return answer
    anchored_matches = list(_MARKER_RE.finditer(answer))
    if not anchored_matches:
        return answer
    anchored_sha8 = {m.group(1) for m in anchored_matches}

    seen: set[str] = set()
    # sha8 → (section, doc_order) for anchored; un_anchored list of (img, section)
    anchored_meta: dict[str, tuple[tuple[str, ...], int]] = {}
    un_anchored: list[tuple[_Img, tuple[str, ...]]] = []
    for cit in citations:
        for img in cit.embedded_images:
            sha = img.checksum_sha256
            if not sha:
                continue
            sha8 = sha[:8]
            if sha8 in seen:
                continue
            seen.add(sha8)
            section = tuple(str(p) for p in img.source_section[:section_prefix_depth])
            if len(section) < section_prefix_depth:
                continue
            if sha8 in anchored_sha8:
                anchored_meta[sha8] = (section, img.doc_order)
            else:
                un_anchored.append((img, section))
    if not un_anchored:
        return answer

    # Each anchored marker occurrence → (section, doc_order, end_offset).
    anchors: list[tuple[tuple[str, ...], int, int]] = []
    for m in anchored_matches:
        meta = anchored_meta.get(m.group(1))
        if meta is None:
            continue
        anchors.append((meta[0], meta[1], m.end()))
    if not anchors:
        return answer

    # For each aux image: choose the same-section anchor with nearest doc_order
    # (tie → earliest text offset). Group aux by chosen anchor offset.
    by_offset: dict[int, list[_Img]] = {}
    for img, section in un_anchored:
        candidates = [a for a in anchors if a[0] == section]
        if not candidates:
            continue  # no same-chapter anchor — stays trailing
        best = min(candidates, key=lambda a: (abs(a[1] - img.doc_order), a[2]))
        by_offset.setdefault(best[2], []).append(img)
    if not by_offset:
        return answer

    insertions: list[tuple[int, str]] = []
    for offset, imgs in by_offset.items():
        imgs_sorted = sorted(imgs, key=lambda im: im.doc_order)
        if max_per_anchor > 0:
            imgs_sorted = imgs_sorted[:max_per_anchor]
        run = "".join(f"[IMG#{im.checksum_sha256[:8]}]" for im in imgs_sorted)
        insertions.append((offset, run))
    insertions.sort(key=lambda p: p[0], reverse=True)
    out = answer
    for pos, text in insertions:
        out = out[:pos] + text + out[pos:]
    return out


# ── metrics ─────────────────────────────────────────────────────────────────────
def max_consecutive_run(answer: str) -> int:
    """Longest run of [IMG#] markers separated only by whitespace (== frontend clump)."""
    matches = list(_MARKER_RE.finditer(answer))
    if not matches:
        return 0
    best = cur = 1
    for prev, nxt in zip(matches, matches[1:], strict=False):
        if answer[prev.end() : nxt.start()].strip() == "":
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best


def marker_count(answer: str) -> int:
    return len(_MARKER_RE.findall(answer))


def distinct_anchor_runs(answer: str) -> int:
    """Number of distinct image-card runs (groups of consecutive markers)."""
    matches = list(_MARKER_RE.finditer(answer))
    if not matches:
        return 0
    runs = 1
    for prev, nxt in zip(matches, matches[1:], strict=False):
        if answer[prev.end() : nxt.start()].strip() != "":
            runs += 1
    return runs


# ── KB config flip / restore ────────────────────────────────────────────────────
def _get_config(client: httpx.Client) -> dict:
    r = client.get("/kb")
    r.raise_for_status()
    for kb in r.json():
        if kb.get("kb_id") == _KB_ID:
            return dict(kb["config"])
    raise RuntimeError(f"KB {_KB_ID} not found")


def _patch_config(client: httpx.Client, config: dict) -> dict:
    r = client.patch(f"/kb/{_KB_ID}/settings", json=config)
    r.raise_for_status()
    return r.json()


def _metrics_for(raw: str, cits: list) -> dict:
    base = inject_section_anchored_markers(
        raw, cits, section_prefix_depth=_DEPTH, max_per_anchor=_CAP
    )
    base_nocap = inject_section_anchored_markers(
        raw, cits, section_prefix_depth=_DEPTH, max_per_anchor=0
    )
    near = inject_nearest(raw, cits, section_prefix_depth=_DEPTH, max_per_anchor=_CAP)
    near_nocap = inject_nearest(raw, cits, section_prefix_depth=_DEPTH, max_per_anchor=0)
    raw_n = marker_count(raw)
    return {
        "raw_markers": raw_n,
        "cap5": {
            "base_maxrun": max_consecutive_run(base),
            "near_maxrun": max_consecutive_run(near),
            "base_injected": marker_count(base) - raw_n,
            "near_injected": marker_count(near) - raw_n,
        },
        "nocap": {
            "base_maxrun": max_consecutive_run(base_nocap),
            "near_maxrun": max_consecutive_run(near_nocap),
            "base_injected": marker_count(base_nocap) - raw_n,
            "near_injected": marker_count(near_nocap) - raw_n,
        },
    }


def main() -> int:
    headers = {"Authorization": f"Bearer {_TOKEN}"}
    queries = _load_queries(_EVAL_SET)
    captures: list[dict] = []
    with httpx.Client(base_url=_BASE_URL, headers=headers, timeout=300.0) as client:
        original = _get_config(client)
        if not original.get("enable_section_anchored_aux_images"):
            print("WARN: knob already OFF — capturing as-is (still raw).")
        flipped = dict(original)
        flipped["enable_section_anchored_aux_images"] = False
        try:
            res = _patch_config(client, flipped)
            print(
                "knob flipped OFF (enable_section_anchored_aux_images="
                f"{res.get('enable_section_anchored_aux_images')}); "
                f"{len(queries)} queries x {_RUNS} runs"
            )
            for qid, qtext in queries:
                for run in range(_RUNS):
                    try:
                        r = client.post(
                            "/query", json={"query": qtext, "kb_id": _KB_ID}
                        )
                        r.raise_for_status()
                        body = r.json()
                        captures.append(
                            {
                                "query_id": qid,
                                "run": run,
                                "answer": body.get("answer") or "",
                                "citations": body.get("citations") or [],
                            }
                        )
                        print(f"  {qid}.{run}: captured "
                              f"({len(body.get('citations') or [])} citations)")
                    except Exception as exc:  # noqa: BLE001
                        print(f"  {qid}.{run}: CAPTURE ERROR {type(exc).__name__}: {exc}")
        finally:
            restored = _patch_config(client, original)
            ok = restored.get("enable_section_anchored_aux_images") is True
            print("knob RESTORED (enable_section_anchored_aux_images="
                  f"{restored.get('enable_section_anchored_aux_images')}) ok={ok}")

    # ── offline A/B per capture: current (chapter-last) vs nearest (doc_order) ───
    rows = []
    helped = worse = 0
    extra_placed_cap5 = 0  # aux images nearest anchors that base dumps to trailing
    clump_reductions = []  # nocap maxrun reduction per capture
    for cap in captures:
        m = _metrics_for(cap["answer"], _citations_from_payload(cap["citations"]))
        m["query_id"], m["run"] = cap["query_id"], cap["run"]
        rows.append(m)
        c5, nc = m["cap5"], m["nocap"]
        if c5["near_injected"] > c5["base_injected"] or nc["near_maxrun"] < nc["base_maxrun"]:
            helped += 1
        if nc["near_maxrun"] > nc["base_maxrun"] or c5["near_injected"] < c5["base_injected"]:
            worse += 1  # structural Pareto says this should stay 0
        extra_placed_cap5 += max(0, c5["near_injected"] - c5["base_injected"])
        clump_reductions.append(nc["base_maxrun"] - nc["near_maxrun"])
        print(
            f"\n{m['query_id']}.{m['run']}: raw_markers={m['raw_markers']}"
        )
        for mode in ("nocap", "cap5"):
            x = m[mode]
            print(
                f"  [{mode:5}] clump: base={x['base_maxrun']:>3} -> near={x['near_maxrun']:>3}"
                f"   anchored: base={x['base_injected']:>3} -> near={x['near_injected']:>3}"
            )

    n = len(rows) or 1
    summary = {
        "captures": len(rows),
        "helped": helped,
        "worse": worse,
        "extra_images_placed_cap5_total": extra_placed_cap5,
        "extra_images_placed_cap5_mean": round(extra_placed_cap5 / n, 2),
        "nocap_clump_reduction_mean": round(sum(clump_reductions) / n, 2),
        "nocap_clump_reduction_max": max(clump_reductions) if clump_reductions else 0,
    }
    print("\n=== AGGREGATE ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(
        json.dumps(
            {"kb_id": _KB_ID, "depth": _DEPTH, "cap": _CAP, "runs": _RUNS,
             "summary": summary, "rows": rows},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    Path("reports/leaf_anchor_captures.json").write_text(
        json.dumps(captures, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nreport -> {_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
