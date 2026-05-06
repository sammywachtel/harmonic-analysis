// Tab 3 — Audio analysis. Drop a recording, the engine runs key detection +
// chord estimation, and we render the headline panel + waveform/timeline +
// chord cards + (optional) ensemble diagnostics.
//
// Architecture:
//   1. UploadCard owns the file picker + form state
//   2. We compute the waveform peaks client-side via Web Audio API
//   3. POST /api/analyze/audio returns the harmonic analysis
//   4. audioAdapter enriches the response with derived fields (function,
//      Roman numerals, sorted key histogram, etc.)
//   5. useAudioPlayer owns playback state — both Timeline and ChordProgression
//      subscribe to it so the playhead and the table highlight stay in sync.
//   6. HeadlinePanel + Timeline + ChordProgression + AnalysisDetails render
//      the result tree.

import { useEffect, useMemo, useState } from 'react';
import { analyzeAudio, analyzeChords } from '../api/analysis';
import type {
  AudioAnalysisResponse,
  AnalyzeAudioOptions,
  EnrichedAudioResult,
} from '../types/audio';
import type { AnalysisResponse } from '../types/analysis';
import { extractPeaks } from '../utils/waveform';
import { enrichAudioResult, filterAudibleChords } from '../utils/audioAdapter';
import { useAudioPlayer } from '../utils/useAudioPlayer';
import { getLibraryVersion } from '../config/environment';
import UploadCard from '../components/audio/UploadCard';
import HeadlinePanel from '../components/audio/HeadlinePanel';
import Timeline from '../components/audio/Timeline';
import ChordProgression from '../components/audio/ChordProgression';
import AnalysisDetails, { type RunMetadata } from '../components/audio/AnalysisDetails';
import AnalysisResults from '../components/AnalysisResults';

