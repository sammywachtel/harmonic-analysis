"""
Tests for musical character and emotional analysis functionality.
"""

import pytest

from harmonic_analysis.api.character import (
    CHORD_EMOTIONAL_QUALITIES,
    MODE_EMOTIONAL_PROFILES,
    SCALE_EMOTIONAL_PROFILES,
    EmotionalBrightness,
    EmotionalEnergy,
    EmotionalProfile,
    EmotionalTension,
    analyze_progression_character,
    describe_emotional_contour,
    enhance_analysis_with_character,
    get_character_suggestions,
    get_mode_emotional_profile,
    get_modes_by_brightness,
)


class TestEmotionalProfiles:
    """Test emotional profile functionality."""

    def test_get_mode_emotional_profile_major_modes(self):
        """Test getting emotional profiles for major scale modes."""
        # Test exact matches
        ionian = get_mode_emotional_profile("Ionian")
        assert ionian is not None
        assert ionian.brightness == EmotionalBrightness.BRIGHT
        assert "joy" in ionian.primary_emotions
        assert "pop" in ionian.typical_genres

        dorian = get_mode_emotional_profile("Dorian")
        assert dorian is not None
        assert dorian.brightness == EmotionalBrightness.NEUTRAL
        assert "contemplation" in dorian.primary_emotions
        assert "jazz" in dorian.typical_genres

        phrygian = get_mode_emotional_profile("Phrygian")
        assert phrygian is not None
        assert phrygian.brightness == EmotionalBrightness.DARK
        assert "mystery" in phrygian.primary_emotions

    def test_get_mode_emotional_profile_partial_matches(self):
        """Test partial string matching for mode names."""
        # Should find Lydian when searching for partial match
        lydian_partial = get_mode_emotional_profile("E Lydian")
        assert lydian_partial is not None
        assert lydian_partial.brightness == EmotionalBrightness.VERY_BRIGHT

        # Should find Aeolian when searching for partial match
        aeolian_partial = get_mode_emotional_profile("A Aeolian")
        assert aeolian_partial is not None
        assert aeolian_partial.brightness == EmotionalBrightness.DARK

    def test_get_mode_emotional_profile_scale_profiles(self):
        """Test getting profiles for non-modal scales."""
        harmonic_minor = get_mode_emotional_profile("Harmonic Minor")
        assert harmonic_minor is not None
        assert harmonic_minor.brightness == EmotionalBrightness.DARK
        assert "drama" in harmonic_minor.primary_emotions

        blues = get_mode_emotional_profile("Blues Scale")
        assert blues is not None
        assert blues.brightness == EmotionalBrightness.DARK
        assert "blues" in blues.primary_emotions

    def test_get_mode_emotional_profile_not_found(self):
        """Test behavior when mode is not found."""
        result = get_mode_emotional_profile("NonexistentMode")
        assert result is None


class TestProgressionCharacter:
    """Test progression character analysis."""

    def test_analyze_progression_character_major_progression(self):
        """Test analysis of a bright major progression."""
        chords = ["C", "F", "G", "C"]
        character = analyze_progression_character(chords)

        assert (
            "optimistic" in character.overall_mood or "bright" in character.overall_mood
        )
        assert len(character.brightness_profile) == 4
        assert all(
            b == EmotionalBrightness.BRIGHT for b in character.brightness_profile
        )
        assert character.cadence_strength > 0.5
        assert len(character.tension_curve) == 4

    def test_analyze_progression_character_minor_progression(self):
        """Test analysis of a dark minor progression."""
        chords = ["Am", "Dm", "Em", "Am"]
        character = analyze_progression_character(chords)

        assert (
            "melancholic" in character.overall_mood
            or "introspective" in character.overall_mood
        )
        assert len(character.brightness_profile) == 4
        assert all(b == EmotionalBrightness.DARK for b in character.brightness_profile)
        assert "melancholic" in character.emotional_keywords

    def test_analyze_progression_character_mixed_progression(self):
        """Test analysis of a mixed brightness progression."""
        chords = ["C", "Am", "F", "G"]
        character = analyze_progression_character(chords)

        assert len(character.brightness_profile) == 4
        # Should have mixed brightness
        brightness_values = [b.value for b in character.brightness_profile]
        assert len(set(brightness_values)) > 1  # Multiple brightness levels

    def test_analyze_progression_character_jazz_chords(self):
        """Test analysis with jazz chord extensions."""
        chords = ["Cmaj7", "Am7", "Dm7", "G7"]
        character = analyze_progression_character(chords)

        assert "jazz" in character.genre_associations
        assert len(character.suggested_instrumentation) > 0

    def test_analyze_progression_character_blues_progression(self):
        """Test analysis of a blues progression."""
        chords = ["C7", "F7", "G7", "C7"]
        character = analyze_progression_character(chords)

        assert "blues" in character.genre_associations
        assert (
            "bluesy" in " ".join(character.emotional_keywords).lower()
            or "blues" in " ".join(character.emotional_keywords).lower()
        )


