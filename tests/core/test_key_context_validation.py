"""
Regression tests for key-context normalization requirements.

These tests ensure that the library enforces key context requirements for
roman numerals, scales, and melodies as specified in Iteration 7.
"""

from unittest.mock import patch

import pytest

from harmonic_analysis.api.analysis import analyze_melody, analyze_scale
from harmonic_analysis.core.pattern_engine.pattern_engine import AnalysisContext
from harmonic_analysis.core.validation_errors import (
    MISSING_KEY_FOR_MELODY_MSG,
    MISSING_KEY_FOR_ROMANS_MSG,
    MISSING_KEY_FOR_SCALE_MSG,
    MissingKeyError,
    validate_key_for_analysis,
    validate_key_for_romans,
)


class TestKeyContextValidation:
    """Test key context validation requirements."""

    def test_romans_require_key_when_non_empty(self):
        """Test that roman numerals require key context when non-empty."""
        # Should pass with empty romans and no key
        validate_key_for_romans([], None)
        validate_key_for_romans([], "")

        # Should pass with romans and key
        validate_key_for_romans(["I", "V", "I"], "C major")

        # Should fail with non-empty romans and no key
        with pytest.raises(MissingKeyError, match=MISSING_KEY_FOR_ROMANS_MSG):
            validate_key_for_romans(["I", "V", "I"], None)

        with pytest.raises(MissingKeyError, match=MISSING_KEY_FOR_ROMANS_MSG):
            validate_key_for_romans(["I", "V", "I"], "")

    def test_modal_symbols_with_key_context(self):
        """Test that modal symbols are accepted when key context is provided."""
        # Modal symbols should be accepted with key context
        modal_romans = ["i", "♭VII", "♭VI", "V"]
        validate_key_for_romans(modal_romans, "A minor")

        # Different modal symbols
        phrygian_romans = ["i", "♭II", "i"]
        validate_key_for_romans(phrygian_romans, "E phrygian")

        # Should still fail if key is missing
        with pytest.raises(MissingKeyError):
            validate_key_for_romans(modal_romans, None)

    def test_analysis_context_key_validation(self):
        """Test AnalysisContext validates key requirements for roman numerals."""
        # Valid: empty romans without key
        ctx = AnalysisContext(
            key=None,
            chords=["C", "F", "G"],
            roman_numerals=[],
            melody=[],
            scales=[],
            metadata={},
        )

        # Valid: romans with key
        AnalysisContext(
            key="C major",
            chords=["C", "F", "G"],
            roman_numerals=["I", "IV", "V"],
            melody=[],
            scales=[],
            metadata={},
        )

        # Invalid: romans without key should raise error
        with pytest.raises(MissingKeyError):
            AnalysisContext(
                key=None,
                chords=["C", "F", "G"],
                roman_numerals=["I", "IV", "V"],
                melody=[],
                scales=[],
                metadata={},
            )

    async def test_analyze_scale_requires_key(self):
        """Test that analyze_scale requires key context."""
        notes = ["C", "D", "E", "F", "G", "A", "B"]

        # Should work with key
        with patch(
            "harmonic_analysis.api.analysis._analyze_scale_melody"
        ) as mock_analyze:
            mock_analyze.return_value = "mock_result"
            result = await analyze_scale(notes, key="C major")
            assert result == "mock_result"
            mock_analyze.assert_called_once_with(notes, "C major", melody=False)

        # Should fail without key
        with pytest.raises(MissingKeyError, match=MISSING_KEY_FOR_SCALE_MSG):
            await analyze_scale(notes, key=None)

        with pytest.raises(MissingKeyError, match=MISSING_KEY_FOR_SCALE_MSG):
            await analyze_scale(notes)  # key defaults to None

    async def test_analyze_melody_requires_key(self):
        """Test that analyze_melody requires key context."""
        notes = ["G", "A", "B", "C", "D"]

        # Should work with key
        with patch(
            "harmonic_analysis.api.analysis._analyze_scale_melody"
        ) as mock_analyze:
            mock_analyze.return_value = "mock_result"
            result = await analyze_melody(notes, key="G major")
            assert result == "mock_result"
            mock_analyze.assert_called_once_with(notes, "G major", melody=True)

        # Should fail without key
        with pytest.raises(MissingKeyError, match=MISSING_KEY_FOR_MELODY_MSG):
            await analyze_melody(notes, key=None)

        with pytest.raises(MissingKeyError, match=MISSING_KEY_FOR_MELODY_MSG):
            await analyze_melody(notes)  # key defaults to None

    def test_validation_error_messages(self):
        """Test that validation errors provide helpful messages."""
        # Test scale analysis error message
        with pytest.raises(MissingKeyError) as exc_info:
            validate_key_for_analysis(None, "scale")
        assert "Scale analysis requires a key context" in str(exc_info.value)

        # Test melody analysis error message
        with pytest.raises(MissingKeyError) as exc_info:
            validate_key_for_analysis(None, "melody")
        assert "Melody analysis requires a key context" in str(exc_info.value)

        # Test roman numeral error message
        with pytest.raises(MissingKeyError) as exc_info:
            validate_key_for_romans(["I", "V"], None)
        assert "Roman numeral analysis requires a key context" in str(exc_info.value)

    def test_error_message_consistency(self):
        """Test that error messages are consistent across the library."""
        # All key requirement errors should mention providing a key parameter
        error_messages = [
            MISSING_KEY_FOR_ROMANS_MSG,
            MISSING_KEY_FOR_SCALE_MSG,
            MISSING_KEY_FOR_MELODY_MSG,
        ]

        for msg in error_messages:
            assert "key" in msg.lower()
            assert "provide" in msg.lower() or "requires" in msg.lower()

    def test_regression_prevent_contextless_modal_analysis(self):
        """Regression test: prevent modal analysis without key context."""
        # This test ensures we don't regress to allowing modal analysis
        # without proper key context, which was identified as an issue
        # in the iteration notes.

        # Modal symbols should not be accepted without key
        modal_progressions = [
            ["i", "♭VII", "♭VI", "V"],  # Andalusian
            ["i", "♭II", "i"],  # Phrygian
            ["I", "♭VII", "I"],  # Mixolydian
        ]

        for romans in modal_progressions:
            with pytest.raises(MissingKeyError):
                validate_key_for_romans(romans, None)

            # But should work with key context
            validate_key_for_romans(romans, "A minor")

    def test_key_context_prevents_validator_blocking(self):
        """Test that key context allows modal symbols through validators."""
        # This addresses the issue mentioned in iteration notes:
        # "Without a key hint, our Roman validator blocks modal symbols"

        # These modal symbols should be validated successfully with key context
        modal_symbols_by_mode = {
            "Mixolydian": ["I", "♭VII", "I"],
            "Dorian": ["i", "iv", "♭VII", "i"],
            "Phrygian": ["i", "♭II", "i"],
            "Lydian": ["I", "♯IV", "I"],
        }

        for mode, romans in modal_symbols_by_mode.items():
            # Should work with appropriate key context
            validate_key_for_romans(romans, f"C {mode}")

            # Should fail without key context
            with pytest.raises(MissingKeyError):
                validate_key_for_romans(romans, None)
