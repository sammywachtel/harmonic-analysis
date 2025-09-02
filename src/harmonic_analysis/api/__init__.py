"""
User-facing API layer for harmonic analysis.

This package contains the primary user-facing functions that 90% of users need.
All functions in this package are exposed at the top level of the library.
"""

# Core analysis functions
from .analysis import analyze_chord_progression, analyze_melody, analyze_scale

# Character and emotional analysis
from .character import (
    CharacterSuggestion,
    EmotionalProfile,
    ProgressionCharacter,
    analyze_progression_character,
    describe_emotional_contour,
    get_character_suggestions,
    get_mode_emotional_profile,
    get_modes_by_brightness,
)

# Musical data access
from .musical_data import (
    get_all_degree_to_mode_mappings,
    get_all_notes,
    get_all_scale_systems,
    get_circle_of_fifths,
    get_complete_musical_reference,
    get_degree_to_mode_mapping,
    get_interval_names,
    get_mode_popularity_ranking,
    get_mode_to_scale_family_mapping,
    get_note_to_pitch_class_mapping,
    get_parent_key_indices,
    get_parent_key_mapping,
    get_pitch_class_to_note_mapping,
    get_relative_major_minor_pairs,
    get_scale_notes,
    get_scale_reference_for_frontend,
    get_scale_system_info,
    get_scale_system_names,
    normalize_note_name,
    note_to_pitch_class,
    pitch_class_to_note,
    validate_musical_input,
)

__all__ = [
    # Core analysis functions
    "analyze_chord_progression",
    "analyze_melody",
    "analyze_scale",
    # Musical data API
    "get_all_degree_to_mode_mappings",
    "get_all_notes",
    "get_all_scale_systems",
    "get_circle_of_fifths",
    "get_complete_musical_reference",
    "get_degree_to_mode_mapping",
    "get_interval_names",
    "get_mode_popularity_ranking",
    "get_mode_to_scale_family_mapping",
    "get_note_to_pitch_class_mapping",
    "get_parent_key_indices",
    "get_parent_key_mapping",
    "get_pitch_class_to_note_mapping",
    "get_relative_major_minor_pairs",
    "get_scale_notes",
    "get_scale_reference_for_frontend",
    "get_scale_system_info",
    "get_scale_system_names",
    "normalize_note_name",
    "note_to_pitch_class",
    "pitch_class_to_note",
    "validate_musical_input",
    # Character and emotional analysis
    "CharacterSuggestion",
    "EmotionalProfile",
    "ProgressionCharacter",
    "analyze_progression_character",
    "describe_emotional_contour",
    "get_character_suggestions",
    "get_mode_emotional_profile",
    "get_modes_by_brightness",
]
