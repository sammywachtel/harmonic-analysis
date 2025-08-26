"""
Analysis helper functions for common music theory operations.

This module provides high-level functions that build on the constants
and mappings to perform common analytical tasks.
"""

from typing import Any, Dict, List

from .music_theory_constants import (
    analyze_melodic_motion,
    classify_phrase_length,
    get_interval_name,
    get_modal_characteristics,
)


def describe_contour(contour_pattern: List[str]) -> str:
    """
    Describe melodic contour from pattern of U (up), D (down), R (repeat).

    Args:
        contour_pattern: List of 'U', 'D', 'R' indicating melodic direction

    Returns:
        Human-readable contour description
    """
    if not contour_pattern:
        return "no contour"

    pattern_length = len(contour_pattern)

    # Count directional movements
    up_count = contour_pattern.count("U")
    down_count = contour_pattern.count("D")
    repeat_count = contour_pattern.count("R")

    # Analyze overall shape
    if up_count > down_count * 2:
        overall_shape = "ascending"
    elif down_count > up_count * 2:
        overall_shape = "descending"
    else:
        overall_shape = "undulating"

    # Analyze specific patterns
    pattern_str = "".join(contour_pattern)

    # Check for arches
    if "U" in pattern_str and "D" in pattern_str:
        first_up = pattern_str.find("U")
        last_down = pattern_str.rfind("D")
        if first_up < last_down:
            # Has arch shape
            if up_count == down_count:
                return f"arch-shaped contour ({pattern_length} movements)"
            elif up_count > down_count:
                return f"ascending arch ({pattern_length} movements)"
            else:
                return f"descending arch ({pattern_length} movements)"

    # Check for terraced patterns
    if repeat_count > pattern_length * 0.3:
        return (
            f"terraced {overall_shape} contour with plateaus "
            f"({pattern_length} movements)"
        )

    # Standard descriptions
    if overall_shape == "undulating":
        return f"wave-like contour with {up_count} ascents and {down_count} descents"
    else:
        return f"{overall_shape} contour ({pattern_length} movements)"


def analyze_intervallic_content(pitch_classes: List[int]) -> Dict[str, Any]:
    """
    Analyze intervallic content of a pitch sequence.

    Args:
        pitch_classes: List of pitch class integers (0-11)

    Returns:
        Dictionary with interval analysis results
    """
    if len(pitch_classes) < 2:
        return {
            "intervals": [],
            "interval_names": [],
            "largest_leap": 0,
            "largest_leap_name": "Unison",
            "melodic_range": 0,
            "motion_analysis": "insufficient data",
        }

    # Calculate intervals between consecutive notes
    intervals = []
    for i in range(1, len(pitch_classes)):
        interval = pitch_classes[i] - pitch_classes[i - 1]
        # Convert to shortest path (considering octave)
        if interval > 6:
            interval = interval - 12
        elif interval < -6:
            interval = interval + 12
        intervals.append(interval)

    # Get interval names
    interval_names = [get_interval_name(abs(interval)) for interval in intervals]

    # Find largest leap
    largest_leap = max(intervals, key=abs) if intervals else 0
    largest_leap_name = get_interval_name(abs(largest_leap))

    # Calculate melodic range
    melodic_range = max(pitch_classes) - min(pitch_classes)

    # Analyze motion type
    motion_type, motion_description = analyze_melodic_motion(intervals)

    return {
        "intervals": intervals,
        "interval_names": interval_names,
        "largest_leap": largest_leap,
        "largest_leap_name": largest_leap_name,
        "melodic_range": melodic_range,
        "motion_analysis": motion_description,
        "motion_type": motion_type.value,
        "stepwise_percentage": (
            round(sum(1 for i in intervals if abs(i) <= 2) / len(intervals) * 100)
            if intervals
            else 0
        ),
    }


def analyze_phrase_structure(
    note_sequence: List[str], contour: List[str]
) -> Dict[str, Any]:
    """
    Analyze phrase structure characteristics.

    Args:
        note_sequence: List of note names
        contour: Contour pattern (U/D/R)

    Returns:
        Dictionary with phrase analysis results
    """
    note_count = len(note_sequence)
    phrase_type = classify_phrase_length(note_count)
    contour_description = describe_contour(contour)

    # Identify potential cadential points
    cadential_points = []

    # Check for repetition at the end (cadential effect)
    if len(note_sequence) > 1 and note_sequence[-1] == note_sequence[-2]:
        cadential_points.append("Final note repetition")

    # Check for return to opening note (rounded phrase)
    if len(note_sequence) > 2 and note_sequence[0] == note_sequence[-1]:
        cadential_points.append("Returns to opening pitch")

    # Check for large leaps near the end
    if len(contour) > 0 and contour[-1] in ["U", "D"]:
        cadential_points.append("Final melodic leap")

    # Identify motivic repetition
    motivic_content = (
        "varied" if len(set(note_sequence)) / len(note_sequence) > 0.6 else "repetitive"
    )

    return {
        "phrase_type": phrase_type.value,
        "phrase_length": f"{note_count} notes",
        "cadential_points": (
            cadential_points if cadential_points else ["No strong cadential points"]
        ),
        "motivic_content": (
            "Predominantly varied content"
            if motivic_content == "varied"
            else "Motivically repetitive content"
        ),
        "contour_description": contour_description,
        "phrase_balance": _analyze_phrase_balance(contour),
    }


