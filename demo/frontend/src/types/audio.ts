// Audio-analysis type contracts. Mirror the FastAPI shapes returned by
// POST /api/analyze/audio (see demo/backend/rest_api/routes.py:418-594 and
// demo/backend/rest_api/models.py:195-324). These are server-side names on
// purpose — keep snake_case so the JSON parses straight in.

export interface AudioGlobalKey {
  tonic: string;          // "A", "F#", "Bb", or "N/A" if undetectable
  mode: string;           // "Ionian", "Aeolian", "N/A", etc.
  key_signature: string;  // "3 sharps", "D major / B minor", etc.
  confidence: number;     // 0..1
}

export interface AudioLocalKey extends AudioGlobalKey {
  region_type: 'stable' | 'modulation' | 'modal_shift' | string;
  region_confidence: number;
  borrowed_tones: string[]; // pitch class labels of borrowed chords
}

export interface AudioChordEvent {
  start_time: number;       // seconds
  end_time: number;         // seconds
  chord_label: string;      // "C", "Am", "C#m"
  confidence: number;       // 0..1, cosine sim
  is_diatonic: boolean;
}

export interface AudioCadenceSummary {
  cadence_detected: boolean;
  cadence_strength: number;
}

export interface AudioSegment {
  start: number;
  end: number;
}

// Tempo metadata — populated when rubato="auto" triggered detection.
// `regions` is empty for stable-tempo material; multiple entries appear
// when the music has sustained tempo changes (e.g., accelerando section
// breaks).
export interface AudioTempoRegion {
  start_time: number;
  end_time: number;
  bpm: number;
  confidence: number;
}

export interface AudioTempo {
  bpm: number;
  confidence: number;
  regions: AudioTempoRegion[];
}

// Diagnostic panel — only populated when show_details=true was sent.
export interface KeyApproachCandidate {
  key: AudioGlobalKey;
  score: number;
}

export interface KeyApproachDetail {
  name: string;
  weight: number;
  description?: string;
  top_3: KeyApproachCandidate[];
  meta?: Record<string, unknown> | null;
}

export interface SynthesisDetail {
  method: string;                  // e.g. "weighted_sum"
  winner: AudioGlobalKey;
  runner_up: AudioGlobalKey | null;
  margin: number;
  key_score_table: Record<string, number>; // "B Aeolian" → score
}

export interface KeyAnalysisDetails {
  approaches: KeyApproachDetail[];
  synthesis: SynthesisDetail;
  modulations: null;               // iteration_02 placeholder
}

export interface AudioAnalysisResponse {
  global: AudioGlobalKey;
  local: AudioLocalKey;
  analysis: AudioCadenceSummary;
  chord_progression: AudioChordEvent[];
  segment: AudioSegment;
  tempo?: AudioTempo;
  key_analysis_details?: KeyAnalysisDetails;
}

// ── Frontend-side enriched shape ────────────────────────────────────────────
// audioAdapter.ts expands the raw response into this for the components.

export type ChordFunction =
  | 'tonic'
  | 'predominant'
  | 'dominant'
  | 'submediant'
  | 'mediant'
  | 'leading'
  | 'chromatic';

export interface EnrichedChordEvent extends AudioChordEvent {
  function: ChordFunction;
  /** Roman numeral derived from chord_label + local key, when computable. */
  roman?: string;
}

export interface KeyCandidate {
  tonic: string;
  mode: string;
  score: number;
}

export interface EnsembleApproach {
  weight: number;
  contribution: number;             // weight * top.score, normalized over total
  top: { tonic: string; mode: string; score: number };
  candidates: KeyCandidate[];
}

