// Diagnostic panel — three sub-tabs:
//   1. 24-key histogram (the full key_score_table from the synthesis)
//   2. Ensemble breakdown (per-approach weight + top candidates)
//   3. Run metadata (audio properties, segment, library + wall-clock info)
//
// Only renders when show_details=true was sent on the analyze request.

import { useState } from 'react';
import type { EnrichedAudioResult } from '../../types/audio';
import SectionCard from '../ui/SectionCard';

export interface RunMetadata {
  /** Audio file's source sample rate (Hz). From client-side decode. */
  sampleRate?: number;
  /** Audio file's channel count. From client-side decode. */
  channels?: number;
  /** Library version string (e.g. "1.0.0"). */
  libraryVersion?: string;
  /** Wall-clock duration of the analyze request, in milliseconds. */
  elapsedMs?: number;
}

interface AnalysisDetailsProps {
  result: EnrichedAudioResult;
  runMetadata?: RunMetadata;
}

type Tab = 'histogram' | 'ensemble' | 'meta';

const AnalysisDetails = ({ result, runMetadata }: AnalysisDetailsProps) => {
  const [tab, setTab] = useState<Tab>('histogram');

  const { analysis, segment, chord_progression } = result;
  const { key_scores, ensemble } = analysis;
  const hasDetails = key_scores.length > 0 || (ensemble?.approaches && Object.keys(ensemble.approaches).length > 0);

  if (!hasDetails) {
    return (
      <SectionCard
        eyebrow="Diagnostics"
        title="Analysis details"
        subtitle="Run with “Show details” enabled to see the ensemble breakdown."
      >
        <p className="text-sm text-slate-500">
          The diagnostic panel is only populated when you analyze with
          <span className="font-mono text-slate-700"> show_details=true</span>. Re-run the file
          with that toggle on.
        </p>
      </SectionCard>
    );
  }

  // Winner of the histogram, used to highlight the top bar in coral.
  const winnerKey =
    key_scores[0] != null ? `${key_scores[0].tonic} ${key_scores[0].mode}` : '';
  const maxScore = key_scores.reduce((m, c) => Math.max(m, c.score), 0);

  return (
    <SectionCard
      eyebrow="Diagnostics"
      title="Analysis details"
      subtitle="How the ensemble arrived at the verdict"
      action={
        <div className="inline-flex p-0.5 bg-slate-100 rounded-lg border border-slate-200">
          {(
            [
              ['histogram', 'Histogram'],
              ['ensemble', 'Ensemble'],
              ['meta', 'Run metadata'],
            ] as const
          ).map(([k, label]) => (
            <button
              key={k}
              type="button"
              onClick={() => setTab(k)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                tab === k ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
              aria-pressed={tab === k}
            >
              {label}
            </button>
          ))}
        </div>
      }
    >
      {tab === 'histogram' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1.5">
          {key_scores.map((kc) => {
            const label = `${kc.tonic} ${kc.mode}`;
            const isWinner = label === winnerKey;
            const widthPct = maxScore > 0 ? Math.max(2, (kc.score / maxScore) * 100) : 0;
            return (
              <div key={label} className="flex items-center gap-3">
                <div className="w-20 text-sm font-serif italic text-slate-700">{label}</div>
                <div className="flex-1 h-3 rounded bg-slate-100 overflow-hidden">
                  <div
                    className={`h-full rounded transition-all duration-700 ease-out ${
                      isWinner ? 'bg-primary-600' : 'bg-slate-300'
                    }`}
                    style={{ width: `${widthPct}%` }}
                  />
                </div>
                <div className="w-12 text-right text-xs font-mono tabular-nums text-slate-500">
                  {kc.score.toFixed(2)}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {tab === 'ensemble' && ensemble && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {Object.entries(ensemble.approaches).map(([name, a]) => (
            <div key={name} className="rounded-xl border border-slate-200 p-4 bg-slate-50/30">
              <div className="flex items-center justify-between mb-2 gap-2">
                <h5 className="font-serif font-semibold text-slate-900 tracking-tight">{name}</h5>
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
                  weight {a.weight.toFixed(2)}
                </span>
              </div>
              <div className="text-xs text-slate-500 mb-3">
                Contribution: <span className="font-mono tabular-nums text-slate-700">
                  {(a.contribution * 100).toFixed(1)}%
                </span>{' '}
                · Top guess:{' '}
                <span className="font-serif italic text-slate-700">
                  {a.top.tonic} {a.top.mode}
                </span>
              </div>
              <div className="space-y-1.5">
                {a.candidates.slice(0, 3).map((c, i) => {
                  const topScore = a.candidates[0]?.score || 1;
                  return (
                    <div key={i} className="flex items-center gap-2 text-xs">
                      <div className="w-16 font-serif italic text-slate-700">
                        {c.tonic} {c.mode}
                      </div>
                      <div className="flex-1 h-2 rounded bg-slate-100 overflow-hidden">
                        <div
                          className={`h-full ${i === 0 ? 'bg-primary-500' : 'bg-slate-300'}`}
                          style={{ width: `${Math.max(2, (c.score / topScore) * 100)}%` }}
                        />
                      </div>
                      <div className="w-10 text-right font-mono tabular-nums text-slate-500">
                        {c.score.toFixed(2)}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'meta' && (
        <div className="space-y-5">
          {/* Audio properties — captured at decode time on the client. */}
          {(runMetadata?.sampleRate || runMetadata?.channels) && (
            <div>
              <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500 mb-2">
                Audio
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 text-sm">
                {runMetadata.sampleRate != null && (
                  <MetaRow
                    label="Sample rate"
                    value={`${(runMetadata.sampleRate / 1000).toFixed(1)} kHz`}
                  />
                )}
                {runMetadata.channels != null && (
                  <MetaRow
                    label="Channels"
                    value={runMetadata.channels === 1 ? 'mono' : runMetadata.channels === 2 ? 'stereo' : `${runMetadata.channels} channels`}
                  />
                )}
              </div>
            </div>
          )}

          {/* Segment + chord summary. */}
          <div>
            <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500 mb-2">
              Segment
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 text-sm">
              <MetaRow label="Segment start" value={`${segment.start.toFixed(2)}s`} />
              <MetaRow label="Segment end" value={`${segment.end.toFixed(2)}s`} />
              <MetaRow
                label="Segment duration"
                value={`${(segment.end - segment.start).toFixed(2)}s`}
              />
              <MetaRow label="Chord events" value={String(chord_progression.length)} />
              <MetaRow
                label="Diatonic chords"
                value={
                  chord_progression.length > 0
                    ? `${chord_progression.filter((c) => c.is_diatonic).length} / ${chord_progression.length} (${((chord_progression.filter((c) => c.is_diatonic).length / chord_progression.length) * 100).toFixed(0)}%)`
                    : '0 / 0'
                }
              />
              <MetaRow
                label="Cadence"
                value={
                  analysis.cadence_detected
                    ? `Detected · ${(analysis.cadence_strength * 100).toFixed(0)}%`
                    : 'None detected'
                }
              />
              <MetaRow
                label="Region type"
                value={result.local.region_type ?? 'stable'}
              />
              <MetaRow
                label="Region confidence"
                value={`${(result.local.region_confidence * 100).toFixed(0)}%`}
              />
            </div>
          </div>

          {/* Library + run timing. */}
          {(runMetadata?.libraryVersion || runMetadata?.elapsedMs != null) && (
            <div>
              <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500 mb-2">
                Run
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 text-sm">
                {runMetadata?.libraryVersion && (
                  <MetaRow
                    label="Algorithm"
                    value={`harmonic-analysis v${runMetadata.libraryVersion}`}
                  />
                )}
                {runMetadata?.elapsedMs != null && (
                  <MetaRow
                    label="Wall clock"
                    value={
                      runMetadata.elapsedMs < 1000
                        ? `${runMetadata.elapsedMs.toFixed(0)} ms`
                        : `${(runMetadata.elapsedMs / 1000).toFixed(2)} s`
                    }
                  />
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </SectionCard>
  );
};

const MetaRow = ({ label, value }: { label: string; value: string }) => (
  <div className="flex items-baseline justify-between gap-3 border-b border-dashed border-slate-200 pb-1.5">
    <span className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500">{label}</span>
    <span className="font-mono tabular-nums text-sm text-slate-800">{value}</span>
  </div>
);

export default AnalysisDetails;
