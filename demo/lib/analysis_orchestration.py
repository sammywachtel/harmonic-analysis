"""
Analysis orchestration and input processing for the harmonic analysis demo.

Coordinates the analysis pipeline:
- Parses and validates user inputs (chords, romans, melody, scales)
- Ensures mutual exclusivity of input types
- Calls the PatternAnalysisService
- Returns analysis results

This module is the bridge between UI inputs and the analysis library.
"""

import asyncio
from typing import TYPE_CHECKING, Any, List, Optional, Sequence

if TYPE_CHECKING:
    from harmonic_analysis.core.pattern_engine.pattern_engine import AnalysisContext
    from harmonic_analysis.services.pattern_analysis_service import (
        PatternAnalysisService,
    )

from demo.lib.constants import (
    MISSING_MELODY_KEY_MSG,
    MISSING_SCALE_KEY_MSG,
    NOTE_RE,
    ROMAN_RE,
)

# Lazy imports to avoid circular dependencies
_SERVICE = None


def get_service() -> "PatternAnalysisService":
    """Get or create the PatternAnalysisService singleton."""
    global _SERVICE
    if _SERVICE is None:
        from harmonic_analysis.services.pattern_analysis_service import (
            PatternAnalysisService,
        )

        _SERVICE = PatternAnalysisService()
    return _SERVICE


# ============================================================================
# Input Parsing and Validation
# ============================================================================


def parse_csv(value: Optional[str]) -> List[str]:
    """Parse comma or space-separated values."""
    if not value:
        return []

    # Handle both comma and space delimiters
    # First try comma separation
    if "," in value:
        return [item.strip() for item in value.split(",") if item.strip()]
    else:
        # Use space separation if no commas found
        return [item.strip() for item in value.split() if item.strip()]


def resolve_key_input(value: Optional[str]) -> Optional[str]:
    """Normalize user-provided key hints, treating 'None' as no key."""
    if value is None:
        return None

    if isinstance(value, str):
        normalized = value.strip()
        if not normalized or normalized.lower() == "none":
            return None
        return normalized


def validate_list(kind: str, items: List[str]) -> List[str]:
    """
    Validate a list of musical tokens (chords, romans, notes).

    Args:
        kind: Type of token ("chord", "roman", "note")
        items: List of token strings to validate

    Returns:
        Validated list of tokens

    Raises:
        ValueError: If any tokens are invalid
    """
    if not items:
        return []

    # Opening move: use library's parsers for validation when available
    if kind == "chord":
        # Chord validation uses the library's ChordParser
        from harmonic_analysis.core.utils.chord_logic import ChordParser

        parser = ChordParser()
        invalid = []
        for item in items:
            try:
                parser.parse_chord(item)
            except ValueError:
                invalid.append(item)
        if invalid:
            raise ValueError(f"Invalid {kind} entries: {', '.join(invalid)}")
        return items
    else:
        # Roman numerals and notes still use regex (library doesn't own these)
        validator = {
            "roman": ROMAN_RE,
            "note": NOTE_RE,
        }[kind]
        invalid = [item for item in items if not validator.match(item)]
        if invalid:
            raise ValueError(f"Invalid {kind} entries: {', '.join(invalid)}")
        return items


def validate_exclusive_input(
    chords_text: Optional[str],
    romans_text: Optional[str],
    melody_text: Optional[str],
    scales_input: Optional[str],
) -> None:
    """Ensure only one type of musical input is provided."""
    inputs_provided = [
        ("chords", chords_text and chords_text.strip()),
        ("romans", romans_text and romans_text.strip()),
        ("melody", melody_text and melody_text.strip()),
        ("scales", scales_input and scales_input.strip()),
    ]

    provided_types = [name for name, value in inputs_provided if value]

    if len(provided_types) == 0:
        raise ValueError(
            "Please provide at least one type of musical input (chords, romans, melody, or scales)."
        )

    if len(provided_types) > 1:
        raise ValueError(
            f"Please provide only one type of musical input. "
            f"Found: {', '.join(provided_types)}. "
            f"Analyze one type at a time for best results."
        )


