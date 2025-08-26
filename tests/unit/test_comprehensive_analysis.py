"""
Unit tests for comprehensive analysis engine.
"""

import pytest

from harmonic_analysis.services.comprehensive_analysis import (
    ComprehensiveAnalysisEngine,
    ComprehensiveAnalysisResult,
)


class TestComprehensiveAnalysisEngine:
    """Test comprehensive analysis engine."""

    @pytest.fixture
    def analyzer(self):
        """Fixture providing analysis engine."""
        return ComprehensiveAnalysisEngine()

    @pytest.mark.asyncio
    async def test_analyze_simple_functional_progression(self, analyzer):
        """Test analysis of simple functional progression."""
        result = await analyzer.analyze_comprehensively("C F G C")

        assert isinstance(result, ComprehensiveAnalysisResult)
        assert result.functional is not None
        assert result.primary_approach == "functional"
        assert result.confidence > 0.0
        assert len(result.functional.chords) == 4

    @pytest.mark.asyncio
    async def test_analyze_modal_progression(self, analyzer):
        """Test analysis of modal progression."""
        # Mixolydian progression with bVII-I
        result = await analyzer.analyze_comprehensively("G F C G")

        assert isinstance(result, ComprehensiveAnalysisResult)
        assert result.functional is not None
        # May detect modal characteristics
        if result.modal:
            assert "Mixolydian" in str(result.modal.modal_characteristics)

    @pytest.mark.skip(
        reason="TODO: Fix parent key parameter passing in comprehensive analysis engine - Test fails due to issue with how parent_key parameter is handled in the comprehensive analysis flow. Need to ensure parent key context is properly propagated through all analysis stages."
    )
    @pytest.mark.asyncio
    async def test_analyze_with_parent_key(self, analyzer):
        """Test analysis with parent key context."""
        result = await analyzer.analyze_comprehensively(
            "Am F C G", parent_key="C major"
        )

        assert result.functional.key_center in ["A", "C"]
        assert result.user_input.parent_key == "C major"

    @pytest.mark.asyncio
    async def test_empty_progression_raises_error(self, analyzer):
        """Test that empty progression raises error."""
        with pytest.raises(ValueError):
            await analyzer.analyze_comprehensively("")

    @pytest.mark.asyncio
    async def test_multiple_interpretations_fallback(self, analyzer):
        """Test multiple interpretations with fallback."""
        from harmonic_analysis.types import AnalysisOptions

        options = AnalysisOptions(parent_key="C major")
        result = await analyzer.analyze_with_multiple_interpretations(
            "C F G C", options
        )

        assert result.primary_analysis is not None
        assert result.primary_analysis.confidence > 0.0
        assert result.metadata["total_interpretations_considered"] >= 1


class TestAnalysisResults:
    """Test analysis result structures."""

    @pytest.mark.asyncio
    async def test_result_has_required_fields(self):
        """Test that results have all required fields."""
        analyzer = ComprehensiveAnalysisEngine()
        result = await analyzer.analyze_comprehensively("C F G C")

        # Check required top-level fields
        assert hasattr(result, "functional")
        assert hasattr(result, "modal")
        assert hasattr(result, "chromatic")
        assert hasattr(result, "primary_approach")
        assert hasattr(result, "confidence")
        assert hasattr(result, "explanation")
        assert hasattr(result, "pedagogical_value")
        assert hasattr(result, "user_input")

        # Check functional analysis fields
        functional = result.functional
        assert hasattr(functional, "key_center")
        assert hasattr(functional, "key_signature")
        assert hasattr(functional, "mode")
        assert hasattr(functional, "chords")
        assert hasattr(functional, "cadences")
        assert hasattr(functional, "confidence")

        # Check user input context
        user_input = result.user_input
        assert hasattr(user_input, "chord_progression")
        assert hasattr(user_input, "parent_key")
        assert hasattr(user_input, "analysis_type")

    @pytest.mark.asyncio
    async def test_confidence_scores_in_valid_range(self):
        """Test that confidence scores are in valid range."""
        analyzer = ComprehensiveAnalysisEngine()
        result = await analyzer.analyze_comprehensively("C F G C")

        assert 0.0 <= result.confidence <= 1.0
        assert 0.0 <= result.functional.confidence <= 1.0

        if result.modal and result.modal.enhanced_analysis:
            assert 0.0 <= result.modal.enhanced_analysis.confidence <= 1.0
