/**
 * W70 (ADR-0055) — inline image markers for the answer display layer.
 *
 * When a KB has `enable_inline_image_markers` on, the synthesiser's answer text
 * carries `[IMG#<sha8>]` position markers (where a screenshot appears in the
 * source document). W70 shipped the strip path (markers hidden, render looks
 * identical to today); W71 adds `parseInlineImageMarkers`, which the chat uses
 * to place `InlineImageCard`s at the marker positions (interleaved render).
 *
 * Streaming: a marker can arrive split across SSE text-deltas, leaving the
 * accumulated content ending in a partial marker (`[IM`, `[IMG#a1b`, …). With
 * `streaming=true` a trailing partial marker is held back (not rendered) until
 * the next delta completes or disproves it — prevents marker fragments
 * flashing in the answer. A legitimate trailing `[` (e.g. a markdown link
 * being streamed) is held for at most one delta and reappears as soon as the
 * next characters rule the marker out. Interleaving happens ONLY on the final
 * (non-streaming) content, so the answer doesn't reflow as cards pop in
 * mid-stream — while streaming the chat keeps using `stripInlineImageMarkers`.
 */

// Complete markers — lenient body match ([^\]\s]*) so a malformed marker the
// LLM invents still never reaches the user. The capture group is the marker
// body (the sha8 for a well-formed marker); parse checks it against the
// surviving-image membership set.
const COMPLETE_MARKER_PATTERN = /\[IMG#([^\]\s]*)\]/g;

// A trailing prefix of an (incomplete) marker: "[", "[I", "[IM", "[IMG",
// "[IMG#", "[IMG#a1b…" (no closing bracket / whitespace yet).
const TRAILING_PARTIAL_PATTERN = /\[(?:I(?:M(?:G(?:#[^\]\s]*)?)?)?)?$/;

export function stripInlineImageMarkers(text: string, streaming = false): string {
  if (!text.includes('[')) return text;
  // Replace with the empty string regardless of the captured body.
  let out = text.replace(COMPLETE_MARKER_PATTERN, '');
  if (streaming) {
    out = out.replace(TRAILING_PARTIAL_PATTERN, '');
  }
  return out;
}

/**
 * The marker key for an image = the first 8 hex of its `checksum_sha256`
 * (markers are `[IMG#<sha8>]`, the sha8 being that prefix — orchestrator
 * `_rewrite_image_markers`, W70 F3). Images without a checksum can't be
 * anchored (no marker can reference them) and fall through to the trailing pile.
 */
export function imageMarkerKey(checksum: string): string {
  return checksum.slice(0, 8);
}

/** One piece of a parsed answer: a run of text, or an anchored image marker. */
export type InlineSegment = { type: 'text'; text: string } | { type: 'image'; sha8: string };

/**
 * Split answer text into ordered text / image segments at `[IMG#<sha8>]`
 * markers, for the W71 interleaved render. Only called on FINAL content (never
 * mid-stream — see module note).
 *
 * Membership + dedup (ADR-0055 display semantics):
 * - a marker whose sha8 IS in `validSha8` and hasn't been anchored yet becomes
 *   an `image` segment (the caller maps sha8 → the surviving `InlineImageCard`);
 * - a marker whose sha8 is NOT in `validSha8` (capped out / decorative-filtered /
 *   malformed / hallucinated) is stripped — its surrounding text merges, exactly
 *   as `stripInlineImageMarkers` would, so no empty / broken card ever shows;
 * - a REPEAT of an already-anchored sha8 is stripped too (each surviving image
 *   anchors at most once; W70 measured ~8-9% duplicate marker occurrences).
 *
 * With an empty `validSha8` the result is a single text segment whose text
 * equals `stripInlineImageMarkers(text)` — the knob-OFF / no-surviving-image
 * zero-regression path.
 */
export function parseInlineImageMarkers(
  text: string,
  validSha8: ReadonlySet<string>,
): InlineSegment[] {
  if (!text.includes('[')) {
    return text ? [{ type: 'text', text }] : [];
  }
  const segments: InlineSegment[] = [];
  const anchored = new Set<string>();
  let buffer = '';
  let lastIndex = 0;
  COMPLETE_MARKER_PATTERN.lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = COMPLETE_MARKER_PATTERN.exec(text)) !== null) {
    buffer += text.slice(lastIndex, match.index);
    lastIndex = COMPLETE_MARKER_PATTERN.lastIndex;
    const sha8 = match[1];
    if (validSha8.has(sha8) && !anchored.has(sha8)) {
      if (buffer) {
        segments.push({ type: 'text', text: buffer });
        buffer = '';
      }
      anchored.add(sha8);
      segments.push({ type: 'image', sha8 });
    }
    // else: strip — drop the marker chars, buffer keeps accumulating so the
    // text before and after the dropped marker merge into one run.
  }
  buffer += text.slice(lastIndex);
  if (buffer) segments.push({ type: 'text', text: buffer });
  return segments;
}
