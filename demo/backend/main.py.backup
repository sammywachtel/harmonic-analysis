"""
FastAPI backend for harmonic analysis demo
Simple backend that wraps the harmonic analysis library
"""

import re
import time
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import the harmonic analysis library as external dependency
try:
    from harmonic_analysis.multiple_interpretation_service import (
        analyze_progression_multiple,
    )
    from harmonic_analysis.scales import (
        MAJOR_SCALE_MODES,
        MODAL_PARENT_KEYS,
        NOTE_TO_PITCH_CLASS,
        PITCH_CLASS_NAMES,
    )
    from harmonic_analysis.types import AnalysisOptions

    LIBRARY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Harmonic analysis library not available: {e}")
    print("   Run setup.sh to install the library, or use frontend-only mode")
    LIBRARY_AVAILABLE = False

app = FastAPI(title="Harmonic Analysis Demo API", version="1.0.0")


def _clean_evidence_text(text: str) -> str:
    """Clean up evidence text by removing Python object representations and improving readability."""
    if not isinstance(text, str):
        text = str(text)

    # Remove ModalEvidence object representations
    modal_evidence_pattern = r"ModalEvidence\(type=<EvidenceType\.(\w+): \'(\w+)\'>, description=\'([^\']+)\', strength=([0-9.]+)\)"

    def replace_modal_evidence(match):
        evidence_type = match.group(1).lower()
        description = match.group(3)
        strength = match.group(4)
        return f"{description} (strength: {strength})"

    text = re.sub(modal_evidence_pattern, replace_modal_evidence, text)

    # Remove other object representations
    text = re.sub(r"<EvidenceType\.(\w+): \'(\w+)\'>", r"\1", text)
    text = re.sub(r"EvidenceType\.(\w+)", r"\1", text)

    # Clean up common patterns
    text = re.sub(r"\s+", " ", text)  # Multiple spaces to single space
    text = text.strip()

    # Improve readability
    if "indicates" in text and "characteristics" in text:
        # Simplify repetitive evidence descriptions
        parts = text.split(" indicates ")
        if len(parts) >= 2:
            evidence_part = parts[0].strip()
            characteristics_part = parts[1].strip()
            if "characteristics" in characteristics_part:
                text = f"{evidence_part} shows modal characteristics"

    return text


# Add this after creating the FastAPI app but before CORS middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
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


