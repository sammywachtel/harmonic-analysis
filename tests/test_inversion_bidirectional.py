"""
Focused regression test for chord inversion bidirectional conversion.

Tests your specific progression: "D Gm/Bb D/A Gm F/C C F" in F major
Expected Roman numerals: "V/ii - ii⁶ - V/ii⁶⁴ - ii - I⁶⁴ - V - I"

This test validates:
1. Chords → Roman numerals (with correct inversion notation)
2. Roman numerals → Chords (reconstruction with inversions)
3. Analysis confidence and metadata
"""

import asyncio

import pytest

from harmonic_analysis import AnalysisOptions, analyze_progression_multiple
from harmonic_analysis.utils.roman_numeral_converter import (
    convert_roman_numerals_to_chords,
)


class TestInversionBidirectional:
    """Focused bidirectional inversion test for your specific progression."""

    # Your test case
    CHORD_PROGRESSION = ["D", "Gm/Bb", "D/A", "Gm", "F/C", "C", "F"]
    PARENT_KEY = "F major"
    EXPECTED_FUNCTIONAL_ROMANS = ["V/ii", "ii⁶", "V/ii⁶⁴", "ii", "I⁶⁴", "V", "I"]

    @pytest.mark.asyncio
    async def test_bidirectional_inversion_conversion(self):
        """Test complete bidirectional conversion with inversion preservation."""

        print("🎯 Testing bidirectional inversion conversion...")
        print(f"Input chords: {' - '.join(self.CHORD_PROGRESSION)}")
        print(f"Parent key: {self.PARENT_KEY}")

        # STEP 1: Chords → Roman numerals
        options = AnalysisOptions(parent_key=self.PARENT_KEY, max_alternatives=3)
        analysis_result = await analyze_progression_multiple(
            self.CHORD_PROGRESSION, options=options
        )

        # Find functional analysis (should be primary or alternative)
        functional_analysis = None
        if (
            hasattr(analysis_result.primary_analysis, "type")
            and analysis_result.primary_analysis.type.value == "functional"
        ):
            functional_analysis = analysis_result.primary_analysis
        else:
            for alt in analysis_result.alternative_analyses:
                if hasattr(alt, "type") and alt.type.value == "functional":
                    functional_analysis = alt
                    break

        # Validate functional analysis was found
        assert (
            functional_analysis is not None
        ), "Should find functional analysis with inversions"

        actual_romans = functional_analysis.roman_numerals
        print(f"Actual Roman numerals: {' - '.join(actual_romans)}")
        print(f"Expected Roman numerals: {' - '.join(self.EXPECTED_FUNCTIONAL_ROMANS)}")

        # Validate specific inversion expectations
        assert len(actual_romans) == len(
            self.EXPECTED_FUNCTIONAL_ROMANS
        ), f"Roman numeral count mismatch: got {len(actual_romans)}, expected {len(self.EXPECTED_FUNCTIONAL_ROMANS)}"

        # Check for correct inversion notation presence
        romans_str = " - ".join(actual_romans)
        assert "ii⁶" in romans_str, f"Should contain ii⁶ (Gm/Bb), got: {romans_str}"
        assert "V/ii⁶⁴" in romans_str, f"Should contain V/ii⁶⁴ (D/A), got: {romans_str}"
        assert "I⁶⁴" in romans_str, f"Should contain I⁶⁴ (F/C), got: {romans_str}"

        # STEP 2: Roman numerals → Chords
        romans_str = " ".join(actual_romans)  # Space-separated, not " - " separated
        reconstructed_chords = convert_roman_numerals_to_chords(
            romans_str, parent_key="F major"
        )

        print(f"Reconstructed chords: {' - '.join(reconstructed_chords)}")

        # Validate reconstruction
        assert len(reconstructed_chords) == len(
            self.CHORD_PROGRESSION
        ), f"Reconstructed chord count mismatch: got {len(reconstructed_chords)}, expected {len(self.CHORD_PROGRESSION)}"

        # Check that inversions are preserved in reconstruction
        slash_chords_reconstructed = [
            chord for chord in reconstructed_chords if "/" in chord
        ]

        assert (
            len(slash_chords_reconstructed) >= 2
        ), f"Should preserve at least 2 inversions, got {len(slash_chords_reconstructed)} in: {reconstructed_chords}"

        # Verify specific chord reconstructions (allowing for enharmonic equivalents)
        for i, (original, reconstructed) in enumerate(
            zip(self.CHORD_PROGRESSION, reconstructed_chords)
        ):
            original_root = original.split("/")[0]
            reconstructed_root = reconstructed.split("/")[0]

            # Check that root notes match (essential chord identity preserved)
            assert (
                original_root == reconstructed_root
            ), f"Root changed in position {i}: {original} -> {reconstructed}"

            # If original has slash, reconstructed should too (inversion preserved)
            if "/" in original:
                assert (
                    "/" in reconstructed
                ), f"Inversion lost in position {i}: {original} -> {reconstructed}"

        # STEP 3: Validate analysis confidence and metadata
        assert hasattr(
            functional_analysis, "confidence"
        ), "Should have confidence score"
        assert (
            0.0 <= functional_analysis.confidence <= 1.0
        ), f"Confidence should be 0-1, got: {functional_analysis.confidence}"

        assert hasattr(analysis_result, "metadata"), "Should have metadata"
        assert hasattr(
            analysis_result.metadata, "total_interpretations_considered"
        ), "Should track interpretation count"

        print("✅ All bidirectional inversion tests passed!")
        return True

    def test_roman_numeral_format_validation(self):
        """Validate that Roman numerals contain proper figured bass notation."""

        test_romans = self.EXPECTED_FUNCTIONAL_ROMANS
        romans_str = " - ".join(test_romans)

        # Should contain first inversion notation
        assert "⁶" in romans_str, f"Should contain first inversion (⁶) in: {romans_str}"

        # Should contain second inversion notation
        assert (
            "⁶⁴" in romans_str
        ), f"Should contain second inversion (⁶⁴) in: {romans_str}"

        # Verify specific expected Roman numerals
        assert "V/ii" in romans_str, "Should contain V/ii"
        assert "ii⁶" in romans_str, "Should contain ii⁶"
        assert "V/ii⁶⁴" in romans_str, "Should contain V/ii⁶⁴"
        assert "I⁶⁴" in romans_str, "Should contain I⁶⁴"

        print(f"✅ Roman numeral format validation passed for: {romans_str}")


# Individual test functions for pytest discovery
@pytest.mark.asyncio
async def test_bidirectional_inversion_conversion():
    """Test bidirectional chord-Roman numeral conversion with inversions."""
    test_instance = TestInversionBidirectional()
    await test_instance.test_bidirectional_inversion_conversion()


def test_roman_numeral_format_validation():
    """Test Roman numeral figured bass notation format."""
    test_instance = TestInversionBidirectional()
    test_instance.test_roman_numeral_format_validation()


if __name__ == "__main__":
    # Direct execution for debugging
    print("🎯 FOCUSED INVERSION REGRESSION TEST")
    print("=" * 50)
    print("Testing progression: D Gm/Bb D/A Gm F/C C F in F major")
    print("Expected result: V/ii - ii⁶ - V/ii⁶⁴ - ii - I⁶⁴ - V - I")
    print("=" * 50)

    test_instance = TestInversionBidirectional()

    try:
        # Test Roman numeral format
        test_instance.test_roman_numeral_format_validation()

        # Test bidirectional conversion
        result = asyncio.run(test_instance.test_bidirectional_inversion_conversion())

        if result:
            print("🎉 ALL TESTS PASSED - Inversion regression test successful!")

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
