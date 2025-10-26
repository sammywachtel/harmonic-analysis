"""
Pydantic models for REST API request/response validation.

Opening move: Define request and response schemas for all API endpoints.
These models provide automatic validation, serialization, and OpenAPI documentation.
"""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


# Kickoff: Helper function for CSV parsing (used by validators)
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
    profile: Optional[str] = Field(default="classical", description="Style profile")
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
    profile: str = Field(
        default="classical", description="Analysis profile (classical, jazz, pop, etc.)"
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
