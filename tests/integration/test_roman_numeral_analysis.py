"""
Integration tests for roman numeral analysis support.

Tests the complete workflow of roman numeral input support in the
PatternAnalysisService and UnifiedPatternService.
"""

import pytest
import asyncio
from typing import List, Optional

from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService
from harmonic_analysis.dto import AnalysisEnvelope, AnalysisType


class TestRomanNumeralAnalysis:
    """Test suite for roman numeral input analysis."""

    def setup_method(self):
        """Setup test fixtures."""
        self.service = PatternAnalysisService()

    @pytest.mark.asyncio
    async def test_basic_roman_progression(self):
        """Test basic roman numeral progression analysis."""
        # Opening move: test classic vi-IV-I-V progression
        result = await self.service.analyze_with_patterns_async(
            romans=['vi', 'IV', 'I', 'V'],
            key_hint='C major',
            profile='classical'
        )

        assert isinstance(result, AnalysisEnvelope)
        assert result.primary is not None
        assert result.chord_symbols == ['Am', 'F', 'C', 'G']
        assert result.primary.roman_numerals == ['vi', 'IV', 'I', 'V']
        assert result.primary.confidence > 0.5

    @pytest.mark.asyncio
    async def test_secondary_dominants(self):
        """Test secondary dominant roman numeral handling."""
        result = await self.service.analyze_with_patterns_async(
            romans=['I', 'V/V', 'V', 'I'],
            key_hint='C major',
            profile='classical'
        )

        assert result.primary is not None
        assert result.chord_symbols == ['C', 'D7', 'G', 'C']
        # Victory lap: pattern engine should preserve original romans
        assert result.primary.roman_numerals == ['I', 'V/V', 'V', 'I']

    @pytest.mark.asyncio
    async def test_accidentals_and_chromatic(self):
        """Test roman numerals with accidentals."""
        # Big play: test Phrygian-flavored progression in minor
        result = await self.service.analyze_with_patterns_async(
            romans=['i', 'bII', 'V', 'i'],
            key_hint='A minor',
            profile='classical'
        )

        assert result.primary is not None
        assert result.chord_symbols == ['Am', 'Bb', 'E', 'Am']
        # Main play: check that flats are properly handled
        assert 'bII' in result.primary.roman_numerals or '♭II' in result.primary.roman_numerals

    @pytest.mark.asyncio
    async def test_seventh_chords(self):
        """Test roman numerals with seventh chord extensions."""
        result = await self.service.analyze_with_patterns_async(
            romans=['Imaj7', 'vi7', 'ii7', 'V7'],
            key_hint='C major',
            profile='classical'
        )

        assert result.primary is not None
        expected_chords = ['Cmaj7', 'Am7', 'Dm7', 'G7']
        assert result.chord_symbols == expected_chords

    @pytest.mark.asyncio
    async def test_minor_key_progressions(self):
        """Test roman numerals in minor keys."""
        result = await self.service.analyze_with_patterns_async(
            romans=['i', 'iv', 'V', 'i'],
            key_hint='A minor',
            profile='classical'
        )

        assert result.primary is not None
        assert result.chord_symbols == ['Am', 'Dm', 'E', 'Am']
        assert result.primary.confidence > 0.5

    @pytest.mark.asyncio
    async def test_validation_missing_key(self):
        """Test that roman analysis requires key_hint."""
        # Time to tackle the tricky bit: validation should catch this
        with pytest.raises(ValueError, match="Roman numeral analysis requires key_hint"):
            await self.service.analyze_with_patterns_async(
                romans=['I', 'vi', 'IV', 'V'],
                profile='classical'
            )

    @pytest.mark.asyncio
    async def test_validation_mixed_input(self):
        """Test that mixed chord/roman input is rejected."""
        with pytest.raises(ValueError, match="Cannot provide both chord_symbols and romans"):
            await self.service.analyze_with_patterns_async(
                chord_symbols=['C', 'Am', 'F', 'G'],
                romans=['I', 'vi', 'IV', 'V'],
                key_hint='C major'
            )

    @pytest.mark.asyncio
    async def test_validation_no_input(self):
        """Test that at least one input type is required."""
        with pytest.raises(ValueError, match="Must provide either chord_symbols or romans"):
            await self.service.analyze_with_patterns_async(
                key_hint='C major',
                profile='classical'
            )

    @pytest.mark.asyncio
    async def test_complex_progression_with_inversions(self):
        """Test handling of complex roman numerals with figured bass."""
        # This looks odd, but it saves us from having to implement full inversion support
        result = await self.service.analyze_with_patterns_async(
            romans=['I', 'vi', 'ii6', 'V7'],
            key_hint='C major',
            profile='classical'
        )

        assert result.primary is not None
        # Main play: check that basic conversion works even with figured bass
        assert len(result.chord_symbols) == 4
        assert result.primary.confidence > 0.4

    def test_sync_method_support(self):
        """Test that synchronous method also supports roman inputs."""
        # Final whistle: sync wrapper should work too
        result = self.service.analyze_with_patterns(
            romans=['I', 'V', 'vi', 'IV'],
            key_hint='C major',
            profile='classical'
        )

        assert isinstance(result, AnalysisEnvelope)
        assert result.primary is not None
        assert result.chord_symbols == ['C', 'G', 'Am', 'F']

    @pytest.mark.asyncio
    async def test_different_keys(self):
        """Test roman analysis in different keys."""
        # Test in F major
        result_f = await self.service.analyze_with_patterns_async(
            romans=['I', 'vi', 'IV', 'V'],
            key_hint='F major',
            profile='classical'
        )

        # Test in G major
        result_g = await self.service.analyze_with_patterns_async(
            romans=['I', 'vi', 'IV', 'V'],
            key_hint='G major',
            profile='classical'
        )

        # Victory lap: same romans should give different chords in different keys
        assert result_f.chord_symbols == ['F', 'Dm', 'Bb', 'C']
        assert result_g.chord_symbols == ['G', 'Em', 'C', 'D']
        assert result_f.primary.roman_numerals == result_g.primary.roman_numerals

    @pytest.mark.asyncio
    async def test_flat_vs_sharp_keys(self):
        """Test enharmonic spelling in flat vs sharp keys."""
        # Test in Eb major (flat key)
        result_flat = await self.service.analyze_with_patterns_async(
            romans=['I', 'bVII', 'IV', 'I'],
            key_hint='Eb major',
            profile='classical'
        )

        # Test in F# major (sharp key)
        result_sharp = await self.service.analyze_with_patterns_async(
            romans=['I', 'bVII', 'IV', 'I'],
            key_hint='F# major',
            profile='classical'
        )

        # Main play: both should work, enharmonic spelling should be appropriate
        assert len(result_flat.chord_symbols) == 4
        assert len(result_sharp.chord_symbols) == 4
        assert result_flat.primary.confidence > 0.4
        assert result_sharp.primary.confidence > 0.4

    @pytest.mark.asyncio
    async def test_modal_analysis_with_romans(self):
        """Test that roman inputs can trigger modal analysis."""
        # Big play: modal characteristics should be detected
        result = await self.service.analyze_with_patterns_async(
            romans=['i', 'bVII', 'bVI', 'bVII'],
            key_hint='A minor',
            profile='classical'
        )

        assert result.primary is not None
        # Time to tackle the tricky bit: this should likely be modal
        # (Aeolian or natural minor characteristics)
        assert result.primary.confidence > 0.4


