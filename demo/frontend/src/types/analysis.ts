// Opening move: TypeScript types mirroring the backend API contract
// This keeps our frontend in sync with the Pydantic models on the server side

export interface AnalysisRequest {
  chords?: string[];
  key?: string;
  profile?: string;
  include_educational?: boolean;
}

// Glossary entry shape from the engine. Older endpoints emitted a bare term
// string; newer ones emit an object with definition + example fields. We
// tolerate both at the type level so consumers can guard at runtime.
export interface GlossaryEntry {
  definition?: string;
  example_in_C_major?: string;
  term?: string;
  type?: string;
}

// Pattern match details from the unified pattern engine
export interface PatternMatch {
  start: number;
  end: number;
  pattern_id: string;
  name: string;
  family: string;
  score: number;
  evidence: Array<{
    features: Record<string, number>;
  }>;
  glossary: GlossaryEntry | string | null;
  section: string | null;
  cadence_role: string | null;
  is_section_closure: boolean;
  // Multi-profile fields: style-aware pattern metadata
  style_tags?: string[];
  detected_via_profile?: string;
  style_typicality?: number;
}

// Modal evidence details
export interface ModalEvidence {
  type: string;
  strength: number;
  description: string;
}

// Glossary term definition
export interface GlossaryTerm {
  label: string;
  tooltip: string;
}

// Chromatic element structure for non-diatonic analysis
export interface ChromaticElement {
  symbol: string;
  type?: string;
  resolution?: string;
  strength?: number;
  explanation?: string;
}

// Multi-profile: per-style analysis detail
export interface StyleAnalysisDetail {
  style_name: string;
  confidence: number;
  typicality: number;
  patterns: PatternMatch[];
  style_notes?: string;
  characteristic_features: string[];
}

export interface PrimaryInterpretation {
  key_signature: string;
  roman_numerals: string[];
  confidence: number;
  interpretation?: string;
  reasoning?: string;
  type?: string;
  mode?: string | null;
  scale_degrees?: string[];
  functional_analysis?: string;
  cadence_detection?: string;
  functional_confidence?: number;
  modal_confidence?: number;
  chromatic_confidence?: number;
  // New fields from unified pattern engine
  patterns?: PatternMatch[];
  modal_characteristics?: string[];
  modal_evidence?: ModalEvidence[];
  chromatic_elements?: ChromaticElement[];
  chromatic_summary?: string | null;
  terms?: Record<string, GlossaryTerm>;
  // Multi-profile: dominant style and style confidence breakdown
  dominant_style?: string;
  style_typicality?: number;
  style_confidence?: Record<string, number>;
  style_analysis?: Record<string, StyleAnalysisDetail>;
}

// Victory lap: Educational content types
export interface VisualizationHints {
  chord_colors: string[]; // ["PD", "D", "T"] for predominant, dominant, tonic
  bracket_range: {
    start: number;
    end: number;
  };
}

/**
 * Educational card for pattern summaries.
 * Progressive disclosure model: Users explore depth through interaction, not skill level labels.
 */
export interface EducationalCard {
  pattern_id: string;
  title: string;
  summary: string;
  category?: string;
  visualization?: VisualizationHints;
}

export interface TechnicalNotes {
  voice_leading?: string;
  theoretical_depth?: string;
  historical_context?: string;
}

export interface FullExplanation {
  pattern_id: string;
  title: string;
  // Layer 1: Core Bernstein-style explanation
  hook: string;
  breakdown: string[];
  story: string;
  composers: string;
  examples: string[];
  try_this: string;
  // Layer 2: Optional technical depth
  technical_notes?: TechnicalNotes;
}

export interface EducationalPayload {
  available: boolean;
  content?: EducationalCard[];
  explanations?: Record<string, FullExplanation>;
}

export interface AnalysisResponse {
  summary: string;
  analysis: {
    primary: PrimaryInterpretation;
    alternatives?: PrimaryInterpretation[];
    functional_summary?: string;
    modal_summary?: string;
    chromatic_summary?: string;
  };
  enhanced_summaries?: {
    patterns_detected?: string[];
    cadences?: string[];
    tonicizations?: string[];
  };
  educational?: EducationalPayload;
}

// Big play: File upload response type matching backend /api/analyze/file schema
export interface ChordWithMeasure {
  measure: number;
  chord: string;
  offset: number;
}

export interface FileMetadata {
  title?: string;
  composer?: string;
  [key: string]: unknown; // Other metadata fields from MusicXML/MIDI
}

export interface FileAnalysisResponse {
  chord_symbols: string[];
  chordified_symbols_with_measures: ChordWithMeasure[];
  key_hint?: string;
  metadata?: FileMetadata;
  notation_url?: string;
  download_url?: string;
  analysis_result?: AnalysisResponse;
  measure_count: number;
  truncated_for_display: boolean;
  is_midi: boolean;
  parsing_logs?: string;
  window_size_used?: number;
}

// Keys endpoint response type
export interface KeysResponse {
  keys: string[];
}
