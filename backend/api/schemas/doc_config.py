"""Per-document config schema (W57 / ADR-0050 — platform P2a / Gap A).

Extends the ADR-0040 per-KB config-scope model down to per-DOCUMENT granularity.
A `DocConfig` carries ONLY the post-retrieval knobs that ADR-0050 resolves per
document via the dominant cited doc — the synthesis (`answer_detail`) + citation /
image enrichment knobs that are consumed AFTER retrieval, when the cited doc is
known.

The retrieval-entry knobs (`default_top_k` / `default_rerank_k` / `parent_doc_*`)
are deliberately ABSENT here: they drive retrieval itself, which runs before any
doc is cited (chicken-and-egg), so they stay per-KB (`KbConfig`). Omitting them
from this schema makes the per-doc contract honest — a KB owner can only set the
knobs that actually take effect per document.

Every field is `Optional` with a `None` default meaning "inherit the next layer
up" (per-KB → global). A `DocConfig` with every field `None` (or no per-doc
record at all) resolves bit-identical to the per-KB config — production-preserve
(G7), mirroring the ADR-0028 / ADR-0040 migration-default precedent.

`generation.effective_config.resolve_effective_config` consumes this as the
per-DOC layer in the chain: per-query > per-DOC (this) > per-KB > global.
"""

from typing import Literal

from pydantic import BaseModel


class DocConfig(BaseModel):
    """Per-document override of the post-retrieval knobs (ADR-0050).

    Field shape is the post-retrieval subset of `KbConfig` — same names so the
    resolver treats `DocConfig` and `KbConfig` uniformly per knob. `None` = inherit
    the per-KB value (then global).
    """

    # CH-006 — synthesis answer detail level (consumed at synth, dominant doc).
    answer_detail: Literal["concise", "detailed"] | None = None

    # post-hoc citation expansion (ADR-0034 / architecture.md §3.7; consumed at
    # the citations stage, after synth — owning doc known).
    enable_citation_post_hoc_expansion: bool | None = None
    citation_expansion_max_aux: int | None = None
    citation_expansion_window: int | None = None
    citation_expansion_section_path_prefix_depth: int | None = None

    # neighbour-image attach (ADR-0034 / ADR-0049 section-fair; consumed at the
    # neighbour-image stage).
    enable_citation_neighbour_images: bool | None = None
    citation_neighbour_max_aux_images: int | None = None
    citation_neighbour_section_path_prefix_depth: int | None = None

    # image flood cap (ADR-0040 + BUG-031) + chapter-overview pin (CH-010 /
    # ADR-0047) — consumed at the image-cap / pin stages.
    max_images_per_answer: int | None = None
    enable_chapter_overview_pin: bool | None = None

    # W70 (ADR-0055) — inline image markers gate (consumed at synth prompt build;
    # post-retrieval, so the per-DOC layer applies).
    enable_inline_image_markers: bool | None = None

    # W97 (ADR-0069) — coverage-oriented synthesis gate (consumed at synth prompt
    # build; post-retrieval, so the per-DOC layer applies).
    enable_complete_coverage: bool | None = None

    # W75 (ADR-0056 段②d) — section-anchored aux images gate (consumed post-synthesis
    # at the marker-injection stage; per-DOC layer applies).
    enable_section_anchored_aux_images: bool | None = None

    # W75 F5 (ADR-0056 段②d) — per-anchor injection cap (per-DOC override; 0 = no cap).
    section_anchor_max_per_anchor: int | None = None
