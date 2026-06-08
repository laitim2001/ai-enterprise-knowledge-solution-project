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
import {
  DECORATIVE_MIN_PX,
  dedupeCitationImages,
  imageSectionPath,
  imageTitle,
  selectInlineImages,
} from '@/lib/chat/citation-images';

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

  it('orders images by document position, not citation/relevance order (BUG-034 Finding D)', () => {
    // Reranker put "Post" (§3.1.5) as citation 1 and "Create" (§3.1.3) as citation 2.
    const post = citation(1, [
      imageRef({
        checksum_sha256: 'sha-post',
        source_section: ['3 GL03. Processing Journal Vouchers', '3.1.5 System Instruction for each step'],
      }),
    ]);
    const create = citation(2, [
      imageRef({
        checksum_sha256: 'sha-create',
        source_section: ['3 GL03. Processing Journal Vouchers', '3.1.3 System Instruction for each step'],
      }),
    ]);
    const result = dedupeCitationImages([post, create]);
    // Rendered in DOCUMENT order: Create (§3.1.3) before Post (§3.1.5).
    expect(result.map((r) => r.image.checksum_sha256)).toEqual(['sha-create', 'sha-post']);
    // …but the numeric badge still reflects citation position (Create was citation 2).
    expect(result.find((r) => r.image.checksum_sha256 === 'sha-create')!.citationIdx).toBe(2);
    expect(result.find((r) => r.image.checksum_sha256 === 'sha-post')!.citationIdx).toBe(1);
  });

  it('keeps same-section images in their original (citation) order — stable sort', () => {
    const sameSection = ['3 GL03', '3.1.3 System Instruction for each step'];
    const result = dedupeCitationImages([
      citation(1, [imageRef({ checksum_sha256: 'sha-1', source_section: sameSection })]),
      citation(2, [imageRef({ checksum_sha256: 'sha-2', source_section: sameSection })]),
    ]);
    expect(result.map((r) => r.image.checksum_sha256)).toEqual(['sha-1', 'sha-2']);
  });
});

describe('dedupeCitationImages — decorative filter (CH-009 / ADR-0046 OD-1)', () => {
  it('drops a decorative icon (min dim < threshold) when dims are known', () => {
    const result = dedupeCitationImages([
      citation(1, [
        imageRef({ checksum_sha256: 'real', width: 800, height: 480 }),
        imageRef({ checksum_sha256: 'icon', width: 32, height: 32 }), // lightbulb-style icon
      ]),
    ]);
    expect(result.map((r) => r.image.checksum_sha256)).toEqual(['real']);
  });

  it('drops a tall-thin decorative strip (one dim < threshold)', () => {
    const result = dedupeCitationImages([
      citation(1, [imageRef({ checksum_sha256: 'strip', width: 600, height: 20 })]),
    ]);
    expect(result).toHaveLength(0);
  });

  it('keeps images with unknown dims (0×0 — pre-re-index data, cannot judge)', () => {
    const result = dedupeCitationImages([
      citation(1, [imageRef({ checksum_sha256: 'legacy', width: 0, height: 0 })]),
    ]);
    expect(result).toHaveLength(1);
  });

  it('keeps an image exactly at the threshold (>= is not decorative)', () => {
    const result = dedupeCitationImages([
      citation(1, [imageRef({ checksum_sha256: 'edge', width: DECORATIVE_MIN_PX, height: 200 })]),
    ]);
    expect(result).toHaveLength(1);
  });
});

