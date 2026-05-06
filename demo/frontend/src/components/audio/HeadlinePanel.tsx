// HeadlinePanel — the audio-tab hero. Two-tier layout: global key on the left
// (whole-clip verdict), local key on the right (segment / region reading), with
// a three-cell meta strip below. The serif tonic + key-signature glyph is the
// same family as the manual-entry hero card; just sized differently to express
// the global/local hierarchy.

import type { EnrichedAudioResult } from '../../types/audio';
import SectionCard from '../ui/SectionCard';
import KeySignatureGlyph from '../ui/KeySignatureGlyph';
import ConfidenceBar from '../ui/ConfidenceBar';
import PedagogyNote from '../ui/PedagogyNote';
import Eyebrow from '../ui/Eyebrow';
import Tag from '../ui/Tag';

interface HeadlinePanelProps {
  result: EnrichedAudioResult;
}

const minorKeyMode = (mode: string) =>
  /minor|aeolian|phrygian|locrian|dorian/i.test(mode);

const HeadlinePanel = ({ result }: HeadlinePanelProps) => {
  const { global: g, local: l, analysis, keysMatch, borrowedLabels } = result;

  const globalIsMinor = minorKeyMode(g.mode);
  const localIsMinor = minorKeyMode(l.mode);

  return (
    <SectionCard
      eyebrow="Detected key"
      title="Global verdict + local reading"
      subtitle="The whole-file key on the left; the segment-specific reading on the right."
      bodyClassName="p-0"
    >
      {/* Two-column hero layout. Stacks on mobile, splits on lg+. */}
      <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] divide-y lg:divide-y-0 lg:divide-x divide-slate-200">
        {/* Global key */}
        <div className="p-6 relative">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary-500 via-primary-400 to-transparent" />
          <Eyebrow tone="primary" className="mb-2">Global key</Eyebrow>
          <div className="flex items-start gap-4 flex-wrap">
            <div className="min-w-0">
              <div className="flex items-baseline gap-3 flex-wrap">
                <span
                  className="font-serif font-bold text-slate-900 tracking-tight"
                  style={{ fontSize: '5.5rem', lineHeight: 0.9 }}
                >
                  {g.tonic}
                </span>
                <span className="font-serif text-2xl text-slate-400 italic font-light">
                  {g.mode.toLowerCase()}
                </span>
              </div>
              <div className="text-[11px] font-mono uppercase tracking-wider text-slate-500 mt-2">
                {globalIsMinor ? 'minor-mode tonic' : 'major-mode tonic'}
              </div>
            </div>
            <div className="ml-auto">
              <KeySignatureGlyph keySignature={g.key_signature} />
            </div>
          </div>
          <div className="mt-5 max-w-md">
            <ConfidenceBar value={g.confidence} color="primary" showValue={false} />
            <div className="text-xs font-mono tabular-nums text-slate-500 mt-1.5">
              Confidence {(g.confidence * 100).toFixed(1)}%
            </div>
          </div>
        </div>

        {/* Local key */}
        <div className="p-6">
          <div className="flex items-center justify-between gap-2 mb-2 flex-wrap">
            <Eyebrow tone="primary">Local key</Eyebrow>
            {keysMatch ? (
              <Tag tone="emerald">matches global</Tag>
            ) : (
              <Tag tone="amber">differs from global</Tag>
            )}
          </div>
          <div className="flex items-start gap-3 flex-wrap">
            <div className="min-w-0">
              <div className="flex items-baseline gap-2 flex-wrap">
                <span
                  className="font-serif font-semibold text-slate-700 tracking-tight"
                  style={{ fontSize: '3rem', lineHeight: 1 }}
                >
                  {l.tonic}
                </span>
                <span className="font-serif text-lg text-slate-400 italic font-light">
                  {l.mode.toLowerCase()}
                </span>
              </div>
              <div className="text-[11px] font-mono uppercase tracking-wider text-slate-500 mt-1.5">
                {localIsMinor ? 'minor-mode tonic' : 'major-mode tonic'}
              </div>
            </div>
            <div className="ml-auto">
              <KeySignatureGlyph keySignature={l.key_signature} size="sm" />
            </div>
          </div>
          {keysMatch && (
            <p className="mt-3 text-xs font-serif italic text-slate-500 leading-relaxed">
              Same notes as the global key — just heard from a different tonal center.
            </p>
          )}
        </div>
      </div>

      {/* Three-cell meta strip: region · cadence · borrowed tones */}
      <div className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-slate-200 border-t border-slate-200">
        <RegionCell
          regionType={l.region_type}
          regionConfidence={l.region_confidence}
        />
        <CadenceCell
          detected={analysis.cadence_detected}
          strength={analysis.cadence_strength}
        />
        <BorrowedCell labels={borrowedLabels} />
      </div>

      <div className="p-6 border-t border-slate-100 bg-slate-50/40">
        <PedagogyNote title="Reading the panel">
          <p>
            <strong>Global</strong> is the whole-clip verdict — it averages across the entire
            audio. <strong>Local</strong> is the reading for the segment you analyzed (the full
            file, by default). When a piece modulates, the local key may differ from the global
            one.
          </p>
        </PedagogyNote>
      </div>
    </SectionCard>
  );
};

const RegionCell = ({ regionType, regionConfidence }: { regionType: string; regionConfidence: number }) => {
  const dot =
    regionType === 'modulation' ? 'bg-amber-500' : regionType === 'modal_shift' ? 'bg-indigo-500' : 'bg-slate-400';
  const headline =
    regionType === 'modulation'
      ? 'Modulation'
      : regionType === 'modal_shift'
        ? 'Modal shift'
        : 'Stable';
  return (
    <MetaCell
      eyebrow="Region"
      headline={headline}
      dot={dot}
      sub={`Confidence ${(regionConfidence * 100).toFixed(0)}%`}
    />
  );
};

const CadenceCell = ({ detected, strength }: { detected: boolean; strength: number }) => (
  <MetaCell
    eyebrow="Cadence"
    headline={detected ? 'Detected' : 'None'}
    dot={detected ? 'bg-emerald-500' : 'bg-slate-400'}
    sub={detected ? `Strength ${(strength * 100).toFixed(0)}%` : 'No V → I resolution'}
  />
);

const BorrowedCell = ({ labels }: { labels: string[] }) => {
  const has = labels.length > 0;
  return (
    <MetaCell
      eyebrow="Borrowed tones"
      headline={has ? `${labels.length}` : 'None'}
      dot={has ? 'bg-rose-500' : 'bg-slate-400'}
      sub={has ? labels.slice(0, 4).join(' · ') + (labels.length > 4 ? ' …' : '') : 'All chords are diatonic'}
    />
  );
};

const MetaCell = ({
  eyebrow,
  headline,
  dot,
  sub,
}: {
  eyebrow: string;
  headline: string;
  dot: string;
  sub: string;
}) => (
  <div className="p-5">
    <div className="flex items-center gap-2 mb-1.5">
      <span className={`w-2 h-2 rounded-full ${dot}`} aria-hidden="true" />
      <span className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500">
        {eyebrow}
      </span>
    </div>
    <div className="font-serif text-2xl font-semibold text-slate-900 tracking-tight leading-tight">
      {headline}
    </div>
    <div className="text-xs text-slate-600 mt-1.5 leading-relaxed">{sub}</div>
  </div>
);

export default HeadlinePanel;
