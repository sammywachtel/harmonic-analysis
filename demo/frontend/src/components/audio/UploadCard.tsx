// UploadCard — file picker + segment + preset + advanced controls.
//
// State machine: empty → file_selected → loading → results | error
//   - empty:         drag-drop zone
//   - file_selected: file info, audio preview, segment range, preset, options
//   - loading:       spinner + cancel
//   - error:         rose-toned callout dismissible via "Try again"
//
// We don't manage results inside this card — the parent Tab3 shows them.

import { useEffect, useState } from 'react';
import type { AnalyzeAudioOptions, KeyDetectionPreset, RubatoPreset } from '../../types/audio';
import SectionCard from '../ui/SectionCard';
import Tag from '../ui/Tag';
import Eyebrow from '../ui/Eyebrow';
import DefinitionTooltip from '../ui/DefinitionTooltip';
import { formatTime } from '../../utils/audioAdapter';

const ACCEPTED_AUDIO = '.wav,.mp3,.ogg,.aac,.flac,.m4a';

interface UploadCardProps {
  /** Currently selected file (lifted into Tab3 so we can pass to Timeline). */
  file: File | null;
  onFileChange: (f: File | null) => void;
  /** Decoded duration in seconds (from waveform.ts). */
  durationSec: number;
  /** Triggered on the analyze button. */
  onAnalyze: (options: AnalyzeAudioOptions) => void;
  loading: boolean;
  error: string | null;
  onClearError: () => void;
}

interface AdvancedConfig {
  preset: KeyDetectionPreset;
  showDetails: boolean;
  runPatternAnalysis: boolean;
  segStart: number;
  segEnd: number;
  weights: Record<string, number>;

  // Timing & tempo
  /** Chord-window timing preset. "auto" detects BPM and sizes
   *  the window dynamically; static presets fix the window grid. */
  rubato: RubatoPreset;
  /** Fractional BPM divergence above which auto-rubato emits a separate
   *  region. null = use library default. */
  tempoRegionThreshold: number | null;

  // Chord matching
  /** Diatonic similarity bonus, 0–0.5. null = use library default. */
  tonalBias: number | null;
  /** Bass-register root-match bonus, 0–1. null = use library default. */
  bassBonus: number | null;
  /** Whether to extract bass-register chroma. null = use library default. */
  useBassChroma: boolean | null;
  /** Min bass-chroma peakiness to fire the bonus. null = use default. */
  bassConfidenceThreshold: number | null;

  // Silence detection
  /** Absolute RMS floor (linear). null = library default. */
  rmsSilenceThreshold: number | null;
  /** Trailing-window length in seconds. null = default. */
  trailingSilenceWindowS: number | null;
  /** Threshold as fraction of trailing-window mean RMS. null = default. */
  trailingSilenceRatio: number | null;

  // Chord consolidation
  /** Merge adjacent same-root events into one. null = library default. */
  mergeSameRoot: boolean | null;
  /** Max merged-event duration (seconds). null = default. */
  maxMergeDurationS: number | null;
}

// Library defaults for the chord-estimation tuning knobs. Same DRY caveat as
// DEFAULT_WEIGHTS — keep these in sync with audio_adapter.py.
const TUNING_DEFAULTS = {
  tonalBias: 0.15,
  bassBonus: 0.3,
  useBassChroma: false,
  bassConfidenceThreshold: 0.25,
  tempoRegionThreshold: 0.20,
  rmsSilenceThreshold: 0.005,
  trailingSilenceWindowS: 3.0,
  trailingSilenceRatio: 0.10,
  mergeSameRoot: true,
  maxMergeDurationS: 4.0,
} as const;

// IMPORTANT: keep these in sync with src/harmonic_analysis/audio/_key_ensemble.py
// DEFAULT_WEIGHTS. The frontend can't sniff the library defaults at runtime
// (no endpoint for it yet), so any drift between these numbers and the library
// silently changes ensemble behavior the moment a user opens "advanced".
const DEFAULT_WEIGHTS: Record<string, number> = {
  template_correlation: 1.0,
  boundary_chords:      0.8,
  bass_dominance:       0.6,
  cadential:            0.7,
};

const weightsAreDefault = (w: Record<string, number>): boolean => {
  for (const k of Object.keys(DEFAULT_WEIGHTS)) {
    if (Math.abs((w[k] ?? DEFAULT_WEIGHTS[k]) - DEFAULT_WEIGHTS[k]) > 1e-6) return false;
  }
  return true;
};

