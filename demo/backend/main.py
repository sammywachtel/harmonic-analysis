"""FastAPI backend for harmonic analysis demo.

Simple backend that wraps the harmonic analysis library.
"""

import time
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import the harmonic analysis library as external dependency
try:
    # Import local formatting utilities (moved from library)
    from formatting import (
        format_scale_melody_analysis,
    )

    from harmonic_analysis import (  # Import utilities from library instead of duplicating
        NOTE_TO_PITCH_CLASS,
        AnalysisOptions,
        analyze_intervallic_content,
        analyze_progression_multiple,
        analyze_scale_melody,
        create_scale_reference_endpoint_data,
        describe_contour,
        format_suggestions_for_api,
        get_all_reference_data,
        get_characteristic_degrees,
        get_harmonic_implications,
        get_interval_name,
        get_modal_chord_progressions,
    )

    LIBRARY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Harmonic analysis library not available: {e}")
    print("   Run setup.sh to install the library, or use frontend-only mode")
    LIBRARY_AVAILABLE = False

app = FastAPI(title="Harmonic Analysis Demo API", version="1.0.0")


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


class ScaleAnalysisRequest(BaseModel):
    """Request model for scale analysis."""

    scale: str
    parent_key: Optional[str] = None
    analysis_depth: str = "comprehensive"


class MelodyAnalysisRequest(BaseModel):
    """Request model for melody analysis."""

    melody: List[str]
    parent_key: Optional[str] = None
    analysis_type: str = "harmonic_implications"


class AnalysisResponse(BaseModel):
    """Response model for analysis results."""

    input_chords: List[str]
    primary_analysis: dict
    alternative_analyses: List[dict]
    metadata: dict


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
        # Create analysis options
        options = AnalysisOptions(
            parent_key=request.parent_key,
            pedagogical_level=request.pedagogical_level,
            confidence_threshold=request.confidence_threshold,
            max_alternatives=request.max_alternatives,
        )

        # Run the analysis
        result = await analyze_progression_multiple(request.chords, options)

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
                "roman_numerals": result.primary_analysis.roman_numerals or [],
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
                    "roman_numerals": alt.roman_numerals or [],
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
