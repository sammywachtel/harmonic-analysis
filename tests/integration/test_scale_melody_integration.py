"""
Comprehensive integration tests for scale and melody analysis with enhanced summaries.

Tests the complete pipeline from input → normalization → pattern engine → enhanced DTOs → reasoning.
"""

import asyncio

import pytest

from harmonic_analysis.dto import AnalysisType, MelodySummaryDTO, ScaleSummaryDTO
from harmonic_analysis.services.unified_pattern_service import UnifiedPatternService


class TestScaleMelodyIntegration:
    """Integration tests for scale and melody analysis with rich summaries."""

    @pytest.fixture
    def service(self):
        """Create UnifiedPatternService for testing."""
        return UnifiedPatternService()

    @pytest.mark.asyncio
    async def test_dorian_scale_analysis_complete(self, service):
        """Test complete Dorian scale analysis with all enhancements."""
        result = await service.analyze_with_patterns_async(
            notes=["C", "D", "E♭", "F", "G", "A", "B♭"], key_hint="C dorian"
        )

        # Test primary analysis structure
        assert result.primary is not None
        assert result.primary.confidence > 0.0

        # Test scale summary population
        assert result.primary.scale_summary is not None
        scale_summary = result.primary.scale_summary

        # Validate scale summary content
        assert scale_summary.detected_mode == "Dorian"
        assert scale_summary.degrees == [1, 2, 3, 4, 5, 6, 7]
        assert "♭3" in scale_summary.characteristic_notes
        assert "♮6" in scale_summary.characteristic_notes
        assert scale_summary.notes == ["C", "D", "Eb", "F", "G", "A", "Bb"]

        # Test enhanced reasoning
        assert "Detected Dorian scale" in result.primary.reasoning

        # Test serialization preservation
        data = result.to_dict()
        restored = result.from_dict(data)
        assert restored.primary.scale_summary is not None
        assert restored.primary.scale_summary.detected_mode == "Dorian"

    @pytest.mark.asyncio
    async def test_phrygian_scale_characteristics(self, service):
        """Test Phrygian scale analysis with mode-specific characteristics."""
        result = await service.analyze_with_patterns_async(
            notes=["C", "D♭", "E♭", "F", "G", "A♭", "B♭"], key_hint="C phrygian"
        )

        # Validate Phrygian-specific characteristics
        assert result.primary.scale_summary is not None
        scale_summary = result.primary.scale_summary

        assert scale_summary.detected_mode == "Phrygian"
        assert "♭2" in scale_summary.characteristic_notes
        assert "♭3" in scale_summary.characteristic_notes

    @pytest.mark.asyncio
    async def test_mixolydian_scale_analysis(self, service):
        """Test Mixolydian scale analysis."""
        result = await service.analyze_with_patterns_async(
            notes=["G", "A", "B", "C", "D", "E", "F"], key_hint="G mixolydian"
        )

        assert result.primary.scale_summary is not None
        scale_summary = result.primary.scale_summary

        assert scale_summary.detected_mode == "Mixolydian"
        assert "♭7" in scale_summary.characteristic_notes

    @pytest.mark.asyncio
    async def test_ascending_melody_analysis_complete(self, service):
        """Test complete ascending melody analysis with all enhancements."""
        result = await service.analyze_with_patterns_async(
            melody=["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"], key_hint="C major"
        )

        # Test melody summary population
        assert result.primary.melody_summary is not None
        melody_summary = result.primary.melody_summary

        # Validate melody summary content
        assert melody_summary.intervals == [2, 2, 1, 2, 2, 2, 1]
        assert melody_summary.contour == "ascending"
        assert melody_summary.range_semitones == 12
        assert melody_summary.leading_tone_resolutions == 2  # E->F and B->C
        assert "stepwise motion" in melody_summary.melodic_characteristics

        # Test enhanced reasoning
        reasoning = result.primary.reasoning
        assert "ascending melodic contour" in reasoning
        assert "multiple leading-tone resolutions" in reasoning
        assert "predominantly stepwise motion" in reasoning

    @pytest.mark.asyncio
    async def test_descending_melody_with_leaps(self, service):
        """Test descending melody with leap characteristics."""
        result = await service.analyze_with_patterns_async(
            melody=["C5", "A4", "F4", "D4", "C4"],  # Contains 3rd and 4th leaps
            key_hint="C major",
        )

        assert result.primary.melody_summary is not None
        melody_summary = result.primary.melody_summary

        # Validate leap detection
        assert melody_summary.contour == "descending"
        assert melody_summary.range_semitones == 12
        # Should detect leap emphasis due to -3, -4, -3, -1 intervals
        assert "leap emphasis" in melody_summary.melodic_characteristics

        # Test reasoning includes contour
        assert "descending melodic contour" in result.primary.reasoning

    @pytest.mark.asyncio
    async def test_chromatic_melody_analysis(self, service):
        """Test melody with chromatic motion."""
        result = await service.analyze_with_patterns_async(
            melody=["C4", "C#4", "D4", "D#4", "E4"],  # Chromatic ascent
            key_hint="C major",
        )

        assert result.primary.melody_summary is not None
        melody_summary = result.primary.melody_summary

        # Check for chromatic motion detection
        assert "chromatic motion" in melody_summary.melodic_characteristics
        assert melody_summary.intervals == [1, 1, 1, 1]

    @pytest.mark.asyncio
    async def test_mixed_contour_melody(self, service):
        """Test melody with mixed up/down contour."""
        result = await service.analyze_with_patterns_async(
            melody=["C4", "E4", "D4", "F4", "E4", "C4"],  # Up-down-up-down pattern
            key_hint="C major",
        )

        assert result.primary.melody_summary is not None
        melody_summary = result.primary.melody_summary

        # Should detect mixed or wave contour
        assert melody_summary.contour in ["mixed", "wave", "arch"]

    @pytest.mark.asyncio
    async def test_serialization_round_trip_complete(self, service):
        """Test complete serialization round-trip with both scale and melody summaries."""
        # Create analysis with both scale and melody data
        scale_result = await service.analyze_with_patterns_async(
            notes=["C", "D", "E♭", "F", "G", "A", "B♭"], key_hint="C dorian"
        )

        melody_result = await service.analyze_with_patterns_async(
            melody=["C4", "D4", "E4", "F4"], key_hint="C major"
        )

        # Test scale serialization
        scale_data = scale_result.to_dict()
        scale_restored = scale_result.from_dict(scale_data)

        assert scale_restored.primary.scale_summary is not None
        assert scale_restored.primary.scale_summary.detected_mode == "Dorian"
        assert scale_restored.primary.scale_summary.characteristic_notes == ["♭3", "♮6"]

        # Test melody serialization
        melody_data = melody_result.to_dict()
        melody_restored = melody_result.from_dict(melody_data)

        assert melody_restored.primary.melody_summary is not None
        assert melody_restored.primary.melody_summary.contour == "ascending"
        assert melody_restored.primary.melody_summary.intervals == [2, 2, 1]

    @pytest.mark.asyncio
    async def test_error_handling_graceful_degradation(self, service):
        """Test graceful handling of invalid inputs."""
        # Test invalid scale notes - should handle gracefully
        with pytest.raises(ValueError, match="Invalid scale input"):
            await service.analyze_with_patterns_async(
                notes=["X", "Y", "Z"], key_hint="C major"
            )

        # Test invalid melody notes - should continue with fallback
        result = await service.analyze_with_patterns_async(
            melody=["C4", "InvalidNote", "E4"], key_hint="C major"
        )

        # Should still produce result with partial melody data
        assert result.primary is not None
        # Melody summary might be None or have minimal data due to invalid input

    def test_scale_summary_dto_creation(self):
        """Test ScaleSummaryDTO creation and properties."""
        scale_summary = ScaleSummaryDTO(
            detected_mode="Dorian",
            parent_key="C major",
            degrees=[1, 2, 3, 4, 5, 6, 7],
            characteristic_notes=["♭3", "♮6"],
            notes=["C", "D", "Eb", "F", "G", "A", "Bb"],
        )

        assert scale_summary.detected_mode == "Dorian"
        assert scale_summary.parent_key == "C major"
        assert len(scale_summary.degrees) == 7
        assert "♭3" in scale_summary.characteristic_notes

    def test_melody_summary_dto_creation(self):
        """Test MelodySummaryDTO creation and properties."""
        melody_summary = MelodySummaryDTO(
            intervals=[2, 2, 1, 2],
            contour="ascending",
            range_semitones=7,
            leading_tone_resolutions=1,
            suspensions=0,
            chromatic_notes=[],
            melodic_characteristics=["stepwise motion"],
        )

        assert melody_summary.contour == "ascending"
        assert melody_summary.range_semitones == 7
        assert melody_summary.leading_tone_resolutions == 1
        assert "stepwise motion" in melody_summary.melodic_characteristics

    @pytest.mark.asyncio
    async def test_pattern_evidence_integration(self, service):
        """Test that scale/melody patterns contribute to evidence and reasoning."""
        result = await service.analyze_with_patterns_async(
            notes=["C", "D", "E♭", "F", "G", "A", "B♭"], key_hint="C dorian"
        )

        # Check that scale information appears in reasoning (even if no specific patterns)
        reasoning = result.primary.reasoning
        assert "Detected Dorian scale" in reasoning or "Dorian" in reasoning

        # Patterns may or may not be detected depending on available pattern definitions
        # This is acceptable as long as scale summary and reasoning are populated

    @pytest.mark.asyncio
    async def test_confidence_scoring_with_summaries(self, service):
        """Test that confidence scoring works correctly with enhanced summaries."""
        # Well-formed Dorian scale should have reasonable confidence
        result = await service.analyze_with_patterns_async(
            notes=["C", "D", "E♭", "F", "G", "A", "B♭"], key_hint="C dorian"
        )

        assert result.primary.confidence > 0.05  # Should have some confidence
        assert result.primary.scale_summary is not None

        # Confidence should be consistent with scale detection
        if result.primary.scale_summary.detected_mode == "Dorian":
            assert result.primary.confidence > 0.0
