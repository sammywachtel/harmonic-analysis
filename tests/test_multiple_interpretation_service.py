"""
Tests for Multiple Interpretation Service

Tests comprehensive multi-perspective analysis including:
- Functional vs modal interpretation ranking
- Confidence scoring and evidence collection
- Alternative analysis filtering
- Pedagogical level adaptation
- Performance and caching
"""

import pytest

from harmonic_analysis import (
    AnalysisOptions,
    EvidenceType,
    InterpretationType,
    MultipleInterpretationService,
    PedagogicalLevel,
    analyze_progression_multiple,
)


class TestMultipleInterpretationService:
    """Test suite for MultipleInterpretationService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = MultipleInterpretationService()

    @pytest.mark.asyncio
    async def test_functional_primary_analysis(self):
        """Test progression that should favor functional interpretation"""
        # Classic I-vi-IV-V progression
        chords = ["C", "Am", "F", "G"]
        result = await self.service.analyze_progression(chords)

        assert result.primary_analysis.type == InterpretationType.FUNCTIONAL
        assert result.primary_analysis.confidence > 0.7
        assert "I" in result.primary_analysis.roman_numerals
        assert "C" in result.primary_analysis.key_signature

    @pytest.mark.asyncio
    async def test_modal_primary_analysis(self):
        """Test progression that should favor modal interpretation"""
        # Mixolydian progression with bVII
        chords = ["G", "F", "C", "G"]
        options = AnalysisOptions(parent_key="C")
        result = await self.service.analyze_progression(chords, options)

        # Should detect modal characteristics
        assert (
            len(result.alternative_analyses) > 0
            or result.primary_analysis.type == InterpretationType.MODAL
        )

        # Check for evidence of modal characteristics
        modal_analysis = None
        if result.primary_analysis.type == InterpretationType.MODAL:
            modal_analysis = result.primary_analysis
        else:
            modal_analysis = next(
                (
                    alt
                    for alt in result.alternative_analyses
                    if alt.type == InterpretationType.MODAL
                ),
                None,
            )

        if modal_analysis:
            assert modal_analysis.mode is not None
            assert any(
                ev.type == EvidenceType.INTERVALLIC for ev in modal_analysis.evidence
            )

    @pytest.mark.asyncio
    async def test_confidence_scoring(self):
        """Test that confidence scoring works correctly"""
        # Strong functional progression
        chords = ["C", "F", "G", "C"]
        result = await self.service.analyze_progression(chords)

        assert result.primary_analysis.confidence > 0.6
        assert len(result.primary_analysis.evidence) > 0

        # Check evidence types
        evidence_types = {ev.type for ev in result.primary_analysis.evidence}
        assert len(evidence_types) > 0

    @pytest.mark.asyncio
    async def test_alternative_analyses_filtering(self):
        """Test filtering of alternative analyses"""
        chords = ["Am", "F", "C", "G"]

        # Test with different confidence thresholds
        low_threshold = AnalysisOptions(confidence_threshold=0.3, max_alternatives=5)
        high_threshold = AnalysisOptions(confidence_threshold=0.8, max_alternatives=5)

        low_result = await self.service.analyze_progression(chords, low_threshold)
        high_result = await self.service.analyze_progression(chords, high_threshold)

        # Low threshold should include more alternatives
        assert len(low_result.alternative_analyses) >= len(
            high_result.alternative_analyses
        )

    @pytest.mark.asyncio
    async def test_pedagogical_level_adaptation(self):
        """Test adaptation to different pedagogical levels"""
        chords = ["Am", "F", "C", "G"]

        # Test different pedagogical levels
        beginner_opts = AnalysisOptions(pedagogical_level="beginner")
        advanced_opts = AnalysisOptions(pedagogical_level="advanced")

        beginner_result = await self.service.analyze_progression(chords, beginner_opts)
        advanced_result = await self.service.analyze_progression(chords, advanced_opts)

        # Advanced should be more likely to show alternatives
        assert beginner_result.metadata.pedagogical_level == PedagogicalLevel.BEGINNER
        assert advanced_result.metadata.pedagogical_level == PedagogicalLevel.ADVANCED

        # Check show_alternatives logic
        if beginner_result.primary_analysis.confidence > 0.8:
            assert not beginner_result.metadata.show_alternatives

        # Advanced users typically see alternatives
        if len(advanced_result.alternative_analyses) > 0:
            assert advanced_result.metadata.show_alternatives

    @pytest.mark.asyncio
    async def test_force_multiple_interpretations(self):
        """Test forcing multiple interpretations"""
        chords = ["C", "F", "G", "C"]
        options = AnalysisOptions(force_multiple_interpretations=True)

        result = await self.service.analyze_progression(chords, options)

        assert result.metadata.show_alternatives

    @pytest.mark.asyncio
    async def test_relationship_descriptions(self):
        """Test relationship descriptions between interpretations"""
        chords = ["Am", "F", "C", "G"]
        result = await self.service.analyze_progression(chords)

        # Check for relationship descriptions in alternatives
        for alt in result.alternative_analyses:
            assert alt.relationship_to_primary != ""
            assert isinstance(alt.relationship_to_primary, str)

    @pytest.mark.asyncio
    async def test_evidence_collection(self):
        """Test evidence collection for different analysis types"""
        # Progression with clear cadence
        chords = ["Am", "F", "G", "C"]
        result = await self.service.analyze_progression(chords)

        # Should have multiple types of evidence
        evidence = result.primary_analysis.evidence
        assert len(evidence) > 0

        # Check evidence structure
        for ev in evidence:
            assert 0 <= ev.strength <= 1
            assert ev.description != ""
            assert ev.musical_basis != ""
            assert len(ev.supported_interpretations) > 0

    @pytest.mark.asyncio
    async def test_caching_behavior(self):
        """Test that caching works correctly"""
        chords = ["C", "Am", "F", "G"]

        # First call should create cache entry
        result1 = await self.service.analyze_progression(chords)

        # Second call should use cache (should be faster)
        import time

        start_time = time.time()
        result2 = await self.service.analyze_progression(chords)
        cache_time = time.time() - start_time

        # Results should be identical (same object from cache)
        assert (
            result1.primary_analysis.confidence == result2.primary_analysis.confidence
        )
        assert result1.primary_analysis.analysis == result2.primary_analysis.analysis

        # Cache should be fast (under 1ms typically)
        assert cache_time < 0.01  # 10ms threshold for cached results

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling for invalid input"""
        # Empty chord list
        with pytest.raises(Exception):
            await self.service.analyze_progression([])

        # Invalid chord symbols should still produce some result
        result = await self.service.analyze_progression(["XYZ", "ABC"])
        assert result is not None
        assert result.primary_analysis is not None

    @pytest.mark.asyncio
    async def test_metadata_completeness(self):
        """Test that metadata is complete and accurate"""
        chords = ["Am", "F", "C", "G"]
        result = await self.service.analyze_progression(chords)

        # Check metadata fields
        metadata = result.metadata
        assert metadata.total_interpretations_considered >= 1
        assert 0 <= metadata.confidence_threshold <= 1
        assert isinstance(metadata.show_alternatives, bool)
        assert metadata.pedagogical_level in [
            PedagogicalLevel.BEGINNER,
            PedagogicalLevel.INTERMEDIATE,
            PedagogicalLevel.ADVANCED,
        ]
        assert metadata.analysis_time_ms > 0

        # Check input preservation
        assert result.input_chords == chords

    @pytest.mark.asyncio
    async def test_reasoning_generation(self):
        """Test that reasoning is generated correctly"""
        chords = ["C", "F", "G", "C"]
        result = await self.service.analyze_progression(chords)

        # Primary analysis should have reasoning
        assert result.primary_analysis.reasoning != ""
        assert result.primary_analysis.theoretical_basis != ""

        # Alternative analyses should also have reasoning
        for alt in result.alternative_analyses:
            assert alt.reasoning != ""
            assert alt.theoretical_basis != ""

    @pytest.mark.asyncio
    async def test_complex_progression_analysis(self):
        """Test analysis of complex progression with multiple valid interpretations"""
        # Progression that could be interpreted multiple ways
        chords = ["Am", "Dm", "G", "Em", "Am"]
        result = await self.service.analyze_progression(chords)

        # Should have high-confidence primary analysis
        assert result.primary_analysis.confidence > 0.5

        # Might have alternative interpretations
        if len(result.alternative_analyses) > 0:
            # Alternatives should have reasonable confidence
            for alt in result.alternative_analyses:
                assert alt.confidence > 0.3
                assert alt.confidence <= result.primary_analysis.confidence


