// Opening move: TypeScript types mirroring the backend API contract
// This keeps our frontend in sync with the Pydantic models on the server side

export interface AnalysisRequest {
  chords?: string[];
  key?: string;
  profile?: string;
  include_educational?: boolean;
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
  glossary: string | null;
  section: string | null;
  cadence_role: string | null;
  is_section_closure: boolean;
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
  chromatic_elements?: string[];
  chromatic_summary?: string | null;
  terms?: Record<string, GlossaryTerm>;
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
