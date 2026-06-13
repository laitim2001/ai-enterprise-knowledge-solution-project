"""W70/W71 (ADR-0055) — inline image marker helpers for the generation layer.

When a KB has `enable_inline_image_markers` on, the synthesiser's answer carries
`[IMG#<sha8>]` position markers (where a screenshot appears in the source
document — see `prompt_builder._MARKER_RULE`). They are display / placement
metadata, not prose: the chat strips them for display (W70) and interleaves
`InlineImageCard`s at their positions (W71), while any path that judges or
exports the answer *as text* must drop them first.

`strip_inline_image_markers` is that backend strip — the symmetric counterpart
of the frontend `lib/chat/inline-image-markers.ts` strip. Lenient body match so
a malformed marker the LLM invents is removed too.
"""

from __future__ import annotations

import re

# Mirrors the frontend lenient pattern (`\[IMG#[^\]\s]*\]`): the well-formed
# marker body is the 8-hex sha8, but anything up to the closing bracket is
# stripped so a malformed marker never survives into judged / exported text.
_INLINE_IMAGE_MARKER_RE = re.compile(r"\[IMG#[^\]\s]*\]")


def strip_inline_image_markers(text: str) -> str:
    """Remove every `[IMG#...]` inline image marker from `text` (fast-path on `[`)."""
    if "[" not in text:
        return text
    return _INLINE_IMAGE_MARKER_RE.sub("", text)
