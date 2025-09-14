"""
Musical Data API - Comprehensive musical language data access for frontend/backend
                   integration.

This module provides a unified API for accessing all musical theory data including
scales, modes, notes, intervals, and relationships. It serves as the single source
of truth for musical vocabulary across all application layers.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..analysis_types import MelodyEvent, MelodyTrack
from ..core.utils.scales import (
    ALL_SCALE_SYSTEMS,
    BLUES_SCALE_MODES,
    DOUBLE_HARMONIC_MAJOR_MODES,
    HARMONIC_MAJOR_MODES,
    HARMONIC_MINOR_MODES,
    MAJOR_PENTATONIC_MODES,
    MAJOR_SCALE_MODES,
    MELODIC_MINOR_MODES,
    NOTE_TO_PITCH_CLASS,
)


@dataclass
class ScaleSystemInfo:
    """Complete information about a scale system."""

    name: str
    modes: Dict[str, List[int]]
    parent_intervals: List[int]
    is_diatonic: bool
    description: str


@dataclass
class MusicalNote:
    """Complete information about a musical note."""

    name: str
    pitch_class: int
    enharmonic_equivalents: List[str]
    frequency_a440: Optional[float] = None


# ============================================================================
# CORE MUSICAL DATA
# ============================================================================


def get_all_notes() -> List[str]:
    """Get all standard note names with enharmonic equivalents."""
    return [
        "C",
        "C♯/D♭",
        "D",
        "D♯/E♭",
        "E",
        "F",
        "F♯/G♭",
        "G",
        "G♯/A♭",
        "A",
        "A♯/B♭",
        "B",
    ]


def get_note_to_pitch_class_mapping() -> Dict[str, int]:
    """Get comprehensive note to pitch class mapping with all variants."""
    return NOTE_TO_PITCH_CLASS.copy()


def get_pitch_class_to_note_mapping() -> Dict[int, Dict[str, str]]:
    """Get pitch class to note name mapping with enharmonic options."""
    return {
        0: {"normal": "C", "sharp": "B♯", "flat": "D♭♭"},
        1: {"normal": "C♯", "flat": "D♭"},
        2: {"normal": "D", "sharp": "C♯♯", "flat": "E♭♭"},
        3: {"normal": "E♭", "sharp": "D♯"},
        4: {"normal": "E", "flat": "F♭", "sharp": "D♯♯"},
        5: {"normal": "F", "sharp": "E♯", "flat": "G♭♭"},
        6: {"normal": "F♯", "flat": "G♭"},
        7: {"normal": "G", "sharp": "F♯♯", "flat": "A♭♭"},
        8: {"normal": "A♭", "sharp": "G♯"},
        9: {"normal": "A", "sharp": "G♯♯", "flat": "B♭♭"},
        10: {"normal": "B♭", "sharp": "A♯"},
        11: {"normal": "B", "flat": "C♭", "sharp": "A♯♯"},
    }


def get_parent_key_indices() -> List[int]:
    """Get parent key indices for scale table organization."""
    return [0, 7, 2, 9, 4, 11, 5, 10, 3, 8, 1, 6]


def get_parent_key_mapping() -> Dict[int, str]:
    """Get parent key pitch class to note name mapping."""
    return {
        0: "C",
        1: "D♭",
        2: "D",
        3: "E♭",
        4: "E",
        5: "F",
        6: "G♭",
        7: "G",
        8: "A♭",
        9: "A",
        10: "B♭",
        11: "B",
    }


# ============================================================================
# SCALE SYSTEM DATA
# ============================================================================


def get_all_scale_systems() -> Dict[str, Dict[str, List[int]]]:
    """Get all scale systems with their modes and intervals."""
    return ALL_SCALE_SYSTEMS.copy()


def get_scale_system_info(scale_name: str) -> Optional[ScaleSystemInfo]:
    """Get comprehensive information about a specific scale system."""
    scale_systems = {
        "Major": ScaleSystemInfo(
            name="Major Scale",
            modes=MAJOR_SCALE_MODES,
            parent_intervals=[0, 2, 4, 5, 7, 9, 11],
            is_diatonic=True,
            description="The fundamental major scale system with seven diatonic modes",
        ),
        "Melodic Minor": ScaleSystemInfo(
            name="Melodic Minor",
            modes=MELODIC_MINOR_MODES,
            parent_intervals=[0, 2, 3, 5, 7, 9, 11],
            is_diatonic=True,
            description="Jazz minor scale system with raised 6th and 7th degrees",
        ),
        "Harmonic Minor": ScaleSystemInfo(
            name="Harmonic Minor",
            modes=HARMONIC_MINOR_MODES,
            parent_intervals=[0, 2, 3, 5, 7, 8, 11],
            is_diatonic=True,
            description="Minor scale with raised 7th degree creating augmented "
            "2nd interval",
        ),
        "Harmonic Major": ScaleSystemInfo(
            name="Harmonic Major",
            modes=HARMONIC_MAJOR_MODES,
            parent_intervals=[0, 2, 4, 5, 7, 8, 11],
            is_diatonic=True,
            description="Major scale with lowered 6th degree creating augmented "
            "2nd interval",
        ),
        "Double Harmonic Major": ScaleSystemInfo(
            name="Double Harmonic Major",
            modes=DOUBLE_HARMONIC_MAJOR_MODES,
            parent_intervals=[0, 1, 4, 5, 7, 8, 11],
            is_diatonic=True,
            description="Byzantine scale with two augmented 2nd intervals",
        ),
        "Major Pentatonic": ScaleSystemInfo(
            name="Major Pentatonic",
            modes=MAJOR_PENTATONIC_MODES,
            parent_intervals=[0, 2, 4, 7, 9],
            is_diatonic=False,
            description="Five-note scale system common in folk and world music",
        ),
        "Blues Scale": ScaleSystemInfo(
            name="Blues Scale",
            modes=BLUES_SCALE_MODES,
            parent_intervals=[0, 3, 5, 6, 7, 10],
            is_diatonic=False,
            description="Six-note scale fundamental to blues and rock music",
        ),
    }
    return scale_systems.get(scale_name)


def get_scale_system_names() -> List[str]:
    """Get all available scale system names."""
    return list(ALL_SCALE_SYSTEMS.keys())


def get_modes_for_scale_system(scale_name: str) -> Optional[Dict[str, List[int]]]:
    """Get all modes for a specific scale system."""
    return ALL_SCALE_SYSTEMS.get(scale_name)


# ============================================================================
# MODE RELATIONSHIPS AND MAPPINGS
# ============================================================================


def get_mode_to_scale_family_mapping() -> Dict[str, str]:
    """Get mapping from mode names to their scale families."""
    mapping = {}

    # Build mapping from all scale systems
    for scale_family, modes in ALL_SCALE_SYSTEMS.items():
        for mode_name in modes.keys():
            mapping[mode_name] = scale_family

    # Add common aliases
    mapping.update(
        {
            "Natural Minor": "Major",
            "Minor": "Major",
            "Jazz Minor": "Melodic Minor",
            "Byzantine": "Double Harmonic Major",
        }
    )

    return mapping


def get_mode_popularity_ranking() -> Dict[str, int]:
    """Get mode popularity rankings (lower number = more popular)."""
    return {
        # Major Scale modes (most common)
        "Ionian": 1,
        "Aeolian": 2,
        "Mixolydian": 3,
        "Dorian": 4,
        "Lydian": 5,
        "Phrygian": 6,
        "Locrian": 7,
        # Common aliases
        "Natural Minor": 2,
        "Minor": 2,
        # Other scale families (higher numbers = less common)
        "Harmonic Minor": 8,
        "Melodic Minor": 9,
        "Jazz Minor": 9,
        "Harmonic Major": 10,
        "Double Harmonic Major": 11,
        "Byzantine": 11,
        "Major Pentatonic": 12,
        "Minor Pentatonic": 13,
        "Blues Scale": 14,
        # Modified modes (even less common)
        "Dorian b2": 15,
        "Lydian Augmented": 16,
        "Lydian Dominant": 17,
        "Mixolydian b6": 18,
        "Locrian Natural 2": 19,
        "Altered": 20,
        "Locrian Natural 6": 21,
        "Ionian Augmented": 22,
        "Ukrainian Dorian": 23,
        "Phrygian Dominant": 24,
        "Lydian Sharp 2": 25,
        "Super Locrian": 26,
        "Dorian b5": 27,
        "Phrygian b4": 28,
        "Lydian b3": 29,
        "Mixolydian b2": 30,
        "Lydian Augmented #2": 31,
        "Locrian bb7": 32,
    }


def get_mode_index_in_scale_family(scale_family: str, mode_name: str) -> Optional[int]:
    """Get the index of a mode within its scale family."""
    modes = ALL_SCALE_SYSTEMS.get(scale_family)
    if not modes:
        return None

    mode_names = list(modes.keys())
    try:
        return mode_names.index(mode_name)
    except ValueError:
        return None


def get_degree_to_mode_mapping(
    scale_system: str,
) -> Optional[Dict[int, Dict[str, Any]]]:
    """Get degree-to-mode mapping for a scale system using parent scale intervals."""
    info = get_scale_system_info(scale_system)
    if not info:
        return None

    modes = ALL_SCALE_SYSTEMS.get(scale_system)
    if not modes:
        return None

    # Build mapping from semitone degree to mode info
    degree_to_mode = {}
    mode_names = list(modes.keys())

    for degree_semitones in info.parent_intervals:
        # Find which mode index this degree corresponds to
        mode_index = info.parent_intervals.index(degree_semitones)
        if mode_index < len(mode_names):
            degree_to_mode[degree_semitones] = {
                "name": mode_names[mode_index],
                "index": mode_index,
            }

    return degree_to_mode


def get_all_degree_to_mode_mappings() -> Dict[str, Dict[int, Dict[str, Any]]]:
    """Get degree-to-mode mappings for all scale systems."""
    mappings = {}
    for scale_name in get_scale_system_names():
        mapping = get_degree_to_mode_mapping(scale_name)
        if mapping:
            mappings[scale_name] = mapping
    return mappings


# ============================================================================
# INTERVAL AND RELATIONSHIP DATA
# ============================================================================


def get_interval_names() -> Dict[int, str]:
    """Get interval names for semitone distances."""
    return {
        0: "Unison (P1)",
        1: "Minor 2nd (m2)",
        2: "Major 2nd (M2)",
        3: "Minor 3rd (m3)",
        4: "Major 3rd (M3)",
        5: "Perfect 4th (P4)",
        6: "Tritone (TT)",
        7: "Perfect 5th (P5)",
        8: "Minor 6th (m6)",
        9: "Major 6th (M6)",
        10: "Minor 7th (m7)",
        11: "Major 7th (M7)",
    }


def get_circle_of_fifths() -> List[str]:
    """Get the circle of fifths progression."""
    return ["C", "G", "D", "A", "E", "B", "F♯/G♭", "D♭", "A♭", "E♭", "B♭", "F"]


def get_relative_major_minor_pairs() -> List[Tuple[str, str]]:
    """Get all relative major/minor key pairs."""
    return [
        ("C major", "A minor"),
        ("G major", "E minor"),
        ("D major", "B minor"),
        ("A major", "F♯ minor"),
        ("E major", "C♯ minor"),
        ("B major", "G♯ minor"),
        ("F♯ major", "D♯ minor"),
        ("D♭ major", "B♭ minor"),
        ("A♭ major", "F minor"),
        ("E♭ major", "C minor"),
        ("B♭ major", "G minor"),
        ("F major", "D minor"),
    ]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def normalize_note_name(note: str) -> str:
    """Normalize note name to standard format."""
    # Handle uppercase versions first
    note_upper = note.upper()

    # Convert ASCII flats and sharps to unicode, being careful with 'B' note
    note_unicode = note_upper.replace("#", "♯")
    # Only replace 'b' with '♭' when it's clearly a flat (lowercase or after a note)
    if "b" in note.lower() and len(note) > 1:
        note_unicode = note_upper.replace("B", "♭")

    # Try different variants in order of preference
    variants_to_try = [
        note_upper,  # ASCII uppercase (most common)
        note_unicode,  # Unicode version
        note,  # Original
        note.capitalize(),
    ]

    for variant in variants_to_try:
        if variant in NOTE_TO_PITCH_CLASS:
            return variant

    return note  # Return original if no match


def note_to_pitch_class(note: str) -> Optional[int]:
    """Convert note name to pitch class."""
    normalized = normalize_note_name(note)
    return NOTE_TO_PITCH_CLASS.get(normalized)


def pitch_class_to_note(pitch_class: int, prefer_sharp: bool = True) -> str:
    """Convert pitch class to note name."""
    mapping = get_pitch_class_to_note_mapping()
    note_info = mapping.get(pitch_class % 12, {"normal": "C"})

    if prefer_sharp and "sharp" in note_info:
        return note_info["sharp"]
    elif not prefer_sharp and "flat" in note_info:
        return note_info["flat"]
    else:
        return note_info["normal"]


def get_scale_notes(root: str, scale_intervals: List[int]) -> List[str]:
    """Generate scale notes from root and interval pattern."""
    root_pc = note_to_pitch_class(root)
    if root_pc is None:
        return []

    notes = []
    for interval in scale_intervals:
        pc = (root_pc + interval) % 12
        notes.append(pitch_class_to_note(pc))

    return notes


def validate_musical_input(input_data: Any) -> Dict[str, Any]:
    """Validate musical input and provide feedback."""
    result: Dict[str, Any] = {"valid": True, "errors": [], "suggestions": []}

    if isinstance(input_data, str):
        # Validate single note
        if note_to_pitch_class(input_data) is None:
            result["valid"] = False
            result["errors"].append(f"Invalid note name: '{input_data}'")
            result["suggestions"].append(
                "Try: C, D, E, F, G, A, B with optional ♯ or ♭"
            )

    elif isinstance(input_data, list):
        # Validate list of notes
        for note in input_data:
            if isinstance(note, str) and note_to_pitch_class(note) is None:
                result["valid"] = False
                result["errors"].append(f"Invalid note name: '{note}'")

    return result


# ============================================================================
# EXPORT FUNCTIONS FOR BACKEND API
# ============================================================================


def get_complete_musical_reference() -> Dict[str, Any]:
    """Get all musical reference data for frontend consumption."""
    return {
        "notes": get_all_notes(),
        "note_to_pitch_class": get_note_to_pitch_class_mapping(),
        "pitch_class_to_note": get_pitch_class_to_note_mapping(),
        "parent_key_indices": get_parent_key_indices(),
        "parent_keys": get_parent_key_mapping(),
        "scale_systems": {
            name: {
                "modes": modes,
                "info": (
                    get_scale_system_info(name).__dict__
                    if get_scale_system_info(name)
                    else None
                ),
            }
            for name, modes in get_all_scale_systems().items()
        },
        "mode_to_scale_family": get_mode_to_scale_family_mapping(),
        "mode_popularity": get_mode_popularity_ranking(),
        "intervals": get_interval_names(),
        "circle_of_fifths": get_circle_of_fifths(),
        "relative_pairs": get_relative_major_minor_pairs(),
    }


def get_scale_reference_for_frontend() -> Dict[str, Any]:
    """Get scale reference data optimized for frontend scale tables."""
    scale_data = []

    for scale_name, modes in get_all_scale_systems().items():
        info = get_scale_system_info(scale_name)
        if not info:
            continue

        # Format mode data for frontend tables
        mode_names = list(modes.keys())
        mode_intervals = list(modes.values())

        scale_data.append(
            {
                "name": info.name,
                "tableId": scale_name.lower().replace(" ", "-") + "-modes",
                "isDiatonic": info.is_diatonic,
                "headers": ["Mode / Scale Degree"] + mode_names,
                "modes": mode_names,
                "modeIntervals": mode_intervals,
                "parentScaleIntervals": info.parent_intervals,
                "description": info.description,
            }
        )

    return {"scaleData": scale_data}


# =============================================================================
# STAGE C: Melody-Chord Alignment Utilities
# =============================================================================


def align_melody_to_chords(
    melody: MelodyTrack, chords: List[str], starts: List[float], ends: List[float]
) -> List[List[MelodyEvent]]:
    """Return per-chord list of melody events within each [start,end) window.

    Aligns melody events with chord boundaries for voice-leading analysis.

    Args:
        melody: MelodyTrack with .events (onset, duration, pitch)
        chords: List of chord symbols (for length reference)
        starts: Start times for each chord
        ends: End times for each chord

    Returns:
        List of melody event lists, one per chord

    Example:
        >>> melody = MelodyTrack([
        ...     MelodyEvent(onset=0.0, pitch=60, duration=1.0),
        ...     MelodyEvent(onset=1.0, pitch=64, duration=1.0)
        ... ])
        >>> chords = ["C", "F"]
        >>> starts = [0.0, 1.0]
        >>> ends = [1.0, 2.0]
        >>> aligned = align_melody_to_chords(melody, chords, starts, ends)
        >>> len(aligned[0])  # Events in first chord
        1
    """
    aligned: List[List[MelodyEvent]] = [[] for _ in chords]

    # Handle case where melody might be None or have no events
    if not melody or not hasattr(melody, "events") or not melody.events:
        return aligned

    for event in melody.events:
        if not hasattr(event, "onset") or not hasattr(event, "duration"):
            continue

        onset = event.onset
        end_time = onset + event.duration

        # Check overlap with each chord window
        for i, (start, end) in enumerate(zip(starts, ends)):
            # Simple overlap test: event overlaps if onset < chord_end
            # AND event_end > chord_start
            if (onset < end) and (end_time > start):
                aligned[i].append(event)

    return aligned


def soprano_degrees_per_chord(
    melody_aligned: List[List[MelodyEvent]], key_center: str
) -> List[Optional[int]]:
    """Map top (soprano) pitch per chord to scale degree 1..7 in the active key.

    Uses a crude top-note heuristic to identify the soprano voice.
    For more sophisticated analysis, this could be replaced with beat-strength
    weighting or quantization-aware selection.

    Args:
        melody_aligned: Per-chord melody events from align_melody_to_chords()
        key_center: Key center string (e.g., "C major")

    Returns:
        List parallel to chord list with scale degrees (1-7) or None

    Example:
        >>> aligned = [[MelodyEvent(onset=0, pitch=67, duration=1)]]  # G
        >>> degrees = soprano_degrees_per_chord(aligned, "C major")
        >>> degrees[0]
        5  # G is scale degree 5 in C major
    """
    # Parse key center
    try:
        parts = key_center.split()
        tonic_name = parts[0] if parts else "C"
        mode = parts[1] if len(parts) > 1 else "major"
    except (IndexError, AttributeError):
        tonic_name = "C"
        mode = "major"

    # Note name to pitch class mapping
    name_to_pc = {
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
    }
    tonic_pc = name_to_pc.get(tonic_name, 0)

    # Scale intervals in semitones from tonic
    if mode.lower().startswith("maj"):
        scale_semitones = [0, 2, 4, 5, 7, 9, 11]  # Major scale
    else:
        scale_semitones = [0, 2, 3, 5, 7, 8, 10]  # Minor scale

    degrees: List[Optional[int]] = []

    for chord_events in melody_aligned:
        if not chord_events:
            degrees.append(None)
            continue

        # Find the highest pitch sounding in this chord window
        try:
            pitches = [event.pitch for event in chord_events if hasattr(event, "pitch")]
            if not pitches:
                degrees.append(None)
                continue

            top_pitch = max(pitches)
            top_pc = top_pitch % 12

            # Find nearest scale degree by semitone distance to tonic
            relative_pc = (top_pc - tonic_pc) % 12

            # Look up scale degree
            if relative_pc in scale_semitones:
                degree = scale_semitones.index(relative_pc) + 1  # 1-indexed
            else:
                degree = None  # Non-diatonic note

            degrees.append(degree)

        except (ValueError, AttributeError, TypeError):
            degrees.append(None)

    return degrees


__all__ = [
    # Core data functions
    "get_all_notes",
    "get_note_to_pitch_class_mapping",
    "get_pitch_class_to_note_mapping",
    "get_parent_key_indices",
    "get_parent_key_mapping",
    # Scale system functions
    "get_all_scale_systems",
    "get_scale_system_info",
    "get_scale_system_names",
    "get_modes_for_scale_system",
    # Mode relationship functions
    "get_mode_to_scale_family_mapping",
    "get_mode_popularity_ranking",
    "get_mode_index_in_scale_family",
    "get_degree_to_mode_mapping",
    "get_all_degree_to_mode_mappings",
    # Interval and relationship functions
    "get_interval_names",
    "get_circle_of_fifths",
    "get_relative_major_minor_pairs",
    # Utility functions
    "normalize_note_name",
    "note_to_pitch_class",
    "pitch_class_to_note",
    "get_scale_notes",
    "validate_musical_input",
    # Export functions
    "get_complete_musical_reference",
    "get_scale_reference_for_frontend",
    # Stage C: Melody-chord alignment
    "align_melody_to_chords",
    "soprano_degrees_per_chord",
    # Data classes
    "ScaleSystemInfo",
    "MusicalNote",
]
