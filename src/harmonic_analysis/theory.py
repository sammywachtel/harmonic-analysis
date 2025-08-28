"""Music Theory Utilities Module.

Music theory constants, mappings, and analytical functions including interval
analysis, modal characteristics, phrase classification, and melodic motion analysis.

This module provides essential music theory building blocks that are used
throughout the library and can be useful for external applications.
"""

# Re-export all music theory constants and utilities
from .utils.music_theory_constants import (
    # Core mappings
    SEMITONE_TO_INTERVAL_NAME,
    INTERVAL_ABBREVIATIONS,
    SEMITONE_TO_STEP_NAME,

    # Scale degrees
    ScaleDegree,

    # Modal characteristics
    ModalCharacteristics,
    MODAL_CHARACTERISTICS,
    SCALE_TO_CHORD_MAPPINGS,

    # Motion analysis
    MotionType,
    analyze_melodic_motion,

    # Phrase classification
    PhraseType,
    classify_phrase_length,

    # Utility functions
    get_interval_name,
    get_modal_characteristics,
    get_characteristic_degrees,
    get_harmonic_implications,
    get_scale_applications,
    describe_step_pattern,

    # Reference collections
    ALL_MODES,
    ALL_MAJOR_KEYS,
    ALL_MINOR_KEYS,
    ALL_KEYS,
)

# Analysis helper functions
from .utils.analysis_helpers import (
    # Contour analysis
    describe_contour,

    # Intervallic analysis
    analyze_intervallic_content,
)

__all__ = [
    # Core mappings
    "SEMITONE_TO_INTERVAL_NAME",
    "INTERVAL_ABBREVIATIONS",
    "SEMITONE_TO_STEP_NAME",

    # Scale degrees
    "ScaleDegree",

    # Modal characteristics
    "ModalCharacteristics",
    "MODAL_CHARACTERISTICS",
    "SCALE_TO_CHORD_MAPPINGS",

    # Motion analysis
    "MotionType",
    "analyze_melodic_motion",

    # Phrase classification
    "PhraseType",
    "classify_phrase_length",

    # Utility functions
    "get_interval_name",
    "get_modal_characteristics",
    "get_characteristic_degrees",
    "get_harmonic_implications",
    "get_scale_applications",
    "describe_step_pattern",

    # Reference collections
    "ALL_MODES",
    "ALL_MAJOR_KEYS",
    "ALL_MINOR_KEYS",
    "ALL_KEYS",

    # Analysis helper functions
    "describe_contour",
    "analyze_intervallic_content",
]
