#!/usr/bin/env python
"""
Open Music Theory Validation Tests

These tests validate the library against established music theory from Open Music Theory.
Unlike the comprehensive test suite, these tests document both CORRECT analysis and
CURRENT LIMITATIONS of the library, serving as:

1. Validation that the library handles core theory correctly
2. Documentation of areas needing improvement
3. Regression tests to prevent deterioration

Each test includes comments explaining what Open Music Theory says vs what the library returns.
"""

import pytest

from harmonic_analysis import (
    AnalysisOptions,
    analyze_progression_multiple,
)


class TestOpenMusicTheoryCorrectAnalysis:
    """Tests where the library correctly matches Open Music Theory expectations"""

    @pytest.mark.asyncio
    async def test_authentic_cadences_correct(self):
        """Test that V-I cadences are correctly identified as functional"""
        # Open Music Theory: V-I is the fundamental authentic cadence in functional harmony

        cadences = [
            (["C", "F", "G", "C"], "I-IV-V-I in C major", ["I", "IV", "V", "I"]),
            (["Dm", "G", "C"], "ii-V-I in C major", ["ii", "V", "I"]),
            (["C", "Am", "F", "G"], "I-vi-IV-V in C major", ["I", "vi", "IV", "V"]),
        ]

        for progression, description, expected_romans in cadences:
            result = await analyze_progression_multiple(
                progression,
                AnalysisOptions(parent_key="C major", confidence_threshold=0.3),
            )

            analysis = result.primary_analysis

            # These should be analyzed as functional (CORRECT)
            assert (
                analysis.type.value == "functional"
            ), f"{description} should be functional, got {analysis.type.value}"

            # Roman numerals should match theory (CORRECT)
            assert (
                analysis.roman_numerals == expected_romans
            ), f"{description}: Expected {expected_romans}, got {analysis.roman_numerals}"

            # Key should be C major (CORRECT)
            assert (
                analysis.key_signature == "C major"
            ), f"{description}: Should be C major, got {analysis.key_signature}"

    @pytest.mark.asyncio
    async def test_modal_characteristics_correct(self):
        """Test that clear modal progressions are correctly identified"""
        # Open Music Theory: Modal progressions have characteristic intervals that distinguish them

        modal_progressions = [
            (
                ["G", "F", "G"],
                "G Mixolydian with bVII",
                "modal",
                "G Mixolydian",
                ["I", "bVII", "I"],
            ),
            # Note: More modal tests would go here as the library improves
        ]

        for (
            progression,
            description,
            expected_type,
            expected_mode,
            expected_romans,
        ) in modal_progressions:
            result = await analyze_progression_multiple(
                progression,
                AnalysisOptions(parent_key="C major", confidence_threshold=0.3),
            )

            analysis = result.primary_analysis

            # Should be modal (CORRECT)
            assert (
                analysis.type.value == expected_type
            ), f"{description}: Expected {expected_type}, got {analysis.type.value}"

            # Should identify correct mode (CORRECT)
            assert (
                expected_mode in analysis.mode
            ), f"{description}: Expected {expected_mode}, got {analysis.mode}"

            # Romans should match modal theory (CORRECT)
            assert (
                analysis.roman_numerals == expected_romans
            ), f"{description}: Expected {expected_romans}, got {analysis.roman_numerals}"


class TestOpenMusicTheoryLimitations:
    """Tests documenting current limitations where library differs from theory"""

    @pytest.mark.asyncio
    async def test_plagal_cadence_limitation(self):
        """Document that plagal cadences are misclassified as modal instead of functional"""
        # Open Music Theory: I-IV-I is a plagal cadence, a type of FUNCTIONAL cadence
        # Current Library Behavior: Classifies as modal (C Ionian)

        result = await analyze_progression_multiple(
            ["C", "F", "C"],
            AnalysisOptions(parent_key="C major", confidence_threshold=0.3),
        )

        analysis = result.primary_analysis

        # LIMITATION: Library incorrectly classifies plagal as modal
        assert (
            analysis.type.value == "modal"
        ), "Library currently classifies I-IV-I as modal (should be functional)"

        assert (
            "Ionian" in analysis.mode
        ), "Library identifies as C Ionian rather than functional plagal cadence"

        # However, roman numerals are correct
        assert analysis.roman_numerals == [
            "I",
            "IV",
            "I",
        ], "Roman numerals are correct even if classification isn't"

        # TODO: When this is fixed, move to TestOpenMusicTheoryCorrectAnalysis

    @pytest.mark.asyncio
    async def test_secondary_dominants_limitation(self):
        """Document handling of secondary dominants"""
        # Open Music Theory: V/vi in C major should be E major (or E7)
        # This tests how the library handles tonicization vs modal analysis

        progressions_to_test = [
            (["C", "E", "Am"], "I-V/vi-vi"),
            (["F", "A", "Dm"], "I-V/vi-vi in F major"),
        ]

        for progression, description in progressions_to_test:
            result = await analyze_progression_multiple(
                progression,
                AnalysisOptions(
                    confidence_threshold=0.2
                ),  # Lower threshold for chromatic
            )

            analysis = result.primary_analysis

            # Document current behavior (may be functional, modal, or chromatic)
            assert analysis is not None, f"{description} should have some analysis"

            # The type will vary - document what it actually does
            actual_type = analysis.type.value
            print(f"Secondary dominant {description} analyzed as: {actual_type}")

            # Romans should at least exist
            assert len(analysis.roman_numerals) == len(
                progression
            ), f"{description} should have roman numerals for all chords"

    @pytest.mark.asyncio
    async def test_borrowed_chords_current_behavior(self):
        """Document how borrowed chords are currently handled"""
        # Open Music Theory: Chords borrowed from parallel mode (e.g. iv from minor)

        borrowed_progressions = [
            (["C", "Fm", "C"], "iv borrowed from C minor"),
            (["C", "Ab", "G", "C"], "bVI-V-I with borrowed bVI"),
            (["C", "Bb", "C"], "bVII borrowed from C minor"),
        ]

        for progression, description in borrowed_progressions:
            result = await analyze_progression_multiple(
                progression, AnalysisOptions(confidence_threshold=0.2)
            )

            analysis = result.primary_analysis

            # Document current behavior
            assert analysis is not None, f"{description} should have analysis"

            actual_type = analysis.type.value
            print(f"Borrowed chord {description} analyzed as: {actual_type}")

            # At minimum should recognize the chromaticism somehow
            analyses_types = [analysis.type.value] + [
                a.type.value for a in result.alternative_analyses
            ]

            # Should offer some recognition of non-diatonic nature
            assert any(
                t in ["chromatic", "modal"] for t in analyses_types
            ), f"{description} should recognize chromatic/modal nature, got: {analyses_types}"