class TestCharacterSuggestions:
    """Test character-based suggestions."""

    def test_get_character_suggestions_happy(self):
        """Test suggestions for achieving happiness."""
        suggestion = get_character_suggestions("happy")

        assert suggestion.target_emotion == "happy"
        assert len(suggestion.suggested_modes) > 0
        assert "Ionian" in suggestion.suggested_modes
        assert len(suggestion.suggested_progressions) > 0
        assert len(suggestion.suggested_keys) > 0
        assert "major" in " ".join(suggestion.suggested_keys).lower()
        assert suggestion.confidence > 0.5

    def test_get_character_suggestions_sad(self):
        """Test suggestions for achieving sadness."""
        suggestion = get_character_suggestions("sad")

        assert suggestion.target_emotion == "sad"
        assert len(suggestion.suggested_modes) > 0
        assert (
            "Aeolian" in suggestion.suggested_modes
            or "Dorian" in suggestion.suggested_modes
        )
        assert len(suggestion.modification_tips) > 0
        assert any("minor" in tip.lower() for tip in suggestion.modification_tips)

    def test_get_character_suggestions_mysterious(self):
        """Test suggestions for achieving mysterious character."""
        suggestion = get_character_suggestions("mysterious")

        assert suggestion.target_emotion == "mysterious"
        assert len(suggestion.suggested_modes) > 0
        assert (
            "Phrygian" in suggestion.suggested_modes
            or "Harmonic Minor" in suggestion.suggested_modes
        )
        assert len(suggestion.modification_tips) > 0

    def test_get_character_suggestions_bluesy(self):
        """Test suggestions for bluesy character."""
        suggestion = get_character_suggestions("bluesy")

        assert suggestion.target_emotion == "bluesy"
        assert (
            "Blues Scale" in suggestion.suggested_modes
            or "Mixolydian" in suggestion.suggested_modes
        )
        assert len(suggestion.example_songs) >= 0  # May be empty but should exist

    def test_get_character_suggestions_unknown_emotion(self):
        """Test suggestions for unknown emotion."""
        suggestion = get_character_suggestions("nonexistent_emotion")

        # Should still provide some suggestions with lower confidence
        assert len(suggestion.suggested_modes) > 0
        assert suggestion.confidence <= 0.9  # Lower confidence for unknown emotions


class TestBrightnessFiltering:
    """Test brightness-based mode filtering."""

    def test_get_modes_by_brightness_bright(self):
        """Test getting bright modes."""
        bright_modes = get_modes_by_brightness("bright")

        assert len(bright_modes) > 0
        assert "Ionian" in bright_modes
        assert "Lydian" in bright_modes
        assert "Mixolydian" in bright_modes

    def test_get_modes_by_brightness_dark(self):
        """Test getting dark modes."""
        dark_modes = get_modes_by_brightness("dark")

        assert len(dark_modes) > 0
        assert "Phrygian" in dark_modes
        assert "Aeolian" in dark_modes
        assert "Locrian" in dark_modes

    def test_get_modes_by_brightness_neutral(self):
        """Test getting neutral modes."""
        neutral_modes = get_modes_by_brightness("neutral")

        assert len(neutral_modes) > 0
        assert "Dorian" in neutral_modes

    def test_get_modes_by_brightness_invalid(self):
        """Test invalid brightness parameter."""
        result = get_modes_by_brightness("invalid")
        assert result == []


class TestEmotionalContour:
    """Test emotional contour description."""

    def test_describe_emotional_contour_ascending(self):
        """Test ascending contour description."""
        contour = ["U", "U", "U", "U"]
        description = describe_emotional_contour(contour)

        assert "ascending" in description.lower()
        assert "energy" in description.lower() or "excitement" in description.lower()
        assert "dramatic rise" in description.lower()

    def test_describe_emotional_contour_descending(self):
        """Test descending contour description."""
        contour = ["D", "D", "D", "D"]
        description = describe_emotional_contour(contour)

        assert "descending" in description.lower()
        assert (
            "relaxation" in description.lower() or "resolution" in description.lower()
        )
        assert "dramatic fall" in description.lower()

    def test_describe_emotional_contour_arch(self):
        """Test arch-shaped contour."""
        contour = ["U", "U", "D", "D"]
        description = describe_emotional_contour(contour)

        assert "arch" in description.lower()
        assert "classical" in description.lower()

    def test_describe_emotional_contour_zigzag(self):
        """Test zigzag contour pattern."""
        contour = ["U", "D", "U", "D", "U", "D"]
        description = describe_emotional_contour(contour)

        assert "zigzag" in description.lower()
        assert "playful" in description.lower()

    def test_describe_emotional_contour_empty(self):
        """Test empty contour."""
        contour = []
        description = describe_emotional_contour(contour)

        assert "no contour" in description.lower()


