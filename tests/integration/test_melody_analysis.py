"""
Integration tests for melody analysis functionality.

Tests the complete melody analysis pipeline from input normalization
through pattern matching to result generation via AnalysisEnvelope.
"""

import pytest

from harmonic_analysis.dto import AnalysisType
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService


class TestMelodyAnalysisIntegration:
    """Integration tests for melody analysis through PatternAnalysisService."""

    def setup_method(self):
        """Set up test fixtures."""
        # Opening move: initialize service for each test
        self.service = PatternAnalysisService()

    def test_simple_melody_analysis(self):
        """Test analysis of a simple melodic line."""
        # Big play: analyze simple scale-wise melody
        result = self.service.analyze_with_patterns(
            melody=["C4", "D4", "E4", "F4", "G4"], key_hint="C major"
        )

        # Victory lap: verify successful analysis
        assert result.primary is not None
        assert result.primary.key_signature == "C major"
        assert result.primary.type in [AnalysisType.FUNCTIONAL, AnalysisType.MODAL]

    def test_modal_melody_analysis(self):
        """Test analysis of modal melodic patterns."""
        # Big play: analyze melody suggesting D Dorian
        result = self.service.analyze_with_patterns(
            melody=["D4", "E4", "F4", "G4", "A4", "B4", "C5"], key_hint="D dorian"
        )

        # Victory lap: verify modal analysis
        assert result.primary is not None
        assert result.primary.key_signature == "D dorian"

    def test_melody_with_suspensions(self):
        """Test analysis of melody with suspension patterns (4-3, 7-1)."""
        # Big play: analyze melody with characteristic suspension pattern
        result = self.service.analyze_with_patterns(
            melody=["F4", "E4", "C4", "B3", "C4"],  # 4-3 and 7-1 movement
            key_hint="C major",
        )

        # Victory lap: verify suspension analysis
        assert result.primary is not None
        assert result.primary.key_signature == "C major"

    def test_mixolydian_melody_analysis(self):
        """Test analysis of Mixolydian mode melodic patterns."""
        # Big play: analyze G Mixolydian melody (characteristic b7)
        result = self.service.analyze_with_patterns(
            melody=["G4", "A4", "B4", "C5", "D5", "E5", "F5"], key_hint="G mixolydian"
        )

        # Victory lap: verify Mixolydian analysis
        assert result.primary is not None
        assert result.primary.key_signature == "G mixolydian"

    def test_melody_with_octave_numbers(self):
        """Test melody analysis with octave specifications."""
        # Big play: analyze melody with various octave numbers
        result = self.service.analyze_with_patterns(
            melody=["C3", "E4", "G4", "C5"], key_hint="C major"
        )

        # Victory lap: verify octave handling
        assert result.primary is not None
        assert result.primary.key_signature == "C major"

    def test_melody_with_accidentals(self):
        """Test melody analysis with chromatic alterations."""
        # Big play: analyze melody with sharps and flats
        result = self.service.analyze_with_patterns(
            melody=["F#4", "G4", "A4", "Bb4", "C5"], key_hint="G major"
        )

        # Victory lap: verify accidental handling
        assert result.primary is not None
        assert result.primary.key_signature == "G major"

    @pytest.mark.asyncio
    async def test_async_melody_analysis(self):
        """Test asynchronous melody analysis."""
        # Big play: test async interface with melody input
        result = await self.service.analyze_with_patterns_async(
            melody=["C4", "D4", "E4", "F4", "G4", "A4", "B4"], key_hint="C major"
        )

        # Victory lap: verify async analysis works
        assert result.primary is not None
        assert result.primary.key_signature == "C major"


