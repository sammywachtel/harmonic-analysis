"""
API helper functions for external application integration.

This module provides functions specifically designed to help external
applications (like demos, web apps, reference tools) interact with
the harmonic analysis library.
"""

from typing import Any, Dict, List, Optional

from ..types import AnalysisSuggestions, KeySuggestion
from .analysis_helpers import get_scale_reference_data
from .music_theory_constants import (
    ALL_KEYS,
    ALL_MAJOR_KEYS,
    ALL_MINOR_KEYS,
    ALL_MODES,
    MODAL_CHARACTERISTICS,
    get_interval_name,
)


def get_all_reference_data() -> Dict[str, Any]:
    """
    Get complete reference data for music theory applications.

    Returns:
        Comprehensive dictionary with all music theory reference data
    """
    return {
        "modes": {
            mode_name: {
                "name": chars.name,
                "characteristic_degrees": chars.characteristic_degrees,
                "harmonic_implications": chars.harmonic_implications,
                "typical_applications": chars.typical_applications,
                "brightness": chars.brightness,
            }
            for mode_name, chars in MODAL_CHARACTERISTICS.items()
        },
        "keys": {"major": ALL_MAJOR_KEYS, "minor": ALL_MINOR_KEYS, "all": ALL_KEYS},
        "intervals": {
            semitones: name
            for semitones, name in [(i, get_interval_name(i)) for i in range(13)]
        },
        "scale_applications": {
            mode: get_scale_reference_data(mode) for mode in ALL_MODES
        },
    }


def format_suggestions_for_api(
    suggestions: Optional[AnalysisSuggestions],
) -> Optional[Dict[str, Any]]:
    """
    Format bidirectional suggestions for API responses.

    Args:
        suggestions: AnalysisSuggestions object from library

    Returns:
        Formatted dictionary suitable for JSON API responses
    """
    if not suggestions:
        return None

    def format_key_suggestion(suggestion: KeySuggestion) -> Dict[str, Any]:
        return {
            "key": suggestion.suggested_key,
            "confidence": suggestion.confidence,
            "reasoning": suggestion.reason,
            "detected_pattern": getattr(suggestion, "detected_pattern", None),
            "improvement_type": suggestion.potential_improvement,
        }

    formatted = {
        "parent_key_suggestions": [],
        "unnecessary_key_suggestions": [],
        "key_change_suggestions": [],
        "general_suggestions": getattr(suggestions, "general_suggestions", []),
    }

    # Format parent key suggestions (add key)
    if (
        hasattr(suggestions, "parent_key_suggestions")
        and suggestions.parent_key_suggestions
    ):
        formatted["parent_key_suggestions"] = [
            format_key_suggestion(s) for s in suggestions.parent_key_suggestions
        ]

    # Format unnecessary key suggestions (remove key)
    if (
        hasattr(suggestions, "unnecessary_key_suggestions")
        and suggestions.unnecessary_key_suggestions
    ):
        formatted["unnecessary_key_suggestions"] = [
            format_key_suggestion(s) for s in suggestions.unnecessary_key_suggestions
        ]

    # Format key change suggestions (change key)
    if (
        hasattr(suggestions, "key_change_suggestions")
        and suggestions.key_change_suggestions
    ):
        formatted["key_change_suggestions"] = [
            format_key_suggestion(s) for s in suggestions.key_change_suggestions
        ]

    return formatted


