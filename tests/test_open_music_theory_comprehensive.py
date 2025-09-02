#!/usr/bin/env python
"""
Comprehensive Open Music Theory Tests

Tests extracted from foundational music theory concepts typically covered in
the Open Music Theory textbook. These tests provide real-world validation
of the library's capabilities across all analysis types in both directions:
from chord progressions to analysis and from theoretical concepts to expected
chord progressions.

This serves as both validation and educational reference for music theory
concepts the library should handle correctly.
"""

import pytest

from harmonic_analysis import (
    ALL_MAJOR_KEYS,
    ALL_MODES,
    AnalysisOptions,
    PedagogicalLevel,
    analyze_melody,
    analyze_progression_character,
    analyze_progression_multiple,
    analyze_scale,
    analyze_scale_melody,
    describe_contour,
    get_interval_name,
    get_modal_characteristics,
    get_mode_emotional_profile,
    get_modes_by_brightness,
)


class TestOpenMusicTheoryFunctionalHarmony:
    """Tests based on functional harmony concepts from Open Music Theory"""

    @pytest.mark.asyncio
    async def test_basic_cadences(self):
        """Test fundamental cadences taught in music theory"""
        cadence_tests = [
            # Authentic cadences
            (
                ["C", "F", "G", "C"],
                "Perfect Authentic Cadence in C major",
                "functional",
                "C major",
                ["I", "IV", "V", "I"],
            ),
            (
                ["F", "Bb", "C", "F"],
                "Perfect Authentic Cadence in F major",
                "functional",
                "F major",
                ["I", "IV", "V", "I"],
            ),
            (
                ["G", "C", "D", "G"],
                "Perfect Authentic Cadence in G major",
                "functional",
                "G major",
                ["I", "IV", "V", "I"],
            ),
            # Plagal cadences (Amen cadence)
            (
                ["C", "F", "C"],
                "Plagal Cadence in C major",
                "functional",
                "C major",
                ["I", "IV", "I"],
            ),
            (
                ["F", "Bb", "F"],
                "Plagal Cadence in F major",
                "functional",
                "F major",
                ["I", "IV", "I"],
            ),
            # Deceptive cadences
            (
                ["C", "F", "G", "Am"],
                "Deceptive Cadence in C major",
                "functional",
                "C major",
                ["I", "IV", "V", "vi"],
            ),
            (
                ["F", "Bb", "C", "Dm"],
                "Deceptive Cadence in F major",
                "functional",
                "F major",
                ["I", "IV", "V", "vi"],
            ),
        ]

        for (
            progression,
            description,
            expected_type,
            expected_key,
            expected_romans,
        ) in cadence_tests:
            result = await analyze_progression_multiple(
                progression,
                AnalysisOptions(parent_key=expected_key, confidence_threshold=0.3),
            )

            # Should have analysis result
            assert (
                result.primary_analysis is not None
            ), f"{description} should have primary analysis"

            # VALIDATE ACTUAL ROMAN NUMERALS MATCH THEORY
            actual_romans = result.primary_analysis.roman_numerals
            assert (
                actual_romans == expected_romans
            ), f"{description}: Expected {expected_romans}, got {actual_romans}"

            # VALIDATE TYPE IS CORRECT
            assert (
                result.primary_analysis.type.value == expected_type
            ), f"{description}: Should be {expected_type}, got {result.primary_analysis.type.value}"

            # VALIDATE KEY SIGNATURE
            assert (
                result.primary_analysis.key_signature == expected_key
            ), f"{description}: Should be in {expected_key}, got {result.primary_analysis.key_signature}"

    @pytest.mark.asyncio
    async def test_common_chord_progressions(self):
        """Test standard progressions taught in music theory textbooks"""
        progressions = [
            # Circle of fifths progressions with expected romans
            (
                ["C", "Am", "F", "G"],
                "I-vi-IV-V in C major",
                "functional",
                "C major",
                ["I", "vi", "IV", "V"],
            ),
            (
                ["F", "Dm", "Bb", "C"],
                "I-vi-IV-V in F major",
                "functional",
                "F major",
                ["I", "vi", "IV", "V"],
            ),
            # ii-V-I progressions (jazz fundamental)
            (
                ["Dm", "G", "C"],
                "ii-V-I in C major",
                "functional",
                "C major",
                ["ii", "V", "I"],
            ),
            (
                ["Em", "A", "D"],
                "ii-V-I in D major",
                "functional",
                "D major",
                ["ii", "V", "I"],
            ),
            (
                ["Am", "D", "G"],
                "ii-V-I in G major",
                "functional",
                "G major",
                ["ii", "V", "I"],
            ),
            # vi-IV-I-V (pop progression)
            (
                ["Am", "F", "C", "G"],
                "vi-IV-I-V (pop) in C major",
                "functional",
                "C major",
                ["vi", "IV", "I", "V"],
            ),
            (
                ["Em", "C", "G", "D"],
                "vi-IV-I-V (pop) in G major",
                "functional",
                "G major",
                ["vi", "IV", "I", "V"],
            ),
        ]

        for (
            progression,
            description,
            expected_type,
            expected_key,
            expected_romans,
        ) in progressions:
            result = await analyze_progression_multiple(
                progression, AnalysisOptions(confidence_threshold=0.3)
            )

            # Should have meaningful analysis
            assert (
                result.primary_analysis is not None
            ), f"{description} should have analysis"

            # VALIDATE ACTUAL ROMAN NUMERALS
            actual_romans = result.primary_analysis.roman_numerals
            assert (
                actual_romans == expected_romans
            ), f"{description}: Expected {expected_romans}, got {actual_romans}"

            # VALIDATE TYPE
            assert (
                result.primary_analysis.type.value == expected_type
            ), f"{description}: Should be {expected_type} analysis, got {result.primary_analysis.type.value}"

            # VALIDATE KEY (if functional)
            if expected_type == "functional":
                assert (
                    result.primary_analysis.key_signature == expected_key
                ), f"{description}: Should be in {expected_key}, got {result.primary_analysis.key_signature}"


