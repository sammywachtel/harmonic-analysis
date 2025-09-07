"""
Regression tests for chord inversion analysis across all architectural levels.

Tests the complete pipeline from chord symbols through analysis to Roman numerals
and back to chord symbols, ensuring inversion notation is consistent throughout.

Focus progression: "D Gm/Bb D/A Gm F/C C F" in F major
Expected result: "V/ii - ii⁶ - V/ii⁶⁴ - ii - I⁶⁴ - V - I"
"""

import asyncio

from harmonic_analysis import (
    AnalysisOptions,
    analyze_chord_progression,
    analyze_progression_multiple,
)
from harmonic_analysis.utils.chord_inversions import (
    analyze_chord_inversion,
    get_bass_pitch_from_slash_chord,
)
from harmonic_analysis.utils.chord_logic import ChordParser
from harmonic_analysis.utils.roman_numeral_converter import (
    convert_roman_numerals_to_chords,
    is_roman_numeral_progression,
)
from harmonic_analysis.utils.scales import NOTE_TO_PITCH_CLASS


class TestInversionRegression:
    """Comprehensive regression tests for inversion analysis."""

    # Reference data for F major progression
    CHORD_PROGRESSION = ["D", "Gm/Bb", "D/A", "Gm", "F/C", "C", "F"]
    PARENT_KEY = "F major"
    EXPECTED_FUNCTIONAL_ROMANS = ["V/ii", "ii⁶", "V/ii⁶⁴", "ii", "I⁶⁴", "V", "I"]

    # Detailed inversion expectations
    CHORD_INVERSION_DETAILS = [
        ("D", None, 0, ""),  # Root position
        ("Gm/Bb", 10, 1, "⁶"),  # First inversion (Bb is minor third of Gm)
        ("D/A", 9, 2, "⁶⁴"),  # Second inversion (A is fifth of D)
        ("Gm", None, 0, ""),  # Root position
        ("F/C", 0, 2, "⁶⁴"),  # Second inversion (C is fifth of F)
        ("C", None, 0, ""),  # Root position
        ("F", None, 0, ""),  # Root position
    ]

    def test_level_1_chord_inversion_utility(self):
        """Test Level 1: Low-level chord inversion utility functions."""
        for (
            chord_symbol,
            expected_bass_pitch,
            expected_inversion,
            expected_figured_bass,
        ) in self.CHORD_INVERSION_DETAILS:
            # Test each chord individually
            # Extract bass pitch if slash chord
            bass_pitch = get_bass_pitch_from_slash_chord(
                chord_symbol, NOTE_TO_PITCH_CLASS
            )
            assert (
                bass_pitch == expected_bass_pitch
            ), f"Bass pitch mismatch for {chord_symbol}"

            if bass_pitch is not None:
                # Get root pitch for inversion analysis
                root_note = chord_symbol.split("/")[0].rstrip("m7")
                root_pitch = NOTE_TO_PITCH_CLASS.get(root_note)

                # Test centralized inversion analysis
                inversion_result = analyze_chord_inversion(
                    root_pitch, bass_pitch, chord_symbol
                )

                assert (
                    inversion_result["inversion"] == expected_inversion
                ), f"Inversion number mismatch for {chord_symbol}"
                assert (
                    inversion_result["figured_bass"] == expected_figured_bass
                ), f"Figured bass mismatch for {chord_symbol}"

    def test_level_2_chord_parser(self):
        """Test Level 2: Chord parsing with inversion detection."""
        parser = ChordParser()

        for (
            chord_symbol,
            expected_bass_pitch,
            expected_inversion,
            _,
        ) in self.CHORD_INVERSION_DETAILS:
            # Test each chord individually
            match = parser.parse_chord(chord_symbol)

            assert match.chord_symbol == chord_symbol
            assert (
                match.bass_pitch == expected_bass_pitch
            ), f"Chord parser bass pitch mismatch for {chord_symbol}"
            assert (
                match.inversion == expected_inversion
            ), f"Chord parser inversion mismatch for {chord_symbol}"

    def test_level_3_high_level_analysis_api(self):
        """Test Level 3: High-level API with full analysis pipeline."""
        # Test single interpretation analysis
        options = AnalysisOptions(parent_key=self.PARENT_KEY)
        result = asyncio.run(
            analyze_chord_progression(self.CHORD_PROGRESSION, options=options)
        )

        # Check that we get Roman numerals with inversions from primary analysis
        assert hasattr(result.primary_analysis, "roman_numerals")
        assert len(result.primary_analysis.roman_numerals) == len(
            self.CHORD_PROGRESSION
        )

        # Check for presence of inversion notation in results
        roman_str = " - ".join(result.primary_analysis.roman_numerals)
        assert "⁶" in roman_str, "Should contain first inversion notation"
        assert "⁶⁴" in roman_str, "Should contain second inversion notation"

    def test_level_3_multiple_interpretation_api(self):
        """Test Level 3: Multiple interpretation API with confidence scoring."""
        options = AnalysisOptions(parent_key=self.PARENT_KEY, max_alternatives=3)
        result = asyncio.run(
            analyze_progression_multiple(self.CHORD_PROGRESSION, options=options)
        )

        # Check primary analysis
        assert result.primary_analysis is not None
        assert hasattr(result.primary_analysis, "roman_numerals")

        # Check for any analysis with inversions (primary or alternatives)
        found_analysis_with_inversions = False
        for analysis in [result.primary_analysis] + result.alternative_analyses:
            romans_str = " - ".join(analysis.roman_numerals)

            # Check if this analysis has the expected inversions
            if (
                "ii⁶" in romans_str
                and "⁶⁴" in romans_str
                and "V/ii⁶⁴" in romans_str
                and "I⁶⁴" in romans_str
            ):
                found_analysis_with_inversions = True
                # Verify specific inversion expectations
                assert "ii⁶" in romans_str, "Should contain ii⁶ (Gm/Bb)"
                assert "⁶⁴" in romans_str, "Should contain ⁶⁴ inversions"
                assert "V/ii⁶⁴" in romans_str, "Should contain V/ii⁶⁴ (D/A)"
                assert "I⁶⁴" in romans_str, "Should contain I⁶⁴ (F/C)"
                break

        assert found_analysis_with_inversions, "Should include analysis with inversions"

    def test_level_4_bidirectional_conversion(self):
        """Test Level 4: Bidirectional conversion (chords → romans → chords)."""
        # Forward: Chords to Roman numerals
        options = AnalysisOptions(parent_key=self.PARENT_KEY)
        analysis_result = asyncio.run(
            analyze_progression_multiple(self.CHORD_PROGRESSION, options=options)
        )

        # Find analysis with inversions (primary should have them)
        analysis_with_inversions = analysis_result.primary_analysis
        romans_str = " - ".join(analysis_with_inversions.roman_numerals)

        # Verify it has the expected inversions
        assert (
            "ii⁶" in romans_str and "⁶⁴" in romans_str
        ), "Primary analysis should have inversions"

        # Extract Roman numerals
        roman_numerals = analysis_with_inversions.roman_numerals
        assert len(roman_numerals) > 0, "Should have Roman numerals"

        # Backward: Roman numerals to chords
        romans_str = " ".join(roman_numerals)  # Convert to space-separated string
        reconstructed_chords = convert_roman_numerals_to_chords(
            romans_str, parent_key="F major"
        )

        assert len(reconstructed_chords) == len(self.CHORD_PROGRESSION)

        # Verify specific inversion reconstructions
        for i, (original_chord, reconstructed_chord) in enumerate(
            zip(self.CHORD_PROGRESSION, reconstructed_chords)
        ):
            if "/" in original_chord:  # Slash chord should remain slash chord
                assert (
                    "/" in reconstructed_chord
                ), f"Inversion lost in reconstruction: {original_chord} -> {reconstructed_chord}"

            # Test that essential chord identity is preserved
            original_root = original_chord.split("/")[0]
            reconstructed_root = reconstructed_chord.split("/")[0]
            assert (
                original_root == reconstructed_root
            ), f"Root changed in reconstruction: {original_chord} -> {reconstructed_chord}"

    def test_confidence_and_metadata_validation(self):
        """Test that analysis includes confidence scores and metadata for inversion detection."""
        options = AnalysisOptions(parent_key=self.PARENT_KEY)
        result = asyncio.run(
            analyze_progression_multiple(self.CHORD_PROGRESSION, options=options)
        )

        # Check metadata is present
        assert hasattr(result, "metadata")
        assert hasattr(result.metadata, "total_interpretations_considered")
        assert hasattr(result.metadata, "analysis_time_ms")

        # Check confidence scoring
        assert hasattr(result.primary_analysis, "confidence")
        assert 0.0 <= result.primary_analysis.confidence <= 1.0

        # Check that alternative analyses have confidence scores
        for alt_analysis in result.alternative_analyses:
            assert hasattr(alt_analysis, "confidence")
            assert 0.0 <= alt_analysis.confidence <= 1.0

    def test_roman_numeral_detection(self):
        """Test Roman numeral string detection for bidirectional testing."""
        # Test positive cases
        roman_examples = [
            "I - V - vi - IV",
            "V/ii⁶ - ii⁶⁴ - V - I",
            "I⁶⁴ - V - I",
        ]

        for roman_string in roman_examples:
            assert is_roman_numeral_progression(
                roman_string
            ), f"Should detect as Roman numerals: {roman_string}"

        # Test negative cases
        chord_examples = [
            "C - F - G - Am",
            "D/A - Gm/Bb - F/C",
            "Cmaj7 - Fmaj7 - G7",
        ]

        for chord_string in chord_examples:
            assert not is_roman_numeral_progression(
                chord_string
            ), f"Should NOT detect as Roman numerals: {chord_string}"

    def test_inversion_consistency_across_modes(self):
        """Test that inversion notation is consistent between functional and modal analyses."""
        options = AnalysisOptions(
            parent_key=self.PARENT_KEY, max_alternatives=5  # Get more alternatives
        )
        result = asyncio.run(
            analyze_progression_multiple(self.CHORD_PROGRESSION, options=options)
        )

        # Collect all Roman numeral results
        all_roman_results = []

        # Primary analysis
        if hasattr(result.primary_analysis, "roman_numerals"):
            all_roman_results.append(result.primary_analysis.roman_numerals)

        # Alternative analyses
        for alt in result.alternative_analyses:
            if hasattr(alt, "roman_numerals"):
                all_roman_results.append(alt.roman_numerals)

        # Check that inversion notation appears consistently
        # (The same chord should have same inversion notation across different analyses)
        inversion_positions = [1, 2, 4]  # Positions with inversions: Gm/Bb, D/A, F/C

        for pos in inversion_positions:
            inversion_notations = []
            for romans in all_roman_results:
                if pos < len(romans):
                    roman = romans[pos]
                    # Extract inversion notation
                    if "⁶⁴" in roman:
                        inversion_notations.append("⁶⁴")
                    elif "⁶" in roman:
                        inversion_notations.append("⁶")
                    else:
                        inversion_notations.append("")

            # All non-empty notations should be the same
            non_empty_notations = [n for n in inversion_notations if n]
            if len(non_empty_notations) > 1:
                assert all(
                    n == non_empty_notations[0] for n in non_empty_notations
                ), f"Inconsistent inversion notation at position {pos}: {non_empty_notations}"


