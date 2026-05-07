"""
Pydantic models for REST API request/response validation.

Opening move: Define request and response schemas for all API endpoints.
These models provide automatic validation, serialization, and OpenAPI documentation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

# Kickoff: Define profile type for validation
ProfileType = Literal["classical", "jazz", "pop", "modal"]


# Helper function for CSV parsing (used by validators)
def parse_csv(text: str) -> List[str]:
    """Parse comma or space-separated input into list."""
    if "," in text:
        return [item.strip() for item in text.split(",") if item.strip()]
    return [item.strip() for item in text.split() if item.strip()]


# Main play: Request models for different analysis types
class ProgressionRequest(BaseModel):
    """Request model for chord/roman/melody/scale progression analysis."""

    key: Optional[str] = Field(
        default=None, description="Optional key hint (e.g. 'C major')"
    )
    profile: Optional[Literal["classical", "jazz", "pop", "modal"]] = Field(
        default="classical", description="Style profile (classical/jazz/pop/modal)"
    )
    chords: Optional[List[str]] = Field(default=None, description="Chord symbols")
    romans: Optional[List[str]] = Field(default=None, description="Roman numerals")
    melody: Optional[List[str]] = Field(default=None, description="Melodic notes")
    scales: Optional[List[List[str]]] = Field(
        default=None,
        description="List of candidate scales (each scale is a list of notes)",
    )
    include_educational: bool = Field(
        default=True, description="Include educational content if available"
    )

    @field_validator("chords", "romans", "melody", mode="before")
    @classmethod
    def _coerce_sequence(cls, value: Any) -> Optional[List[str]]:
        """Big play: coerce string input to lists for flexibility."""
        if value is None:
            return None
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value  # type: ignore[no-any-return]

    @field_validator("scales", mode="before")
    @classmethod
    def _coerce_scales(cls, value: Any) -> Optional[List[List[str]]]:
        """Victory lap: handle multi-line scale input."""
        if value is None:
            return None
        if isinstance(value, str):
            lines = [line.strip() for line in value.splitlines() if line.strip()]
            return [parse_csv(line) for line in lines]
        if isinstance(value, list) and value and isinstance(value[0], str):
            return [parse_csv(item) for item in value]
        return value  # type: ignore[no-any-return]


class ScaleRequest(BaseModel):
    """Request model for dedicated scale analysis."""

    notes: List[str]
    key: Optional[str] = Field(default=None, description="Key context (required)")

    @field_validator("notes", mode="before")
    @classmethod
    def _coerce_notes(cls, value: Any) -> List[str]:
        """Main play: coerce string to list if needed."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value  # type: ignore[no-any-return]


class MelodyRequest(ScaleRequest):
    """Request model for melody analysis (identical shape to ScaleRequest)."""

    pass


class FileUploadRequest(BaseModel):
    """
    Request parameters for file upload analysis.

    Note: The file itself comes through FastAPI's UploadFile parameter,
    this model captures the additional configuration options.
    """

    add_chordify: bool = Field(
        default=True, description="Generate chord reduction using music21's chordify"
    )
    label_chords: bool = Field(
        default=True, description="Add chord symbol labels to notation"
    )
    run_analysis: bool = Field(
        default=False,
        description="Run harmonic analysis on extracted progression",
    )
    profile: Optional[Literal["classical", "jazz", "pop", "modal"]] = Field(
        default="classical", description="Analysis profile (classical/jazz/pop/modal)"
    )
    process_full_file: bool = Field(
        default=False,
        description="Process entire file (vs first 20 measures for preview)",
    )
    auto_window: bool = Field(
        default=True, description="Auto-calculate window size from tempo"
    )
    manual_window_size: float = Field(
        default=1.0, description="Manual window size in quarter lengths (if auto=False)"
    )
    key_mode_preference: str = Field(
        default="Major",
        description=(
            "Treat key signature as Major or Minor "
            "(e.g., 2 sharps = D major or B minor)"
        ),
    )


# Victory lap: Response models (if needed for strict typing)
class EducationalPayload(BaseModel):
    """Educational content payload for analysis responses."""

    available: bool = Field(
        description="Whether educational features are installed and available"
    )
    content: Optional[List[dict]] = Field(
        default=None,
        description="List of educational cards for detected patterns",
    )


class AnalysisResponse(BaseModel):
    """Generic response model for analysis endpoints."""

    summary: dict
    analysis: dict
    enhanced_summaries: Optional[dict] = None
    educational: Optional[EducationalPayload] = Field(
        default=None, description="Educational enrichment for detected patterns"
    )


class FileAnalysisResponse(BaseModel):
    """Response model for file upload endpoint."""

    chord_symbols: List[str]
    chordified_symbols_with_measures: Optional[List[dict]] = None
    key_hint: Optional[str] = None
    metadata: dict
    notation_url: str
    download_url: str
    analysis_result: Optional[dict] = None
    measure_count: int
    truncated_for_display: bool
    is_midi: bool
    parsing_logs: Optional[str] = None
    window_size_used: Optional[float] = None


