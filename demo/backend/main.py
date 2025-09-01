"""FastAPI backend for harmonic analysis demo.

Simple backend that wraps the harmonic analysis library.
"""

import re
import time
from typing import List, Literal, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

# Import the harmonic analysis library as external dependency
try:
    # Import local formatting utilities (moved from library)
    from formatting import (
        format_scale_melody_analysis,
    )

    from harmonic_analysis import (  # Import utilities from library instead of duplicating
        AnalysisOptions,
        analyze_progression_multiple,
        analyze_scale_melody,
        describe_contour,
        get_interval_name,
        # Character and Emotional Analysis
        analyze_progression_character,
        get_mode_emotional_profile,
        get_character_suggestions,
        get_modes_by_brightness,
        describe_emotional_contour,
        CharacterSuggestion,
        EmotionalProfile,
        ProgressionCharacter,
    )

    # Import additional utilities from submodules
    from harmonic_analysis.utils.analysis_helpers import (
        analyze_intervallic_content,
        get_scale_reference_data
    )

    LIBRARY_AVAILABLE = True

    # Add fallback implementations for missing utility functions
    def format_suggestions_for_api(suggestions):
        """Format analysis suggestions for API response."""
        if not suggestions:
            return None
        return {
            "parent_key_suggestions": [
                {
                    "key": suggestion.suggested_key,
                    "confidence": suggestion.confidence,
                    "reasoning": suggestion.reason,
                    "improvement_type": suggestion.potential_improvement,
                }
                for suggestion in (suggestions.parent_key_suggestions or [])
            ],
            "general_suggestions": [],
        }

    def get_all_reference_data():
        """Get all music theory reference data from the library."""
        from harmonic_analysis.utils.music_theory_constants import (
            ALL_MODES, ALL_MAJOR_KEYS, ALL_MINOR_KEYS,
            MODAL_CHARACTERISTICS, SCALE_TO_CHORD_MAPPINGS, SEMITONE_TO_INTERVAL_NAME,
            get_modal_characteristics
        )
        from harmonic_analysis.scales import ALL_SCALE_SYSTEMS, PITCH_CLASS_NAMES
        from harmonic_analysis.utils.scales import KEY_SIGNATURES
        from harmonic_analysis.utils.roman_numeral_converter import convert_roman_numerals_to_chords, is_roman_numeral_progression

        return {
            "modes": {
                "all_modes": ALL_MODES,
                "mode_characteristics": {
                    mode: {
                        "characteristic_degrees": get_modal_characteristics(mode).characteristic_degrees,
                        "harmonic_implications": get_modal_characteristics(mode).harmonic_implications,
                        "typical_applications": get_modal_characteristics(mode).typical_applications,
                        "brightness": get_modal_characteristics(mode).brightness,
                        "chord_types": SCALE_TO_CHORD_MAPPINGS.get(mode, [])
                    } for mode in ALL_MODES
                }
            },
            "keys": {
                "major_keys": ALL_MAJOR_KEYS,
                "minor_keys": ALL_MINOR_KEYS,
            },
            "scales": {
                "scale_systems": ALL_SCALE_SYSTEMS,
                "pitch_classes": PITCH_CLASS_NAMES,
            },
            "intervals": {
                "semitone_to_name": SEMITONE_TO_INTERVAL_NAME,
                "abbreviations": dict(enumerate(["P1", "m2", "M2", "m3", "M3", "P4", "TT", "P5", "m6", "M6", "m7", "M7"]))
            },
            "chord_mappings": SCALE_TO_CHORD_MAPPINGS,
            "key_signatures": KEY_SIGNATURES,
        }

    def get_modal_chord_progressions():
        """Get modal chord progressions reference using library data."""
        from harmonic_analysis.utils.music_theory_constants import (
            SCALE_TO_CHORD_MAPPINGS, get_modal_characteristics, ALL_MODES
        )

        # Build comprehensive modal progressions from library data
        progressions = {}
        for mode in ALL_MODES:
            characteristics = get_modal_characteristics(mode)
            chord_types = SCALE_TO_CHORD_MAPPINGS.get(mode, [])

            # Create mode-appropriate progressions based on characteristics
            if mode == "Ionian":
                progressions[mode] = ["I-vi-IV-V", "vi-IV-I-V", "I-IV-vi-V", "ii-V-I"]
            elif mode == "Dorian":
                progressions[mode] = ["i-IV-i-♭VII", "i-♭VII-IV-i", "i-ii-♭VII-i"]
            elif mode == "Phrygian":
                progressions[mode] = ["i-♭II-♭VII-i", "i-♭VII-♭VI-i", "♭II-i-♭VII-i"]
            elif mode == "Lydian":
                progressions[mode] = ["I-II-I-V", "I-♯iv°-V-I", "I-II-V-I"]
            elif mode == "Mixolydian":
                progressions[mode] = ["I-♭VII-IV-I", "I-IV-♭VII-I", "I-♭VII-♭VII-I"]
            elif mode == "Aeolian":
                progressions[mode] = ["i-♭VI-♭VII-i", "i-iv-♭VII-♭VI", "i-♭VII-♭VI-♭VII"]
            elif mode == "Locrian":
                progressions[mode] = ["i°-♭II-♭VII-i°", "♭II-♭VI-♭VII-i°"]
            else:
                progressions[mode] = ["Modal progression examples not available"]

        return {
            "modal_progressions": progressions,
            "mode_chord_mappings": SCALE_TO_CHORD_MAPPINGS,
            "characteristic_info": {
                mode: {
                    "characteristic_degrees": get_modal_characteristics(mode).characteristic_degrees,
                    "harmonic_implications": get_modal_characteristics(mode).harmonic_implications[:2]  # Top 2
                } for mode in ALL_MODES
            }
        }

    def create_scale_reference_endpoint_data(scale_name):
        """Create reference data for a specific scale using library data."""
        from harmonic_analysis.scales import ALL_SCALE_SYSTEMS, PITCH_CLASS_NAMES
        from harmonic_analysis.utils.music_theory_constants import get_modal_characteristics, SCALE_TO_CHORD_MAPPINGS

        # Find the scale in available systems
        scale_intervals = None
        scale_system = None

        for system_name, scales in ALL_SCALE_SYSTEMS.items():
            if scale_name in scales:
                scale_intervals = scales[scale_name]
                scale_system = system_name
                break

        if not scale_intervals:
            return {
                "error": f"Scale '{scale_name}' not found in library",
                "available_scales": [scale for scales in ALL_SCALE_SYSTEMS.values() for scale in scales.keys()]
            }

        # Convert intervals to note names (starting from C)
        notes = []
        for interval in scale_intervals:
            notes.append(PITCH_CLASS_NAMES[interval])

        # Get modal characteristics if available
        characteristics = None
        try:
            characteristics = get_modal_characteristics(scale_name)
        except:
            pass

        # Get chord types
        chord_types = SCALE_TO_CHORD_MAPPINGS.get(scale_name, [])

        return {
            "scale_name": scale_name,
            "scale_system": scale_system,
            "intervals_semitones": scale_intervals,
            "notes_from_C": notes,
            "step_pattern": [
                scale_intervals[i+1] - scale_intervals[i]
                for i in range(len(scale_intervals)-1)
            ] + [12 - scale_intervals[-1]],  # Last interval back to octave
            "characteristics": {
                "characteristic_degrees": characteristics.characteristic_degrees if characteristics else [],
                "harmonic_implications": characteristics.harmonic_implications if characteristics else [],
                "typical_applications": characteristics.typical_applications if characteristics else [],
                "brightness": characteristics.brightness if characteristics else "unknown"
            } if characteristics else None,
            "chord_types": chord_types,
            "related_modes": [
                mode for mode in ALL_SCALE_SYSTEMS.get("Major", {}).keys()
                if mode != scale_name
            ] if scale_system == "Major" else []
        }

    def get_characteristic_degrees(mode):
        """Get characteristic degrees for a mode using library data."""
        try:
            characteristics = get_modal_characteristics(mode)
            return characteristics.characteristic_degrees
        except:
            # Fallback for unknown modes
            return ["1", "3", "5"]

    def get_harmonic_implications(chords, mode):
        """Get harmonic implications for chord progression using library data."""
        try:
            characteristics = get_modal_characteristics(mode)
            return characteristics.harmonic_implications
        except:
            # Fallback for unknown modes
            return [f"Implies {mode} tonality", "Suggests functional harmony"]

