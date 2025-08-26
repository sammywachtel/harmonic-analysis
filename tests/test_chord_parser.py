"""
Tests for Chord Parser

Tests comprehensive chord parsing and detection including:
- Complex chord symbol parsing
- MIDI note chord detection
- Partial chord handling
- Suspended and add chords
- Inversion detection
"""

from harmonic_analysis import (
    ChordParser,
    find_chords_from_midi,
    parse_chord,
    parse_chord_progression,
)


class TestChordParser:
    """Test suite for ChordParser"""

    def setup_method(self):
        """Setup test fixtures"""
        self.parser = ChordParser()

    def test_parse_basic_chord_symbols(self):
        """Test parsing of basic chord symbols"""
        test_cases = [
            ("C", "major", "C"),
            ("Am", "minor", "A"),
            ("G7", "dominant7", "G"),
            ("Dmaj7", "major7", "D"),
            ("Em7", "minor7", "E"),
            ("Bdim", "diminished", "B"),
            ("Faug", "augmented", "F"),
            ("Cm7b5", "half_diminished", "C"),
        ]

        for symbol, expected_quality, expected_root in test_cases:
            result = self.parser.parse_chord_symbol(symbol)
            assert result is not None
            assert result["quality"] == expected_quality
            assert result["root"] == expected_root

    def test_parse_chord_with_extensions(self):
        """Test parsing chords with extensions"""
        result = self.parser.parse_chord_symbol("Cmaj7add9")
        assert result is not None
        assert result["quality"] == "major7"
        assert "9" in result["extensions"] or "add9" in result["extensions"]

    def test_parse_chord_with_inversion(self):
        """Test parsing chords with bass notes (inversions)"""
        result = self.parser.parse_chord_symbol("C/E")
        assert result is not None
        assert result["root"] == "C"
        assert result["bass_note"] == "E"

    def test_parse_suspended_chords(self):
        """Test parsing suspended chords"""
        test_cases = [
            ("Csus2", "sus2"),
            ("Gsus4", "sus4"),
            ("Dsus", "sus4"),  # Default sus to sus4
        ]

        for symbol, expected_quality in test_cases:
            result = self.parser.parse_chord_symbol(symbol)
            assert result is not None
            assert result["quality"] == expected_quality

    def test_find_major_chord_from_midi(self):
        """Test finding major chord from MIDI notes"""
        # C major triad: C(60), E(64), G(67)
        midi_notes = [60, 64, 67]
        matches = self.parser.find_chord_matches(midi_notes)

        assert len(matches) > 0
        best_match = matches[0]
        assert best_match.root_name == "C"
        assert best_match.chord_name == "Major"
        assert best_match.confidence > 0.8

    def test_find_minor_chord_from_midi(self):
        """Test finding minor chord from MIDI notes"""
        # A minor triad: A(69), C(72), E(76)
        midi_notes = [69, 72, 76]
        matches = self.parser.find_chord_matches(midi_notes)

        assert len(matches) > 0
        best_match = matches[0]
        assert best_match.root_name == "A"
        assert best_match.chord_name == "Minor"

    def test_find_seventh_chord_from_midi(self):
        """Test finding seventh chord from MIDI notes"""
        # G7 chord: G(67), B(71), D(74), F(77)
        midi_notes = [67, 71, 74, 77]
        matches = self.parser.find_chord_matches(midi_notes)

        assert len(matches) > 0
        # Look for dominant 7th in matches
        dom7_match = next((m for m in matches if "Dominant 7th" in m.chord_name), None)
        assert dom7_match is not None
        assert dom7_match.root_name == "G"

    def test_detect_chord_inversion(self):
        """Test detection of chord inversions"""
        # C major first inversion: E(64) as bass, G(67), C(72)
        midi_notes = [64, 67, 72]  # E is lowest note
        matches = self.parser.find_chord_matches(midi_notes)

        assert len(matches) > 0
        # Find C major match
        c_major = next(
            (m for m in matches if m.root_name == "C" and "Major" in m.chord_name), None
        )
        assert c_major is not None
        assert c_major.inversion == "/E"  # First inversion

    def test_partial_chord_detection(self):
        """Test detection of partial chords (2-note combinations)"""
        # Power chord: C(60), G(67)
        midi_notes = [60, 67]
        matches = self.parser.find_chord_matches(midi_notes)

        assert len(matches) > 0
        # Look for power chord
        power_chord = next((m for m in matches if "Power" in m.chord_name), None)
        assert power_chord is not None
        assert power_chord.is_partial
        assert power_chord.missing_notes is not None

    def test_sus_chord_detection(self):
        """Test detection of suspended chords"""
        # Csus4: C(60), F(65), G(67)
        midi_notes = [60, 65, 67]
        matches = self.parser.find_chord_matches(midi_notes)

        assert len(matches) > 0
        # Look for sus4 chord
        sus4_match = next((m for m in matches if "sus4" in m.chord_symbol), None)
        assert sus4_match is not None

    def test_add_chord_detection(self):
        """Test detection of add chords"""
        # Am(add4): A(69), C(72), D(74) - minor 3rd + 4th
        midi_notes = [69, 72, 74]
        matches = self.parser.find_chord_matches(midi_notes)

        # Should find minor add4
        add4_match = next(
            (m for m in matches if "add4" in m.chord_symbol.lower()), None
        )
        assert add4_match is not None

    def test_detect_partial_sus_chords(self):
        """Test specialized partial sus chord detection"""
        # A-C#-D pattern (major 3rd + 4th)
        midi_notes = [69, 73, 74]  # A, C#, D
        matches = self.parser.detect_partial_sus_chords(midi_notes)

        assert len(matches) > 0
        sus_match = next((m for m in matches if "sus4" in m.chord_symbol), None)
        assert sus_match is not None
        assert sus_match.is_partial
        assert sus_match.pedagogical_note is not None

    def test_empty_input_handling(self):
        """Test handling of empty or invalid input"""
        # Empty notes
        matches = self.parser.find_chord_matches([])
        assert matches == []

        # Single note
        matches = self.parser.find_chord_matches([60])
        assert matches == []

        # Invalid chord symbol
        result = self.parser.parse_chord_symbol("")
        assert result is None

        result = self.parser.parse_chord_symbol("XYZ")
        assert result is None

    def test_confidence_scoring(self):
        """Test that confidence scoring works correctly"""
        # Perfect major triad should have high confidence
        midi_notes = [60, 64, 67]  # C major
        matches = self.parser.find_chord_matches(midi_notes)

        assert len(matches) > 0
        best_match = matches[0]
        assert best_match.confidence > 0.9

        # Partial chord should have lower confidence
        midi_notes = [60, 64]  # C major without 5th
        matches = self.parser.find_chord_matches(midi_notes)

        assert len(matches) > 0
        partial_match = matches[0]
        assert partial_match.confidence < 0.85
        assert partial_match.is_partial

    def test_pedagogical_notes(self):
        """Test that pedagogical notes are generated"""
        # Power chord
        midi_notes = [60, 67]  # C5
        matches = self.parser.find_chord_matches(midi_notes)

        power_chord = next((m for m in matches if "Power" in m.chord_name), None)
        assert power_chord is not None
        assert power_chord.pedagogical_note is not None
        assert "power" in power_chord.pedagogical_note.lower()

    def test_parse_chord_progression(self):
        """Test parsing chord progression strings"""
        # Test with spaces
        progression = "Am F C G"
        chords = parse_chord_progression(progression)
        assert chords == ["Am", "F", "C", "G"]

        # Test with measure bars
        progression = "Am | F | C | G"
        chords = parse_chord_progression(progression)
        assert chords == ["Am", "F", "C", "G"]

        # Test with commas
        progression = "Am, F, C, G"
        chords = parse_chord_progression(progression)
        assert chords == ["Am", "F", "C", "G"]

    def test_convenience_functions(self):
        """Test convenience functions"""
        # Test find_chords_from_midi
        midi_notes = [60, 64, 67]
        matches = find_chords_from_midi(midi_notes)
        assert len(matches) > 0

        # Test parse_chord
        result = parse_chord("Cmaj7")
        assert result is not None
        assert result["quality"] == "major7"