def get_modal_chord_progressions() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get common chord progressions for each mode.

    Returns:
        Dictionary mapping mode names to common progressions
    """
    return {
        "Ionian": [
            {
                "progression": ["I", "V", "vi", "IV"],
                "description": "Classic pop progression",
            },
            {"progression": ["I", "vi", "IV", "V"], "description": "50s progression"},
            {"progression": ["IV", "V", "I"], "description": "Plagal resolution"},
        ],
        "Dorian": [
            {
                "progression": ["i", "♭VII", "IV", "i"],
                "description": "Dorian i-♭VII-IV",
            },
            {
                "progression": ["i", "iv", "♭VII", "i"],
                "description": "Minor modal progression",
            },
            {"progression": ["i", "♭III", "♭VII", "IV"], "description": "Dorian cycle"},
        ],
        "Phrygian": [
            {
                "progression": ["i", "♭II", "♭III", "i"],
                "description": "Phrygian cadence",
            },
            {
                "progression": ["i", "♭vii", "♭VI", "♭VII"],
                "description": "Descending Phrygian",
            },
            {"progression": ["♭II", "♭III", "i"], "description": "Spanish cadence"},
        ],
        "Lydian": [
            {"progression": ["I", "#IV", "I"], "description": "Lydian characteristic"},
            {"progression": ["I", "II", "I"], "description": "Bright Lydian sound"},
            {
                "progression": ["I", "#IV", "♭VII", "I"],
                "description": "Lydian modal cycle",
            },
        ],
        "Mixolydian": [
            {
                "progression": ["I", "♭VII", "IV", "I"],
                "description": "Mixolydian I-♭VII-IV",
            },
            {"progression": ["I", "♭VII", "I"], "description": "Dominant modal sound"},
            {
                "progression": ["I", "iv", "♭VII", "I"],
                "description": "Mixed major/minor",
            },
        ],
        "Aeolian": [
            {
                "progression": ["i", "♭VI", "♭VII", "i"],
                "description": "Natural minor progression",
            },
            {
                "progression": ["i", "iv", "♭VII", "♭VI"],
                "description": "Descending minor",
            },
            {
                "progression": ["i", "♭III", "♭VI", "♭VII"],
                "description": "Minor modal cycle",
            },
        ],
        "Locrian": [
            {"progression": ["i°", "♭II", "♭III"], "description": "Unstable Locrian"},
            {"progression": ["♭II", "♭III", "i°"], "description": "Avoiding tonic"},
            {"progression": ["♭VI", "♭VII", "i°"], "description": "Rare Locrian usage"},
        ],
    }


def get_chord_scale_relationships() -> Dict[str, List[str]]:
    """
    Get chord types that work with each scale.

    Returns:
        Dictionary mapping scales to compatible chord types
    """
    return {
        "Major (Ionian)": ["maj7", "6", "maj9", "add9", "maj7#11"],
        "Dorian": ["m7", "m6", "m9", "m13", "madd9"],
        "Phrygian": ["m7", "m♭9", "sus♭9", "m7♭9"],
        "Lydian": ["maj7#11", "maj9#11", "#11", "add#11"],
        "Mixolydian": ["7", "9", "13", "sus4", "7sus4"],
        "Natural Minor (Aeolian)": ["m7", "m6", "m9", "madd9"],
        "Locrian": ["m7♭5", "ø7", "°7"],
        "Harmonic Minor": ["mM7", "°7", "m6", "7♭9"],
        "Melodic Minor": ["mM7", "m6", "maj7#11", "7#11"],
    }


def get_interval_training_data() -> Dict[str, Dict[str, Any]]:
    """
    Get data for interval training applications.

    Returns:
        Comprehensive interval training data
    """
    training_data = {}

    for semitones in range(13):  # Unison to octave
        interval_name = get_interval_name(semitones)

        training_data[interval_name] = {
            "semitones": semitones,
            "name": interval_name,
            "abbreviation": get_interval_name(semitones, use_abbreviation=True),
            "quality": _get_interval_quality(semitones),
            "inversion": (
                get_interval_name(12 - semitones) if semitones > 0 else "Unison"
            ),
            "common_examples": _get_interval_examples(semitones),
            "difficulty_level": _get_interval_difficulty(semitones),
        }

    return training_data


def _get_interval_quality(semitones: int) -> str:
    """Get interval quality classification."""
    if semitones in [0, 5, 7, 12]:
        return "Perfect"
    elif semitones in [1, 3, 6, 8, 10]:
        return "Minor" if semitones in [1, 3, 8, 10] else "Augmented"
    else:
        return "Major"


def _get_interval_examples(semitones: int) -> List[str]:
    """Get common musical examples for interval."""
    examples = {
        0: ["Same note", "Unison singing"],
        1: ["Jaws theme", "Chromatic steps"],
        2: ["Happy Birthday start", "Mary Had a Little Lamb"],
        3: ["Greensleeves", "Georgia on My Mind"],
        4: ["Oh When the Saints", "Here Comes the Bride"],
        5: ["Amazing Grace", "Auld Lang Syne"],
        6: ["Maria (West Side Story)", "The Simpsons theme"],
        7: ["Twinkle Star", "Perfect 5th harmony"],
        8: ["Nobody Knows", "Minor 6th leap"],
        9: ["My Way", "Major 6th leap up"],
        10: ["There's a Place for Us", "Minor 7th"],
        11: ["Take On Me", "Major 7th leap"],
        12: ["Somewhere Over Rainbow", "Octave leap"],
    }
    return examples.get(semitones, ["Various examples"])


def _get_interval_difficulty(semitones: int) -> str:
    """Get difficulty level for interval training."""
    if semitones in [0, 7, 12]:  # Unison, 5th, octave
        return "Beginner"
    elif semitones in [2, 4, 5]:  # 2nd, 3rd, 4th
        return "Easy"
    elif semitones in [3, 8, 9]:  # Minor 3rd, 6ths
        return "Intermediate"
    else:  # 7ths, tritone
        return "Advanced"


def create_scale_reference_endpoint_data(mode: str) -> Dict[str, Any]:
    """
    Create comprehensive data for a scale reference endpoint.

    Args:
        mode: Name of mode/scale

    Returns:
        Complete reference data for the mode
    """
    base_data = get_scale_reference_data(mode)
    progressions = get_modal_chord_progressions().get(mode, [])
    chord_relationships = get_chord_scale_relationships().get(mode, [])

    return {
        **base_data,
        "common_progressions": progressions,
        "compatible_chords": chord_relationships,
        "interval_structure": _get_mode_interval_structure(mode),
        "relative_modes": _get_relative_modes(mode),
    }


def _get_mode_interval_structure(mode: str) -> List[str]:
    """Get interval structure for a mode."""
    # This would ideally be computed from scale degree patterns
    # Simplified version here
    structures = {
        "Ionian": ["W", "W", "H", "W", "W", "W", "H"],
        "Dorian": ["W", "H", "W", "W", "W", "H", "W"],
        "Phrygian": ["H", "W", "W", "W", "H", "W", "W"],
        "Lydian": ["W", "W", "W", "H", "W", "W", "H"],
        "Mixolydian": ["W", "W", "H", "W", "W", "H", "W"],
        "Aeolian": ["W", "H", "W", "W", "H", "W", "W"],
        "Locrian": ["H", "W", "W", "H", "W", "W", "W"],
    }
    return structures.get(mode, ["W", "W", "H", "W", "W", "W", "H"])


def _get_relative_modes(mode: str) -> List[str]:
    """Get modes that share the same key signature."""
    mode_families = {
        "Ionian": ["Dorian", "Phrygian", "Lydian", "Mixolydian", "Aeolian", "Locrian"],
        "Dorian": ["Phrygian", "Lydian", "Mixolydian", "Aeolian", "Locrian", "Ionian"],
        "Phrygian": ["Lydian", "Mixolydian", "Aeolian", "Locrian", "Ionian", "Dorian"],
        "Lydian": ["Mixolydian", "Aeolian", "Locrian", "Ionian", "Dorian", "Phrygian"],
        "Mixolydian": ["Aeolian", "Locrian", "Ionian", "Dorian", "Phrygian", "Lydian"],
        "Aeolian": ["Locrian", "Ionian", "Dorian", "Phrygian", "Lydian", "Mixolydian"],
        "Locrian": ["Ionian", "Dorian", "Phrygian", "Lydian", "Mixolydian", "Aeolian"],
    }
    return mode_families.get(mode, [])
