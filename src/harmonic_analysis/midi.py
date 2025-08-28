"""MIDI Integration and Chord Parsing Module.

MIDI integration and comprehensive chord parsing functionality including
chord symbol parsing, MIDI note detection, and chord progression parsing.

This module provides MIDI and parsing capabilities for users who need
to integrate with DAWs, MIDI controllers, or parse complex chord symbols.
"""

# Re-export all MIDI and chord parsing functionality
from .utils.chord_parser import (
    # MIDI functions
    find_chords_from_midi,

    # Chord parsing
    parse_chord,
    parse_chord_progression,

    # Classes
    ChordParser,
    ChordMatch,

    # Data structures
    ChordTemplate,

    # Constants
    NOTE_TO_PITCH_CLASS,
    NOTE_NAMES,
    NOTE_NAMES_SHARP,
    NOTE_NAMES_FLAT,
)

# Additional utilities that might be useful
from .utils.chord_logic import (
    find_chord_matches,
    determine_chord_function,
)

__all__ = [
    # MIDI functions
    "find_chords_from_midi",

    # Chord parsing
    "parse_chord",
    "parse_chord_progression",

    # Classes
    "ChordParser",
    "ChordMatch",

    # Data structures
    "ChordTemplate",

    # Chord logic utilities
    "find_chord_matches",
    "determine_chord_function",

    # Constants
    "NOTE_TO_PITCH_CLASS",
    "NOTE_NAMES",
    "NOTE_NAMES_SHARP",
    "NOTE_NAMES_FLAT",
]
