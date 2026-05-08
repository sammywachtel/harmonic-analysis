// Audio timeline — waveform + chord ribbon + playhead + transport.
//
// The canvas paints the waveform once (with a re-paint on resize). Chord
// ribbon and playhead are positioned in DOM so they stay sharp at any zoom and
// can capture pointer events without canvas hit-testing.
//
// Playback state (currentTime, isPlaying, togglePlay, seek) is OWNED by the
// parent via the useAudioPlayer hook so the chord-progression table and the
// timeline both see the same live playhead.

import { useEffect, useMemo, useRef, useState } from 'react';
import type { EnrichedChordEvent, ChordFunction } from '../../types/audio';
import SectionCard from '../ui/SectionCard';
import Tag from '../ui/Tag';
import { formatTime } from '../../utils/audioAdapter';

interface TimelineProps {
  /** Full audio file duration in seconds (NOT the analyzed segment span). */
  duration: number;
  peaks: number[];           // 0..1 amplitude bins, spanning the full file
  /** Chord events with absolute file-time start_time/end_time (the adapter
   *  already shifted them out of segment-relative time). */
  chords: EnrichedChordEvent[];
  /** Analyzed range in absolute file seconds. When the segment doesn't cover
   *  the whole file, the timeline ZOOMS into this region — the waveform peaks
   *  are sliced to just the segment, the chord ribbon spans full width, and
   *  click/hover/playhead positions are mapped against the segment span. */
  segmentStart?: number;
  segmentEnd?: number;
  /** Current absolute file time, driven by the parent's audio element. */
  currentTime: number;
  isPlaying: boolean;
  togglePlay: () => void;
  seek: (timeSec: number) => void;
  /** Whether playback is available (an audio file is loaded). */
  hasAudio: boolean;
}

const FUNCTION_COLORS: Record<ChordFunction, string> = {
  tonic:        '#e8420f', // primary-600
  predominant:  '#4338ca', // indigo-700
  dominant:     '#f59e0b', // amber-500
  submediant:   '#10b981', // emerald-500
  mediant:      '#34d399', // emerald-400
  leading:      '#fb7185', // rose-400
  chromatic:    '#f43f5e', // rose-500
};

const drawWaveform = (
  canvas: HTMLCanvasElement,
  peaks: number[],
  baseHeight: number,
) => {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  const dpr = window.devicePixelRatio || 1;
  const cssWidth = canvas.clientWidth;
  const cssHeight = baseHeight;
  canvas.width = Math.max(1, Math.floor(cssWidth * dpr));
  canvas.height = Math.max(1, Math.floor(cssHeight * dpr));
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, cssWidth, cssHeight);

  if (peaks.length === 0) {
    // Empty fallback: thin baseline so the area still reads as a track.
    ctx.fillStyle = '#e2e8f0'; // slate-200
    ctx.fillRect(0, cssHeight / 2 - 0.5, cssWidth, 1);
    return;
  }

  const mid = cssHeight / 2;
  const barWidth = Math.max(1, cssWidth / peaks.length);
  ctx.fillStyle = '#cbd5e1'; // slate-300
  for (let i = 0; i < peaks.length; i++) {
    const h = peaks[i] * (cssHeight * 0.95);
    ctx.fillRect(i * barWidth, mid - h / 2, Math.max(1, barWidth - 0.5), h);
  }
};

