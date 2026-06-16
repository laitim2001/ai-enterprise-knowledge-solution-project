/**
 * Chat citation → image dedup (BUG-026 Finding A).
 *
 * The backend `attach_neighbour_images` (citation_image_neighbors.py, W25 F5 D1
 * / ADR-0034) attaches neighbour-chunk images to intro/meta citations, and
 * dedups only WITHIN a single citation. Across citations the same image (same
 * `checksum_sha256`) can therefore appear in several citations' `embedded_images`
 * — e.g. a §8.1 figure is both the §8.1 chunk's direct image AND the §8 intro
 * chunk's neighbour image. The chat answer previously rendered the flattened
 * (citation, image) pairs with no cross-citation dedup, so the same image showed
 * up multiple times in the inline cards + "Referenced screenshots" gallery.
 *
 * `dedupeCitationImages` flattens to a list of unique images keyed by
 * `checksum_sha256` (falling back to `blob_url` when the checksum is absent —
 * pre-BUG-009 chunks). Each unique image is attributed to the FIRST citation
 * (in citation order) that references it, so the inline cards, the gallery, and
 * the image count all draw from one consistent deduped list. The list is then
 * ordered by DOCUMENT position (the image's section_path) per BUG-034 Finding D
 * so a procedure reads start→end rather than leading with the highest-reranked
 * sub-step; the numeric badge still reflects citation position.
 *
 * The mockup (ekp-page-chat.jsx:621-664) never shows the same screenshot twice,
 * so deduping moves the implementation closer to the mockup (a reverse-direction
 * drift fix, not an H7 deviation per CLAUDE.md §5.7).
 */
import type { Citation, ImageRef } from '@/lib/api/query';
import { imageMarkerKey, parseInlineImageMarkers } from '@/lib/chat/inline-image-markers';

/**
 * CH-009 / ADR-0046 (OD-1) — a screenshot whose smaller dimension is below this
 * is treated as a decorative icon (the manual's Tip/Note/idea graphics), not a
 * content figure, and is filtered at display. Only applied when dims are KNOWN
 * (>0 — populated by the ADR-0046 PNG IHDR probe at ingest; pre-re-index data
 * has 0×0 and is never judged decorative). Threshold tunable.
 */
export const DECORATIVE_MIN_PX = 64;

/**
 * CH-009 / ADR-0046 (OD-4, 2026-06-08) — large near-square graphics are ALSO
 * decorative. The manual's tip/idea icons (e.g. the 384×384 lightbulb-with-gear
 * "idea" graphic, checksum 6c0bd5c2…) are exported at ~1:1 and slip past the
 * OD-1 `min < 64` rule, which only catches tiny glyphs (e.g. the 93×62 Excel
 * file-link icon). In the Drive manuals every real content figure is a landscape
 * UI screenshot (aspect ≥ ~1.3); a small-to-medium image (≤ `SQUARE_MAX_PX` on
 * its long edge) that is near-square (aspect ≤ `MAX_ASPECT`) is therefore an
 * icon, not a figure. Thresholds are deliberately tight — the closest real
 * screenshot observed is 778×604 (aspect 1.29), well clear of 1.15 — so no
 * genuine screenshot is dropped. Only applied when dims are KNOWN (>0).
 */
export const DECORATIVE_SQUARE_MAX_PX = 512;
export const DECORATIVE_MAX_ASPECT = 1.15;

function isDecorativeImage(image: ImageRef): boolean {
  if (image.width <= 0 || image.height <= 0) return false; // unknown dims — never judged
  const minDim = Math.min(image.width, image.height);
  const maxDim = Math.max(image.width, image.height);
  if (minDim < DECORATIVE_MIN_PX) return true; // OD-1 — tiny icon / thin strip
  // OD-4 — large near-square graphic (the high-res tip/idea icons)
  return maxDim <= DECORATIVE_SQUARE_MAX_PX && maxDim / minDim <= DECORATIVE_MAX_ASPECT;
}

export interface DedupedCitationImage {
  /** The first citation (in citation order) that references this image. */
  citation: Citation;
  image: ImageRef;
  /**
   * 1-based position of `citation` in the full citations array — used for the
   * numeric badge / "Citation [N]" caption so it matches CitationPill /
   * SourcesStrip / ScreenshotModal numbering (all anchor on full-citations
   * position, per BUG-024).
   */
  citationIdx: number;
}

/**
 * Flatten citations into a list of unique images, deduped by `checksum_sha256`
 * (fallback `blob_url`). Each unique image is attributed to the first citation
 * that references it. Images with neither a checksum nor a blob_url are skipped
 * (no stable identity to render or dedup on).
 */