def _analyze_phrase_balance(contour: List[str]) -> str:
    """Analyze balance of phrase motion."""
    if not contour:
        return "static"

    up_count = contour.count("U")
    down_count = contour.count("D")

    if up_count == down_count:
        return "balanced motion"
    elif up_count > down_count:
        return "net ascending motion"
    else:
        return "net descending motion"


def get_scale_reference_data(scale_name: str) -> Dict[str, Any]:
    """
    Get complete reference data for a scale/mode.

    Args:
        scale_name: Name of scale/mode

    Returns:
        Complete reference data dictionary
    """
    characteristics = get_modal_characteristics(scale_name)

    if not characteristics:
        return {
            "name": scale_name,
            "characteristics": None,
            "error": "Scale not found in reference data",
        }

    return {
        "name": characteristics.name,
        "characteristic_degrees": characteristics.characteristic_degrees,
        "harmonic_implications": characteristics.harmonic_implications,
        "typical_applications": characteristics.typical_applications,
        "brightness": characteristics.brightness,
        "chord_compatibility": _get_chord_compatibility(scale_name),
        "related_scales": _get_related_scales(scale_name),
    }


def _get_chord_compatibility(scale_name: str) -> List[str]:
    """Get chords that work well with this scale."""
    # This could be expanded with more sophisticated logic
    scale_lower = scale_name.lower()

    if "major" in scale_lower or "ionian" in scale_lower:
        return ["maj7", "maj9", "6/9", "add9"]
    elif "minor" in scale_lower or "aeolian" in scale_lower:
        return ["m7", "m9", "m6", "madd9"]
    elif "dorian" in scale_lower:
        return ["m7", "m9", "m6", "m(add9)"]
    elif "mixolydian" in scale_lower:
        return ["7", "9", "13", "sus4"]
    elif "lydian" in scale_lower:
        return ["maj7#11", "maj9#11", "add#11"]
    elif "phrygian" in scale_lower:
        return ["m7", "sus♭9", "m7♭9"]
    else:
        return ["various modal chords"]


def _get_related_scales(scale_name: str) -> List[str]:
    """Get scales related to this one."""
    # Simplified - could be much more sophisticated
    scale_lower = scale_name.lower()

    if "dorian" in scale_lower:
        return ["Aeolian", "Mixolydian", "Natural Minor"]
    elif "mixolydian" in scale_lower:
        return ["Ionian", "Dorian", "Major"]
    elif "lydian" in scale_lower:
        return ["Ionian", "Mixolydian", "Major"]
    else:
        return ["Related modal scales"]


def format_analysis_for_display(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format analysis data for clean display in UIs.

    Args:
        analysis_data: Raw analysis results

    Returns:
        Formatted data suitable for display
    """
    formatted: Dict[str, Any] = {}

    # Format confidence as percentage
    if "confidence" in analysis_data:
        formatted["confidence_percentage"] = f"{analysis_data['confidence'] * 100:.1f}%"

    # Format interval data
    if "intervals" in analysis_data:
        intervallic = analysis_data["intervals"]
        formatted["intervallic_summary"] = {
            "primary_intervals": intervallic.get("interval_names", [])[:3],  # First 3
            "largest_leap": intervallic.get("largest_leap_name", "Unknown"),
            "motion_character": intervallic.get("motion_analysis", "Unknown"),
            "stepwise_percentage": f"{intervallic.get('stepwise_percentage', 0)}%",
        }

    # Format evidence for display
    if "evidence" in analysis_data:
        formatted["evidence_summary"] = []
        for evidence in analysis_data["evidence"][:3]:  # Limit to top 3
            formatted["evidence_summary"].append(
                {
                    "type": evidence.get("type", "Unknown"),
                    "strength": f"{evidence.get('strength', 0):.2f}",
                    "description": (
                        evidence.get("description", "")[:100] + "..."
                        if len(evidence.get("description", "")) > 100
                        else evidence.get("description", "")
                    ),
                }
            )

    return formatted