# Individual test functions for pytest discovery
def test_low_level_chord_inversion_utility():
    """Test low-level chord inversion utility functions."""
    test_instance = TestInversionRegression()
    test_instance.test_level_1_chord_inversion_utility()


def test_chord_parser_integration():
    """Test chord parser with inversion detection."""
    test_instance = TestInversionRegression()
    test_instance.test_level_2_chord_parser()


def test_high_level_analysis_api():
    """Test high-level API with full analysis pipeline."""
    test_instance = TestInversionRegression()
    test_instance.test_level_3_high_level_analysis_api()


def test_multiple_interpretation_api():
    """Test multiple interpretation API with confidence scoring."""
    test_instance = TestInversionRegression()
    test_instance.test_level_3_multiple_interpretation_api()


def test_bidirectional_conversion():
    """Test bidirectional conversion (chords → romans → chords)."""
    test_instance = TestInversionRegression()
    test_instance.test_level_4_bidirectional_conversion()


def test_confidence_and_metadata():
    """Test confidence scores and metadata validation."""
    test_instance = TestInversionRegression()
    test_instance.test_confidence_and_metadata_validation()


def test_roman_numeral_detection():
    """Test Roman numeral string detection."""
    test_instance = TestInversionRegression()
    test_instance.test_roman_numeral_detection()


