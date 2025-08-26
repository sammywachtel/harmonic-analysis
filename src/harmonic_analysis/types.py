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
    LEADING_TONE = "leading_tone"
    CHROMATIC = "chromatic"


class ChromaticType(Enum):
    """Types of chromatic harmonic elements."""

    SECONDARY_DOMINANT = "secondary_dominant"
    BORROWED_CHORD = "borrowed_chord"
    CHROMATIC_MEDIANT = "chromatic_mediant"
    AUGMENTED_SIXTH = "augmented_sixth"
    NEAPOLITAN = "neapolitan"


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
