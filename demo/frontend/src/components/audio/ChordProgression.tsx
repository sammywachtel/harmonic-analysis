// Audio chord progression — dense table view of every chord event the engine
// emitted, with the currently-playing row highlighted. We dropped the "cards"
// alternative view; the table is the sweet spot for skimming long chord lists,
// and the richer pattern/Roman analysis lives in the optional library
// pass-through (rendered separately as <AnalysisResults>).

import { useMemo } from 'react';
import type { EnrichedChordEvent, ChordFunction } from '../../types/audio';
import SectionCard from '../ui/SectionCard';
import Tag from '../ui/Tag';
import { formatTime } from '../../utils/audioAdapter';

interface ChordProgressionProps {
  chords: EnrichedChordEvent[];
  /** Current playback time in seconds, used to highlight the active row. */
  currentTime?: number;
  /** Click on a row → seek the audio there. */
  onSeek?: (timeSec: number) => void;
}

const FUNCTION_TONES: Record<ChordFunction, 'primary' | 'indigo' | 'amber' | 'rose' | 'emerald' | 'slate'> = {
  tonic:        'primary',
  predominant:  'indigo',
  dominant:     'amber',
  submediant:   'emerald',
  mediant:      'emerald',
  leading:      'rose',
  chromatic:    'rose',
};

const FUNCTION_LABELS: Record<ChordFunction, string> = {
  tonic:        'Tonic',
  predominant:  'Predominant',
  dominant:     'Dominant',
  submediant:   'Submediant',
  mediant:      'Mediant',
  leading:      'Leading',
  chromatic:    'Chromatic',
};

const ChordProgression = ({ chords, currentTime = 0, onSeek }: ChordProgressionProps) => {
  // Find which chord index is currently playing. Linear scan is fine — these
  // lists are typically <100 entries.
  const activeIndex = useMemo(() => {
    return chords.findIndex(
      (c) => currentTime >= c.start_time && currentTime < c.end_time,
    );
  }, [chords, currentTime]);

  return (
    <SectionCard
      eyebrow="Chord progression"
      title={`Chord events · ${chords.length}`}
      subtitle="Time-aligned chord estimates with diatonic / borrowed annotation"
    >
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500">
              <th className="py-2 pr-3 font-semibold">#</th>
              <th className="py-2 pr-3 font-semibold">Chord</th>
              <th className="py-2 pr-3 font-semibold">Roman</th>
              <th className="py-2 pr-3 font-semibold">Time</th>
              <th className="py-2 pr-3 font-semibold">Dur</th>
              <th className="py-2 pr-3 font-semibold">Function</th>
              <th className="py-2 pr-3 font-semibold">Conf</th>
              <th className="py-2 font-semibold">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {chords.map((c, i) => {
              const tone = FUNCTION_TONES[c.function];
              const label = FUNCTION_LABELS[c.function];
              const isActive = i === activeIndex;
              return (
                <tr
                  key={`${c.start_time}-${i}`}
                  className={`cursor-pointer transition-colors ${
                    isActive ? 'bg-rose-50' : 'hover:bg-primary-50/40'
                  }`}
                  onClick={() => onSeek?.(c.start_time)}
                >
                  <td className="py-2 pr-3 font-mono tabular-nums text-slate-500">{i}</td>
                  <td className="py-2 pr-3 font-serif text-base text-slate-900">
                    {c.chord_label}
                  </td>
                  <td className="py-2 pr-3 font-serif italic text-slate-700">{c.roman ?? '—'}</td>
                  <td className="py-2 pr-3 font-mono tabular-nums text-slate-700 text-xs">
                    {formatTime(c.start_time)}
                  </td>
                  <td className="py-2 pr-3 font-mono tabular-nums text-slate-500 text-xs">
                    {(c.end_time - c.start_time).toFixed(1)}s
                  </td>
                  <td className="py-2 pr-3">
                    <Tag tone={tone} className="text-[10px]">{label}</Tag>
                  </td>
                  <td className="py-2 pr-3 font-mono tabular-nums text-slate-700 text-xs">
                    {(c.confidence * 100).toFixed(0)}%
                  </td>
                  <td className="py-2 text-xs">
                    {/* No "playing" tag — the row's rose background already
                        signals the current position. Adding a tag here makes
                        the column resize as playback moves between rows that
                        do/don't have the "borrowed" tag, which jitters the
                        whole table layout. */}
                    {!c.is_diatonic && <Tag tone="amber" className="text-[10px]">borrowed</Tag>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </SectionCard>
  );
};

export default ChordProgression;
