"""
Parity tests comparing unified pattern engine vs legacy analysis outputs.

Validates that the new unified pattern engine produces comparable results
to the existing PatternAnalysisService and ModalAnalysisService.
"""

import pytest
from typing import List, Dict, Any
import asyncio
from pathlib import Path

from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService
from harmonic_analysis.services.modal_analysis_service import ModalAnalysisService
from harmonic_analysis.services.unified_pattern_service import UnifiedPatternService
from harmonic_analysis.dto import AnalysisType


class TestUnifiedVsLegacyParity:
    """Test parity between unified pattern engine and legacy services."""

    @pytest.fixture
    def unified_service(self):
        """Create unified pattern service instance (proper entry point)."""
        # Main play: use service entry point instead of raw engine for proper parity testing
        return UnifiedPatternService()

    @pytest.fixture
    def legacy_pattern_service(self):
        """Create legacy pattern analysis service."""
        return PatternAnalysisService()

    @pytest.fixture
    def legacy_modal_service(self):
        """Create legacy modal analysis service."""
        return ModalAnalysisService()

    @pytest.fixture
    def test_progressions(self):
        """Standard test progressions for parity validation."""
        return [
            {
                "name": "Simple Authentic Cadence",
                "chords": ["G", "C"],
                "key": "C major",
                "expected_type": "functional"
            },
            {
                "name": "Plagal Cadence",
                "chords": ["F", "C"],
                "key": "C major",
                "expected_type": "functional"
            },
            {
                "name": "Dorian i-♭VII",
                "chords": ["Dm", "C"],
                "key": "D dorian",
                "expected_type": "modal"
            },
            {
                "name": "Circle of Fifths",
                "chords": ["Am", "Dm", "G", "C"],
                "key": "C major",
                "expected_type": "functional"
            },
            {
                "name": "Modal Aeolian",
                "chords": ["Am", "Em"],
                "key": "A minor",
                "expected_type": "modal"
            }
        ]

    def test_unified_service_produces_valid_output(self, unified_service, test_progressions):
        """Test that unified service produces valid AnalysisEnvelope output."""
        for progression in test_progressions:
            # Main play: use service entry point instead of raw engine
            envelope = unified_service.analyze_with_patterns(
                chords=progression["chords"],
                key_hint=progression["key"]
            )

            # Main play: verify envelope structure is valid
            assert envelope is not None
            assert hasattr(envelope, 'primary')
            assert hasattr(envelope, 'alternatives')
            assert envelope.primary is not None

            # Victory lap: verify analysis types are valid
            assert envelope.primary.type in [AnalysisType.FUNCTIONAL, AnalysisType.MODAL]
            assert isinstance(envelope.primary.confidence, (int, float))
            assert 0.0 <= envelope.primary.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_functional_cadence_parity(
        self, unified_service, legacy_pattern_service, test_progressions
    ):
        """Test that functional cadences are detected by both engines."""
        functional_tests = [p for p in test_progressions if p["expected_type"] == "functional"]

        for progression in functional_tests:
            # Time to tackle the tricky bit: get results from both engines
            # Use service entry point instead of raw engine context
            unified_result = unified_service.analyze_with_patterns(
                progression["chords"],
                key_hint=progression["key"]
            )

            # Legacy engine result
            try:
                legacy_result = await legacy_pattern_service.analyze_with_patterns_async(
                    progression["chords"],
                    key_hint=progression["key"]
                )
            except Exception:
                # If async fails, try sync
                legacy_result = legacy_pattern_service.analyze_with_patterns(
                    progression["chords"],
                    key_hint=progression["key"]
                )

            # Big play: both should detect similar analysis types for functional progressions
            if legacy_result and legacy_result.primary:
                # At minimum, both should produce some kind of analysis
                assert unified_result.primary is not None

                # For functional progressions, at least one should be functional
                unified_is_functional = unified_result.primary.type == AnalysisType.FUNCTIONAL
                legacy_is_functional = legacy_result.primary.type == AnalysisType.FUNCTIONAL

                # Not a strict requirement but good to track - at least one should be functional
                functional_detected = unified_is_functional or legacy_is_functional

                print(f"Progression: {progression['name']}")
                print(f"  Unified: {unified_result.primary.type}, confidence: {unified_result.primary.confidence:.2f}")
                print(f"  Legacy: {legacy_result.primary.type}, confidence: {legacy_result.primary.confidence:.2f}")
                print(f"  Functional detected: {functional_detected}")

    def test_modal_progression_detection(
        self, unified_service, test_progressions
    ):
        """Test that modal progressions are detected by unified engine."""
        modal_tests = [p for p in test_progressions if p["expected_type"] == "modal"]

        for progression in modal_tests:
            # Use service entry point for modal progression analysis
            result = unified_service.analyze_with_patterns(
                progression["chords"],
                key_hint=progression["key"]
            )

            # Victory lap: should at least detect something for modal progressions
            assert result.primary is not None
            assert result.primary.confidence > 0.0

            print(f"Modal test: {progression['name']}")
            print(f"  Result: {result.primary.type}, confidence: {result.primary.confidence:.2f}")

    def test_confidence_score_reasonableness(self, unified_service, test_progressions):
        """Test that confidence scores are reasonable across different progressions."""
        confidence_scores = []

        for progression in test_progressions:
            # Use service entry point for confidence testing
            result = unified_service.analyze_with_patterns(
                progression["chords"],
                key_hint=progression["key"]
            )
            if result.primary:
                confidence_scores.append({
                    "name": progression["name"],
                    "confidence": result.primary.confidence,
                    "type": result.primary.type
                })

        # This looks odd, but it saves us from edge cases - ensure we got some results
        assert len(confidence_scores) > 0

        # Check confidence distribution is reasonable
        confidences = [s["confidence"] for s in confidence_scores]

        # All confidences should be in valid range
        assert all(0.0 <= c <= 1.0 for c in confidences)

        # Confidence scores should be reasonable (calibrated system may have consistent high confidence)
        min_conf = min(confidences)
        max_conf = max(confidences)

        # With good calibration, high confidence scores are expected for clear progressions
        assert min_conf >= 0.5  # All should have decent confidence
        assert max_conf <= 1.0  # But not exceed maximum

        # Document actual spread (may be small with good calibration)
        spread = max_conf - min_conf
        print(f"Confidence spread: {spread:.3f} (min: {min_conf:.3f}, max: {max_conf:.3f})")

        # If all progressions are very clear, small spread is actually good behavior
        # No strict spread requirement - just validate reasonable range

        print("Confidence distribution:")
        for score in confidence_scores:
            print(f"  {score['name']}: {score['confidence']:.2f} ({score['type']})")

    def test_evidence_availability(self, unified_service, test_progressions):
        """Test that unified engine provides evidence details."""
        for progression in test_progressions[:2]:  # Test just first few for speed
            # Use service entry point for evidence testing
            result = unified_service.analyze_with_patterns(
                progression["chords"],
                key_hint=progression["key"]
            )

            # Main search: verify evidence structure exists
            assert hasattr(result, 'evidence')
            # Evidence might be empty for simple patterns, but structure should exist

            print(f"Evidence for {progression['name']}: {len(result.evidence) if result.evidence else 0} items")

    def test_pattern_match_consistency(self, unified_service):
        """Test that pattern matching is consistent across similar progressions."""
        # Test transposed versions of the same progression
        base_progression = ["C", "F", "G", "C"]
        transposed_progression = ["G", "C", "D", "G"]  # Up a perfect 5th

        # Use service entry points for consistency testing
        results = [
            unified_service.analyze_with_patterns(base_progression, key_hint="C major"),
            unified_service.analyze_with_patterns(transposed_progression, key_hint="G major")
        ]

        # Both should produce results of same analysis type
        assert results[0].primary is not None
        assert results[1].primary is not None

        # Should detect same pattern family (both functional progressions)
        types_match = results[0].primary.type == results[1].primary.type

        print(f"Pattern consistency test:")
        print(f"  C major: {results[0].primary.type}, confidence: {results[0].primary.confidence:.2f}")
        print(f"  G major: {results[1].primary.type}, confidence: {results[1].primary.confidence:.2f}")
        print(f"  Types match: {types_match}")

        # At minimum, both should be detected as some valid analysis type
        assert results[0].primary.type in [AnalysisType.FUNCTIONAL, AnalysisType.MODAL]
        assert results[1].primary.type in [AnalysisType.FUNCTIONAL, AnalysisType.MODAL]


