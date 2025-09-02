"""MIDI Integration and Chord Parsing Module.

MIDI integration and comprehensive chord parsing functionality including
chord symbol parsing, MIDI note detection, and chord progression parsing.

This module provides MIDI and parsing capabilities for users who need
to integrate with DAWs, MIDI controllers, or parse complex chord symbols.
"""

# Additional utilities that might be useful
from ..utils.chord_logic import (
    determine_chord_function,
    find_chord_matches,
)

# Re-export all MIDI and chord parsing functionality
# MIDI functions; Chord parsing; Classes; Data structures; Constants
from ..utils.chord_parser import (
    NOTE_NAMES,
    NOTE_NAMES_FLAT,
    NOTE_NAMES_SHARP,
    NOTE_TO_PITCH_CLASS,
    ChordMatch,
    ChordParser,
    ChordTemplate,
    find_chords_from_midi,
    parse_chord,
    parse_chord_progression,
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