export function dedupeCitationImages(citations: Citation[]): DedupedCitationImage[] {
  const seen = new Set<string>();
  const out: DedupedCitationImage[] = [];
  citations.forEach((citation, idx) => {
    for (const image of citation.embedded_images) {
      const key = image.checksum_sha256 || image.blob_url;
      if (!key) continue; // no stable identity — skip
      if (isDecorativeImage(image)) continue; // CH-009 OD-1 — drop decorative icons at display
      if (seen.has(key)) continue; // already shown under an earlier citation
      seen.add(key);
      out.push({ citation, image, citationIdx: idx + 1 });
    }
  });
  // BUG-034 Finding D — render screenshots in DOCUMENT order (the image's own
  // section_path) instead of citation/relevance order. A procedural query like
  // "how do I post a journal entry" reranks the literal "Post" sub-step (§3.1.5,
  // ~p31) above the "Create General Journal" start (§3.1.3, ~p20-28), so the
  // gallery used to LEAD with the wrong (later) step. Ordering by section makes
  // it read start→end (Create → Approve → Post), matching the manual's flow.
  // Attribution + numeric badge (citationIdx) still anchor on citation position —
  // only the render order changes. Lexical section compare suffices for Tier 1
  // manuals (single-digit sub-sections); the sort is stable so same-section
  // images keep their original (citation) order.
  // CH-011 / ADR-0048 — the section sort above reads start->end ACROSS sections but
  // CANNOT page-order WITHIN one section (every step figure shares one source_section,
  // so they fell back to neighbour-attach nearest-first order — the figure-3+ scramble).
  // Per-image `doc_order` (parser monotonic document position) is the PRIMARY key:
  // when every image carries a real doc_order (KB re-indexed under CH-011), sort by it
  // for exact reading flow (also fixes the multi-digit sub-section lexical bug). When
  // any image lacks it (pre-CH-011 / not re-indexed / legacy stored conversation), fall
  // back to the section sort so behaviour is bit-identical to pre-CH-011. Mode is decided
  // ONCE (not per-pair) to keep the comparator transitive; the sort is stable so ties
  // keep citation order.
  const allHaveDocOrder = out.every((d) => (d.image.doc_order ?? 0) > 0);
  out.sort((a, b) => {
    if (allHaveDocOrder) {
      const da = a.image.doc_order ?? 0;
      const db = b.image.doc_order ?? 0;
      if (da !== db) return da - db;
    }
    const ka = imageSectionPath(a.image, a.citation).join(' ');
    const kb = imageSectionPath(b.image, b.citation).join(' ');
    return ka < kb ? -1 : ka > kb ? 1 : 0;
  });
  return out;
}

/**
 * CH-009 / ADR-0046 (OD-2) — choose the inline images: the first `cap` in
 * DOCUMENT order. `deduped` is already document-sorted (BUG-034 Finding D), so a
 * procedure leads with its overview/start figures (e.g. §3.1.1 High Level Process)
 * rather than a mid-procedure step. `cap` = per-KB `max_images_per_answer` (null →
 * caller default, e.g. INLINE_IMAGE_CAP); overflow stays in "View all in Image
 * Library". (OD-3 relevance-select was reverted 2026-06-08 — for procedural
 * manuals the document-order overview-first read is what the user expects; the
 * low-rerank-score chapter overview must not be dropped from the cap.)
 */
export function selectInlineImages(
  deduped: DedupedCitationImage[],
  cap: number,
): DedupedCitationImage[] {
  if (cap <= 0) return [];
  return deduped.slice(0, cap);
}

/** A surviving image placed in the answer, with its 1-based figure number. */
export interface PlacedImage {
  entry: DedupedCitationImage;
  figureIdx: number;
}

/**
 * W71 (ADR-0055) — partition the surviving (capped) images into the ones
 * anchored inline at an `[IMG#<sha8>]` marker in the answer and the ones left
 * for the trailing pile.
 *
 * - `inlineBySha8` maps a marker's sha8 → the image to render at that position
 *   (the chat's `AnswerBodyMarkdown` injects an `InlineImageCard` there);
 * - `trailing` is the surviving images with NO anchored marker, rendered as the
 *   end-of-answer pile (per ADR-0055 an anchored image does NOT repeat there).
 *
 * Figure numbers run continuously across the answer: anchored first, in marker
 * order, then trailing, in document order. Membership + first-occurrence dedup
 * come from `parseInlineImageMarkers` (the single source of truth shared with
 * the render). Images without a checksum can't be anchored (no marker can
 * reference them) and always fall to `trailing`.
 */
export interface AnchoredImagePlan {
  inlineBySha8: Map<string, PlacedImage>;
  trailing: PlacedImage[];
}

