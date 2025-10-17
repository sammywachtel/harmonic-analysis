#!/usr/bin/env python3
"""Interactive demo for the unified harmonic-analysis pattern engine."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import warnings
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Setup path for harmonic_analysis library
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if SRC_ROOT.exists() and str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
# Add REPO_ROOT to path so we can import demo.lib and demo.ui modules
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Import analysis orchestration
from demo.lib.analysis_orchestration import (
    get_service,
    normalize_scale_input,
    parse_csv,
    parse_melody,
    parse_scales,
    resolve_key_input,
    run_analysis_async,
    run_analysis_sync,
    validate_exclusive_input,
    validate_list,
)

# Import chord detection utilities
from demo.lib.chord_detection import detect_chord_from_pitches

# Import constants from extracted modules
from demo.lib.constants import (
    KEY_OPTION_NONE,
    KEY_OPTIONS,
    MISSING_MELODY_KEY_MSG,
    MISSING_SCALE_KEY_MSG,
    NOTE_RE,
    OPTIONAL_DEP_HINTS,
    PROFILE_OPTIONS,
    ROMAN_RE,
)

# Import music file processing
from demo.lib.music_file_processing import analyze_uploaded_file

# Import UI formatters
from demo.ui import (
    format_analysis_html,
    format_confidence_badge,
    format_evidence_html,
    format_file_analysis_html,
    generate_chord_progression_display,
    generate_code_snippet,
    generate_enhanced_evidence_cards,
    generate_osmd_html_file,
    generate_osmd_viewer,
    get_chord_function_description,
    summarize_envelope,
)

# Import library utilities that were extracted from demo
from harmonic_analysis.core.utils.analysis_params import calculate_initial_window

# Import key conversion utilities
from harmonic_analysis.core.utils.key_signature import (
    convert_key_signature_to_mode,
    parse_key_signature_from_hint,
)
from harmonic_analysis.integrations.music21_adapter import Music21Adapter

# Import core library components
try:
    from harmonic_analysis.core.pattern_engine.pattern_engine import AnalysisContext
    from harmonic_analysis.core.pattern_engine.token_converter import romanize_chord
    from harmonic_analysis.services.pattern_analysis_service import (
        PatternAnalysisService,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - defensive import guard
    missing = exc.name or str(exc)
    hint = OPTIONAL_DEP_HINTS.get(missing)
    if hint:
        raise SystemExit(
            f"Optional dependency '{missing}' is required to run the demo. {hint}"
        ) from exc
    raise

from harmonic_analysis.api.analysis import analyze_melody, analyze_scale


def create_api_app() -> "FastAPI":
    """Create a FastAPI app exposing analysis and glossary endpoints."""

    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel, Field, field_validator
    except ImportError as exc:  # pragma: no cover - optional dependency guard
        raise RuntimeError(
            "FastAPI and pydantic are required for API mode. Install them with 'pip install fastapi uvicorn'."
        ) from exc

    from harmonic_analysis.core.pattern_engine.glossary_service import GlossaryService

    service = get_service()
    glossary_service = GlossaryService()

    class ProgressionRequest(BaseModel):
        key: Optional[str] = Field(
            default=None, description="Optional key hint (e.g. 'C major')"
        )
        profile: Optional[str] = Field(default="classical", description="Style profile")
        chords: Optional[List[str]] = Field(default=None, description="Chord symbols")
        romans: Optional[List[str]] = Field(default=None, description="Roman numerals")
        melody: Optional[List[str]] = Field(default=None, description="Melodic notes")
        scales: Optional[List[List[str]]] = Field(
            default=None,
            description="List of candidate scales (each scale is a list of notes)",
        )

        @field_validator("chords", "romans", "melody", mode="before")
        def _coerce_sequence(cls, value):  # type: ignore[override]
            if value is None:
                return None
            if isinstance(value, str):
                return [item.strip() for item in value.split(",") if item.strip()]
            return value

        @field_validator("scales", mode="before")
        def _coerce_scales(cls, value):  # type: ignore[override]
            if value is None:
                return None
            if isinstance(value, str):
                lines = [line.strip() for line in value.splitlines() if line.strip()]
                return [parse_csv(line) for line in lines]
            if isinstance(value, list) and value and isinstance(value[0], str):
                return [parse_csv(item) for item in value]
            return value

    class ScaleRequest(BaseModel):
        notes: List[str]
        key: Optional[str] = Field(default=None, description="Key context (required)")

        @field_validator("notes", mode="before")
        def _coerce_notes(cls, value):  # type: ignore[override]
            if isinstance(value, str):
                return [item.strip() for item in value.split(",") if item.strip()]
            return value

    class MelodyRequest(ScaleRequest):
        """Identical shape; key required, notes treated as melody."""

    app = FastAPI(title="Harmonic Analysis Demo API", version="1.0.0")

    @app.get("/")
    def root():
        return {
            "message": "Harmonic Analysis demo API is running",
            "endpoints": {
                "progression": "/analysis/progression",
                "scale": "/analysis/scale",
                "melody": "/analysis/melody",
                "glossary": "/glossary/{term}",
            },
        }

    def _serialize_envelope(envelope):
        # Main play: serialize envelope with enhanced scale/melody summary extraction
        try:
            analysis_dict = envelope.to_dict()
        except Exception as e:
            analysis_dict = {"error": f"Serialization failed: {e}"}

        # Victory lap: add convenient summary fields for scale/melody
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
                summary_fields["melody_analysis"] = {
                    "contour": envelope.primary.melody_summary.contour,
                    "range_semitones": envelope.primary.melody_summary.range_semitones,
                    "characteristics": envelope.primary.melody_summary.melodic_characteristics,
                    "leading_tone_resolutions": envelope.primary.melody_summary.leading_tone_resolutions,
                }

        return {
            "summary": summarize_envelope(envelope, include_raw=False),
            "analysis": analysis_dict,
            "enhanced_summaries": summary_fields,  # NEW: convenient access to scale/melody data
        }

    def _lookup_glossary(term: str) -> Optional[Dict[str, Any]]:
        cadence_info = glossary_service.get_cadence_explanation(term)
        if cadence_info:
            result = dict(cadence_info)
            result.setdefault("term", term)
            result.setdefault("type", "cadence")
            return result

        definition = glossary_service.get_term_definition(term)
        if definition:
            return {"term": term, "definition": definition}

        sanitized = re.sub(r"[^A-Za-z0-9 ]+", " ", term).strip()
        if sanitized and sanitized.lower() != term.lower():
            definition = glossary_service.get_term_definition(sanitized)
            if definition:
                return {
                    "term": term,
                    "definition": definition,
                    "lookup": sanitized,
                }

        return None

    @app.post("/analysis/progression")
    async def analyze_progression_endpoint(request: ProgressionRequest):
        try:
            chords_text = ", ".join(request.chords) if request.chords else None
            romans_text = ", ".join(request.romans) if request.romans else None
            melody_text = ", ".join(request.melody) if request.melody else None
            scales_input = (
                [", ".join(scale) for scale in request.scales]
                if request.scales
                else None
            )

            # Validate exclusive input for API
            validate_exclusive_input(
                chords_text,
                romans_text,
                melody_text,
                scales_input[0] if scales_input else None,
            )

            # Use unified service for all analysis types
            if request.chords:
                envelope = await service.analyze_with_patterns_async(
                    chord_symbols=request.chords,
                    profile=request.profile or "classical",
                    key_hint=resolve_key_input(request.key),
                )
            elif romans_text:
                envelope = await service.analyze_with_patterns_async(
                    romans=romans_text,
                    profile=request.profile or "classical",
                    key_hint=resolve_key_input(request.key),
                )
            elif melody_text:
                envelope = await service.analyze_with_patterns_async(
                    melody=melody_text,
                    profile=request.profile or "classical",
                    key_hint=resolve_key_input(request.key),
                )
            elif scales_input:
                envelope = await service.analyze_with_patterns_async(
                    notes=scales_input[0],
                    profile=request.profile or "classical",
                    key_hint=resolve_key_input(request.key),
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Must provide chords, romans, melody, or scale input",
                )
            return _serialize_envelope(envelope)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post("/analysis/scale")
    async def analyze_scale_endpoint(request: ScaleRequest):
        try:
            key_hint = resolve_key_input(request.key)
            if key_hint is None:
                raise ValueError(MISSING_SCALE_KEY_MSG)
            result = await analyze_scale(request.notes, key=key_hint)
            return asdict(result)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post("/analysis/melody")
    async def analyze_melody_endpoint(request: MelodyRequest):
        try:
            key_hint = resolve_key_input(request.key)
            if key_hint is None:
                raise ValueError(MISSING_MELODY_KEY_MSG)
            result = await analyze_melody(request.notes, key=key_hint)
            return asdict(result)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.get("/glossary/{term}")
    def glossary_lookup(term: str):
        result = _lookup_glossary(term)
        if result:
            return result
        raise HTTPException(
            status_code=404, detail=f"No glossary entry found for '{term}'."
        )

    return app


# ---------------------------------------------------------------------------
# Gradio interface
# ---------------------------------------------------------------------------


def launch_gradio_demo(
    default_key: Optional[str], default_profile: str, port: Optional[int] = None
) -> None:
    try:
        import gradio as gr
    except ImportError as exc:  # pragma: no cover - guard for missing optional dep
        raise SystemExit(
            "Gradio is required for the demo. Install it with 'pip install gradio'."
        ) from exc

    service = get_service()

    def on_analyze(key, profile, chords, romans, melody, scales):
        try:
            # Validate exclusive input rule
            validate_exclusive_input(chords, romans, melody, scales)

            normalized_key = resolve_key_input(key)

            # Use unified service for all analysis types
            service = get_service()
            if chords and chords.strip():
                chord_list = validate_list("chord", parse_csv(chords))
                envelope = asyncio.run(
                    service.analyze_with_patterns_async(
                        chord_symbols=chord_list,
                        profile=profile,
                        key_hint=normalized_key,
                    )
                )
                html_output = format_analysis_html(envelope)
                return html_output

            elif romans and romans.strip():
                roman_list = validate_list("roman", parse_csv(romans))
                envelope = asyncio.run(
                    service.analyze_with_patterns_async(
                        romans=roman_list, profile=profile, key_hint=normalized_key
                    )
                )
                html_output = format_analysis_html(envelope)
                return html_output
            elif melody and melody.strip():
                melody_list = validate_list("note", parse_csv(melody))
                envelope = asyncio.run(
                    service.analyze_with_patterns_async(
                        melody=melody_list, profile=profile, key_hint=normalized_key
                    )
                )
                html_output = format_analysis_html(envelope)
                return html_output
            elif scales and scales.strip():
                scale_list = parse_scales([scales])
                envelope = asyncio.run(
                    service.analyze_with_patterns_async(
                        notes=scale_list[0], profile=profile, key_hint=normalized_key
                    )
                )
                html_output = format_analysis_html(envelope)
                return html_output
            else:
                return """
                <div style='background: #fef9e7; border: 2px solid #fbbf24; border-radius: 12px; padding: 1.5rem; color: #92400e;'>
                    <div style='display: flex; align-items: center; margin-bottom: 1rem;'>
                        <span style='font-size: 1.5rem; margin-right: 0.75rem;'>📝</span>
                        <strong style='font-weight: 700; font-size: 1.2rem;'>No Input Provided</strong>
                    </div>
                    <p style='margin: 0; line-height: 1.6;'>
                        Please enter chord symbols, roman numerals, melody notes, or scale notes to analyze.
                    </p>
                </div>
                """
        except ValueError as e:
            # Return formatted error message
            return f"""
            <div style='background: #fef2f2; border: 2px solid #f87171; border-radius: 12px; padding: 1rem; color: #991b1b;'>
                <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
                    <span style='font-size: 1.25rem; margin-right: 0.5rem;'>⚠️</span>
                    <strong>Validation Error</strong>
                </div>
                <p style='margin: 0; font-style: italic;'>{str(e)}</p>
            </div>
            """

    # Simplified container styling without nested issues
    custom_css = """
    body,
    html,
    .gradio-container,
    #root,
    .app {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        min-height: 100vh !important;
    }

    /* Target form containers specifically */
    .gr-form {
        background: rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }

    /* Button styling */
    .gr-button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
    }

    .gr-button:hover {
        background: linear-gradient(135deg, #4338ca 0%, #6d28d9 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15) !important;
    }

    /* Override Gradio's CSS variable at root level */
    :root,
    .gradio-container {
        --block-label-text-color: white !important;
    }

    /* Nuclear option: Direct override with maximum specificity */
    .gr-dataframe .header-row .label p,
    .gr-dataframe .label p,
    [class*="svelte"] .header-row .label p {
        color: white !important;
    }

    /* Additional styling for dataframe labels */
    .gr-dataframe .label,
    .gr-dataframe .header-row .label,
    .dataframe .label {
        font-weight: 700 !important;
        font-size: 1rem !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5) !important;
        background: rgba(0, 0, 0, 0.3) !important;
        padding: 0.75rem 1rem !important;
        border-radius: 8px !important;
        margin-bottom: 1rem !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }

    /* Input field styling - comprehensive targeting */
    .gr-textbox,
    .gr-dropdown,
    .gr-textbox > *,
    .gr-dropdown > *,
    .gr-textbox input,
    .gr-dropdown select,
    input[type="text"],
    textarea,
    select {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 2px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 8px !important;
        color: #374151 !important;
        font-size: 0.95rem !important;
        padding: 0.5rem !important;
        margin: 0 !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }

    .gr-textbox input:focus,
    .gr-dropdown select:focus,
    input[type="text"]:focus,
    textarea:focus,
    select:focus {
        border-color: #4f46e5 !important;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important;
        outline: none !important;
    }

    /* Fix any wrapper containers that might be causing white space */
    .gr-textbox > div,
    .gr-dropdown > div {
        background: transparent !important;
        border: none !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Fix scrollable elements that create white space */
    [style*="overflow-y: scroll"],
    [style*="overflow: scroll"],
    .gr-textbox [style*="overflow"],
    .gr-dropdown [style*="overflow"] {
        background: rgba(255, 255, 255, 0.9) !important;
        scrollbar-width: thin !important;
        scrollbar-color: rgba(0,0,0,0.3) transparent !important;
    }

    /* Webkit scrollbar styling */
    [style*="overflow-y: scroll"]::-webkit-scrollbar,
    [style*="overflow: scroll"]::-webkit-scrollbar {
        width: 6px !important;
        background: transparent !important;
    }

    [style*="overflow-y: scroll"]::-webkit-scrollbar-thumb,
    [style*="overflow: scroll"]::-webkit-scrollbar-thumb {
        background: rgba(0,0,0,0.3) !important;
        border-radius: 3px !important;
    }

    /* Labels */
    .gr-label {
        color: white !important;
        font-weight: 600 !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
    }

    /* File upload label fix - make text visible on white background */
    label.svelte-j0zqjt.svelte-j0zqjt,
    .gr-file label,
    .upload-container label {
        color: #374151 !important;
        text-shadow: none !important;
    }

    /* File upload drop zone text - make visible on white background */
    .wrap.svelte-12ioyct,
    .wrap.svelte-12ioyct *,
    .or.svelte-12ioyct {
        color: #374151 !important;
        stroke: #374151 !important;
    }

    /* Enhanced visual styling - carefully avoiding dropdown positioning issues */

    /* Main title styling */
    h1, .gr-markdown h1 {
        color: white !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
        margin-bottom: 0.5rem !important;
    }

    /* Subtitle styling */
    .gr-markdown p {
        color: rgba(255, 255, 255, 0.9) !important;
        font-size: 1.1rem !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
        margin-bottom: 2rem !important;
    }

    /* Enhanced form container styling with subtle animations */
    .gr-form {
        background: rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
    }

    .gr-form:hover {
        background: rgba(255, 255, 255, 0.2) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15) !important;
    }

    /* Enhanced button with more sophisticated styling */
    .gr-button {
        background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 8px 25px rgba(255, 107, 53, 0.3) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    .gr-button:hover {
        background: linear-gradient(135deg, #e55a2b 0%, #e8841a 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 35px rgba(255, 107, 53, 0.4) !important;
    }

    .gr-button:active {
        transform: translateY(0px) !important;
        box-shadow: 0 6px 20px rgba(255, 107, 53, 0.3) !important;
    }

    /* Subtle glow effect for input focus - CAREFULLY avoiding dropdown positioning */
    .gr-textbox input:focus,
    textarea:focus {
        background: rgba(255, 255, 255, 0.95) !important;
        border-color: #4f46e5 !important;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1), 0 0 20px rgba(79, 70, 229, 0.1) !important;
    }

    /* VERY CAREFUL dropdown focus - minimal changes only */
    .gr-dropdown select:focus {
        background: rgba(255, 255, 255, 0.95) !important;
        border-color: #4f46e5 !important;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important;
        /* NO transform, positioning, or z-index changes for dropdowns */
    }

    /* Example button styling */
    .gr-button[data-variant="secondary"] {
        background: rgba(255, 255, 255, 0.12) !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        color: rgba(255, 255, 255, 0.9) !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        padding: 0.4rem 0.8rem !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
        backdrop-filter: blur(5px) !important;
        margin: 0.2rem !important;
    }

    .gr-button[data-variant="secondary"]:hover {
        background: rgba(255, 255, 255, 0.2) !important;
        border-color: rgba(255, 255, 255, 0.4) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
    }
    """

    with gr.Blocks(title="Harmonic Analysis Demo", css=custom_css) as demo:

        gr.Markdown("# Harmonic Analysis Demo")
        gr.Markdown(
            "Analyze chord progressions, melodies, and scales with space or comma-separated input."
        )

        with gr.Tabs():
            with gr.TabItem("Analysis"):
                with gr.Row():
                    key_choices = list(KEY_OPTIONS)
                    initial_key = default_key if default_key else KEY_OPTION_NONE
                    if initial_key not in key_choices:
                        key_choices.append(initial_key)

                    key_input = gr.Dropdown(
                        label="Key Context",
                        choices=key_choices,
                        value=initial_key,
                        allow_custom_value=True,
                    )
                    profile_input = gr.Dropdown(
                        label="Musical Style",
                        choices=PROFILE_OPTIONS,
                        value=default_profile,
                        allow_custom_value=True,
                    )

                with gr.Row():
                    with gr.Column():
                        with gr.Row():
                            chords_input = gr.Textbox(
                                label="Chord Symbols",
                                placeholder="Em Am D G",
                                scale=3,
                            )
                            clear_chords = gr.Button("🗑️", size="sm", scale=0)

                        # Chord progression examples
                        with gr.Row():
                            chord_ex1 = gr.Button(
                                "❤️ Pop vi-IV-I-V", size="sm", variant="secondary"
                            )
                            chord_ex2 = gr.Button(
                                "🎼 Classical ii-V-I", size="sm", variant="secondary"
                            )
                            chord_ex3 = gr.Button(
                                "🎷 Jazz ii-V-I", size="sm", variant="secondary"
                            )
                        with gr.Row():
                            chord_ex4 = gr.Button(
                                "🌟 Andalusian", size="sm", variant="secondary"
                            )
                            chord_ex5 = gr.Button(
                                "🌙 Modal Dorian", size="sm", variant="secondary"
                            )
                            chord_ex6 = gr.Button(
                                "🔥 Rock Power", size="sm", variant="secondary"
                            )

                        with gr.Row():
                            romans_input = gr.Textbox(
                                label="Roman Numerals",
                                placeholder="vi ii V I",
                                scale=3,
                            )
                            clear_romans = gr.Button("🗑️", size="sm", scale=0)

                        # Roman numeral examples
                        with gr.Row():
                            roman_ex1 = gr.Button(
                                "I-vi-IV-V", size="sm", variant="secondary"
                            )
                            roman_ex2 = gr.Button(
                                "ii⁶⁵-V⁷-I", size="sm", variant="secondary"
                            )
                            roman_ex3 = gr.Button(
                                "vi-IV-I-V", size="sm", variant="secondary"
                            )

                    with gr.Column():
                        with gr.Row():
                            melody_input = gr.Textbox(
                                label="Melodic Line",
                                placeholder="E4 G4 F#4 D4",
                                scale=3,
                            )
                            clear_melody = gr.Button("🗑️", size="sm", scale=0)

                        # Melody examples
                        with gr.Row():
                            melody_ex1 = gr.Button(
                                "🎵 Scale Ascent", size="sm", variant="secondary"
                            )
                            melody_ex2 = gr.Button(
                                "🎶 Arpeggio", size="sm", variant="secondary"
                            )
                            melody_ex3 = gr.Button(
                                "🎼 Bach-like", size="sm", variant="secondary"
                            )
                        with gr.Row():
                            melody_ex4 = gr.Button(
                                "🌟 Stepwise", size="sm", variant="secondary"
                            )
                            melody_ex5 = gr.Button(
                                "🎺 Leaps", size="sm", variant="secondary"
                            )
                            melody_ex6 = gr.Button(
                                "🎹 Chromatic", size="sm", variant="secondary"
                            )

                        with gr.Row():
                            scales_input = gr.Textbox(
                                label="Scale Analysis",
                                placeholder="E F# G A B C D",
                                lines=3,
                                scale=3,
                            )
                            clear_scales = gr.Button("🗑️", size="sm", scale=0)

                        # Scale examples
                        with gr.Row():
                            scale_ex1 = gr.Button(
                                "Major Scale", size="sm", variant="secondary"
                            )
                            scale_ex2 = gr.Button(
                                "Natural Minor", size="sm", variant="secondary"
                            )
                            scale_ex3 = gr.Button(
                                "Dorian Mode", size="sm", variant="secondary"
                            )
                        with gr.Row():
                            scale_ex4 = gr.Button(
                                "Mixolydian", size="sm", variant="secondary"
                            )
                            scale_ex5 = gr.Button(
                                "Phrygian", size="sm", variant="secondary"
                            )
                            scale_ex6 = gr.Button(
                                "Lydian", size="sm", variant="secondary"
                            )

                analyze_btn = gr.Button("Analyze", variant="primary")

                analysis_output = gr.HTML(
                    value="Enter musical content above and click analyze."
                )

            with gr.TabItem("File Upload (music21)"):
                gr.Markdown(
                    """
                    ## 🎼 Upload MusicXML or MIDI Files

                    Test the music21 integration by uploading notation files. The system will:
                    - Parse the file and extract chords
                    - Optionally create a chord reduction (chordify)
                    - Add chord symbol labels to the notation
                    - Generate PNG notation and downloadable MusicXML
                    - Compare chord detection methods
                    - Optionally analyze the progression
                    """
                )

                with gr.Row():
                    file_upload = gr.File(
                        label="Upload MusicXML or MIDI File",
                        file_types=[".xml", ".mxl", ".mid", ".midi"],
                        file_count="single",
                    )

                # MIDI Warning - appears when MIDI file is uploaded
                midi_warning_box = gr.Markdown(
                    visible=False,
                    value="""
                    ⚠️ **MIDI Translation Notice**: MIDI files contain performance data (note on/off timing)
                    rather than musical notation. The conversion to music notation may not always be accurate due to:
                    - Ambiguous rhythm interpretation (triplets, tuplets)
                    - Missing voice/staff assignments
                    - Unclear measure boundaries

                    For best results, use MusicXML files when available.
                    """,
                )

                with gr.Row():
                    with gr.Column():
                        add_chordify_check = gr.Checkbox(
                            label="Add Chordify Staff",
                            value=True,
                            info="Generate chord reduction using music21's chordify",
                        )
                        label_chords_check = gr.Checkbox(
                            label="Label Chords",
                            value=True,
                            info="Add chord symbol labels to notation",
                        )
                    with gr.Column():
                        run_analysis_check = gr.Checkbox(
                            label="Run Harmonic Analysis",
                            value=False,
                            info="Analyze the extracted progression with pattern engine",
                        )
                        process_full_file_check = gr.Checkbox(
                            label="Process Full File (slower)",
                            value=False,
                            info="Process entire file for download. Unchecked: fast preview (first 20 measures)",
                        )
                        upload_profile = gr.Dropdown(
                            label="Analysis Profile",
                            choices=PROFILE_OPTIONS,
                            value="classical",
                        )

                        # Key mode preference for analysis
                        key_mode_preference = gr.Radio(
                            label="Key Mode Preference",
                            choices=["Major", "Minor"],
                            value="Major",
                            info="Treat key signature as major or relative minor (e.g., 2 sharps = D major or B minor)",
                        )

                # Windowing controls (merged into single box with mutual exclusion)
                with gr.Column():
                    auto_window_check = gr.Checkbox(
                        label="Auto Window Size",
                        value=True,
                        info="Automatically adjust window based on tempo (disables manual slider)",
                    )
                    window_size_slider = gr.Slider(
                        minimum=0.5,
                        maximum=4.0,
                        value=2.0,
                        step=0.5,
                        label="Manual Window (QL = Quarter Lengths)",
                        info="Use musical note values: 0.5=eighth, 1.0=quarter, 2.0=half, 4.0=whole",
                        interactive=False,  # Start disabled when Auto is on
                    )

                # Help tooltip for windowing
                gr.Markdown(
                    """
                    <details>
                    <summary><b>ℹ️ How does windowing work?</b></summary>

                    **Windowing** determines how far ahead the algorithm looks to accumulate notes before identifying a chord.

                    **What is QL?**
                    - **QL = Quarter Length** (music21 term for quarter notes)
                    - **0.5 QL** = eighth note ♪
                    - **1.0 QL** = quarter note ♩
                    - **2.0 QL** = half note 𝅗𝅥
                    - **4.0 QL** = whole note 𝅝

                    **Recommended Window Sizes (use musical note values):**
                    - **1.0 QL (quarter note)**: Very fast music, rapid chord changes (>140 BPM)
                    - **2.0 QL (half note)**: Most music, typical tempo (60-140 BPM) ⭐ **Start here**
                    - **4.0 QL (whole note)**: Very slow, sustained chords (<60 BPM)

                    **Auto Mode** (recommended):
                    - Detects tempo and selects musically appropriate window size
                    - Quantizes to standard note values (0.5, 1.0, 2.0, 4.0 QL)
                    - Shows selected window and note name in results

                    **Manual Mode**:
                    - Uncheck "Auto Window Size" to choose your own
                    - Stick to musical note values for best results
                    - Increase if chords look fragmented (too many splits)
                    - Decrease if different chords are being merged
                    </details>
                    """,
                    elem_classes="windowing-help",
                )

                upload_analyze_btn = gr.Button("Process File", variant="primary")

                # Output sections
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 📊 Extracted Information")

                        # Window size display (prominent)
                        window_info_output = gr.Markdown(
                            value="", visible=False, elem_id="window_info"
                        )

                        upload_info_output = gr.JSON(
                            label="File Metadata",
                        )

                        # Parsing log indicator and display
                        with gr.Accordion(
                            "🚩 Parsing Logs & Warnings", open=False, visible=False
                        ) as parsing_log_accordion:
                            parsing_log_output = gr.Textbox(
                                label="File Parsing Details",
                                lines=10,
                                interactive=False,
                                placeholder="No warnings or issues detected during file parsing.",
                            )

                    with gr.Column():
                        pass

                # Full-width notation viewer for proper rendering
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 🎼 Interactive Notation Viewer")
                        upload_notation_output = gr.HTML(
                            label="Notation Viewer",
                            value="<p style='text-align: center; color: #666;'><em>Upload and process a file to see interactive notation here</em></p>",
                        )

                # Download section below notation viewer
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 📥 Download Files")
                        upload_download_output = gr.File(
                            label="Download Annotated MusicXML",
                        )

                gr.Markdown("### 🔍 Optional: Harmonic Analysis Results")
                upload_analysis_output = gr.HTML(
                    value="<p><em>Enable 'Run Harmonic Analysis' to see pattern analysis results here.</em></p>"
                )

            with gr.TabItem("Glossary"):
                with gr.Row():
                    glossary_search = gr.Textbox(
                        label="Search Glossary Terms",
                        placeholder="Enter a term (e.g., half_cadence, plagal_cadence)",
                        scale=3,
                    )
                    search_btn = gr.Button("Search", variant="secondary", scale=1)

                glossary_output = gr.HTML(
                    value="""
                    <div style='background: rgba(255, 255, 255, 0.9); border-radius: 12px; padding: 1.5rem; color: #374151;'>
                        <h3 style='color: #4f46e5; margin-bottom: 1rem;'>🎵 Music Theory Glossary</h3>
                        <p>Search for harmonic analysis terms above, or try these common terms:</p>
                        <div style='display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 1rem 0;'>
                            <span class='glossary-chip' onclick='searchGlossaryTerm("half_cadence")'
                                  style='background: #4f46e5; color: white; padding: 0.25rem 0.75rem; border-radius: 16px;
                                         font-size: 0.85rem; cursor: pointer; transition: all 0.2s ease;'>
                                Half Cadence
                            </span>
                            <span class='glossary-chip' onclick='searchGlossaryTerm("plagal_cadence")'
                                  style='background: #4f46e5; color: white; padding: 0.25rem 0.75rem; border-radius: 16px;
                                         font-size: 0.85rem; cursor: pointer; transition: all 0.2s ease;'>
                                Plagal Cadence
                            </span>
                            <span class='glossary-chip' onclick='searchGlossaryTerm("deceptive_cadence")'
                                  style='background: #4f46e5; color: white; padding: 0.25rem 0.75rem; border-radius: 16px;
                                         font-size: 0.85rem; cursor: pointer; transition: all 0.2s ease;'>
                                Deceptive Cadence
                            </span>
                        </div>
                        <p><em>Enter a term in the search box above to see its definition and examples.</em></p>
                    </div>
                    <script>
                        function searchGlossaryTerm(term) {
                            const searchInput = document.querySelector('input[placeholder*="Enter a term"]');
                            if (searchInput) {
                                searchInput.value = term;
                                // Trigger search button click
                                const searchBtn = searchInput.closest('.gradio-container').querySelector('button');
                                if (searchBtn) searchBtn.click();
                            }
                        }
                    </script>
                    """
                )

        def guarded_analyze(*inputs):
            try:
                return on_analyze(*inputs)
            except ValueError as exc:
                error_html = f"""
                <div style='background: #fef2f2; border: 2px solid #f87171; border-radius: 12px; padding: 1rem; color: #991b1b; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);'>
                    <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
                        <span style='font-size: 1.25rem; margin-right: 0.5rem; color: #dc2626;'>⚠️</span>
                        <strong style='color: #991b1b; font-weight: 700;'>Analysis Error</strong>
                    </div>
                    <p style='margin: 0; font-style: italic; color: #7f1d1d; font-weight: 500;'>{str(exc)}</p>
                </div>
                """
                return error_html

        def search_glossary_term(term):
            """Search for a glossary term and format the result."""
            if not term or not term.strip():
                return """
                <div style='background: rgba(255, 255, 255, 0.9); border-radius: 12px; padding: 1.5rem; color: #374151;'>
                    <h3 style='color: #4f46e5; margin-bottom: 1rem;'>🎵 Music Theory Glossary</h3>
                    <p><em>Enter a term above to search the glossary.</em></p>
                </div>
                """

            term = term.strip().lower()

            # Try to find the term in the glossary service
            try:
                # First try cadence explanation
                cadence_info = glossary_service.get_cadence_explanation(term)
                if cadence_info:
                    definition = cadence_info.get(
                        "definition", "No definition available"
                    )
                    example = cadence_info.get("example_in_C_major", "")

                    example_html = (
                        f"<div style='margin-top: 0.75rem; padding: 0.75rem; background: rgba(79, 70, 229, 0.1); border-radius: 8px;'><strong>Example in C major:</strong> {example}</div>"
                        if example
                        else ""
                    )

                    return f"""
                    <div style='background: rgba(255, 255, 255, 0.9); border-radius: 12px; padding: 1.5rem; color: #374151;'>
                        <h3 style='color: #4f46e5; margin-bottom: 1rem;'>🎵 {term.replace('_', ' ').title()}</h3>
                        <div style='font-size: 1.1rem; line-height: 1.6; margin-bottom: 1rem;'>{definition}</div>
                        {example_html}
                        <div style='margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; font-size: 0.9rem; color: #6b7280;'>
                            <em>Type: Cadence</em>
                        </div>
                    </div>
                    """

                # Try general term definition
                definition = glossary_service.get_term_definition(term)
                if definition:
                    return f"""
                    <div style='background: rgba(255, 255, 255, 0.9); border-radius: 12px; padding: 1.5rem; color: #374151;'>
                        <h3 style='color: #4f46e5; margin-bottom: 1rem;'>🎵 {term.replace('_', ' ').title()}</h3>
                        <div style='font-size: 1.1rem; line-height: 1.6; margin-bottom: 1rem;'>{definition}</div>
                        <div style='margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; font-size: 0.9rem; color: #6b7280;'>
                            <em>Type: General term</em>
                        </div>
                    </div>
                    """

                # Term not found
                return f"""
                <div style='background: rgba(255, 255, 255, 0.9); border-radius: 12px; padding: 1.5rem; color: #374151;'>
                    <h3 style='color: #ef4444; margin-bottom: 1rem;'>❌ Term Not Found</h3>
                    <p>No definition found for <strong>"{term}"</strong>.</p>
                    <div style='margin-top: 1rem; padding: 0.75rem; background: rgba(79, 70, 229, 0.1); border-radius: 8px;'>
                        <strong>Try these common terms:</strong><br>
                        half_cadence, plagal_cadence, deceptive_cadence, authentic_cadence
                    </div>
                </div>
                """

            except Exception as e:
                return f"""
                <div style='background: rgba(255, 255, 255, 0.9); border-radius: 12px; padding: 1.5rem; color: #374151;'>
                    <h3 style='color: #ef4444; margin-bottom: 1rem;'>⚠️ Search Error</h3>
                    <p>Error searching for term: {str(e)}</p>
                </div>
                """

        def process_uploaded_file_wrapper(
            file_obj,
            add_chordify,
            label_chords,
            run_analysis,
            process_full_file,
            profile,
            auto_window,
            manual_window_size,
            key_mode_preference,
        ):
            """
            Wrapper for analyze_uploaded_file() that formats outputs for Gradio.

            Handles file upload, processes through analyze_uploaded_file(), and
            formats results for Gradio components.
            """
            # Opening move: handle empty file upload
            if file_obj is None:
                return (
                    gr.update(visible=False),  # window_info_output
                    {"error": "No file uploaded"},
                    None,
                    None,
                    "<p><em>Please upload a file first.</em></p>",
                    gr.update(visible=False),  # midi_warning_box
                    gr.update(visible=False),  # parsing_log_accordion
                    "",  # parsing_log_output
                )

            # Main play: process the file
            try:
                import os

                file_path = (
                    file_obj.name if hasattr(file_obj, "name") else str(file_obj)
                )

                result = analyze_uploaded_file(
                    file_path=file_path,
                    add_chordify=add_chordify,
                    label_chords=label_chords,
                    run_analysis=run_analysis,
                    profile=profile,
                    process_full_file=process_full_file,
                    auto_window=auto_window,
                    manual_window_size=manual_window_size,
                    key_mode_preference=key_mode_preference,
                )

                # Format info JSON
                info_json = {
                    "chord_symbols": result["chord_symbols"],
                    "key_hint": result["key_hint"],
                    "metadata": result["metadata"],
                }

                # Format window size info prominently
                window_info_text = ""
                window_info_visible = False
                if result.get("window_size_used") is not None:
                    # Map QL to note names
                    ql_to_note = {
                        0.5: "eighth note",
                        1.0: "quarter note",
                        2.0: "half note",
                        4.0: "whole note",
                    }
                    note_name = ql_to_note.get(result["window_size_used"], "custom")
                    info_json["window_size"] = (
                        f"{result['window_size_used']} QL ({note_name})"
                    )

                    # Create prominent display
                    window_mode = "🤖 Auto" if auto_window else "✋ Manual"
                    window_info_text = f"**🎯 Analysis Window:** {window_mode} - **{result['window_size_used']} QL** ({note_name})"
                    window_info_visible = True

                # Comparison functionality removed - no longer used by demo UI
                comparison_data = None
                agreement_text = ""

                # Format analysis HTML (if available)
                analysis_html = "<p><em>No analysis run.</em></p>"
                if result["analysis_result"]:
                    analysis_html = format_file_analysis_html(
                        result["analysis_result"],
                        result.get("chordified_symbols_with_measures", []),
                        result.get("key_hint"),
                    )

                # Victory lap: return all formatted outputs
                # Generate standalone OSMD HTML file (Gradio blocks inline JS)
                # Use notation_url (always 20 measures) for viewer, not download_url
                notation_html_file = generate_osmd_html_file(result["notation_url"])
                print(f"DEBUG: Generated OSMD viewer file: {notation_html_file}")

                # Read HTML content and encode as data URI (Gradio file serving doesn't work for iframes)
                import base64
                import os

                # Check size of MusicXML file
                xml_size = (
                    os.path.getsize(result["download_url"])
                    if os.path.exists(result["download_url"])
                    else 0
                )
                print(f"DEBUG: MusicXML file size: {xml_size:,} bytes")

                # Read and encode the HTML viewer
                with open(notation_html_file, "rb") as f:
                    html_bytes = f.read()
                html_base64 = base64.b64encode(html_bytes).decode("utf-8")

                # Create iframe with data URI instead of file path
                notation_iframe = f'<iframe src="data:text/html;base64,{html_base64}" width="100%" height="700px" frameborder="0" style="border: 1px solid #ddd; border-radius: 8px;"></iframe>'
                print(
                    f"DEBUG: Created data URI iframe ({len(html_base64)} base64 chars)"
                )

                # Determine if we should show MIDI warning and parsing logs
                show_midi_warning = result.get("is_midi", False)
                parsing_logs = result.get("parsing_logs")
                show_parsing_logs = parsing_logs is not None and len(parsing_logs) > 0

                return (
                    gr.update(
                        value=window_info_text, visible=window_info_visible
                    ),  # window_info_output
                    info_json,
                    notation_iframe,  # Return iframe pointing to HTML file
                    result["download_url"],
                    analysis_html,
                    gr.update(visible=show_midi_warning),  # midi_warning_box
                    gr.update(
                        visible=show_parsing_logs, open=show_parsing_logs
                    ),  # parsing_log_accordion
                    parsing_logs or "",  # parsing_log_output
                )

            except Exception as e:
                # Handle errors gracefully
                import traceback

                error_details = traceback.format_exc()
                return (
                    gr.update(visible=False),  # window_info_output (hide on error)
                    {"error": str(e)},
                    None,
                    None,
                    f"<div style='color: red;'><strong>Error:</strong> {e}<br/><pre>{error_details}</pre></div>",
                    gr.update(visible=False),  # midi_warning_box
                    gr.update(
                        visible=True, open=True
                    ),  # parsing_log_accordion (show on error)
                    f"❌ Error during processing:\n{error_details}",  # parsing_log_output
                )

        # Event handlers
        search_btn.click(
            search_glossary_term, inputs=[glossary_search], outputs=[glossary_output]
        )

        # Mutual exclusion: Auto checkbox toggles slider interactivity
        auto_window_check.change(
            fn=lambda auto: gr.update(interactive=not auto),
            inputs=[auto_window_check],
            outputs=[window_size_slider],
        )

        upload_analyze_btn.click(
            process_uploaded_file_wrapper,
            inputs=[
                file_upload,
                add_chordify_check,
                label_chords_check,
                run_analysis_check,
                process_full_file_check,
                upload_profile,
                auto_window_check,
                window_size_slider,
                key_mode_preference,  # Major or Minor key preference
            ],
            outputs=[
                window_info_output,  # Window size display (prominent)
                upload_info_output,
                upload_notation_output,
                upload_download_output,
                upload_analysis_output,
                midi_warning_box,  # Show/hide MIDI warning
                parsing_log_accordion,  # Show/hide parsing log accordion
                parsing_log_output,  # Parsing log text
            ],
        )

        analyze_btn.click(
            guarded_analyze,
            inputs=[
                key_input,
                profile_input,
                chords_input,
                romans_input,
                melody_input,
                scales_input,
            ],
            outputs=[analysis_output],
        )

        # Clear button handlers
        clear_chords.click(
            lambda: "",
            outputs=[chords_input],
        )
        clear_romans.click(
            lambda: "",
            outputs=[romans_input],
        )
        clear_melody.click(
            lambda: "",
            outputs=[melody_input],
        )
        clear_scales.click(
            lambda: "",
            outputs=[scales_input],
        )

        # Chord progression example handlers - Clear other fields and set chord + profile + key
        chord_ex1.click(
            lambda: ("Am F C G", "", "", "", "pop", "C major"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )
        chord_ex2.click(
            lambda: ("Dm G7 C", "", "", "", "classical", "C major"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )
        chord_ex3.click(
            lambda: ("Dm7 G7 Cmaj7", "", "", "", "jazz", "C major"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )
        chord_ex4.click(
            lambda: ("Am F C G", "", "", "", "classical", "A minor"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )
        chord_ex5.click(
            lambda: ("C F Bb C", "", "", "", "folk", "C major"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )
        chord_ex6.click(
            lambda: ("E5 A5 B5 E5", "", "", "", "pop", "E major"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )

        # Roman numeral example handlers - Clear other fields and set romans + profile + key
        roman_ex1.click(
            lambda: ("", "I vi IV V", "", "", "classical", "C major"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )
        roman_ex2.click(
            lambda: ("", "ii65 V7 I", "", "", "classical", "C major"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )
        roman_ex3.click(
            lambda: ("", "vi IV I V", "", "", "classical", "C major"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )

        # Melody example handlers - Clear other fields and set melody + profile + key
        melody_ex1.click(
            lambda: ("", "", "C4 D4 E4 F4 G4 A4 B4 C5", "", "classical", "C major"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )
        melody_ex2.click(
            lambda: ("", "", "C4 E4 G4 C5 G4 E4 C4", "", "classical", "C major"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )
        melody_ex3.click(
            lambda: ("", "", "G4 A4 B4 C5 B4 A4 G4 F4", "", "classical", "C major"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )
        melody_ex4.click(
            lambda: ("", "", "E4 F4 G4 A4 B4 C5", "", "classical", "C major"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )
        melody_ex5.click(
            lambda: ("", "", "C4 F4 A4 D5 G4 C5", "", "classical", "C major"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )
        melody_ex6.click(
            lambda: ("", "", "C4 C#4 D4 D#4 E4 F4 F#4 G4", "", "classical", "C major"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )

        # Scale example handlers - Clear other fields and set scale + profile + key
        scale_ex1.click(
            lambda: ("", "", "", "C D E F G A B", "classical", "C major"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )
        scale_ex2.click(
            lambda: ("", "", "", "A B C D E F G", "classical", "A minor"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )
        scale_ex3.click(
            lambda: ("", "", "", "D E F G A B C", "folk", "C major"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )
        scale_ex4.click(
            lambda: ("", "", "", "G A B C D E F", "folk", "C major"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )
        scale_ex5.click(
            lambda: ("", "", "", "E F G A B C D", "classical", "C major"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )
        scale_ex6.click(
            lambda: ("", "", "", "F G A B C D E", "classical", "C major"),
            outputs=[
                chords_input,
                romans_input,
                melody_input,
                scales_input,
                profile_input,
                key_input,
            ],
        )

    server_port = port or int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    demo.launch(
        server_name="127.0.0.1",
        server_port=server_port,
        share=False,
        debug=False,
        show_error=True,
        inline=False,
    )


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the harmonic analysis demo (CLI or Gradio UI). Provide at least one "
            "of chords, roman numerals, melody, or scale notes."
        )
    )
    parser.add_argument(
        "--key", default=None, help="Optional key hint (e.g. 'C major')"
    )
    parser.add_argument(
        "--profile",
        default="classical",
        help="Profile hint (e.g. classical, jazz, pop)",
    )
    parser.add_argument(
        "--chords",
        help=(
            "Chord symbols separated by spaces or commas (e.g. 'G7 Cmaj7' or 'G7,Cmaj7'). "
            "Half-diminished: use 'm7b5' (e.g. 'Dm7b5') - keyboard friendly! "
            "Slash chords: 'C/E' for inversions. Optional."
        ),
    )
    parser.add_argument(
        "--romans",
        help="Roman numerals separated by spaces or commas. Optional; align with chords if both provided.",
    )
    parser.add_argument(
        "--melody",
        help="Melody notes or MIDI numbers separated by spaces or commas. Optional.",
    )
    parser.add_argument(
        "--scale",
        action="append",
        help="Scale notes separated by spaces or commas (e.g. 'F# A A A G# F#')."
        " Provide multiple --scale flags for additional options.",
    )
    parser.add_argument(
        "--gradio",
        action="store_true",
        help="Launch the Gradio UI instead of the CLI summary.",
    )
    parser.add_argument(
        "--gradio-port",
        type=int,
        help="Optional port for Gradio UI (default: 7860). Only used with --gradio.",
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Launch the FastAPI server (requires fastapi and uvicorn).",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for API mode (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for API mode (default: 8000).",
    )
    args = parser.parse_args()

    if args.gradio and args.api:
        parser.error("Choose either --gradio or --api, not both.")

    if args.api:
        try:
            import uvicorn
        except ImportError as exc:  # pragma: no cover - optional dependency guard
            raise SystemExit(
                "Uvicorn is required for API mode. Install it with 'pip install uvicorn'."
            ) from exc

        app = create_api_app()
        uvicorn.run(app, host=args.host, port=args.port)
        return

    if args.gradio:
        import os

        gradio_port = args.gradio_port or int(os.getenv("GRADIO_SERVER_PORT", "7860"))
        launch_gradio_demo(
            default_key=args.key, default_profile=args.profile, port=gradio_port
        )
        return

    try:
        key_hint = resolve_key_input(args.key)

        # Validate exclusive input rule
        scales_input_text = args.scale[0] if args.scale else None
        validate_exclusive_input(
            args.chords, args.romans, args.melody, scales_input_text
        )

        # Use unified service for all analysis types
        service = get_service()
        if args.chords:
            chords = validate_list("chord", parse_csv(args.chords))
            envelope = asyncio.run(
                service.analyze_with_patterns_async(
                    chord_symbols=chords, profile=args.profile, key_hint=key_hint
                )
            )
        elif args.romans:
            romans = validate_list("roman", parse_csv(args.romans))
            envelope = asyncio.run(
                service.analyze_with_patterns_async(
                    romans=romans, profile=args.profile, key_hint=key_hint
                )
            )
        elif args.melody:
            melody = validate_list("note", parse_csv(args.melody))
            envelope = asyncio.run(
                service.analyze_with_patterns_async(
                    melody=melody, profile=args.profile, key_hint=key_hint
                )
            )
        elif args.scale:
            scales = parse_scales(args.scale)
            envelope = asyncio.run(
                service.analyze_with_patterns_async(
                    notes=scales[0], profile=args.profile, key_hint=key_hint
                )
            )
        else:
            raise ValueError(
                "Must provide one of: --chords, --romans, --melody, or --scale"
            )
    except ValueError as exc:
        parser.error(str(exc))

    print(summarize_envelope(envelope, include_raw=False))


if __name__ == "__main__":
    main()
