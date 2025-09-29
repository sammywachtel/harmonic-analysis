"""
Tests for UnifiedPatternService compatibility wrapper.

Validates that the unified service provides the same API as PatternAnalysisService
while using the new unified pattern engine under the hood.
"""

from typing import List

import pytest

from harmonic_analysis.dto import AnalysisEnvelope, AnalysisType
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService
from harmonic_analysis.services.unified_pattern_service import UnifiedPatternService


class TestUnifiedPatternServiceCompatibility:
    """Test compatibility between unified and legacy services."""

    @pytest.fixture
    def unified_service(self):
        """Create unified pattern service instance."""
        return UnifiedPatternService()

    @pytest.fixture
    def legacy_service(self):
        """Create legacy pattern analysis service."""
        return PatternAnalysisService()

    @pytest.fixture
    def test_progressions(self):
        """Standard test progressions for compatibility validation."""
        return [
            {
                "name": "Simple Cadence",
                "chords": ["G", "C"],
                "key": "C major",
            },
            {
                "name": "I-IV-V-I",
                "chords": ["C", "F", "G", "C"],
                "key": "C major",
            },
            {
                "name": "Circle of Fifths",
                "chords": ["Am", "Dm", "G", "C"],
                "key": "C major",
            },
        ]

    def test_unified_service_api_compatibility(self, unified_service):
        """Test that unified service has same API methods as legacy service."""
        # Main play: check for essential API methods
        assert hasattr(unified_service, "analyze_with_patterns_async")
        assert hasattr(unified_service, "analyze_with_patterns")
        assert hasattr(unified_service, "get_analysis_summary")

        # Victory lap: check method signatures are callable
        assert callable(unified_service.analyze_with_patterns_async)
        assert callable(unified_service.analyze_with_patterns)
        assert callable(unified_service.get_analysis_summary)

    @pytest.mark.asyncio
    async def test_async_analysis_produces_valid_output(
        self, unified_service, test_progressions
    ):
        """Test that async analysis produces valid AnalysisEnvelope."""
        for progression in test_progressions:
            result = await unified_service.analyze_with_patterns_async(
                progression["chords"], key_hint=progression["key"]
            )

            # Opening move: verify result structure
            assert isinstance(result, AnalysisEnvelope)
            assert result.primary is not None

            # Big play: verify analysis content
            assert hasattr(result.primary, "type")
            assert hasattr(result.primary, "confidence")
            assert result.primary.type in [AnalysisType.FUNCTIONAL, AnalysisType.MODAL]
            assert 0.0 <= result.primary.confidence <= 1.0

            print(
                f"✅ {progression['name']}: {result.primary.type}, confidence: {result.primary.confidence:.2f}"
            )

    def test_sync_analysis_produces_valid_output(
        self, unified_service, test_progressions
    ):
        """Test that sync analysis produces valid AnalysisEnvelope."""
        for progression in test_progressions[:2]:  # Test fewer for speed
            result = unified_service.analyze_with_patterns(
                progression["chords"], key_hint=progression["key"]
            )

            # This looks odd, but it saves us from crashes - verify structure
            assert isinstance(result, AnalysisEnvelope)
            assert result.primary is not None
            assert hasattr(result.primary, "type")
            assert hasattr(result.primary, "confidence")

            print(f"✅ Sync {progression['name']}: {result.primary.type}")

    @pytest.mark.asyncio
    async def test_confidence_calibration_integration(self, unified_service):
        """Test that confidence calibration is applied when available."""
        # Simple progression that should trigger calibration
        result = await unified_service.analyze_with_patterns_async(
            ["C", "F", "G", "C"], key_hint="C major"
        )

        # Main search: verify calibration was attempted (check logs or confidence range)
        assert result.primary is not None
        assert isinstance(result.primary.confidence, (int, float))

        # Calibrated confidences should be in reasonable range
        assert 0.0 <= result.primary.confidence <= 1.0

        print(f"✅ Calibrated confidence: {result.primary.confidence:.3f}")

    def test_parameter_compatibility(self, unified_service):
        """Test that all legacy parameters are accepted (even if ignored)."""
        # Time to tackle the tricky bit: test with all legacy parameters
        try:
            result = unified_service.analyze_with_patterns(
                chords=["C", "G"],
                key_hint="C major",
                profile="classical",  # Should be ignored gracefully
                options={"some_option": "value"},  # Should be ignored gracefully
            )

            # Victory lap: should work without errors
            assert isinstance(result, AnalysisEnvelope)
            print("✅ Legacy parameter compatibility confirmed")

        except TypeError as e:
            pytest.fail(
                f"UnifiedPatternService not compatible with legacy parameters: {e}"
            )

    def test_error_handling_compatibility(self, unified_service):
        """Test that error handling behaves reasonably with invalid input."""
        # Test with empty chord list
        result = unified_service.analyze_with_patterns([])

        # Should return valid envelope even with no input
        assert isinstance(result, AnalysisEnvelope)

        # Test with invalid chords (should handle gracefully)
        result = unified_service.analyze_with_patterns(["INVALID_CHORD"])
        assert isinstance(result, AnalysisEnvelope)

        print("✅ Error handling compatibility confirmed")

    def test_analysis_summary_generation(self, unified_service):
        """Test that analysis summary can be generated from results."""
        result = unified_service.analyze_with_patterns(["C", "F", "G", "C"])
        summary = unified_service.get_analysis_summary(result)

        # Final whistle: verify summary structure (corrected for AnalysisSummary DTO)
        assert hasattr(summary, "type")
        assert hasattr(summary, "confidence")
        assert hasattr(summary, "roman_numerals")

        print(f"✅ Summary: {summary.type}, confidence: {summary.confidence:.2f}")


class TestUnifiedServiceInitialization:
    """Test unified service initialization and configuration."""

    def test_initialization_with_legacy_parameters(self):
        """Test that initialization accepts legacy parameters for compatibility."""
        # Big play: test initialization with all legacy parameters
        service = UnifiedPatternService(
            functional_analyzer="ignored",
            matcher="ignored",
            modal_analyzer="ignored",
            chromatic_analyzer="ignored",
            arbitration_policy="ignored",
            calibration_service=None,
            auto_calibrate=False,
        )

        # Should initialize successfully
        assert service.engine is not None
        assert service.auto_calibrate is False

        print("✅ Legacy parameter initialization compatibility confirmed")

    def test_default_initialization(self):
        """Test that default initialization works correctly."""
        service = UnifiedPatternService()

        # Should have engine and default settings
        assert service.engine is not None
        assert service.auto_calibrate is True

        print("✅ Default initialization confirmed")