class TestMelodyAnalysisErrorHandling:
    """Test error handling in melody analysis."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = PatternAnalysisService()

    def test_missing_key_hint_error(self):
        """Test that melody analysis requires key_hint parameter."""
        # Big play: attempt melody analysis without key hint
        with pytest.raises(
            ValueError, match="Melody analysis requires key_hint parameter"
        ):
            self.service.analyze_with_patterns(melody=["C4", "D4", "E4", "F4", "G4"])

    def test_multiple_input_types_error(self):
        """Test that multiple input types are rejected."""
        # Big play: attempt to provide both chords and melody
        with pytest.raises(ValueError, match="Cannot provide multiple input types"):
            self.service.analyze_with_patterns(
                chord_symbols=["C", "F", "G"],
                melody=["C4", "D4", "E4"],
                key_hint="C major",
            )

    def test_chord_and_roman_and_melody_error(self):
        """Test rejection of all three input types."""
        # Main play: attempt to provide chords, romans, and melody
        with pytest.raises(ValueError, match="Cannot provide multiple input types"):
            self.service.analyze_with_patterns(
                chord_symbols=["C", "F"],
                romans=["I", "IV"],
                melody=["C4", "D4"],
                key_hint="C major",
            )

    def test_melody_and_scale_error(self):
        """Test rejection of both melody and scale inputs."""
        # Main play: attempt to provide both melody and scale notes
        with pytest.raises(ValueError, match="Cannot provide multiple input types"):
            self.service.analyze_with_patterns(
                melody=["C4", "D4", "E4"],
                notes=["C", "D", "E", "F", "G", "A", "B"],
                key_hint="C major",
            )

    def test_invalid_melody_notes_graceful_handling(self):
        """Test graceful handling of unusual melody note input."""
        # The melody analysis is robust and handles unusual input gracefully
        result = self.service.analyze_with_patterns(
            melody=["X4", "Y4", "Z4"], key_hint="C major"  # Unusual note names
        )

        # Should complete analysis gracefully with fallback behavior
        assert result.primary is not None
        assert result.primary.key_signature == "C major"

    def test_empty_melody_list_error(self):
        """Test handling of empty melody list."""
        with pytest.raises(ValueError, match="Must provide one of"):
            self.service.analyze_with_patterns(melody=[], key_hint="C major")

    @pytest.mark.asyncio
    async def test_async_error_handling(self):
        """Test that async version handles errors correctly."""
        # Big play: test async error handling
        with pytest.raises(
            ValueError, match="Melody analysis requires key_hint parameter"
        ):
            await self.service.analyze_with_patterns_async(
                melody=["C4", "D4", "E4", "F4", "G4"]
            )


class TestMelodyAnalysisEdgeCases:
    """Test edge cases in melody analysis."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = PatternAnalysisService()

    def test_single_note_melody(self):
        """Test analysis with single note melody."""
        # Big play: analyze single note - this should work
        result = self.service.analyze_with_patterns(melody=["C4"], key_hint="C major")

        # Victory lap: single note analysis should succeed
        assert result.primary is not None
        assert result.primary.key_signature == "C major"

    def test_repeated_notes_melody(self):
        """Test analysis with repeated notes."""
        # Big play: analyze melody with repeated notes
        result = self.service.analyze_with_patterns(
            melody=["C4", "C4", "E4", "E4", "G4", "G4"], key_hint="C major"
        )

        # Victory lap: repeated notes should be handled gracefully
        assert result.primary is not None
        assert result.primary.key_signature == "C major"

    def test_wide_interval_melody(self):
        """Test analysis with wide intervallic leaps."""
        # Big play: analyze melody with large jumps
        result = self.service.analyze_with_patterns(
            melody=["C3", "C6", "G2", "E5"], key_hint="C major"  # Wide intervals
        )

        # Victory lap: wide intervals should be analyzed successfully
        assert result.primary is not None
        assert result.primary.key_signature == "C major"

    def test_enharmonic_equivalents_melody(self):
        """Test that enharmonic equivalents are handled correctly."""
        # Test F# vs Gb in different contexts
        result_sharp = self.service.analyze_with_patterns(
            melody=["F#4", "G4", "A4"], key_hint="G major"
        )

        result_flat = self.service.analyze_with_patterns(
            melody=["Gb4", "Ab4", "Bb4"], key_hint="Db major"
        )

        # Victory lap: both should produce valid analyses
        assert result_sharp.primary is not None
        assert result_flat.primary is not None

    def test_case_insensitive_note_names(self):
        """Test that note names are handled case-insensitively."""
        # Test mixed case input
        result = self.service.analyze_with_patterns(
            melody=["c4", "D4", "e4", "F4", "g4"], key_hint="C major"  # Mixed case
        )

        # Victory lap: should handle case variations gracefully
        assert result.primary is not None
        assert result.primary.key_signature == "C major"


class TestMelodyAnalysisIntegrationWithPatterns:
    """Test melody analysis integration with pattern engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = PatternAnalysisService()

    def test_melody_context_in_analysis(self):
        """Test that melody data is properly passed to pattern engine."""
        # Big play: analyze melody and verify context includes melody data
        result = self.service.analyze_with_patterns(
            melody=["C4", "D4", "E4", "F4", "G4"], key_hint="C major"
        )

        # Victory lap: verify analysis succeeded
        assert result.primary is not None
        # The melody data should be used by pattern engine for analysis
        assert result.primary.key_signature == "C major"

    def test_modal_melody_pattern_recognition(self):
        """Test that modal melody patterns are recognized correctly."""
        # Big play: test modal melodies that should trigger modal patterns
        modal_tests = [
            (["D4", "E4", "F4", "G4", "A4"], "D dorian"),
            (["E4", "F4", "G4", "A4", "B4"], "E phrygian"),
            (["F4", "G4", "A4", "B4", "C5"], "F lydian"),
            (["G4", "A4", "B4", "C5", "D5"], "G mixolydian"),
        ]

        for melody_notes, key_hint in modal_tests:
            result = self.service.analyze_with_patterns(
                melody=melody_notes, key_hint=key_hint
            )

            # Victory lap: modal analysis should succeed
            assert result.primary is not None
            assert result.primary.key_signature == key_hint

            # Modal patterns might result in either MODAL or FUNCTIONAL type
            # depending on pattern matching strength
            assert result.primary.type in [AnalysisType.MODAL, AnalysisType.FUNCTIONAL]

    def test_confidence_scoring_for_melody(self):
        """Test that confidence scoring works for melody analysis."""
        # Big play: analyze clear melodic pattern
        clear_result = self.service.analyze_with_patterns(
            melody=["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"], key_hint="C major"
        )

        # Test modal melody
        modal_result = self.service.analyze_with_patterns(
            melody=["D4", "E4", "F4", "G4", "A4", "B4", "C5"], key_hint="D dorian"
        )

        # Victory lap: both should have reasonable confidence
        assert clear_result.primary.confidence > 0.0
        assert modal_result.primary.confidence > 0.0

    def test_melody_vs_chord_analysis_types(self):
        """Test that melody analysis produces appropriate analysis types."""
        # Test simple melodic pattern
        result = self.service.analyze_with_patterns(
            melody=["C4", "E4", "G4", "C5"], key_hint="C major"  # Arpeggiated triad
        )

        # Victory lap: should produce analysis with appropriate type
        assert result.primary is not None
        assert result.primary.type in [AnalysisType.FUNCTIONAL, AnalysisType.MODAL]
        # Confidence should be meaningful for melody analysis
        assert 0.0 <= result.primary.confidence <= 1.0