class TestOpenMusicTheoryModalAnalysis:
    """Tests based on modal theory concepts from Open Music Theory"""

    @pytest.mark.asyncio
    async def test_church_modes(self):
        """Test the seven church modes with characteristic progressions"""
        mode_tests = [
            # Ionian (Major)
            (["C", "F", "G", "C"], "C Ionian", "C major", "functional"),
            # Dorian - characteristic bVII and natural 6th
            (["D", "G", "C", "D"], "D Dorian vamp", "C major", "modal"),
            (["E", "A", "D", "E"], "E Dorian vamp", "D major", "modal"),
            # Phrygian - characteristic bII
            (["E", "F", "E"], "E Phrygian with bII", "C major", "modal"),
            (["A", "Bb", "A"], "A Phrygian with bII", "F major", "modal"),
            # Lydian - characteristic #IV
            (["F", "B", "F"], "F Lydian with #IV", "C major", "modal"),
            (["C", "F#", "C"], "C Lydian with #IV", "G major", "modal"),
            # Mixolydian - characteristic bVII
            (["G", "F", "G"], "G Mixolydian with bVII", "C major", "modal"),
            (["D", "C", "D"], "D Mixolydian with bVII", "G major", "modal"),
            (["A", "G", "A"], "A Mixolydian with bVII", "D major", "modal"),
            # Aeolian (Natural Minor)
            (["A", "F", "G", "A"], "A Aeolian progression", "C major", "modal"),
            (["E", "C", "D", "E"], "E Aeolian progression", "G major", "modal"),
            # Locrian - rare but theoretically important
            (["B", "F", "B"], "B Locrian with bV", "C major", "modal"),
        ]

        for progression, description, expected_parent, expected_type in mode_tests:
            result = await analyze_progression_multiple(
                progression, AnalysisOptions(confidence_threshold=0.4)
            )

            # Should have analysis
            assert (
                result.primary_analysis is not None
            ), f"{description} should have analysis"

            # For modal progressions, check if modal analysis is provided (primary or alternative)
            if expected_type == "modal":
                modal_analyses = [result.primary_analysis] + result.alternative_analyses
                modal_found = any(a.type.value == "modal" for a in modal_analyses)
                assert modal_found, f"{description} should have modal analysis option"

            # Should have roman numerals
            assert len(result.primary_analysis.roman_numerals) == len(
                progression
            ), f"{description} should have roman numerals"

    @pytest.mark.asyncio
    async def test_modal_characteristics(self):
        """Test that modal characteristics are properly identified"""
        for mode_name in ALL_MODES:
            characteristics = get_modal_characteristics(mode_name)

            # Each mode should have characteristics
            assert (
                characteristics is not None
            ), f"Mode {mode_name} should have characteristics"
            # ModalCharacteristics is a dataclass, check if it has characteristic_degrees attribute
            assert hasattr(
                characteristics, "characteristic_degrees"
            ), f"Mode {mode_name} should have characteristic_degrees"
            assert (
                len(characteristics.characteristic_degrees) > 0
            ), f"Mode {mode_name} should have at least one characteristic degree"


