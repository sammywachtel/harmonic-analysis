"""
Tests for chord detection from MIDI pitches.

Comprehensive test coverage for all 36 chord templates including:
- Basic triads (major, minor, diminished, augmented)
- Suspended chords (sus2, sus4) and partial variations
- Seventh chords (maj7, m7, 7, dim7, m7b5, aug7, m(maj7))
- Add chords (add4, madd4)
- Partial chords (no5 variations)
- Inversion detection with slash notation
- Edge cases (empty list, single note, unrecognized patterns)
"""

import pytest

from harmonic_analysis.core.utils.chord_detection import (
    _calculate_confidence,
    detect_chord_from_pitches,
)


class TestBasicTriads:
    """Test detection of basic triads."""

    def test_c_major_triad(self):
        """C major: C-E-G (60, 64, 67)"""
        result = detect_chord_from_pitches([60, 64, 67])
        assert result == "C"

    def test_a_minor_triad(self):
        """A minor: A-C-E (69, 72, 76)"""
        result = detect_chord_from_pitches([69, 72, 76])
        assert result == "Am"

    def test_b_diminished_triad(self):
        """B diminished: B-D-F (71, 74, 77)"""
        result = detect_chord_from_pitches([71, 74, 77])
        assert result == "Bdim"

    def test_c_augmented_triad(self):
        """C augmented: C-E-G# (60, 64, 68)"""
        result = detect_chord_from_pitches([60, 64, 68])
        assert result == "Caug"

    def test_d_major_triad(self):
        """D major: D-F#-A (62, 66, 69)"""
        result = detect_chord_from_pitches([62, 66, 69])
        assert result == "D"

    def test_e_minor_triad(self):
        """E minor: E-G-B (64, 67, 71)"""
        result = detect_chord_from_pitches([64, 67, 71])
        assert result == "Em"


class TestSuspendedChords:
    """Test detection of suspended chords."""

    def test_csus2_complete(self):
        """Csus2: C-D-G (60, 62, 67)"""
        result = detect_chord_from_pitches([60, 62, 67])
        assert result == "Csus2"

    def test_csus4_complete(self):
        """Csus4: C-F-G (60, 65, 67)"""
        result = detect_chord_from_pitches([60, 65, 67])
        assert result == "Csus4"

    def test_asus4_complete(self):
        """Asus4: A-D-E (69, 74, 76)"""
        # Note: This could also be detected as Dsus2/A (enharmonic equivalent)
        result = detect_chord_from_pitches([69, 74, 76])
        assert result in ["Asus4", "Dsus2/A"]  # Both are valid interpretations

    def test_dsus2_partial(self):
        """Dsus2(no5): D-E (62, 64)"""
        result = detect_chord_from_pitches([62, 64])
        assert result == "Dsus2(no5)"

    def test_gsus4_partial(self):
        """Gsus4(no5): G-C (67, 72)"""
        # Note: G-C is a perfect 4th, could be C5/G or Gsus4(no5)
        result = detect_chord_from_pitches([67, 72])
        assert result in ["Gsus4(no5)", "C5/G"]  # Both interpretations valid


class TestSeventhChords:
    """Test detection of seventh chords."""

    def test_cmaj7(self):
        """Cmaj7: C-E-G-B (60, 64, 67, 71)"""
        result = detect_chord_from_pitches([60, 64, 67, 71])
        assert result == "Cmaj7"

    def test_dm7(self):
        """Dm7: D-F-A-C (62, 65, 69, 72)"""
        result = detect_chord_from_pitches([62, 65, 69, 72])
        assert result == "Dm7"

    def test_g7_dominant(self):
        """G7: G-B-D-F (67, 71, 74, 77)"""
        result = detect_chord_from_pitches([67, 71, 74, 77])
        assert result == "G7"

    def test_bdim7(self):
        """Bdim7: B-D-F-Ab (71, 74, 77, 80)"""
        # Note: Diminished 7th chords are symmetrical - could be any root
        result = detect_chord_from_pitches([71, 74, 77, 80])
        assert "dim7" in result  # Accept any root due to symmetry

    def test_bm7b5_half_diminished(self):
        """Bm7b5 (half-diminished): B-D-F-A (71, 74, 77, 81)"""
        result = detect_chord_from_pitches([71, 74, 77, 81])
        assert result == "Bm7b5"

    def test_caug7(self):
        """Caug7: C-E-G#-Bb (60, 64, 68, 70)"""
        result = detect_chord_from_pitches([60, 64, 68, 70])
        assert result == "Caug7"

    def test_cm_maj7(self):
        """Cm(maj7): C-Eb-G-B (60, 63, 67, 71)"""
        result = detect_chord_from_pitches([60, 63, 67, 71])
        assert result == "Cm(maj7)"


class TestPartialChords:
    """Test detection of partial chords (missing 5th or other notes)."""

    def test_c_major_no5(self):
        """C(no5): C-E (60, 64)"""
        result = detect_chord_from_pitches([60, 64])
        assert result == "C(no5)"

    def test_a_minor_no5(self):
        """Am(no5): A-C (69, 72)"""
        result = detect_chord_from_pitches([69, 72])
        assert result == "Am(no5)"

    def test_power_chord(self):
        """C5 (power chord): C-G (60, 67)"""
        result = detect_chord_from_pitches([60, 67])
        assert result == "C5"

    def test_g7_no_fifth(self):
        """G7(no5): G-B-F (67, 71, 77)"""
        result = detect_chord_from_pitches([67, 71, 77])
        assert result == "G7(no5)"

    def test_am7_no_fifth(self):
        """Am7(no5): A-C-G (69, 72, 79)"""
        result = detect_chord_from_pitches([69, 72, 79])
        assert result == "Am7(no5)"

    def test_cmaj7_no_fifth(self):
        """Cmaj7(no5): C-E-B (60, 64, 71)"""
        result = detect_chord_from_pitches([60, 64, 71])
        assert result == "Cmaj7(no5)"


