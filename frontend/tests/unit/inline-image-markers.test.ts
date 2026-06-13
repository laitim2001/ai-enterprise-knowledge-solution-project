/**
 * Unit tests — W70/W71 (ADR-0055) — inline image markers for the answer
 * display layer (`lib/chat/inline-image-markers.ts`).
 *
 * W70 strip path: `[IMG#<sha8>]` markers removed before markdown render; while
 * streaming a trailing PARTIAL marker is held back so fragments never flash.
 * W71 parse path: the same markers split the final answer into text / image
 * segments for the interleaved render, with membership + dedup validation.
 */

import { describe, expect, it } from 'vitest';

import {
  imageMarkerKey,
  parseInlineImageMarkers,
  stripInlineImageMarkers,
  type InlineSegment,
} from '@/lib/chat/inline-image-markers';

describe('W70 — stripInlineImageMarkers (complete markers)', () => {
  it('strips a single inline marker', () => {
    expect(stripInlineImageMarkers('Click Save. [IMG#a1b2c3d4] Then close.')).toBe(
      'Click Save.  Then close.',
    );
  });

  it('strips multiple markers including paragraph-standalone ones', () => {
    const text = 'Step 1. [IMG#a1b2c3d4]\n\n[IMG#b2c3d4e5]\n\nStep 2. [IMG#c3d4e5f6]';
    const out = stripInlineImageMarkers(text);
    expect(out).not.toContain('[IMG#');
    expect(out).toContain('Step 1.');
    expect(out).toContain('Step 2.');
  });

  it('strips malformed marker bodies too (defensive — W71 adds validation)', () => {
    expect(stripInlineImageMarkers('x [IMG#zz-not-hex!] y')).toBe('x  y');
  });

  it('leaves citation markers and ordinary brackets untouched', () => {
    const text = 'Fact one. [chunk-kb-a_doc-b_chunk-0001] See [the docs](url).';
    expect(stripInlineImageMarkers(text)).toBe(text);
  });

  it('returns marker-less text unchanged (fast path)', () => {
    expect(stripInlineImageMarkers('no markers here')).toBe('no markers here');
  });
});

describe('W70 — streaming partial-marker hold-back', () => {
  it.each(['[', '[I', '[IM', '[IMG', '[IMG#', '[IMG#a1b'])(
    'holds back trailing partial %j while streaming',
    (partial) => {
      expect(stripInlineImageMarkers(`Click Save. ${partial}`, true)).toBe('Click Save. ');
    },
  );

  it('still strips complete markers while streaming', () => {
    expect(stripInlineImageMarkers('Done. [IMG#a1b2c3d4] Next [IMG#b2c', true)).toBe(
      'Done.  Next ',
    );
  });

  it('does NOT hold back a trailing partial when not streaming (final render)', () => {
    // A final answer ending in "[IMG#abc" is malformed-but-final; without the
    // streaming flag the partial is literal text (W71 validation territory).
    expect(stripInlineImageMarkers('tail [IMG#a1b')).toBe('tail [IMG#a1b');
  });

  it('releases a held "[" once the next delta disproves the marker', () => {
    // delta 1: trailing "[" held; delta 2 arrives → "[link]" is not a marker.
    expect(stripInlineImageMarkers('See [', true)).toBe('See ');
    expect(stripInlineImageMarkers('See [the docs](url)', true)).toBe('See [the docs](url)');
  });
});

describe('W71 — imageMarkerKey', () => {
  it('takes the first 8 hex of a checksum', () => {
    expect(imageMarkerKey('019f36cfdeadbeef00112233')).toBe('019f36cf');
  });

  it('returns a short checksum unchanged (no padding)', () => {
    expect(imageMarkerKey('abc')).toBe('abc');
    expect(imageMarkerKey('')).toBe('');
  });
});