const Timeline = ({
  duration,
  peaks,
  chords,
  segmentStart = 0,
  segmentEnd,
  currentTime,
  isPlaying,
  togglePlay,
  seek,
  hasAudio,
}: TimelineProps) => {
  // Normalize segment bounds. The visible "view" equals the segment when one
  // is specified — we zoom into it so it fills the timeline. If the segment
  // is the whole file, the view is the whole file.
  const segStart = Math.max(0, Math.min(duration, segmentStart));
  const segEnd = Math.max(segStart, Math.min(duration, segmentEnd ?? duration));
  const viewSpan = Math.max(0.001, segEnd - segStart);
  const isFullFile = segStart <= 0 && segEnd >= duration - 0.01;

  // Slice the waveform peaks to just the visible region. The canvas painter
  // scales whatever it gets to fill the canvas width, so a slice naturally
  // expands to fill the available space.
  const visiblePeaks = (() => {
    if (peaks.length === 0 || duration <= 0) return peaks;
    if (isFullFile) return peaks;
    const startIdx = Math.max(0, Math.floor((segStart / duration) * peaks.length));
    const endIdx = Math.min(peaks.length, Math.ceil((segEnd / duration) * peaks.length));
    return peaks.slice(startIdx, endIdx);
  })();

  // Map an absolute file time to a percentage across the visible track.
  const toViewPct = (fileTime: number): number =>
    Math.max(0, Math.min(100, ((fileTime - segStart) / viewSpan) * 100));

  // Map a click ratio (0..1 across the visible track) back to an absolute
  // file time inside the segment.
  const fromViewRatio = (ratio: number): number =>
    segStart + Math.max(0, Math.min(1, ratio)) * viewSpan;

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const trackRef = useRef<HTMLDivElement | null>(null);
  const [hoveredChord, setHoveredChord] = useState<EnrichedChordEvent | null>(null);

  // Repaint waveform on mount + resize. Use the segment-sliced peaks so the
  // visible waveform represents only the analyzed region.
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    drawWaveform(canvas, visiblePeaks, 96);
    const onResize = () => drawWaveform(canvas, visiblePeaks, 96);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [visiblePeaks]);

  // Click on the track scrubs. Both click and hover positions map through the
  // view (segment) range so a click at the leftmost pixel goes to segStart,
  // not file t=0.
  const handleTrackClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    seek(fromViewRatio(ratio));
  };

  const handleTrackHover = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    const fileTime = fromViewRatio(ratio);
    const chord = chords.find((c) => fileTime >= c.start_time && fileTime < c.end_time) ?? null;
    setHoveredChord(chord);
  };

  // Playhead — clamped to [0, 100] of the visible track. When the audio
  // plays past segEnd, the head pins to the right edge.
  const playheadPct = toViewPct(currentTime);
  const playheadInView = currentTime >= segStart && currentTime <= segEnd;

  // The chord we surface in the indicator strip: hover wins when active,
  // otherwise we show whatever's playing. Computed once so the strip and any
  // playhead label use the same reference.
  //
  // 50 ms look-ahead on currentTime compensates for audio-element seek
  // rounding — browsers land seeks at the nearest decoded frame, typically
  // 10–30 ms off the requested time. Without it, clicking row N's start
  // would highlight row N-1 (the seek lands just inside the previous
  // chord's [start, end) window). Same fix applied in ChordProgression.tsx.
  const playingChord = useMemo(
    () => {
      const t = currentTime + 0.05;
      return chords.find((c) => t >= c.start_time && t < c.end_time) ?? null;
    },
    [chords, currentTime],
  );
  const activeChord = hoveredChord ?? playingChord;
  const activeReason: 'hover' | 'playing' | null = hoveredChord
    ? 'hover'
    : playingChord
      ? 'playing'
      : null;

  // When zoomed, surface the analyzed range in the subtitle so it's clear
  // why only part of the file is visible.
  const subtitle = isFullFile
    ? 'Click the track to scrub; hover to inspect a chord'
    : `Showing analyzed segment ${formatTime(segStart)} → ${formatTime(segEnd)} · click to scrub`;

  return (
    <SectionCard
      eyebrow="Timeline"
      title="Waveform + chord ribbon"
      subtitle={subtitle}
    >
      {/* Single chord indicator strip. Always present so the layout doesn't
          jump; reads "—" when nothing is active. Hover wins over playback so
          the user can probe specific chords without having to pause. Sits
          above the waveform so it never obstructs the colored bars. */}
      <div className="mb-3 min-h-[2rem] flex items-center justify-between gap-3 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200">
        {activeChord ? (
          <>
            <div className="flex items-baseline gap-2 flex-wrap min-w-0">
              <span className="font-serif text-lg font-semibold text-slate-900 leading-none">
                {activeChord.chord_label}
              </span>
              {activeChord.roman && (
                <span className="font-serif italic text-sm text-slate-500 leading-none">
                  {activeChord.roman}
                </span>
              )}
              <span className="text-slate-300 text-xs">·</span>
              <span className="font-mono text-xs tabular-nums text-slate-600">
                {formatTime(activeChord.start_time)} → {formatTime(activeChord.end_time)}
              </span>
              <span className="text-slate-300 text-xs">·</span>
              <span className="font-mono text-xs tabular-nums text-slate-600">
                {(activeChord.confidence * 100).toFixed(0)}%
              </span>
              {!activeChord.is_diatonic && (
                <Tag tone="amber" className="text-[10px]">borrowed</Tag>
              )}
            </div>
            <span className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500 whitespace-nowrap">
              {activeReason === 'hover' ? 'hover' : 'now playing'}
            </span>
          </>
        ) : (
          <span className="text-xs text-slate-400 italic">
            Hover the track or press play to inspect a chord
          </span>
        )}
      </div>
      {/* Waveform + chord ribbon share a single bordered container. Wrapping
          them together is the only way to guarantee the chord blocks at t=0
          and t=duration land flush with the waveform edges — the canvas's
          border + rounded corners would otherwise leave a hairline gap on
          each side. Playhead and tooltip overlay both layers. */}
      <div
        ref={trackRef}
        onClick={handleTrackClick}
        onMouseMove={handleTrackHover}
        onMouseLeave={() => setHoveredChord(null)}
        className="relative cursor-pointer select-none rounded-lg border border-slate-200 bg-slate-50 overflow-hidden"
      >
        {/* Waveform — top 96px. The canvas paints visiblePeaks (the segment
            slice when zoomed in) across the full canvas width, so the segment
            naturally fills the available space. */}
        <div className="relative h-24">
          <canvas ref={canvasRef} className="w-full h-full block" />
        </div>

        {/* Chord ribbon — chord blocks position via the view-pct mapping so
            they line up with the (possibly zoomed) waveform above. */}
        <div className="relative h-7 bg-white border-t border-slate-200">
          {chords.map((c, i) => {
            const startClamped = Math.max(segStart, Math.min(segEnd, c.start_time));
            const endClamped = Math.max(startClamped, Math.min(segEnd, c.end_time));
            if (endClamped <= startClamped) return null;
            const leftPct = toViewPct(startClamped);
            const widthPct = toViewPct(endClamped) - leftPct;
            const opacity = 0.55 + c.confidence * 0.4;
            return (
              <div
                key={`${c.start_time}-${i}`}
                className="absolute top-0 bottom-0 border-r border-white/40"
                style={{
                  left: `${leftPct}%`,
                  width: `${widthPct}%`,
                  background: FUNCTION_COLORS[c.function],
                  opacity,
                }}
              />
            );
          })}
        </div>

        {/* Playhead — full-height vertical line + circle, drawn on top of
            both the waveform and the chord ribbon. Hidden when playback
            wanders outside the visible segment so we don't pin a misleading
            line to either edge. */}
        {playheadInView && (
          <div
            className="absolute top-0 bottom-0 w-px bg-rose-500 pointer-events-none"
            style={{ left: `${playheadPct}%` }}
          >
            <div className="w-3 h-3 bg-rose-500 rounded-full -ml-[5px] -mt-1 shadow" />
          </div>
        )}

        {/* The chord indicator strip above the waveform reads from
            activeChord; we don't need a floating tooltip overlapping the
            ribbon anymore. */}
      </div>

      {/* Transport row */}
      <div className="mt-4 flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={togglePlay}
            disabled={!hasAudio}
            className="w-10 h-10 rounded-full bg-primary-600 hover:bg-primary-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white flex items-center justify-center transition shadow-sm"
            aria-label={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? (
              <svg viewBox="0 0 24 24" className="w-5 h-5" fill="currentColor" aria-hidden="true">
                <rect x="6" y="5" width="4" height="14" rx="1" />
                <rect x="14" y="5" width="4" height="14" rx="1" />
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" className="w-5 h-5 ml-0.5" fill="currentColor" aria-hidden="true">
                <path d="M8 5v14l11-7L8 5z" />
              </svg>
            )}
          </button>
          <div className="font-mono tabular-nums text-sm text-slate-700">
            {formatTime(currentTime)} <span className="text-slate-300">/</span>{' '}
            <span className="text-slate-500">{formatTime(duration)}</span>
          </div>
          {/* Discoverability hint for the keyboard shortcuts. Hidden on
              narrow screens to keep the transport row uncluttered. */}
          <div
            className="hidden md:flex items-center gap-1.5 text-[10px] font-mono text-slate-500"
            title="Space toggles play/pause; ←/→ scan ±5s (Shift for ±15s)"
          >
            <kbd className="px-1.5 py-0.5 border border-slate-300 rounded bg-slate-50 leading-none">space</kbd>
            <span className="text-slate-400">play</span>
            <kbd className="ml-2 px-1.5 py-0.5 border border-slate-300 rounded bg-slate-50 leading-none">←</kbd>
            <kbd className="px-1.5 py-0.5 border border-slate-300 rounded bg-slate-50 leading-none">→</kbd>
            <span className="text-slate-400">scan</span>
          </div>
        </div>

        {/* Mini legend */}
        <div className="flex items-center gap-3 text-[10px] font-mono uppercase tracking-wider text-slate-500">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-primary-500" /> tonic
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-indigo-500" /> predominant
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-amber-500" /> dominant
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-rose-500" /> chromatic
          </span>
        </div>
      </div>
    </SectionCard>
  );
};

export default Timeline;
