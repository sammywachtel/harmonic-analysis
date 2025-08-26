"""
Comprehensive music theory constants and mappings.

This module provides centralized access to fundamental music theory data
that can be used throughout the library and by external applications.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

# =============================================================================
# INTERVAL MAPPINGS
# =============================================================================

SEMITONE_TO_INTERVAL_NAME: Dict[int, str] = {
    0: "Unison",
    1: "Minor 2nd",
    2: "Major 2nd",
    3: "Minor 3rd",
    4: "Major 3rd",
    5: "Perfect 4th",
    6: "Tritone",
    7: "Perfect 5th",
    8: "Minor 6th",
    9: "Major 6th",
    10: "Minor 7th",
    11: "Major 7th",
    12: "Octave",
}

INTERVAL_ABBREVIATIONS: Dict[int, str] = {
    0: "P1",
    1: "m2",
    2: "M2",
    3: "m3",
    4: "M3",
    5: "P4",
    6: "TT",
    7: "P5",
    8: "m6",
    9: "M6",
    10: "m7",
    11: "M7",
    12: "P8",
}

# =============================================================================
# STEP PATTERNS
# =============================================================================

SEMITONE_TO_STEP_NAME: Dict[int, str] = {
    1: "H",  # Half step
    2: "W",  # Whole step
    3: "W+H",  # Augmented step
    4: "2W",  # Double whole step
}


def describe_step_pattern(intervals: List[int]) -> str:
    """Convert list of semitone intervals to step pattern description."""
    if not intervals or len(intervals) < 2:
        return "Insufficient intervals"

    steps = [(intervals[i + 1] - intervals[i]) % 12 for i in range(len(intervals) - 1)]
    step_names = []

    for step in steps:
        if step in SEMITONE_TO_STEP_NAME:
            step_names.append(SEMITONE_TO_STEP_NAME[step])
        else:
            step_names.append(f"{step}hs")

    return "-".join(step_names)


# =============================================================================
# SCALE DEGREE NOTATION
# =============================================================================


class ScaleDegree(Enum):
    """Scale degree with proper notation."""

    ROOT = "1"
    FLAT_TWO = "♭2"
    TWO = "2"
    FLAT_THREE = "♭3"
    THREE = "3"
    FOUR = "4"
    FLAT_FIVE = "♭5"
    FIVE = "5"
    FLAT_SIX = "♭6"
    SIX = "6"
    FLAT_SEVEN = "♭7"
    SEVEN = "7"


# =============================================================================
# MODAL CHARACTERISTICS
# =============================================================================


@dataclass
class ModalCharacteristics:
    """Characteristics that define a modal scale."""

    name: str
    characteristic_degrees: List[str]
    harmonic_implications: List[str]
    typical_applications: List[str]
    brightness: str  # "bright", "dark", "neutral"


MODAL_CHARACTERISTICS: Dict[str, ModalCharacteristics] = {
    "Ionian": ModalCharacteristics(
        name="Ionian (Major)",
        characteristic_degrees=["1", "3", "5", "7"],
        harmonic_implications=[
            "Strong tonal center with leading tone",
            "Classic major harmony foundation",
            "Supports functional harmony progressions",
        ],
        typical_applications=[
            "Pop and folk melodies",
            "Classical tonal music",
            "Functional harmony contexts",
        ],
        brightness="bright",
    ),
    "Dorian": ModalCharacteristics(
        name="Dorian",
        characteristic_degrees=["1", "♭3", "6", "♭7"],
        harmonic_implications=[
            "Natural 6th creates brighter minor sound",
            "Modal quality without leading tone",
            "Works well over minor 7th chords",
        ],
        typical_applications=[
            "Jazz and folk music",
            "Celtic and medieval music",
            "Rock ballads and progressions",
        ],
        brightness="neutral",
    ),
    "Phrygian": ModalCharacteristics(
        name="Phrygian",
        characteristic_degrees=["1", "♭2", "♭3", "♭6"],
        harmonic_implications=[
            "Flat 2nd creates exotic, Spanish flavor",
            "Dark minor character",
            "Prominent half-step relationships",
        ],
        typical_applications=[
            "Flamenco and Spanish music",
            "Heavy metal and progressive rock",
            "Middle Eastern influenced music",
        ],
        brightness="dark",
    ),
    "Lydian": ModalCharacteristics(
        name="Lydian",
        characteristic_degrees=["1", "3", "#4", "7"],
        harmonic_implications=[
            "Raised 4th creates bright, dreamy quality",
            "Avoids perfect 4th tritone resolution",
            "Floating, ethereal harmonic character",
        ],
        typical_applications=[
            "Film scores and ambient music",
            "Progressive rock and jazz fusion",
            "New age and cinematic music",
        ],
        brightness="bright",
    ),
    "Mixolydian": ModalCharacteristics(
        name="Mixolydian",
        characteristic_degrees=["1", "3", "5", "♭7"],
        harmonic_implications=[
            "Dominant character with flat 7th",
            "Bluesy and rock applications",
            "Perfect over dominant 7th chords",
        ],
        typical_applications=[
            "Blues and rock music",
            "Celtic traditional music",
            "Jazz improvisation over dom7 chords",
        ],
        brightness="bright",
    ),
    "Aeolian": ModalCharacteristics(
        name="Aeolian (Natural Minor)",
        characteristic_degrees=["1", "♭3", "♭6", "♭7"],
        harmonic_implications=[
            "Classic minor scale character",
            "Flat 6th distinguishes from Dorian",
            "Foundation for minor key harmony",
        ],
        typical_applications=[
            "Classical minor key music",
            "Pop and rock ballads",
            "Traditional folk melodies",
        ],
        brightness="dark",
    ),
    "Locrian": ModalCharacteristics(
        name="Locrian",
        characteristic_degrees=["1", "♭2", "♭3", "♭5"],
        harmonic_implications=[
            "Flat 5th creates instability",
            "Most dissonant of the modes",
            "Rare as tonal center",
        ],
        typical_applications=[
            "Theoretical study",
            "Avant-garde and experimental music",
            "Brief modal inflections",
        ],
        brightness="dark",
    ),
    "Phrygian Dominant": ModalCharacteristics(
        name="Phrygian Dominant",
        characteristic_degrees=["1", "♭2", "3", "♭6"],
        harmonic_implications=[
            "Strong dominant character with exotic flavor",
            "Augmented 2nd creates harmonic tension",
            "Combines major and Phrygian elements",
        ],
        typical_applications=[
            "Middle Eastern and flamenco music",
            "Heavy metal and progressive genres",
            "Dominant function in harmonic minor contexts",
        ],
        brightness="neutral",
    ),
}


# =============================================================================
# MELODIC MOTION ANALYSIS
# =============================================================================


class MotionType(Enum):
    """Types of melodic motion."""

    STEPWISE = "stepwise"
    LEAPING = "leaping"
    MIXED = "mixed"


def analyze_melodic_motion(intervals: List[int]) -> Tuple[MotionType, str]:
    """Analyze melodic motion patterns from interval list."""
    if not intervals:
        return MotionType.MIXED, "no motion"

    stepwise = sum(1 for i in intervals if abs(i) <= 2)
    leaping = len(intervals) - stepwise

    if stepwise > leaping * 2:
        return MotionType.STEPWISE, "predominantly stepwise motion"
    elif leaping > stepwise:
        return MotionType.LEAPING, "predominantly leaping motion"
    else:
        return MotionType.MIXED, "mixed stepwise and leaping motion"


# =============================================================================
# PHRASE CLASSIFICATION
# =============================================================================


class PhraseType(Enum):
    """Classification of phrase lengths."""

    MOTIF = "motif"
    SHORT_PHRASE = "short_phrase"
    STANDARD_PHRASE = "standard_phrase"
    EXTENDED_PHRASE = "extended_phrase"


def classify_phrase_length(note_count: int) -> PhraseType:
    """Classify phrase type based on note count."""
    if note_count <= 4:
        return PhraseType.MOTIF
    elif note_count <= 8:
        return PhraseType.SHORT_PHRASE
    elif note_count <= 16:
        return PhraseType.STANDARD_PHRASE
    else:
        return PhraseType.EXTENDED_PHRASE


# =============================================================================
# CHORD AND SCALE RELATIONSHIPS
# =============================================================================

SCALE_TO_CHORD_MAPPINGS: Dict[str, List[str]] = {
    "Ionian": ["maj7", "maj9", "maj6"],
    "Dorian": ["m7", "m9", "m6"],
    "Phrygian": ["m7", "m9", "sus♭9"],
    "Lydian": ["maj7#11", "maj9#11"],
    "Mixolydian": ["dom7", "dom9", "dom13"],
    "Aeolian": ["m7", "m9"],
    "Locrian": ["m7♭5", "ø7"],
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_interval_name(semitones: int, use_abbreviation: bool = False) -> str:
    """Get interval name from semitone count."""
    # Handle negative intervals and octave extensions
    abs_semitones = abs(semitones)
    octaves = abs_semitones // 12
    interval_within_octave = abs_semitones % 12

    mapping = INTERVAL_ABBREVIATIONS if use_abbreviation else SEMITONE_TO_INTERVAL_NAME
    base_name = mapping.get(
        interval_within_octave, f"{interval_within_octave} semitones"
    )

    if octaves > 0:
        base_name = f"{base_name} + {octaves} octave{'s' if octaves > 1 else ''}"

    return base_name


def get_modal_characteristics(scale_name: str) -> Optional[ModalCharacteristics]:
    """Get characteristics for a modal scale."""
    # Try exact match first
    if scale_name in MODAL_CHARACTERISTICS:
        return MODAL_CHARACTERISTICS[scale_name]

    # Try partial matches
    for modal_name, characteristics in MODAL_CHARACTERISTICS.items():
        if modal_name.lower() in scale_name.lower():
            return characteristics

    return None


def get_characteristic_degrees(scale_name: str) -> List[str]:
    """Get characteristic scale degrees for a mode."""
    characteristics = get_modal_characteristics(scale_name)
    return characteristics.characteristic_degrees if characteristics else []


def get_harmonic_implications(scale_name: str) -> List[str]:
    """Get harmonic implications for a scale."""
    characteristics = get_modal_characteristics(scale_name)
    return (
        characteristics.harmonic_implications
        if characteristics
        else [
            "Modal harmonic character",
            "Distinctive intervallic relationships",
            "Specific harmonic context applications",
        ]
    )


def get_scale_applications(scale_name: str) -> List[str]:
    """Get typical musical applications for a scale."""
    characteristics = get_modal_characteristics(scale_name)
    return (
        characteristics.typical_applications
        if characteristics
        else ["Various musical contexts", "Modal and tonal applications"]
    )


# =============================================================================
# ALL SCALES AND MODES REFERENCE
# =============================================================================

ALL_MODES: List[str] = list(MODAL_CHARACTERISTICS.keys())

ALL_MAJOR_KEYS: List[str] = [
    "C major",
    "G major",
    "D major",
    "A major",
    "E major",
    "B major",
    "F# major",
    "Db major",
    "Ab major",
    "Eb major",
    "Bb major",
    "F major",
]

ALL_MINOR_KEYS: List[str] = [
    "A minor",
    "E minor",
    "B minor",
    "F# minor",
    "C# minor",
    "G# minor",
    "D# minor",
    "Bb minor",
    "F minor",
    "C minor",
    "G minor",
    "D minor",
]

ALL_KEYS: List[str] = ALL_MAJOR_KEYS + ALL_MINOR_KEYS
