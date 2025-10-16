"""
Test suite for key signature conversion utilities.

Tests both conversion directions:
1. convert_key_signature_to_mode() - sharps/flats → key name
2. parse_key_signature_from_hint() - key name → sharps/flats

Covers all 30 major/minor keys (15 major + 15 minor) with comprehensive edge cases.
"""

import pytest

from harmonic_analysis.core.utils.key_signature import (
    convert_key_signature_to_mode,
    parse_key_signature_from_hint,
)


# ============================================================================
# Test convert_key_signature_to_mode() - Sharps/Flats → Key Name
# ============================================================================


class TestConvertKeySignatureToMode:
    """Test conversion from sharps/flats to key names."""

    # Opening move: Test all 15 major keys (0 to ±7 sharps/flats)
    def test_all_major_keys(self):
        """Test all major keys from circle of fifths."""
        major_keys = [
            (-7, "Cb major"),
            (-6, "Gb major"),
            (-5, "Db major"),
            (-4, "Ab major"),
            (-3, "Eb major"),
            (-2, "Bb major"),
            (-1, "F major"),
            (0, "C major"),
            (1, "G major"),
            (2, "D major"),
            (3, "A major"),
            (4, "E major"),
            (5, "B major"),
            (6, "F# major"),
            (7, "C# major"),
        ]

        for sharps_flats, expected_key in major_keys:
            result = convert_key_signature_to_mode(sharps_flats, prefer_minor=False)
            assert result == expected_key, (
                f"Expected {expected_key} for {sharps_flats} sharps/flats, "
                f"got {result}"
            )

    # Main play: Test all 15 minor keys (0 to ±7 sharps/flats)
    def test_all_minor_keys(self):
        """Test all minor keys (relative minors)."""
        minor_keys = [
            (-7, "Ab minor"),
            (-6, "Eb minor"),
            (-5, "Bb minor"),
            (-4, "F minor"),
            (-3, "C minor"),
            (-2, "G minor"),
            (-1, "D minor"),
            (0, "A minor"),
            (1, "E minor"),
            (2, "B minor"),
            (3, "F# minor"),
            (4, "C# minor"),
            (5, "G# minor"),
            (6, "D# minor"),
            (7, "A# minor"),
        ]

        for sharps_flats, expected_key in minor_keys:
            result = convert_key_signature_to_mode(sharps_flats, prefer_minor=True)
            assert result == expected_key, (
                f"Expected {expected_key} for {sharps_flats} sharps/flats, "
                f"got {result}"
            )

    # Edge cases: Invalid key signatures
    def test_out_of_range_sharps(self):
        """Test handling of excessive sharps (>7)."""
        result = convert_key_signature_to_mode(10, prefer_minor=False)
        assert result == "C major"  # Fallback to C major

    def test_out_of_range_flats(self):
        """Test handling of excessive flats (<-7)."""
        result = convert_key_signature_to_mode(-10, prefer_minor=False)
        assert result == "C major"  # Fallback to C major

    def test_out_of_range_minor_fallback(self):
        """Test fallback to A minor for invalid input when prefer_minor=True."""
        result = convert_key_signature_to_mode(99, prefer_minor=True)
        assert result == "A minor"  # Fallback to A minor

    # Tricky bit: Verify major/minor preference flag works correctly
    def test_prefer_minor_flag(self):
        """Test that prefer_minor flag switches between major and relative minor."""
        # 2 sharps = D major or B minor
        assert convert_key_signature_to_mode(2, prefer_minor=False) == "D major"
        assert convert_key_signature_to_mode(2, prefer_minor=True) == "B minor"

        # -2 flats = Bb major or G minor
        assert convert_key_signature_to_mode(-2, prefer_minor=False) == "Bb major"
        assert convert_key_signature_to_mode(-2, prefer_minor=True) == "G minor"

        # 0 = C major or A minor
        assert convert_key_signature_to_mode(0, prefer_minor=False) == "C major"
        assert convert_key_signature_to_mode(0, prefer_minor=True) == "A minor"


# ============================================================================
# Test parse_key_signature_from_hint() - Key Name → Sharps/Flats
# ============================================================================