class TestAddChords:
    """Test detection of add chords (retaining 3rd + added note)."""

    def test_cadd4(self):
        """Cadd4: C-E-F (60, 64, 65)"""
        result = detect_chord_from_pitches([60, 64, 65])
        assert result == "Cadd4"

    def test_amadd4(self):
        """Amadd4: A-C-D (69, 72, 74)"""
        result = detect_chord_from_pitches([69, 72, 74])
        assert result == "Amadd4"


class TestSusExtensions:
    """Test detection of sus chords with extensions."""

    def test_csus2_add7(self):
        """Csus2(add7): C-D-Bb (60, 62, 70)"""
        result = detect_chord_from_pitches([60, 62, 70])
        assert result == "Csus2(add7)"

    def test_gsus4_add7(self):
        """Gsus4(add7): G-C-F (67, 72, 77)"""
        # Note: G-C-F could be Csus4/G or Gsus4(add7)
        result = detect_chord_from_pitches([67, 72, 77])
        assert result in ["Gsus4(add7)", "Csus4/G"]  # Both valid


class TestInversions:
    """Test detection of chord inversions with slash notation."""

    def test_c_major_first_inversion(self):
        """C/E (first inversion): E-G-C (64, 67, 72)"""
        result = detect_chord_from_pitches([64, 67, 72])
        assert result == "C/E"

    def test_c_major_second_inversion(self):
        """C/G (second inversion): G-C-E (67, 72, 76)"""
        result = detect_chord_from_pitches([67, 72, 76])
        assert result == "C/G"

    def test_am_first_inversion(self):
        """Am/C (first inversion): C-E-A (72, 76, 81)"""
        result = detect_chord_from_pitches([72, 76, 81])
        assert result == "Am/C"  # Should detect minor quality

    def test_fsharp_m7b5_first_inversion(self):
        """F#m7b5/A (first inversion): A-C-E-F# (69, 72, 76, 78)"""
        result = detect_chord_from_pitches([69, 72, 76, 78])
        # Should detect F#m7b5 with A in bass
        assert result == "F#m7b5/A"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_single_note(self):
        """Single note returns Unknown"""
        result = detect_chord_from_pitches([60])
        assert result == "Unknown"

    def test_empty_list(self):
        """Empty list returns Unknown"""
        result = detect_chord_from_pitches([])
        assert result == "Unknown"

    def test_unrecognized_interval_pattern(self):
        """Unusual interval pattern might return Unknown or best guess"""
        # Two notes a tritone apart (not in templates)
        result = detect_chord_from_pitches([60, 66])
        # Should still detect something (power chord or partial)
        assert result != ""


class TestConfidenceScoring:
    """Test confidence scoring logic."""

    def test_exact_match_gets_bonus(self):
        """Exact match should get confidence bonus"""
        # Template: [0, 4, 7], played: [0, 4, 7]
        confidence = _calculate_confidence([0, 4, 7], [0, 4, 7], 3, 1.0)
        assert confidence == 1.0  # Base 1.0 + 0.1 bonus = 1.1, clamped to 1.0

    def test_extra_notes_penalized(self):
        """Extra notes reduce confidence"""
        # Template: [0, 4, 7], played: [0, 4, 7, 10, 11]
        # 2 extra notes = 2 * 0.08 = 0.16 penalty
        confidence = _calculate_confidence([0, 4, 7, 10, 11], [0, 4, 7], 5, 1.0)
        assert confidence == pytest.approx(0.84, abs=0.01)

    def test_partial_chord_base_confidence(self):
        """Partial chords start with lower base confidence"""
        # Partial chord with base confidence 0.7
        confidence = _calculate_confidence([0, 4], [0, 4], 2, 0.7)
        # Base 0.7 + 0.1 exact match bonus = 0.8
        assert confidence == pytest.approx(0.8, abs=0.01)

    def test_confidence_clamped_to_valid_range(self):
        """Confidence is clamped between 0.0 and 1.0"""
        # High penalty should clamp to 0
        confidence = _calculate_confidence([0, 1, 2, 3, 4, 5, 6, 7, 8], [0], 9, 0.5)
        assert 0.0 <= confidence <= 1.0

        # High bonus should clamp to 1.0
        confidence = _calculate_confidence([0], [0], 1, 1.0)
        assert confidence == 1.0


class TestComplexRealWorldChords:
    """Test realistic complex chord voicings."""

    def test_jazz_voicing_cmaj7(self):
        """Jazz voicing with doubled notes: Cmaj7 (60, 64, 67, 71, 76)"""
        result = detect_chord_from_pitches([60, 64, 67, 71, 76])
        # Should detect Cmaj7 even with extra E
        assert "maj7" in result

    def test_piano_voicing_with_octaves(self):
        """Piano voicing with octave doubling: C (48, 60, 64, 67)"""
        result = detect_chord_from_pitches([48, 60, 64, 67])
        # Should detect C major (pitch classes collapse octaves)
        assert result in ["C", "C/C"]

    def test_sus4_with_third(self):
        """Sus4 with 3rd (4-note voicing): C-E-F-G (60, 64, 65, 67)"""
        result = detect_chord_from_pitches([60, 64, 65, 67])
        # Should detect sus4 template with 3rd
        assert result == "Csus4"
