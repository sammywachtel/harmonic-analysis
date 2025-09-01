#!/usr/bin/env python3
"""
Musical Character and Emotional Analysis Demo

This demo showcases the new character analysis functionality that provides
emotional profiles, brightness classification, and character-based suggestions
for scales, modes, and progressions.
"""

import asyncio
from harmonic_analysis import (
    # Core analysis
    analyze_progression_multiple,
    # Character analysis
    get_mode_emotional_profile,
    analyze_progression_character,
    get_character_suggestions,
    get_modes_by_brightness,
    describe_emotional_contour,
    # Data types
    EmotionalProfile,
    ProgressionCharacter,
    CharacterSuggestion,
)


def demo_modal_character_analysis():
    """Demonstrate modal emotional profile analysis."""
    print("🎨 MODAL CHARACTER ANALYSIS")
    print("=" * 50)

    modes = [
        "Ionian",
        "Dorian",
        "Phrygian",
        "Lydian",
        "Mixolydian",
        "Aeolian",
        "Locrian",
    ]

    for mode in modes:
        profile = get_mode_emotional_profile(mode)
        if profile:
            print(f"\n🎼 {mode} Mode:")
            print(f"   Brightness: {profile.brightness.value}")
            print(f"   Primary emotions: {', '.join(profile.primary_emotions[:3])}")
            print(f"   Typical genres: {', '.join(profile.typical_genres[:3])}")
            print(f"   Character: {profile.descriptive_terms[0]}")


def demo_progression_character():
    """Demonstrate chord progression character analysis."""
    print("\n\n🎸 PROGRESSION CHARACTER ANALYSIS")
    print("=" * 50)

    test_progressions = [
        (["C", "F", "G", "C"], "Classic I-IV-V-I"),
        (["Am", "F", "C", "G"], "Popular vi-IV-I-V"),
        (["C7", "F7", "G7", "C7"], "Blues progression"),
        (["Cmaj7", "Am7", "Dm7", "G7"], "Jazz ii-V-I"),
        (["Em", "F", "Em", "G"], "Modal/Phrygian flavor"),
    ]

    for chords, description in test_progressions:
        character = analyze_progression_character(chords)

        print(f"\n🎶 {description}: {' - '.join(chords)}")
        print(f"   Overall mood: {character.overall_mood}")
        print(f"   Emotional trajectory: {character.emotional_trajectory}")
        print(f"   Genre associations: {', '.join(character.genre_associations)}")
        print(f"   Emotional keywords: {', '.join(character.emotional_keywords)}")
        if character.suggested_instrumentation:
            print(
                f"   Suggested instruments: {', '.join(character.suggested_instrumentation[:3])}"
            )


def demo_character_suggestions():
    """Demonstrate character-based suggestions."""
    print("\n\n💡 CHARACTER-BASED SUGGESTIONS")
    print("=" * 50)

    desired_emotions = ["happy", "sad", "mysterious", "bluesy", "peaceful"]

    for emotion in desired_emotions:
        suggestion = get_character_suggestions(emotion)

        print(f"\n🎯 For '{emotion}' character:")
        print(f"   Suggested modes: {', '.join(suggestion.suggested_modes[:3])}")
        print(f"   Suggested keys: {', '.join(suggestion.suggested_keys)}")
        if suggestion.modification_tips:
            print(f"   Tips: {suggestion.modification_tips[0]}")
        if suggestion.example_songs:
            print(f"   Example: {suggestion.example_songs[0]}")
        print(f"   Confidence: {suggestion.confidence:.0%}")


def demo_brightness_classification():
    """Demonstrate brightness-based mode filtering."""
    print("\n\n✨ BRIGHTNESS CLASSIFICATION")
    print("=" * 50)

    for brightness in ["bright", "neutral", "dark"]:
        modes = get_modes_by_brightness(brightness)
        print(f"\n{brightness.upper()} modes: {', '.join(modes)}")


def demo_melodic_contour():
    """Demonstrate emotional contour analysis."""
    print("\n\n📈 MELODIC CONTOUR EMOTIONS")
    print("=" * 50)

    contour_examples = [
        (["U", "U", "U"], "Rising melody"),
        (["D", "D", "D"], "Falling melody"),
        (["U", "U", "D", "D"], "Arch shape"),
        (["U", "D", "U", "D"], "Zigzag pattern"),
        (["D", "D", "U", "U"], "Valley shape"),
    ]

    for contour, description in contour_examples:
        emotional_desc = describe_emotional_contour(contour)
        print(f"\n🎵 {description} {contour}:")
        print(f"   {emotional_desc}")


async def demo_integrated_analysis():
    """Demonstrate integration with main analysis."""
    print("\n\n🔗 INTEGRATED CHARACTER ANALYSIS")
    print("=" * 50)

    # Analyze a progression with character enhancement
    progression = ["Em", "C", "G", "D"]
    result = await analyze_progression_multiple(progression)

    print(f"\n🎼 Analyzing: {' - '.join(progression)}")
    print(f"Analysis: {result.primary_analysis.analysis}")
    print(f"Type: {result.primary_analysis.type.value}")
    print(f"Confidence: {result.primary_analysis.confidence:.0%}")

    # Analyze character separately
    character = analyze_progression_character(progression)
    print(f"\nCharacter Analysis:")
    print(f"   Mood: {character.overall_mood}")
    print(f"   Keywords: {', '.join(character.emotional_keywords)}")

    # If modal, get mode character
    if result.primary_analysis.type.value == "modal" and hasattr(
        result.primary_analysis, "mode"
    ):
        mode_profile = get_mode_emotional_profile(result.primary_analysis.mode)
        if mode_profile:
            print(f"   Mode brightness: {mode_profile.brightness.value}")
            print(f"   Mode emotions: {', '.join(mode_profile.primary_emotions[:2])}")


def main():
    """Run all character analysis demonstrations."""
    print("🎨 MUSICAL CHARACTER & EMOTIONAL ANALYSIS DEMO")
    print("🎵 Exploring the emotional landscape of music theory")
    print("=" * 60)

    # Run synchronous demos
    demo_modal_character_analysis()
    demo_progression_character()
    demo_character_suggestions()
    demo_brightness_classification()
    demo_melodic_contour()

    # Run async demo
    print("\n" + "=" * 60)
    asyncio.run(demo_integrated_analysis())

    print("\n\n🎊 CHARACTER ANALYSIS COMPLETE!")
    print("✨ The harmonic-analysis library now provides rich emotional")
    print("   and character insights to enhance your musical analysis!")


if __name__ == "__main__":
    main()