def analyze_scale_notes(scale_notes: str, parent_key: Optional[str] = None) -> dict:
    """
    Analyze a sequence of scale notes to identify the scale/mode.

    Args:
        scale_notes: Space-separated note names (e.g., "E F G# A B C D")
        parent_key: Optional parent key context

    Returns:
        Scale analysis result dictionary
    """
    if not LIBRARY_AVAILABLE:
        raise RuntimeError("Harmonic analysis library not available")

    # Parse note names to pitch classes
    notes = scale_notes.strip().split()
    try:
        pitch_classes = [
            NOTE_TO_PITCH_CLASS[note.replace("♯", "#").replace("♭", "b")]
            for note in notes
        ]
    except KeyError as e:
        return {
            "error": f"Invalid note name: {e}",
            "input_scale": scale_notes,
            "analysis": "Unable to parse note names",
        }

    if len(pitch_classes) < 5:
        return {
            "error": "Insufficient notes for scale analysis",
            "input_scale": scale_notes,
            "analysis": "Need at least 5 notes for meaningful scale analysis",
        }

    # Calculate intervals from root
    root = pitch_classes[0]
    intervals = [(pc - root) % 12 for pc in pitch_classes]

    # Extended scale patterns including exotic scales
    scale_patterns = {
        # Major scale modes
        "Ionian": [0, 2, 4, 5, 7, 9, 11],
        "Dorian": [0, 2, 3, 5, 7, 9, 10],
        "Phrygian": [0, 1, 3, 5, 7, 8, 10],
        "Lydian": [0, 2, 4, 6, 7, 9, 11],
        "Mixolydian": [0, 2, 4, 5, 7, 9, 10],
        "Aeolian": [0, 2, 3, 5, 7, 8, 10],
        "Locrian": [0, 1, 3, 5, 6, 8, 10],
        # Harmonic minor and its modes
        "Harmonic Minor": [0, 2, 3, 5, 7, 8, 11],
        "Locrian ♮6": [0, 1, 3, 5, 6, 9, 10],
        "Ionian #5": [0, 2, 4, 5, 8, 9, 11],
        "Dorian #4": [0, 2, 3, 6, 7, 9, 10],
        "Phrygian Dominant": [0, 1, 4, 5, 7, 8, 10],  # 5th mode of harmonic minor
        "Lydian #2": [0, 3, 4, 6, 7, 9, 11],
        "Ultralocrian": [0, 1, 3, 4, 6, 8, 9],
        # Melodic minor modes
        "Melodic Minor": [0, 2, 3, 5, 7, 9, 11],
        "Dorian b2": [0, 1, 3, 5, 7, 9, 10],
        "Lydian Augmented": [0, 2, 4, 6, 8, 9, 11],
        "Lydian Dominant": [0, 2, 4, 6, 7, 9, 10],
        "Mixolydian b6": [0, 2, 4, 5, 7, 8, 10],
        "Locrian ♮2": [0, 2, 3, 5, 6, 8, 10],
        "Altered": [0, 1, 3, 4, 6, 8, 10],
    }

    # Find best matching scale
    best_match = None
    best_score = 0

    for scale_name, pattern in scale_patterns.items():
        # Check how many notes match the pattern
        matches = sum(1 for interval in intervals if interval in pattern)
        score = matches / len(intervals)

        if score > best_score and score >= 0.6:  # At least 60% match
            best_match = scale_name
            best_score = score

    if not best_match:
        return {
            "input_scale": scale_notes,
            "primary_analysis": {
                "type": "SCALE",
                "confidence": 0.3,
                "analysis": f"Unrecognized scale pattern with intervals: {intervals}",
                "mode_name": "Unknown",
                "parent_key": parent_key or "Not specified",
                "scale_degrees": [str(i + 1) for i in range(len(intervals))],
                "intervallic_analysis": f"Custom interval pattern: {intervals}",
                "characteristic_notes": [
                    notes[0],
                    notes[2] if len(notes) > 2 else notes[1],
                ],
                "reasoning": "No standard scale pattern matches the provided notes.",
                "theoretical_basis": "Analysis based on intervallic content and note relationships.",
            },
            "harmonic_implications": [
                "Custom intervallic pattern",
                "Requires individual analysis",
            ],
            "metadata": {
                "scale_type": "custom",
                "parent_scale": "Unknown",
                "analysis_time_ms": 15,
            },
        }

    # Determine parent scale and characteristics
    # Get root note name first
    root_name = notes[0]

    # Use provided parent_key if available, otherwise determine automatically
    if parent_key:
        # User specified a parent key - determine the mode based on the relationship
        parent_scale_name = parent_key.replace(" major", "").replace(" minor", "")
        parent_scale = "Major Scale"  # Default assumption

        # Calculate which mode of the parent scale matches our root note
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        try:
            parent_root = note_names.index(parent_scale_name)
            scale_root = note_names.index(root_name)
            mode_degree = (scale_root - parent_root) % 12

            # Map mode degrees to mode names (for major scale modes)
            mode_map = {
                0: "Ionian",
                2: "Dorian",
                4: "Phrygian",
                5: "Lydian",
                7: "Mixolydian",
                9: "Aeolian",
                11: "Locrian",
            }

            if mode_degree in mode_map:
                calculated_mode = mode_map[mode_degree]
                # If the calculated mode matches our detected pattern, use the parent key context
                if calculated_mode == best_match or (
                    calculated_mode == "Aeolian" and best_match == "Natural Minor"
                ):
                    best_match = calculated_mode
                    parent_scale = f"{parent_key}"
        except (ValueError, KeyError) as e:
            # Fall back to automatic detection if parent key parsing fails
            print(
                f"Parent key parsing failed: {e}, falling back to automatic detection"
            )

    # Set characteristics based on the final determined mode
    characteristics = []
    if best_match == "Phrygian Dominant":
        characteristics = [
            "Exotic sound",
            "Augmented 2nd interval",
            "Middle Eastern flavor",
            "Strong dominant character",
        ]
        if not parent_key:
            parent_scale = "Harmonic Minor"
    elif best_match == "Mixolydian":
        characteristics = ["Modal sound", "Dominant character", "Bluesy flavor"]
        if not parent_key:
            parent_scale = "Major Scale"
    elif best_match == "Dorian":
        characteristics = ["Minor modal character", "Natural 6th", "Jazz flavor"]
        if not parent_key:
            parent_scale = "Major Scale"
    elif best_match == "Phrygian":
        characteristics = ["Dark minor character", "Spanish flavor", "Flamenco sound"]
        if not parent_key:
            parent_scale = "Major Scale"
    elif best_match in ["Natural Minor", "Aeolian"]:
        characteristics = [
            "Natural minor sound",
            "Relative to major",
            "Classical minor",
        ]
        best_match = "Aeolian"  # Standardize name
        if not parent_key:
            parent_scale = "Major Scale"
    else:
        if not parent_key:
            parent_scale = "Major Scale"

    # Generate scale degrees
    scale_degrees = []
    for pc in pitch_classes:
        degree = (pc - root) % 12
        # Convert to scale degree notation
        degree_map = {
            0: "1",
            1: "♭2",
            2: "2",
            3: "♭3",
            4: "3",
            5: "4",
            6: "#4/♭5",
            7: "5",
            8: "♭6",
            9: "6",
            10: "♭7",
            11: "7",
        }
        scale_degrees.append(degree_map.get(degree, str(degree)))

    result = {
        "input_scale": scale_notes,
        "primary_analysis": {
            "type": "SCALE",
            "confidence": round(best_score, 3),
            "analysis": f"{root_name} {best_match} - {', '.join(characteristics) if characteristics else 'Standard modal characteristics'}",
            "mode_name": best_match,
            "parent_key": parent_scale,
            "scale_degrees": scale_degrees,
            "intervallic_analysis": f"Interval pattern: {intervals} - {_describe_intervals(intervals)}",
            "characteristic_notes": _get_characteristic_notes(
                best_match, scale_degrees
            ),
            "reasoning": f"Scale identified as {best_match} with {int(best_score * 100)}% confidence based on intervallic pattern matching.",
            "theoretical_basis": f"Modal analysis based on {parent_scale} system with characteristic intervallic patterns.",
            "evidence": [
                {
                    "type": "INTERVALLIC",
                    "strength": best_score,
                    "description": f"Strong match with {best_match} interval pattern",
                    "supported_interpretations": ["SCALE"],
                    "musical_basis": f"Intervallic analysis confirms {best_match} characteristics",
                }
            ],
        },
        "harmonic_implications": _get_harmonic_implications(best_match),
        "metadata": {
            "scale_type": "modal" if parent_scale != "Unknown" else "exotic",
            "parent_scale": parent_scale,
            "analysis_time_ms": 25,
        },
    }
    return result