class ProfileInfo(BaseModel):
    """Information about a single analysis profile."""

    name: str = Field(description="Profile identifier (e.g., 'classical')")
    display_name: str = Field(description="Human-readable name (e.g., 'Classical')")
    description: str = Field(description="Brief description of the profile")
    enabled: bool = Field(default=True, description="Whether this profile is available")


class ProfileResponse(BaseModel):
    """Response model for available profiles endpoint."""

    profiles: List[ProfileInfo] = Field(
        description="List of available analysis profiles"
    )


# Audio analysis models — documentation/parity guard only.
# The route returns Dict[str, Any] (DD3), not a typed response_model.
# These exist so the shape is declared once and can be validated in tests.


class ChordEventModel(BaseModel):
    """A single timestamped chord event from the audio pipeline."""

    start_time: float = Field(description="Start time in seconds")
    end_time: float = Field(description="End time in seconds")
    chord_label: str = Field(description="Detected chord symbol (e.g. 'C', 'Am')")
    confidence: float = Field(description="Cosine similarity confidence 0-1")
    is_diatonic: bool = Field(
        description="Whether the chord belongs to the estimated key"
    )


class _KeyInfoModel(BaseModel):
    """Key estimation subset — excludes diatonic_pitch_classes (frozenset, not JSON-safe)."""

    tonic: str
    mode: str
    key_signature: str
    confidence: float


class _LocalKeyModel(_KeyInfoModel):
    """Key info plus region classification for the local key.

    The route flattens KeyInfo + RegionInfo into one dict under ``local``.
    This model reflects that combined shape so the OpenAPI schema stays honest.
    """

    region_type: str
    region_confidence: float
    borrowed_tones: List[str] = Field(default_factory=list)


class _RegionModel(BaseModel):
    """Region classification result."""

    type: str
    confidence: float
    borrowed_tones: List[str] = Field(default_factory=list)


class _AnalysisModel(BaseModel):
    """Cadence detection summary."""

    cadence_detected: bool
    cadence_strength: float


class _SegmentModel(BaseModel):
    """Analyzed time window."""

    start: float
    end: float


class _TempoRegionModel(BaseModel):
    """One constant-tempo span detected during variable-tempo analysis."""

    start_time: float
    end_time: float
    bpm: float
    confidence: float


class _TempoModel(BaseModel):
    """BPM metadata for the analyzed segment.

    Populated when ``rubato="auto"`` triggered tempo detection. ``regions``
    is empty for stable-tempo material (one region or detection failure);
    multiple entries appear when the music has sustained tempo changes.
    """

    bpm: float
    confidence: float
    regions: List[_TempoRegionModel] = []


class AudioAnalysisResponse(BaseModel):
    """Shape of the JSON returned by POST /api/analyze/audio.

    Mirrors the dict the route builds manually. Does NOT include
    ``diatonic_pitch_classes`` (frozenset is not JSON-serializable)
    or ``visuals`` (not produced by the library).
    """

    global_key: _KeyInfoModel = Field(alias="global")
    local_key: _LocalKeyModel = Field(alias="local")
    analysis: _AnalysisModel
    chord_progression: List[ChordEventModel]
    segment: _SegmentModel
    tempo: Optional[_TempoModel] = None
    key_analysis_details: Optional["KeyAnalysisDetails"] = None

    model_config = {"populate_by_name": True}


# Diagnostic-panel models. The route returns Dict[str, Any], so these
# exist to document the shape and feed OpenAPI. Same loose-typing pattern
# as the rest of the audio response models above.


class _RankedKey(BaseModel):
    """One row in an approach's top_3 ranking — KeyInfo + score."""

    key: _KeyInfoModel
    score: float


class KeyApproachDetail(BaseModel):
    """One approach's contribution to the diagnostic panel.

    Each approach reports its name, the weight applied during synthesis,
    and the top-3 candidates it produced. The full ranked list lives in
    the synthesis ``key_score_table`` — top_3 is what humans look at first.
    """

    name: str = Field(description="Approach identifier, e.g. 'template_correlation'")
    weight: float = Field(description="Weight applied to this approach's votes")
    top_3: List[_RankedKey] = Field(
        default_factory=list,
        description="Top-3 (KeyInfo, score) candidates from this approach",
    )


class SynthesisDetail(BaseModel):
    """Synthesizer's output for the diagnostic panel.

    Mirrors ``SynthesisResult`` but uses dict-of-floats for the score
    table so the JSON response can be parsed without custom decoders.
    """

    method: str = Field(description="Synthesis method, e.g. 'weighted_sum'")
    winner: _KeyInfoModel
    runner_up: Optional[_KeyInfoModel] = None
    margin: float = Field(description="winner_total - runner_up_total")
    key_score_table: Dict[str, float] = Field(
        default_factory=dict,
        description="All candidates' summed weighted scores, keyed by key_signature",
    )


class KeyAnalysisDetails(BaseModel):
    """Top-level diagnostic-panel payload.

    Populated only when the request includes ``show_details=true``.
    iteration_01 doesn't ship HMM segmentation, so ``modulations`` is
    always None for now.
    """

    approaches: List[KeyApproachDetail] = Field(default_factory=list)
    synthesis: SynthesisDetail
    modulations: Optional[List[dict]] = None
