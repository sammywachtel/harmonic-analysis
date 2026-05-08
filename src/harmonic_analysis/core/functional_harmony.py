"""
Functional-harmony dataclasses and Roman-numeral / chord-function tables.

Once upon a time this module hosted ``FunctionalHarmonyAnalyzer`` — a
parallel implementation of the same key-detection heuristic that
``services/unified_pattern_service.py`` runs in production. The duplicate
is gone; the production path is the only path. What survives here is the
shared shape: dataclasses (FunctionalChordAnalysis, Cadence,
ChromaticElement, FunctionalAnalysisResult) plus the Roman-numeral and
chord-function lookup tables that other modules still consume as type
hints and reference data.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..analysis_types import ChordFunction, ChromaticType, ProgressionType

# Enhanced Roman numeral templates with chromatic chord support
FUNCTIONAL_ROMAN_NUMERALS = {
    "major": {
        "diatonic": ["I", "ii", "iii", "IV", "V", "vi", "vii°"],
        "chromatic": {
            # Secondary dominants (used as fallback for non-dominant quality
            # chords at these intervals)
            2: "V/V",  # D7 - Dominant of V (very common)
            4: "V/vi",  # E7 - Dominant of vi
            9: "V/ii",  # A7 - Dominant of ii
            11: "V/iii",  # B7 - Dominant of iii
        },
    },
    "minor": {
        # In minor, the natural subtonic is conventionally notated as ♭VII
        # (major triad on lowered 7̂)
        "diatonic": ["i", "ii°", "III", "iv", "v", "VI", "bVII"],
        "chromatic": {
            # Secondary dominants
            2: "V/III",  # Dominant of III
            5: "V/iv",  # Dominant of iv
            7: "V/v",  # Dominant of v
            9: "V/VI",  # Dominant of VI
            11: "V/VII",  # Dominant of VII
            # Common chromatic chords in minor keys
            4: "#iv°",  # Raised 4th diminished
        },
    },
}

# Chord function mapping based on Roman numeral degree
CHORD_FUNCTIONS: Dict[int, Dict[str, ChordFunction]] = {
    # Major key functions
    0: {"major": ChordFunction.TONIC, "minor": ChordFunction.TONIC},  # I/i
    1: {
        "major": ChordFunction.CHROMATIC,
        "minor": ChordFunction.CHROMATIC,
    },  # Chromatic
    2: {
        "major": ChordFunction.PREDOMINANT,
        "minor": ChordFunction.PREDOMINANT,
    },  # ii/ii°
    4: {
        "major": ChordFunction.MEDIANT,
        "minor": ChordFunction.MEDIANT,
    },  # iii/III - mediant in major and minor
    5: {
        "major": ChordFunction.SUBDOMINANT,
        "minor": ChordFunction.SUBDOMINANT,
    },  # IV/iv
    6: {"major": ChordFunction.CHROMATIC, "minor": ChordFunction.CHROMATIC},  # Tritone
    7: {"major": ChordFunction.DOMINANT, "minor": ChordFunction.DOMINANT},  # V/v
    8: {
        "major": ChordFunction.CHROMATIC,
        "minor": ChordFunction.CHROMATIC,
    },  # Chromatic
    9: {
        "major": ChordFunction.SUBMEDIANT,
        "minor": ChordFunction.SUBDOMINANT,
    },  # vi/VI - submediant in major, subdominant in minor
    10: {
        "major": ChordFunction.CHROMATIC,
        "minor": ChordFunction.SUBDOMINANT,
    },  # bVII - modal in major, natural in minor
    11: {
        "major": ChordFunction.LEADING_TONE,
        "minor": ChordFunction.LEADING_TONE,
    },  # vii°/VII
}


@dataclass
class FunctionalChordAnalysis:
    """Analysis result for a single chord in functional harmony context."""

    chord_symbol: str
    root: int
    chord_name: str
    roman_numeral: str
    figured_bass: str
    inversion: int
    function: ChordFunction
    is_chromatic: bool
    chromatic_type: Optional[ChromaticType] = None
    bass_note: Optional[int] = None


@dataclass
class Cadence:
    """Cadence analysis result."""

    type: str  # 'authentic', 'plagal', 'deceptive', 'half'
    chords: List[FunctionalChordAnalysis]
    strength: float
    position: str  # 'phrase_ending' or 'mid_phrase'


@dataclass
class ChromaticElement:
    """Chromatic harmony element."""

    chord: FunctionalChordAnalysis
    type: ChromaticType
    resolution: Optional[FunctionalChordAnalysis]
    explanation: str


@dataclass
class FunctionalAnalysisResult:
    """Complete functional harmony analysis result."""

    key_center: str
    key_signature: str
    mode: str  # 'major', 'minor', 'modal'
    chords: List[FunctionalChordAnalysis]
    cadences: List[Cadence]
    progression_type: ProgressionType
    confidence: float
    explanation: str
    chromatic_elements: List[ChromaticElement]
    ambiguity_factors: Optional[List[str]] = None
    key_source: str = "detected"  # 'user' | 'detected'
    key_locked: bool = False