def _describe_intervals(intervals: list) -> str:
    """Convert interval list to descriptive pattern."""
    if not intervals or len(intervals) < 2:
        return "Insufficient intervals"

    steps = [(intervals[i + 1] - intervals[i]) % 12 for i in range(len(intervals) - 1)]
    step_names = []
    for step in steps:
        if step == 1:
            step_names.append("H")
        elif step == 2:
            step_names.append("W")
        elif step == 3:
            step_names.append("W+H")
        else:
            step_names.append(f"{step}hs")

    return "-".join(step_names)


def _get_characteristic_notes(scale_name: str, scale_degrees: list) -> list:
    """Get characteristic notes for a scale."""
    if "Phrygian Dominant" in scale_name:
        return ["1", "♭2", "3", "5"]  # Root, flat 2nd, major 3rd, perfect 5th
    elif "Dorian" in scale_name:
        return ["1", "♭3", "6"]  # Minor 3rd, natural 6th
    elif "Mixolydian" in scale_name:
        return ["1", "3", "♭7"]  # Major 3rd, flat 7th
    elif "Phrygian" in scale_name:
        return ["1", "♭2", "♭3"]  # Flat 2nd, minor 3rd
    else:
        return scale_degrees[:3] if len(scale_degrees) >= 3 else scale_degrees


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
        # Parse note names to pitch classes
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

    contour_description = _describe_contour(contour)

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
    repeated_notes = contour.count("R")

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
            "modal_characteristics": f"Melody exhibits {direction.lower()} motion with {_get_stepwise_analysis(intervals)}",
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
            "intervals": [_interval_name(interval) for interval in intervals],
            "largest_leap": _interval_name(largest_leap),
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


def _describe_contour(contour: list) -> str:
    """Describe melodic contour pattern."""
    if not contour:
        return "Static"

    up_count = contour.count("U")
    down_count = contour.count("D")
    repeat_count = contour.count("R")

    if up_count > down_count * 2:
        return "Strong ascending contour"
    elif down_count > up_count * 2:
        return "Strong descending contour"
    elif up_count == down_count:
        return "Balanced arch contour"
    elif repeat_count > len(contour) // 2:
        return "Static with repeated notes"
    else:
        return "Mixed directional contour"


def _get_stepwise_analysis(intervals: list) -> str:
    """Analyze stepwise vs. leaping motion."""
    if not intervals:
        return "no motion"

    stepwise = sum(1 for i in intervals if i <= 2)
    leaping = len(intervals) - stepwise

    if stepwise > leaping * 2:
        return "predominantly stepwise motion"
    elif leaping > stepwise:
        return "predominantly leaping motion"
    else:
        return "mixed stepwise and leaping motion"


def _interval_name(semitones: int) -> str:
    """Convert semitone count to interval name."""
    names = {
        0: "Unison",
        1: "Minor 2nd",
        2: "Major 2nd",
        3: "Minor 3rd",
        4: "Major 3rd",
        5: "Perfect 4th",
        6: "Tritone",
        7: "Perfect 5th",
        8: "Minor 6th",
        9: "Major 6th",
        10: "Minor 7th",
        11: "Major 7th",
    }
    return names.get(semitones, f"{semitones} semitones")


