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
 * the image count all draw from one consistent deduped list.
 *
 * The mockup (ekp-page-chat.jsx:621-664) never shows the same screenshot twice,
 * so deduping moves the implementation closer to the mockup (a reverse-direction
 * drift fix, not an H7 deviation per CLAUDE.md §5.7).
 */
import type { Citation, ImageRef } from '@/lib/api/query';

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
      if (seen.has(key)) continue; // already shown under an earlier citation
      seen.add(key);
      out.push({ citation, image, citationIdx: idx + 1 });
    }
  });
  return out;
}