class TestConvenienceFunctions:
    """Test convenience functions"""

    @pytest.mark.asyncio
    async def test_analyze_progression_multiple(self):
        """Test convenience function"""
        chords = ["C", "Am", "F", "G"]
        result = await analyze_progression_multiple(chords)

        assert result is not None
        assert result.primary_analysis is not None
        assert result.input_chords == chords

    @pytest.mark.asyncio
    async def test_analyze_progression_multiple_with_options(self):
        """Test convenience function with options"""
        chords = ["Am", "F", "C", "G"]
        options = AnalysisOptions(
            parent_key="C", pedagogical_level="advanced", confidence_threshold=0.4
        )

        result = await analyze_progression_multiple(chords, options)

        assert result.metadata.pedagogical_level == PedagogicalLevel.ADVANCED
        assert result.metadata.confidence_threshold == 0.4


class TestPerformance:
    """Test performance characteristics"""

    @pytest.mark.asyncio
    async def test_analysis_performance(self):
        """Test that analysis completes in reasonable time"""
        chords = ["C", "Am", "F", "G", "Em", "Dm", "G7", "C"]

        import time

        start_time = time.time()
        result = await analyze_progression_multiple(chords)
        analysis_time = time.time() - start_time

        # Should complete within reasonable time (5 seconds)
        assert analysis_time < 5.0
        assert result.metadata.analysis_time_ms > 0

        # Analysis time in metadata should be accurate (within 50ms)
        assert abs(result.metadata.analysis_time_ms - analysis_time * 1000) < 50