export function planAnchoredImages(
  content: string,
  capped: DedupedCitationImage[],
): AnchoredImagePlan {
  const bySha8 = new Map<string, DedupedCitationImage>();
  for (const entry of capped) {
    const key = imageMarkerKey(entry.image.checksum_sha256);
    if (key && !bySha8.has(key)) bySha8.set(key, entry);
  }
  const segments = parseInlineImageMarkers(content, new Set(bySha8.keys()));
  const anchoredOrder = segments.flatMap((s) => (s.type === 'image' ? [s.sha8] : []));
  const anchoredSet = new Set(anchoredOrder);

  const inlineBySha8 = new Map<string, PlacedImage>();
  anchoredOrder.forEach((sha8, i) => {
    inlineBySha8.set(sha8, { entry: bySha8.get(sha8)!, figureIdx: i + 1 });
  });
  const trailing: PlacedImage[] = capped
    .filter((entry) => {
      const key = imageMarkerKey(entry.image.checksum_sha256);
      return !key || !anchoredSet.has(key);
    })
    .map((entry, i) => ({ entry, figureIdx: anchoredOrder.length + i + 1 }));

  return { inlineBySha8, trailing };
}

/**
 * The section an image should be attributed to (BUG-026 C-ii). Prefers the
 * image's OWN section (`source_section`, propagated from its owning chunk at
 * ingest) so a neighbour-attached image shows ITS section rather than the
 * citing intro/meta chunk's. Falls back to the citing chunk's `section_path`
 * for images indexed before C-ii (empty / absent `source_section`).
 */
export function imageSectionPath(image: ImageRef, citation: Citation): string[] {
  return image.source_section && image.source_section.length > 0
    ? image.source_section
    : citation.section_path;
}

/** W83 (ADR-0064) — a trailing-pile group whose images share one section. */
export interface TrailingSectionGroup {
  /** The shared section_path (image's own source_section, citing fallback). */
  sectionPath: string[];
  /** Display label = the section leaf (deepest heading), or 'Other' when empty. */
  sectionLabel: string;
  /** The group's trailing images, in their original (document) order. */
  items: PlacedImage[];
}

/**
 * W83 (ADR-0064) — group the trailing (non-anchored) images by the section they
 * visually belong to (`imageSectionPath`), so the end-of-answer pile renders as a
 * labelled "section appendix" (each image knows its step-chapter) instead of one
 * undifferentiated wall of screenshots.
 *
 * Why (root cause, verified 2026-06-16 on drive-images-1): a "per-field
 * screenshot" manual section (FA §2.1.3 — 633 chars / ~12 steps but 47 field
 * screenshots) has FAR more images than the answer has step sentences to anchor
 * [IMG#] markers at, so ~35 field screenshots fall to the trailing pile with no
 * surrounding text. Grouping by section gives each a chapter heading.
 *
 * Group order follows first appearance in `trailing` (already document-ordered by
 * `dedupeCitationImages`), so groups read start→end; items keep their order WITHIN
 * a group. `figureIdx` is NOT touched — the continuous inline→trailing numbering is
 * preserved; this only partitions the render. Returns [] for empty trailing, so a
 * marker-less / fully-anchored answer renders the same (zero groups) as pre-W83.
 *
 * Pure function; no IO; testable in isolation without mocks.
 */
export function groupTrailingBySection(trailing: PlacedImage[]): TrailingSectionGroup[] {
  const groups: TrailingSectionGroup[] = [];
  const byKey = new Map<string, TrailingSectionGroup>();
  for (const placed of trailing) {
    const sectionPath = imageSectionPath(placed.entry.image, placed.entry.citation);
    const key = sectionPath.join(' / ');
    let group = byKey.get(key);
    if (!group) {
      const leaf = sectionPath.length > 0 ? sectionPath[sectionPath.length - 1] : '';
      group = { sectionPath, sectionLabel: leaf || 'Other', items: [] };
      byKey.set(key, group);
      groups.push(group);
    }
    group.items.push(placed);
  }
  return groups;
}

/**
 * The best human label for an image (BUG-026). Prefers the real figure caption
 * (`alt_text`), then the leaf of the image's own section (C-ii — so distinct
 * images under one citation no longer collapse to the same chunk label), then
 * the citing chunk's title.
 */
export function imageTitle(image: ImageRef, citation: Citation): string {
  if (image.alt_text) return image.alt_text;
  const section = imageSectionPath(image, citation);
  const leaf = section.length > 0 ? section[section.length - 1] : '';
  return leaf || citation.chunk_title || 'Screenshot';
}

/**
 * Format a citation relevance score for display (BUG-034 Finding C).
 *
 * Citation post-hoc expansion (backend §3.7 citation_expansion.py) materializes
 * neighbour citations with a sentinel `relevance_score` of 0 — they were added
 * for context completeness, never independently reranked. Rendering that as
 * "0.000" reads as "zero relevance / broken" next to a genuinely-reranked
 * sibling in the same section. Show an em-dash for the sentinel instead; a real
 * Cohere rerank score is effectively never exactly 0, so `score > 0` reliably
 * distinguishes reranked hits from expansion neighbours.
 */
export function formatRelevance(score: number): string {
  return score > 0 ? score.toFixed(3) : '—';
}