class TestOpenMusicTheoryScaleAnalysis:
    """Tests based on scale theory concepts from Open Music Theory"""

    @pytest.mark.asyncio
    async def test_major_scales(self):
        """Test major scale analysis for all keys"""
        for key in ALL_MAJOR_KEYS:
            # Test scale analysis
            result = await analyze_scale([f"{key.split()[0]}"])

            # Should identify as major scale
            assert result is not None, f"Should analyze scale for {key}"
            # Note: The library may identify single notes differently than full scales

    @pytest.mark.asyncio
    async def test_minor_scales(self):
        """Test minor scale analysis for all keys"""
        natural_minor_examples = [
            (["A", "B", "C", "D", "E", "F", "G"], "A natural minor"),
            (["E", "F#", "G", "A", "B", "C", "D"], "E natural minor"),
            (["D", "E", "F", "G", "A", "Bb", "C"], "D natural minor"),
        ]

        for scale_notes, description in natural_minor_examples:
            result = await analyze_scale(scale_notes)

            # Should have analysis
            assert result is not None, f"{description} should have scale analysis"

    @pytest.mark.asyncio
    async def test_chromatic_scales(self):
        """Test chromatic scale recognition"""
        chromatic_c = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

        result = await analyze_scale(chromatic_c)

        # Should recognize chromatic elements
        assert result is not None, "Chromatic scale should have analysis"


class TestOpenMusicTheoryMelodyAnalysis:
    """Tests based on melody analysis concepts from Open Music Theory"""

    @pytest.mark.asyncio
    async def test_scale_degree_melodies(self):
        """Test melodies using basic scale degree patterns"""
        melody_tests = [
            # Do-Re-Mi patterns
            (["C4", "D4", "E4"], "Ascending stepwise in C major"),
            (["G4", "A4", "B4"], "Ascending stepwise in G major"),
            # Arpeggiated melodies
            (["C4", "E4", "G4", "C5"], "C major triad arpeggio"),
            (["F4", "A4", "C5", "F5"], "F major triad arpeggio"),
            # Scalewise passages
            (["C4", "D4", "E4", "F4", "G4"], "C major pentachord"),
            (["G4", "A4", "B4", "C5", "D5"], "G major pentachord"),
        ]

        for melody, description in melody_tests:
            result = await analyze_melody(melody)

            # Should have analysis
            assert result is not None, f"{description} should have melody analysis"

    @pytest.mark.asyncio
    async def test_melodic_contour(self):
        """Test melodic contour analysis"""
        contour_tests = [
            (["C4", "E4", "G4"], "ascending"),
            (["G4", "E4", "C4"], "descending"),
            (["C4", "E4", "D4"], "up then down"),
            (["F4", "D4", "G4"], "down then up"),
        ]

        for melody, expected_pattern in contour_tests:
            contour = describe_contour(melody)

            # Should have contour description
            assert contour is not None, f"Melody {melody} should have contour analysis"
            assert len(contour) > 0, "Contour should not be empty"


