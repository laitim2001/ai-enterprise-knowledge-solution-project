/**
 * Unit tests — BUG-034 Finding C (citation relevance display).
 *
 * Expansion-added neighbour citations carry a sentinel relevance_score of 0.
 * formatRelevance must render that as an em-dash (not a misleading "0.000")
 * while showing real reranked scores to 3 decimals.
 */

import { describe, expect, it } from 'vitest';
import { formatRelevance } from '@/lib/chat/citation-images';

describe('BUG-034 Finding C — formatRelevance', () => {
  it('renders an em-dash for the expansion sentinel score of 0', () => {
    expect(formatRelevance(0)).toBe('—');
  });

  it('renders a real reranked score to 3 decimals', () => {
    expect(formatRelevance(0.091)).toBe('0.091');
    expect(formatRelevance(0.899)).toBe('0.899');
    expect(formatRelevance(1)).toBe('1.000');
  });

  it('treats a tiny positive score as a real score (not the sentinel)', () => {
    expect(formatRelevance(0.0004)).toBe('0.000'); // rounds to 0.000 but is a real, non-sentinel score
    expect(formatRelevance(0.001)).toBe('0.001');
  });
});