def parse_melody(value: Optional[str]) -> List[str]:
    """Parse melody input, accepting both note names and MIDI numbers."""
    items = parse_csv(value)
    if not items:
        return []

    validated: List[str] = []
    for item in items:
        token = item.strip()
        if token.isdigit():
            validated.append(token)
        else:
            if not NOTE_RE.match(token):
                raise ValueError(f"Invalid melody note: {token}")
            validated.append(token)
    return validated


def parse_scales(values: Optional[Sequence[str]]) -> List[List[str]]:
    """Parse scale definitions from multiple lines."""
    if not values:
        return []

    scales: List[List[str]] = []
    for raw in values:
        notes = validate_list("note", parse_csv(raw))
        if not notes:
            raise ValueError("Scale definitions cannot be empty.")
        scales.append(notes)
    return scales


def normalize_scale_input(raw_scales: Optional[str | Sequence[str]]) -> List[str]:
    """Normalize scale input from string or sequence."""
    if raw_scales is None:
        return []
    if isinstance(raw_scales, str):
        candidates = [
            line.strip() for line in raw_scales.splitlines() if line and line.strip()
        ]
        return candidates
    return [item.strip() for item in raw_scales if item and item.strip()]


# ============================================================================
# Analysis Orchestration
# ============================================================================


def analyze_progression(
    *,
    key: Optional[str],
    profile: str,
    chords_text: Optional[str],
    romans_text: Optional[str],
    melody_text: Optional[str],
    scales_input: Optional[str | Sequence[str]],
) -> "AnalysisContext":
    """
    Coordinate analysis of a musical progression.

    Validates inputs, parses them, and creates an AnalysisContext.

    Args:
        key: Optional key hint
        profile: Analysis profile name
        chords_text: Comma-separated chord symbols
        romans_text: Comma-separated roman numerals
        melody_text: Comma-separated melody notes
        scales_input: Scale definitions (multi-line or sequence)

    Returns:
        AnalysisContext object ready for analysis

    Raises:
        ValueError: If inputs are invalid or conflicting
    """
    from harmonic_analysis.core.pattern_engine.pattern_engine import AnalysisContext
    from harmonic_analysis.core.pattern_engine.token_converter import romanize_chord

    if not any([chords_text, romans_text, melody_text, scales_input]):
        raise ValueError(
            "Provide at least one of --chords, --romans, --melody, or --scale for analysis."
        )

    key_hint = resolve_key_input(key)

    chords = validate_list("chord", parse_csv(chords_text)) if chords_text else []

    romans = validate_list("roman", parse_csv(romans_text)) if romans_text else []
    if chords and romans and len(romans) != len(chords):
        raise ValueError("Number of roman numerals must match number of chords.")

    # Auto-romanize chords if we have a key but no romans
    if chords and not romans and key_hint:
        auto_romans = []
        for chord in chords:
            try:
                auto_romans.append(romanize_chord(chord, key_hint))
            except Exception:
                auto_romans = []
                break
        if auto_romans:
            romans = [rn.replace("b", "♭") for rn in auto_romans]

    melody = parse_melody(melody_text)

    scale_entries = normalize_scale_input(scales_input)
    scales = parse_scales(scale_entries)

    if melody and not key_hint:
        raise ValueError(MISSING_MELODY_KEY_MSG)

    if scales and not key_hint:
        raise ValueError(MISSING_SCALE_KEY_MSG)

    return AnalysisContext(
        key=key_hint,
        chords=chords,
        roman_numerals=romans,
        melody=melody,
        scales=scales,
        metadata={"profile": profile, "source": "demo/full_library_demo.py"},
    )


async def run_analysis_async(
    chord_symbols: List[str], profile: str, key_hint: Optional[str]
) -> Any:
    """Run analysis asynchronously."""
    service = get_service()
    return await service.analyze_with_patterns_async(
        chord_symbols=chord_symbols, profile=profile, key_hint=key_hint
    )


def run_analysis_sync(
    chord_symbols: List[str], profile: str, key_hint: Optional[str]
) -> Any:
    """Synchronous wrapper for CLI usage."""
    return asyncio.run(run_analysis_async(chord_symbols, profile, key_hint))
