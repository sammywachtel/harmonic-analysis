"""Text Formatting Utilities for Harmonic Analysis.

Provides consistent formatting for analysis results, evidence descriptions,
and user-facing output across the library.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional


def clean_evidence_text(text: str) -> str:
    """
    Clean up evidence text by removing Python object representations
    and improving readability.

    Args:
        text: Raw evidence text that may contain object representations

    Returns:
        Cleaned, human-readable text
    """
    if not isinstance(text, str):
        text = str(text)

    # Remove ModalEvidence object representations (split for line length)
    modal_evidence_pattern = (
        r"ModalEvidence\(type=<EvidenceType\.(\w+): \'(\w+)\'>, "
        r"description=\'([^\']+)\', strength=([0-9.]+)\)"
    )

    def replace_modal_evidence(match):
        description = match.group(3)
        strength = match.group(4)
        return f"{description} (strength: {strength})"

    text = re.sub(modal_evidence_pattern, replace_modal_evidence, text)

    # Remove other object representations
    text = re.sub(r"<EvidenceType\.(\w+): \'(\w+)\'>", r"\1", text)
    text = re.sub(r"EvidenceType\.(\w+)", r"\1", text)

    # Clean up common patterns
    text = re.sub(r"\s+", " ", text)  # Multiple spaces to single space
    text = text.strip()

    # Improve readability
    if "indicates" in text and "characteristics" in text:
        # Simplify repetitive evidence descriptions
        parts = text.split(" indicates ")
        if len(parts) >= 2:
            evidence_part = parts[0].strip()
            characteristics_part = parts[1].strip()
            if "characteristics" in characteristics_part:
                text = f"{evidence_part} shows modal characteristics"

    return text


def format_chord_progression(chords: List[str], separator: str = " - ") -> str:
    """
    Format chord progression for display.

    Args:
        chords: List of chord symbols
        separator: String to use between chords

    Returns:
        Formatted chord progression string
    """
    if not chords:
        return ""

    return separator.join(chords)


def format_roman_numerals(numerals: List[str], separator: str = " - ") -> str:
    """
    Format Roman numeral progression for display.

    Args:
        numerals: List of Roman numerals
        separator: String to use between numerals

    Returns:
        Formatted Roman numeral string
    """
    if not numerals:
        return ""

    return separator.join(numerals)


def format_confidence_level(confidence: float) -> str:
    """
    Convert numeric confidence to descriptive level.

    Args:
        confidence: Confidence score (0.0 to 1.0)

    Returns:
        Descriptive confidence level string
    """
    if confidence >= 0.85:
        return "Very High"
    elif confidence >= 0.70:
        return "High"
    elif confidence >= 0.55:
        return "Moderate"
    elif confidence >= 0.40:
        return "Low"
    else:
        return "Very Low"


def format_analysis_summary(
    analysis_type: str,
    confidence: float,
    key_findings: List[str],
    max_findings: int = 3,
) -> str:
    """
    Format a concise analysis summary.

    Args:
        analysis_type: Type of analysis (e.g., "Modal", "Functional")
        confidence: Confidence score
        key_findings: List of key findings
        max_findings: Maximum findings to include

    Returns:
        Formatted summary string
    """
    confidence_level = format_confidence_level(confidence)

    findings_text = ""
    if key_findings:
        limited_findings = key_findings[:max_findings]
        findings_text = f" - {'; '.join(limited_findings)}"

    return f"{analysis_type} Analysis ({confidence_level} confidence){findings_text}"


def format_modal_characteristics(characteristics: List[str]) -> str:
    """
    Format modal characteristics for display.

    Args:
        characteristics: List of modal characteristics

    Returns:
        Formatted characteristics string
    """
    if not characteristics:
        return "No specific modal characteristics detected"

    # Group similar characteristics
    grouped = {}
    for char in characteristics:
        if "chord" in char.lower():
            category = "Characteristic Chords"
        elif "scale" in char.lower() or "degree" in char.lower():
            category = "Scale Degrees"
        elif "cadence" in char.lower():
            category = "Cadential Patterns"
        else:
            category = "General Features"

        if category not in grouped:
            grouped[category] = []
        grouped[category].append(char)

    # Format grouped characteristics
    formatted_groups = []
    for category, items in grouped.items():
        if len(items) == 1:
            formatted_groups.append(f"{category}: {items[0]}")
        else:
            formatted_groups.append(f"{category}: {', '.join(items)}")

    return " | ".join(formatted_groups)


def format_scale_degrees(degrees: List[str]) -> str:
    """
    Format scale degrees with proper notation.

    Args:
        degrees: List of scale degree strings

    Returns:
        Formatted scale degrees string
    """
    if not degrees:
        return ""

    # Convert common notation
    formatted = []
    for degree in degrees:
        # Convert flats and sharps to proper symbols if needed
        degree = degree.replace("b", "♭").replace("#", "♯")
        formatted.append(degree)

    return " - ".join(formatted)


def truncate_with_ellipsis(text: str, max_length: int = 100) -> str:
    """
    Truncate text with ellipsis if too long.

    Args:
        text: Text to potentially truncate
        max_length: Maximum length before truncation

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text

    # Try to break at word boundary
    truncated = text[: max_length - 3]
    last_space = truncated.rfind(" ")

    if last_space > max_length * 0.7:  # If we can break reasonably close
        return truncated[:last_space] + "..."
    else:
        return truncated + "..."