def test_inversion_consistency():
    """Test inversion notation consistency across analysis types."""
    test_instance = TestInversionRegression()
    test_instance.test_inversion_consistency_across_modes()


if __name__ == "__main__":
    # Run tests when executed directly
    import sys

    test_instance = TestInversionRegression()

    print("🎯 Running comprehensive inversion regression tests...")
    print("=" * 60)

    tests = [
        (
            "Level 1: Chord Inversion Utilities",
            test_instance.test_level_1_chord_inversion_utility,
        ),
        ("Level 2: Chord Parser Integration", test_instance.test_level_2_chord_parser),
        (
            "Level 3: High-Level Analysis API",
            test_instance.test_level_3_high_level_analysis_api,
        ),
        (
            "Level 3: Multiple Interpretation API",
            test_instance.test_level_3_multiple_interpretation_api,
        ),
        (
            "Level 4: Bidirectional Conversion",
            test_instance.test_level_4_bidirectional_conversion,
        ),
        (
            "Confidence and Metadata Validation",
            test_instance.test_confidence_and_metadata_validation,
        ),
        ("Roman Numeral Detection", test_instance.test_roman_numeral_detection),
        (
            "Inversion Consistency Across Modes",
            test_instance.test_inversion_consistency_across_modes,
        ),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"Running {test_name}...")
            test_func()
            print(f"✅ {test_name} PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name} FAILED: {e}")
            failed += 1

    print("=" * 60)
    print(f"🎉 Test Results: {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)
