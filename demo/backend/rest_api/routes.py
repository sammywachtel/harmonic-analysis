"""
REST API route handlers for harmonic analysis endpoints.

Opening move: Define all HTTP endpoints for the API.
These routes handle chord/roman/melody/scale analysis plus file uploads.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import asdict
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from harmonic_analysis import ALL_KEYS
from harmonic_analysis.api.analysis import analyze_melody, analyze_scale
from harmonic_analysis.core.pattern_engine.glossary_provider import GlossaryProvider
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

# Educational imports with graceful fallback
try:
    from harmonic_analysis.educational import EducationalService, is_available

    EDUCATIONAL_AVAILABLE = is_available()
except ImportError:
    EDUCATIONAL_AVAILABLE = False
    EducationalService = None  # type: ignore

from .models import (
    MelodyRequest,
    ProfileInfo,
    ProfileResponse,
    ProgressionRequest,
    ScaleRequest,
)

# Kickoff: Constants from demo
MISSING_SCALE_KEY_MSG = (
    "Scale analysis requires a key context. Please provide --key parameter."
)
MISSING_MELODY_KEY_MSG = (
    "Melody analysis requires a key context. Please provide --key parameter."
)


# Main play: Initialize services
def get_service() -> PatternAnalysisService:
    """Get or create the pattern analysis service."""
    return PatternAnalysisService()


def get_glossary_provider() -> GlossaryProvider:
    """Get or create the glossary service."""
    return GlossaryProvider()


# Helper functions
def resolve_key_input(key_input: Optional[str]) -> Optional[str]:
    """
    Resolve key input from user to normalized format.

    Handles special values like "None" or "(auto)" by returning None.
    """
    if not key_input or key_input.strip().lower() in ["none", "(auto)"]:
        return None
    return key_input.strip()


def summarize_envelope(envelope: Any, include_raw: bool = False) -> str:
    """
    Summarize analysis envelope for display.

    Big play: Extract key information from the analysis result
    and format it for human consumption.
    """
    if not envelope or not envelope.primary:
        return "No analysis result available."

    primary = envelope.primary
    lines = []

    # Header
    if hasattr(primary, "key") and primary.key:
        lines.append(f"Key: {primary.key}")

    # Roman numerals
    if hasattr(primary, "roman_numerals") and primary.roman_numerals:
        romans_str = " - ".join(primary.roman_numerals)
        lines.append(f"Analysis: {romans_str}")

    # Interpretation
    if hasattr(primary, "interpretation") and primary.interpretation:
        lines.append(f"Interpretation: {primary.interpretation}")

    # Confidence
    if hasattr(primary, "confidence"):
        lines.append(f"Confidence: {primary.confidence:.2f}")

    return "\n".join(lines) if lines else "Analysis complete."


def _serialize_envelope(
    envelope: Any, include_educational: bool = True
) -> Dict[str, Any]:
    """
    Serialize analysis envelope to JSON-compatible dictionary.

    Victory lap: Convert analysis result to API response
    format with convenient summary fields for scale/melody data.
    """
    try:
        analysis_dict = envelope.to_dict()
    except Exception as e:
        analysis_dict = {"error": f"Serialization failed: {e}"}

    # Add convenient summary fields for scale/melody
    summary_fields = {}
    if envelope.primary:
        if (
            hasattr(envelope.primary, "scale_summary")
            and envelope.primary.scale_summary
        ):
            summary_fields["scale_analysis"] = {
                "mode": envelope.primary.scale_summary.detected_mode,
                "parent_key": envelope.primary.scale_summary.parent_key,
                "characteristics": envelope.primary.scale_summary.characteristic_notes,
                "notes": envelope.primary.scale_summary.notes,
            }
        if (
            hasattr(envelope.primary, "melody_summary")
            and envelope.primary.melody_summary
        ):
            melody = envelope.primary.melody_summary
            summary_fields["melody_analysis"] = {
                "contour": melody.contour,
                "range_semitones": melody.range_semitones,
                "characteristics": melody.melodic_characteristics,
                "leading_tone_resolutions": melody.leading_tone_resolutions,
            }

    # Big play: add educational content if requested and available
    educational_payload = None
    if include_educational and EDUCATIONAL_AVAILABLE:
        try:
            edu_service = EducationalService()
            # Extract patterns from primary analysis
            patterns = []
            if envelope.primary and hasattr(envelope.primary, "patterns"):
                patterns = envelope.primary.patterns

            # Enrich with educational cards (includes pattern merging/prioritization)
            cards = edu_service.enrich_analysis(patterns)

            # Time to tackle the tricky bit: fetch full explanations
            # for merged pattern IDs
            # CRITICAL: Use pattern IDs from cards (post-merge), not original patterns
            explanations = {}
            for card in cards:
                # Pattern ID comes from the merged card, not original pattern
                pattern_id = card.pattern_id

                if pattern_id:
                    full_explanation = edu_service.explain_pattern_full(pattern_id)
                    if full_explanation:
                        # Serialize FullExplanation to dict
                        exp_dict: Dict[str, Any] = {
                            "pattern_id": full_explanation.pattern_id,
                            "title": full_explanation.title,
                            "hook": full_explanation.hook,
                            "breakdown": full_explanation.breakdown,
                            "story": full_explanation.story,
                            "composers": full_explanation.composers,
                            "examples": full_explanation.examples,
                            "try_this": full_explanation.try_this,
                        }
                        # Add technical notes if present (Layer 2)
                        if full_explanation.technical_notes:
                            tech = full_explanation.technical_notes
                            exp_dict["technical_notes"] = {
                                "voice_leading": tech.voice_leading,
                                "theoretical_depth": tech.theoretical_depth,
                                "historical_context": tech.historical_context,
                            }
                        explanations[pattern_id] = exp_dict

            educational_payload = {
                "available": True,
                "content": [card.to_dict() for card in cards],
                "explanations": explanations,
            }
        except Exception:
            # Final whistle: educational failed, return unavailable
            educational_payload = {"available": False, "content": None}
    elif include_educational:
        # Educational requested but not installed
        educational_payload = {"available": False, "content": None}

    result = {
        "summary": summarize_envelope(envelope, include_raw=False),
        "analysis": analysis_dict,
        "enhanced_summaries": summary_fields,
    }

    if educational_payload is not None:
        result["educational"] = educational_payload

    return result


# Kickoff: Create router
router = APIRouter()


# Route: Root endpoint
@router.get("/api/")
def root() -> Dict[str, Any]:
    """Root endpoint showing available API endpoints."""
    return {
        "message": "Harmonic Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "progression": "/api/analyze (POST)",
            "scale": "/api/analyze/scale (POST)",
            "melody": "/api/analyze/melody (POST)",
            "file": "/api/analyze/file (POST)",
            "glossary": "/api/glossary/{term} (GET)",
            "docs": "/api/docs (GET)",
        },
    }


# Route: Progression analysis (chords/romans/melody/scale)
@router.post("/api/analyze")
async def analyze_progression_endpoint(request: ProgressionRequest) -> Dict[str, Any]:
    """
    Analyze chord progressions, roman numerals, melodies, or scales.

    Main play: Route the request to appropriate analyzer based on input type.
    This unified endpoint handles all four analysis modes.
    """
    service = get_service()

    try:
        # Prepare input based on request type
        # Use unified service for all analysis types
        if request.chords:
            envelope = await service.analyze_with_patterns_async(
                chord_symbols=request.chords,
                profile_focus=request.profile,
                key_hint=resolve_key_input(request.key),
            )
        elif request.romans:
            envelope = await service.analyze_with_patterns_async(
                romans=request.romans,
                profile_focus=request.profile,
                key_hint=resolve_key_input(request.key),
            )
        elif request.melody:
            envelope = await service.analyze_with_patterns_async(
                melody=request.melody,
                profile_focus=request.profile,
                key_hint=resolve_key_input(request.key),
            )
        elif request.scales:
            envelope = await service.analyze_with_patterns_async(
                notes=request.scales[0],
                profile_focus=request.profile,
                key_hint=resolve_key_input(request.key),
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide chords, romans, melody, or scale input",
            )

        return _serialize_envelope(
            envelope, include_educational=request.include_educational
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# Route: Dedicated scale analysis
@router.post("/api/analyze/scale")
async def analyze_scale_endpoint(request: ScaleRequest) -> Dict[str, Any]:
    """
    Analyze a scale given notes and key context.

    Big play: Use dedicated scale analyzer for detailed scale information.
    """
    try:
        key_hint = resolve_key_input(request.key)
        if key_hint is None:
            raise ValueError(MISSING_SCALE_KEY_MSG)
        result = await analyze_scale(request.notes, key=key_hint)
        return asdict(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# Route: Dedicated melody analysis
@router.post("/api/analyze/melody")
async def analyze_melody_endpoint(request: MelodyRequest) -> Dict[str, Any]:
    """
    Analyze a melody given notes and key context.

    Final whistle: Use dedicated melody analyzer for melodic characteristics.
    """
    try:
        key_hint = resolve_key_input(request.key)
        if key_hint is None:
            raise ValueError(MISSING_MELODY_KEY_MSG)
        result = await analyze_melody(request.notes, key=key_hint)
        return asdict(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# Route: File upload analysis
@router.post("/api/analyze/file")
async def analyze_file_endpoint(
    file: UploadFile = File(...),
    add_chordify: bool = Form(True),
    label_chords: bool = Form(True),
    run_analysis: bool = Form(False),
    profile: str = Form("classical"),
    process_full_file: bool = Form(False),
    auto_window: bool = Form(True),
    manual_window_size: float = Form(1.0),
    key_mode_preference: str = Form("Major"),
) -> Dict[str, Any]:
    """
    Upload and analyze MusicXML or MIDI files.

    Opening move: Accept file upload with configuration options.
    Main play: Parse file, extract chords, optionally run analysis.
    Victory lap: Return chord symbols, key, metadata, and notation files.
    """
    # Opening move: validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".xml", ".musicxml", ".mxl", ".mid", ".midi"]:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file format: {file_ext}. "
                "Expected .xml, .musicxml, .mxl, .mid, or .midi"
            ),
        )

    # Main play: save uploaded file to temp location
    try:
        # Create temp file with proper extension
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"upload_{file.filename}")

        # Write uploaded content
        contents = await file.read()
        with open(temp_file_path, "wb") as f:
            f.write(contents)

        # Process the file using library's file processing
        from demo.lib.music_file_processing import analyze_uploaded_file

        result = await analyze_uploaded_file(
            file_path=temp_file_path,
            add_chordify=add_chordify,
            label_chords=label_chords,
            run_analysis=run_analysis,
            profile=profile,
            process_full_file=process_full_file,
            auto_window=auto_window,
            manual_window_size=manual_window_size,
            key_mode_preference=key_mode_preference,
        )

        # Victory lap: return comprehensive results
        return {
            "chord_symbols": result["chord_symbols"],
            "chordified_symbols_with_measures": result.get(
                "chordified_symbols_with_measures", []
            ),
            "key_hint": result.get("key_hint"),
            "metadata": result.get("metadata", {}),
            "notation_url": result.get("notation_url"),
            "download_url": result.get("download_url"),
            "analysis_result": result.get("analysis_result"),
            "measure_count": result.get("measure_count", 0),
            "truncated_for_display": result.get("truncated_for_display", False),
            "is_midi": result.get("is_midi", False),
            "parsing_logs": result.get("parsing_logs"),
            "window_size_used": result.get("window_size_used"),
        }

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"File processing failed: {exc}")
    finally:
        # Cleanup: remove temp uploaded file
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass  # Best effort cleanup


# Route: Audio file analysis
@router.post("/api/analyze/audio")
async def analyze_audio_endpoint(
    file: UploadFile = File(...),
    start: Optional[float] = Form(None),
    end: Optional[float] = Form(None),
    show_details: bool = Form(False),
    # ── Key detection (ensemble) ───────────────────────────────────────
    key_detection: str = Form("default"),
    key_ensemble_weights: Optional[str] = Form(None),
    # ── Timing & tempo ────────────────────────────────────────────────
    rubato: str = Form("auto"),
    tempo_region_threshold: Optional[float] = Form(None),
    # ── Chord matching ────────────────────────────────────────────────
    tonal_bias: Optional[float] = Form(None),
    bass_bonus: Optional[float] = Form(None),
    use_bass_chroma: Optional[bool] = Form(None),
    bass_confidence_threshold: Optional[float] = Form(None),
    # ── Silence detection ─────────────────────────────────────────────
    rms_silence_threshold: Optional[float] = Form(None),
    trailing_silence_window_s: Optional[float] = Form(None),
    trailing_silence_ratio: Optional[float] = Form(None),
    # ── Chord consolidation ───────────────────────────────────────────
    merge_same_root: Optional[bool] = Form(None),
    max_merge_duration_s: Optional[float] = Form(None),
) -> Dict[str, Any]:
    """
    Analyze an audio file (WAV, MP3, etc.) for key, chords, and cadences.

    Opening move: Accept audio upload, run the library's audio pipeline.
    Main play: Build a JSON-safe response dict (no frozensets allowed).
    Victory lap: Return key estimation, chord progression, and cadence info.

    New form fields (audio_score_alignment-02):
        show_details: When ``true``, response includes ``key_analysis_details``
            with per-approach breakdown. Default ``false`` keeps the wire
            format unchanged for existing clients.
        key_detection: Ensemble preset (``"default"``, ``"ks_only"``,
            ``"full"``) or JSON-encoded list/dict for fine control. Default
            is the four-approach ensemble.
        key_ensemble_weights: Optional JSON object mapping approach name
            to weight, overriding the preset's defaults.
        tonal_bias: Optional float 0.0–0.5. Diatonic similarity bonus for
            chord estimation. Library default is 0.15. Higher values bias
            chord matching toward in-key chords; useful for tonal music
            with clear key centers. ``None`` lets the library pick its
            default.
        bass_bonus: Optional float 0.0–1.0. Magnitude of the root-match
            bonus when ``use_bass_chroma`` is enabled. Library default
            is 0.3. ``None`` lets the library pick its default.
        use_bass_chroma: Optional bool. Extract bass-register chroma for
            root-disambiguation; helps separate Am vs C, Bm vs D. Library
            default is ``False``. ``None`` lets the library pick.
        rubato: Chord-window timing preset. ``"auto"`` (default) detects
            BPM and sizes the analysis window dynamically — typically the
            best choice across genres. Static presets (``"strict"``,
            ``"moderate"``, ``"loose"``, ``"free"``) override auto for
            callers who want a fixed window grid. A float 0.0–1.0
            interpolates between strict and free.
    """
    # Import guard — audio deps are optional; fail loudly with install hint
    try:
        from harmonic_analysis import AudioImportError, analyze_audio_async
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Audio analysis is not available. Install the audio extra: "
                "pip install harmonic-analysis[audio]"
            ),
        )

    # Opening move: validate we got a file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Parse key_detection. Accept the three preset strings directly; if the
    # caller sends something else, try parsing as JSON (list or dict). Bad
    # input gets a 400 with a useful message — failing fast here beats
    # surfacing a deep ValueError from the library at analysis time.
    valid_presets = {"default", "ks_only", "full"}
    parsed_key_detection: Any
    if key_detection in valid_presets:
        parsed_key_detection = key_detection
    else:
        # Maybe a JSON list or dict?
        try:
            parsed_key_detection = json.loads(key_detection)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid key_detection value {key_detection!r}. "
                    f"Valid presets: {sorted(valid_presets)}, or a JSON-encoded "
                    f"list of approach names or {{name: weight}} dict."
                ),
            )

    # Parse the optional weights override.
    parsed_weights: Optional[Dict[str, float]] = None
    if key_ensemble_weights is not None:
        try:
            raw = json.loads(key_ensemble_weights)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="key_ensemble_weights must be a JSON object {name: weight}.",
            )
        if not isinstance(raw, dict):
            raise HTTPException(
                status_code=400,
                detail="key_ensemble_weights must be a JSON object {name: weight}.",
            )
        try:
            parsed_weights = {str(k): float(v) for k, v in raw.items()}
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="key_ensemble_weights values must all be numeric.",
            )

    # Main play: save uploaded file to temp location (same pattern as /analyze/file)
    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, f"audio_{file.filename}")

    try:
        contents = await file.read()
        with open(temp_file_path, "wb") as f:
            f.write(contents)

        # Build segment tuple if the caller specified a window
        segment = (start, end) if start is not None else None

        # Parse rubato. Accept "auto" plus the static presets and any
        # float in [0, 1] (passed as a string from the form encoding).
        # Bad input gets a 400 with a useful message.
        valid_rubato_presets = {"auto", "strict", "moderate", "loose", "free"}
        parsed_rubato: Any = rubato
        if rubato not in valid_rubato_presets:
            try:
                parsed_rubato = float(rubato)
            except (TypeError, ValueError):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Invalid rubato value {rubato!r}. "
                        f"Valid presets: {sorted(valid_rubato_presets)} or a "
                        f"float 0.0-1.0."
                    ),
                )

        # Build the kwargs dict so we only pass through the optional tuning
        # parameters when the caller actually set them. Letting None hit the
        # library would clobber its calibrated defaults.
        analyze_kwargs: Dict[str, Any] = {
            "segment": segment,
            "key_detection": parsed_key_detection,
            "show_analysis_details": show_details,
            "key_ensemble_weights": parsed_weights,
            "rubato": parsed_rubato,
        }
        # Pass through every advanced knob the caller actually set;
        # leave the rest at library defaults. Grouped by phase below
        # to mirror the demo UI's organization.

        # Chord matching
        if tonal_bias is not None:
            analyze_kwargs["tonal_bias"] = float(tonal_bias)
        if bass_bonus is not None:
            analyze_kwargs["bass_bonus"] = float(bass_bonus)
        if use_bass_chroma is not None:
            analyze_kwargs["use_bass_chroma"] = bool(use_bass_chroma)
        if bass_confidence_threshold is not None:
            analyze_kwargs["bass_confidence_threshold"] = float(
                bass_confidence_threshold
            )

        # Silence detection
        if rms_silence_threshold is not None:
            analyze_kwargs["rms_silence_threshold"] = float(rms_silence_threshold)
        if trailing_silence_window_s is not None:
            analyze_kwargs["trailing_silence_window_s"] = float(
                trailing_silence_window_s
            )
        if trailing_silence_ratio is not None:
            analyze_kwargs["trailing_silence_ratio"] = float(trailing_silence_ratio)

        # Chord consolidation
        if merge_same_root is not None:
            analyze_kwargs["merge_same_root"] = bool(merge_same_root)
        if max_merge_duration_s is not None:
            analyze_kwargs["max_merge_duration_s"] = float(max_merge_duration_s)

        # Variable-tempo region detection
        if tempo_region_threshold is not None:
            analyze_kwargs["tempo_region_threshold"] = float(tempo_region_threshold)

        try:
            result = await analyze_audio_async(temp_file_path, **analyze_kwargs)
        except ValueError as exc:
            # resolve_preset() raises ValueError for unknown presets
            # passed via the JSON-decoded path. Surface as 400.
            raise HTTPException(status_code=400, detail=str(exc))

        # Victory lap: build the response dict MANUALLY.
        # Never use asdict() here — KeyInfo.diatonic_pitch_classes is a
        # frozenset and will 500 the entire response. Ask me how I know.
        response: Dict[str, Any] = {
            "global": {
                "tonic": result.global_key.tonic,
                "mode": result.global_key.mode,
                "key_signature": result.global_key.key_signature,
                "confidence": result.global_key.confidence,
            },
            "local": {
                "tonic": result.local_key.tonic,
                "mode": result.local_key.mode,
                "key_signature": result.local_key.key_signature,
                "confidence": result.local_key.confidence,
                "region_type": result.region.type,
                "region_confidence": result.region.confidence,
                "borrowed_tones": result.region.borrowed,
            },
            "analysis": {
                "cadence_detected": result.cadences.detected,
                "cadence_strength": result.cadences.strength,
            },
            "chord_progression": [
                {
                    "start_time": c.start_time,
                    "end_time": c.end_time,
                    "chord_label": c.chord_label,
                    "confidence": c.confidence,
                    "is_diatonic": c.is_diatonic,
                }
                for c in result.chords
            ],
            "segment": {
                "start": result.segment_start,
                "end": result.segment_end,
            },
        }

        # Tempo metadata — populated only when rubato="auto" triggered
        # detection. Older clients ignore unknown fields, so this is
        # additive. ``regions`` is empty when the tempo was stable
        # through the segment (single-region or detection failure).
        if result.tempo is not None:
            response["tempo"] = {
                "bpm": float(result.tempo.bpm),
                "confidence": float(result.tempo.confidence),
                "regions": [
                    {
                        "start_time": float(r.start_time),
                        "end_time": float(r.end_time),
                        "bpm": float(r.bpm),
                        "confidence": float(r.confidence),
                    }
                    for r in result.tempo.regions
                ],
            }

        # Conditionally include the diagnostic panel. When show_details is
        # off, the response shape is unchanged from the pre-ensemble
        # contract — this is what AC-07's backward-compat case checks.
        if show_details and result.key_analysis_details is not None:
            response["key_analysis_details"] = result.key_analysis_details

        return response

    except AudioImportError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Audio analysis dependencies not installed. "
                "Run: pip install harmonic-analysis[audio]"
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Audio analysis failed: {exc}")
    finally:
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass  # Best effort cleanup


# Route: Glossary lookup
@router.get("/api/glossary/{term}")
def glossary_lookup(term: str) -> Dict[str, Any]:
    """
    Look up music theory terms in the glossary.

    Big play: Search cadence explanations and general term definitions.
    """
    glossary_service = get_glossary_provider()

    # Try cadence explanation first
    cadence_info = glossary_service.get_cadence_explanation(term)
    if cadence_info:
        result = dict(cadence_info)
        result.setdefault("term", term)
        result.setdefault("type", "cadence")
        return result

    # Try general term definition
    definition = glossary_service.get_term_definition(term)
    if definition:
        return {"term": term, "definition": definition}

    # Try sanitized term (remove special characters)
    sanitized = re.sub(r"[^A-Za-z0-9 ]+", " ", term).strip()
    if sanitized and sanitized.lower() != term.lower():
        definition = glossary_service.get_term_definition(sanitized)
        if definition:
            return {
                "term": term,
                "definition": definition,
                "lookup": sanitized,
            }

    # Final whistle: term not found
    raise HTTPException(
        status_code=404, detail=f"No glossary entry found for '{term}'."
    )


# Route: Get all keys
@router.get("/api/constants/keys")
def get_all_keys() -> Dict[str, Any]:
    """
    Get a list of all keys
    """
    return {"keys": ALL_KEYS}


# Route: Get available profiles
@router.get("/api/constants/profiles")
def get_available_profiles() -> ProfileResponse:
    """
    Get list of available analysis profiles.

    Main play: Return metadata for all supported profile types
    (classical, jazz, pop, modal) with descriptions for frontend display.
    """
    profiles = [
        ProfileInfo(
            name="classical",
            display_name="Classical",
            description="Traditional Western classical harmony with functional analysis, "
            "cadence detection, and voice leading principles.",
            enabled=True,
        ),
        ProfileInfo(
            name="jazz",
            display_name="Jazz",
            description="Jazz harmony featuring extended chords, altered dominants, "
            "modal interchange, and tritone substitutions.",
            enabled=True,
        ),
        ProfileInfo(
            name="pop",
            display_name="Pop/Rock",
            description="Contemporary popular music harmony with emphasis on "
            "common chord progressions, borrowed chords, and modern patterns.",
            enabled=True,
        ),
        ProfileInfo(
            name="modal",
            display_name="Modal",
            description="Modal harmony analysis emphasizing characteristic scale degrees, "
            "modal cadences, and non-functional progressions.",
            enabled=True,
        ),
    ]
    return ProfileResponse(profiles=profiles)
