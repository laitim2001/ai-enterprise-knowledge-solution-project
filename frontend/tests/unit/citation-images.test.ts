/**
 * Unit test — dedupeCitationImages (BUG-026 Finding A).
 *
 * Proves the cross-citation image dedup: when the same image (same
 * checksum_sha256) is referenced by more than one citation — as happens when
 * `attach_neighbour_images` attaches a §X.1 figure to both the §X.1 chunk and
 * the §X intro chunk — it appears exactly once in the flattened render list,
 * attributed to the first citation in citation order.
 */
import { describe, expect, it } from 'vitest';

import type { Citation, ImageRef } from '@/lib/api/query';
import { dedupeCitationImages } from '@/lib/chat/citation-images';

function imageRef(over: Partial<ImageRef> = {}): ImageRef {
  return {
    blob_url: 'https://blob.example/shot.png',
    alt_text: 'shot',
    checksum_sha256: 'sha-default',
    width: 800,
    height: 480,
    ...over,
  };
}

function citation(idx: number, images: ImageRef[]): Citation {
  return {
    chunk_id: `chunk-${idx}`,
    doc_id: `doc-${idx}.docx`,
    doc_title: `Document ${idx}`,
    doc_format: 'docx',
    chunk_title: `Section ${idx}`,
    chunk_index: idx,
    section_path: ['A', 'B'],
    relevance_score: 0.9,
    embedded_images: images,
  };
}

describe('dedupeCitationImages (BUG-026 Finding A)', () => {
  it('dedups the same image across citations, keeping the first occurrence', () => {
    const shared = imageRef({ checksum_sha256: 'sha-shared' });
    const result = dedupeCitationImages([
      citation(1, [shared]), // §8 intro — neighbour-attached
      citation(2, [imageRef({ ...shared })]), // §8.1 — direct image, same checksum
    ]);

    expect(result).toHaveLength(1);
    // Attributed to the FIRST citation (citation order), not the later one.
    expect(result[0]!.citation.chunk_id).toBe('chunk-1');
    expect(result[0]!.citationIdx).toBe(1);
  });

  it('keeps distinct images and assigns full-citation badge indices', () => {
    const result = dedupeCitationImages([
      citation(1, [imageRef({ checksum_sha256: 'sha-a' })]),
      citation(2, []), // no image — must not shift the badge of later images
      citation(3, [imageRef({ checksum_sha256: 'sha-b' })]),
    ]);

    expect(result).toHaveLength(2);
    expect(result.map((r) => r.image.checksum_sha256)).toEqual(['sha-a', 'sha-b']);
    // citationIdx anchors on the FULL citations array position (1-based), so
    // the §3 image's badge is 3 even though it is the 2nd image rendered.
    expect(result.map((r) => r.citationIdx)).toEqual([1, 3]);
  });

  it('keeps multiple distinct images within one citation', () => {
    const result = dedupeCitationImages([
      citation(1, [imageRef({ checksum_sha256: 'sha-x' }), imageRef({ checksum_sha256: 'sha-y' })]),
    ]);

    expect(result).toHaveLength(2);
    expect(result.every((r) => r.citationIdx === 1)).toBe(true);
  });

  it('falls back to blob_url for dedup when checksum is absent', () => {
    const result = dedupeCitationImages([
      citation(1, [imageRef({ checksum_sha256: '', blob_url: 'https://blob/x.png' })]),
      citation(2, [imageRef({ checksum_sha256: '', blob_url: 'https://blob/x.png' })]),
    ]);

    expect(result).toHaveLength(1);
    expect(result[0]!.citation.chunk_id).toBe('chunk-1');
  });

  it('skips images with neither checksum nor blob_url (no stable identity)', () => {
    const result = dedupeCitationImages([
      citation(1, [imageRef({ checksum_sha256: '', blob_url: '' })]),
    ]);

    expect(result).toHaveLength(0);
  });

  it('returns an empty list when no citation carries images', () => {
    const result = dedupeCitationImages([citation(1, []), citation(2, [])]);
    expect(result).toEqual([]);
  });
});