def format_evidence_list(evidence_items: List[Dict[str, Any]]) -> List[str]:
    """
    Format evidence items for display.

    Args:
        evidence_items: List of evidence dictionaries

    Returns:
        List of formatted evidence strings
    """
    formatted = []

    for evidence in evidence_items:
        description = evidence.get("description", "")
        strength = evidence.get("strength", 0.0)

        # Clean the description
        cleaned_desc = clean_evidence_text(description)

        # Format with strength if significant
        if strength >= 0.7:
            strength_text = " (strong evidence)"
        elif strength >= 0.5:
            strength_text = " (moderate evidence)"
        else:
            strength_text = ""

        formatted.append(f"{cleaned_desc}{strength_text}")

    return formatted


# Language configuration loading
def _load_language_config() -> Dict[str, Any]:
    """Load language configuration from JSON file."""
    current_dir = os.path.dirname(__file__)
    language_file = os.path.join(current_dir, "language.json")

    try:
        with open(language_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback to hardcoded defaults if file missing/corrupted
        return {
            "classifications": {
                "diatonic": "Diatonic within provided key context",
                "modal_borrowing": "Modal borrowing from parent scale",
                "modal_candidate": "Modal characteristics without clear parent key",
            },
            "scale_degrees": {str(i): str(i + 1) for i in range(12)},
            "analysis_templates": {
                "non_diatonic_notes": "Non-diatonic: {notes}",
                "analysis_parts_separator": " - ",
            },
        }


# Load language config once at module level
_LANGUAGE = _load_language_config()


def format_classification_description(classification: str) -> str:
    """
    Convert classification to human-readable description.

    Args:
        classification: Classification type (diatonic, modal_borrowing, modal_candidate)

    Returns:
        Human-readable description
    """
    return _LANGUAGE["classifications"].get(classification, classification)


def generate_scale_degrees_from_notes(notes: List[str]) -> List[str]:
    """
    Generate scale degree notation from note names.

    Args:
        notes: List of note names (e.g., ["C", "D", "E"])

    Returns:
        List of scale degree strings (e.g., ["1", "2", "3"])
    """
    if not notes:
        return []

    from harmonic_analysis.utils.chord_parser import NOTE_TO_PITCH_CLASS

    try:
        root_pc = NOTE_TO_PITCH_CLASS[notes[0].replace("♯", "#").replace("♭", "b")]
        scale_degrees = []

        for note in notes:
            pc = NOTE_TO_PITCH_CLASS[note.replace("♯", "#").replace("♭", "b")]
            degree = (pc - root_pc) % 12

            scale_degrees.append(
                _LANGUAGE["scale_degrees"].get(str(degree), str(degree))
            )

        return scale_degrees
    except KeyError:
        # Fallback to numbered degrees if note parsing fails
        return [str(i + 1) for i in range(len(notes))]


def format_harmonic_implications(
    result, classification: Optional[str] = None
) -> List[str]:
    """
    Generate harmonic implications from analysis result.

    Args:
        result: Analysis result object with classification and other fields
        classification: Optional override classification

    Returns:
        List of harmonic implication strings
    """
    implications = []

    # Use provided classification or extract from result
    if classification is None:
        classification = getattr(result, "classification", "modal_candidate")

    # Get base implications for classification
    base_implications = _LANGUAGE.get("harmonic_implications", {}).get(
        classification, []
    )
    implications.extend(base_implications)

    # Add non-diatonic implications
    non_diatonic = getattr(result, "non_diatonic_pitches", [])
    if non_diatonic:
        template = _LANGUAGE["analysis_templates"]["non_diatonic_implications"]
        implications.append(template.format(notes=", ".join(non_diatonic)))

    # Add parent scale compatibility
    parent_scales = getattr(result, "parent_scales", [])
    if parent_scales:
        template = _LANGUAGE["analysis_templates"]["parent_scale_compatibility"]
        implications.append(template.format(scales=", ".join(parent_scales)))

    return implications


def format_scale_melody_analysis(result) -> Dict[str, Any]:
    """
    Format complete scale/melody analysis for API responses.

    Args:
        result: ScaleMelodyAnalysisResult object

    Returns:
        Formatted analysis dictionary ready for API response
    """
    from harmonic_analysis.scale_melody_analysis import ScaleMelodyAnalysisResult

    if not isinstance(result, ScaleMelodyAnalysisResult):
        raise ValueError("Expected ScaleMelodyAnalysisResult object")

    # Generate primary mode name
    if result.modal_labels:
        # Prefer the most likely modal label or the first available
        if result.suggested_tonic and result.suggested_tonic in result.modal_labels:
            mode_name = result.modal_labels[result.suggested_tonic]
        elif result.notes and len(result.notes) > 0:
            # For scales, use the first note as the assumed tonic
            first_note = result.notes[0]
            # Extract just the note name without octave
            first_note_root = first_note.split()[0] if " " in first_note else first_note
            first_note_root = re.sub(
                r"[0-9]", "", first_note_root
            )  # Remove octave numbers

            if first_note_root in result.modal_labels:
                mode_name = result.modal_labels[first_note_root]
            else:
                # Fallback to first available modal label
                mode_name = list(result.modal_labels.values())[0]
        else:
            mode_name = list(result.modal_labels.values())[0]
    else:
        mode_name = "Unknown mode"

    # Build analysis text parts
    analysis_parts = [mode_name]

    # Add classification description
    if result.classification:
        classification_desc = format_classification_description(result.classification)
        analysis_parts.append(classification_desc)

    # Add non-diatonic notes if present
    if result.non_diatonic_pitches:
        template = _LANGUAGE["analysis_templates"]["non_diatonic_notes"]
        analysis_parts.append(
            template.format(notes=", ".join(result.non_diatonic_pitches))
        )

    # Join analysis parts
    separator = _LANGUAGE["analysis_templates"]["analysis_parts_separator"]
    analysis_text = separator.join(analysis_parts)

    # Generate scale degrees
    scale_degrees = generate_scale_degrees_from_notes(result.notes)

    # Generate harmonic implications
    implications = format_harmonic_implications(result)

    return {
        "input_scale": " ".join(result.notes) if result.notes else "",
        "primary_analysis": {
            "type": "MELODY" if result.melody else "SCALE",
            "confidence": result.confidence or 0.7,
            "analysis": analysis_text,
            "mode_name": mode_name,
            "parent_key": (
                result.key
                if result.key
                else (result.parent_scales[0] if result.parent_scales else None)
            ),
            "classification": result.classification,
            "modal_labels": result.modal_labels,
            "scale_degrees": scale_degrees,
            "harmonic_implications": implications,
            "suggested_tonic": result.suggested_tonic,
        },
        "metadata": {
            "analysis_time_ms": 15,
            "scale_type": result.classification,
            "parent_scales": result.parent_scales,
            "non_diatonic_pitches": result.non_diatonic_pitches,
        },
        "rationale": result.rationale,
    }


def describe_contour(contour: List[str]) -> str:
    """
    Describe melodic contour pattern using language configuration.

    Args:
        contour: List of contour directions ("U", "D", "R")

    Returns:
        Human-readable contour description
    """
    if not contour:
        return _LANGUAGE["contour_descriptions"]["static"]

    up_count = contour.count("U")
    down_count = contour.count("D")
    repeat_count = contour.count("R")

    if up_count > down_count * 2:
        return _LANGUAGE["contour_descriptions"]["strong_ascending"]
    elif down_count > up_count * 2:
        return _LANGUAGE["contour_descriptions"]["strong_descending"]
    elif up_count == down_count:
        return _LANGUAGE["contour_descriptions"]["balanced_arch"]
    elif repeat_count > len(contour) // 2:
        return _LANGUAGE["contour_descriptions"]["static_repeated"]
    else:
        return _LANGUAGE["contour_descriptions"]["mixed_directional"]