class TestOpenMusicTheoryBidirectionalValidation:
    """Test bidirectional validation: given theoretical concepts, does the library recognize them?"""

    @pytest.mark.asyncio
    async def test_cadence_types_recognition(self):
        """Test that the library can distinguish different cadence types"""
        # From Open Music Theory: Different cadences have different functional roles

        cadence_tests = [
            # Strong cadences (should be high confidence functional)
            (["G", "C"], "V-I authentic", "functional", True),
            (["Dm", "G", "C"], "ii-V-I", "functional", True),
            # Weaker cadences
            (
                ["F", "C"],
                "IV-I plagal",
                "functional",
                False,
            ),  # Currently modal, so False
            # Deceptive (should be functional but to vi)
            (["G", "Am"], "V-vi deceptive", "functional", True),
        ]

        for progression, description, expected_type, currently_works in cadence_tests:
            result = await analyze_progression_multiple(
                progression,
                AnalysisOptions(parent_key="C major", confidence_threshold=0.3),
            )

            analysis = result.primary_analysis

            if currently_works:
                # These should work correctly
                assert (
                    analysis.type.value == expected_type
                ), f"{description}: Should be {expected_type}, got {analysis.type.value}"
            else:
                # These are current limitations - document them
                print(
                    f"LIMITATION: {description} analyzed as {analysis.type.value} (expected {expected_type})"
                )

    @pytest.mark.asyncio
    async def test_mode_characteristic_intervals(self):
        """Test recognition of characteristic intervals that define modes"""
        # From Open Music Theory: Each mode has characteristic intervals

        mode_tests = [
            # Clear modal characteristics that should be recognized
            (["G", "F", "G"], "Mixolydian bVII", "modal", "Mixolydian", True),
            (
                ["D", "G", "C", "D"],
                "Dorian progression",
                "modal",
                "Dorian",
                False,
            ),  # TBD
            (["E", "F", "E"], "Phrygian bII", "modal", "Phrygian", False),  # TBD
        ]

        for (
            progression,
            description,
            expected_type,
            expected_mode,
            currently_works,
        ) in mode_tests:
            result = await analyze_progression_multiple(
                progression, AnalysisOptions(confidence_threshold=0.3)
            )

            analysis = result.primary_analysis

            if currently_works:
                assert (
                    analysis.type.value == expected_type
                ), f"{description}: Should be {expected_type}, got {analysis.type.value}"
                assert (
                    expected_mode in analysis.mode
                ), f"{description}: Should contain {expected_mode}, got {analysis.mode}"
            else:
                # Document current behavior for future validation
                print(
                    f"MODE TEST: {description} -> {analysis.type.value}, {analysis.mode}"
                )


class TestOpenMusicTheoryProgressionValidation:
    """Validate analysis of real-world progressions from music theory literature"""

    @pytest.mark.asyncio
    async def test_circle_of_fifths_progressions(self):
        """Test progressions moving by circle of fifths"""
        # Open Music Theory: Circle of fifths creates strong harmonic motion

        circle_progressions = [
            (["C", "F", "Bb", "Eb"], "Descending fifths"),
            (["Am", "Dm", "G", "C"], "Ascending fourths (same as desc. fifths)"),
        ]

        for progression, description in circle_progressions:
            result = await analyze_progression_multiple(
                progression, AnalysisOptions(confidence_threshold=0.3)
            )

            analysis = result.primary_analysis

            # Should have strong analysis due to clear harmonic motion
            assert (
                analysis.confidence > 0.5
            ), f"{description} should have decent confidence due to clear harmonic motion"

            # Should have roman numerals for all chords
            assert len(analysis.roman_numerals) == len(
                progression
            ), f"{description} should analyze all chords"

    @pytest.mark.asyncio
    async def test_common_pop_progressions(self):
        """Test common progressions from popular music"""
        # These appear in Open Music Theory's discussion of contemporary harmony

        pop_progressions = [
            (["C", "G", "Am", "F"], "I-V-vi-IV (popular)"),
            (["Am", "F", "C", "G"], "vi-IV-I-V (popular)"),
            (["F", "G", "Am"], "IV-V-vi (deceptive ending)"),
        ]

        for progression, description in pop_progressions:
            result = await analyze_progression_multiple(
                progression, AnalysisOptions(confidence_threshold=0.3)
            )

            analysis = result.primary_analysis

            # These common progressions should be analyzed consistently
            assert analysis.type.value in [
                "functional",
                "modal",
            ], f"{description} should have functional or modal analysis"

            # Should provide roman numerals
            assert len(analysis.roman_numerals) == len(
                progression
            ), f"{description} should have complete roman numeral analysis"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to see print statements