class TestAnalysisEnhancement:
    """Test enhancement of existing analysis with character."""

    def test_enhance_modal_analysis(self):
        """Test enhancing modal analysis with character."""
        original_analysis = {
            "type": "modal",
            "mode": "E Dorian",
            "confidence": 0.8,
            "key": "E minor",
        }

        enhanced = enhance_analysis_with_character(original_analysis)

        assert "emotional_profile" in enhanced
        assert "brightness" in enhanced["emotional_profile"]
        assert "primary_emotions" in enhanced["emotional_profile"]
        assert "typical_genres" in enhanced["emotional_profile"]
        assert "suggested_tempo" in enhanced["emotional_profile"]

    def test_enhance_progression_analysis(self):
        """Test enhancing progression analysis with character."""
        original_analysis = {
            "progression": ["C", "Am", "F", "G"],
            "key": "C major",
            "type": "functional",
        }

        enhanced = enhance_analysis_with_character(original_analysis)

        assert "progression_character" in enhanced
        assert "overall_mood" in enhanced["progression_character"]
        assert "emotional_trajectory" in enhanced["progression_character"]
        assert "emotional_keywords" in enhanced["progression_character"]
        assert "suggested_instrumentation" in enhanced["progression_character"]

    def test_enhance_analysis_no_character_data(self):
        """Test enhancing analysis that doesn't have character-relevant data."""
        original_analysis = {"type": "functional", "confidence": 0.7}

        enhanced = enhance_analysis_with_character(original_analysis)

        # Should not add character data
        assert "emotional_profile" not in enhanced
        assert "progression_character" not in enhanced
        # Should preserve original data
        assert enhanced["type"] == "functional"
        assert enhanced["confidence"] == 0.7


class TestDataIntegrity:
    """Test data structure integrity."""

    def test_mode_emotional_profiles_completeness(self):
        """Test that all expected modes have emotional profiles."""
        expected_modes = [
            "Ionian",
            "Dorian",
            "Phrygian",
            "Lydian",
            "Mixolydian",
            "Aeolian",
            "Locrian",
        ]

        for mode in expected_modes:
            assert mode in MODE_EMOTIONAL_PROFILES
            profile = MODE_EMOTIONAL_PROFILES[mode]
            assert isinstance(profile, EmotionalProfile)
            assert profile.brightness in EmotionalBrightness
            assert profile.energy in EmotionalEnergy
            assert profile.tension in EmotionalTension
            assert len(profile.primary_emotions) > 0
            assert len(profile.typical_genres) > 0

    def test_scale_emotional_profiles_completeness(self):
        """Test that scale profiles are properly structured."""
        for scale_name, profile in SCALE_EMOTIONAL_PROFILES.items():
            assert isinstance(profile, EmotionalProfile)
            assert profile.brightness in EmotionalBrightness
            assert len(profile.primary_emotions) > 0
            assert len(profile.typical_genres) > 0

    def test_chord_emotional_qualities_structure(self):
        """Test chord emotional qualities data structure."""
        for chord_type, qualities in CHORD_EMOTIONAL_QUALITIES.items():
            assert "brightness" in qualities
            assert "tension" in qualities
            assert "stability" in qualities

            # Values should be between 0 and 1
            assert 0 <= qualities["brightness"] <= 1
            assert 0 <= qualities["tension"] <= 1
            assert 0 <= qualities["stability"] <= 1


class TestIntegration:
    """Test integration with main API."""

    def test_main_api_imports(self):
        """Test that character functions are available from main API."""
        # These imports should work if the main __init__.py is properly configured
        try:
            from harmonic_analysis import (
                analyze_progression_character,
                describe_emotional_contour,
                get_character_suggestions,
                get_mode_emotional_profile,
                get_modes_by_brightness,
            )

            # Basic functionality test
            profile = get_mode_emotional_profile("Dorian")
            assert profile is not None

            character = analyze_progression_character(["C", "F", "G"])
            assert character is not None

            suggestion = get_character_suggestions("happy")
            assert suggestion is not None

            modes = get_modes_by_brightness("bright")
            assert len(modes) > 0

            contour_desc = describe_emotional_contour(["U", "D", "U"])
            assert len(contour_desc) > 0

        except ImportError as e:
            pytest.fail(
                f"Character analysis functions not properly exported from main API: {e}"
            )


if __name__ == "__main__":
    pytest.main([__file__])
