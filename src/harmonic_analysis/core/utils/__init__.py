"""
Core utilities for harmonic analysis.

This package contains fundamental utilities that are used across core modules.
These utilities provide essential music theory constants, scale data,
chord parsing, and other foundational functionality.
"""

from .analysis_params import calculate_initial_window
from .chord_detection import detect_chord_from_pitches
from .chord_inversions import analyze_chord_inversion
from .chord_logic import ChordMatch, ChordParser
from .key_signature import convert_key_signature_to_mode, parse_key_signature_from_hint

# Import commonly used constants and functions
from .music_theory_constants import (
    ALL_MAJOR_KEYS,
    ALL_MINOR_KEYS,
    ALL_MODES,
    INTERVAL_ABBREVIATIONS,
    MODAL_CHARACTERISTICS,
    SEMITONE_TO_INTERVAL_NAME,
)
from .scales import KEY_SIGNATURES, NOTE_TO_PITCH_CLASS, PITCH_CLASS_NAMES, ScaleData

__all__ = [
    # Music theory constants
    "SEMITONE_TO_INTERVAL_NAME",
    "INTERVAL_ABBREVIATIONS",
    "MODAL_CHARACTERISTICS",
    "ALL_MODES",
    "ALL_MAJOR_KEYS",
    "ALL_MINOR_KEYS",
    # Scale utilities
    "ScaleData",
    "NOTE_TO_PITCH_CLASS",
    "PITCH_CLASS_NAMES",
    "KEY_SIGNATURES",
    # Chord utilities
    "ChordMatch",
    "ChordParser",
    "analyze_chord_inversion",
    "detect_chord_from_pitches",
    # Key signature utilities
    "convert_key_signature_to_mode",
    "parse_key_signature_from_hint",
    # Analysis parameter utilities
    "calculate_initial_window",
]
