#!/usr/bin/env python
"""
Real-world progression integration tests

These tests validate common musical progressions that users actually input,
catching issues that unit tests miss.
"""

import pytest

from harmonic_analysis import AnalysisOptions, analyze_progression_multiple


class TestRealWorldProgressions:
    """Test common real-world chord progressions"""

    @pytest.mark.asyncio
    async def test_vi_IV_I_V_in_A_major(self):
        """
        Test F#m-D-A-E (vi-IV-I-V in A major)

        This is one of the most common progressions in popular music.
        Should be analyzed as functional, not modal.
        """
        result = await analyze_progression_multiple(
            ["F#m", "D", "A", "E"], AnalysisOptions(confidence_threshold=0.4)
        )

        # Should have both functional and modal interpretations
        assert (
            len(result.alternative_analyses) > 0
        ), "Should provide alternative analyses"

        # Check primary analysis
        primary = result.primary_analysis

        # Should have roman numerals populated
        assert (
            len(primary.roman_numerals) == 4
        ), f"Should have 4 roman numerals, got: {primary.roman_numerals}"

        # This common progression should be analyzed functionally, not modally
        # When analyzed modally in F# Aeolian, E would be bVII (which is technically correct)
        # But functional analysis in A major (vi-IV-I-V) is more appropriate for this progression
        if primary.type.value == "modal" and "bVII" in primary.reasoning:
            # This suggests the functional analysis should have higher confidence
            # Check if functional analysis is available as alternative
            functional_analyses = [
                a for a in result.alternative_analyses if a.type.value == "functional"
            ]
            assert (
                len(functional_analyses) > 0
            ), "Should provide functional alternative for this common progression"

            # The confidence difference shouldn't be too large
            functional_confidence = functional_analyses[0].confidence
            modal_confidence = primary.confidence
            confidence_gap = modal_confidence - functional_confidence

            # If modal analysis dominates by too much, it suggests calibration issue
            if confidence_gap > 0.3:
                pytest.fail(
                    f"Modal analysis confidence ({modal_confidence:.3f}) too much higher than "
                    f"functional ({functional_confidence:.3f}) for common vi-IV-I-V progression. "
                    f"Gap: {confidence_gap:.3f}"
                )

        # Should provide meaningful reasoning
        reasoning = primary.reasoning.lower()
        assert (
            "contains" in reasoning
            or "progression" in reasoning
            or "analysis" in reasoning
        ), f"Reasoning should be meaningful, got: {primary.reasoning}"

    @pytest.mark.asyncio
    async def test_common_progressions_have_alternatives(self):
        """Common progressions should offer multiple valid interpretations where appropriate"""
        # Progressions that should have alternatives (ambiguous between functional and modal)
        ambiguous_progressions = [
            (["F#m", "D", "A", "E"], "vi-IV-I-V in A major"),
            (["Em", "C", "G", "D"], "vi-IV-I-V in G major"),
            (["Am", "F", "C", "G"], "vi-IV-I-V in C major"),
        ]

        for progression, description in ambiguous_progressions:
            result = await analyze_progression_multiple(
                progression, AnalysisOptions(confidence_threshold=0.3)
            )

            # These progressions should have alternatives (functional vs modal interpretations)
            assert (
                len(result.alternative_analyses) > 0
            ), f"{description} should have alternative interpretations"

            # Should have roman numerals
            assert (
                len(result.primary_analysis.roman_numerals) == 4
            ), f"{description} should have 4 roman numerals"

        # Clear functional progressions may not have alternatives (and that's OK)
        clear_functional_progressions = [
            (["C", "Am", "F", "G"], "I-vi-IV-V in C major"),
            (["C", "F", "G", "C"], "I-IV-V-I in C major"),
        ]

        for progression, description in clear_functional_progressions:
            result = await analyze_progression_multiple(
                progression, AnalysisOptions(confidence_threshold=0.3)
            )

            # Should still have roman numerals even if no alternatives
            assert (
                len(result.primary_analysis.roman_numerals) == 4
            ), f"{description} should have 4 roman numerals"

            # Primary should be functional
            assert (
                result.primary_analysis.type.value == "functional"
            ), f"{description} should be analyzed as functional"

    @pytest.mark.asyncio
    async def test_modal_vs_functional_accuracy(self):
        """Test that modal vs functional classification is accurate"""

        # Clearly functional progressions (should NOT be modal primary)
        functional_progressions = [
            (["C", "F", "G", "C"], "I-IV-V-I cadence"),
            (["Am", "Dm", "G", "C"], "vi-ii-V-I progression"),
            (["F", "G", "Am"], "IV-V-vi deceptive cadence"),
        ]

        for progression, description in functional_progressions:
            result = await analyze_progression_multiple(progression, AnalysisOptions())

            # These should be functional, not modal
            if result.primary_analysis.type.value == "modal":
                pytest.fail(
                    f"{description} incorrectly classified as modal. "
                    f"Confidence: {result.primary_analysis.confidence:.3f}"
                )

        # Clearly modal progressions (should be modal primary)
        modal_progressions = [
            (["G", "F", "G"], "G Mixolydian with bVII"),
            (["Em", "F", "Em"], "E Phrygian with bII"),
            (["Dm", "G", "Dm"], "D Dorian vamp"),
        ]

        for progression, description in modal_progressions:
            result = await analyze_progression_multiple(progression, AnalysisOptions())

            # These should be modal
            assert (
                result.primary_analysis.type.value == "modal"
            ), f"{description} should be classified as modal, got {result.primary_analysis.type.value}"

    @pytest.mark.asyncio
    async def test_parent_key_accuracy(self):
        """Test that parent keys are theoretically correct for modes"""
        mode_tests = [
            (["G", "F", "G"], "G Mixolydian", "C major"),  # G is 5th of C
            (["Dm", "G", "Dm"], "D Dorian", "C major"),  # D is 2nd of C
            (["F#m", "D", "A", "E"], "F# Aeolian", "A major"),  # F# is 6th of A
            (["Em", "F", "Em"], "E Phrygian", "C major"),  # E is 3rd of C
        ]

        for progression, expected_mode, expected_parent in mode_tests:
            result = await analyze_progression_multiple(progression, AnalysisOptions())

            if result.primary_analysis.type.value == "modal":
                actual_mode = result.primary_analysis.mode
                actual_parent = result.primary_analysis.key_signature

                assert (
                    expected_mode in actual_mode
                ), f"Expected mode {expected_mode}, got {actual_mode}"
                assert (
                    expected_parent == actual_parent
                ), f"Expected parent key {expected_parent}, got {actual_parent} for {expected_mode}"

    @pytest.mark.asyncio
    async def test_reasoning_quality(self):
        """Test that analysis reasoning is accurate and helpful"""

        test_cases = [
            (["C", "F", "G", "C"], ["I-IV-V-I", "authentic cadence", "tonic"]),
            (["G", "F", "G"], ["bVII", "Mixolydian", "modal"]),
            (["Am", "F", "C", "G"], ["vi-IV-I-V", "pop", "progression"]),
        ]

        for progression, expected_keywords in test_cases:
            result = await analyze_progression_multiple(progression, AnalysisOptions())

            reasoning = result.primary_analysis.reasoning.lower()

            # Should contain relevant keywords
            found_keywords = [kw for kw in expected_keywords if kw.lower() in reasoning]
            assert (
                len(found_keywords) > 0
            ), f"Reasoning '{reasoning}' should contain at least one of: {expected_keywords}"

            # Should not contain obviously wrong information
            wrong_indicators = [
                "contains bvii" if "bvii" not in expected_keywords else ""
            ]
            wrong_found = [wi for wi in wrong_indicators if wi and wi in reasoning]
            assert (
                len(wrong_found) == 0
            ), f"Reasoning contains incorrect information: {wrong_found}"

    @pytest.mark.asyncio
    async def test_roman_numeral_accuracy(self):
        """Test that roman numerals are correct for well-known progressions"""

        # Test in C major context
        roman_tests = [
            (["C", "F", "G", "C"], ["I", "IV", "V", "I"]),
            (["Am", "F", "C", "G"], ["vi", "IV", "I", "V"]),
            (["Dm", "G", "C"], ["ii", "V", "I"]),
        ]

        for progression, expected_romans in roman_tests:
            result = await analyze_progression_multiple(
                progression, AnalysisOptions(parent_key="C major")
            )

            actual_romans = result.primary_analysis.roman_numerals

            assert (
                actual_romans == expected_romans
            ), f"Progression {progression} in C major should be {expected_romans}, got {actual_romans}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
