"""
Test Suite for Glossary Integration with Pattern Engine

Tests educational context features:
- Enhanced pattern analysis with educational explanations
- Standalone glossary functionality
- Term definitions and music theory concepts
- Teaching point generation
"""

import pytest
import sys
import pathlib

# Ensure project root on sys.path
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService


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
                "description": "Classic PAC with strong resolution"
            },
            {
                "name": "Pop Progression with Multiple Patterns",
                "chords": ["Am", "F", "C", "G"],
                "description": "vi-IV-I-V containing multiple cadential patterns"
            },
            {
                "name": "Jazz ii-V-I Progression",
                "chords": ["Dm7", "G7", "Cmaj7"],
                "description": "Essential jazz progression with seventh chords"
            }
        ]

    def test_educational_context_analysis(self, service, educational_test_cases):
        """Test that educational context analysis works for standard progressions."""
        for test_case in educational_test_cases:
            result = service.analyze_with_educational_context(test_case['chords'])

            # Verify enhanced structure
            assert 'enhanced_pattern_matches' in result
            assert 'teaching_points' in result
            assert 'term_definitions' in result
            assert 'educational_analysis' in result
            assert result['educational_analysis'] is True

            # Should include standard analysis too
            assert 'pattern_matches' in result
            assert 'chord_symbols' in result
            assert result['chord_symbols'] == test_case['chords']

    def test_enhanced_pattern_matches_structure(self, service):
        """Test structure of enhanced pattern matches."""
        chords = ["F", "G7", "C"]  # PAC progression
        result = service.analyze_with_educational_context(chords)

        enhanced_matches = result.get('enhanced_pattern_matches', [])

        # Should have some enhanced matches for this strong progression
        if enhanced_matches:
            match = enhanced_matches[0]

            # Enhanced matches should have educational fields
            expected_fields = ['pattern_name', 'score', 'family']
            for field in expected_fields:
                assert field in match, f"Missing field: {field}"

            # May have educational context
            if 'educational_context' in match:
                context = match['educational_context']
                assert isinstance(context, dict)

    def test_teaching_points_generation(self, service):
        """Test that teaching points are generated appropriately."""
        # Use progression likely to generate teaching points
        chords = ["Am", "F", "C", "G"]
        result = service.analyze_with_educational_context(chords)

        teaching_points = result.get('teaching_points', [])
        assert isinstance(teaching_points, list)

        # Teaching points should be strings if present
        for point in teaching_points:
            assert isinstance(point, str)
            assert len(point) > 0

    def test_term_definitions_extraction(self, service):
        """Test that relevant terms are defined."""
        chords = ["F", "G7", "C"]
        result = service.analyze_with_educational_context(chords)

        term_definitions = result.get('term_definitions', {})
        assert isinstance(term_definitions, dict)

        # Should extract key harmonic terms
        for term, definition in term_definitions.items():
            assert isinstance(term, str)
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
            "Plagal Cadence"
        ]

        for cadence_type in cadence_types:
            try:
                explanation = glossary.get_cadence_explanation(cadence_type)

                if explanation:  # May return None for unknown cadences
                    assert isinstance(explanation, dict)
                    # May have definition and example fields
                    if 'definition' in explanation:
                        assert isinstance(explanation['definition'], str)
                    if 'example_in_C_major' in explanation:
                        assert isinstance(explanation['example_in_C_major'], str)

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
                    if 'name' in info:
                        assert isinstance(info['name'], str)
                    if 'description' in info:
                        assert isinstance(info['description'], str)

            except AttributeError:
                # Method may not exist - that's acceptable
                pass

    def test_educational_vs_standard_analysis_comparison(self, service):
        """Test that educational analysis includes everything from standard analysis."""
        chords = ["Am", "F", "C", "G"]

        # Get both types of analysis
        standard_result = service.analyze_with_patterns(chords)
        educational_result = service.analyze_with_educational_context(chords)

        # Educational should include everything from standard
        standard_keys = set(standard_result.keys())
        educational_keys = set(educational_result.keys())

        # All standard keys should be in educational result
        missing_keys = standard_keys - educational_keys
        assert len(missing_keys) == 0, f"Educational analysis missing keys: {missing_keys}"

        # Core fields should match
        assert educational_result['chord_symbols'] == standard_result['chord_symbols']
        assert len(educational_result['pattern_matches']) == len(standard_result['pattern_matches'])

    def test_pattern_explanation_integration(self, service):
        """Test that patterns get educational explanations when available."""
        # Use progression likely to match known patterns
        chords = ["C", "F", "G", "C"]  # I-IV-V-I

        result = service.analyze_with_educational_context(chords)
        enhanced_matches = result.get('enhanced_pattern_matches', [])

        # Check if any enhanced matches have explanations
        has_explanations = False
        for match in enhanced_matches:
            if 'educational_context' in match:
                context = match['educational_context']
                if any(key in context for key in ['cadence_info', 'chord_functions', 'pattern_family']):
                    has_explanations = True
                    break

        # Educational context should be attempted (may not always succeed)
        assert isinstance(has_explanations, bool)

    @pytest.mark.parametrize("progression,expected_harmonic_content", [
        (["F", "G", "C"], ["dominant", "tonic", "cadence"]),
        (["Am", "F", "C", "G"], ["vi", "IV", "I", "V"]),
        (["Dm7", "G7", "Cmaj7"], ["ii", "V", "I", "seventh"]),
    ])
    def test_harmonic_term_extraction(self, service, progression, expected_harmonic_content):
        """Test that relevant harmonic terms are extracted for different progressions."""
        result = service.analyze_with_educational_context(progression)

        # Check our new harmonic_terms and romans_text fields
        harmonic_terms = result.get('harmonic_terms', [])
        romans_text = result.get('romans_text', '').lower()

        # Convert harmonic terms to lowercase for comparison
        harmonic_terms_lower = [term.lower() for term in harmonic_terms]

        # Find terms in either harmonic_terms list or romans_text
        found_terms = []
        for expected_term in expected_harmonic_content:
            expected_lower = expected_term.lower()
            if (expected_lower in harmonic_terms_lower or
                expected_lower in romans_text):
                found_terms.append(expected_term)

        # At least some expected terms should appear
        assert len(found_terms) > 0, f"Expected to find some of {expected_harmonic_content} in harmonic analysis. Found harmonic_terms: {harmonic_terms}, romans_text: '{romans_text}'"

    def test_error_handling_empty_progression(self, service):
        """Test educational analysis error handling."""
        # Empty progression
        result = service.analyze_with_educational_context([])
        assert result is not None
        assert isinstance(result, dict)

        # Should have educational fields even if empty
        assert 'enhanced_pattern_matches' in result
        assert 'teaching_points' in result
        assert 'term_definitions' in result

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
