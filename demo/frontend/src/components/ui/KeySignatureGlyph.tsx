// Key-signature glyph badge. Mirrors the small floating panel on the design
// hero card: a serif sharp/flat/natural glyph above an eyebrow ("key signature")
// with a one-line label of the actual accidentals (e.g. "F♯ · C♯ · G♯").
//
// Accepts either a raw signature string from the backend (like "3 sharps" or
// "D major / B minor") or an explicit accidental count + kind.

import { describeKeySignature } from '../../utils/keyGlyph';

interface KeySignatureGlyphProps {
  /** Backend signature string, e.g. "3 sharps", "2 flats", "C major / A minor". */
  keySignature?: string | null;
  /** Optional override: explicit accidental count (positive=sharps, negative=flats). */
  accidentals?: number;
  /** Visual size: "md" for hero card, "sm" for inline use. */
  size?: 'sm' | 'md';
  className?: string;
}

const KeySignatureGlyph = ({
  keySignature,
  accidentals,
  size = 'md',
  className = '',
}: KeySignatureGlyphProps) => {
  const desc = describeKeySignature(keySignature, accidentals);

  const glyphSize = size === 'sm' ? 'text-xl' : 'text-2xl sm:text-3xl';
  const padding = size === 'sm' ? 'px-2 py-1' : 'px-3 py-2';

  // Coral for sharps (warm, leading), slate for flats/natural (cooler, settled).
  const glyphColor = desc.kind === 'sharps' ? 'text-primary-700' : desc.kind === 'flats' ? 'text-slate-700' : 'text-slate-400';

  return (
    <div
      className={`bg-white/80 border border-primary-100 rounded-lg ${padding} flex flex-col items-center gap-0.5 ${className}`}
    >
      <span
        className={`font-serif ${glyphSize} ${glyphColor} leading-none`}
        aria-hidden="true"
      >
        {desc.glyph}
      </span>
      <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
        key signature
      </span>
      {desc.label && (
        <span className="text-[11px] font-medium text-slate-700 tracking-tight whitespace-nowrap">
          {desc.label}
        </span>
      )}
    </div>
  );
};

export default KeySignatureGlyph;
