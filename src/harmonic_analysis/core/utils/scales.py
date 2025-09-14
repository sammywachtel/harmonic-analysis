"""
Scale data and constants for music theory analysis.
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ScaleData:
    """Data structure for scale information."""

    name: str
    intervals: List[int]
    mode_names: List[str]
    parent_scale_intervals: List[int]


# Pitch class mapping
NOTE_TO_PITCH_CLASS: Dict[str, int] = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
    # Extended enharmonic equivalents
    "B#": 0,
    "Cb": 11,
    "E#": 5,
    "Fb": 4,
}

# Reverse mapping for display
PITCH_CLASS_NAMES: List[str] = [
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B",
]

# Major scale modes with intervals
MAJOR_SCALE_MODES: Dict[str, List[int]] = {
    "Ionian": [0, 2, 4, 5, 7, 9, 11],
    "Dorian": [0, 2, 3, 5, 7, 9, 10],
    "Phrygian": [0, 1, 3, 5, 7, 8, 10],
    "Lydian": [0, 2, 4, 6, 7, 9, 11],
    "Mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "Aeolian": [0, 2, 3, 5, 7, 8, 10],
    "Locrian": [0, 1, 3, 5, 6, 8, 10],
}

# Modal parent key relationships
MODAL_PARENT_KEYS: Dict[str, Dict[str, Any]] = {
    "Ionian": {"offset": 0, "mode": "major"},
    "Dorian": {"offset": -2, "mode": "major"},
    "Phrygian": {"offset": -4, "mode": "major"},
    "Lydian": {"offset": 2, "mode": "major"},
    "Mixolydian": {"offset": -7, "mode": "major"},
    "Aeolian": {"offset": -9, "mode": "major"},
    "Locrian": {"offset": -11, "mode": "major"},
}

# Melodic minor modes
MELODIC_MINOR_MODES: Dict[str, List[int]] = {
    "Melodic Minor": [0, 2, 3, 5, 7, 9, 11],
    "Dorian b2": [0, 1, 3, 5, 7, 9, 10],
    "Lydian Augmented": [0, 2, 4, 6, 8, 9, 11],
    "Lydian Dominant": [0, 2, 4, 6, 7, 9, 10],
    "Mixolydian b6": [0, 2, 4, 5, 7, 8, 10],
    "Locrian Natural 2": [0, 2, 3, 5, 6, 8, 10],
    "Altered": [0, 1, 3, 4, 6, 8, 10],
}

# Harmonic minor modes
HARMONIC_MINOR_MODES: Dict[str, List[int]] = {
    "Harmonic Minor": [0, 2, 3, 5, 7, 8, 11],
    "Locrian Natural 6": [0, 1, 3, 5, 6, 9, 10],
    "Ionian Augmented": [0, 2, 4, 5, 8, 9, 11],
    "Ukrainian Dorian": [0, 2, 3, 6, 7, 9, 10],
    "Phrygian Dominant": [0, 1, 4, 5, 7, 8, 10],
    "Lydian Sharp 2": [0, 3, 4, 7, 8, 10, 11],
    "Super Locrian": [0, 1, 3, 4, 6, 7, 9],
}

# Harmonic major modes
HARMONIC_MAJOR_MODES: Dict[str, List[int]] = {
    "Harmonic Major": [0, 2, 4, 5, 7, 8, 11],
    "Dorian b5": [0, 2, 3, 5, 6, 9, 10],
    "Phrygian b4": [0, 1, 3, 4, 7, 8, 10],
    "Lydian b3": [0, 2, 3, 6, 7, 9, 11],
    "Mixolydian b2": [0, 1, 4, 5, 7, 9, 10],
    "Lydian Augmented #2": [0, 3, 4, 7, 9, 10, 11],
    "Locrian bb7": [0, 1, 3, 5, 6, 8, 9],
}

# Double harmonic major modes (Byzantine scale)
DOUBLE_HARMONIC_MAJOR_MODES: Dict[str, List[int]] = {
    "Double Harmonic Major": [0, 1, 4, 5, 7, 8, 11],  # Byzantine
    "Lydian #2 #6": [0, 3, 4, 6, 7, 10, 11],
    "Ultraphrygian": [0, 1, 3, 4, 7, 9, 10],
    "Hungarian Minor": [0, 2, 3, 6, 7, 8, 10],
    "Oriental": [0, 1, 4, 5, 6, 9, 10],
    "Ionian Augmented #2": [0, 3, 4, 5, 8, 9, 11],
    "Ultra Locrian": [0, 1, 2, 4, 5, 7, 8],
}

# Major pentatonic modes
MAJOR_PENTATONIC_MODES: Dict[str, List[int]] = {
    "Major Pentatonic": [0, 2, 4, 7, 9],
    "Suspended": [0, 2, 5, 7, 10],
    "Jue": [0, 3, 5, 8, 10],  # Man Gong
    "Zhi": [0, 2, 5, 7, 9],  # Shang
    "Minor Pentatonic": [0, 3, 5, 7, 10],  # Gong
}

# Blues scale modes
BLUES_SCALE_MODES: Dict[str, List[int]] = {
    "Blues Scale": [0, 3, 5, 6, 7, 10],
    "Blues Mode II": [0, 2, 3, 4, 7, 9],
    "Blues Mode III": [0, 1, 2, 5, 7, 10],
    "Blues Mode IV": [0, 1, 4, 6, 9, 11],
    "Blues Mode V": [0, 3, 5, 8, 10, 11],
    "Blues Mode VI": [0, 2, 3, 7, 8, 9],
}

# All scale systems combined
ALL_SCALE_SYSTEMS: Dict[str, Dict[str, List[int]]] = {
    "Major": MAJOR_SCALE_MODES,
    "Melodic Minor": MELODIC_MINOR_MODES,
    "Harmonic Minor": HARMONIC_MINOR_MODES,
    "Harmonic Major": HARMONIC_MAJOR_MODES,
    "Double Harmonic Major": DOUBLE_HARMONIC_MAJOR_MODES,
    "Major Pentatonic": MAJOR_PENTATONIC_MODES,
    "Blues Scale": BLUES_SCALE_MODES,
}


def get_parent_key(local_tonic: str, mode_name: str) -> str:
    """
    Calculate parent key signature for a given local tonic and mode.

    Args:
        local_tonic: The local tonic note (e.g., "G")
        mode_name: The mode name (e.g., "Mixolydian")

    Returns:
        Parent key signature (e.g., "C major")
    """
    if mode_name not in MODAL_PARENT_KEYS:
        raise ValueError(f"Unknown mode: {mode_name}")

    local_pitch = NOTE_TO_PITCH_CLASS.get(local_tonic)
    if local_pitch is None:
        raise ValueError(f"Invalid note: {local_tonic}")

    offset = MODAL_PARENT_KEYS[mode_name]["offset"]
    parent_pitch = (local_pitch + offset) % 12
    parent_note = PITCH_CLASS_NAMES[parent_pitch]

    mode_type = MODAL_PARENT_KEYS[mode_name]["mode"]
    return f"{parent_note} {mode_type}"


def generate_scale_notes(tonic: str, intervals: List[int]) -> List[str]:
    """
    Generate scale notes from tonic and interval pattern.

    Args:
        tonic: Starting note
        intervals: List of intervals in semitones

    Returns:
        List of note names in the scale
    """
    tonic_pitch = NOTE_TO_PITCH_CLASS.get(tonic)
    if tonic_pitch is None:
        raise ValueError(f"Invalid tonic: {tonic}")

    scale_notes = []
    for interval in intervals:
        pitch_class = (tonic_pitch + interval) % 12
        scale_notes.append(PITCH_CLASS_NAMES[pitch_class])

    return scale_notes


# Key signature definitions - moved from multiple locations to centralize
KEY_SIGNATURES: Dict[str, List[str]] = {
    # Major keys
    "C major": [],  # No sharps or flats
    "G major": ["F#"],
    "D major": ["F#", "C#"],
    "A major": ["F#", "C#", "G#"],
    "E major": ["F#", "C#", "G#", "D#"],
    "B major": ["F#", "C#", "G#", "D#", "A#"],
    "F# major": ["F#", "C#", "G#", "D#", "A#", "E#"],
    "C# major": ["F#", "C#", "G#", "D#", "A#", "E#", "B#"],
    "F major": ["Bb"],
    "Bb major": ["Bb", "Eb"],
    "Eb major": ["Bb", "Eb", "Ab"],
    "Ab major": ["Bb", "Eb", "Ab", "Db"],
    "Db major": ["Bb", "Eb", "Ab", "Db", "Gb"],
    "Gb major": ["Bb", "Eb", "Ab", "Db", "Gb", "Cb"],
    "Cb major": ["Bb", "Eb", "Ab", "Db", "Gb", "Cb", "Fb"],
    # Minor keys (relative to major keys)
    "A minor": [],  # Same as C major
    "E minor": ["F#"],  # Same as G major
    "B minor": ["F#", "C#"],  # Same as D major
    "F# minor": ["F#", "C#", "G#"],  # Same as A major
    "C# minor": ["F#", "C#", "G#", "D#"],  # Same as E major
    "G# minor": ["F#", "C#", "G#", "D#", "A#"],  # Same as B major
    "D# minor": ["F#", "C#", "G#", "D#", "A#", "E#"],  # Same as F# major
    "A# minor": ["F#", "C#", "G#", "D#", "A#", "E#", "B#"],  # Same as C# major
    "D minor": ["Bb"],  # Same as F major
    "G minor": ["Bb", "Eb"],  # Same as Bb major
    "C minor": ["Bb", "Eb", "Ab"],  # Same as Eb major
    "F minor": ["Bb", "Eb", "Ab", "Db"],  # Same as Ab major
    "Bb minor": ["Bb", "Eb", "Ab", "Db", "Gb"],  # Same as Db major
    "Eb minor": ["Bb", "Eb", "Ab", "Db", "Gb", "Cb"],  # Same as Gb major
    "Ab minor": ["Bb", "Eb", "Ab", "Db", "Gb", "Cb", "Fb"],  # Same as Cb major
}
