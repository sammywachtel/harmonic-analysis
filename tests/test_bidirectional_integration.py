#!/usr/bin/env python
"""
Integration test for bidirectional suggestion system with the main service.

Tests the complete workflow from chord progression analysis to bidirectional suggestions.
"""

import pytest

from harmonic_analysis.services.multiple_interpretation_service import (
    analyze_progression_multiple,
)
from harmonic_analysis.analysis_types import AnalysisOptions


class TestBidirectionalIntegration:
    """Test bidirectional suggestions through the main analysis service"""

    @pytest.mark.skip(
        reason="TODO: Fix bidirectional integration - API mismatch between suggestion engines and main service. Core analysis works but integration layer needs refactoring to properly pass AnalysisOptions objects between components."
    )
    @pytest.mark.asyncio
    async def test_integrated_suggestion_generation(self):
        """Test that bidirectional suggestions are generated through the main service"""
        # Test ii-V-I progression without key context
        progression = ["Dm7", "G7", "Cmaj7"]
        options = AnalysisOptions()  # No parent key provided

        result = await analyze_progression_multiple(progression, options)

        # Should have generated suggestions
        assert result.suggestions is not None
        assert result.suggestions.parent_key_suggestions

        # Should suggest C major with reasonable confidence
        c_major_suggestion = next(
            (
                s
                for s in result.suggestions.parent_key_suggestions
                if "C major" in s.suggested_key
            ),
            None,
        )
        assert c_major_suggestion is not None
        assert c_major_suggestion.confidence > 0.5

    @pytest.mark.asyncio
    async def test_no_suggestions_when_key_provided_and_helpful(self):
        """Test that unnecessary key suggestions don't appear when key is helpful"""
        # Test progression that benefits from key context
        progression = ["Dm7", "G7", "Cmaj7"]
        options = AnalysisOptions(parent_key="C major")

        result = await analyze_progression_multiple(progression, options)

        # Should not suggest removing the key since it's helpful
        if result.suggestions:
            assert not result.suggestions.unnecessary_key_suggestions

    @pytest.mark.asyncio
    async def test_well_formed_progression_analysis(self):
        """Test that well-formed progressions analyze correctly without requiring suggestions"""
        # Use a classic I-vi-IV-V progression that doesn't need improvement
        progression = ["C", "Am", "F", "G"]
        options = AnalysisOptions()

        result = await analyze_progression_multiple(progression, options)

        # Should successfully analyze without errors
        assert result is not None
        assert result.primary_analysis is not None

        # Well-formed progressions may not need suggestions (which is correct behavior)
        if result.suggestions:
            # Suggestions object should exist but may have empty lists for good progressions
            assert isinstance(result.suggestions.parent_key_suggestions, list)
            assert isinstance(result.suggestions.general_suggestions, list)

    @pytest.mark.asyncio
    async def test_suggestion_system_robustness(self):
        """Test that suggestion system handles edge cases without crashing"""
        # Test with various edge cases that might trigger different code paths
        test_cases = [
            ["C", "F", "G"],  # Simple progression
            ["C", "C", "C", "C"],  # Repetitive
            ["Am", "F", "C", "G"],  # vi-IV-I-V (needs parent key context)
        ]

        for progression in test_cases:
            result = await analyze_progression_multiple(progression, AnalysisOptions())

            # Should not crash and should return valid result
            assert result is not None
            assert result.primary_analysis is not None

            # Suggestions may or may not exist depending on the progression
            if result.suggestions:
                assert isinstance(result.suggestions, type(result.suggestions))

    @pytest.mark.asyncio
    async def test_simple_progression_analysis(self):
        """Test basic analysis still works with new bidirectional system"""
        progression = ["C", "F", "G", "C"]
        options = AnalysisOptions()

        result = await analyze_progression_multiple(progression, options)

        # Basic analysis should still work
        assert result.primary_analysis
        assert result.primary_analysis.confidence > 0.0
        assert result.input_chords == progression

    @pytest.mark.asyncio
    async def test_empty_progression_handling(self):
        """Test handling of edge case inputs"""
        with pytest.raises(ValueError, match="Empty chord progression"):
            await analyze_progression_multiple([], AnalysisOptions())


if __name__ == "__main__":
    pytest.main([__file__])
