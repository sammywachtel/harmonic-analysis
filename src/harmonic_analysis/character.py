"""
Musical Character and Emotional Analysis Module

This module provides comprehensive character analysis for musical elements,
including emotional profiles, brightness classification, and character-based
suggestions for scales, modes, and progressions.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

# =============================================================================
# EMOTIONAL ENUMS AND TYPES
# =============================================================================


class EmotionalBrightness(Enum):
    """Classification of emotional brightness/darkness."""

    VERY_BRIGHT = "very_bright"
    BRIGHT = "bright"
    NEUTRAL = "neutral"
    DARK = "dark"
    VERY_DARK = "very_dark"


class EmotionalEnergy(Enum):
    """Classification of emotional energy levels."""

    HIGH = "high"
    MEDIUM_HIGH = "medium_high"
    MEDIUM = "medium"
    MEDIUM_LOW = "medium_low"
    LOW = "low"


class EmotionalTension(Enum):
    """Classification of harmonic tension."""

    VERY_TENSE = "very_tense"
    TENSE = "tense"
    MODERATE = "moderate"
    RELAXED = "relaxed"
    VERY_RELAXED = "very_relaxed"


# =============================================================================
# EMOTIONAL PROFILE DATA STRUCTURES
# =============================================================================


@dataclass
class EmotionalProfile:
    """Complete emotional profile for a musical element."""

    brightness: EmotionalBrightness
    energy: EmotionalEnergy
    tension: EmotionalTension
    primary_emotions: List[str]
    secondary_emotions: List[str]
    typical_genres: List[str]
    descriptive_terms: List[str]
    color_associations: List[str]  # Synesthetic associations
    cultural_contexts: List[str]
    suggested_tempo_range: Tuple[int, int]  # BPM range
    suggested_dynamics: List[str]  # pp, p, mf, f, ff


@dataclass
class ProgressionCharacter:
    """Character analysis for a chord progression."""

    overall_mood: str
    emotional_trajectory: str  # e.g., "builds tension then resolves"
    brightness_profile: List[EmotionalBrightness]  # brightness per chord
    tension_curve: List[float]  # tension values 0-1
    cadence_strength: float  # 0-1
    modal_flavor: Optional[str]
    genre_associations: List[str]
    emotional_keywords: List[str]
    suggested_instrumentation: List[str]


@dataclass
class CharacterSuggestion:
    """Suggestion for achieving a desired emotional character."""

    target_emotion: str
    suggested_modes: List[str]
    suggested_progressions: List[List[str]]
    suggested_keys: List[str]
    modification_tips: List[str]
    example_songs: List[str]
    confidence: float


# =============================================================================
# EMOTIONAL PROFILES FOR MODES
# =============================================================================

MODE_EMOTIONAL_PROFILES: Dict[str, EmotionalProfile] = {
    "Ionian": EmotionalProfile(
        brightness=EmotionalBrightness.BRIGHT,
        energy=EmotionalEnergy.HIGH,
        tension=EmotionalTension.RELAXED,
        primary_emotions=["joy", "happiness", "optimism", "triumph"],
        secondary_emotions=["celebration", "satisfaction", "confidence"],
        typical_genres=["pop", "folk", "classical", "children's music"],
        descriptive_terms=["uplifting", "stable", "familiar", "resolved"],
        color_associations=["yellow", "bright blue", "white", "gold"],
        cultural_contexts=["Western classical tradition", "popular music", "hymns"],
        suggested_tempo_range=(90, 140),
        suggested_dynamics=["mf", "f"],
    ),
    "Dorian": EmotionalProfile(
        brightness=EmotionalBrightness.NEUTRAL,
        energy=EmotionalEnergy.MEDIUM,
        tension=EmotionalTension.MODERATE,
        primary_emotions=["contemplation", "sophistication", "coolness"],
        secondary_emotions=["melancholy with hope", "introspection", "groove"],
        typical_genres=["jazz", "funk", "celtic", "progressive rock"],
        descriptive_terms=["groovy", "sophisticated", "bittersweet", "jazzy"],
        color_associations=["purple", "deep blue", "silver"],
        cultural_contexts=["Jazz tradition", "Celtic music", "Modal jazz"],
        suggested_tempo_range=(70, 120),
        suggested_dynamics=["mp", "mf"],
    ),
    "Phrygian": EmotionalProfile(
        brightness=EmotionalBrightness.DARK,
        energy=EmotionalEnergy.MEDIUM_HIGH,
        tension=EmotionalTension.TENSE,
        primary_emotions=["mystery", "exoticism", "darkness", "passion"],
        secondary_emotions=["aggression", "sensuality", "ancient"],
        typical_genres=["flamenco", "metal", "middle eastern", "film scores"],
        descriptive_terms=["exotic", "Spanish", "mysterious", "intense"],
        color_associations=["dark red", "black", "deep orange"],
        cultural_contexts=["Spanish flamenco", "Middle Eastern music", "Heavy metal"],
        suggested_tempo_range=(60, 180),
        suggested_dynamics=["p", "ff"],
    ),
    "Lydian": EmotionalProfile(
        brightness=EmotionalBrightness.VERY_BRIGHT,
        energy=EmotionalEnergy.MEDIUM,
        tension=EmotionalTension.MODERATE,
        primary_emotions=["wonder", "dreaminess", "ethereal", "magic"],
        secondary_emotions=["floating", "otherworldly", "nostalgic"],
        typical_genres=["film music", "progressive rock", "new age", "ambient"],
        descriptive_terms=["floating", "magical", "spacey", "shimmering"],
        color_associations=["light blue", "white", "iridescent", "pastel"],
        cultural_contexts=["Film scoring", "Impressionist music", "Progressive genres"],
        suggested_tempo_range=(60, 100),
        suggested_dynamics=["pp", "p", "mp"],
    ),
    "Mixolydian": EmotionalProfile(
        brightness=EmotionalBrightness.BRIGHT,
        energy=EmotionalEnergy.HIGH,
        tension=EmotionalTension.MODERATE,
        primary_emotions=["playfulness", "bluesy joy", "earthiness"],
        secondary_emotions=["swagger", "celebration", "groove"],
        typical_genres=["blues", "rock", "country", "funk"],
        descriptive_terms=["bluesy", "rockin'", "earthy", "dominant"],
        color_associations=["orange", "brown", "warm yellow"],
        cultural_contexts=["Blues tradition", "Rock music", "Celtic folk"],
        suggested_tempo_range=(90, 150),
        suggested_dynamics=["mf", "f"],
    ),
    "Aeolian": EmotionalProfile(
        brightness=EmotionalBrightness.DARK,
        energy=EmotionalEnergy.MEDIUM_LOW,
        tension=EmotionalTension.MODERATE,
        primary_emotions=["sadness", "melancholy", "introspection"],
        secondary_emotions=["longing", "seriousness", "depth"],
        typical_genres=["ballads", "classical minor", "alternative rock"],
        descriptive_terms=["sad", "serious", "deep", "natural minor"],
        color_associations=["grey", "dark blue", "brown"],
        cultural_contexts=[
            "Classical minor key music",
            "Folk ballads",
            "Alternative music",
        ],
        suggested_tempo_range=(60, 110),
        suggested_dynamics=["pp", "p", "mp"],
    ),
    "Locrian": EmotionalProfile(
        brightness=EmotionalBrightness.VERY_DARK,
        energy=EmotionalEnergy.LOW,
        tension=EmotionalTension.VERY_TENSE,
        primary_emotions=["instability", "dissonance", "unease"],
        secondary_emotions=["experimental", "avant-garde", "theoretical"],
        typical_genres=["experimental", "avant-garde", "theoretical"],
        descriptive_terms=["unstable", "dissonant", "unresolved", "diminished"],
        color_associations=["black", "dark grey", "void"],
        cultural_contexts=["Experimental music", "Music theory", "Brief passages"],
        suggested_tempo_range=(40, 80),
        suggested_dynamics=["ppp", "pp"],
    ),
}


# Additional profiles for other common scales
SCALE_EMOTIONAL_PROFILES: Dict[str, EmotionalProfile] = {
    "Harmonic Minor": EmotionalProfile(
        brightness=EmotionalBrightness.DARK,
        energy=EmotionalEnergy.MEDIUM_HIGH,
        tension=EmotionalTension.TENSE,
        primary_emotions=["drama", "exoticism", "classical darkness"],
        secondary_emotions=["baroque", "middle eastern", "neoclassical"],
        typical_genres=["classical", "neoclassical metal", "middle eastern"],
        descriptive_terms=["dramatic", "exotic", "classical", "augmented second"],
        color_associations=["burgundy", "dark purple", "gold accents"],
        cultural_contexts=["Classical music", "Middle Eastern music", "Metal"],
        suggested_tempo_range=(70, 140),
        suggested_dynamics=["p", "f", "ff"],
    ),
    "Melodic Minor": EmotionalProfile(
        brightness=EmotionalBrightness.NEUTRAL,
        energy=EmotionalEnergy.MEDIUM,
        tension=EmotionalTension.MODERATE,
        primary_emotions=["sophistication", "jazz", "modernity"],
        secondary_emotions=["complexity", "urban", "contemporary"],
        typical_genres=["jazz", "fusion", "contemporary classical"],
        descriptive_terms=["jazzy", "sophisticated", "modern", "ascending"],
        color_associations=["midnight blue", "silver", "chrome"],
        cultural_contexts=["Jazz tradition", "Contemporary music", "Film scoring"],
        suggested_tempo_range=(60, 140),
        suggested_dynamics=["mp", "mf"],
    ),
    "Pentatonic Major": EmotionalProfile(
        brightness=EmotionalBrightness.BRIGHT,
        energy=EmotionalEnergy.MEDIUM_HIGH,
        tension=EmotionalTension.VERY_RELAXED,
        primary_emotions=["simplicity", "universality", "folk spirit"],
        secondary_emotions=["innocence", "nature", "ancient"],
        typical_genres=["folk", "world music", "children's songs"],
        descriptive_terms=["simple", "universal", "folk", "natural"],
        color_associations=["earth tones", "green", "natural wood"],
        cultural_contexts=["Global folk traditions", "Ancient music", "World music"],
        suggested_tempo_range=(80, 120),
        suggested_dynamics=["mp", "mf"],
    ),
    "Blues Scale": EmotionalProfile(
        brightness=EmotionalBrightness.DARK,
        energy=EmotionalEnergy.MEDIUM,
        tension=EmotionalTension.TENSE,
        primary_emotions=["blues", "soul", "expression", "pain"],
        secondary_emotions=["grit", "authenticity", "storytelling"],
        typical_genres=["blues", "rock", "jazz", "soul"],
        descriptive_terms=["bluesy", "soulful", "expressive", "bent"],
        color_associations=["indigo", "deep blue", "rust"],
        cultural_contexts=["African American tradition", "Blues", "Rock"],
        suggested_tempo_range=(60, 120),
        suggested_dynamics=["mp", "mf", "f"],
    ),
}


# =============================================================================
# CHORD CHARACTER MAPPINGS
# =============================================================================

CHORD_EMOTIONAL_QUALITIES: Dict[str, Dict[str, float]] = {
    # Major family
    "major": {"brightness": 0.8, "tension": 0.2, "stability": 0.9},
    "maj7": {"brightness": 0.85, "tension": 0.3, "stability": 0.8},
    "maj9": {"brightness": 0.9, "tension": 0.35, "stability": 0.75},
    "6": {"brightness": 0.75, "tension": 0.25, "stability": 0.85},
    "add9": {"brightness": 0.82, "tension": 0.3, "stability": 0.8},
    # Minor family
    "minor": {"brightness": 0.3, "tension": 0.4, "stability": 0.8},
    "m7": {"brightness": 0.25, "tension": 0.45, "stability": 0.75},
    "m9": {"brightness": 0.28, "tension": 0.5, "stability": 0.7},
    "m6": {"brightness": 0.35, "tension": 0.35, "stability": 0.8},
    "m(maj7)": {"brightness": 0.2, "tension": 0.7, "stability": 0.6},
    # Dominant family
    "7": {"brightness": 0.6, "tension": 0.6, "stability": 0.5},
    "9": {"brightness": 0.62, "tension": 0.65, "stability": 0.45},
    "13": {"brightness": 0.65, "tension": 0.7, "stability": 0.4},
    "7b9": {"brightness": 0.3, "tension": 0.85, "stability": 0.3},
    "7#9": {"brightness": 0.35, "tension": 0.8, "stability": 0.35},
    # Diminished/Augmented
    "dim": {"brightness": 0.1, "tension": 0.9, "stability": 0.2},
    "dim7": {"brightness": 0.05, "tension": 0.95, "stability": 0.15},
    "aug": {"brightness": 0.5, "tension": 0.8, "stability": 0.3},
    # Suspended
    "sus2": {"brightness": 0.6, "tension": 0.5, "stability": 0.6},
    "sus4": {"brightness": 0.55, "tension": 0.55, "stability": 0.55},
}


# =============================================================================
# CHARACTER ANALYSIS FUNCTIONS
# =============================================================================


def get_mode_emotional_profile(mode_name: str) -> Optional[EmotionalProfile]:
    """
    Get the complete emotional profile for a mode.

    Args:
        mode_name: Name of the mode

    Returns:
        EmotionalProfile or None if not found
    """
    mode_name_lower = mode_name.lower()

    # Check for exact matches first
    for key, profile in MODE_EMOTIONAL_PROFILES.items():
        if key.lower() == mode_name_lower:
            return profile

    # Check for partial matches in mode profiles (longest match first to
    #   avoid substrings)
    sorted_keys = sorted(MODE_EMOTIONAL_PROFILES.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if key.lower() in mode_name_lower:
            return MODE_EMOTIONAL_PROFILES[key]

    # Check scale profiles (exact match first)
    for key, profile in SCALE_EMOTIONAL_PROFILES.items():
        if key.lower() == mode_name_lower:
            return profile

    # Check scale profiles (partial match)
    sorted_scale_keys = sorted(SCALE_EMOTIONAL_PROFILES.keys(), key=len, reverse=True)
    for key in sorted_scale_keys:
        if key.lower() in mode_name_lower:
            return SCALE_EMOTIONAL_PROFILES[key]

    return None


def analyze_progression_character(
    chords: List[str], key_context: Optional[str] = None
) -> ProgressionCharacter:
    """
    Analyze the emotional character of a chord progression.

    Args:
        chords: List of chord symbols
        key_context: Optional key context

    Returns:
        ProgressionCharacter with detailed analysis
    """
    brightness_profile = []
    tension_values = []
    emotional_keywords = set()

    # Analyze each chord
    for chord in chords:
        # Simplified chord type extraction
        chord_type = "major"  # Default
        if "m" in chord.lower() and "maj" not in chord.lower():
            chord_type = "minor"
        elif "dim" in chord.lower():
            chord_type = "dim"
        elif "7" in chord:
            chord_type = "7"
        elif "sus" in chord.lower():
            chord_type = "sus4"

        # Get chord qualities
        qualities = CHORD_EMOTIONAL_QUALITIES.get(
            chord_type, {"brightness": 0.5, "tension": 0.5, "stability": 0.5}
        )

        # Determine brightness
        if qualities["brightness"] > 0.7:
            brightness_profile.append(EmotionalBrightness.BRIGHT)
            emotional_keywords.add("uplifting")
        elif qualities["brightness"] > 0.4:
            brightness_profile.append(EmotionalBrightness.NEUTRAL)
            emotional_keywords.add("balanced")
        else:
            brightness_profile.append(EmotionalBrightness.DARK)
            emotional_keywords.add("melancholic")

        # Add chord-specific emotional keywords
        if chord_type == "7":
            emotional_keywords.add("bluesy")
        elif chord_type == "minor":
            emotional_keywords.add("melancholic")
        elif chord_type == "major":
            emotional_keywords.add("bright")

        tension_values.append(qualities["tension"])

    # Analyze overall trajectory with key context consideration
    brightness_scores = []
    for i, b in enumerate(brightness_profile):
        score = (
            1
            if b == EmotionalBrightness.BRIGHT
            else 0 if b == EmotionalBrightness.NEUTRAL else -1
        )

        # Weight first and last chords more heavily (tonic function emphasis)
        weight = 1.5 if i == 0 or i == len(brightness_profile) - 1 else 1.0
        brightness_scores.append(score * weight)

    avg_brightness = sum(brightness_scores) / sum(
        1.5 if i == 0 or i == len(brightness_profile) - 1 else 1.0
        for i in range(len(brightness_profile))
    )

    # Apply key context bias
    key_bias = 0.0
    if key_context:
        if "minor" in key_context.lower():
            key_bias = -0.4  # Strong bias toward melancholic for minor keys
        elif "major" in key_context.lower():
            key_bias = 0.2  # Mild bias toward bright for major keys

    adjusted_brightness = avg_brightness + key_bias

    # Determine overall mood with adjusted thresholds
    if adjusted_brightness > 0.2:
        overall_mood = "optimistic and bright"
    elif adjusted_brightness < -0.2:
        overall_mood = "melancholic and introspective"
    else:
        overall_mood = "balanced and contemplative"

    # Analyze tension trajectory
    tension_change = (
        tension_values[-1] - tension_values[0] if len(tension_values) > 1 else 0
    )
    if tension_change < -0.3:
        trajectory = "builds tension then resolves"
        emotional_keywords.add("resolution")
    elif tension_change > 0.3:
        trajectory = "increases tension throughout"
        emotional_keywords.add("building")
    else:
        trajectory = "maintains consistent emotional level"
        emotional_keywords.add("stable")

    # Determine cadence strength
    if len(chords) >= 2:
        last_two = chords[-2:]
        # V-I or IV-I patterns are strong cadences
        cadence_strength = (
            0.8 if any(["7" in last_two[0], "IV" in str(last_two)]) else 0.6
        )
    else:
        cadence_strength = 0.3

    # Genre associations based on progression patterns
    genre_associations = []
    chord_str = " ".join(chords)

    if "maj7" in chord_str:
        genre_associations.append("jazz")
    if "7" in chord_str and "maj7" not in chord_str:
        genre_associations.append("blues")
    if all(c in ["C", "G", "Am", "F"] for c in chords):
        genre_associations.append("pop")
    if "dim" in chord_str or "aug" in chord_str:
        genre_associations.append("classical")

    # Suggested instrumentation based on character
    suggested_instrumentation = []
    if "jazz" in genre_associations:
        suggested_instrumentation.extend(["piano", "upright bass", "drums"])
    if "blues" in genre_associations:
        suggested_instrumentation.extend(["electric guitar", "harmonica"])
    if overall_mood == "melancholic and introspective":
        suggested_instrumentation.extend(["strings", "piano"])
    if overall_mood == "optimistic and bright":
        suggested_instrumentation.extend(["acoustic guitar", "brass"])

    return ProgressionCharacter(
        overall_mood=overall_mood,
        emotional_trajectory=trajectory,
        brightness_profile=brightness_profile,
        tension_curve=tension_values,
        cadence_strength=cadence_strength,
        modal_flavor=None,  # Would be set by modal analysis
        genre_associations=genre_associations,
        emotional_keywords=list(emotional_keywords),
        suggested_instrumentation=list(set(suggested_instrumentation)),
    )


def get_character_suggestions(
    desired_emotion: str, current_context: Optional[Dict] = None
) -> CharacterSuggestion:
    """
    Get suggestions for achieving a desired emotional character.

    Args:
        desired_emotion: Target emotion (e.g., "happy", "mysterious", "tense")
        current_context: Optional current musical context

    Returns:
        CharacterSuggestion with specific recommendations
    """
    desired_emotion_lower = desired_emotion.lower()

    # Define emotion to mode mappings
    emotion_mode_map = {
        "happy": ["Ionian", "Mixolydian", "Lydian"],
        "sad": ["Aeolian", "Dorian", "Phrygian"],
        "mysterious": ["Phrygian", "Locrian", "Harmonic Minor"],
        "dreamy": ["Lydian", "Dorian"],
        "tense": ["Locrian", "Phrygian", "Harmonic Minor"],
        "bluesy": ["Mixolydian", "Blues Scale", "Dorian"],
        "exotic": ["Phrygian", "Harmonic Minor", "Phrygian Dominant"],
        "jazzy": ["Dorian", "Melodic Minor", "Lydian"],
        "peaceful": ["Ionian", "Pentatonic Major"],
        "dark": ["Phrygian", "Aeolian", "Locrian"],
        "bright": ["Lydian", "Ionian", "Mixolydian"],
    }

    # Define emotion to progression patterns
    emotion_progression_map = {
        "happy": [["C", "F", "G", "C"], ["I", "V", "vi", "IV"]],
        "sad": [["Am", "F", "C", "G"], ["i", "iv", "i", "v"]],
        "mysterious": [["Em", "F", "Em", "G"], ["i", "bII", "i", "III"]],
        "tense": [["Bdim", "C", "Bdim", "Am"], ["vii°", "I", "vii°", "vi"]],
        "bluesy": [["C7", "F7", "C7", "G7"], ["I7", "IV7", "I7", "V7"]],
    }

    # Find matching modes
    suggested_modes = []
    for emotion_key, modes in emotion_mode_map.items():
        if emotion_key in desired_emotion_lower:
            suggested_modes.extend(modes)

    # Default if no match
    if not suggested_modes:
        suggested_modes = ["Ionian", "Aeolian", "Dorian"]

    # Find matching progressions
    suggested_progressions = []
    for emotion_key, progressions in emotion_progression_map.items():
        if emotion_key in desired_emotion_lower:
            suggested_progressions.extend(progressions)

    # Default progression if no match
    if not suggested_progressions:
        suggested_progressions = [["I", "IV", "V", "I"]]

    # Suggest keys based on emotion
    if "bright" in desired_emotion_lower or "happy" in desired_emotion_lower:
        suggested_keys = ["C major", "G major", "D major"]
    elif "dark" in desired_emotion_lower or "sad" in desired_emotion_lower:
        suggested_keys = ["A minor", "E minor", "D minor"]
    else:
        suggested_keys = ["C major", "A minor"]

    # Modification tips
    modification_tips = []
    if "happy" in desired_emotion_lower:
        modification_tips.append("Use major chords and avoid minor ii and vi")
        modification_tips.append("Keep tempo upbeat (120-140 BPM)")
    elif "sad" in desired_emotion_lower:
        modification_tips.append("Emphasize minor chords and descending motion")
        modification_tips.append("Use slower tempo (60-90 BPM)")
    elif "mysterious" in desired_emotion_lower:
        modification_tips.append("Use chromatic motion and unexpected chord changes")
        modification_tips.append("Add diminished or augmented chords")
    elif "tense" in desired_emotion_lower:
        modification_tips.append("Avoid resolution, use suspended chords")
        modification_tips.append("Employ dissonant intervals")

    # Example songs (simplified examples)
    example_songs_map = {
        "happy": ["Happy - Pharrell Williams", "Good Vibrations - Beach Boys"],
        "sad": ["Mad World - Gary Jules", "Hurt - Johnny Cash"],
        "mysterious": ["Pyramid Song - Radiohead", "Twin Peaks Theme"],
        "bluesy": ["The Thrill Is Gone - B.B. King", "Pride and Joy - SRV"],
        "jazzy": ["Take Five - Dave Brubeck", "So What - Miles Davis"],
    }

    example_songs = []
    for emotion_key, songs in example_songs_map.items():
        if emotion_key in desired_emotion_lower:
            example_songs.extend(songs)

    # Calculate confidence based on how well we matched the emotion
    confidence = 0.9 if suggested_modes and suggested_progressions else 0.6

    return CharacterSuggestion(
        target_emotion=desired_emotion,
        suggested_modes=list(set(suggested_modes))[:5],
        suggested_progressions=suggested_progressions[:3],
        suggested_keys=suggested_keys,
        modification_tips=modification_tips,
        example_songs=example_songs[:3],
        confidence=confidence,
    )


def get_modes_by_brightness(brightness: str) -> List[str]:
    """
    Get all modes matching a brightness level.

    Args:
        brightness: "bright", "neutral", or "dark"

    Returns:
        List of mode names
    """
    matching_modes = []

    # Map string to enum
    brightness_map = {
        "bright": [EmotionalBrightness.BRIGHT, EmotionalBrightness.VERY_BRIGHT],
        "neutral": [EmotionalBrightness.NEUTRAL],
        "dark": [EmotionalBrightness.DARK, EmotionalBrightness.VERY_DARK],
    }

    target_brightness = brightness_map.get(brightness.lower(), [])

    for mode_name, profile in MODE_EMOTIONAL_PROFILES.items():
        if profile.brightness in target_brightness:
            matching_modes.append(mode_name)

    return matching_modes


def describe_emotional_contour(contour_pattern: List[str]) -> str:
    """
    Describe the emotional character of a melodic contour.

    Args:
        contour_pattern: List of 'U' (up), 'D' (down), 'R' (repeat)

    Returns:
        Emotional description of the contour
    """
    if not contour_pattern:
        return "No contour to analyze"

    # Count movements
    ups = contour_pattern.count("U")
    downs = contour_pattern.count("D")
    repeats = contour_pattern.count("R")

    # Analyze overall direction
    if ups > downs * 1.5:
        direction = "ascending"
        emotion = "building energy, excitement, hope"
    elif downs > ups * 1.5:
        direction = "descending"
        emotion = "relaxation, sadness, resolution"
    else:
        direction = "balanced"
        emotion = "stability, contemplation"

    # Add repetition characteristics
    if repeats > len(contour_pattern) * 0.4:
        emotion += ", static, meditative"

    # Analyze patterns
    pattern_str = "".join(contour_pattern)

    if "UUU" in pattern_str:
        emotion += ", dramatic rise"
    if "DDD" in pattern_str:
        emotion += ", dramatic fall"
    if "UDUD" in pattern_str or "DUDU" in pattern_str:
        emotion += ", playful zigzag"
    if pattern_str[:2] == pattern_str[-2:]:
        emotion += ", circular return"

    # Check for arch patterns
    if len(contour_pattern) >= 4:
        mid = len(contour_pattern) // 2
        first_half = contour_pattern[:mid]
        second_half = contour_pattern[mid:]

        first_half_ups = first_half.count("U")
        first_half_downs = first_half.count("D")
        second_half_ups = second_half.count("U")
        second_half_downs = second_half.count("D")

        if first_half_ups > first_half_downs and second_half_downs > second_half_ups:
            return f"Arch shape (rise and fall) - {emotion}, classical balance"
        elif first_half_downs > first_half_ups and second_half_ups > second_half_downs:
            return f"Inverted arch (fall and rise) - {emotion}, tension and release"

    return f"{direction.capitalize()} contour - {emotion}"


# =============================================================================
# INTEGRATION WITH EXISTING ANALYSIS
# =============================================================================


def enhance_analysis_with_character(analysis_result: Dict) -> Dict:
    """
    Enhance an existing analysis result with character information.

    Args:
        analysis_result: Existing analysis result dictionary

    Returns:
        Enhanced result with character analysis
    """
    enhanced = analysis_result.copy()

    # Add mode emotional profile if modal analysis
    if analysis_result.get("type") == "modal" and analysis_result.get("mode"):
        mode_name = analysis_result["mode"]
        emotional_profile = get_mode_emotional_profile(mode_name)

        if emotional_profile:
            enhanced["emotional_profile"] = {
                "brightness": emotional_profile.brightness.value,
                "primary_emotions": emotional_profile.primary_emotions,
                "typical_genres": emotional_profile.typical_genres,
                "suggested_tempo": emotional_profile.suggested_tempo_range,
            }

    # Add progression character if chord progression
    if "progression" in analysis_result:
        progression = analysis_result["progression"]
        character = analyze_progression_character(
            progression, analysis_result.get("key")
        )

        enhanced["progression_character"] = {
            "overall_mood": character.overall_mood,
            "emotional_trajectory": character.emotional_trajectory,
            "emotional_keywords": character.emotional_keywords,
            "suggested_instrumentation": character.suggested_instrumentation,
        }

    return enhanced


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Classes and types
    "EmotionalBrightness",
    "EmotionalEnergy",
    "EmotionalTension",
    "EmotionalProfile",
    "ProgressionCharacter",
    "CharacterSuggestion",
    # Data
    "MODE_EMOTIONAL_PROFILES",
    "SCALE_EMOTIONAL_PROFILES",
    "CHORD_EMOTIONAL_QUALITIES",
    # Functions
    "get_mode_emotional_profile",
    "analyze_progression_character",
    "get_character_suggestions",
    "get_modes_by_brightness",
    "describe_emotional_contour",
    "enhance_analysis_with_character",
]