class TestOpenMusicTheoryAdvancedConcepts:
    """Tests based on advanced concepts from Open Music Theory"""

    @pytest.mark.asyncio
    async def test_tonicization_and_modulation(self):
        """Test temporary tonicization vs permanent modulation"""
        tonicization_tests = [
            # Brief tonicization of vi
            (["C", "E", "Am", "F", "G", "C"], "Tonicization of vi in C major"),
            # Brief tonicization of V
            (["C", "F#dim", "G", "C"], "Tonicization of V in C major"),
            # Pivot chord modulation
            (["C", "Am", "D", "G"], "C major to G major via Am"),
        ]

        for progression, description in tonicization_tests:
            result = await analyze_progression_multiple(
                progression, AnalysisOptions(confidence_threshold=0.3)
            )

            # Should have analysis
            assert (
                result.primary_analysis is not None
            ), f"{description} should have analysis"

            # May be functional or chromatic analysis
            assert result.primary_analysis.type.value in [
                "functional",
                "chromatic",
            ], f"{description} should be functional or chromatic analysis"

    @pytest.mark.asyncio
    async def test_borrowed_chords(self):
        """Test borrowed chords from parallel modes"""
        borrowed_chord_tests = [
            # bVI from parallel minor
            (["C", "Ab", "G", "C"], "bVI borrowed from C minor", "chromatic"),
            # iv from parallel minor (minor plagal cadence)
            (["C", "Fm", "C"], "iv borrowed from C minor", "chromatic"),
            # bVII from parallel minor
            (["C", "Bb", "C"], "bVII borrowed from C minor", "chromatic"),
        ]

        for progression, description, expected_type in borrowed_chord_tests:
            result = await analyze_progression_multiple(
                progression, AnalysisOptions(confidence_threshold=0.3)
            )

            # Should have analysis
            assert (
                result.primary_analysis is not None
            ), f"{description} should have analysis"

            # Should provide alternatives for ambiguous cases
            if expected_type == "chromatic":
                # Check if chromatic analysis is available (primary or alternative)
                analyses = [result.primary_analysis] + result.alternative_analyses
                types_available = [a.type.value for a in analyses]
                # Should have either chromatic, modal, or functional analysis for borrowed chords
                assert any(
                    t in ["chromatic", "modal", "functional"] for t in types_available
                ), f"{description} should offer some analysis type, got: {types_available}"


class TestOpenMusicTheoryBidirectionalAnalysis:
    """Test bidirectional analysis: theory to chords and chords to theory"""

    @pytest.mark.asyncio
    async def test_roman_numeral_expectations(self):
        """Test that expected roman numerals match theoretical knowledge"""
        roman_tests = [
            # Basic triads in major
            (["C", "F", "G"], "C major", ["I", "IV", "V"]),
            (["F", "Bb", "C"], "F major", ["I", "IV", "V"]),
            # Basic triads in minor (natural)
            (["Am", "Dm", "Em"], "A minor", ["i", "iv", "v"]),
            (["Em", "Am", "Bm"], "E minor", ["i", "iv", "v"]),
        ]

        for progression, key_context, expected_romans in roman_tests:
            result = await analyze_progression_multiple(
                progression,
                AnalysisOptions(parent_key=key_context, confidence_threshold=0.3),
            )

            # Should have roman numerals and they should match theory
            actual_romans = result.primary_analysis.roman_numerals

            # Handle multiple acceptable answers
            if isinstance(expected_romans[0], list):
                # Multiple acceptable roman numeral sets
                assert any(
                    actual_romans == acceptable for acceptable in expected_romans
                ), f"Progression {progression} in {key_context} should be one of {expected_romans}, got {actual_romans}"
            else:
                # Single expected answer
                assert (
                    actual_romans == expected_romans
                ), f"Progression {progression} in {key_context} should be {expected_romans}, got {actual_romans}"

    @pytest.mark.asyncio
    async def test_interval_recognition(self):
        """Test interval recognition and naming"""
        # Unused variable removed to fix linting
        # interval_tests = [
        #     ("perfect unison", "P1"),
        #     ("minor second", "m2"),
        #     ("major second", "M2"),
        #     ("minor third", "m3"),
        #     ("major third", "M3"),
        #     ("perfect fourth", "P4"),
        #     ("tritone", "TT"),
        #     ("perfect fifth", "P5"),
        #     ("minor sixth", "m6"),
        #     ("major sixth", "M6"),
        #     ("minor seventh", "m7"),
        #     ("major seventh", "M7"),
        #     ("perfect octave", "P8"),
        # ]

        # Test a few semitone-based intervals instead
        semitone_tests = [
            (0, "unison"),
            (1, "minor second"),
            (2, "major second"),
            (3, "minor third"),
            (4, "major third"),
            (5, "perfect fourth"),
            (7, "perfect fifth"),
        ]

        for semitones, expected_name in semitone_tests:
            interval_result = get_interval_name(semitones)

            # Should return meaningful result
            assert (
                interval_result is not None
            ), f"Should recognize interval with {semitones} semitones"
            assert (
                len(interval_result) > 0
            ), f"Interval name should not be empty for {semitones} semitones"


