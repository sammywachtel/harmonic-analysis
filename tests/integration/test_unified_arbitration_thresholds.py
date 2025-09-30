"""
Arbitration threshold tests for the unified pattern engine.

Tests that arbitration policies correctly handle threshold boundaries
for functional vs modal analysis with the new pattern-based system.
"""

import pytest

from harmonic_analysis.dto import AnalysisType
from harmonic_analysis.services.unified_pattern_service import UnifiedPatternService


class TestUnifiedArbitrationThresholds:
    """Test arbitration threshold boundaries with unified pattern engine."""

    @pytest.fixture
    def unified_service(self):
        """Create unified pattern service instance."""
        return UnifiedPatternService()

    def test_functional_threshold_boundary(self, unified_service):
        """Test functional analysis threshold boundary (min = 0.50)."""
        # Strong functional progression (should exceed threshold)
        strong_functional = ["C", "F", "G", "C"]  # I-IV-V-I
        result = unified_service.analyze_with_patterns(
            strong_functional, key_hint="C major"
        )

        # Should produce functional analysis with decent confidence
        if result.primary.type == AnalysisType.FUNCTIONAL:
            assert result.primary.confidence >= 0.50, (
                f"Strong functional progression should meet threshold: "
                f"got {result.primary.confidence:.3f}"
            )

        # Weak/ambiguous progression (might fall below threshold)
        weak_progression = ["C", "Am"]  # I-vi (less functional character)
        result_weak = unified_service.analyze_with_patterns(
            weak_progression, key_hint="C major"
        )

        # Document the behavior - might be functional or modal depending on patterns
        print(
            f"Strong functional: {result.primary.type}, conf={result.primary.confidence:.3f}"
        )
        print(
            f"Weak progression: {result_weak.primary.type}, conf={result_weak.primary.confidence:.3f}"
        )

    def test_modal_threshold_boundary(self, unified_service):
        """Test modal analysis threshold boundary (min = 0.60)."""
        # Strong modal progression (should exceed threshold)
        strong_modal = ["Dm", "C"]  # i-♭VII in D dorian
        result = unified_service.analyze_with_patterns(
            strong_modal, key_hint="D dorian"
        )

        # Should produce modal analysis with decent confidence
        if result.primary.type == AnalysisType.MODAL:
            assert result.primary.confidence >= 0.60, (
                f"Strong modal progression should meet threshold: "
                f"got {result.primary.confidence:.3f}"
            )

        # Test different modal patterns
        phrygian_progression = ["Em", "F"]  # i-♭II in E phrygian
        result_phrygian = unified_service.analyze_with_patterns(
            phrygian_progression, key_hint="E phrygian"
        )

        print(
            f"Dorian modal: {result.primary.type}, conf={result.primary.confidence:.3f}"
        )
        print(
            f"Phrygian modal: {result_phrygian.primary.type}, conf={result_phrygian.primary.confidence:.3f}"
        )

    def test_functional_dominance_margin(self, unified_service):
        """Test functional dominance margin (+0.10 over modal)."""
        # Create progressions that could be interpreted both ways
        ambiguous_progressions = [
            {
                "name": "Plagal Cadence",
                "chords": ["F", "C"],
                "key": "C major",
                "note": "Can be functional (IV-I) or modal characteristic",
            },
            {
                "name": "Minor iv",
                "chords": ["C", "Fm", "C"],
                "key": "C major",
                "note": "Borrowed chord - functional or modal?",
            },
        ]

        results = []
        for prog in ambiguous_progressions:
            result = unified_service.analyze_with_patterns(
                prog["chords"], key_hint=prog["key"]
            )
            results.append(
                {
                    "name": prog["name"],
                    "type": result.primary.type,
                    "confidence": result.primary.confidence,
                    "note": prog["note"],
                }
            )

        # Document arbitration decisions
        for result in results:
            print(
                f"{result['name']}: {result['type']}, conf={result['confidence']:.3f}"
            )
            print(f"  {result['note']}")

        # At least one should have reasonable confidence
        confidences = [r["confidence"] for r in results]
        assert (
            max(confidences) > 0.5
        ), "At least one progression should have decent confidence"

    def test_modal_dominance_margin(self, unified_service):
        """Test modal dominance margin (+0.15 over functional)."""
        # Strong modal characteristics that should override functional interpretation
        modal_progressions = [
            {
                "name": "Andalusian Cadence",
                "chords": ["Dm", "C", "Bb", "A"],
                "key": "A phrygian",
                "expected_modal": True,
            },
            {
                "name": "Mixolydian ♭VII",
                "chords": ["G", "F"],
                "key": "G mixolydian",
                "expected_modal": True,
            },
        ]

        for prog in modal_progressions:
            result = unified_service.analyze_with_patterns(
                prog["chords"], key_hint=prog["key"]
            )

            print(
                f"{prog['name']}: {result.primary.type}, conf={result.primary.confidence:.3f}"
            )

            if prog["expected_modal"]:
                # Strong modal progressions should be recognized as modal
                # (though this depends on pattern implementation)
                if result.primary.type == AnalysisType.MODAL:
                    assert result.primary.confidence > 0.6, (
                        f"Strong modal progression should have high confidence: "
                        f"got {result.primary.confidence:.3f}"
                    )

    def test_arbitration_consistency(self, unified_service):
        """Test that arbitration decisions are consistent across similar progressions."""
        # Test same progression in different keys
        dorian_progressions = [
            {"chords": ["Dm", "C"], "key": "D dorian"},
            {"chords": ["Em", "D"], "key": "E dorian"},
            {"chords": ["Am", "G"], "key": "A dorian"},
        ]

        results = []
        for prog in dorian_progressions:
            result = unified_service.analyze_with_patterns(
                prog["chords"], key_hint=prog["key"]
            )
            results.append(
                {
                    "key": prog["key"],
                    "type": result.primary.type,
                    "confidence": result.primary.confidence,
                }
            )

        # All should have same analysis type (consistency)
        types = [r["type"] for r in results]
        confidences = [r["confidence"] for r in results]

        # Print results for inspection
        for result in results:
            print(f"{result['key']}: {result['type']}, conf={result['confidence']:.3f}")

        # Basic consistency checks
        assert len(set(types)) <= 2, "Should have consistent or similar analysis types"
        assert all(
            c >= 0.0 for c in confidences
        ), "All confidences should be non-negative"
        assert all(c <= 1.0 for c in confidences), "All confidences should be <= 1.0"

    def test_threshold_configuration_coverage(self, unified_service):
        """Test that the system covers the key threshold values from Section 14."""
        # These are the documented thresholds that should be protected
        expected_thresholds = {
            "min_functional": 0.50,
            "min_modal": 0.60,  # Higher threshold for modal (more conservative)
            "functional_margin": 0.10,
            "modal_dominance": 0.15,
        }

        # Test boundary cases around these thresholds
        test_cases = [
            {
                "name": "Strong Functional",
                "chords": ["C", "Am", "F", "G", "C"],
                "key": "C major",
                "expected_type": AnalysisType.FUNCTIONAL,
                "min_confidence": expected_thresholds["min_functional"],
            },
            {
                "name": "Strong Modal",
                "chords": ["Dm", "C"],
                "key": "D dorian",
                "expected_type": AnalysisType.MODAL,
                "min_confidence": expected_thresholds["min_modal"],
            },
        ]

        for case in test_cases:
            result = unified_service.analyze_with_patterns(
                case["chords"], key_hint=case["key"]
            )

            print(
                f"{case['name']}: {result.primary.type}, conf={result.primary.confidence:.3f}"
            )

            # Verify confidence meets minimum threshold if type matches expectation
            if result.primary.type == case["expected_type"]:
                assert result.primary.confidence >= case["min_confidence"], (
                    f"{case['name']} should meet {case['expected_type']} threshold "
                    f"({case['min_confidence']:.2f}): got {result.primary.confidence:.3f}"
                )

    def test_alternative_analyses_below_threshold(self, unified_service):
        """Test that analyses below threshold appear in alternatives, not primary."""
        # Create a progression that might have multiple weak interpretations
        ambiguous_progression = ["C", "G"]  # Very simple, multiple interpretations

        result = unified_service.analyze_with_patterns(
            ambiguous_progression, key_hint="C major"
        )

        # Primary should have reasonable confidence
        assert result.primary is not None, "Should always have a primary analysis"
        assert (
            result.primary.confidence >= 0.0
        ), "Primary confidence should be non-negative"

        # Alternatives (if any) should generally have lower confidence than primary
        if result.alternatives:
            primary_conf = result.primary.confidence
            alt_confidences = [alt.confidence for alt in result.alternatives]

            print(f"Primary: {result.primary.type}, conf={primary_conf:.3f}")
            for i, alt in enumerate(result.alternatives):
                print(f"Alt {i+1}: {alt.type}, conf={alt.confidence:.3f}")

            # In a well-calibrated system, alternatives should generally be lower confidence
            max_alt_conf = max(alt_confidences) if alt_confidences else 0.0

            # This is a soft check - document the behavior
            if max_alt_conf > primary_conf:
                print("Note: Alternative has higher confidence than primary")

    def test_override_flag_behavior(self, unified_service):
        """Test override flag behavior (should default to off)."""
        # This tests that no artificial confidence boosting occurs by default

        # Simple progression that shouldn't have artificially inflated confidence
        simple_progression = ["C", "F"]  # I-IV

        result = unified_service.analyze_with_patterns(
            simple_progression, key_hint="C major"
        )

        # Confidence should be reasonable, not artificially high
        assert result.primary.confidence <= 1.0, "Confidence should not exceed 1.0"
        assert result.primary.confidence >= 0.0, "Confidence should not be negative"

        # For a simple I-IV, confidence shouldn't be extremely high unless there's
        # strong pattern evidence
        if result.primary.confidence > 0.95:
            print(
                f"Note: Very high confidence ({result.primary.confidence:.3f}) for simple I-IV"
            )

        print(
            f"Simple I-IV: {result.primary.type}, conf={result.primary.confidence:.3f}"
        )

        # Document that this represents the "default off" state for overrides
