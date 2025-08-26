"""
Utility functions and helpers for harmonic analysis.

This module contains music theory constants, analysis helpers, and API utilities
that can be used throughout the library and by external applications.
"""

# Analysis helper functions
from .analysis_helpers import (
    analyze_intervallic_content,
    analyze_phrase_structure,
    describe_contour,
    format_analysis_for_display,
    get_scale_reference_data,
)

# API integration helpers
from .api_helpers import (
    create_scale_reference_endpoint_data,
    format_suggestions_for_api,
    get_all_reference_data,
    get_chord_scale_relationships,
    get_interval_training_data,
    get_modal_chord_progressions,
)

# Music theory constants and mappings
from .music_theory_constants import (
    ALL_KEYS,
    ALL_MAJOR_KEYS,
    ALL_MINOR_KEYS,
    ALL_MODES,
    INTERVAL_ABBREVIATIONS,
    MODAL_CHARACTERISTICS,
    SEMITONE_TO_INTERVAL_NAME,
    MotionType,
    PhraseType,
    ScaleDegree,
    analyze_melodic_motion,
    classify_phrase_length,
    describe_step_pattern,
    get_characteristic_degrees,
    get_harmonic_implications,
    get_interval_name,
    get_modal_characteristics,
    get_scale_applications,
)

__all__ = [
    # Constants and mappings
    "SEMITONE_TO_INTERVAL_NAME",
    "INTERVAL_ABBREVIATIONS",
    "MODAL_CHARACTERISTICS",
    "ALL_MODES",
    "ALL_MAJOR_KEYS",
    "ALL_MINOR_KEYS",
    "ALL_KEYS",
    # Core utility functions
    "get_interval_name",
    "get_modal_characteristics",
    "get_characteristic_degrees",
    "get_harmonic_implications",
    "get_scale_applications",
    "describe_step_pattern",
    "analyze_melodic_motion",
    "classify_phrase_length",
    # Analysis helpers
    "describe_contour",
    "analyze_intervallic_content",
    "analyze_phrase_structure",
    "get_scale_reference_data",
    "format_analysis_for_display",
    # API helpers
    "get_all_reference_data",
    "format_suggestions_for_api",
    "get_modal_chord_progressions",
    "get_chord_scale_relationships",
    "get_interval_training_data",
    "create_scale_reference_endpoint_data",
    # Enums
    "MotionType",
    "ScaleDegree",
    "PhraseType",
]