export interface EnrichedAudioResult {
  duration: number;
  global: AudioGlobalKey;
  local: AudioLocalKey;
  analysis: AudioCadenceSummary & {
    key_scores: KeyCandidate[];     // sorted desc, full 24-key histogram
    ensemble?: { approaches: Record<string, EnsembleApproach> };
  };
  chord_progression: EnrichedChordEvent[];
  segment: AudioSegment;
  /** Tempo info from auto-rubato detection. `undefined` when the caller
   *  used a static rubato preset (no detection performed). */
  tempo?: AudioTempo;
  /** When global tonic+mode == local tonic+mode (modulo enharmonic), the
   *  region card calls out "same notes, different tonal center". */
  keysMatch: boolean;
  /** Pre-computed list of borrowed labels — falls back to scanning
   *  chord_progression for !is_diatonic when local.borrowed_tones is empty. */
  borrowedLabels: string[];
}

// ── Audio analyze request options ───────────────────────────────────────────
export type KeyDetectionPreset = 'default' | 'ks_only' | 'full';
export type RubatoPreset = 'auto' | 'strict' | 'moderate' | 'loose' | 'free';

export interface AnalyzeAudioOptions {
  start?: number;       // segment start in seconds
  end?: number;         // segment end in seconds
  showDetails?: boolean;
  preset?: KeyDetectionPreset;
  /** Optional weight overrides per approach name. */
  weights?: Record<string, number>;

  // ── Timing & tempo ──────────────────────────────────────────────────
  /** Chord-window timing preset. `"auto"` (default in the demo) detects BPM
   *  and sizes the analysis window dynamically. Static presets override auto.
   *  A number 0.0–1.0 interpolates between strict and free. */
  rubato?: RubatoPreset | number;
  /** Fractional BPM change above which auto-rubato emits a separate tempo
   *  region. Library default 0.20 (= 20%). Lower values over-segment;
   *  higher values miss real tempo changes. Only effective when
   *  `rubato="auto"`. */
  tempoRegionThreshold?: number;

  // ── Chord matching ──────────────────────────────────────────────────
  /** Diatonic similarity bonus for chord estimation. Library default 0.15.
   *  Higher values bias chord matching toward in-key chords. */
  tonalBias?: number;
  /** Magnitude of the bass-register root-match bonus when use_bass_chroma is
   *  enabled. Library default 0.3. */
  bassBonus?: number;
  /** When true, the chord estimator extracts a bass-register chroma layer to
   *  disambiguate roots (Am vs C, Bm vs D). Library default false. */
  useBassChroma?: boolean;
  /** Minimum bass-chroma peakiness for the bass-bonus to fire. Library
   *  default 0.25. Higher values restrict the bonus to very clear bass
   *  signals. Only meaningful when useBassChroma is on. */
  bassConfidenceThreshold?: number;

  // ── Silence detection ───────────────────────────────────────────────
  /** Absolute RMS amplitude floor below which a window is treated as
   *  silence. Library default 0.005 (~-46 dBFS). */
  rmsSilenceThreshold?: number;
  /** Length in seconds of the trailing window the adaptive (envelope-
   *  relative) silence gate uses for context. Library default 3.0s.
   *  Set to 0 to disable adaptive gating. */
  trailingSilenceWindowS?: number;
  /** Threshold for the adaptive gate as a fraction of trailing-window mean
   *  RMS. Library default 0.10 (current window must be >10% of recent
   *  loudness, ~20 dB drop). Set to 0 to disable. */
  trailingSilenceRatio?: number;

  // ── Chord consolidation ─────────────────────────────────────────────
  /** When true (default), adjacent same-root chord events with different
   *  qualities are merged into one. Disable to see the raw matcher output. */
  mergeSameRoot?: boolean;
  /** Upper cap (seconds) on a merged chord event's duration. Real chord
   *  changes across bar lines shouldn't fuse just because they share a
   *  root. Library default 4.0s (≈ one measure at typical tempos). */
  maxMergeDurationS?: number;

  /** When true, the demo also runs the extracted chord labels through the
   *  library's pattern analysis (the same engine Manual entry uses) and
   *  renders the full Roman / cadence / pattern result tree. */
  runPatternAnalysis?: boolean;
}
