// Key-signature parsing — turns whatever the backend says about a key's
// accidentals into a glyph + accidental name list.
//
// Backend returns shapes like:
//   "0 sharps"            → natural
//   "3 sharps"            → ♯, names: F# C# G#
//   "2 flats"             → ♭, names: Bb Eb
//   "D major / B minor"   → secondary form, has 2 sharps under the hood
//   "C major"             → 0 accidentals
//
// We try a couple of regexes and fall back to inferring from the tonic/mode.

const SHARP_ORDER = ['F♯', 'C♯', 'G♯', 'D♯', 'A♯', 'E♯', 'B♯'];
const FLAT_ORDER  = ['B♭', 'E♭', 'A♭', 'D♭', 'G♭', 'C♭', 'F♭'];

// Major-key accidental map. Negative = flats, positive = sharps.
const MAJOR_KEY_ACCIDENTALS: Record<string, number> = {
  'C': 0, 'G': 1, 'D': 2, 'A': 3, 'E': 4, 'B': 5, 'F#': 6, 'C#': 7,
  'F': -1, 'Bb': -2, 'Eb': -3, 'Ab': -4, 'Db': -5, 'Gb': -6, 'Cb': -7,
};

// Relative-minor offsets (e.g. A minor = C major).
const MINOR_TO_MAJOR: Record<string, string> = {
  'A': 'C', 'E': 'G', 'B': 'D', 'F#': 'A', 'C#': 'E', 'G#': 'B', 'D#': 'F#', 'A#': 'C#',
  'D': 'F', 'G': 'Bb', 'C': 'Eb', 'F': 'Ab', 'Bb': 'Db', 'Eb': 'Gb', 'Ab': 'Cb',
};

export interface KeySignatureDescription {
  kind: 'sharps' | 'flats' | 'natural';
  count: number;
  glyph: string;     // ♯ / ♯♯ / ♭ / ♭♭ / ♮
  label: string;     // "F♯ · C♯", "B♭ · E♭ · A♭", or ""
  raw: string;       // original string for debug
}

const NATURAL: KeySignatureDescription = {
  kind: 'natural',
  count: 0,
  glyph: '♮',
  label: 'no accidentals',
  raw: '',
};

/** Build the glyph string. We cap at 3 stacked symbols so it stays legible. */
const buildGlyph = (kind: 'sharps' | 'flats', count: number): string => {
  if (count <= 0) return '♮';
  const symbol = kind === 'sharps' ? '♯' : '♭';
  if (count === 1) return symbol;
  if (count === 2) return `${symbol}${symbol}`;
  // 3+ accidentals: show the symbol with a small ×N to keep it readable.
  return `${symbol}×${count}`;
};

const buildLabel = (kind: 'sharps' | 'flats', count: number): string => {
  if (count <= 0) return 'no accidentals';
  const order = kind === 'sharps' ? SHARP_ORDER : FLAT_ORDER;
  return order.slice(0, Math.min(count, order.length)).join(' · ');
};

/**
 * Parse a backend key-signature string ("3 sharps", "2 flats", etc).
 * Optional accidentals override wins if provided.
 */
export const describeKeySignature = (
  keySignature?: string | null,
  accidentals?: number,
): KeySignatureDescription => {
  if (typeof accidentals === 'number') {
    if (accidentals === 0) return { ...NATURAL, raw: keySignature ?? '' };
    const kind = accidentals > 0 ? 'sharps' : 'flats';
    const count = Math.abs(accidentals);
    return {
      kind,
      count,
      glyph: buildGlyph(kind, count),
      label: buildLabel(kind, count),
      raw: keySignature ?? '',
    };
  }

  if (!keySignature) return NATURAL;

  // Try the explicit "N sharps" / "N flats" form first.
  const explicit = keySignature.match(/(\d+)\s*(sharp|flat)s?/i);
  if (explicit) {
    const count = parseInt(explicit[1], 10);
    if (count === 0) return { ...NATURAL, raw: keySignature };
    const kind = explicit[2].toLowerCase().startsWith('sharp') ? 'sharps' : 'flats';
    return {
      kind,
      count,
      glyph: buildGlyph(kind, count),
      label: buildLabel(kind, count),
      raw: keySignature,
    };
  }

  // Fall back to inferring from "X major" or "X minor".
  const majorMatch = keySignature.match(/([A-G][#b]?)\s*major/i);
  if (majorMatch) {
    const tonic = normalizeTonic(majorMatch[1]);
    const acc = MAJOR_KEY_ACCIDENTALS[tonic];
    if (acc != null) return describeKeySignature(keySignature, acc);
  }

  const minorMatch = keySignature.match(/([A-G][#b]?)\s*(minor|aeolian)/i);
  if (minorMatch) {
    const tonic = normalizeTonic(minorMatch[1]);
    const relMajor = MINOR_TO_MAJOR[tonic];
    const acc = relMajor != null ? MAJOR_KEY_ACCIDENTALS[relMajor] : undefined;
    if (acc != null) return describeKeySignature(keySignature, acc);
  }

  // Couldn't parse — show natural and let the surrounding UI carry the meaning.
  return { ...NATURAL, raw: keySignature };
};

/** "Bb" → "Bb"; "B♭" → "Bb"; "F♯" → "F#". */
const normalizeTonic = (tonic: string): string => tonic.replace('♯', '#').replace('♭', 'b');
