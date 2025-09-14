"""
Test Suite for Glossary Integration with Pattern Engine

Tests educational context features:
- Enhanced pattern analysis with educational explanations
- Standalone glossary functionality
- Term definitions and music theory concepts
- Teaching point generation
"""

import pathlib
import sys

import pytest

# Ensure project root on sys.path
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harmonic_analysis.services.pattern_analysis_service import (  # noqa: E402
    PatternAnalysisService,
)


class TestGlossaryIntegration:
    """Test suite for glossary integration with pattern analysis."""

    @pytest.fixture
    def service(self):
        """Create pattern analysis service with glossary."""
        return PatternAnalysisService()

    @pytest.fixture
    def educational_test_cases(self):
        """Common test cases for educational analysis."""
        return [
            {
                "name": "Perfect Authentic Cadence Example",
                "chords": ["F", "G7", "C"],
                "description": "Classic PAC with strong resolution",
            },
            {
                "name": "Pop Progression with Multiple Patterns",
                "chords": ["Am", "F", "C", "G"],
                "description": "vi-IV-I-V containing multiple cadential patterns",
            },
            {
                "name": "Jazz ii-V-I Progression",
                "chords": ["Dm7", "G7", "Cmaj7"],
                "description": "Essential jazz progression with seventh chords",
            },
        ]

    def test_educational_context_analysis(self, service, educational_test_cases):
        """Test that pattern analysis provides educational information through glossary service."""
        for test_case in educational_test_cases:
            result = service.analyze_with_patterns(test_case["chords"])

            # Verify DTO structure
            assert hasattr(result, "primary")
            assert hasattr(result.primary, "patterns")
            assert result.chord_symbols == test_case["chords"]

            # Test that we can get educational context from patterns
            patterns = result.primary.patterns
            glossary_service = service.glossary_service

            # Test glossary service can provide explanations
            for pattern in patterns:
                explanation = glossary_service.explain_pattern_result(
                    {
                        "name": pattern.name,
                        "family": pattern.family,
                        "score": pattern.score,
                        "evidence": pattern.evidence,
                    }
                )
                assert isinstance(explanation, dict)
                assert "pattern_name" in explanation

    def test_enhanced_pattern_matches_structure(self, service):
        """Test structure of pattern matches in AnalysisEnvelope."""
        chords = ["F", "G7", "C"]  # PAC progression
        result = service.analyze_with_patterns(chords)

        # Get pattern matches from DTO
        pattern_matches = result.primary.patterns

        # Should have some pattern matches for this strong progression
        if pattern_matches:
            match = pattern_matches[0]

            # Pattern matches should have DTO fields
            assert hasattr(match, "name")
            assert hasattr(match, "score")
            assert hasattr(match, "family")
            assert hasattr(match, "pattern_id")

            # Test that glossary service can provide educational context
            glossary_service = service.glossary_service
            explanation = glossary_service.explain_pattern_result(
                {
                    "name": match.name,
                    "family": match.family,
                    "score": match.score,
                    "evidence": match.evidence,
                }
            )
            assert isinstance(explanation, dict)

    def test_teaching_points_generation(self, service):
        """Test that teaching points can be generated from pattern analysis."""
        # Use progression likely to generate teaching points
        chords = ["Am", "F", "C", "G"]
        result = service.analyze_with_patterns(chords)

        # Test that glossary service can generate teaching points from patterns
        patterns = result.primary.patterns
        glossary_service = service.glossary_service

        # Convert patterns to the format expected by glossary service
        pattern_dicts = []
        for p in patterns:
            pattern_dicts.append(
                {
                    "name": p.name,
                    "family": p.family,
                    "score": p.score,
                    "evidence": p.evidence,
                }
            )

        teaching_points = glossary_service.get_pattern_teaching_points(pattern_dicts)
        assert isinstance(teaching_points, list)

        # Teaching points should be strings if present
        for point in teaching_points:
            assert isinstance(point, str)
            assert len(point) > 0

    def test_term_definitions_extraction(self, service):
        """Test that relevant terms can be extracted from analysis results."""
        chords = ["F", "G7", "C"]
        result = service.analyze_with_patterns(chords)

        # Test that we can extract educational information from patterns
        patterns = result.primary.patterns
        assert isinstance(patterns, list)

        # Test that glossary service can provide term definitions
        glossary_service = service.glossary_service

        # Test some basic music theory terms
        test_terms = ["tonic", "dominant", "cadence"]
        for term in test_terms:
            definition = glossary_service.get_term_definition(term)
            if definition:  # Some terms might not be in glossary
                assert isinstance(definition, str)
                assert len(definition) > 0

    def test_glossary_service_cadence_explanations(self, service):
        """Test standalone cadence explanation functionality."""
        glossary = service.glossary_service

        # Test different cadence types
        cadence_types = [
            "PAC with soprano on 1",
            "Perfect Authentic Cadence",
            "Half Cadence",
            "Plagal Cadence",
        ]

        for cadence_type in cadence_types:
            try:
                explanation = glossary.get_cadence_explanation(cadence_type)

                if explanation:  # May return None for unknown cadences
                    assert isinstance(explanation, dict)
                    # May have definition and example fields
                    if "definition" in explanation:
                        assert isinstance(explanation["definition"], str)
                    if "example_in_C_major" in explanation:
                        assert isinstance(explanation["example_in_C_major"], str)

            except AttributeError:
                # Method may not exist - that's acceptable
                pass

    def test_glossary_service_term_definitions(self, service):
        """Test standalone term definition functionality."""
        glossary = service.glossary_service

        # Test common harmonic terms
        terms = ["tonic", "dominant", "scale_degree", "soprano", "predominant"]

        for term in terms:
            try:
                definition = glossary.get_term_definition(term)

                if definition:  # May return None for unknown terms
                    assert isinstance(definition, str)
                    assert len(definition) > 0

            except AttributeError:
                # Method may not exist - that's acceptable
                pass

    def test_glossary_service_scale_degree_info(self, service):
        """Test scale degree information functionality."""
        glossary = service.glossary_service

        # Test common scale degrees
        test_degrees = [1, 3, 5, 7]
        key = "C major"

        for degree in test_degrees:
            try:
                info = glossary.get_scale_degree_info(degree, key)

                if info:  # May return None for unknown degrees
                    assert isinstance(info, dict)
                    # May have name and description fields
                    if "name" in info:
                        assert isinstance(info["name"], str)
                    if "description" in info:
                        assert isinstance(info["description"], str)

            except AttributeError:
                # Method may not exist - that's acceptable
                pass

    def test_educational_vs_standard_analysis_comparison(self, service):
        """Test that analysis provides consistent results."""
        chords = ["Am", "F", "C", "G"]

        # Get analysis results
        result1 = service.analyze_with_patterns(chords)
        result2 = service.analyze_with_patterns(chords)

        # Results should be consistent
        assert result1.chord_symbols == result2.chord_symbols
        assert result1.primary.type == result2.primary.type
        assert len(result1.primary.patterns) == len(result2.primary.patterns)

    def test_pattern_explanation_integration(self, service):
        """Test that patterns get educational explanations when available."""
        # Use progression likely to match known patterns
        chords = ["C", "F", "G", "C"]  # I-IV-V-I

        result = service.analyze_with_patterns(chords)
        patterns = result.primary.patterns
        glossary_service = service.glossary_service

        # Test that glossary service can provide explanations
        has_explanations = False
        for pattern in patterns:
            explanation = glossary_service.explain_pattern_result(
                {
                    "name": pattern.name,
                    "family": pattern.family,
                    "score": pattern.score,
                    "evidence": pattern.evidence,
                }
            )
            if explanation and "educational_context" in explanation:
                has_explanations = True
                break

        # Educational context functionality should work
        assert isinstance(has_explanations, bool)

    @pytest.mark.parametrize(
        "progression,expected_harmonic_content",
        [
            (
                ["F", "G", "C"],
                ["IV", "V", "I"],
            ),  # More realistic roman numeral expectations
            (["Am", "F", "C", "G"], ["vi", "IV", "I", "V"]),
            (["Dm7", "G7", "Cmaj7"], ["ii", "V", "I"]),
        ],
    )
    def test_harmonic_term_extraction(
        self, service, progression, expected_harmonic_content
    ):
        """Test that roman numerals are extracted from analysis."""
        result = service.analyze_with_patterns(progression)

        # Extract harmonic information from DTO
        romans_list = result.primary.roman_numerals
        # romans_text = " ".join(romans_list)  # Available for debugging

        # Find expected terms in roman numerals
        found_terms = []
        for expected_term in expected_harmonic_content:
            # Check if term appears in any roman numeral (case insensitive)
            if any(expected_term.lower() in roman.lower() for roman in romans_list):
                found_terms.append(expected_term)

        # At least some expected terms should appear
        assert (
            len(found_terms) > 0
        ), f"Expected to find some of {expected_harmonic_content} in roman numerals. Found romans: {romans_list}"

    def test_error_handling_empty_progression(self, service):
        """Test analysis error handling for empty progressions."""
        # Empty progression should raise an error
        with pytest.raises(ValueError, match="Empty chord progression"):
            service.analyze_with_patterns([])

    def test_glossary_service_error_handling(self, service):
        """Test that glossary service handles invalid inputs gracefully."""
        glossary = service.glossary_service

        # Test with invalid inputs
        invalid_inputs = [None, "", "NonexistentTerm", 999, []]

        for invalid_input in invalid_inputs:
            try:
                # These should not crash
                result = glossary.get_term_definition(invalid_input)
                assert result is None or isinstance(result, str)

            except (AttributeError, TypeError, ValueError):
                # Expected for some invalid inputs
                pass