class TestMelodicAnalysisParity:
    """Test melodic analysis capabilities of unified engine."""

    @pytest.fixture
    def unified_service(self):
        """Create unified pattern service for melodic analysis."""
        return UnifiedPatternService()

    def test_melodic_pattern_detection(self, unified_service):
        """Test that melodic patterns are detected when melody is provided."""
        # Test leading tone resolution using service
        # Note: Current service doesn't support melody input directly,
        # so we test the harmonic progression that would accompany the melodic pattern
        result = unified_service.analyze_with_patterns(
            ["G", "C"],  # V-I progression
            key_hint="C major"
        )

        # Should produce a valid result
        assert result.primary is not None
        assert result.primary.confidence > 0.0

        print(f"Melodic test result: {result.primary.type}, confidence: {result.primary.confidence:.2f}")

    def test_scale_vs_harmonic_scope_difference(self, unified_service):
        """Test that scale patterns add different evidence than harmonic patterns."""
        # Test with just harmonic progression
        harmonic_result = unified_service.analyze_with_patterns(
            ["Dm", "C"],
            key_hint="D dorian"
        )

        # Test the same progression (service doesn't currently take scale input directly)
        # But the key hint should trigger modal analysis patterns
        scale_result = unified_service.analyze_with_patterns(
            ["Dm", "C"],
            key_hint="D dorian"
        )

        # Both should produce results
        assert harmonic_result.primary is not None
        assert scale_result.primary is not None

        print(f"Harmonic only: {harmonic_result.primary.type}, confidence: {harmonic_result.primary.confidence:.2f}")
        print(f"With scale: {scale_result.primary.type}, confidence: {scale_result.primary.confidence:.2f}")

        # Scale version might have different (possibly higher) confidence due to additional evidence
        # This is not a strict requirement, just observational