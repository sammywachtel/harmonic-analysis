#!/usr/bin/env python3
"""Interactive demo for the unified harmonic-analysis pattern engine."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

OPTIONAL_DEP_HINTS: Dict[str, str] = {
    "scipy": "Install SciPy (e.g. 'pip install scipy' or 'pip install -r requirements.txt').",
    "sklearn": "Install scikit-learn (e.g. 'pip install scikit-learn' or 'pip install -r requirements.txt').",
    "jsonschema": "Install jsonschema (e.g. 'pip install jsonschema' or 'pip install -r requirements.txt').",
}

PROFILE_OPTIONS = [
    "classical",
    "jazz",
    "pop",
    "folk",
    "choral",
]

KEY_OPTION_NONE = "None"

KEY_OPTIONS = [
    KEY_OPTION_NONE,
    "C major",
    "G major",
    "D major",
    "A major",
    "E major",
    "B major",
    "F# major",
    "C# major",
    "F major",
    "Bb major",
    "Eb major",
    "Ab major",
    "Db major",
    "Gb major",
    "Cb major",
    "A minor",
    "E minor",
    "B minor",
    "F# minor",
    "C# minor",
    "G# minor",
    "D# minor",
    "A# minor",
    "D minor",
    "G minor",
    "C minor",
    "F minor",
    "Bb minor",
    "Eb minor",
    "Ab minor",
]

MISSING_SCALE_KEY_MSG = "Scale analysis requires a key context."
MISSING_MELODY_KEY_MSG = "Melody analysis requires a key context."

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if SRC_ROOT.exists() and str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from harmonic_analysis.core.pattern_engine.aggregator import Aggregator
    from harmonic_analysis.core.pattern_engine.pattern_engine import (
        AnalysisContext,
        PatternEngine,
    )
    from harmonic_analysis.core.pattern_engine.pattern_loader import PatternLoader
    from harmonic_analysis.core.pattern_engine.plugin_registry import PluginRegistry
    from harmonic_analysis.core.pattern_engine.token_converter import romanize_chord
except ModuleNotFoundError as exc:  # pragma: no cover - defensive import guard
    missing = exc.name or str(exc)
    hint = OPTIONAL_DEP_HINTS.get(missing)
    if hint:
        raise SystemExit(
            f"Optional dependency '{missing}' is required to run the demo. {hint}"
        ) from exc
    raise

from harmonic_analysis.api.analysis import analyze_melody, analyze_scale


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

CHORD_RE = re.compile(
    r"^[A-G](?:#|b)?(?:"
    r"maj7|maj9|maj13|maj11|maj|m7|m9|m11|m13|m6|m|dim7|dim|aug|add9|sus2|sus4|"
    r"7|9|11|13|6|\+7|\+|°|ø)?"
    r"(?:/[A-G](?:#|b)?)?$",
    re.IGNORECASE,
)

ROMAN_RE = re.compile(r"^[ivIV]+(?:[#b♯♭]?[ivIV]+)?(?:[°ø+]?)(?:\d+)?$")
NOTE_RE = re.compile(r"^[A-Ga-g](?:#|b)?(?:\d+)?$")


def parse_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []

    # Handle both comma and space delimiters
    # First try comma separation
    if "," in value:
        return [item.strip() for item in value.split(",") if item.strip()]
    else:
        # Use space separation if no commas found
        return [item.strip() for item in value.split() if item.strip()]


def resolve_key_input(value: Optional[str]) -> Optional[str]:
    """Normalize user-provided key hints, treating 'None' as no key."""

    if value is None:
        return None

    if isinstance(value, str):
        normalized = value.strip()
        if not normalized or normalized.lower() == "none":
            return None
        return normalized

    return value


def validate_list(kind: str, items: List[str]) -> List[str]:
    if not items:
        return []

    validator = {
        "chord": CHORD_RE,
        "roman": ROMAN_RE,
        "note": NOTE_RE,
    }[kind]

    invalid = [item for item in items if not validator.match(item)]
    if invalid:
        raise ValueError(f"Invalid {kind} entries: {', '.join(invalid)}")
    return items


def parse_melody(value: Optional[str]) -> List[str]:
    items = parse_csv(value)
    if not items:
        return []
    validated: List[str] = []
    for item in items:
        token = item.strip()
        if token.isdigit():
            validated.append(token)
        else:
            if not NOTE_RE.match(token):
                raise ValueError(f"Invalid melody note: {token}")
            validated.append(token)
    return validated


def parse_scales(values: Optional[Sequence[str]]) -> List[List[str]]:
    if not values:
        return []

    scales: List[List[str]] = []
    for raw in values:
        notes = validate_list("note", parse_csv(raw))
        if not notes:
            raise ValueError("Scale definitions cannot be empty.")
        scales.append(notes)
    return scales


# ---------------------------------------------------------------------------
# Engine bootstrap
# ---------------------------------------------------------------------------

_ENGINE: Optional[PatternEngine] = None


def build_engine() -> PatternEngine:
    loader = PatternLoader()
    aggregator = Aggregator()
    plugins = PluginRegistry()
    engine = PatternEngine(loader=loader, aggregator=aggregator, plugins=plugins)

    patterns_path = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "harmonic_analysis"
        / "core"
        / "pattern_engine"
        / "patterns_unified.json"
    )
    engine.load_patterns(patterns_path)
    return engine


def get_engine() -> PatternEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = build_engine()
    return _ENGINE


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


def format_confidence_badge(confidence: float) -> str:
    """Create a colored confidence badge based on value."""
    if confidence >= 0.8:
        color = "#22c55e"  # Green
        label = "High"
    elif confidence >= 0.6:
        color = "#f59e0b"  # Amber
        label = "Medium"
    elif confidence >= 0.4:
        color = "#ef4444"  # Red
        label = "Low"
    else:
        color = "#64748b"  # Gray
        label = "Very Low"

    return f'<span style="background-color: {color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">{label} ({confidence:.3f})</span>'


def format_evidence_html(evidence_list) -> str:
    """Format evidence list as styled HTML."""
    if not evidence_list:
        return "<p style='color: #64748b; font-style: italic;'>No evidence patterns found.</p>"

    html = "<div style='margin-top: 1rem;'>"
    for i, evidence in enumerate(evidence_list, 1):
        details = evidence.details or {}
        raw_features = details.get("features", {})

        if isinstance(raw_features, dict):
            features = dict(raw_features)
            features_ui = features.pop("features_ui", {})
        else:
            features = raw_features
            features_ui = {}

        # Evidence card
        html += f"""
        <div style='background: #f8fafc; border-left: 4px solid #3b82f6; padding: 1rem; margin-bottom: 0.75rem; border-radius: 0 8px 8px 0;'>
            <div style='font-weight: 600; color: #1e40af; margin-bottom: 0.5rem;'>
                🎼 Pattern {i}: {evidence.reason}
            </div>
        """

        # Features
        if features_ui:
            html += "<div style='margin-left: 1rem; color: #475569;'>"
            for key, meta in features_ui.items():
                label = meta.get("label", key)
                val = meta.get("value")
                tooltip = meta.get("tooltip", "")
                tooltip_text = (
                    f" <span style='color: #64748b; font-size: 0.85rem;'>({tooltip})</span>"
                    if tooltip
                    else ""
                )
                html += f"<div style='margin: 0.25rem 0;'>• <strong>{label}:</strong> {val}{tooltip_text}</div>"
            html += "</div>"
        elif features:
            html += "<div style='margin-left: 1rem; color: #475569;'>"
            for key, val in features.items():
                html += f"<div style='margin: 0.25rem 0;'>• <strong>{key}:</strong> {val}</div>"
            html += "</div>"

        # Additional details
        raw_score = details.get("raw_score")
        if raw_score is not None:
            html += f"<div style='margin-left: 1rem; color: #64748b; font-size: 0.9rem;'>Raw score: {raw_score}</div>"

        if "span" in details:
            html += f"<div style='margin-left: 1rem; color: #64748b; font-size: 0.9rem;'>Span: {details['span']}</div>"

        html += "</div>"

    html += "</div>"
    return html


def format_analysis_html(envelope) -> str:
    """Format the analysis envelope as rich HTML."""
    primary = envelope.primary

    # Main container with modern styling
    html = """
    <div style='font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #334155;'>
    """

    # Primary interpretation section
    html += """
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem;'>
        <h2 style='margin: 0 0 1rem 0; display: flex; align-items: center; font-size: 1.5rem;'>
            🎵 Primary Interpretation
        </h2>
    """

    if not primary:
        html += "<p style='margin: 0; opacity: 0.9;'>No primary interpretation returned.</p>"
    else:
        # Analysis type and confidence
        html += f"""
        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;'>
            <div>
                <div style='opacity: 0.8; font-size: 0.9rem; margin-bottom: 0.25rem;'>Analysis Type</div>
                <div style='font-size: 1.25rem; font-weight: 600;'>{primary.type.value.title()}</div>
            </div>
            <div>
                <div style='opacity: 0.8; font-size: 0.9rem; margin-bottom: 0.25rem;'>Confidence</div>
                <div style='font-size: 1.25rem;'>{format_confidence_badge(primary.confidence)}</div>
            </div>
        </div>
        """

        # Key and mode info
        if primary.key_signature or primary.mode:
            html += "<div style='display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;'>"
            if primary.key_signature:
                html += f"""
                <div>
                    <div style='opacity: 0.8; font-size: 0.9rem; margin-bottom: 0.25rem;'>Key Signature</div>
                    <div style='font-size: 1.1rem; font-weight: 500;'>{primary.key_signature}</div>
                </div>
                """
            if primary.mode:
                html += f"""
                <div>
                    <div style='opacity: 0.8; font-size: 0.9rem; margin-bottom: 0.25rem;'>Mode</div>
                    <div style='font-size: 1.1rem; font-weight: 500;'>{primary.mode}</div>
                </div>
                """
            html += "</div>"

        # Roman numerals
        if primary.roman_numerals:
            html += f"""
            <div style='margin-bottom: 1rem;'>
                <div style='opacity: 0.8; font-size: 0.9rem; margin-bottom: 0.5rem;'>Roman Numeral Analysis</div>
                <div style='background: rgba(255,255,255,0.15); padding: 0.75rem; border-radius: 8px; font-family: "SF Mono", Monaco, monospace; font-size: 1.1rem; letter-spacing: 0.5px;'>
                    {' - '.join(primary.roman_numerals)}
                </div>
            </div>
            """

        # Reasoning
        if primary.reasoning:
            html += f"""
            <div style='margin-bottom: 1rem;'>
                <div style='opacity: 0.8; font-size: 0.9rem; margin-bottom: 0.5rem;'>Analysis Reasoning</div>
                <div style='background: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 8px; font-style: italic;'>
                    {primary.reasoning}
                </div>
            </div>
            """

        # Glossary terms
        if primary.terms:
            html += """
            <div>
                <div style='opacity: 0.8; font-size: 0.9rem; margin-bottom: 0.5rem;'>Glossary Terms</div>
                <div style='display: flex; flex-wrap: wrap; gap: 0.5rem;'>
            """
            for key, value in primary.terms.items():
                if isinstance(value, dict):
                    label = value.get("label", key)
                    tooltip = value.get("tooltip", "")
                else:
                    label = value
                    tooltip = ""

                tooltip_text = f" - {tooltip}" if tooltip else ""
                html += f"""
                <span style='background: rgba(255,255,255,0.2); color: white; padding: 0.25rem 0.75rem; border-radius: 16px; font-size: 0.85rem;' title='{key}: {label}{tooltip_text}'>
                    {label}
                </span>
                """
            html += "</div></div>"

    html += "</div>"  # End primary section

    # Alternatives section
    if envelope.alternatives:
        html += """
        <div style='background: #f1f5f9; border: 2px solid #e2e8f0; padding: 1.25rem; border-radius: 12px; margin-bottom: 1.5rem;'>
            <h3 style='margin: 0 0 1rem 0; color: #475569; display: flex; align-items: center;'>
                🔄 Alternative Interpretations
            </h3>
            <div style='display: grid; gap: 0.75rem;'>
        """

        for idx, alt in enumerate(envelope.alternatives, 1):
            html += f"""
            <div style='background: white; padding: 0.75rem 1rem; border-radius: 8px; border-left: 3px solid #6366f1; display: flex; justify-content: space-between; align-items: center;'>
                <span><strong>#{idx}</strong> {alt.type.value.title()}</span>
                <span>{format_confidence_badge(alt.confidence)}</span>
            </div>
            """

        html += "</div></div>"

    # Evidence section
    if envelope.evidence:
        html += """
        <div style='background: white; border: 2px solid #e5e7eb; padding: 1.25rem; border-radius: 12px;'>
            <h3 style='margin: 0 0 1rem 0; color: #374151; display: flex; align-items: center;'>
                🔍 Supporting Evidence
            </h3>
        """
        html += format_evidence_html(envelope.evidence)
        html += "</div>"

    html += "</div>"  # End main container
    return html


def summarize_envelope(envelope, include_raw: bool = True) -> str:
    lines: List[str] = []
    primary = envelope.primary
    lines.append("===== Primary Interpretation =====")
    if not primary:
        lines.append("No primary interpretation returned.")
    else:
        lines.append(f"Type           : {primary.type.value}")
        lines.append(f"Confidence     : {primary.confidence:.3f}")
        if primary.key_signature:
            lines.append(f"Key            : {primary.key_signature}")
        if primary.mode:
            lines.append(f"Mode           : {primary.mode}")
        if primary.reasoning:
            lines.append(f"Reasoning      : {primary.reasoning}")
        if primary.roman_numerals:
            lines.append(f"Roman Numerals : {', '.join(primary.roman_numerals)}")
        if primary.terms:
            lines.append("")
            lines.append("Glossary Terms:")
            for key, value in primary.terms.items():
                if isinstance(value, dict):
                    label = value.get("label", key)
                    tooltip = value.get("tooltip", "")
                else:
                    label = value
                    tooltip = ""
                suffix = f" ({tooltip})" if tooltip else ""
                lines.append(f"  - {key}: {label}{suffix}")

    if envelope.alternatives:
        lines.append("")
        lines.append("===== Alternatives =====")
        for idx, alt in enumerate(envelope.alternatives, start=1):
            lines.append(f"[{idx}] {alt.type.value} — confidence {alt.confidence:.3f}")

    if envelope.evidence:
        lines.append("")
        lines.append("===== Evidence =====")
        for evidence in envelope.evidence:
            details = evidence.details or {}
            raw_features = details.get("features", {})
            if isinstance(raw_features, dict):
                features = dict(raw_features)
                features_ui = features.pop("features_ui", {})
            else:
                features = raw_features
                features_ui = {}
            lines.append(f"- Pattern: {evidence.reason}")
            if features_ui:
                for key, meta in features_ui.items():
                    label = meta.get("label", key)
                    val = meta.get("value")
                    tooltip = meta.get("tooltip", "")
                    suffix = f" ({tooltip})" if tooltip else ""
                    lines.append(f"    • {label}: {val}{suffix}")
            elif features:
                for key, val in features.items():
                    lines.append(f"    • {key}: {val}")
            raw_score = details.get("raw_score")
            if raw_score is not None:
                lines.append(f"    • Raw score: {raw_score}")
            if "span" in details:
                lines.append(f"    • Span: {details['span']}")

    if include_raw:
        lines.append("")
        lines.append("===== Raw Envelope =====")
        lines.append(json.dumps(envelope.to_dict(), indent=2))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------


def normalize_scale_input(raw_scales: Optional[str | Sequence[str]]) -> List[str]:
    if raw_scales is None:
        return []
    if isinstance(raw_scales, str):
        candidates = [
            line.strip() for line in raw_scales.splitlines() if line and line.strip()
        ]
        return candidates
    return [item.strip() for item in raw_scales if item and item.strip()]


def analyze_progression(
    *,
    key: Optional[str],
    profile: str,
    chords_text: Optional[str],
    romans_text: Optional[str],
    melody_text: Optional[str],
    scales_input: Optional[str | Sequence[str]],
) -> AnalysisContext:
    if not any([chords_text, romans_text, melody_text, scales_input]):
        raise ValueError(
            "Provide at least one of --chords, --romans, --melody, or --scale for analysis."
        )

    key_hint = resolve_key_input(key)

    chords = validate_list("chord", parse_csv(chords_text)) if chords_text else []

    romans = validate_list("roman", parse_csv(romans_text)) if romans_text else []
    if chords and romans and len(romans) != len(chords):
        raise ValueError("Number of roman numerals must match number of chords.")

    if chords and not romans and key_hint:
        auto_romans = []
        for chord in chords:
            try:
                auto_romans.append(romanize_chord(chord, key_hint))
            except Exception:
                auto_romans = []
                break
        if auto_romans:
            romans = [rn.replace("b", "♭") for rn in auto_romans]

    melody = parse_melody(melody_text)

    scale_entries = normalize_scale_input(scales_input)
    scales = parse_scales(scale_entries)

    if melody and not key_hint:
        raise ValueError(MISSING_MELODY_KEY_MSG)

    if scales and not key_hint:
        raise ValueError(MISSING_SCALE_KEY_MSG)

    return AnalysisContext(
        key=key_hint,
        chords=chords,
        roman_numerals=romans,
        melody=melody,
        scales=scales,
        metadata={"profile": profile, "source": "demo/full_library_demo.py"},
    )


def run_analysis(context: AnalysisContext):
    engine = get_engine()
    return engine.analyze(context)


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

    engine = get_engine()
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
        return {
            "summary": summarize_envelope(envelope, include_raw=False),
            "analysis": envelope.to_dict(),
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

            context = analyze_progression(
                key=resolve_key_input(request.key),
                profile=request.profile or "classical",
                chords_text=chords_text,
                romans_text=romans_text,
                melody_text=melody_text,
                scales_input=scales_input,
            )
            envelope = engine.analyze(context)
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


def launch_gradio_demo(default_key: Optional[str], default_profile: str) -> None:
    try:
        import gradio as gr
    except ImportError as exc:  # pragma: no cover - guard for missing optional dep
        raise SystemExit(
            "Gradio is required for the demo. Install it with 'pip install gradio'."
        ) from exc

    engine = get_engine()

    def on_analyze(key, profile, chords, romans, melody, scales):
        normalized_key = resolve_key_input(key)
        context = analyze_progression(
            key=normalized_key,
            profile=profile,
            chords_text=chords,
            romans_text=romans,
            melody_text=melody,
            scales_input=scales,
        )
        envelope = engine.analyze(context)
        html_output = format_analysis_html(envelope)
        return html_output

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
    """

    with gr.Blocks(title="Harmonic Analysis Demo", css=custom_css) as demo:

        gr.Markdown("# Harmonic Analysis Demo")
        gr.Markdown(
            "Analyze chord progressions, melodies, and scales with space or comma-separated input."
        )

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
                chords_input = gr.Textbox(
                    label="Chord Symbols",
                    placeholder="Em Am D G",
                )
                romans_input = gr.Textbox(
                    label="Roman Numerals",
                    placeholder="vi ii V I",
                )

            with gr.Column():
                melody_input = gr.Textbox(
                    label="Melodic Line",
                    placeholder="E4 G4 F#4 D4",
                )
                scales_input = gr.Textbox(
                    label="Scale Analysis",
                    placeholder="E F# G A B C D",
                    lines=3,
                )

        analyze_btn = gr.Button("Analyze", variant="primary")

        analysis_output = gr.HTML(
            value="Enter musical content above and click analyze."
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

    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        debug=True,
        show_error=True,
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
        help="Chord symbols separated by spaces or commas (e.g. 'G7 Cmaj7' or 'G7,Cmaj7'). Optional.",
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
        launch_gradio_demo(default_key=args.key, default_profile=args.profile)
        return

    try:
        key_hint = resolve_key_input(args.key)
        context = analyze_progression(
            key=key_hint,
            profile=args.profile,
            chords_text=args.chords,
            romans_text=args.romans,
            melody_text=args.melody,
            scales_input=args.scale,
        )
        envelope = run_analysis(context)
    except ValueError as exc:
        parser.error(str(exc))

    print(summarize_envelope(envelope))


if __name__ == "__main__":
    main()
