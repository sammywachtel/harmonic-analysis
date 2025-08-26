"""
Unit tests for chord parsing and logic.
"""

import pytest

from harmonic_analysis.types import ChordFunction
from harmonic_analysis.utils.chord_logic import (
    ChordMatch,
    ChordParser,
    determine_chord_function,
    find_chord_matches,
    parse_chord_progression,
)


class TestChordParser:
    """Test chord symbol parsing."""

    def test_parse_basic_major_chord(self):
        """Test parsing basic major chord."""
        parser = ChordParser()
        result = parser.parse_chord("C")

        assert result.chord_symbol == "C"
        assert result.root == "C"
        assert result.root_pitch == 0
        assert result.quality == "major"
        assert result.bass_note is None
        assert result.inversion == 0

    def test_parse_minor_chord(self):
        """Test parsing minor chord."""
        parser = ChordParser()
        result = parser.parse_chord("Dm")

        assert result.chord_symbol == "Dm"
        assert result.root == "D"
        assert result.root_pitch == 2
        assert result.quality == "minor"

    def test_parse_diminished_chord(self):
        """Test parsing diminished chord."""
        parser = ChordParser()
        result = parser.parse_chord("F#dim")

        assert result.chord_symbol == "F#dim"
        assert result.root == "F#"
        assert result.root_pitch == 6
        assert result.quality == "diminished"

    def test_parse_slash_chord(self):
        """Test parsing slash chord (inversion)."""
        parser = ChordParser()
        result = parser.parse_chord("C/E")

        assert result.chord_symbol == "C/E"
        assert result.root == "C"
        assert result.bass_note == "E"
        assert result.bass_pitch == 4
        assert result.inversion == 1

    def test_parse_invalid_chord_raises_error(self):
        """Test that invalid chord symbols raise errors."""
        parser = ChordParser()

        with pytest.raises(ValueError):
            parser.parse_chord("")

        with pytest.raises(ValueError):
            parser.parse_chord("XYZ")


class TestChordProgression:
    """Test chord progression parsing."""

    def test_parse_simple_progression(self):
        """Test parsing simple chord progression."""
        result = parse_chord_progression("C F G C")
        assert result == ["C", "F", "G", "C"]

    def test_parse_progression_with_pipes(self):
        """Test parsing progression with pipe separators."""
        result = parse_chord_progression("C | F | G | C")
        assert result == ["C", "F", "G", "C"]

    def test_parse_progression_mixed_separators(self):
        """Test parsing with mixed separators."""
        result = parse_chord_progression("C F | G C")
        assert result == ["C", "F", "G", "C"]

    def test_empty_progression_raises_error(self):
        """Test that empty progression raises error."""
        with pytest.raises(ValueError):
            parse_chord_progression("")

        with pytest.raises(ValueError):
            parse_chord_progression("   ")


class TestChordFunction:
    """Test chord function determination."""

    def test_tonic_function_in_c_major(self):
        """Test tonic function identification in C major."""
        chord_match = ChordMatch(
            chord_symbol="C", root="C", root_pitch=0, quality="major"
        )

        function = determine_chord_function(chord_match, "C", "major")
        assert function == ChordFunction.TONIC

    def test_dominant_function_in_c_major(self):
        """Test dominant function identification in C major."""
        chord_match = ChordMatch(
            chord_symbol="G", root="G", root_pitch=7, quality="major"
        )

        function = determine_chord_function(chord_match, "C", "major")
        assert function == ChordFunction.DOMINANT

    def test_subdominant_function_in_c_major(self):
        """Test subdominant function identification in C major."""
        chord_match = ChordMatch(
            chord_symbol="F", root="F", root_pitch=5, quality="major"
        )

        function = determine_chord_function(chord_match, "C", "major")
        assert function == ChordFunction.SUBDOMINANT


class TestFindChordMatches:
    """Test finding chord matches from symbols."""

    def test_find_matches_for_progression(self):
        """Test finding matches for chord progression."""
        chord_symbols = ["C", "Am", "F", "G"]
        matches = find_chord_matches(chord_symbols)

        assert len(matches) == 4
        assert matches[0].root == "C"
        assert matches[1].root == "A"
        assert matches[2].root == "F"
        assert matches[3].root == "G"

    def test_find_matches_handles_invalid_chords(self):
        """Test that invalid chords are handled gracefully."""
        chord_symbols = ["C", "InvalidChord", "F"]
        matches = find_chord_matches(chord_symbols)

        assert len(matches) == 3
        # Invalid chord should still create a match object
        assert matches[1].chord_symbol == "InvalidChord"
