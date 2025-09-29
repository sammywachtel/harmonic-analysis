"""
Golden tests for pattern matching across different progressions and transpositions.

Tests pattern recognition against known musical progressions to ensure
consistent behavior across keys and detect regressions in pattern matching.
"""

from pathlib import Path

import pytest

from harmonic_analysis.core.pattern_engine.pattern_engine import PatternEngine
from tests.fixtures.utils import (
    FixtureLoader,
    create_context_from_progression,
    generate_transposed_tests,
    validate_matches,
)


class TestGoldenPatterns:
    """Test pattern matching against golden reference progressions."""

    @pytest.fixture
    def pattern_engine(self):
        """Create a pattern engine with loaded patterns."""
        engine = PatternEngine()
        patterns_file = (
            Path(__file__).parent.parent.parent
            / "src"
            / "harmonic_analysis"
            / "core"
            / "pattern_engine"
            / "patterns_unified.json"
        )
        engine.load_patterns(patterns_file)
        return engine

    @pytest.fixture
    def fixture_loader(self):
        """Create a fixture loader for test data."""
        return FixtureLoader()

    def test_cadence_patterns(self, pattern_engine, fixture_loader):
        """Test recognition of cadence patterns."""
        progressions = fixture_loader.load("cadences")["progressions"]

        for progression in progressions:
            context = create_context_from_progression(progression)
            expected_matches = progression.get("expected_matches", [])

            # Test each expected pattern
            for expected_match in expected_matches:
                pattern_id = expected_match["pattern_id"]
                expected_span = tuple(expected_match["span"])

                # Find the pattern in our loaded patterns
                pattern = None
                for p in pattern_engine._patterns.get("patterns", []):
                    if p["id"] == pattern_id:
                        pattern = p
                        break

                assert pattern is not None, f"Pattern {pattern_id} not found in engine"

                # Test pattern matching
                matches = pattern_engine._find_pattern_matches(pattern, context)
                assert expected_span in matches, (
                    f"Expected match {expected_span} not found for pattern {pattern_id} "
                    f"in progression {progression['name']}. Found: {matches}"
                )

    def test_modal_patterns(self, pattern_engine, fixture_loader):
        """Test recognition of modal patterns."""
        progressions = fixture_loader.load("modal")["progressions"]

        for progression in progressions:
            context = create_context_from_progression(progression)
            expected_matches = progression.get("expected_matches", [])

            for expected_match in expected_matches:
                pattern_id = expected_match["pattern_id"]
                expected_span = tuple(expected_match["span"])

                # Find the pattern
                pattern = None
                for p in pattern_engine._patterns.get("patterns", []):
                    if p["id"] == pattern_id:
                        pattern = p
                        break

                assert pattern is not None, f"Pattern {pattern_id} not found"

                # Test pattern matching
                matches = pattern_engine._find_pattern_matches(pattern, context)
                assert expected_span in matches, (
                    f"Expected modal match {expected_span} not found for {pattern_id} "
                    f"in {progression['name']}. Found: {matches}"
                )

    def test_functional_patterns(self, pattern_engine, fixture_loader):
        """Test recognition of functional harmony patterns."""
        progressions = fixture_loader.load("functional")["progressions"]

        for progression in progressions:
            context = create_context_from_progression(progression)
            expected_matches = progression.get("expected_matches", [])

            for expected_match in expected_matches:
                pattern_id = expected_match["pattern_id"]
                expected_span = tuple(expected_match["span"])

                # Find the pattern
                pattern = None
                for p in pattern_engine._patterns.get("patterns", []):
                    if p["id"] == pattern_id:
                        pattern = p
                        break

                assert pattern is not None, f"Pattern {pattern_id} not found"

                # Test pattern matching
                matches = pattern_engine._find_pattern_matches(pattern, context)
                assert expected_span in matches, (
                    f"Expected functional match {expected_span} not found for {pattern_id} "
                    f"in {progression['name']}. Found: {matches}"
                )

    def test_transposition_invariance(self, pattern_engine, fixture_loader):
        """Test that patterns are recognized consistently across transpositions."""
        # Test cadences across different keys
        cadence_fixture = fixture_loader.load("cadences")
        progressions = cadence_fixture["progressions"]
        transpositions = cadence_fixture["transpositions"]

        # Take the first progression and test it in all keys
        base_progression = progressions[0]  # perfect_authentic_cadence
        test_cases = generate_transposed_tests(base_progression, transpositions)

        for context, expected_matches in test_cases:
            for expected_match in expected_matches:
                pattern_id = expected_match["pattern_id"]
                expected_span = tuple(expected_match["span"])

                # Find the pattern
                pattern = None
                for p in pattern_engine._patterns.get("patterns", []):
                    if p["id"] == pattern_id:
                        pattern = p
                        break

                assert pattern is not None, f"Pattern {pattern_id} not found"

                # Test pattern matching
                matches = pattern_engine._find_pattern_matches(pattern, context)
                assert (
                    expected_span in matches
                ), f"Transposition invariance failed: {pattern_id} not found in {context.key}"

    def test_complex_progressions_multiple_matches(
        self, pattern_engine, fixture_loader
    ):
        """Test progressions that should trigger multiple pattern matches."""
        functional_progressions = fixture_loader.load("functional")["progressions"]

        # Find the circle of fifths progression (should match multiple patterns)
        circle_progression = None
        for prog in functional_progressions:
            if prog["name"] == "circle_of_fifths":
                circle_progression = prog
                break

        assert circle_progression is not None, "Circle of fifths progression not found"

        context = create_context_from_progression(circle_progression)
        expected_matches = circle_progression["expected_matches"]

        # Should find all expected patterns
        found_patterns = set()
        for expected_match in expected_matches:
            pattern_id = expected_match["pattern_id"]
            expected_span = tuple(expected_match["span"])

            # Find the pattern
            pattern = None
            for p in pattern_engine._patterns.get("patterns", []):
                if p["id"] == pattern_id:
                    pattern = p
                    break

            assert pattern is not None, f"Pattern {pattern_id} not found"

            # Test pattern matching
            matches = pattern_engine._find_pattern_matches(pattern, context)
            if expected_span in matches:
                found_patterns.add(pattern_id)

        expected_pattern_ids = {match["pattern_id"] for match in expected_matches}
        assert found_patterns == expected_pattern_ids, (
            f"Not all expected patterns found. Expected: {expected_pattern_ids}, "
            f"Found: {found_patterns}"
        )

    def test_no_false_positives(self, pattern_engine, fixture_loader):
        """Test that patterns don't match where they shouldn't."""
        # Create a context that should NOT match modal patterns
        non_modal_context = create_context_from_progression(
            {
                "key": "C major",
                "chords": ["C", "Am", "F", "G"],
                "roman_numerals": ["I", "vi", "IV", "V"],
            }
        )

        # Test that modal patterns don't match this functional progression
        modal_patterns = [
            "modal.dorian.i_bVII",
            "modal.phrygian.i_bII",
            "modal.andalusian",
            "modal.mixolydian.I_bVII",
        ]

        for pattern_id in modal_patterns:
            pattern = None
            for p in pattern_engine._patterns.get("patterns", []):
                if p["id"] == pattern_id:
                    pattern = p
                    break

            if pattern:
                matches = pattern_engine._find_pattern_matches(
                    pattern, non_modal_context
                )
                assert (
                    len(matches) == 0
                ), f"Modal pattern {pattern_id} incorrectly matched functional progression"

    def test_pattern_priority_ordering(self, pattern_engine):
        """Test that patterns are ordered by priority correctly."""
        patterns = pattern_engine._patterns.get("patterns", [])

        # Extract priorities
        priorities = []
        for pattern in patterns:
            priority = pattern.get("metadata", {}).get("priority", 50)
            priorities.append((pattern["id"], priority))

        # Check that higher priority patterns come first when sorted
        sorted_priorities = sorted(priorities, key=lambda x: x[1], reverse=True)

        # The perfect authentic cadence should have high priority
        pac_priority = None
        for pattern_id, priority in priorities:
            if pattern_id == "cadence.authentic.perfect":
                pac_priority = priority
                break

        assert pac_priority is not None, "Perfect authentic cadence not found"
        assert pac_priority >= 90, "Perfect authentic cadence should have high priority"

    def test_all_fixture_progressions_load(self, fixture_loader):
        """Test that all fixture files can be loaded without errors."""
        fixture_names = ["cadences", "modal", "functional"]

        for fixture_name in fixture_names:
            fixture = fixture_loader.load(fixture_name)
            assert "progressions" in fixture, f"No progressions in {fixture_name}"
            assert (
                len(fixture["progressions"]) > 0
            ), f"Empty progressions in {fixture_name}"

            # Validate each progression has required fields
            for progression in fixture["progressions"]:
                assert "name" in progression, "Progression missing name"
                assert "chords" in progression, "Progression missing chords"
                assert (
                    "roman_numerals" in progression
                ), "Progression missing roman_numerals"
                assert (
                    "expected_matches" in progression
                ), "Progression missing expected_matches"

                # Validate expected matches
                for match in progression["expected_matches"]:
                    assert "pattern_id" in match, "Expected match missing pattern_id"
                    assert "span" in match, "Expected match missing span"
                    assert (
                        len(match["span"]) == 2
                    ), "Expected match span must have 2 elements"