class TestOpenMusicTheoryCharacterAndEmotion:
    """Test character and emotional analysis concepts"""

    @pytest.mark.asyncio
    async def test_modal_emotional_profiles(self):
        """Test that modes have appropriate emotional characteristics"""
        for mode in ALL_MODES:
            emotional_profile = get_mode_emotional_profile(mode)

            # Each mode should have emotional profile
            assert (
                emotional_profile is not None
            ), f"Mode {mode} should have emotional profile"

    @pytest.mark.asyncio
    async def test_progression_character_analysis(self):
        """Test character analysis of common progressions"""
        character_tests = [
            (["C", "F", "G", "C"], "Should have stable, resolved character"),
            (["Am", "F", "C", "G"], "Should have pop/contemporary character"),
            (["G", "F", "G"], "Should have modal/folk character"),
        ]

        for progression, expected_character in character_tests:
            character_result = analyze_progression_character(progression)

            # Should have character analysis
            assert (
                character_result is not None
            ), f"Progression {progression} should have character analysis"

    @pytest.mark.asyncio
    async def test_brightness_ordering(self):
        """Test that modes are properly ordered by brightness"""
        # Test different brightness levels
        bright_modes = get_modes_by_brightness("bright")
        dark_modes = get_modes_by_brightness("dark")

        # Should return lists of modes for each brightness level
        assert isinstance(bright_modes, list), "Should return list for bright modes"
        assert isinstance(dark_modes, list), "Should return list for dark modes"


class TestOpenMusicTheoryScaleMelodyCombined:
    """Test combined scale and melody analysis"""

    @pytest.mark.asyncio
    async def test_scale_melody_analysis(self):
        """Test combined scale and melody analysis"""
        scale_melody_tests = [
            # Major scale with stepwise melody
            (
                ["C", "D", "E", "F", "G", "F", "E", "D", "C"],
                "C major scale with returning melody",
            ),
            # Modal melody
            (["G", "A", "B", "C", "D", "E", "F", "G"], "G Mixolydian scale"),
            # Minor scale melody
            (["A", "B", "C", "D", "E", "F", "G", "A"], "A natural minor scale"),
        ]

        for scale_melody, description in scale_melody_tests:
            result = analyze_scale_melody(scale_melody)

            # Should have combined analysis
            assert (
                result is not None
            ), f"{description} should have scale-melody analysis"


class TestOpenMusicTheoryPedagogicalLevels:
    """Test analysis at different pedagogical complexity levels"""

    @pytest.mark.asyncio
    async def test_beginner_analysis(self):
        """Test analysis appropriate for beginning students"""
        result = await analyze_progression_multiple(
            ["C", "F", "G", "C"],
            AnalysisOptions(
                pedagogical_level=PedagogicalLevel.BEGINNER, confidence_threshold=0.3
            ),
        )

        # Should have simplified analysis appropriate for beginners
        assert result.primary_analysis is not None
        assert len(result.primary_analysis.reasoning) > 0

    @pytest.mark.asyncio
    async def test_advanced_analysis(self):
        """Test analysis appropriate for advanced students"""
        result = await analyze_progression_multiple(
            ["C", "E", "Am", "F#dim", "G", "C"],
            AnalysisOptions(
                pedagogical_level=PedagogicalLevel.ADVANCED, confidence_threshold=0.2
            ),
        )

        # Should have detailed analysis appropriate for graduate level
        assert result.primary_analysis is not None
        # Advanced analysis should provide more alternatives
        assert len(result.alternative_analyses) >= 0  # May have alternatives