except ImportError as e:
    print(f"⚠️  Harmonic analysis library not available: {e}")
    print("   Run setup.sh to install the library, or use frontend-only mode")
    LIBRARY_AVAILABLE = False

# Helper function to update analysis descriptions with original Roman numerals
def _update_analysis_with_original_romans(result, original_romans):
    """Update analysis descriptions to use original Roman numerals instead of library-generated ones."""
    # Convert original Romans to formatted version with superscripts
    formatted_romans = [_format_roman_numeral_superscript(roman) for roman in original_romans]
    roman_sequence = " - ".join(formatted_romans)
    
    # Update primary analysis description
    if hasattr(result.primary_analysis, 'analysis') and result.primary_analysis.analysis:
        original_analysis = result.primary_analysis.analysis
        # Replace the Roman numeral sequence in the analysis description
        # Pattern: looks for sequences like "V7/ii - ii⁶ - V7/ii⁶ - ii - I⁶ - V - I"
        pattern = r'([IV]+[♭♯]?[⁰⁺⁶⁴⁷]*/[iv]+[⁰⁺⁶⁴⁷]*|[IV]+[♭♯]?[⁰⁺⁶⁴⁷]*)(?: - ([IV]+[♭♯]?[⁰⁺⁶⁴⁷]*/[iv]+[⁰⁺⁶⁴⁷]*|[IV]+[♭♯]?[⁰⁺⁶⁴⁷]*))*'
        
        # For now, simple replacement: find and replace the Roman numeral sequence
        # This assumes the analysis follows the pattern "TYPE progression: ROMANS. ..."
        if ': ' in original_analysis and '. ' in original_analysis:
            parts = original_analysis.split(': ', 1)
            if len(parts) == 2:
                prefix = parts[0] + ': '
                rest = parts[1].split('. ', 1)
                if len(rest) == 2:
                    suffix = '. ' + rest[1]
                    updated_analysis = prefix + roman_sequence + suffix
                    result.primary_analysis.analysis = updated_analysis
    
    return result


def _format_roman_numeral_superscript(roman):
    """Convert Roman numeral notation to use proper superscripts."""
    # Convert regular numbers to superscript equivalents
    superscript_map = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
    }
    
    result = roman
    for digit, superscript in superscript_map.items():
        result = result.replace(digit, superscript)
    
    return result


app = FastAPI(title="Harmonic Analysis Demo API", version="1.0.0")