describe('W71 — parseInlineImageMarkers (segments)', () => {
  const VALID = new Set(['a1b2c3d4', 'b2c3d4e5', 'c3d4e5f6']);

  it('returns a single text segment when there are no markers', () => {
    expect(parseInlineImageMarkers('plain answer', VALID)).toEqual([
      { type: 'text', text: 'plain answer' },
    ]);
  });

  it('returns [] for empty text', () => {
    expect(parseInlineImageMarkers('', VALID)).toEqual([]);
  });

  it('anchors a valid marker into text / image / text segments', () => {
    expect(parseInlineImageMarkers('Click Save. [IMG#a1b2c3d4] Then close.', VALID)).toEqual([
      { type: 'text', text: 'Click Save. ' },
      { type: 'image', sha8: 'a1b2c3d4' },
      { type: 'text', text: ' Then close.' },
    ]);
  });

  it('emits no leading empty text segment when a marker is first', () => {
    expect(parseInlineImageMarkers('[IMG#a1b2c3d4]tail', VALID)).toEqual([
      { type: 'image', sha8: 'a1b2c3d4' },
      { type: 'text', text: 'tail' },
    ]);
  });

  it('keeps adjacent valid markers as back-to-back image segments', () => {
    expect(parseInlineImageMarkers('x [IMG#a1b2c3d4][IMG#b2c3d4e5] y', VALID)).toEqual([
      { type: 'text', text: 'x ' },
      { type: 'image', sha8: 'a1b2c3d4' },
      { type: 'image', sha8: 'b2c3d4e5' },
      { type: 'text', text: ' y' },
    ]);
  });

  it('strips a marker not in the surviving set (capped out / decorative) and merges text', () => {
    // d4e5f6a7 ∉ VALID → no card; surrounding text joins into one run
    expect(parseInlineImageMarkers('before [IMG#d4e5f6a7] after', VALID)).toEqual([
      { type: 'text', text: 'before  after' },
    ]);
  });

  it('strips a malformed marker body defensively', () => {
    expect(parseInlineImageMarkers('x [IMG#zz-not-hex!] y', VALID)).toEqual([
      { type: 'text', text: 'x  y' },
    ]);
  });

  it('anchors a sha8 at most once — a repeat marker is stripped', () => {
    const out = parseInlineImageMarkers('A [IMG#a1b2c3d4] B [IMG#a1b2c3d4] C', VALID);
    expect(out).toEqual([
      { type: 'text', text: 'A ' },
      { type: 'image', sha8: 'a1b2c3d4' },
      { type: 'text', text: ' B  C' },
    ]);
    expect(
      out.filter((s): s is Extract<InlineSegment, { type: 'image' }> => s.type === 'image'),
    ).toHaveLength(1);
  });

  it('with an empty membership set degrades to one stripped text segment', () => {
    // zero-regression: text of the single segment == stripInlineImageMarkers(text)
    const text = 'Step 1. [IMG#a1b2c3d4]\n\n[IMG#b2c3d4e5]\n\nStep 2. [IMG#c3d4e5f6]';
    const segments = parseInlineImageMarkers(text, new Set());
    expect(segments).toHaveLength(1);
    expect(segments[0]).toEqual({ type: 'text', text: stripInlineImageMarkers(text) });
  });

  it('leaves citation markers and ordinary brackets untouched', () => {
    const text = 'Fact. [chunk-kb-a_doc-b_chunk-0001] See [the docs](url).';
    expect(parseInlineImageMarkers(text, VALID)).toEqual([{ type: 'text', text }]);
  });

  it('treats a final trailing partial marker as literal text (not streaming)', () => {
    // a final answer ending in "[IMG#a1b" is malformed-but-final — no closing
    // bracket, so the complete-marker pattern never matches it (mirrors strip)
    expect(parseInlineImageMarkers('tail [IMG#a1b', VALID)).toEqual([
      { type: 'text', text: 'tail [IMG#a1b' },
    ]);
  });
});