const Tab3 = () => {
  const [file, setFile] = useState<File | null>(null);
  const [audioSrc, setAudioSrc] = useState<string | null>(null);
  const [peaks, setPeaks] = useState<number[]>([]);
  const [durationSec, setDurationSec] = useState<number>(0);
  const [audioSampleRate, setAudioSampleRate] = useState<number | undefined>(undefined);
  const [audioChannels, setAudioChannels] = useState<number | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [raw, setRaw] = useState<AudioAnalysisResponse | null>(null);
  const [enriched, setEnriched] = useState<EnrichedAudioResult | null>(null);
  const [elapsedMs, setElapsedMs] = useState<number | undefined>(undefined);
  const [patternAnalysis, setPatternAnalysis] = useState<AnalysisResponse | null>(null);
  const [patternChords, setPatternChords] = useState<string[]>([]);
  const [patternLoading, setPatternLoading] = useState(false);
  const [patternError, setPatternError] = useState<string | null>(null);

  // When the user picks a new file, decode it locally for the waveform and
  // create the object URL the Timeline + UploadCard share for playback.
  useEffect(() => {
    if (!file) {
      setPeaks([]);
      setDurationSec(0);
      setAudioSampleRate(undefined);
      setAudioChannels(undefined);
      setAudioSrc(null);
      setRaw(null);
      setEnriched(null);
      setElapsedMs(undefined);
      setPatternAnalysis(null);
      setPatternChords([]);
      setPatternError(null);
      return;
    }
    let cancelled = false;
    const url = URL.createObjectURL(file);
    setAudioSrc(url);
    extractPeaks(file).then((p) => {
      if (cancelled) return;
      setPeaks(p.peaks);
      setDurationSec(p.durationSec);
      setAudioSampleRate(p.sampleRate || undefined);
      setAudioChannels(p.channels || undefined);
    });
    return () => {
      cancelled = true;
      URL.revokeObjectURL(url);
    };
  }, [file]);

  const handleAnalyze = async (options: AnalyzeAudioOptions) => {
    if (!file) return;
    try {
      setLoading(true);
      setError(null);
      setRaw(null);
      setEnriched(null);
      setElapsedMs(undefined);
      setPatternAnalysis(null);
      setPatternChords([]);
      setPatternError(null);

      // Wall-clock measure: only the audio request, not the optional pattern
      // pass-through that may follow. performance.now() reads at sub-ms
      // precision in modern browsers.
      const startedAt = performance.now();
      const response = await analyzeAudio(file, options);
      setElapsedMs(performance.now() - startedAt);
      setRaw(response);
      const enrichedResult = enrichAudioResult(response);
      setEnriched(enrichedResult);

      // Optional pass-through: hand the audio-extracted chord labels to the
      // library's pattern engine. Done as a second request so the audio
      // analysis result lands quickly even if pattern analysis is slow or
      // chokes on a tricky progression.
      if (options.runPatternAnalysis) {
        const audibleSubset = filterAudibleChords(
          enrichedResult.chord_progression,
          peaks,
          durationSec || enrichedResult.duration,
        );
        const chordLabels = audibleSubset.map((c) => c.chord_label).filter(Boolean);
        if (chordLabels.length === 0) {
          setPatternError('No audible chord events to analyze.');
        } else {
          // Use the local key as a hint when available — gives the pattern
          // engine a head-start that matches what the audio adapter heard.
          const keyHint =
            enrichedResult.local.tonic && enrichedResult.local.mode
              ? `${enrichedResult.local.tonic} ${enrichedResult.local.mode === 'Aeolian' ? 'minor' : 'major'}`
              : undefined;
          try {
            setPatternLoading(true);
            const result = await analyzeChords({
              chords: chordLabels,
              key: keyHint,
              include_educational: true,
            });
            setPatternAnalysis(result);
            setPatternChords(chordLabels);
          } catch (patternErr) {
            console.error('Pattern analysis failed:', patternErr);
            setPatternError(
              patternErr instanceof Error
                ? `Pattern analysis failed: ${patternErr.message}`
                : 'Pattern analysis failed. The chord labels may have confused the engine.',
            );
          } finally {
            setPatternLoading(false);
          }
        }
      }
    } catch (err) {
      console.error('Audio analysis failed:', err);
      let msg = 'Failed to analyze audio. Make sure the backend is running and ffmpeg is installed for non-WAV files.';
      if (err && typeof err === 'object') {
        const e = err as { response?: { data?: { detail?: string }; status?: number }; message?: string };
        if (e.response?.status === 503) {
          msg = 'The backend is missing the audio extra. Install with: pip install harmonic-analysis[audio]';
        } else if (e.response?.data?.detail) {
          msg = String(e.response.data.detail);
        } else if (e.message) {
          msg = e.message;
        }
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  // Storage key includes the file name so swapping files doesn't carry over
  // a stale playhead. (Hash would be better but length+name is a good-enough
  // discriminator for a demo.)
  const storageKey = file ? `${file.name}-${file.size}` : 'default';

  // Chord events whose audio is at or below the noise floor get dropped so
  // the timeline ribbon and chord cards stop pretending there's music
  // happening in the decay tail. The diagnostic panel still shows raw counts.
  const audibleChords = useMemo(() => {
    if (!enriched) return [];
    return filterAudibleChords(
      enriched.chord_progression,
      peaks,
      durationSec || enriched.duration,
    );
  }, [enriched, peaks, durationSec]);

  // Centralized playback controller. Both the Timeline waveform and the
  // ChordProgression table subscribe to this so the playhead and the
  // currently-playing row update together as audio plays.
  const player = useAudioPlayer({
    audioSrc: audioSrc ?? undefined,
    storageKey,
    segmentStart: enriched?.segment.start,
    segmentEnd: enriched?.segment.end,
    maxTime: durationSec || enriched?.duration || 0,
    enableKeyboardShortcuts: !!enriched,
  });

  return (
    <div className="space-y-8">
      {/* Page intro */}
      <header>
        <h1 className="font-serif font-semibold text-4xl text-slate-900 tracking-tight">
          Audio analysis
        </h1>
        <p className="mt-2 text-slate-600 max-w-2xl text-base leading-relaxed">
          Drop a recording. The engine estimates global and local key, detects cadences and
          modulations, and produces a time-aligned chord progression — all running through the
          same harmonic-analysis library you'd use in Python.
        </p>
      </header>

      {/* Single canonical audio element. Lives at the page level so playback
          survives any layout reflow inside Timeline or ChordProgression. */}
      {audioSrc && (
        <audio
          ref={player.audioRef}
          src={audioSrc}
          preload="metadata"
          className="hidden"
        />
      )}

      <UploadCard
        file={file}
        onFileChange={setFile}
        durationSec={durationSec}
        onAnalyze={handleAnalyze}
        loading={loading}
        error={error}
        onClearError={() => setError(null)}
      />

      {/* Loading skeleton — keeps the layout stable while waiting. */}
      {loading && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 space-y-4 animate-pulse">
          <div className="h-6 bg-slate-100 rounded w-1/3" />
          <div className="h-24 bg-slate-100 rounded" />
          <div className="h-4 bg-slate-100 rounded w-1/2" />
        </div>
      )}

      {/* Results tree — only shown after a successful analysis. */}
      {enriched && raw && (
        <div className="space-y-8">
          <HeadlinePanel result={enriched} />

          <Timeline
            duration={durationSec || enriched.duration}
            peaks={peaks}
            chords={audibleChords}
            segmentStart={enriched.segment.start}
            segmentEnd={enriched.segment.end}
            currentTime={player.currentTime}
            isPlaying={player.isPlaying}
            togglePlay={player.togglePlay}
            seek={player.seek}
            hasAudio={!!audioSrc}
          />

          <ChordProgression
            chords={audibleChords}
            currentTime={player.currentTime}
            onSeek={player.seek}
          />

          {/* Library pattern analysis pass-through. Identical chrome to Manual
              entry — Roman numeral score, pattern cards, modal/chromatic
              callouts, alt-style disclosure — fed by the audio-extracted
              chord labels. Only renders when the user opted in. */}
          {patternLoading && (
            <div className="rounded-2xl border border-slate-200 bg-white p-6 space-y-4 animate-pulse">
              <div className="h-6 bg-slate-100 rounded w-1/3" />
              <div className="h-4 bg-slate-100 rounded w-2/3" />
              <div className="h-24 bg-slate-100 rounded" />
            </div>
          )}
          {patternError && (
            <div className="rounded-2xl border border-rose-200 bg-rose-50/50 p-6">
              <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-rose-700/70 mb-1">
                Pattern analysis
              </div>
              <p className="text-sm text-rose-800">{patternError}</p>
            </div>
          )}
          {patternAnalysis && (
            <AnalysisResults
              results={patternAnalysis}
              chords={patternChords}
            />
          )}

          <AnalysisDetails
            result={enriched}
            runMetadata={{
              sampleRate: audioSampleRate,
              channels: audioChannels,
              libraryVersion: getLibraryVersion(),
              elapsedMs,
            } satisfies RunMetadata}
          />
        </div>
      )}
    </div>
  );
};

export default Tab3;