// User-facing copy for each ensemble approach. Order here drives the order
// shown in the advanced panel.
const APPROACH_HELP: ReadonlyArray<{
  key: keyof typeof DEFAULT_WEIGHTS;
  title: string;
  description: string;
}> = [
  {
    key: 'template_correlation',
    title: 'Krumhansl–Schmuckler',
    description:
      'The classic. Correlates the file\'s 12-bin pitch histogram against all 24 major/minor key templates and votes for the best fit. Strong baseline; included in every preset.',
  },
  {
    key: 'boundary_chords',
    title: 'Structural emphasis',
    description:
      'Counts chords at structurally important moments (segment boundaries, downbeats) and votes by which key those chords most belong to. Helps when a piece begins or ends decisively on the tonic.',
  },
  {
    key: 'bass_dominance',
    title: 'Bass-register voting',
    description:
      'Looks at just the low-frequency chroma — the "bassline shape" of the piece. Resolves relative-key ambiguity (Am vs C, D vs Bm) by asking which root the bass actually circles back to.',
  },
  {
    key: 'cadential',
    title: 'V → I detector',
    description:
      'Finds dominant→tonic resolutions in the chord progression and votes for the key those cadences imply. High signal-to-noise for tonal music; quiet on modal or static-harmony tracks.',
  },
];

