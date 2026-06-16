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
  groupTrailingBySection,
  imageSectionPath,
  imageTitle,
  planAnchoredImages,
  selectInlineImages,
  type DedupedCitationImage,
  type PlacedImage,
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
        source_section: [
          '3 GL03. Processing Journal Vouchers',
          '3.1.5 System Instruction for each step',
        ],
      }),
    ]);
    const create = citation(2, [
      imageRef({
        checksum_sha256: 'sha-create',
        source_section: [
          '3 GL03. Processing Journal Vouchers',
          '3.1.3 System Instruction for each step',
        ],
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

describe('dedupeCitationImages — within-section page order (CH-011 / ADR-0048)', () => {
  const STEP_SECTION = [
    '3 GL03. Processing Journal Vouchers',
    '3.1.3 System Instruction for each step',
  ];

  it('page-orders images WITHIN one section by doc_order (the figure-3+ scramble fix)', () => {
    // All three step figures share ONE source_section, so the lexical section sort
    // cannot disambiguate them — neighbour-attach delivered them out of page order.
    // doc_order restores true reading order regardless of input order.
    const result = dedupeCitationImages([
      citation(1, [
        imageRef({ checksum_sha256: 'import-p24', source_section: STEP_SECTION, doc_order: 30 }),
        imageRef({ checksum_sha256: 'step1-p21', source_section: STEP_SECTION, doc_order: 25 }),
        imageRef({ checksum_sha256: 'step2-p22', source_section: STEP_SECTION, doc_order: 27 }),
      ]),
    ]);
    expect(result.map((r) => r.image.checksum_sha256)).toEqual([
      'step1-p21',
      'step2-p22',
      'import-p24',
    ]);
  });

  it('orders across sections by doc_order too (overview leads the procedure)', () => {
    const OVERVIEW = ['3 GL03. Processing Journal Vouchers', '3.1.1 Overview'];
    const result = dedupeCitationImages([
      citation(1, [
        imageRef({ checksum_sha256: 'step', source_section: STEP_SECTION, doc_order: 27 }),
      ]),
      citation(2, [
        imageRef({ checksum_sha256: 'overview', source_section: OVERVIEW, doc_order: 24 }),
      ]),
    ]);
    // doc_order 24 (overview) < 27 (step) → overview leads.
    expect(result.map((r) => r.image.checksum_sha256)).toEqual(['overview', 'step']);
  });

  it('falls back to source_section order when any image lacks doc_order (production-preserve)', () => {
    // Mixed (e.g. legacy stored conversation): one image has doc_order, one does not →
    // mode resolves to legacy section sort, transitive + no crash.
    const STEP_5 = ['3', '3.1.5 step'];
    const STEP_3 = ['3', '3.1.3 step'];
    const result = dedupeCitationImages([
      citation(1, [imageRef({ checksum_sha256: 'late', source_section: STEP_5, doc_order: 5 })]),
      citation(2, [imageRef({ checksum_sha256: 'early', source_section: STEP_3 })]), // no doc_order
    ]);
    // allHaveDocOrder=false → section lexical: 3.1.3 (early) before 3.1.5 (late).
    expect(result.map((r) => r.image.checksum_sha256)).toEqual(['early', 'late']);
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

describe('dedupeCitationImages — large near-square icon filter (CH-009 / ADR-0046 OD-4)', () => {
  it('drops the 384×384 lightbulb/idea icon (square, ≤512px) that slips past OD-1', () => {
    // Real-world repro: sha 6c0bd5c2 in drive-images-1 — the lightbulb-with-gear
    // "idea" graphic. min(384,384)=384 ≥ 64 so OD-1 keeps it; OD-4 catches it.
    const result = dedupeCitationImages([
      citation(1, [
        imageRef({ checksum_sha256: 'shot', width: 836, height: 329 }),
        imageRef({ checksum_sha256: 'lightbulb', width: 384, height: 384 }),
      ]),
    ]);
    expect(result.map((r) => r.image.checksum_sha256)).toEqual(['shot']);
  });

  it('keeps a real landscape screenshot just above the aspect threshold (778×604, aspect 1.29)', () => {
    const result = dedupeCitationImages([
      citation(1, [imageRef({ checksum_sha256: 'real-near-square', width: 778, height: 604 })]),
    ]);
    expect(result).toHaveLength(1);
  });

  it('keeps a large square content diagram (>512px — only small near-square icons are dropped)', () => {
    const result = dedupeCitationImages([
      citation(1, [imageRef({ checksum_sha256: 'big-diagram', width: 1024, height: 1024 })]),
    ]);
    expect(result).toHaveLength(1);
  });

  it('keeps a 512×512 image at the size ceiling but drops a 384×384 below it', () => {
    const result = dedupeCitationImages([
      citation(1, [
        imageRef({ checksum_sha256: 'ceiling', width: 600, height: 520 }), // maxDim 600 > 512 → kept
        imageRef({ checksum_sha256: 'icon', width: 384, height: 384 }), // square + ≤512 → dropped
      ]),
    ]);
    expect(result.map((r) => r.image.checksum_sha256)).toEqual(['ceiling']);
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

describe('planAnchoredImages (W71 — ADR-0055 interleave partition)', () => {
  // Build a deduped entry directly (the caller already deduped + capped).
  function placed(checksum: string, citationIdx = 1): DedupedCitationImage {
    const image = imageRef({ checksum_sha256: checksum });
    return { citation: citation(citationIdx, [image]), image, citationIdx };
  }

  it('anchors nothing when the answer has no markers — all images trail, figures 1..n', () => {
    const capped = [placed('aaaaaaaa1111'), placed('bbbbbbbb2222')];
    const plan = planAnchoredImages('Plain answer, no markers.', capped);
    expect(plan.inlineBySha8.size).toBe(0);
    expect(plan.trailing.map((p) => [p.entry.image.checksum_sha256, p.figureIdx])).toEqual([
      ['aaaaaaaa1111', 1],
      ['bbbbbbbb2222', 2],
    ]);
  });

  it('anchors a marker by its sha8 prefix and leaves the rest trailing', () => {
    const capped = [placed('aaaaaaaa1111'), placed('bbbbbbbb2222')];
    const plan = planAnchoredImages('Step. [IMG#aaaaaaaa] done.', capped);
    expect([...plan.inlineBySha8.keys()]).toEqual(['aaaaaaaa']);
    expect(plan.inlineBySha8.get('aaaaaaaa')!.figureIdx).toBe(1);
    // the un-anchored image trails, numbered AFTER the anchored one
    expect(plan.trailing.map((p) => [p.entry.image.checksum_sha256, p.figureIdx])).toEqual([
      ['bbbbbbbb2222', 2],
    ]);
  });

  it('numbers anchored figures by MARKER order, not capped order', () => {
    const capped = [placed('aaaaaaaa1111'), placed('bbbbbbbb2222')];
    // marker for b comes first in the text → b is figure 1, a is figure 2
    const plan = planAnchoredImages('[IMG#bbbbbbbb] then [IMG#aaaaaaaa]', capped);
    expect(plan.inlineBySha8.get('bbbbbbbb')!.figureIdx).toBe(1);
    expect(plan.inlineBySha8.get('aaaaaaaa')!.figureIdx).toBe(2);
    expect(plan.trailing).toEqual([]);
  });

  it('anchors a repeated marker at most once (no double card)', () => {
    const capped = [placed('aaaaaaaa1111')];
    const plan = planAnchoredImages('[IMG#aaaaaaaa] x [IMG#aaaaaaaa]', capped);
    expect(plan.inlineBySha8.size).toBe(1);
    expect(plan.trailing).toEqual([]);
  });

  it('ignores a marker whose sha8 is not among the surviving images', () => {
    const capped = [placed('aaaaaaaa1111')];
    const plan = planAnchoredImages('[IMG#deadbeef] stray', capped);
    expect(plan.inlineBySha8.size).toBe(0);
    // the real image still trails (figure 1 — nothing anchored before it)
    expect(plan.trailing.map((p) => p.figureIdx)).toEqual([1]);
  });

  it('keeps a checksum-less image in the trailing pile (can never be anchored)', () => {
    const noChecksum: DedupedCitationImage = {
      citation: citation(1, []),
      image: imageRef({ checksum_sha256: '', blob_url: 'https://blob/x.png' }),
      citationIdx: 1,
    };
    const plan = planAnchoredImages('[IMG#aaaaaaaa]', [placed('aaaaaaaa1111'), noChecksum]);
    expect(plan.inlineBySha8.size).toBe(1);
    expect(plan.trailing).toHaveLength(1);
    expect(plan.trailing[0]!.entry.image.blob_url).toBe('https://blob/x.png');
    expect(plan.trailing[0]!.figureIdx).toBe(2); // continues after the anchored figure 1
  });

  it('numbers figures continuously across anchored then trailing', () => {
    const capped = [placed('aaaaaaaa1111'), placed('bbbbbbbb2222'), placed('cccccccc3333')];
    const plan = planAnchoredImages('only [IMG#bbbbbbbb] anchored', capped);
    expect(plan.inlineBySha8.get('bbbbbbbb')!.figureIdx).toBe(1);
    // the two un-anchored images get 2 and 3, in capped order
    expect(plan.trailing.map((p) => [p.entry.image.checksum_sha256, p.figureIdx])).toEqual([
      ['aaaaaaaa1111', 2],
      ['cccccccc3333', 3],
    ]);
  });
});

describe('groupTrailingBySection (W83 — ADR-0064 trailing section grouping)', () => {
  // A trailing PlacedImage: a deduped image carried at a continuous figure index.
  function placedImg(
    sha: string,
    section: string[],
    figureIdx: number,
    citationIdx = 1,
  ): PlacedImage {
    const image = imageRef({ checksum_sha256: sha, source_section: section });
    return { entry: { citation: citation(citationIdx, [image]), image, citationIdx }, figureIdx };
  }

  const FA_3 = ['2 FA01. Fixed Asset Registration', '2.1.3 System Instruction for each step'];
  const FA_4 = ['2 FA01. Fixed Asset Registration', '2.1.4 System Instruction for each step'];

  it('returns an empty list for empty trailing (marker-less / fully-anchored = pre-W83)', () => {
    expect(groupTrailingBySection([])).toEqual([]);
  });

  it('groups one section into a single group, items in order', () => {
    const groups = groupTrailingBySection([
      placedImg('a', FA_3, 1),
      placedImg('b', FA_3, 2),
      placedImg('c', FA_3, 3),
    ]);
    expect(groups).toHaveLength(1);
    expect(groups[0]!.sectionLabel).toBe('2.1.3 System Instruction for each step');
    expect(groups[0]!.items.map((p) => p.entry.image.checksum_sha256)).toEqual(['a', 'b', 'c']);
  });

  it('splits distinct sections into groups in first-appearance (document) order', () => {
    const groups = groupTrailingBySection([
      placedImg('a3', FA_3, 1),
      placedImg('b3', FA_3, 2),
      placedImg('a4', FA_4, 3),
    ]);
    expect(groups.map((g) => g.sectionLabel)).toEqual([
      '2.1.3 System Instruction for each step',
      '2.1.4 System Instruction for each step',
    ]);
    expect(groups[0]!.items.map((p) => p.entry.image.checksum_sha256)).toEqual(['a3', 'b3']);
    expect(groups[1]!.items.map((p) => p.entry.image.checksum_sha256)).toEqual(['a4']);
  });

  it('groups by section identity, not contiguous run (a re-appearing section rejoins)', () => {
    // trailing is document-ordered so interleaving is rare, but grouping must key on
    // section identity — a §2.1.3 image after a §2.1.4 image rejoins the §2.1.3 group.
    const groups = groupTrailingBySection([
      placedImg('a3', FA_3, 1),
      placedImg('a4', FA_4, 2),
      placedImg('b3', FA_3, 3),
    ]);
    expect(groups).toHaveLength(2);
    expect(groups[0]!.sectionLabel).toBe('2.1.3 System Instruction for each step');
    expect(groups[0]!.items.map((p) => p.entry.image.checksum_sha256)).toEqual(['a3', 'b3']);
  });

  it('preserves figureIdx unchanged (continuous inline→trailing numbering)', () => {
    // Anchored figures took 1-2; trailing starts at 3 — grouping must not renumber.
    const groups = groupTrailingBySection([placedImg('a', FA_3, 3), placedImg('b', FA_4, 4)]);
    expect(groups.flatMap((g) => g.items.map((p) => p.figureIdx))).toEqual([3, 4]);
  });

  it('exposes the full sectionPath + leaf label', () => {
    const groups = groupTrailingBySection([placedImg('a', FA_3, 1)]);
    expect(groups[0]!.sectionPath).toEqual(FA_3);
    expect(groups[0]!.sectionLabel).toBe('2.1.3 System Instruction for each step');
  });

  it("falls back to 'Other' label when the image has no section signal (defensive)", () => {
    const image = imageRef({ checksum_sha256: 'x', source_section: [] });
    const cit = citation(1, [image]);
    cit.section_path = []; // source_section empty AND citing chunk section empty
    const groups = groupTrailingBySection([
      { entry: { citation: cit, image, citationIdx: 1 }, figureIdx: 1 },
    ]);
    expect(groups).toHaveLength(1);
    expect(groups[0]!.sectionLabel).toBe('Other');
  });
});
