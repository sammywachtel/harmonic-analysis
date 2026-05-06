// Hero key card — the editorial centerpiece for Tabs 1 & 2.
// Big serif tonic, mode word in italic, key-signature glyph floating right,
// optional alt-reading callout, confidence bar tucked below.
//
// This replaces the chip-heavy "primary interpretation" header from the old
// AnalysisResults. All the data comes from the existing PrimaryInterpretation
// shape — we just project it differently.

import ConfidenceBar from './ui/ConfidenceBar';
import KeySignatureGlyph from './ui/KeySignatureGlyph';
import Eyebrow from './ui/Eyebrow';

interface HeroKeyCardProps {
  /** e.g. "C", "F♯", "Bb" — the tonic letter shown in 5.5rem serif. */
  tonic: string;
  /** e.g. "major", "minor", "Dorian" — italic word next to the tonic. */
  mode?: string;
  /** Backend signature string like "3 sharps" or "D major / B minor". */
  keySignature?: string;
  /** 0..1 confidence value. */
  confidence: number;
  /** Optional secondary reading (Tab 2's "also reads as F♯ Dorian"). */
  altReading?: string;
  /** Optional eyebrow above the tonic ("primary key", "global key", etc). */
  eyebrow?: string;
  className?: string;
}

const HeroKeyCard = ({
  tonic,
  mode,
  keySignature,
  confidence,
  altReading,
  eyebrow,
  className = '',
}: HeroKeyCardProps) => {
  const minorish = mode ? /minor|aeolian|phrygian|locrian|dorian/i.test(mode) : false;
  const modeMeta = mode ? `${minorish ? 'minor' : 'major'}-mode tonic` : 'tonal center';

  return (
    <div
      className={`relative rounded-2xl border border-primary-200/70 bg-gradient-to-br from-primary-50/60 via-white to-white p-6 overflow-hidden ${className}`}
      data-testid="hero-key-card"
    >
      {/* Top accent stripe — drawn left-to-right, fading to transparent so it
          feels like a brushstroke rather than a hard banner. */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary-500 via-primary-400 to-transparent" />

      <div className="flex items-start gap-6 flex-wrap">
        <div className="min-w-0">
          {eyebrow && <Eyebrow tone="primary" className="mb-2">{eyebrow}</Eyebrow>}
          <div className="flex items-baseline gap-3 flex-wrap">
            <span
              className="font-serif font-bold text-slate-900 tracking-tight"
              style={{ fontSize: '5.5rem', lineHeight: 0.9 }}
              data-testid="hero-tonic"
            >
              {tonic}
            </span>
            {mode && (
              <span className="font-serif text-2xl text-slate-400 italic font-light">
                {mode.toLowerCase()}
              </span>
            )}
          </div>
          <div className="text-[11px] font-mono uppercase tracking-wider text-slate-500 mt-2">
            {modeMeta}
          </div>
        </div>

        {altReading && (
          <div className="bg-indigo-50/60 border border-indigo-100 rounded-xl px-4 py-3 max-w-xs">
            <div className="text-[10px] font-mono uppercase tracking-wider text-indigo-700/70">
              also reads as
            </div>
            <div className="font-serif text-xl text-slate-800 italic font-medium mt-0.5">
              {altReading}
            </div>
          </div>
        )}

        <div className="ml-auto">
          <KeySignatureGlyph keySignature={keySignature} />
        </div>
      </div>

      <div className="mt-6 max-w-md">
        <ConfidenceBar
          value={confidence}
          color="primary"
          size="md"
          showValue={false}
        />
        <div className="text-xs font-mono tabular-nums text-slate-500 mt-1.5">
          Confidence {(confidence * 100).toFixed(1)}%
        </div>
      </div>
    </div>
  );
};

export default HeroKeyCard;