const UploadCard = ({
  file,
  onFileChange,
  durationSec,
  onAnalyze,
  loading,
  error,
  onClearError,
}: UploadCardProps) => {
  const [config, setConfig] = useState<AdvancedConfig>({
    preset: 'default',
    showDetails: false,
    runPatternAnalysis: false,
    segStart: 0,
    segEnd: 0,
    weights: { ...DEFAULT_WEIGHTS },
    rubato: 'auto',
    tempoRegionThreshold: null,
    tonalBias: null,
    bassBonus: null,
    useBassChroma: null,
    bassConfidenceThreshold: null,
    rmsSilenceThreshold: null,
    trailingSilenceWindowS: null,
    trailingSilenceRatio: null,
    mergeSameRoot: null,
    maxMergeDurationS: null,
  });
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [audioSrc, setAudioSrc] = useState<string | null>(null);

  // Re-sync segment bounds whenever a new duration arrives.
  useEffect(() => {
    setConfig((c) => ({ ...c, segStart: 0, segEnd: durationSec || 0 }));
  }, [durationSec]);

  // Keep an object URL for the <audio> preview; revoke on file change to
  // avoid leaking URLs across uploads.
  useEffect(() => {
    if (!file) { setAudioSrc(null); return; }
    const url = URL.createObjectURL(file);
    setAudioSrc(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const handleAnalyze = () => {
    if (!file) return;
    // Send weights whenever they differ from defaults — regardless of whether
    // the advanced panel is open. Otherwise a user who tunes a weight then
    // collapses the disclosure would silently lose their override.
    const weightsTouched = !weightsAreDefault(config.weights);
    onAnalyze({
      start: config.segStart > 0 ? config.segStart : undefined,
      end: config.segEnd < durationSec && config.segEnd > 0 ? config.segEnd : undefined,
      showDetails: config.showDetails,
      preset: config.preset,
      weights: weightsTouched ? config.weights : undefined,
      rubato: config.rubato,
      tempoRegionThreshold: config.tempoRegionThreshold ?? undefined,
      tonalBias: config.tonalBias ?? undefined,
      bassBonus: config.bassBonus ?? undefined,
      useBassChroma: config.useBassChroma ?? undefined,
      bassConfidenceThreshold: config.bassConfidenceThreshold ?? undefined,
      rmsSilenceThreshold: config.rmsSilenceThreshold ?? undefined,
      trailingSilenceWindowS: config.trailingSilenceWindowS ?? undefined,
      trailingSilenceRatio: config.trailingSilenceRatio ?? undefined,
      mergeSameRoot: config.mergeSameRoot ?? undefined,
      maxMergeDurationS: config.maxMergeDurationS ?? undefined,
      runPatternAnalysis: config.runPatternAnalysis,
    });
  };

  const resetWeights = () => {
    setConfig((c) => ({
      ...c,
      weights: { ...DEFAULT_WEIGHTS },
      rubato: 'auto',
      tempoRegionThreshold: null,
      tonalBias: null,
      bassBonus: null,
      useBassChroma: null,
      bassConfidenceThreshold: null,
      rmsSilenceThreshold: null,
      trailingSilenceWindowS: null,
      trailingSilenceRatio: null,
      mergeSameRoot: null,
      maxMergeDurationS: null,
    }));
  };

  const fileExt = file ? '.' + file.name.split('.').pop()?.toLowerCase() : '';

  // ── Empty state ─────────────────────────────────────────────────────────
  if (!file) {
    return (
      <SectionCard
        eyebrow="Upload"
        title="Drop a recording"
        subtitle="WAV native; MP3 / OGG / AAC / FLAC / M4A via ffmpeg on the server"
      >
        <label
          className="block border-2 border-dashed border-slate-300 hover:border-primary-400 rounded-xl px-6 py-10 text-center cursor-pointer transition bg-slate-50/40 hover:bg-slate-50"
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            const dropped = e.dataTransfer.files?.[0];
            if (dropped) onFileChange(dropped);
          }}
        >
          <input
            type="file"
            accept={ACCEPTED_AUDIO}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) onFileChange(f);
            }}
            className="hidden"
          />
          <svg
            viewBox="0 0 24 24"
            aria-hidden="true"
            className="w-10 h-10 text-slate-400 mx-auto"
            fill="currentColor"
          >
            <path d="M19 3v11.55a4 4 0 1 1-2-3.46V6.62L9 8.5v8.55a4 4 0 1 1-2-3.46V6l12-3z" />
          </svg>
          <p className="mt-3 text-base font-semibold text-slate-900 font-serif">
            Drop an audio file or click to browse
          </p>
          <p className="mt-2 text-xs text-slate-500 font-mono">
            {ACCEPTED_AUDIO.replace(/,/g, ' · ')}
          </p>
        </label>
      </SectionCard>
    );
  }

  // ── File selected ───────────────────────────────────────────────────────
  return (
    <SectionCard
      eyebrow="Upload"
      title="Recording selected"
      subtitle="Tune the analysis options below, then run"
      action={
        <button
          type="button"
          onClick={() => onFileChange(null)}
          className="text-sm text-slate-600 hover:text-slate-900 underline"
          disabled={loading}
        >
          Replace
        </button>
      }
    >
      <div className="space-y-5">
        {/* File info */}
        <div className="border border-slate-200 rounded-xl p-4 bg-slate-50/40">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div className="min-w-0 flex-1">
              <Eyebrow tone="primary">File</Eyebrow>
              <div className="mt-1 font-mono text-sm text-slate-900 truncate">{file.name}</div>
              <div className="mt-1 text-xs text-slate-500 font-mono tabular-nums">
                {(file.size / 1024 / 1024).toFixed(2)} MB
                {fileExt && (<><span className="mx-1.5 text-slate-300">·</span>{fileExt}</>)}
                {durationSec > 0 && (<><span className="mx-1.5 text-slate-300">·</span>{formatTime(durationSec)}</>)}
              </div>
            </div>
            <Tag tone="primary">{fileExt.replace('.', '').toUpperCase() || 'AUDIO'}</Tag>
          </div>
          {audioSrc && (
            <audio controls src={audioSrc} className="mt-3 w-full" preload="metadata" />
          )}
        </div>

        {/* Segment range */}
        {durationSec > 0 && (
          <div>
            <Eyebrow tone="slate" className="mb-2">Segment</Eyebrow>
            <SegmentRange
              durationSec={durationSec}
              start={config.segStart}
              end={config.segEnd}
              onChange={(s, e) => setConfig((c) => ({ ...c, segStart: s, segEnd: e }))}
            />
            <div className="text-xs text-slate-500 mt-2 font-mono tabular-nums">
              {formatTime(config.segStart)} → {formatTime(config.segEnd)}
              <span className="mx-1.5 text-slate-300">·</span>
              {(config.segEnd - config.segStart).toFixed(1)}s of {formatTime(durationSec)}
            </div>
            <p className="text-[11px] text-slate-500 mt-2 leading-relaxed">
              Drag the two handles to analyze just a portion of the file. Useful when you want
              the key/chord analysis focused on a specific section (a verse, a bridge) rather
              than averaged across the whole recording.
            </p>
          </div>
        )}

        {/* Key detection preset */}
        <div>
          <div className="flex items-baseline gap-2 mb-2">
            <Eyebrow tone="slate">Key detection</Eyebrow>
            <DefinitionTooltip
              className="text-[11px] font-mono normal-case tracking-normal"
              definition={
                <span>
                  The ensemble combines multiple algorithms (template
                  correlation, boundary chords, bass dominance, cadential)
                  to disambiguate relative-key pairs like B minor vs D major
                  — keys that share the same accidentals but feel different
                  tonally.
                </span>
              }
            >
              how does this work?
            </DefinitionTooltip>
          </div>
          <div className="inline-flex p-0.5 bg-slate-100 rounded-lg border border-slate-200" role="radiogroup">
            {(
              [
                ['default', 'Default ensemble'],
                ['ks_only', 'Krumhansl-Schmuckler only'],
                ['full', 'Full (with iteration_02)'],
              ] as const
            ).map(([k, label]) => (
              <button
                key={k}
                type="button"
                onClick={() => setConfig((c) => ({ ...c, preset: k }))}
                role="radio"
                aria-checked={config.preset === k}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  config.preset === k
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          <ul className="text-[11px] text-slate-500 mt-2 space-y-1 leading-relaxed">
            <li>
              <strong className="text-slate-700">Default ensemble.</strong> Blends four
              independent approaches (template correlation, boundary chords, bass dominance,
              cadential evidence). The most accurate option in everyday use.
            </li>
            <li>
              <strong className="text-slate-700">Krumhansl-Schmuckler only.</strong> Pure
              pitch-histogram template matching — the classic algorithm by itself. Fastest, and
              useful as a baseline to compare the ensemble against.
            </li>
            <li>
              <strong className="text-slate-700">Full.</strong> Adds opt-in research approaches
              (pattern engine, HMM) on top of the default ensemble. Experimental;
              iteration_02 features may produce inconsistent results on some files.
            </li>
          </ul>
        </div>

        {/* Show details */}
        <div>
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={config.showDetails}
              onChange={(e) => setConfig((c) => ({ ...c, showDetails: e.target.checked }))}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-slate-300 rounded"
            />
            <span className="text-sm text-slate-700">Show analysis details</span>
          </label>
          <p className="text-[11px] text-slate-500 mt-1 ml-6 leading-relaxed">
            Adds a diagnostic panel to the results: a 24-key score histogram and a per-approach
            ensemble breakdown showing which approach voted for which key and how much it
            contributed to the final verdict. Helpful when debugging a surprising key call.
          </p>
        </div>

        {/* Run library pattern analysis on the extracted chord labels */}
        <div>
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={config.runPatternAnalysis}
              onChange={(e) =>
                setConfig((c) => ({ ...c, runPatternAnalysis: e.target.checked }))
              }
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-slate-300 rounded"
            />
            <span className="text-sm text-slate-700">Run pattern analysis on extracted chords</span>
          </label>
          <p className="text-[11px] text-slate-500 mt-1 ml-6 leading-relaxed">
            After audio analysis, hand the extracted chord labels to the library's pattern
            engine — the same one Manual entry uses — to surface Roman numerals, cadences,
            modal characteristics, and pattern matches. Adds one extra request after the audio
            run completes.
          </p>
        </div>

        {/* Advanced disclosure */}
        <div>
          <button
            type="button"
            onClick={() => setAdvancedOpen(!advancedOpen)}
            className="text-sm text-primary-700 hover:text-primary-900 font-medium flex items-center gap-1"
            aria-expanded={advancedOpen}
          >
            {advancedOpen ? 'Hide' : 'Show'} advanced
            <svg
              className={`w-4 h-4 transition-transform ${advancedOpen ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {advancedOpen && (
            <div className="mt-3 p-4 border border-slate-200 rounded-xl bg-slate-50/40 space-y-3">
              <p className="text-xs text-slate-600 leading-relaxed">
                The default key detector runs four <strong className="text-slate-900">approaches</strong>{' '}
                in parallel; each one casts a weighted vote, and the ensemble combines them into
                the final key. Tune these weights to bias the result toward whichever approach
                fits your music best — e.g., raise <span className="font-mono text-slate-700">cadential</span>{' '}
                for tonal music with clear V→I resolutions, or lower{' '}
                <span className="font-mono text-slate-700">template_correlation</span> for material
                where the raw pitch histogram is misleading (heavy borrowed chords, modal
                writing). To see your changes take effect, expand{' '}
                <strong className="text-slate-900">Show analysis details</strong> above; the
                ensemble breakdown there reports the actually-applied weights and per-approach
                contribution percentages.
              </p>

              <div className="space-y-2.5">
                {APPROACH_HELP.map(({ key, title, description }) => {
                  const value = config.weights[key] ?? DEFAULT_WEIGHTS[key];
                  const isDefault = Math.abs(value - DEFAULT_WEIGHTS[key]) < 1e-6;
                  return (
                    <label
                      key={key}
                      className="grid grid-cols-[1fr_auto] items-start gap-x-3 gap-y-0.5 py-1.5 border-t border-slate-200 first:border-t-0 first:pt-0"
                    >
                      <div className="min-w-0">
                        <div className="flex items-baseline gap-2">
                          <span className="font-mono text-sm text-slate-900">{key}</span>
                          <span className="text-[10px] font-mono text-slate-400">
                            default {DEFAULT_WEIGHTS[key]}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-600 leading-relaxed mt-0.5">
                          <strong className="text-slate-700 font-semibold">{title}.</strong>{' '}
                          {description}
                        </div>
                      </div>
                      <input
                        type="number"
                        min={0}
                        max={2}
                        step={0.1}
                        value={value}
                        onChange={(e) => {
                          const v = parseFloat(e.target.value);
                          setConfig((c) => ({
                            ...c,
                            weights: {
                              ...c.weights,
                              [key]: Number.isFinite(v) ? v : DEFAULT_WEIGHTS[key],
                            },
                          }));
                        }}
                        className={`w-20 px-2 py-1 text-sm font-mono tabular-nums border rounded-md self-center bg-white ${
                          isDefault ? 'border-slate-300' : 'border-primary-400 ring-1 ring-primary-100'
                        }`}
                        aria-label={`${key} weight`}
                      />
                    </label>
                  );
                })}
              </div>

              {/* Below the ensemble-vote weights, the chord-estimation
                  pipeline is broken into four logical sub-groups. Order
                  follows the pipeline phases the parameters affect, top
                  to bottom: timing → matching → consolidation → silence
                  gates. Most users only ever touch the timing section. */}

              {/* ── Timing & tempo ─────────────────────────────────── */}
              <div className="border-t border-slate-200 pt-3 space-y-3">
                <div>
                  <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500 mb-1">
                    Timing &amp; tempo
                  </div>
                  <p className="text-[11px] text-slate-600 leading-relaxed">
                    How wide the chord-recognition window is and how the
                    tempo-region detector splits sections.
                  </p>
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-baseline gap-2">
                    <span className="text-sm font-medium text-slate-700">rubato</span>
                    <span className="text-[10px] font-mono text-slate-400">default auto</span>
                  </div>
                  <p className="text-[11px] text-slate-500 leading-relaxed">
                    Chord-window timing.{' '}
                    <strong className="text-slate-700">auto</strong> detects the BPM and
                    sizes the window to ~2 beats. Move toward{' '}
                    <strong className="text-slate-700">strict</strong> for fast chord
                    changes; toward <strong className="text-slate-700">loose</strong>/
                    <strong className="text-slate-700">free</strong> if chord events look
                    over-fragmented (slow ballads, busy figuration).
                  </p>
                  <select
                    value={config.rubato}
                    onChange={(e) =>
                      setConfig((c) => ({ ...c, rubato: e.target.value as RubatoPreset }))
                    }
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                  >
                    <option value="auto">auto — detect tempo, size dynamically</option>
                    <option value="strict">strict — 0.25s window (fast changes)</option>
                    <option value="moderate">moderate — 0.5s window</option>
                    <option value="loose">loose — 0.75s window (smoother)</option>
                    <option value="free">free — 1.0s window (very smooth)</option>
                  </select>
                </div>

                <SliderRow
                  label="tempo_region_threshold"
                  title="Tempo-region sensitivity"
                  description="Fractional BPM divergence above which auto-rubato emits a separate region. Lower (0.10) over-segments on performance jitter; higher (0.30) misses real tempo changes. Only effective when rubato='auto'."
                  value={config.tempoRegionThreshold ?? TUNING_DEFAULTS.tempoRegionThreshold}
                  defaultValue={TUNING_DEFAULTS.tempoRegionThreshold}
                  isDefault={config.tempoRegionThreshold === null}
                  min={0.05}
                  max={0.50}
                  step={0.01}
                  onChange={(v) => setConfig((c) => ({ ...c, tempoRegionThreshold: v }))}
                  disabled={config.rubato !== 'auto'}
                  disabledHint="Set rubato='auto' to use this."
                />
              </div>

              {/* ── Chord matching ─────────────────────────────────── */}
              <div className="border-t border-slate-200 pt-3 space-y-3">
                <div>
                  <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500 mb-1">
                    Chord matching
                  </div>
                  <p className="text-[11px] text-slate-600 leading-relaxed">
                    How the template-matcher weighs candidates. Defaults are calibrated for
                    general-purpose pop / rock / classical material.
                  </p>
                </div>

                <SliderRow
                  label="tonal_bias"
                  title="Diatonic preference"
                  description="Bonus added to chord templates whose root sits inside the detected key. Raise to sharpen tonal music; lower to let modal / chromatic chords compete on equal footing."
                  value={config.tonalBias ?? TUNING_DEFAULTS.tonalBias}
                  defaultValue={TUNING_DEFAULTS.tonalBias}
                  isDefault={config.tonalBias === null}
                  min={0}
                  max={0.5}
                  step={0.01}
                  onChange={(v) => setConfig((c) => ({ ...c, tonalBias: v }))}
                />

                <label className="flex items-start gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={config.useBassChroma ?? TUNING_DEFAULTS.useBassChroma}
                    onChange={(e) =>
                      setConfig((c) => ({ ...c, useBassChroma: e.target.checked }))
                    }
                    className="h-4 w-4 mt-0.5 text-primary-600 focus:ring-primary-500 border-slate-300 rounded"
                  />
                  <div className="flex-1">
                    <div className="text-sm text-slate-700">
                      use_bass_chroma{' '}
                      <span className="text-[10px] font-mono text-slate-400">
                        default {TUNING_DEFAULTS.useBassChroma ? 'on' : 'off'}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 leading-relaxed mt-0.5">
                      Extracts a separate bass-register chroma layer to disambiguate roots
                      (Am vs C, Bm vs D). Adds a small amount of compute per file.
                    </p>
                  </div>
                </label>

                <SliderRow
                  label="bass_bonus"
                  title="Bass-root bonus"
                  description="When bass-chroma is on, this is the extra score chord templates whose root matches the bass note receive. Higher = bass tells you the chord; lower = treat the bass as one voice among many."
                  value={config.bassBonus ?? TUNING_DEFAULTS.bassBonus}
                  defaultValue={TUNING_DEFAULTS.bassBonus}
                  isDefault={config.bassBonus === null}
                  min={0}
                  max={1}
                  step={0.05}
                  onChange={(v) => setConfig((c) => ({ ...c, bassBonus: v }))}
                  disabled={config.useBassChroma !== true}
                  disabledHint="Enable bass-chroma above to use this."
                />

                <SliderRow
                  label="bass_confidence_threshold"
                  title="Bass-bonus gating"
                  description="Minimum bass-chroma 'peakiness' (max-PC vs mean) for the bonus to fire. Higher restricts the bonus to very clear bass signals; lower lets it fire on noisier basslines."
                  value={config.bassConfidenceThreshold ?? TUNING_DEFAULTS.bassConfidenceThreshold}
                  defaultValue={TUNING_DEFAULTS.bassConfidenceThreshold}
                  isDefault={config.bassConfidenceThreshold === null}
                  min={0}
                  max={1}
                  step={0.05}
                  onChange={(v) => setConfig((c) => ({ ...c, bassConfidenceThreshold: v }))}
                  disabled={config.useBassChroma !== true}
                  disabledHint="Enable bass-chroma above to use this."
                />
              </div>

              {/* ── Chord consolidation ────────────────────────────── */}
              <div className="border-t border-slate-200 pt-3 space-y-3">
                <div>
                  <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500 mb-1">
                    Chord consolidation
                  </div>
                  <p className="text-[11px] text-slate-600 leading-relaxed">
                    Post-processing that fuses ping-pong chord events sharing the same root.
                  </p>
                </div>

                <label className="flex items-start gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={config.mergeSameRoot ?? TUNING_DEFAULTS.mergeSameRoot}
                    onChange={(e) =>
                      setConfig((c) => ({ ...c, mergeSameRoot: e.target.checked }))
                    }
                    className="h-4 w-4 mt-0.5 text-primary-600 focus:ring-primary-500 border-slate-300 rounded"
                  />
                  <div className="flex-1">
                    <div className="text-sm text-slate-700">
                      merge_same_root{' '}
                      <span className="text-[10px] font-mono text-slate-400">
                        default {TUNING_DEFAULTS.mergeSameRoot ? 'on' : 'off'}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 leading-relaxed mt-0.5">
                      Merges adjacent same-root events that disagree on quality (e.g.
                      Dm7→D7→Dm7 collapses to one). Disable to see raw matcher output.
                    </p>
                  </div>
                </label>

                <SliderRow
                  label="max_merge_duration_s"
                  title="Max merge duration"
                  description="Upper cap (seconds) on a merged event. Real chord changes across bar lines shouldn't fuse just because they share a root. ~1 measure at typical tempos is the sweet spot."
                  value={config.maxMergeDurationS ?? TUNING_DEFAULTS.maxMergeDurationS}
                  defaultValue={TUNING_DEFAULTS.maxMergeDurationS}
                  isDefault={config.maxMergeDurationS === null}
                  min={0.5}
                  max={10}
                  step={0.5}
                  onChange={(v) => setConfig((c) => ({ ...c, maxMergeDurationS: v }))}
                  disabled={config.mergeSameRoot === false}
                  disabledHint="Enable merge_same_root above to use this."
                />
              </div>

              {/* ── Silence detection ──────────────────────────────── */}
              <div className="border-t border-slate-200 pt-3 space-y-3">
                <div>
                  <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500 mb-1">
                    Silence detection
                  </div>
                  <p className="text-[11px] text-slate-600 leading-relaxed">
                    Two stacked gates: an absolute floor (catches true silence) and an
                    adaptive trailing-window gate (catches fade-outs that are quiet relative
                    to recent context).
                  </p>
                </div>

                <SliderRow
                  label="rms_silence_threshold"
                  title="Absolute silence floor"
                  description="Windows whose mean RMS amplitude falls below this are skipped. 0.005 ≈ -46 dBFS — drops noise floor without biting into pp passages."
                  value={config.rmsSilenceThreshold ?? TUNING_DEFAULTS.rmsSilenceThreshold}
                  defaultValue={TUNING_DEFAULTS.rmsSilenceThreshold}
                  isDefault={config.rmsSilenceThreshold === null}
                  min={0}
                  max={0.05}
                  step={0.001}
                  onChange={(v) => setConfig((c) => ({ ...c, rmsSilenceThreshold: v }))}
                />

                <SliderRow
                  label="trailing_silence_window_s"
                  title="Trailing-window length"
                  description="How far back the adaptive gate looks to compute recent loudness. 3-5s is the sweet spot — long enough for stability, short enough to react to fade-outs."
                  value={config.trailingSilenceWindowS ?? TUNING_DEFAULTS.trailingSilenceWindowS}
                  defaultValue={TUNING_DEFAULTS.trailingSilenceWindowS}
                  isDefault={config.trailingSilenceWindowS === null}
                  min={0}
                  max={10}
                  step={0.5}
                  onChange={(v) => setConfig((c) => ({ ...c, trailingSilenceWindowS: v }))}
                />

                <SliderRow
                  label="trailing_silence_ratio"
                  title="Adaptive gate ratio"
                  description="Threshold as a fraction of trailing-window mean RMS. 0.10 = 'current window must be more than 20 dB below recent average to trip the gate'. Set to 0 to disable adaptive gating."
                  value={config.trailingSilenceRatio ?? TUNING_DEFAULTS.trailingSilenceRatio}
                  defaultValue={TUNING_DEFAULTS.trailingSilenceRatio}
                  isDefault={config.trailingSilenceRatio === null}
                  min={0}
                  max={0.5}
                  step={0.01}
                  onChange={(v) => setConfig((c) => ({ ...c, trailingSilenceRatio: v }))}
                  disabled={
                    (config.trailingSilenceWindowS ?? TUNING_DEFAULTS.trailingSilenceWindowS) ===
                    0
                  }
                  disabledHint="Trailing-window length is 0 — adaptive gate is off."
                />
              </div>

              <div className="flex items-center justify-between gap-3 border-t border-slate-200 pt-2.5">
                <div className="text-[11px] text-slate-500 leading-relaxed">
                  <strong className="text-slate-700">Tuning tips:</strong> set a weight to{' '}
                  <span className="font-mono">0</span> to disable an approach entirely.
                  Numbers above <span className="font-mono">1</span> amplify its
                  contribution. Changes only take effect on the next analyze.
                </div>
                <button
                  type="button"
                  onClick={resetWeights}
                  disabled={
                    weightsAreDefault(config.weights) &&
                    config.rubato === 'auto' &&
                    config.tempoRegionThreshold === null &&
                    config.tonalBias === null &&
                    config.bassBonus === null &&
                    config.useBassChroma === null &&
                    config.bassConfidenceThreshold === null &&
                    config.rmsSilenceThreshold === null &&
                    config.trailingSilenceWindowS === null &&
                    config.trailingSilenceRatio === null &&
                    config.mergeSameRoot === null &&
                    config.maxMergeDurationS === null
                  }
                  className="text-xs font-medium text-primary-700 hover:text-primary-900 disabled:text-slate-400 disabled:cursor-not-allowed whitespace-nowrap"
                >
                  Reset to defaults
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Run button */}
        <button
          type="button"
          onClick={handleAnalyze}
          disabled={loading}
          className="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition shadow-sm"
        >
          {loading ? 'Analyzing audio…' : 'Analyze recording'}
        </button>

        {error && (
          <div className="bg-rose-50 border border-rose-200 rounded-xl px-4 py-3 text-sm text-rose-800 flex items-start gap-3">
            <span className="flex-1">{error}</span>
            <button
              type="button"
              onClick={onClearError}
              className="text-rose-600 hover:text-rose-800 font-medium text-xs"
            >
              Dismiss
            </button>
          </div>
        )}
      </div>
    </SectionCard>
  );
};

// Two-handle range slider. The two <input type=range> elements stack on top of
// the same track; the styled .audio-range CSS in index.css makes the thumbs
// look right and keeps the runnable track transparent so we can paint our own.
const SegmentRange = ({
  durationSec,
  start,
  end,
  onChange,
}: {
  durationSec: number;
  start: number;
  end: number;
  onChange: (start: number, end: number) => void;
}) => {
  const startPct = (start / durationSec) * 100;
  const endPct = (end / durationSec) * 100;

  return (
    <div className="relative h-6 select-none">
      {/* Track + selected fill */}
      <div className="absolute top-1/2 -translate-y-1/2 left-0 right-0 h-1 bg-slate-200 rounded-full" />
      <div
        className="absolute top-1/2 -translate-y-1/2 h-1 bg-primary-500 rounded-full"
        style={{ left: `${startPct}%`, right: `${100 - endPct}%` }}
      />
      <input
        type="range"
        min={0}
        max={durationSec}
        step={0.1}
        value={start}
        onChange={(e) => {
          const v = Math.min(parseFloat(e.target.value), end - 0.5);
          onChange(Math.max(0, v), end);
        }}
        className="audio-range absolute inset-0 w-full appearance-none bg-transparent"
        aria-label="Segment start"
      />
      <input
        type="range"
        min={0}
        max={durationSec}
        step={0.1}
        value={end}
        onChange={(e) => {
          const v = Math.max(parseFloat(e.target.value), start + 0.5);
          onChange(start, Math.min(durationSec, v));
        }}
        className="audio-range absolute inset-0 w-full appearance-none bg-transparent"
        aria-label="Segment end"
      />
    </div>
  );
};

// Single-knob slider row used in the Advanced disclosure for the chord-
// estimation tuning parameters. Shows the param name, a one-line title,
// the current value, the default reference, and a description.
interface SliderRowProps {
  label: string;
  title: string;
  description: string;
  value: number;
  defaultValue: number;
  isDefault: boolean;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
  disabled?: boolean;
  disabledHint?: string;
}

const SliderRow = ({
  label,
  title,
  description,
  value,
  defaultValue,
  isDefault,
  min,
  max,
  step,
  onChange,
  disabled = false,
  disabledHint,
}: SliderRowProps) => (
  <div className={`grid grid-cols-[1fr_auto] gap-x-3 gap-y-1 ${disabled ? 'opacity-50' : ''}`}>
    <div className="min-w-0">
      <div className="flex items-baseline gap-2 flex-wrap">
        <span className="font-mono text-sm text-slate-900">{label}</span>
        <span className="text-[10px] font-mono text-slate-400">
          default {defaultValue}
        </span>
      </div>
      <div className="text-[11px] text-slate-600 leading-relaxed mt-0.5">
        <strong className="text-slate-700 font-semibold">{title}.</strong> {description}
      </div>
      {disabled && disabledHint && (
        <div className="text-[10px] italic text-slate-400 mt-0.5">{disabledHint}</div>
      )}
    </div>
    <div className="flex items-start gap-2 self-center">
      {/* The .audio-range CSS makes the native track transparent so we can
          paint our own. A slate hairline behind the input makes the track
          visible; the coral fill on top traces from min to current value. */}
      <div className="relative w-32 h-6 select-none">
        <div className="absolute top-1/2 -translate-y-1/2 left-0 right-0 h-1 bg-slate-200 rounded-full" />
        <div
          className="absolute top-1/2 -translate-y-1/2 left-0 h-1 bg-primary-500 rounded-full"
          style={{ width: `${((value - min) / (max - min)) * 100}%` }}
        />
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          className="audio-range audio-range-single absolute inset-0 w-full appearance-none bg-transparent"
          aria-label={label}
        />
      </div>
      <span
        className={`w-10 text-right text-xs font-mono tabular-nums ${
          isDefault ? 'text-slate-500' : 'text-primary-700 font-semibold'
        }`}
      >
        {value.toFixed(2)}
      </span>
    </div>
  </div>
);

export default UploadCard;