class TestParseKeySignatureFromHint:
    """Test parsing key names to sharps/flats counts."""

    # Opening move: Test all 15 major keys
    def test_all_major_key_names(self):
        """Test parsing all major key names."""
        major_keys = [
            ("C major", 0),
            ("G major", 1),
            ("D major", 2),
            ("A major", 3),
            ("E major", 4),
            ("B major", 5),
            ("F# major", 6),
            ("C# major", 7),
            ("F major", -1),
            ("Bb major", -2),
            ("Eb major", -3),
            ("Ab major", -4),
            ("Db major", -5),
            ("Gb major", -6),
            ("Cb major", -7),
        ]

        for key_name, expected_sharps_flats in major_keys:
            result = parse_key_signature_from_hint(key_name)
            assert result == expected_sharps_flats, (
                f"Expected {expected_sharps_flats} for '{key_name}', got {result}"
            )

    # Main play: Test all 15 minor keys
    def test_all_minor_key_names(self):
        """Test parsing all minor key names."""
        minor_keys = [
            ("A minor", 0),
            ("E minor", 1),
            ("B minor", 2),
            ("F# minor", 3),
            ("C# minor", 4),
            ("G# minor", 5),
            ("D# minor", 6),
            ("A# minor", 7),
            ("D minor", -1),
            ("G minor", -2),
            ("C minor", -3),
            ("F minor", -4),
            ("Bb minor", -5),
            ("Eb minor", -6),
            ("Ab minor", -7),
        ]

        for key_name, expected_sharps_flats in minor_keys:
            result = parse_key_signature_from_hint(key_name)
            assert result == expected_sharps_flats, (
                f"Expected {expected_sharps_flats} for '{key_name}', got {result}"
            )

    # Tricky bit: Test explicit sharp/flat count patterns
    def test_explicit_sharp_count(self):
        """Test parsing explicit sharp counts like '2 sharps'."""
        assert parse_key_signature_from_hint("2 sharps") == 2
        assert parse_key_signature_from_hint("5 sharps") == 5
        assert parse_key_signature_from_hint("1 sharp") == 1

    def test_explicit_flat_count(self):
        """Test parsing explicit flat counts like '3 flats'."""
        assert parse_key_signature_from_hint("3 flats") == -3
        assert parse_key_signature_from_hint("2 flats") == -2
        assert parse_key_signature_from_hint("1 flat") == -1

    # Edge cases: Case insensitivity
    def test_case_insensitive_major(self):
        """Test case-insensitive parsing for major keys."""
        assert parse_key_signature_from_hint("D MAJOR") == 2
        assert parse_key_signature_from_hint("d major") == 2
        assert parse_key_signature_from_hint("D Major") == 2

    def test_case_insensitive_minor(self):
        """Test case-insensitive parsing for minor keys."""
        assert parse_key_signature_from_hint("B MINOR") == 2
        assert parse_key_signature_from_hint("b minor") == 2
        assert parse_key_signature_from_hint("B Minor") == 2

    # Edge cases: Empty and invalid input
    def test_empty_string(self):
        """Test handling of empty string."""
        assert parse_key_signature_from_hint("") == 0

    def test_none_input(self):
        """Test handling of None input (falsy value)."""
        assert parse_key_signature_from_hint(None) == 0  # type: ignore

    def test_invalid_key_name(self):
        """Test handling of invalid key name."""
        assert parse_key_signature_from_hint("Z major") == 0
        assert parse_key_signature_from_hint("Invalid") == 0

    def test_malformed_sharp_count(self):
        """Test handling of malformed sharp count."""
        assert parse_key_signature_from_hint("sharps") == 0  # No number
        assert parse_key_signature_from_hint("sharp abc") == 0  # No digits

    def test_malformed_flat_count(self):
        """Test handling of malformed flat count."""
        assert parse_key_signature_from_hint("flats") == 0  # No number
        assert parse_key_signature_from_hint("flat xyz") == 0  # No digits


# ============================================================================
# Test Round-Trip Behavior
# ============================================================================