describe('selectInlineImages — document-order cap (CH-009 / ADR-0046 OD-2; OD-3 reverted)', () => {
  // Helper: a citation with a single image in a given section (relevance kept on
  // the model but NOT used for selection — OD-3 relevance-select reverted 2026-06-08).
  function cit(idx: number, relevance: number, sha: string, section: string[]): Citation {
    return {
      chunk_id: `chunk-${idx}`,
      doc_id: 'doc.docx',
      doc_title: 'Doc',
      doc_format: 'docx',
      chunk_title: `S${idx}`,
      chunk_index: idx,
      section_path: section,
      relevance_score: relevance,
      embedded_images: [imageRef({ checksum_sha256: sha, source_section: section })],
    };
  }

  it('returns the full list (document order) when count <= cap', () => {
    const deduped = dedupeCitationImages([
      cit(1, 0.9, 'a', ['3', '3.1.5']),
      cit(2, 0.5, 'b', ['3', '3.1.3']),
    ]);
    const selected = selectInlineImages(deduped, 8);
    // document order: 3.1.3 (b) before 3.1.5 (a) — NOT relevance order.
    expect(selected.map((d) => d.image.checksum_sha256)).toEqual(['b', 'a']);
  });

  it('takes the first `cap` in DOCUMENT order — low-rerank overview leads, not the high-score step', () => {
    // The §3.1.1 chapter overview has a LOW (0) rerank score but must still lead
    // the procedure (the user-reported regression: relevance-select buried it).
    const deduped = dedupeCitationImages([
      cit(1, 0.0, 'overview', ['3', '3.1.1']), // earliest section, score 0
      cit(2, 0.9, 'step5', ['3', '3.1.5']), // latest section, highest score
      cit(3, 0.8, 'step3', ['3', '3.1.3']), // middle section
    ]);
    const selected = selectInlineImages(deduped, 2);
    // first 2 in document order = overview (§3.1.1) + step3 (§3.1.3); step5 overflows.
    expect(selected.map((d) => d.image.checksum_sha256)).toEqual(['overview', 'step3']);
  });

  it('returns empty for cap <= 0', () => {
    const deduped = dedupeCitationImages([cit(1, 0.9, 'a', ['3', '3.1.1'])]);
    expect(selectInlineImages(deduped, 0)).toEqual([]);
  });
});

describe('imageSectionPath (BUG-026 C-ii)', () => {
  it("prefers the image's own source_section over the citing chunk's section", () => {
    // §8.4 figure neighbour-attached to the §8 intro citation: must show §8.4.
    const intro = citation(1, []);
    intro.section_path = ['8. Integration scenarios'];
    const image = imageRef({
      source_section: ['8. Integration scenarios', '8.4 Scenario D'],
    });
    expect(imageSectionPath(image, intro)).toEqual(['8. Integration scenarios', '8.4 Scenario D']);
  });

  it('falls back to the citing chunk section when source_section is absent', () => {
    const cit = citation(1, []);
    cit.section_path = ['3. Architectural principles', '3.7 Idempotency'];
    const image = imageRef({ source_section: undefined });
    expect(imageSectionPath(image, cit)).toEqual([
      '3. Architectural principles',
      '3.7 Idempotency',
    ]);
  });

  it('falls back to the citing chunk section when source_section is empty', () => {
    const cit = citation(1, []);
    cit.section_path = ['X'];
    expect(imageSectionPath(imageRef({ source_section: [] }), cit)).toEqual(['X']);
  });
});

describe('imageTitle (BUG-026)', () => {
  it('prefers the real figure caption (alt_text) when present', () => {
    const image = imageRef({
      alt_text: 'Figure 1: High-level integration architecture',
      source_section: ['4. High-level architecture'],
    });
    expect(imageTitle(image, citation(1, []))).toBe(
      'Figure 1: High-level integration architecture',
    );
  });

  it("uses the image's own section leaf when alt_text is empty (C-ii)", () => {
    // Two distinct images under one citation no longer collapse to one label.
    const cit = citation(1, []);
    cit.chunk_title = '8. Integration scenarios';
    const a = imageRef({
      alt_text: '',
      source_section: ['8. Integration scenarios', '8.4 Scenario D'],
    });
    const b = imageRef({
      alt_text: '',
      source_section: ['8. Integration scenarios', '8.5 Scenario E'],
    });
    expect(imageTitle(a, cit)).toBe('8.4 Scenario D');
    expect(imageTitle(b, cit)).toBe('8.5 Scenario E');
  });

  it('falls back to the citing chunk title when no caption and no section', () => {
    const cit = citation(1, []);
    cit.chunk_title = 'Section 7';
    cit.section_path = [];
    expect(imageTitle(imageRef({ alt_text: '', source_section: [] }), cit)).toBe('Section 7');
  });
});
