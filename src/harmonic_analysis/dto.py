"""
Stable API types for the harmonic analysis library.

These DTOs form the public contract between the library and its users.
They should evolve carefully to maintain backwards compatibility.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

# -----------------------------
# Enums
# -----------------------------
# Define enumeration types used throughout the analysis DTOs.
# These enums provide a fixed set of string values representing analysis categories.


class AnalysisType(str, Enum):
    FUNCTIONAL = "functional"
    MODAL = "modal"
    CHROMATIC = "chromatic"


class ProgressionType(str, Enum):
    """Classification of chord progression types for arbitration heuristics"""

    CLEAR_FUNCTIONAL = "clear_functional"
    CLEAR_MODAL = "clear_modal"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"


# -----------------------------
# Leaf DTOs
# -----------------------------
# Basic data transfer objects representing elemental components of harmonic analysis,
# such as individual chords, detected patterns, chromatic elements,
# and evidence entries.


@dataclass
class FunctionalChordDTO:
    """A single chord as analyzed functionally."""

    chord_symbol: str  # e.g., "Dm7"
    roman_numeral: Optional[str] = None  # e.g., "ii7"
    function: Optional[str] = None  # e.g., "predominant"
    inversion: Optional[int] = None  # 0 = root position, etc.
    quality: Optional[str] = None  # "triad", "seventh", etc.
    secondary_of: Optional[str] = None  # e.g., "V" for V/V
    is_chromatic: Optional[bool] = None
    bass_note: Optional[str] = None  # e.g., "G" if slash chord


@dataclass
class SectionDTO:
    """A labeled section of the analyzed piece (e.g., verse, chorus)."""

    id: str  # e.g., "A", "B", "Bridge", or "0", "1"
    start: int  # inclusive chord index
    end: int  # exclusive chord index
    label: Optional[str] = None  # optional display name


@dataclass
class PatternMatchDTO:
    """A detected harmonic pattern (cadence, schema, etc.)."""

    start: int
    end: int
    pattern_id: str
    name: str
    family: str
    score: float
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    glossary: Optional[Dict[str, Any]] = None
    # Section-aware fields (as per music-alg-2h.md specification)
    section: Optional[str] = None  # Section ID: "A", "B", "Verse1", etc.
    cadence_role: Optional[Literal["final", "section-final", "internal"]] = (
        None  # Cadence type
    )
    is_section_closure: Optional[bool] = None  # True if pattern closes a section


@dataclass
class ChromaticElementDTO:
    """A chromatic device (e.g., secondary_dominant, mixture)."""

    index: int  # chord index in progression
    symbol: str  # chord symbol (e.g., "A7")
    type: str  # e.g., "secondary_dominant", "mixture", "chromatic_mediant"
    resolution: Optional[str] = None  # resolution pattern (e.g., "A7→Dm")
    strength: Optional[float] = None  # confidence/strength score
    explanation: Optional[str] = None  # detailed explanation

    # Modern dual-surface target fields
    target_chord: Optional[str] = None  # chord symbol target (e.g., "Dm")
    target_roman: Optional[str] = None  # roman numeral target (e.g., "ii")

    def __str__(self) -> str:
        """Human-readable string representation."""
        # Format: "A7 (V/ii) → Dm [0.82]" or "Ab (mixture) [0.75]"
        parts = [self.symbol]

        # Get the target to display (prefer roman, fall back to chord, then legacy)
        display_target = self.target_roman or self.target_chord

        # Add type/function info
        if self.type == "secondary_dominant" and display_target:
            parts.append(f"(V/{display_target})")
        elif self.type == "applied_leading" and display_target:
            parts.append(f"(vii°/{display_target})")
        else:
            parts.append(f"({self.type})")

        # Add resolution if present (prefer chord symbol for resolution display)
        if self.resolution:
            resolution_target = self.target_chord or display_target or "unresolved"
            parts.append(f"→ {resolution_target}")

        # Add strength if present
        if self.strength is not None:
            parts.append(f"[{self.strength:.2f}]")

        return " ".join(parts)

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"ChromaticElementDTO(index={self.index}, symbol='{self.symbol}', "
            f"type='{self.type}', target_chord={self.target_chord!r}, "
            f"target_roman={self.target_roman!r}, strength={self.strength})"
        )


@dataclass
class ChromaticSummaryDTO:
    """Summary of chromatic analysis findings."""

    counts: Dict[str, int] = field(default_factory=dict)  # type counts
    has_applied_dominants: bool = False
    borrowed_key_area: Optional[str] = None
    notes: List[str] = field(default_factory=list)  # observations


@dataclass
class ScaleSummaryDTO:
    """Summary of scale analysis findings."""

    detected_mode: Optional[str] = None  # "Dorian", "Phrygian", "Ionian", etc.
    parent_key: Optional[str] = None  # "C major", "D minor", etc.
    degrees: List[int] = field(
        default_factory=list
    )  # Scale degrees [1, 2, 3, 4, 5, 6, 7]
    characteristic_notes: List[str] = field(
        default_factory=list
    )  # ["♭7", "♭3"] for notable intervals
    notes: List[str] = field(
        default_factory=list
    )  # Actual note names ["C", "D", "E♭", ...]


@dataclass
class MelodySummaryDTO:
    """Summary of melody analysis findings."""

    intervals: List[int] = field(
        default_factory=list
    )  # Semitone intervals between notes
    contour: Optional[str] = None  # "ascending", "descending", "arch", "wave"
    range_semitones: Optional[int] = None  # Total melodic range in semitones
    leading_tone_resolutions: int = 0  # Count of leading tone → tonic resolutions
    suspensions: int = 0  # Count of suspension patterns
    chromatic_notes: List[str] = field(default_factory=list)  # Non-diatonic notes
    melodic_characteristics: List[str] = field(
        default_factory=list
    )  # ["stepwise motion", "leap emphasis"]


@dataclass
class EvidenceDTO:
    """Arbitration/tracing evidence for why an analysis was chosen."""

    reason: str  # short reason code, e.g., "modal-vamp"
    details: Dict[str, Any] = field(default_factory=dict)


# -----------------------------
# Core summaries
# -----------------------------
# DTOs summarizing the results of harmonic analysis interpretations,
# including either functional or modal analyses, confidence scores,
# and detailed metadata.


@dataclass
class AnalysisSummary:
    """
    Summary of a single harmonic analysis interpretation.

    This represents either a functional analysis (e.g., I–IV–V–I) or a modal analysis
    (e.g., G Mixolydian over C major parent key) with confidence metrics and details.
    """

    type: AnalysisType
    roman_numerals: List[str]
    confidence: float

    # Common context
    key_signature: Optional[str] = None  # "C major", "A minor"
    mode: Optional[str] = None  # "major", "minor", "Mixolydian", etc.
    reasoning: Optional[str] = None  # human-readable rationale

    # Confidence decomposition (optional)
    functional_confidence: Optional[float] = None
    modal_confidence: Optional[float] = None
    chromatic_confidence: Optional[float] = None

    # Structured extras (optional)
    terms: Dict[str, Any] = field(default_factory=dict)
    patterns: List[PatternMatchDTO] = field(default_factory=list)
    chromatic_elements: List[ChromaticElementDTO] = field(default_factory=list)
    chromatic_summary: Optional[ChromaticSummaryDTO] = None

    # Optional chord list (useful in functional primary)
    chords: List[FunctionalChordDTO] = field(default_factory=list)

    # Optional modal features (e.g., "♭VII chord", "raised 4th")
    modal_characteristics: List[str] = field(default_factory=list)

    # Modal evidence for rich analysis (populated by modal analyzer)
    modal_evidence: List[Any] = field(
        default_factory=list
    )  # List[ModalEvidence] from analyzer

    # Scale and melody summaries (populated when scale/melody analysis is performed)
    scale_summary: Optional[ScaleSummaryDTO] = None
    melody_summary: Optional[MelodySummaryDTO] = None

    # NEW: Section-aware fields (only populated when sections are supplied)
    sections: List[SectionDTO] = field(default_factory=list)

    # NEW: all cadences that close sections (including the global final if applicable)
    terminal_cadences: List[PatternMatchDTO] = field(default_factory=list)

    # EXISTING: keep a single global final cadence (if any)
    final_cadence: Optional[PatternMatchDTO] = None

    def __post_init__(self) -> None:
        # Clamp confidence values into [0, 1] to ensure valid probability ranges.
        def clamp(x: Optional[float]) -> Optional[float]:
            if x is None:
                return None
            return min(1.0, max(0.0, x))

        self.confidence = clamp(self.confidence) or 0.0
        self.functional_confidence = clamp(self.functional_confidence)
        self.modal_confidence = clamp(self.modal_confidence)

    # Convenience (std-lib) serialization without extra deps
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Convert enum to its string value before serialization
        d["type"] = self.type.value
        return d

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "AnalysisSummary":
        """
        Deserialize a dictionary into an AnalysisSummary object.

        Handles nested DTOs and legacy key mappings for backward compatibility.

        Helper functions:
        - _pm: Converts dicts representing PatternMatchDTOs, normalizing
              keys and default values.
        - _ce: Converts dicts representing ChromaticElementDTOs,
              handling legacy keys and renaming.
        - _fc: Converts dicts representing FunctionalChordDTOs.
        """
        # Accept either a string or enum instance for analysis type
        atype = d.get("type", AnalysisType.FUNCTIONAL)
        if isinstance(atype, str):
            atype = AnalysisType(atype)

        def _pm(x: Any) -> PatternMatchDTO:
            """
            Convert a dict or object into a PatternMatchDTO.

            Handles legacy keys:
            - 'id' renamed to 'pattern_id'
            Ensures required keys are present with defaults:
            - start, end, evidence, family, name
            Converts score to float.
            """
            if isinstance(x, dict):
                y = dict(x)
                # tolerate legacy/plain keys
                if "pattern_id" not in y and "id" in y:
                    y["pattern_id"] = y.pop("id")
                y.setdefault("start", 0)
                y.setdefault("end", 0)
                y.setdefault("evidence", [])
                y.setdefault("family", y.get("family", "unknown"))
                y.setdefault("name", y.get("pattern_id", ""))
                # ensure numeric score
                y["score"] = float(y.get("score", 0.0))
                return PatternMatchDTO(**y)
            # If x is already a PatternMatchDTO, return it as-is
            if isinstance(x, PatternMatchDTO):
                return x
            # For any other type, create a default PatternMatchDTO
            return PatternMatchDTO(
                start=0, end=0, pattern_id="", name="", family="", score=0.0
            )

        def _ce(x: Any) -> ChromaticElementDTO:
            """
            Convert a dict or object into a ChromaticElementDTO.
            """
            if isinstance(x, dict):
                y = dict(x)

                # Provide required field defaults
                if "index" not in y:
                    y["index"] = 0
                if "symbol" not in y:
                    y["symbol"] = ""
                if "type" not in y:
                    y["type"] = "unknown"

                # Only keep valid fields for DTO structure
                valid_fields = {
                    "index",
                    "symbol",
                    "type",
                    "target",
                    "resolution",
                    "strength",
                    "explanation",
                    "target_chord",
                    "target_roman",
                }
                y = {k: v for k, v in y.items() if k in valid_fields}

                return ChromaticElementDTO(**y)
            # If x is already a ChromaticElementDTO, return it as-is
            if isinstance(x, ChromaticElementDTO):
                return x
            # For any other type, create a default ChromaticElementDTO
            return ChromaticElementDTO(index=0, symbol="", type="unknown")

        def _fc(x: Any) -> FunctionalChordDTO:
            """
            Convert a dict or object into a FunctionalChordDTO.

            Assumes input is a dict with appropriate keys.
            """
            return FunctionalChordDTO(**x) if isinstance(x, dict) else x

        return AnalysisSummary(
            type=atype,
            roman_numerals=list(d.get("roman_numerals", [])),
            confidence=float(d.get("confidence", 0.0)),
            key_signature=d.get("key_signature"),
            mode=d.get("mode"),
            reasoning=d.get("reasoning"),
            functional_confidence=d.get("functional_confidence"),
            modal_confidence=d.get("modal_confidence"),
            terms=dict(d.get("terms", {})),
            patterns=[_pm(x) for x in d.get("patterns", [])],
            chromatic_elements=[_ce(x) for x in d.get("chromatic_elements", [])],
            chords=[_fc(x) for x in d.get("chords", [])],
            modal_characteristics=list(d.get("modal_characteristics", [])),
            modal_evidence=list(d.get("modal_evidence", [])),
            scale_summary=(
                ScaleSummaryDTO(**d["scale_summary"])
                if d.get("scale_summary")
                else None
            ),
            melody_summary=(
                MelodySummaryDTO(**d["melody_summary"])
                if d.get("melody_summary")
                else None
            ),
            sections=[
                SectionDTO(**x) if isinstance(x, dict) else x
                for x in d.get("sections", [])
            ],
            terminal_cadences=[_pm(x) for x in d.get("terminal_cadences", [])],
            final_cadence=_pm(d["final_cadence"]) if d.get("final_cadence") else None,
        )


# -----------------------------
# Envelope (top-level result)
# -----------------------------
# The top-level DTO encapsulating the full analysis result,
# including the primary interpretation, alternative analyses, metadata, and evidence.


@dataclass
class AnalysisEnvelope:
    """
    Complete analysis result containing primary interpretation and alternatives.

    This is the main DTO returned by the PatternAnalysisService and represents
    the stable public API contract.
    """

    primary: AnalysisSummary
    alternatives: List[AnalysisSummary] = field(default_factory=list)

    # Analysis metadata
    analysis_time_ms: Optional[float] = None
    chord_symbols: List[str] = field(default_factory=list)
    evidence: List[EvidenceDTO] = field(default_factory=list)

    # Contract metadata (for forward/backward compatibility)
    schema_version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary": self.primary.to_dict(),
            "alternatives": [a.to_dict() for a in self.alternatives],
            "analysis_time_ms": self.analysis_time_ms,
            "chord_symbols": list(self.chord_symbols),
            "evidence": [asdict(e) for e in self.evidence],
            "schema_version": self.schema_version,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "AnalysisEnvelope":
        """
        Deserialize a dictionary into an AnalysisEnvelope object.

        Handles nested AnalysisSummary and EvidenceDTO objects.
        """

        def _sum(x: Any) -> AnalysisSummary:
            return AnalysisSummary.from_dict(x) if isinstance(x, dict) else x

        def _ev(x: Any) -> EvidenceDTO:
            return EvidenceDTO(**x) if isinstance(x, dict) else x

        return AnalysisEnvelope(
            primary=_sum(d["primary"]),
            alternatives=[_sum(x) for x in d.get("alternatives", [])],
            analysis_time_ms=d.get("analysis_time_ms"),
            chord_symbols=list(d.get("chord_symbols", [])),
            evidence=[_ev(x) for x in d.get("evidence", [])],
            schema_version=d.get("schema_version", "1.0"),
        )


# -----------------------------
# Arbitration DTOs
# -----------------------------
# Result types for analysis arbitration between functional and modal approaches.


@dataclass
class ArbitrationResult:
    """Result of arbitration analysis between functional and modal approaches"""

    primary: AnalysisSummary
    alternatives: List[AnalysisSummary]
    confidence_gap: float
    progression_type: ProgressionType
    rationale: str
    warnings: List[str] = field(default_factory=list)