class TestRoundTripConversion:
    """Test that conversions work correctly in both directions."""

    # Victory lap: Test round-trip for all major keys
    def test_round_trip_all_major_keys(self):
        """Test parse → convert matches original for all major keys."""
        major_keys = [
            "C major",
            "G major",
            "D major",
            "A major",
            "E major",
            "B major",
            "F# major",
            "C# major",
            "F major",
            "Bb major",
            "Eb major",
            "Ab major",
            "Db major",
            "Gb major",
            "Cb major",
        ]

        for original_key in major_keys:
            # Parse key name to sharps/flats
            sharps_flats = parse_key_signature_from_hint(original_key)
            # Convert back to key name
            reconstructed_key = convert_key_signature_to_mode(
                sharps_flats, prefer_minor=False
            )
            # Should match original
            assert reconstructed_key == original_key, (
                f"Round-trip failed for {original_key}: "
                f"parsed to {sharps_flats}, converted back to {reconstructed_key}"
            )

    # Victory lap: Test round-trip for all minor keys
    def test_round_trip_all_minor_keys(self):
        """Test parse → convert matches original for all minor keys."""
        minor_keys = [
            "A minor",
            "E minor",
            "B minor",
            "F# minor",
            "C# minor",
            "G# minor",
            "D# minor",
            "A# minor",
            "D minor",
            "G minor",
            "C minor",
            "F minor",
            "Bb minor",
            "Eb minor",
            "Ab minor",
        ]

        for original_key in minor_keys:
            # Parse key name to sharps/flats
            sharps_flats = parse_key_signature_from_hint(original_key)
            # Convert back to key name
            reconstructed_key = convert_key_signature_to_mode(
                sharps_flats, prefer_minor=True
            )
            # Should match original
            assert reconstructed_key == original_key, (
                f"Round-trip failed for {original_key}: "
                f"parsed to {sharps_flats}, converted back to {reconstructed_key}"
            )

    # Tricky bit: Test relative major/minor relationships
    def test_relative_major_minor_pairs(self):
        """Test that major and minor keys with same signature are correctly related."""
        pairs = [
            (0, "C major", "A minor"),
            (2, "D major", "B minor"),
            (-2, "Bb major", "G minor"),
            (3, "A major", "F# minor"),
            (-3, "Eb major", "C minor"),
        ]

        for sharps_flats, major_key, minor_key in pairs:
            # Same signature should produce relative major/minor pair
            assert convert_key_signature_to_mode(sharps_flats, False) == major_key
            assert convert_key_signature_to_mode(sharps_flats, True) == minor_key

            # Parsing both should produce same sharps/flats count
            assert parse_key_signature_from_hint(major_key) == sharps_flats
            assert parse_key_signature_from_hint(minor_key) == sharps_flats


# ============================================================================
# Test Integration with MusicXML/MIDI Use Cases
# ============================================================================


class TestMusicXMLMIDIIntegration:
    """Test realistic scenarios from MusicXML/MIDI file processing."""

    def test_midi_ambiguous_key_signature(self):
        """
        Test scenario: MIDI file has 2 sharps. User can choose major or minor.

        This simulates the demo's key mode preference feature where
        users select "Major" or "Minor" preference for ambiguous keys.
        """
        # MIDI file has 2 sharps - could be D major or B minor
        sharps_flats = 2

        # User prefers major - should get D major
        major_result = convert_key_signature_to_mode(sharps_flats, prefer_minor=False)
        assert major_result == "D major"

        # User prefers minor - should get B minor
        minor_result = convert_key_signature_to_mode(sharps_flats, prefer_minor=True)
        assert minor_result == "B minor"

    def test_musicxml_key_hint_parsing(self):
        """
        Test scenario: MusicXML file contains key hint that needs parsing.

        MusicXML files may include key signatures in various formats.
        """
        # Common MusicXML key hint formats
        assert parse_key_signature_from_hint("D major") == 2
        assert parse_key_signature_from_hint("B minor") == 2
        assert parse_key_signature_from_hint("Bb major") == -2

        # Should handle case variations
        assert parse_key_signature_from_hint("d major") == 2
        assert parse_key_signature_from_hint("D MAJOR") == 2

    def test_no_key_signature_fallback(self):
        """Test handling when no key signature is detected (defaults to C/Am)."""
        # Empty or invalid key hints should return 0 (C major/A minor)
        assert parse_key_signature_from_hint("") == 0
        assert parse_key_signature_from_hint("Unknown") == 0

        # Converting 0 should give C major or A minor
        assert convert_key_signature_to_mode(0, prefer_minor=False) == "C major"
        assert convert_key_signature_to_mode(0, prefer_minor=True) == "A minor"

    def test_enharmonic_equivalents(self):
        """
        Test enharmonic spellings.

        Note: The library uses specific enharmonic spellings based on
        circle of fifths convention (F# for 6 sharps, Gb for 6 flats).
        """
        # 6 sharps = F# major (not Gb major)
        assert convert_key_signature_to_mode(6, prefer_minor=False) == "F# major"

        # -6 flats = Gb major (not F# major)
        assert convert_key_signature_to_mode(-6, prefer_minor=False) == "Gb major"

        # Both are enharmonically equivalent but have different representations
        # This is correct music theory - the spelling depends on context
