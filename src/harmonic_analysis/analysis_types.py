"""
Type definitions and data structures for music theory analysis.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Literal, Optional


class ChordFunction(Enum):
    """Harmonic function classification for chords."""

    TONIC = "tonic"
    PREDOMINANT = "predominant"
    DOMINANT = "dominant"
    SUBDOMINANT = "subdominant"
    MEDIANT = "mediant"
    SUBMEDIANT = "submediant"
    LEADING_TONE = "leading_tone"
    CHROMATIC = "chromatic"


class ChromaticType(Enum):
    """Types of chromatic harmonic elements."""

    SECONDARY_DOMINANT = "secondary_dominant"
    BORROWED_CHORD = "borrowed_chord"
    CHROMATIC_MEDIANT = "chromatic_mediant"
    AUGMENTED_SIXTH = "augmented_sixth"
    NEAPOLITAN = "neapolitan"


class EvidenceType(Enum):
    """Types of analytical evidence for harmonic interpretation."""

    HARMONIC = "harmonic"
    STRUCTURAL = "structural"
    CADENTIAL = "cadential"
    INTERVALLIC = "intervallic"
    CONTEXTUAL = "contextual"


class InterpretationType(Enum):
    """Types of harmonic interpretation."""

    FUNCTIONAL = "functional"
    MODAL = "modal"
    CHROMATIC = "chromatic"


class PedagogicalLevel(Enum):
    """Pedagogical levels for adaptive disclosure."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ProgressionType(Enum):
    """Types of chord progressions."""

    AUTHENTIC_CADENCE = "authentic_cadence"
    PLAGAL_CADENCE = "plagal_cadence"
    DECEPTIVE_CADENCE = "deceptive_cadence"
    HALF_CADENCE = "half_cadence"
    CIRCLE_OF_FIFTHS = "circle_of_fifths"
    MODAL_PROGRESSION = "modal_progression"
    CHROMATIC_SEQUENCE = "chromatic_sequence"
    BLUES_PROGRESSION = "blues_progression"
    JAZZ_STANDARD = "jazz_standard"
    OTHER = "other"


@dataclass
class UserInputContext:
    """Context information about user input."""

    chord_progression: str
    parent_key: Optional[str] = None
    analysis_type: str = "chord_progression"


@dataclass
class AnalysisOptions:
    """Options for configuring analysis behavior."""

    parent_key: Optional[str] = None
    pedagogical_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    confidence_threshold: float = 0.5
    max_alternatives: int = 3
    force_multiple_interpretations: bool = False
    analysis_type: str = "progression"
    include_borrowed: bool = True
    include_secondary: bool = True
    include_character: bool = True
    include_enhancements: bool = True


@dataclass
class Evidence:
    """Evidence supporting an analytical interpretation."""

    type: Literal["structural", "cadential", "intervallic", "contextual"]
    strength: float  # 0.0 to 1.0
    description: str
    supported_interpretations: List[str]
    musical_basis: str


@dataclass
class Interpretation:
    """A single analytical interpretation."""

    type: Literal["functional", "modal", "chromatic"]
    confidence: float
    analysis: str
    roman_numerals: List[str]
    key_signature: str
    evidence: List[Evidence]
    reasoning: str
    theoretical_basis: str
    mode: Optional[str] = None


@dataclass
class KeySuggestion:
    """Suggestion for parent key that could improve analysis."""

    suggested_key: str  # e.g., "C major"
    confidence: float  # How confident we are this would help (0.0-1.0)
    reason: str  # Why this key would be beneficial
    detected_pattern: str  # What pattern suggests this key (e.g., "ii-V-I progression")
    potential_improvement: str  # What would improve (e.g., "Roman numerals available")


@dataclass
class AnalysisSuggestions:
    """Suggestions for improving analysis quality."""

    parent_key_suggestions: List[KeySuggestion]
    general_suggestions: List[str]  # Other helpful suggestions

    # Enhanced bidirectional suggestions
    unnecessary_key_suggestions: Optional[List[KeySuggestion]] = (
        None  # Suggest removing keys
    )
    key_change_suggestions: Optional[List[KeySuggestion]] = (
        None  # Suggest different keys
    )


@dataclass
class MultipleInterpretationResult:
    """Result containing multiple analytical interpretations."""

    primary_analysis: Interpretation
    alternative_analyses: List[Interpretation]
    metadata: Dict[str, Any]
    input: Dict[str, Any]
    suggestions: Optional[AnalysisSuggestions] = None


# =============================================================================
# STAGE C: Voice-Leading and Melodic Analysis Data Structures
# =============================================================================


@dataclass
class KeyCandidate:
    """A candidate key with confidence and provenance information."""

    name: str  # e.g., "C major"
    confidence: float  # confidence score (0.0 to 1.0)
    source: str  # "user_hint", "prior:scale", or "estimated"


@dataclass
class ScalePrior:
    """Prior information about key candidates from scale analysis."""

    candidates: List[KeyCandidate]  # sorted by descending confidence


@dataclass
class MelodyEvent:
    """A single melodic event with timing and pitch information."""

    onset: float  # onset time in seconds or beats
    pitch: int  # MIDI pitch number
    duration: float  # duration in seconds or beats
    ppq: Optional[float] = None  # pulses per quarter note (optional)
    bar_offset: Optional[float] = None  # position within bar (optional)


@dataclass
class MelodyTrack:
    """A track containing a sequence of melodic events."""

    events: List[MelodyEvent]


@dataclass
class MelodicEvents:
    """Voice-leading events detected in melodic analysis.

    Can be extracted from explicit melody data or inferred from harmonic progressions.
    All lists are per-chord-index, parallel to the chord symbol list.
    """

    soprano_degree: List[Optional[int]]  # per-index soprano scale degrees (1-7) or None
    voice_4_to_3: List[bool]  # per-index 4→3 suspension flags
    voice_7_to_1: List[bool]  # per-index 7→1 resolution flags
    fi_to_sol: List[bool]  # per-index ♯4→5 melodic motion flags
    le_to_sol: List[bool]  # per-index ♭6→5 melodic motion flags
    source: str  # "melody" or "inference"


@dataclass
class ModalCharacteristic:
    """A detected modal characteristic with supporting evidence."""

    label: str  # e.g., "mixolydian_color (bVII)", "borrowed_iv_from_minor"
    evidence: List[str]  # short strings like "bVII present with I in major context"


@dataclass
class ModalAnalysisResult:
    """Result of modal analysis with characteristics and confidence."""

    characteristics: List[ModalCharacteristic]
    parent_key_relationship: Optional[str]  # "aligns" | "conflicts" | None
    confidence: float  # 0.0–1.0

    # Optional downstream UX fields
    inferred_mode: Optional[str] = None  # e.g., "Mixolydian", "Dorian"
    rationale: Optional[str] = None
