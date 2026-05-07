// Map the raw POST /api/analyze/audio response into the richer shape the
// audio components want. The backend gives us minimal-but-honest data; the
// adapter computes the helpful derivations:
//
//   - chord function (tonic / predominant / dominant / etc.) from each chord's
//     root pitch class relative to the local key
//   - Roman numeral guess per chord
//   - sorted 24-key score histogram (from key_analysis_details if present)
//   - ensemble approach contributions for the diagnostic panel
//   - keysMatch flag + borrowedLabels fallback
//
// Nothing here calls the backend; everything is a pure transform.

import type {
  AudioAnalysisResponse,
  AudioChordEvent,
  EnrichedAudioResult,
  EnrichedChordEvent,
  KeyCandidate,
  EnsembleApproach,
  ChordFunction,
} from '../types/audio';

const PITCH_CLASSES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const ENHARMONIC_FLATS: Record<string, string> = {
  Db: 'C#', Eb: 'D#', Gb: 'F#', Ab: 'G#', Bb: 'A#',
};

const normalizeRoot = (root: string): string => ENHARMONIC_FLATS[root] ?? root;

/** Parse "C", "Cm", "C#7", "F#m7b5" → "C", "C#" etc. (the root only). */
const parseRoot = (chordLabel: string): string => {
  const match = chordLabel.match(/^([A-G])([#b♯♭]?)/);
  if (!match) return 'C';
  const letter = match[1];
  const accidental = match[2].replace('♯', '#').replace('♭', 'b');
  return normalizeRoot(letter + accidental);
};

const isMinorChord = (chordLabel: string): boolean =>
  /^[A-G][#b♯♭]?m(?!aj)/.test(chordLabel);

/** Pitch class index 0..11 for a root name. */
const pitchClassIndex = (root: string): number => {
  const idx = PITCH_CLASSES.indexOf(normalizeRoot(root));
  return idx === -1 ? 0 : idx;
};

/** Diatonic-degree → chord function lookup. Major and minor key flavor. */
const FUNCTION_BY_DEGREE: Record<string, Record<number, ChordFunction>> = {
  major: {
    0: 'tonic',        // I
    2: 'mediant',      // ii
    4: 'mediant',      // iii
    5: 'predominant',  // IV
    7: 'dominant',     // V
    9: 'submediant',   // vi
    11: 'leading',     // vii°
  },
  minor: {
    0: 'tonic',        // i
    2: 'predominant',  // ii°
    3: 'mediant',      // III (relative major)
    5: 'predominant',  // iv
    7: 'dominant',     // V (raised) / v
    8: 'submediant',   // VI
    10: 'leading',     // VII
  },
};

const getChordFunction = (
  chordLabel: string,
  tonicRoot: string,
  mode: string,
  isDiatonic: boolean,
): ChordFunction => {
  if (!isDiatonic) return 'chromatic';
  const flavor = /minor|aeolian|phrygian|locrian|dorian/i.test(mode) ? 'minor' : 'major';
  const degree = (pitchClassIndex(parseRoot(chordLabel)) - pitchClassIndex(tonicRoot) + 12) % 12;
  return FUNCTION_BY_DEGREE[flavor][degree] ?? 'chromatic';
};

/** Build a quick Roman numeral. Approximate — good enough for the timeline. */
const romanForDegree = (
  degree: number,
  flavor: 'major' | 'minor',
  isMinor: boolean,
): string => {
  const majorMap: Record<number, string> = {
    0: 'I', 2: 'ii', 4: 'iii', 5: 'IV', 7: 'V', 9: 'vi', 11: 'vii°',
  };
  const minorMap: Record<number, string> = {
    0: 'i', 2: 'ii°', 3: 'III', 5: 'iv', 7: 'V', 8: 'VI', 10: 'VII',
  };
  const base = (flavor === 'major' ? majorMap : minorMap)[degree];
  if (base) return base;
  // Off-diatonic — show as ♭ or ♯ inflection of the nearest pitch class.
  const accidentals = ['♭I', 'I', '♭II', 'II', '♭III', 'III', '♯IV', 'IV', '♭V', 'V', '♭VI', 'VI', '♭VII'];
  return isMinor ? accidentals[degree].toLowerCase() : accidentals[degree];
};

const computeRoman = (chord: AudioChordEvent, tonicRoot: string, mode: string): string => {
  const flavor: 'major' | 'minor' = /minor|aeolian|phrygian|locrian|dorian/i.test(mode) ? 'minor' : 'major';
  const degree = (pitchClassIndex(parseRoot(chord.chord_label)) - pitchClassIndex(tonicRoot) + 12) % 12;
  const isMinor = isMinorChord(chord.chord_label);
  let roman = romanForDegree(degree, flavor, isMinor);
  // Tag dominant 7s with a superscript-ish "7"
  if (/7/.test(chord.chord_label) && !/maj7/i.test(chord.chord_label)) roman += '7';
  if (/maj7/i.test(chord.chord_label)) roman += 'maj7';
  return roman;
};

export const enrichAudioResult = (response: AudioAnalysisResponse): EnrichedAudioResult => {
  const tonicRoot = parseRoot(response.local.tonic || response.global.tonic || 'C');
  const mode = response.local.mode || response.global.mode || 'major';

  // Backend returns segment-relative timestamps (0..segmentSpan). We shift
  // them to absolute file seconds here so every downstream consumer sees a
  // single consistent time basis — the Timeline canvas, the chord cards, the
  // hover tooltips, and the audio playback all agree on what "0:35" means.
  const segmentOffset = response.segment.start || 0;
  const chord_progression: EnrichedChordEvent[] = response.chord_progression.map((c) => ({
    ...c,
    start_time: c.start_time + segmentOffset,
    end_time: c.end_time + segmentOffset,
    function: getChordFunction(c.chord_label, tonicRoot, mode, c.is_diatonic),
    roman: computeRoman(c, tonicRoot, mode),
  }));

  // 24-key histogram: backend-side `key_score_table` is "B Aeolian" → score.
  // Sort descending; we render this in AnalysisDetails.
  let key_scores: KeyCandidate[] = [];
  if (response.key_analysis_details?.synthesis?.key_score_table) {
    key_scores = Object.entries(response.key_analysis_details.synthesis.key_score_table)
      .map(([key, score]) => {
        const [t, m = 'Ionian'] = key.split(/\s+/);
        return { tonic: t, mode: m, score: typeof score === 'number' ? score : 0 };
      })
      .sort((a, b) => b.score - a.score);
  }

  // Ensemble approach contributions — for the diagnostic panel.
  let ensemble: { approaches: Record<string, EnsembleApproach> } | undefined;
  if (response.key_analysis_details?.approaches?.length) {
    const approaches = response.key_analysis_details.approaches;
    const totalContribution = approaches.reduce(
      (sum, a) => sum + (a.weight ?? 0) * (a.top_3?.[0]?.score ?? 0),
      0,
    );
    const records: Record<string, EnsembleApproach> = {};
    for (const a of approaches) {
      const top = a.top_3?.[0];
      const contribution =
        totalContribution > 0 ? ((a.weight ?? 0) * (top?.score ?? 0)) / totalContribution : 0;
      records[a.name] = {
        weight: a.weight ?? 0,
        contribution,
        top: { tonic: top?.key.tonic ?? '?', mode: top?.key.mode ?? '?', score: top?.score ?? 0 },
        candidates: (a.top_3 ?? []).map((c) => ({
          tonic: c.key.tonic,
          mode: c.key.mode,
          score: c.score,
        })),
      };
    }
    ensemble = { approaches: records };
  }

  // Borrowed labels: prefer backend's `local.borrowed_tones`; fall back to
  // unique chord_labels with is_diatonic=false.
  let borrowedLabels = response.local.borrowed_tones ?? [];
  if (borrowedLabels.length === 0) {
    const seen = new Set<string>();
    for (const c of response.chord_progression) {
      if (!c.is_diatonic && !seen.has(c.chord_label)) {
        seen.add(c.chord_label);
      }
    }
    borrowedLabels = Array.from(seen);
  }

  const keysMatch =
    normalizeRoot(response.global.tonic) === normalizeRoot(response.local.tonic) &&
    response.global.mode === response.local.mode;

  return {
    duration: response.segment.end - response.segment.start || response.segment.end || 0,
    global: response.global,
    local: response.local,
    analysis: {
      cadence_detected: response.analysis.cadence_detected,
      cadence_strength: response.analysis.cadence_strength,
      key_scores,
      ensemble,
    },
    chord_progression,
    segment: response.segment,
    tempo: response.tempo,
    keysMatch,
    borrowedLabels,
  };
};

export const formatTime = (seconds: number): string => {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
};

/**
 * Drop chord events that fall over silent or near-silent audio. The library's
 * chord estimator can keep firing on harmonic decay (overtones in a release
 * tail, room hum, etc.) even though no real chord is being played. Since we
 * already have the waveform peaks for the canvas display, we can use them
 * directly: for each chord event, peek at the peak slice that overlaps it
 * and require the max amplitude to clear a noise threshold.
 *
 * threshold defaults to 0.04 of full-scale, which empirically separates
 * "audible chord" from "decay tail" without dropping legitimate quiet chords.
 */
export const filterAudibleChords = <T extends { start_time: number; end_time: number }>(
  chords: T[],
  peaks: number[],
  fileDuration: number,
  threshold: number = 0.04,
): T[] => {
  if (!peaks.length || fileDuration <= 0 || chords.length === 0) return chords;
  return chords.filter((c) => {
    const startIdx = Math.max(0, Math.floor((c.start_time / fileDuration) * peaks.length));
    const endIdx = Math.min(peaks.length, Math.ceil((c.end_time / fileDuration) * peaks.length));
    if (endIdx <= startIdx) return false;
    let maxPeak = 0;
    for (let i = startIdx; i < endIdx; i++) {
      if (peaks[i] > maxPeak) maxPeak = peaks[i];
    }
    return maxPeak >= threshold;
  });
};
