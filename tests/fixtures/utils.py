"""
Utilities for loading and working with test fixtures.

Provides helpers for loading golden test data, creating normalized contexts,
and validating pattern matching results across transpositions.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from harmonic_analysis.core.pattern_engine.pattern_engine import AnalysisContext


def load_fixture(fixture_name: str) -> Dict[str, Any]:
    """
    Load a golden test fixture by name.

    Args:
        fixture_name: Name of fixture file (without .golden.json extension)

    Returns:
        Loaded fixture data

    Raises:
        FileNotFoundError: If fixture file doesn't exist
    """
    fixture_path = (
        Path(__file__).parent / "progressions" / f"{fixture_name}.golden.json"
    )
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_path}")

    with fixture_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def create_context_from_progression(progression: Dict[str, Any]) -> AnalysisContext:
    """
    Create an AnalysisContext from a progression fixture.

    Args:
        progression: Progression data from fixture

    Returns:
        Normalized AnalysisContext
    """
    return AnalysisContext(
        key=progression.get("key"),
        chords=progression.get("chords", []),
        roman_numerals=progression.get("roman_numerals", []),
        melody=progression.get("melody", []),
        scales=progression.get("scales", []),
        metadata=progression.get("metadata", {}),
    )


def transpose_progression(
    progression: Dict[str, Any], target_key: str, semitones: int
) -> Dict[str, Any]:
    """
    Transpose a progression to a different key.

    This is a simplified transposition for testing - in reality this would
    use the full harmonic analysis transposition utilities.

    Args:
        progression: Original progression
        target_key: Target key name
        semitones: Semitones to transpose

    Returns:
        Transposed progression
    """
    # For testing, we keep roman numerals the same (they're transposition-invariant)
    # and update the key. Real implementation would transpose chord symbols.
    transposed = progression.copy()
    transposed["key"] = target_key

    # In a real implementation, we'd transpose the chord symbols here
    # For now, keep them as-is for testing the pattern matching logic

    return transposed


def validate_matches(
    actual_matches: List[Tuple[int, int]], expected_matches: List[Dict[str, Any]]
) -> List[str]:
    """
    Validate actual pattern matches against expected matches.

    Args:
        actual_matches: List of (start, end) tuples from pattern engine
        expected_matches: Expected match data from fixtures

    Returns:
        List of validation error messages (empty if all valid)
    """
    errors = []

    # Convert expected matches to spans for comparison
    expected_spans = []
    for expected in expected_matches:
        span = expected.get("span")
        if span and len(span) == 2:
            expected_spans.append((span[0], span[1]))

    # Check if all expected matches were found
    for expected_span in expected_spans:
        if expected_span not in actual_matches:
            errors.append(f"Expected match {expected_span} not found in actual matches")

    # Check for unexpected matches
    for actual_span in actual_matches:
        if actual_span not in expected_spans:
            errors.append(f"Unexpected match {actual_span} found")

    return errors


def get_all_progressions(fixture_name: str) -> List[Dict[str, Any]]:
    """
    Get all progressions from a fixture file.

    Args:
        fixture_name: Name of fixture file

    Returns:
        List of progression dictionaries
    """
    fixture = load_fixture(fixture_name)
    return fixture.get("progressions", [])


def get_transposition_keys(fixture_name: str) -> List[Dict[str, Any]]:
    """
    Get transposition test keys from a fixture file.

    Args:
        fixture_name: Name of fixture file

    Returns:
        List of transposition data with keys and semitone offsets
    """
    fixture = load_fixture(fixture_name)
    return fixture.get("transpositions", [])


def generate_transposed_tests(
    progression: Dict[str, Any], transpositions: List[Dict[str, Any]]
) -> List[Tuple[AnalysisContext, List[Dict[str, Any]]]]:
    """
    Generate test cases for all transpositions of a progression.

    Args:
        progression: Base progression
        transpositions: List of transposition data

    Returns:
        List of (context, expected_matches) tuples for each transposition
    """
    test_cases = []

    for transposition in transpositions:
        target_key = transposition["key"]
        semitones = transposition["semitones"]

        # Transpose the progression
        transposed = transpose_progression(progression, target_key, semitones)
        context = create_context_from_progression(transposed)

        # Expected matches remain the same (spans don't change with transposition)
        expected_matches = progression.get("expected_matches", [])

        test_cases.append((context, expected_matches))

    return test_cases


class FixtureLoader:
    """Helper class for loading and working with fixtures."""

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize fixture loader.

        Args:
            base_path: Base path for fixtures (defaults to this directory)
        """
        self.base_path = base_path or Path(__file__).parent / "progressions"

    def load(self, fixture_name: str) -> Dict[str, Any]:
        """Load a fixture by name."""
        return load_fixture(fixture_name)

    def list_fixtures(self) -> List[str]:
        """List all available fixture files."""
        return [
            f.stem.replace(".golden", "") for f in self.base_path.glob("*.golden.json")
        ]

    def get_progression_by_name(
        self, fixture_name: str, progression_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific progression from a fixture by name.

        Args:
            fixture_name: Name of fixture file
            progression_name: Name of progression within fixture

        Returns:
            Progression data or None if not found
        """
        fixture = self.load(fixture_name)
        for progression in fixture.get("progressions", []):
            if progression.get("name") == progression_name:
                return progression
        return None