class TestChordQuality:
    """Test chord quality parsing"""

    def setup_method(self):
        self.parser = ChordParser()

    def test_complex_chord_qualities(self):
        """Test parsing of complex chord qualities"""
        test_cases = [
            ("Cm7b5", "half_diminished"),
            ("C°7", "diminished"),
            ("Cdim7", "diminished7"),
            ("C+", "augmented"),
            ("Cm(maj7)", "minor_major7"),
            ("CmM7", "minor_major7"),
            ("C7+", "augmented7"),
        ]

        for symbol, expected_quality in test_cases:
            result = self.parser.parse_chord_symbol(symbol)
            assert result is not None
            assert result["quality"] == expected_quality


class TestChordPatterns:
    """Test specific chord pattern handling"""

    def setup_method(self):
        self.parser = ChordParser()

    def test_three_note_pattern_disambiguation(self):
        """Test disambiguation of 3-note patterns"""
        # A-C-D pattern (minor 3rd + 4th) - should be Am(add4)
        midi_notes = [69, 72, 74]
        matches = self.parser.find_chord_matches(midi_notes)

        # Check that Am(add4) is preferred over sus interpretations
        best_match = matches[0]
        assert "add4" in best_match.chord_symbol.lower() or "A" in best_match.root_name

        # A-C#-D pattern (major 3rd + 4th) - could be sus4 partial
        midi_notes = [69, 73, 74]
        matches = self.parser.find_chord_matches(midi_notes)

        # Should find some interpretation
        assert len(matches) > 0