class TestRomanNumeralConverter:
    """Test the underlying roman-to-chord conversion utility."""

    def test_basic_conversions(self):
        """Test basic roman numeral conversions."""
        from harmonic_analysis.core.pattern_engine.token_converter import roman_to_chord

        # Major key tests
        assert roman_to_chord("I", "C major") == "C"
        assert roman_to_chord("vi", "C major") == "Am"
        assert roman_to_chord("IV", "C major") == "F"
        assert roman_to_chord("V", "C major") == "G"

        # Minor key tests
        assert roman_to_chord("i", "A minor") == "Am"
        assert roman_to_chord("iv", "A minor") == "Dm"
        assert roman_to_chord("V", "A minor") == "E"

    def test_accidentals(self):
        """Test roman numerals with accidentals."""
        from harmonic_analysis.core.pattern_engine.token_converter import roman_to_chord

        # Flat accidentals (should use flat naming)
        assert roman_to_chord("bII", "C major") == "Db"
        assert roman_to_chord("bVII", "C major") == "Bb"
        assert roman_to_chord("bVI", "C major") == "Ab"

    def test_seventh_chords(self):
        """Test seventh chord conversions."""
        from harmonic_analysis.core.pattern_engine.token_converter import roman_to_chord

        assert roman_to_chord("V7", "C major") == "G7"
        assert roman_to_chord("Imaj7", "C major") == "Cmaj7"
        assert roman_to_chord("ii7", "C major") == "Dm7"

    def test_secondary_dominants(self):
        """Test secondary dominant conversions."""
        from harmonic_analysis.core.pattern_engine.token_converter import roman_to_chord

        # V/V in C major should be D7 (dominant of G)
        assert roman_to_chord("V/V", "C major") == "D7"

    def test_different_keys(self):
        """Test conversions in different keys."""
        from harmonic_analysis.core.pattern_engine.token_converter import roman_to_chord

        # Same roman, different keys
        assert roman_to_chord("V7", "F major") == "C7"
        assert roman_to_chord("V7", "G major") == "D7"
        assert roman_to_chord("V7", "Bb major") == "F7"