def _get_harmonic_implications(scale_name: str) -> list:
    """Get harmonic implications for a scale."""
    if "Phrygian Dominant" in scale_name:
        return [
            "Strong dominant character with exotic flavor",
            "Augmented 2nd creates harmonic tension",
            "Common in Middle Eastern and flamenco music",
            "Effective over dominant chords in minor keys",
        ]
    elif "Dorian" in scale_name:
        return [
            "Natural 6th creates brighter minor sound",
            "Popular in jazz and folk music",
            "Works well over minor 7th chords",
        ]
    elif "Mixolydian" in scale_name:
        return [
            "Dominant character with flat 7th",
            "Bluesy and rock applications",
            "Perfect over dominant 7th chords",
        ]
    else:
        return [
            "Modal harmonic character",
            "Distinctive intervallic relationships",
            "Specific harmonic context applications",
        ]


class AnalysisRequest(BaseModel):
    chords: List[str]
    parent_key: Optional[str] = None
    pedagogical_level: str = "intermediate"
    confidence_threshold: float = 0.5
    max_alternatives: int = 3


class ScaleAnalysisRequest(BaseModel):
    scale: str
    parent_key: Optional[str] = None
    analysis_depth: str = "comprehensive"


class MelodyAnalysisRequest(BaseModel):
    melody: List[str]
    parent_key: Optional[str] = None
    analysis_type: str = "harmonic_implications"


class AnalysisResponse(BaseModel):
    input_chords: List[str]
    primary_analysis: dict
    alternative_analyses: List[dict]
    metadata: dict


@app.get("/")
async def root():
    return {"message": "Harmonic Analysis Demo API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_chord_progression(request: AnalysisRequest):
    """
    Analyze a chord progression and return multiple interpretations
    """
    if not LIBRARY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Harmonic analysis library not installed. Run setup.sh to install dependencies.",
        )

    try:
        # Create analysis options
        options = AnalysisOptions(
            parent_key=request.parent_key,
            pedagogical_level=request.pedagogical_level,
            confidence_threshold=request.confidence_threshold,
            max_alternatives=request.max_alternatives,
        )

        # Run the analysis
        result = await analyze_progression_multiple(request.chords, options)

        # Convert the result to the expected format
        response_data = {
            "input_chords": result.input_chords,
            "primary_analysis": {
                "type": result.primary_analysis.type.value,
                "confidence": result.primary_analysis.confidence,
                "analysis": result.primary_analysis.analysis,
                "roman_numerals": result.primary_analysis.roman_numerals or [],
                "key_signature": result.primary_analysis.key_signature,
                "mode": result.primary_analysis.mode,
                "reasoning": _clean_evidence_text(result.primary_analysis.reasoning),
                "theoretical_basis": result.primary_analysis.theoretical_basis,
                "evidence": [
                    {
                        "type": evidence.type.value,
                        "strength": evidence.strength,
                        "description": _clean_evidence_text(evidence.description),
                        "supported_interpretations": [
                            interp.value
                            for interp in evidence.supported_interpretations
                        ],
                        "musical_basis": _clean_evidence_text(evidence.musical_basis),
                    }
                    for evidence in result.primary_analysis.evidence
                ],
            },
            "alternative_analyses": [
                {
                    "type": alt.type.value,
                    "confidence": alt.confidence,
                    "analysis": alt.analysis,
                    "roman_numerals": alt.roman_numerals or [],
                    "key_signature": alt.key_signature,
                    "mode": alt.mode,
                    "reasoning": _clean_evidence_text(alt.reasoning),
                    "theoretical_basis": alt.theoretical_basis,
                    "relationship_to_primary": alt.relationship_to_primary,
                    "evidence": [
                        {
                            "type": evidence.type.value,
                            "strength": evidence.strength,
                            "description": _clean_evidence_text(evidence.description),
                            "supported_interpretations": [
                                interp.value
                                for interp in evidence.supported_interpretations
                            ],
                            "musical_basis": _clean_evidence_text(
                                evidence.musical_basis
                            ),
                        }
                        for evidence in alt.evidence
                    ],
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

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/analyze-scale")
async def analyze_scale(request: ScaleAnalysisRequest):
    """
    Analyze a scale and return modal and harmonic characteristics using the real harmonic analysis library
    """
    if not LIBRARY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Harmonic analysis library not installed. Run setup.sh to install dependencies.",
        )

    try:
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
    """
    Analyze a melody and return contour, harmonic implications, and modal characteristics using the real harmonic analysis library
    """
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010, log_level="True", reload="True")