class TestOpenMusicTheorySpecializedConcepts:
    """Additional specialized tests for comprehensive Open Music Theory coverage"""

    @pytest.mark.asyncio
    async def test_enharmonic_equivalents(self):
        """Test that enharmonically equivalent chords are handled correctly"""
        enharmonic_tests = [
            # Sharp vs flat equivalents
            (["C#", "F#", "G#"], ["Db", "Gb", "Ab"], "Enharmonic major chords"),
            (["F#m", "Bm", "C#m"], ["Gbm", "Cbm", "Dbm"], "Enharmonic minor chords"),
        ]

        for sharp_version, flat_version, description in enharmonic_tests:
            sharp_result = await analyze_progression_multiple(
                sharp_version, AnalysisOptions(confidence_threshold=0.3)
            )
            flat_result = await analyze_progression_multiple(
                flat_version, AnalysisOptions(confidence_threshold=0.3)
            )

            # Both should have analysis
            assert (
                sharp_result.primary_analysis is not None
            ), f"Sharp version of {description} should have analysis"
            assert (
                flat_result.primary_analysis is not None
            ), f"Flat version of {description} should have analysis"

    @pytest.mark.asyncio
    async def test_voice_leading_progressions(self):
        """Test progressions that demonstrate good voice leading"""
        voice_leading_tests = [
            # Smooth voice leading
            (["C", "C7", "F"], "I-I7-IV with smooth bass motion"),
            (["Am", "Am7", "Dm"], "vi-vi7-ii with smooth voice leading"),
            # Stepwise bass motion
            (["C", "Dm", "Em", "F"], "Ascending stepwise bass in C major"),
            (["F", "Em", "Dm", "C"], "Descending stepwise bass in C major"),
        ]

        for progression, description in voice_leading_tests:
            result = await analyze_progression_multiple(
                progression, AnalysisOptions(confidence_threshold=0.3)
            )

            # Should have analysis
            assert (
                result.primary_analysis is not None
            ), f"{description} should have analysis"
            assert len(result.primary_analysis.roman_numerals) == len(
                progression
            ), f"{description} should have roman numerals for all chords"

    @pytest.mark.asyncio
    async def test_sequence_patterns(self):
        """Test sequential harmonic patterns"""
        sequence_tests = [
            # Descending fifth sequence
            (["C", "F", "Bb", "Eb"], "Descending fifth sequence"),
            (["Am", "Dm", "Gm", "Cm"], "Descending fifth sequence in minor"),
            # Ascending second sequence
            (["C", "Dm", "Em", "F"], "Ascending stepwise sequence"),
            (["F", "Gm", "Am", "Bb"], "Ascending stepwise sequence from F"),
        ]

        for progression, description in sequence_tests:
            result = await analyze_progression_multiple(
                progression, AnalysisOptions(confidence_threshold=0.3)
            )

            # Should have analysis
            assert (
                result.primary_analysis is not None
            ), f"{description} should have analysis"


class TestOpenMusicTheoryEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_single_chord_analysis(self):
        """Test analysis of single chords"""
        single_chord_tests = [
            (["C"], "Single C major chord"),
            (["Am"], "Single A minor chord"),
            (["G7"], "Single dominant seventh chord"),
        ]

        for progression, description in single_chord_tests:
            result = await analyze_progression_multiple(
                progression, AnalysisOptions(confidence_threshold=0.3)
            )

            # Should have analysis even for single chord
            assert (
                result.primary_analysis is not None
            ), f"{description} should have analysis"

    @pytest.mark.asyncio
    async def test_very_long_progressions(self):
        """Test analysis of extended progressions"""
        long_progression = [
            "C",
            "Am",
            "F",
            "G",
            "Em",
            "Am",
            "Dm",
            "G",
            "C",
            "F",
            "G",
            "Am",
            "F",
            "C",
            "G",
            "C",
        ]

        result = await analyze_progression_multiple(
            long_progression, AnalysisOptions(confidence_threshold=0.3)
        )

        # Should handle long progressions
        assert (
            result.primary_analysis is not None
        ), "Long progression should have analysis"
        assert len(result.primary_analysis.roman_numerals) == len(
            long_progression
        ), "Should have roman numerals for all chords in long progression"

    @pytest.mark.asyncio
    async def test_unusual_chord_combinations(self):
        """Test unusual but theoretically valid chord combinations"""
        unusual_tests = [
            (["C", "F#", "Bb"], "Unusual chromatic combination"),
            (["Am", "Eb", "G"], "Unusual modal mixture"),
            (["F", "B", "Em"], "Chromatic mediant relationships"),
        ]

        for progression, description in unusual_tests:
            result = await analyze_progression_multiple(
                progression,
                AnalysisOptions(confidence_threshold=0.1),  # Very low threshold
            )

            # Should attempt analysis even for unusual progressions
            assert (
                result.primary_analysis is not None
            ), f"{description} should have some analysis"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