# Custom exception handler for validation errors
# This ensures that unknown parameters are rejected with helpful error messages
# instead of being silently ignored. Common mistakes like 'key_context' instead
# of 'parent_key' will now trigger clear error messages with suggestions.
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors with helpful messages.

    Rejects unknown parameters and provides suggestions for common mistakes:
    - 'key_context' → suggests 'parent_key'
    - 'key' → suggests 'parent_key'
    - 'level' → suggests 'pedagogical_level'
    """
    errors = exc.errors()
    error_messages = []

    for error in errors:
        if error['type'] == 'extra_forbidden':
            # Extract the unknown field name
            unknown_field = error['loc'][0] if error['loc'] else 'unknown'

            # Provide helpful suggestions for common mistakes
            suggestions = []
            if unknown_field == 'key_context':
                suggestions.append("Did you mean 'parent_key'? The API uses 'parent_key' for key context.")
            elif unknown_field == 'key':
                suggestions.append("Did you mean 'parent_key'? Use 'parent_key' to specify the key context.")
            elif unknown_field == 'level':
                suggestions.append("Did you mean 'pedagogical_level'? Valid values are: beginner, intermediate, advanced")

            error_msg = f"Unknown parameter '{unknown_field}' is not allowed."
            if suggestions:
                error_msg += f" {suggestions[0]}"
            error_messages.append(error_msg)
        else:
            # Handle other validation errors
            field = '.'.join(str(loc) for loc in error['loc'])
            error_messages.append(f"{field}: {error['msg']}")

    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "detail": error_messages,
            "message": "Request contains invalid or unknown parameters. Please check the API documentation."
        }
    )


# Add this after creating the FastAPI app but before CORS middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log HTTP requests with timing information."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(
        f"{request.method} {request.url} - {response.status_code} - {process_time:.4f}s"
    )
    return response


# ... rest of your CORS middleware setup ...
# Basic CORS setup for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3010"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _convert_brightness_to_float(brightness_enum) -> float:
    """Convert EmotionalBrightness enum to float value 0-1."""
    brightness_map = {
        "very_bright": 1.0,
        "bright": 0.75,
        "neutral": 0.5,
        "dark": 0.25,
        "very_dark": 0.0
    }
    return brightness_map.get(brightness_enum.value, 0.5)


def _convert_energy_to_float(energy_enum) -> float:
    """Convert EmotionalEnergy enum to float value 0-1."""
    energy_map = {
        "high": 1.0,
        "medium_high": 0.75,
        "medium": 0.5,
        "medium_low": 0.25,
        "low": 0.0
    }
    return energy_map.get(energy_enum.value, 0.5)


def _convert_tension_to_float(tension_enum) -> float:
    """Convert EmotionalTension enum to float value 0-1."""
    tension_map = {
        "very_tense": 1.0,
        "tense": 0.75,
        "moderate": 0.5,
        "relaxed": 0.25,
        "very_relaxed": 0.0
    }
    return tension_map.get(tension_enum.value, 0.5)


def analyze_scale_notes(scale_notes: str, parent_key: Optional[str] = None) -> dict:
    """
    Analyze a sequence of scale notes using the sophisticated scale analysis library.

    Args:
        scale_notes: Space-separated note names (e.g., "E F G# A B C D")
        parent_key: Optional parent key context

    Returns:
        Scale analysis result dictionary with contextual classification
    """
    if not LIBRARY_AVAILABLE:
        raise RuntimeError("Harmonic analysis library not available")

    # Parse note names
    notes = scale_notes.strip().split()

    if len(notes) < 3:
        return {
            "error": "Insufficient notes for scale analysis",
            "input_scale": scale_notes,
            "analysis": "Need at least 3 notes for meaningful scale analysis",
        }

    try:
        # Use the library's sophisticated analysis
        result = analyze_scale_melody(notes, parent_key, melody=False)

        # Debug logging for parent key logic
        print(
            f"🎯 Scale analysis result: classification='{result.classification}', "
            f"parent_scales={result.parent_scales}"
        )
        print(f"🎯 Modal labels: {result.modal_labels}")
        print(f"🎯 Non-diatonic pitches: {result.non_diatonic_pitches}")

        # Use library's comprehensive formatting - this replaces all the manual formatting above!
        formatted_result = format_scale_melody_analysis(result)

        # Return the properly formatted result from the library
        return formatted_result

    except Exception as e:
        # Fallback to basic analysis if sophisticated analysis fails
        print(f"⚠️  Sophisticated analysis failed: {e}, falling back to basic analysis")
        return _basic_scale_analysis(scale_notes, parent_key)


def _basic_scale_analysis(scale_notes: str, parent_key: Optional[str] = None) -> dict:
    """Fallback basic analysis if sophisticated analysis fails."""
    notes = scale_notes.strip().split()
    return {
        "input_scale": scale_notes,
        "primary_analysis": {
            "type": "SCALE",
            "confidence": 0.5,
            "analysis": f"Basic analysis of {len(notes)} notes",
            "mode_name": "Unknown",
            "parent_key": parent_key or "Not specified",
            "scale_degrees": [str(i + 1) for i in range(len(notes))],
            "reasoning": "Fallback analysis due to processing error",
            "theoretical_basis": "Basic note sequence analysis",
        },
        "harmonic_implications": ["Requires manual analysis"],
        "metadata": {"scale_type": "basic", "analysis_time_ms": 5},
        "alternative_analyses": [],
    }


# Functions moved to library utilities - using library versions now


def analyze_melody_notes(
    melody_notes: List[str], parent_key: Optional[str] = None
) -> dict:
    """
    Analyze a melody sequence to identify contour, scale context, and harmonic implications.

    Args:
        melody_notes: List of note names (e.g., ["C", "D", "E", "F", "G", "A", "B", "C"])
        parent_key: Optional parent key context

    Returns:
        Melody analysis result dictionary
    """
    if not LIBRARY_AVAILABLE:
        raise RuntimeError("Harmonic analysis library not available")

    if len(melody_notes) < 3:
        return {
            "error": "Insufficient notes for melody analysis",
            "input_melody": melody_notes,
            "analysis": "Need at least 3 notes for meaningful melody analysis",
        }

    try:
        # Parse note names to pitch classes - import NOTE_TO_PITCH_CLASS locally
        from harmonic_analysis.utils.chord_parser import NOTE_TO_PITCH_CLASS
        pitch_classes = [
            NOTE_TO_PITCH_CLASS[note.replace("♯", "#").replace("♭", "b")]
            for note in melody_notes
        ]
    except KeyError as e:
        return {
            "error": f"Invalid note name: {e}",
            "input_melody": melody_notes,
            "analysis": "Unable to parse note names",
        }

    # Analyze melodic contour
    contour = []
    for i in range(1, len(pitch_classes)):
        prev = pitch_classes[i - 1]
        curr = pitch_classes[i]
        diff = (curr - prev) % 12
        if diff == 0:
            contour.append("R")  # Repeated
        elif diff <= 6:
            contour.append("U")  # Up
        else:
            contour.append("D")  # Down

    contour_description = describe_contour(contour)

    # Calculate intervals between consecutive notes
    intervals = []
    for i in range(1, len(pitch_classes)):
        interval = (pitch_classes[i] - pitch_classes[i - 1]) % 12
        intervals.append(interval)

    # Determine melodic range
    min_pc = min(pitch_classes)
    max_pc = max(pitch_classes)
    melodic_range = (max_pc - min_pc) % 12

    # Find largest leap
    largest_leap = max(intervals) if intervals else 0
    if largest_leap > 6:
        largest_leap = 12 - largest_leap  # Convert to smaller interval

    # Determine directional tendency
    up_movements = contour.count("U")
    down_movements = contour.count("D")

    if up_movements > down_movements:
        direction = "Generally ascending"
    elif down_movements > up_movements:
        direction = "Generally descending"
    else:
        direction = "Balanced movement"

    # Analyze scale context using unique notes
    unique_notes = list(
        dict.fromkeys(melody_notes)
    )  # Preserve order, remove duplicates
    scale_analysis = analyze_scale_notes(" ".join(unique_notes), parent_key)

    # Determine harmonic implications
    if (
        "primary_analysis" in scale_analysis
        and "mode_name" in scale_analysis["primary_analysis"]
    ):
        scale_mode = scale_analysis["primary_analysis"]["mode_name"]
        harmonic_implications = f"Suggests {scale_mode} tonality based on note content"
    else:
        harmonic_implications = "Chromatic or atonal harmonic implications"

    # Analyze phrase structure
    phrase_length = len(melody_notes)
    if phrase_length <= 4:
        phrase_type = "Motif"
    elif phrase_length <= 8:
        phrase_type = "Short phrase"
    elif phrase_length <= 16:
        phrase_type = "Standard phrase"
    else:
        phrase_type = "Extended phrase"

    # Identify potential cadential points (large leaps or repeated notes at end)
    cadential_points = []
    if len(intervals) > 0:
        if intervals[-1] == 0:  # Ends on repeated note
            cadential_points.append("Final note repetition")
        elif abs(intervals[-1]) >= 7:  # Large leap at end
            cadential_points.append("Final large interval")
        if any(interval >= 7 for interval in intervals):
            cadential_points.append("Internal large leaps")

    return {
        "input_melody": melody_notes,
        "primary_analysis": {
            "type": "MELODY",
            "confidence": 0.8,
            "analysis": f"Melodic analysis of {len(melody_notes)}-note sequence with {contour_description}",
            "melodic_contour": contour_description,
            "scale_context": scale_analysis.get("primary_analysis", {}).get(
                "mode_name", "Undetermined"
            )
            + " context",
            "modal_characteristics": f"Melody exhibits {direction.lower()} motion with stepwise analysis",
            "phrase_analysis": f"{phrase_type} ({phrase_length} notes) with {direction.lower()}",
            "harmonic_implications": harmonic_implications,
            "reasoning": f"Melodic analysis reveals {phrase_length} notes with {contour_description} and {largest_leap}-semitone maximum interval.",
            "theoretical_basis": "Melodic analysis based on contour, intervallic content, scale membership, and phrase structure.",
            "evidence": [
                {
                    "type": "STRUCTURAL",
                    "strength": 0.8,
                    "description": f"Clear melodic direction and {phrase_type.lower()} structure",
                    "supported_interpretations": ["MELODY"],
                    "musical_basis": "Melodic contour and phrase structure analysis",
                }
            ],
        },
        "intervallic_analysis": {
            "intervals": [get_interval_name(abs(interval)) for interval in intervals],
            "largest_leap": get_interval_name(abs(largest_leap)),
            "melodic_range": f"{melodic_range} semitones",
            "directional_tendency": direction,
        },
        "phrase_structure": {
            "phrase_length": f"{phrase_length} notes",
            "cadential_points": (
                cadential_points if cadential_points else ["No strong cadential points"]
            ),
            "motivic_content": f"{'Stepwise' if all(i <= 2 for i in intervals) else 'Mixed stepwise and leaping'} motion pattern",
        },
        "metadata": {
            "melody_type": "stepwise" if all(i <= 2 for i in intervals) else "mixed",
            "note_count": phrase_length,
            "analysis_type": "harmonic_implications",
            "parent_key": parent_key,
            "analysis_time_ms": 30,
        },
    }


def generate_character_analysis(chords, primary_type, key_signature, mode, confidence):
    """Generate character analysis for a chord progression."""
    try:
        # Use library's character analysis
        # Combine key_signature and mode into single key_context
        key_context = f"{key_signature or 'C major'} ({mode or 'Ionian'})" if mode and mode != "Ionian" else key_signature or "C major"
        character_result = analyze_progression_character(
            chords,
            key_context
        )

        # Get mode emotional profile
        if mode and mode != "Unknown":
            emotional_profile = get_mode_emotional_profile(mode)
        else:
            emotional_profile = None

        # Get character suggestions
        suggestions = get_character_suggestions(
            character_result.overall_mood,
            emotional_profile.brightness if emotional_profile else 0.5
        )

        return {
            "primary_character": {
                "name": character_result.overall_mood,
                "confidence": character_result.cadence_strength,  # Use cadence_strength as confidence
                "description": character_result.emotional_trajectory,
                "musical_elements": character_result.emotional_keywords,
            },
            "emotional_profile": {
                "brightness": _convert_brightness_to_float(emotional_profile.brightness) if emotional_profile else 0.5,
                "energy": _convert_energy_to_float(emotional_profile.energy) if emotional_profile else 0.5,
                "tension": _convert_tension_to_float(emotional_profile.tension) if emotional_profile else 0.5,
                "warmth": 0.5,  # Default value since warmth doesn't exist in EmotionalProfile
                "description": ", ".join(emotional_profile.primary_emotions) if emotional_profile and emotional_profile.primary_emotions else "Neutral emotional character",
            } if emotional_profile else None,
            "character_suggestions": [
                {
                    "character": suggestions.target_emotion,
                    "description": f"Suggestions for achieving {suggestions.target_emotion} character",
                    "musical_techniques": suggestions.modification_tips,
                    "complementary_modes": suggestions.suggested_modes,
                }
            ],
            "emotional_contour": character_result.emotional_trajectory,
        }

    except Exception as e:
        print(f"⚠️  Character analysis failed: {e}")
        return {
            "primary_character": {
                "name": "Neutral",
                "confidence": 0.3,
                "description": "Character analysis unavailable",
                "musical_elements": [],
            },
            "error": str(e),
        }


def get_mode_character_profile(mode_name):
    """Get character profile for a specific mode."""
    try:
        # Clean mode name
        clean_mode = mode_name.replace(" context", "").strip()

        # Get emotional profile
        emotional_profile = get_mode_emotional_profile(clean_mode)

        # Get brightness ranking context - get all modes sorted by brightness
        # We'll construct a full brightness ordering
        bright_modes = get_modes_by_brightness("bright")
        neutral_modes = get_modes_by_brightness("neutral")
        dark_modes = get_modes_by_brightness("dark")
        brightness_modes = bright_modes + neutral_modes + dark_modes

        mode_rank = next(
            (i for i, mode in enumerate(brightness_modes) if mode.lower() == clean_mode.lower()),
            3  # Default to middle rank
        )

        return {
            "mode_name": clean_mode,
            "emotional_profile": {
                "brightness": emotional_profile.brightness.value if hasattr(emotional_profile.brightness, 'value') else str(emotional_profile.brightness),
                "energy": emotional_profile.energy.value if hasattr(emotional_profile.energy, 'value') else str(emotional_profile.energy),
                "tension": emotional_profile.tension.value if hasattr(emotional_profile.tension, 'value') else str(emotional_profile.tension),
                "primary_emotions": emotional_profile.primary_emotions,
                "typical_genres": emotional_profile.typical_genres,
                "description": ", ".join(emotional_profile.primary_emotions) if emotional_profile.primary_emotions else "No description available",
            },
            "brightness_rank": mode_rank + 1,  # 1-based ranking
            "total_modes": len(brightness_modes),
            "brightness_context": f"Ranks {mode_rank + 1} of {len(brightness_modes)} in brightness",
        }

    except Exception as e:
        print(f"⚠️  Mode character profile failed: {e}")
        return {
            "mode_name": mode_name,
            "error": str(e),
            "brightness_rank": 4,
            "total_modes": 7,
        }


def get_modes_by_mood_keywords(mood_keywords):
    """Get modes that match mood keywords using brightness and emotional profiles."""
    try:
        # Get all modes ranked by brightness
        bright_modes = get_modes_by_brightness("bright")
        neutral_modes = get_modes_by_brightness("neutral")
        dark_modes = get_modes_by_brightness("dark")
        brightness_modes = bright_modes + neutral_modes + dark_modes

        # Define mood keyword mappings
        mood_mappings = {
            "bright": bright_modes,  # Bright modes
            "happy": bright_modes,   # Also bright modes
            "sad": dark_modes,    # Dark modes
            "dark": dark_modes,   # Dark modes
            "mysterious": ["Phrygian", "Locrian", "Aeolian"],
            "uplifting": ["Lydian", "Ionian"],
            "melancholy": ["Aeolian", "Dorian"],
            "energetic": ["Mixolydian", "Dorian"],
            "peaceful": ["Ionian", "Aeolian"],
            "tense": ["Locrian", "Phrygian"],
        }

        # Find matching modes
        matching_modes = set()
        for keyword in mood_keywords:
            if keyword in mood_mappings:
                matching_modes.update(mood_mappings[keyword])

        # Get emotional profiles for matches
        results = []
        for mode in matching_modes:
            try:
                profile = get_mode_emotional_profile(mode)
                results.append({
                    "mode": mode,
                    "emotional_profile": {
                        "brightness": profile.brightness.value if hasattr(profile.brightness, 'value') else str(profile.brightness),
                        "energy": profile.energy.value if hasattr(profile.energy, 'value') else str(profile.energy),
                        "tension": profile.tension.value if hasattr(profile.tension, 'value') else str(profile.tension),
                        "primary_emotions": profile.primary_emotions,
                        "description": ", ".join(profile.primary_emotions) if profile.primary_emotions else "No description available",
                    },
                    "match_keywords": [
                        keyword for keyword in mood_keywords
                        if keyword in mood_mappings and mode in mood_mappings[keyword]
                    ],
                })
            except Exception:
                continue

        return {
            "mood_keywords": mood_keywords,
            "matching_modes": results,
            "total_matches": len(results),
        }

    except Exception as e:
        print(f"⚠️  Mood keyword analysis failed: {e}")
        return {
            "mood_keywords": mood_keywords,
            "error": str(e),
            "matching_modes": [],
        }


async def generate_enhancement_suggestions(chords, primary_analysis):
    """Generate real enhancement suggestions using the harmonic analysis library."""
    try:
        # Import the real suggestion engines from the library
        from harmonic_analysis.services.bidirectional_suggestion_engine import BidirectionalSuggestionEngine

        # Extract analysis information
        analysis_type = getattr(primary_analysis, 'type', 'FUNCTIONAL')
        if hasattr(analysis_type, 'value'):
            analysis_type = analysis_type.value

        confidence = getattr(primary_analysis, 'confidence', 0.5)
        key_signature = getattr(primary_analysis, 'key_signature', None)
        mode = getattr(primary_analysis, 'mode', 'Ionian')
        roman_numerals = getattr(primary_analysis, 'roman_numerals', [])

        suggestions = []

        # Use the library's bidirectional suggestion engine for key suggestions
        if LIBRARY_AVAILABLE:
            suggestion_engine = BidirectionalSuggestionEngine()
            options = AnalysisOptions(parent_key=key_signature)

            # Get key-related suggestions (add/remove/change key context)
            analysis_suggestions = await suggestion_engine.generate_bidirectional_suggestions(
                chords, options, confidence, roman_numerals
            )

            # Convert library suggestions to demo format
            for key_suggestion in analysis_suggestions.parent_key_suggestions:
                suggestions.append({
                    "type": "key_context",
                    "description": key_suggestion.reason,
                    "example": f"Try analyzing in {key_suggestion.suggested_key}",
                    "difficulty": "intermediate",
                    "confidence": key_suggestion.confidence,
                    "potential_improvement": key_suggestion.potential_improvement,
                })

        # Use character analysis for emotional enhancement suggestions
        if LIBRARY_AVAILABLE:
            try:
                # Get character analysis for current progression
                character_analysis = analyze_progression_character(chords)
                current_emotion = character_analysis.overall_mood

                # Get suggestions for common desired emotions
                emotional_targets = ["mysterious", "uplifting", "melancholy", "energetic"]

                for emotion in emotional_targets:
                    if emotion.lower() != current_emotion.lower():
                        character_suggestion = get_character_suggestions(emotion)

                        if character_suggestion.suggested_modes:
                            mode_suggestions = ", ".join(character_suggestion.suggested_modes[:2])
                            suggestions.append({
                                "type": "emotional_enhancement",
                                "description": f"For a more {emotion} sound, consider {mode_suggestions} modes",
                                "example": f"Current: {current_emotion} → Target: {emotion}",
                                "difficulty": "intermediate",
                                "confidence": 0.7,
                            })
                            break  # Only add one emotional suggestion

            except Exception as e:
                # Character analysis failed, skip emotional suggestions
                print(f"Character analysis failed: {e}")

        # If no real suggestions available, return minimal response
        if not suggestions:
            return {
                "suggestions": [],
                "analysis_context": {
                    "type": analysis_type,
                    "confidence": confidence,
                    "key_signature": key_signature,
                    "mode": mode,
                },
                "suggestion_categories": [],
                "note": "Enhancement suggestions require library analysis capabilities"
            }

        # Limit suggestions
        suggestions = suggestions[:4]  # Max 4 real suggestions

        return {
            "suggestions": suggestions,
            "analysis_context": {
                "type": analysis_type,
                "confidence": confidence,
                "key_signature": key_signature,
                "mode": mode,
            },
            "suggestion_categories": list(set(s["type"] for s in suggestions)),
        }

    except Exception as e:
        print(f"⚠️  Enhancement suggestion failed: {e}")
        return {
            "suggestions": [],
            "analysis_context": {
                "type": getattr(primary_analysis, 'type', 'UNKNOWN'),
                "confidence": getattr(primary_analysis, 'confidence', 0.0),
                "key_signature": getattr(primary_analysis, 'key_signature', None),
                "mode": getattr(primary_analysis, 'mode', 'Unknown'),
            },
            "suggestion_categories": [],
            "error": str(e),
        }


# More functions moved to library utilities - using library versions


# Suggestions formatting moved to library - using format_suggestions_for_api() now


# Harmonic implications moved to library - using get_harmonic_implications() now


class AnalysisRequest(BaseModel):
    """Request model for chord progression analysis."""

    chords: List[str]
    parent_key: Optional[str] = None
    pedagogical_level: str = "intermediate"
    confidence_threshold: float = 0.5
    max_alternatives: int = 3

    class Config:
        extra = "forbid"  # Reject unknown fields


class ScaleAnalysisRequest(BaseModel):
    """Request model for scale analysis."""

    scale: str
    parent_key: Optional[str] = None
    analysis_depth: str = "comprehensive"

    class Config:
        extra = "forbid"  # Reject unknown fields


class MelodyAnalysisRequest(BaseModel):
    """Request model for melody analysis."""

    melody: List[str]
    parent_key: Optional[str] = None
    analysis_type: str = "harmonic_implications"

    class Config:
        extra = "forbid"  # Reject unknown fields


class AnalysisResponse(BaseModel):
    """Response model for analysis results."""

    input_chords: List[str]
    primary_analysis: dict
    alternative_analyses: List[dict]
    metadata: dict


class UnifiedAnalysisRequest(BaseModel):
    """Request model for unified analysis with character integration."""

    input_data: str  # Could be chords, scale, or melody
    analysis_type: str  # 'progression', 'scale', or 'melody'
    parent_key: Optional[str] = None
    pedagogical_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    confidence_threshold: float = 0.5
    max_alternatives: int = 3
    include_character: bool = True
    include_enhancements: bool = True
    scale_mode: str = "scale"  # 'scale' or 'melody' for scale analysis

    class Config:
        extra = "forbid"  # Reject unknown fields


class CharacterAnalysisRequest(BaseModel):
    """Request model for character-only analysis."""

    input_data: str
    analysis_type: str  # 'progression', 'mode', or 'mood'

    class Config:
        extra = "forbid"  # Reject unknown fields


class EnhancementRequest(BaseModel):
    """Request model for enhancement suggestions."""

    chords: List[str]
    current_analysis: Optional[dict] = None

    class Config:
        extra = "forbid"  # Reject unknown fields


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Harmonic Analysis Demo API", "status": "running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_chord_progression(request: AnalysisRequest):
    """Analyze a chord progression and return multiple interpretations."""
    if not LIBRARY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Harmonic analysis library not installed. Run setup.sh to install dependencies.",
        )

    try:
        # Import Roman numeral conversion functions
        from harmonic_analysis.utils.roman_numeral_converter import convert_roman_numerals_to_chords, is_roman_numeral_progression
        
        # Check if input contains Roman numerals and convert if needed
        chord_input = " ".join(request.chords)
        original_roman_numerals = None
        
        if is_roman_numeral_progression(chord_input):
            # Roman numerals detected - parent key is required
            if not request.parent_key:
                raise HTTPException(
                    status_code=400, 
                    detail="Parent key is required when using Roman numeral notation. Please specify a parent key (e.g., 'C major', 'A minor')."
                )
            
            # Store original Roman numerals to preserve in output
            original_roman_numerals = request.chords.copy()
            
            # Convert Roman numerals to chord symbols
            try:
                converted_chords = convert_roman_numerals_to_chords(chord_input, request.parent_key)
                print(f"🎼 Converted Roman numerals '{chord_input}' to chord symbols: {converted_chords}")
                print(f"🎼 Preserving original Roman numerals: {original_roman_numerals}")
            except Exception as convert_error:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to convert Roman numerals: {convert_error}. Please check your Roman numeral notation and parent key."
                )
        else:
            # Use chord symbols as-is
            converted_chords = request.chords
        
        # Create analysis options
        options = AnalysisOptions(
            parent_key=request.parent_key,
            pedagogical_level=request.pedagogical_level,
            confidence_threshold=request.confidence_threshold,
            max_alternatives=request.max_alternatives,
        )

        # Run the analysis with converted chords
        result = await analyze_progression_multiple(converted_chords, options)
        
        # If we have original Roman numerals, update the analysis description 
        if original_roman_numerals:
            result = _update_analysis_with_original_romans(result, original_roman_numerals)

        # Debug logging for suggestions
        print(f"🎯 Analysis result has suggestions: {result.suggestions is not None}")
        if result.suggestions:
            print(f"🎯 Suggestions object: {result.suggestions}")
            print(
                f"🎯 Parent key suggestions exist: {result.suggestions.parent_key_suggestions is not None}"
            )
            if result.suggestions.parent_key_suggestions:
                print(
                    f"🎯 Parent key suggestions length: {len(result.suggestions.parent_key_suggestions)}"
                )
                print(
                    f"🎯 First suggestion: {result.suggestions.parent_key_suggestions[0]}"
                )

        formatted_suggestions = None
        if result.suggestions and result.suggestions.parent_key_suggestions:
            # Simplified direct formatting for now
            print(f"🎯 Creating manual formatted suggestions...")
            formatted_suggestions = {
                "parent_key_suggestions": [
                    {
                        "key": result.suggestions.parent_key_suggestions[
                            0
                        ].suggested_key,
                        "confidence": result.suggestions.parent_key_suggestions[
                            0
                        ].confidence,
                        "reasoning": result.suggestions.parent_key_suggestions[
                            0
                        ].reason,
                        "detected_pattern": getattr(
                            result.suggestions.parent_key_suggestions[0],
                            "detected_pattern",
                            "unknown",
                        ),
                        "improvement_type": result.suggestions.parent_key_suggestions[
                            0
                        ].potential_improvement,
                    }
                ],
                "unnecessary_key_suggestions": [],
                "key_change_suggestions": [],
                "general_suggestions": [],
            }
            print(f"🎯 Manual formatted suggestions: {formatted_suggestions}")
        else:
            print(f"🎯 No suggestions to format")

        # Convert the result to the expected format including enhanced fields
        response_data = {
            "input_chords": result.input_chords,
            "primary_analysis": {
                "type": result.primary_analysis.type.value,
                "confidence": result.primary_analysis.confidence,
                "analysis": result.primary_analysis.analysis,
                "roman_numerals": [_format_roman_numeral_superscript(roman) for roman in original_roman_numerals] if original_roman_numerals else (result.primary_analysis.roman_numerals or []),
                "key_signature": result.primary_analysis.key_signature,
                "mode": result.primary_analysis.mode,
                "reasoning": result.primary_analysis.reasoning,
                "theoretical_basis": result.primary_analysis.theoretical_basis,
                "evidence": [
                    {
                        "type": evidence.type.value,
                        "strength": evidence.strength,
                        "description": evidence.description,
                        "supported_interpretations": [
                            interp.value
                            for interp in evidence.supported_interpretations
                        ],
                        "musical_basis": evidence.musical_basis,
                    }
                    for evidence in result.primary_analysis.evidence
                ],
                # Enhanced analysis fields
                "modal_characteristics": getattr(
                    result.primary_analysis, "modal_characteristics", []
                ),
                "parent_key_relationship": getattr(
                    result.primary_analysis, "parent_key_relationship", None
                ),
                "secondary_dominants": getattr(
                    result.primary_analysis, "secondary_dominants", []
                ),
                "borrowed_chords": getattr(
                    result.primary_analysis, "borrowed_chords", []
                ),
                "chromatic_mediants": getattr(
                    result.primary_analysis, "chromatic_mediants", []
                ),
                "cadences": getattr(result.primary_analysis, "cadences", []),
                "chord_functions": getattr(
                    result.primary_analysis, "chord_functions", []
                ),
                "contextual_classification": getattr(
                    result.primary_analysis, "contextual_classification", None
                ),
                "functional_confidence": getattr(
                    result.primary_analysis, "functional_confidence", None
                ),
                "modal_confidence": getattr(
                    result.primary_analysis, "modal_confidence", None
                ),
                "chromatic_confidence": getattr(
                    result.primary_analysis, "chromatic_confidence", None
                ),
            },
            # Include bidirectional suggestions in the response
            "suggestions": format_suggestions_for_api(result.suggestions),
            "alternative_analyses": [
                {
                    "type": alt.type.value,
                    "confidence": alt.confidence,
                    "analysis": alt.analysis,
                    "roman_numerals": [_format_roman_numeral_superscript(roman) for roman in original_roman_numerals] if original_roman_numerals else (alt.roman_numerals or []),
                    "key_signature": alt.key_signature,
                    "mode": alt.mode,
                    "reasoning": alt.reasoning,
                    "theoretical_basis": alt.theoretical_basis,
                    "relationship_to_primary": alt.relationship_to_primary,
                    "evidence": [
                        {
                            "type": evidence.type.value,
                            "strength": evidence.strength,
                            "description": evidence.description,
                            "supported_interpretations": [
                                interp.value
                                for interp in evidence.supported_interpretations
                            ],
                            "musical_basis": evidence.musical_basis,
                        }
                        for evidence in alt.evidence
                    ],
                    # Enhanced fields for alternatives too
                    "modal_characteristics": getattr(alt, "modal_characteristics", []),
                    "parent_key_relationship": getattr(
                        alt, "parent_key_relationship", None
                    ),
                    "secondary_dominants": getattr(alt, "secondary_dominants", []),
                    "borrowed_chords": getattr(alt, "borrowed_chords", []),
                    "chromatic_mediants": getattr(alt, "chromatic_mediants", []),
                    "cadences": getattr(alt, "cadences", []),
                    "chord_functions": getattr(alt, "chord_functions", []),
                    "contextual_classification": getattr(
                        alt, "contextual_classification", None
                    ),
                    "functional_confidence": getattr(
                        alt, "functional_confidence", None
                    ),
                    "modal_confidence": getattr(alt, "modal_confidence", None),
                    "chromatic_confidence": getattr(alt, "chromatic_confidence", None),
                }
                for alt in result.alternative_analyses
            ],
            "metadata": {
                "total_interpretations_considered": result.metadata.total_interpretations_considered,
                "confidence_threshold": result.metadata.confidence_threshold,
                "show_alternatives": result.metadata.show_alternatives,
                "pedagogical_level": result.metadata.pedagogical_level.value,
                "analysis_time_ms": result.metadata.analysis_time_ms,
            },
        }

        # Debug logging for final response
        print(f"🎯 Response includes suggestions: {'suggestions' in response_data}")
        if "suggestions" in response_data and response_data["suggestions"]:
            print(f"🎯 Suggestions data: {response_data['suggestions']}")

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/analyze-scale")
async def analyze_scale(request: ScaleAnalysisRequest):
    """Analyze a scale and return modal and harmonic characteristics."""
    if not LIBRARY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Harmonic analysis library not installed. Run setup.sh to install dependencies.",
        )

    try:
        # Debug logging to see what we received
        print(
            f"🔍 Scale analysis request: scale='{request.scale}', "
            f"parent_key='{request.parent_key}'"
        )

        # Use the real scale analysis function
        result = analyze_scale_notes(request.scale, request.parent_key)

        # Add metadata safely
        if "metadata" not in result:
            result["metadata"] = {}
        result["metadata"]["analysis_depth"] = request.analysis_depth
        result["alternative_analyses"] = (
            []
        )  # For consistency with frontend expectations

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scale analysis failed: {str(e)}")


@app.post("/api/analyze-melody")
async def analyze_melody(request: MelodyAnalysisRequest):
    """Analyze a melody and return contour, harmonic implications, and modal characteristics."""
    if not LIBRARY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Harmonic analysis library not installed. Run setup.sh to install dependencies.",
        )

    try:
        # Use the real melody analysis function
        result = analyze_melody_notes(request.melody, request.parent_key)

        # Add metadata
        result["metadata"]["analysis_type"] = request.analysis_type
        result["alternative_analyses"] = (
            []
        )  # For consistency with frontend expectations

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Melody analysis failed: {str(e)}")


@app.post("/api/analyze/unified")
async def analyze_unified(request: UnifiedAnalysisRequest):
    """Unified analysis endpoint combining harmonic, character, and enhancement analysis."""
    if not LIBRARY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Harmonic analysis library not installed. Run setup.sh to install dependencies.",
        )

    try:
        # Parse input data based on analysis type
        if request.analysis_type == "progression":
            chords = request.input_data.strip().split()

            # Debug logging for parent key validation
            print(f"🔍 UNIFIED ENDPOINT: Analyzing {chords} with parent_key='{request.parent_key}'")

            # Create analysis options
            options = AnalysisOptions(
                parent_key=request.parent_key,
                include_character=request.include_character,
                include_enhancements=request.include_enhancements,
                pedagogical_level=request.pedagogical_level,
                confidence_threshold=request.confidence_threshold,
                max_alternatives=request.max_alternatives,
                force_multiple_interpretations=False
            )

            # Run harmonic analysis
            harmonic_result = await analyze_progression_multiple(chords, options)

            # Debug the result
            print(f"🔍 UNIFIED RESULT: Primary confidence={harmonic_result.primary_analysis.confidence:.3f}, type={harmonic_result.primary_analysis.type}, key={harmonic_result.primary_analysis.key_signature}")
            print(f"🔍 CHROMATIC ELEMENTS: secondary_dominants={harmonic_result.primary_analysis.secondary_dominants}, borrowed_chords={harmonic_result.primary_analysis.borrowed_chords}")
            if harmonic_result.suggestions:
                print(f"🔍 SUGGESTIONS EXIST: parent_key_suggestions={len(harmonic_result.suggestions.parent_key_suggestions) if harmonic_result.suggestions.parent_key_suggestions else 0}")
                if harmonic_result.suggestions.parent_key_suggestions:
                    for s in harmonic_result.suggestions.parent_key_suggestions:
                        print(f"   - Suggestion: {s.suggested_key} (confidence: {s.confidence:.3f})")
            else:
                print("🔍 NO SUGGESTIONS GENERATED")
            if hasattr(harmonic_result.primary_analysis, 'parent_key_validation'):
                print(f"🔍 Parent key validation: {harmonic_result.primary_analysis.parent_key_validation}")

            # Extract primary analysis for character analysis
            primary_type = harmonic_result.primary_analysis.type.value
            primary_confidence = harmonic_result.primary_analysis.confidence
            key_signature = harmonic_result.primary_analysis.key_signature
            mode = harmonic_result.primary_analysis.mode

            # Generate character analysis if requested
            character_analysis = None
            if request.include_character:
                character_analysis = generate_character_analysis(
                    chords, primary_type, key_signature, mode, primary_confidence
                )

            # Generate enhancement suggestions if requested
            enhancement_suggestions = None
            if request.include_enhancements:
                print(f"🔍 GENERATING ENHANCEMENTS for {chords} with parent_key={request.parent_key}")
                enhancement_suggestions = await generate_enhancement_suggestions(
                    chords, harmonic_result.primary_analysis
                )
                print(f"🔍 ENHANCEMENT RESULT: {enhancement_suggestions}")

            # Combine results
            return {
                "input_data": request.input_data,
                "analysis_type": request.analysis_type,
                "harmonic_analysis": {
                    "primary_analysis": {
                        "type": primary_type,
                        "confidence": primary_confidence,
                        "analysis": harmonic_result.primary_analysis.analysis,
                        "key_signature": key_signature,
                        "mode": mode,
                        "reasoning": harmonic_result.primary_analysis.reasoning,
                    },
                    "alternative_analyses": [
                        {
                            "type": alt.type.value,
                            "confidence": alt.confidence,
                            "analysis": alt.analysis,
                            "key_signature": alt.key_signature,
                            "mode": alt.mode,
                        }
                        for alt in harmonic_result.alternative_analyses[:2]  # Limit for compactness
                    ],
                },
                "character_analysis": character_analysis,
                "enhancement_suggestions": enhancement_suggestions,
                "metadata": {
                    "pedagogical_level": request.pedagogical_level,
                    "include_character": request.include_character,
                    "include_enhancements": request.include_enhancements,
                    "analysis_time_ms": harmonic_result.metadata.analysis_time_ms,
                },
            }

        elif request.analysis_type == "scale":
            # Scale analysis with character integration
            scale_result = analyze_scale_notes(request.input_data, request.parent_key)

            character_analysis = None
            if request.include_character and "primary_analysis" in scale_result:
                mode = scale_result["primary_analysis"].get("mode_name", "Unknown")
                if mode != "Unknown":
                    character_analysis = get_mode_character_profile(mode)

            return {
                "input_data": request.input_data,
                "analysis_type": request.analysis_type,
                "scale_analysis": scale_result,
                "character_analysis": character_analysis,
                "metadata": {
                    "pedagogical_level": request.pedagogical_level,
                    "scale_mode": request.scale_mode,
                    "include_character": request.include_character,
                },
            }

        elif request.analysis_type == "melody":
            # Melody analysis with character integration
            melody_notes = request.input_data.strip().split()
            melody_result = analyze_melody_notes(melody_notes, request.parent_key)

            character_analysis = None
            if request.include_character and "primary_analysis" in melody_result:
                scale_context = melody_result["primary_analysis"].get("scale_context", "")
                if "context" in scale_context:
                    mode = scale_context.replace(" context", "")
                    character_analysis = get_mode_character_profile(mode)

            return {
                "input_data": request.input_data,
                "analysis_type": request.analysis_type,
                "melody_analysis": melody_result,
                "character_analysis": character_analysis,
                "metadata": {
                    "pedagogical_level": request.pedagogical_level,
                    "include_character": request.include_character,
                },
            }

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported analysis type: {request.analysis_type}"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unified analysis failed: {str(e)}")


@app.post("/api/analyze/character")
async def analyze_character(request: CharacterAnalysisRequest):
    """Character-only analysis endpoint for mood and emotional profiling."""
    if not LIBRARY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Harmonic analysis library not installed. Run setup.sh to install dependencies.",
        )

    try:
        if request.analysis_type == "progression":
            chords = request.input_data.strip().split()
            # Quick harmonic analysis to get mode/key context
            options = AnalysisOptions(confidence_threshold=0.3)
            harmonic_result = await analyze_progression_multiple(chords, options)

            primary_type = harmonic_result.primary_analysis.type.value
            key_signature = harmonic_result.primary_analysis.key_signature
            mode = harmonic_result.primary_analysis.mode
            confidence = harmonic_result.primary_analysis.confidence

            character_analysis = generate_character_analysis(
                chords, primary_type, key_signature, mode, confidence
            )

        elif request.analysis_type == "mode":
            # Direct mode character analysis
            mode_name = request.input_data.strip()
            character_analysis = get_mode_character_profile(mode_name)

        elif request.analysis_type == "mood":
            # Mood-based analysis using brightness scale
            mood_keywords = request.input_data.strip().lower().split()
            character_analysis = get_modes_by_mood_keywords(mood_keywords)

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported character analysis type: {request.analysis_type}"
            )

        return {
            "input_data": request.input_data,
            "analysis_type": request.analysis_type,
            "character_analysis": character_analysis,
            "metadata": {
                "analysis_focus": "character_only",
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Character analysis failed: {str(e)}")


@app.post("/api/analyze/enhancements")
async def analyze_enhancements(request: EnhancementRequest):
    """Enhancement suggestions endpoint for chord progression improvements."""
    if not LIBRARY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Harmonic analysis library not installed. Run setup.sh to install dependencies.",
        )

    try:
        # If current analysis is provided, use it; otherwise analyze fresh
        if request.current_analysis:
            primary_analysis = request.current_analysis
        else:
            options = AnalysisOptions(confidence_threshold=0.4)
            harmonic_result = await analyze_progression_multiple(request.chords, options)
            primary_analysis = harmonic_result.primary_analysis

        # Generate enhancement suggestions
        enhancements = await generate_enhancement_suggestions(request.chords, primary_analysis)

        return {
            "input_chords": request.chords,
            "enhancement_suggestions": enhancements,
            "metadata": {
                "suggestion_count": len(enhancements.get("suggestions", [])),
                "analysis_basis": "harmonic_function" if request.current_analysis else "fresh_analysis",
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhancement analysis failed: {str(e)}")


@app.get("/api/reference/all")
async def get_music_theory_reference():
    """Get complete music theory reference data for building reference applications."""
    if not LIBRARY_AVAILABLE:
        raise HTTPException(
            status_code=503, detail="Harmonic analysis library not installed."
        )

    try:
        return get_all_reference_data()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Reference data retrieval failed: {str(e)}"
        )


@app.get("/api/reference/modes")
async def get_modal_reference():
    """Get modal reference data including chord progressions."""
    if not LIBRARY_AVAILABLE:
        raise HTTPException(
            status_code=503, detail="Harmonic analysis library not installed."
        )

    try:
        return get_modal_chord_progressions()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Modal reference retrieval failed: {str(e)}"
        )


@app.get("/api/reference/scale/{scale_name}")
async def get_scale_reference(scale_name: str):
    """Get comprehensive reference data for a specific scale/mode."""
    if not LIBRARY_AVAILABLE:
        raise HTTPException(
            status_code=503, detail="Harmonic analysis library not installed."
        )

    try:
        return create_scale_reference_endpoint_data(scale_name)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Scale reference retrieval failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010, log_level="info")
