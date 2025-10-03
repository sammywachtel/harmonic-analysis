#!/usr/bin/env python3
"""Interactive demo for the unified harmonic-analysis pattern engine."""

from __future__ import annotations

import argparse
import asyncio
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


def validate_exclusive_input(
    chords_text: Optional[str],
    romans_text: Optional[str],
    melody_text: Optional[str],
    scales_input: Optional[str],
) -> None:
    """Ensure only one type of musical input is provided."""
    inputs_provided = [
        ("chords", chords_text and chords_text.strip()),
        ("romans", romans_text and romans_text.strip()),
        ("melody", melody_text and melody_text.strip()),
        ("scales", scales_input and scales_input.strip()),
    ]

    provided_types = [name for name, value in inputs_provided if value]

    if len(provided_types) == 0:
        raise ValueError(
            "Please provide at least one type of musical input (chords, romans, melody, or scales)."
        )

    if len(provided_types) > 1:
        raise ValueError(
            f"Please provide only one type of musical input. "
            f"Found: {', '.join(provided_types)}. "
            f"Analyze one type at a time for best results."
        )


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
# Service bootstrap
# ---------------------------------------------------------------------------

_SERVICE: Optional[PatternAnalysisService] = None


def get_service() -> PatternAnalysisService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = PatternAnalysisService()
    return _SERVICE


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


def generate_code_snippet(
    chord_symbols: List[str], profile: str, key_hint: Optional[str], envelope
) -> str:
    """Generate Python code snippet to reproduce the analysis."""

    # Escape single quotes in inputs for code generation
    chords_str = str(chord_symbols).replace("'", "\\'")
    profile_escaped = profile.replace("'", "\\'")
    key_escaped = key_hint.replace('"', '\\"') if key_hint else None
    key_str = f"'{key_escaped}'" if key_hint else "None"

    # Basic async example
    async_code = f"""from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

# Initialize the analysis service
service = PatternAnalysisService()

# Analyze your chord progression
result = await service.analyze_with_patterns_async(
    chord_symbols={chords_str},
    profile='{profile_escaped}',
    key_hint={key_str}
)

# Access the results
print(f"Analysis Type: {{result.primary.type.value}}")
print(f"Confidence: {{result.primary.confidence:.3f}}")
print(f"Roman Numerals: {{' - '.join(result.primary.roman_numerals)}}")
print(f"Key: {{result.primary.key_signature}}")
print(f"Mode: {{result.primary.mode}}")

# Access evidence patterns
for evidence in result.evidence:
    print(f"Pattern: {{evidence.reason}} (Score: {{evidence.details.raw_score}})")"""

    # Sync wrapper example
    sync_code = f"""from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService
import asyncio

# Initialize the analysis service
service = PatternAnalysisService()

# Sync wrapper function
def analyze_progression():
    return asyncio.run(
        service.analyze_with_patterns_async(
            chord_symbols={chords_str},
            profile='{profile_escaped}',
            key_hint={key_str}
        )
    )

# Run the analysis
result = analyze_progression()
print(f"{{result.primary.type.value}} analysis with {{result.primary.confidence:.3f}} confidence")"""

    # API usage example
    api_code = f"""import requests
import json

# API endpoint
url = "http://localhost:7860/analysis/progression"

# Request payload
payload = {{
    "chords": {chords_str},
    "profile": "{profile_escaped}",
    "key": {key_str}
}}

# Make the request
response = requests.post(url, json=payload)
result = response.json()

# Display results
primary = result["primary"]
print(f"Analysis: {{primary['type']}} ({{primary['confidence']:.3f}})")
print(f"Roman Numerals: {{' - '.join(primary['roman_numerals'])}}")"""

    return async_code, sync_code, api_code


def generate_enhanced_evidence_cards(envelope) -> str:
    """Generate enhanced evidence display with rich cards and visualizations."""
    if not envelope.evidence:
        return ""

    evidence_html = """
    <div style='margin-top: 1.5rem;'>
        <div style='opacity: 0.9; font-size: 1rem; margin-bottom: 1rem; font-weight: 600; color: white;'>
            📊 Analysis Evidence
        </div>
        <div style='display: flex; flex-direction: column; gap: 1rem;'>
    """

    for evidence in envelope.evidence:
        pattern_family = (
            evidence.reason.split(".")[0] if "." in evidence.reason else "general"
        )

        # Color coding by pattern family
        family_colors = {
            "cadence": "#8b5cf6",  # Purple
            "modal": "#06b6d4",  # Cyan
            "functional": "#22c55e",  # Green
            "chromatic": "#f59e0b",  # Amber
            "general": "#6b7280",  # Gray
        }

        color = family_colors.get(pattern_family, family_colors["general"])
        score = evidence.details.get("raw_score", 0)
        span = evidence.details.get("span", [])

        # Create chord span display
        chord_span_text = ""
        if span and len(span) >= 2:
            start_idx, end_idx = span[0], span[1]
            if hasattr(envelope, "chord_symbols") and envelope.chord_symbols:
                chords_in_span = envelope.chord_symbols[start_idx:end_idx]
                chord_span_text = f"Chords {start_idx+1}-{end_idx}: <strong>{' → '.join(chords_in_span)}</strong>"

        # Progress bar for confidence
        progress_width = min(100, max(5, score * 100))  # Ensure visible minimum

        evidence_html += f"""
        <div style='background: rgba(255, 255, 255, 0.95); border-radius: 12px; padding: 1rem;
                    border-left: 4px solid {color}; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;'>
                <div>
                    <span style='background: {color}; color: white; padding: 0.25rem 0.75rem;
                                 border-radius: 16px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;'>
                        {pattern_family}
                    </span>
                    <span style='margin-left: 0.75rem; font-weight: 600; color: #374151; font-size: 1rem;'>
                        {evidence.reason.replace('_', ' ').title()}
                    </span>
                </div>
                <div style='font-weight: 600; color: {color}; font-size: 1.1rem;'>
                    {score:.3f}
                </div>
            </div>

            <div style='background: #f3f4f6; border-radius: 8px; height: 8px; margin-bottom: 0.75rem;'>
                <div style='background: {color}; height: 100%; border-radius: 8px; width: {progress_width}%;
                            transition: width 0.3s ease;'></div>
            </div>

            {f"<div style='color: #6b7280; font-size: 0.9rem;'>{chord_span_text}</div>" if chord_span_text else ""}
        </div>
        """

    evidence_html += """
        </div>
    </div>
    """

    return evidence_html


def generate_chord_progression_display(envelope) -> str:
    """Generate enhanced chord progression display with music notation styling."""
    if not hasattr(envelope, "chord_symbols") or not envelope.chord_symbols:
        return ""

    primary = envelope.primary
    chord_symbols = envelope.chord_symbols
    romans = primary.roman_numerals if primary.roman_numerals else []

    # Ensure we have matching arrays
    max_length = max(len(chord_symbols), len(romans))
    chord_symbols_padded = chord_symbols + [""] * (max_length - len(chord_symbols))
    romans_padded = romans + [""] * (max_length - len(romans))

    html = """
    <div style='margin-top: 1.5rem;'>
        <div style='opacity: 0.9; font-size: 1rem; margin-bottom: 1rem; font-weight: 600; color: white;'>
            🎼 Chord Progression
        </div>
        <div style='background: rgba(255, 255, 255, 0.95); border-radius: 12px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
            <div style='display: flex; flex-wrap: wrap; gap: 1rem; justify-content: center; align-items: center;'>
    """

    for i, (chord, roman) in enumerate(zip(chord_symbols_padded, romans_padded)):
        if not chord:
            continue

        # Determine chord quality color
        chord_colors = {
            "major": "#22c55e",  # Green for major
            "minor": "#3b82f6",  # Blue for minor
            "diminished": "#ef4444",  # Red for diminished
            "augmented": "#f59e0b",  # Amber for augmented
            "dominant": "#8b5cf6",  # Purple for dominant
            "default": "#6b7280",  # Gray default
        }

        # Simple chord quality detection
        color = chord_colors["default"]
        if "m" in chord.lower() and "maj" not in chord.lower():
            color = chord_colors["minor"]
        elif any(x in chord for x in ["dim", "°"]):
            color = chord_colors["diminished"]
        elif any(x in chord for x in ["aug", "+"]):
            color = chord_colors["augmented"]
        elif (
            any(x in chord for x in ["7", "9", "11", "13"])
            and "maj" not in chord.lower()
        ):
            color = chord_colors["dominant"]
        else:
            color = chord_colors["major"]

        # Add progression arrow if not first chord
        if i > 0:
            html += """
            <div style='display: flex; align-items: center; color: #6b7280; font-size: 1.5rem; font-weight: 300;'>
                →
            </div>
            """

        html += f"""
        <div style='display: flex; flex-direction: column; align-items: center; min-width: 80px;
                    background: {color}; color: white; padding: 1rem; border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: transform 0.2s ease;'
             onmouseover='this.style.transform="scale(1.05)"'
             onmouseout='this.style.transform="scale(1)"'>
            <div style='font-size: 1.5rem; font-weight: 700; margin-bottom: 0.25rem; font-family: "Times New Roman", serif;'>
                {chord}
            </div>
            {f'<div style="font-size: 1rem; font-weight: 600; opacity: 0.9;">{roman}</div>' if roman else ''}
            <div style='font-size: 0.75rem; opacity: 0.8; margin-top: 0.25rem;'>
                Chord {i+1}
            </div>
        </div>
        """

    html += """
            </div>
        </div>
    </div>
    """

    return html


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
    """Format the analysis envelope as rich HTML with interactive glossary."""
    primary = envelope.primary

    # Include JavaScript for glossary modal functionality
    modal_js = """
    <script>
    function showGlossaryModal(term, label, tooltip) {
        // Create modal overlay
        const overlay = document.createElement('div');
        overlay.id = 'glossary-modal-overlay';
        overlay.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.5); z-index: 1000; display: flex;
            align-items: center; justify-content: center; cursor: pointer;
        `;

        // Create modal content
        const modal = document.createElement('div');
        modal.style.cssText = `
            background: white; padding: 2rem; border-radius: 12px;
            max-width: 500px; width: 90%; max-height: 80vh; overflow-y: auto;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            cursor: default;
        `;

        modal.innerHTML = `
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                <h3 style='margin: 0; color: #1f2937;'>📆 ${label}</h3>
                <button onclick='closeGlossaryModal()' style='background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #6b7280;'>&times;</button>
            </div>
            <div style='color: #374151; line-height: 1.6;'>
                <div style='background: #f9fafb; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
                    <strong>Term:</strong> ${term}
                </div>
                ${tooltip ? `<div><strong>Definition:</strong><br>${tooltip}</div>` : '<div><em>Loading definition...</em></div>'}
                <div style='margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 0.9rem;'>
                    💡 <strong>Tip:</strong> Click outside this modal to close
                </div>
            </div>
        `;

        // Close modal when clicking overlay
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeGlossaryModal();
        });

        // Prevent modal from closing when clicking inside
        modal.addEventListener('click', (e) => e.stopPropagation());

        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        // Focus trap for accessibility
        modal.focus();
    }

    function closeGlossaryModal() {
        const overlay = document.getElementById('glossary-modal-overlay');
        if (overlay) {
            overlay.remove();
        }
    }

    // Close modal with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeGlossaryModal();
    });
    </script>
    """

    # Main container with modern styling
    html = (
        modal_js
        + """
    <div style='font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #334155;'>
    """
    )

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

        # Scale Summary (NEW in iteration 14-a)
        if hasattr(primary, "scale_summary") and primary.scale_summary:
            scale_summary = primary.scale_summary
            html += f"""
            <div style='margin-bottom: 1rem;'>
                <div style='opacity: 0.8; font-size: 0.9rem; margin-bottom: 0.5rem;'>🎼 Scale Analysis</div>
                <div style='background: rgba(255,255,255,0.15); padding: 0.75rem; border-radius: 8px;'>
            """
            if scale_summary.detected_mode:
                html += (
                    f"<div><strong>Mode:</strong> {scale_summary.detected_mode}</div>"
                )
            if scale_summary.parent_key:
                html += f"<div><strong>Parent Key:</strong> {scale_summary.parent_key}</div>"
            if scale_summary.characteristic_notes:
                html += f"<div><strong>Characteristics:</strong> {', '.join(scale_summary.characteristic_notes)}</div>"
            if scale_summary.notes:
                html += f"<div><strong>Scale Notes:</strong> {' - '.join(scale_summary.notes)}</div>"
            html += "</div></div>"

        # Melody Summary (NEW in iteration 14-a)
        if hasattr(primary, "melody_summary") and primary.melody_summary:
            melody_summary = primary.melody_summary
            html += f"""
            <div style='margin-bottom: 1rem;'>
                <div style='opacity: 0.8; font-size: 0.9rem; margin-bottom: 0.5rem;'>🎵 Melody Analysis</div>
                <div style='background: rgba(255,255,255,0.15); padding: 0.75rem; border-radius: 8px;'>
            """
            if melody_summary.contour:
                html += f"<div><strong>Contour:</strong> {melody_summary.contour.title()}</div>"
            if melody_summary.range_semitones is not None:
                html += f"<div><strong>Range:</strong> {melody_summary.range_semitones} semitones</div>"
            if melody_summary.leading_tone_resolutions > 0:
                html += f"<div><strong>Leading Tone Resolutions:</strong> {melody_summary.leading_tone_resolutions}</div>"
            if melody_summary.melodic_characteristics:
                html += f"<div><strong>Characteristics:</strong> {', '.join(melody_summary.melodic_characteristics)}</div>"
            if melody_summary.chromatic_notes:
                html += f"<div><strong>Chromatic Notes:</strong> {', '.join(melody_summary.chromatic_notes)}</div>"
            html += "</div></div>"

    # Interactive Chord Progression Display (moved outside the primary section to be full-width)
    html += generate_chord_progression_display(envelope)

    # Back to white background for remaining sections
    html += """
    <div style='background: white; border: 2px solid #e5e7eb; padding: 1.25rem; border-radius: 12px; margin-top: 1.5rem;'>
    """

    # Continue with primary analysis content if needed
    if primary:
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

        # Interactive glossary terms
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

                # Create clickable glossary chip with modal trigger
                escaped_key = key.replace("'", "&#39;").replace('"', "&quot;")
                escaped_tooltip = (
                    tooltip.replace("'", "&#39;").replace('"', "&quot;")
                    if tooltip
                    else ""
                )

                html += f"""
                <span class='glossary-chip'
                      onclick='showGlossaryModal("{escaped_key}", "{label}", "{escaped_tooltip}")'
                      style='background: rgba(255,255,255,0.2); color: white; padding: 0.25rem 0.75rem; border-radius: 16px; font-size: 0.85rem; cursor: pointer; transition: all 0.2s ease; border: 1px solid rgba(255,255,255,0.3);'
                      onmouseover='this.style.background="rgba(255,255,255,0.3)"; this.style.transform="translateY(-1px)"'
                      onmouseout='this.style.background="rgba(255,255,255,0.2)"; this.style.transform="translateY(0)"'
                      title='Click for definition'>
                    {label} 📆
                </span>
                """
            html += "</div></div>"

    html += "</div>"  # End primary section

    # Alternatives section with enhanced details
    if envelope.alternatives:
        html += """
        <div style='background: #f1f5f9; border: 2px solid #e2e8f0; padding: 1.25rem; border-radius: 12px; margin-bottom: 1.5rem;'>
            <h3 style='margin: 0 0 1rem 0; color: #475569; display: flex; align-items: center;'>
                🔄 Alternative Interpretations
            </h3>
            <div style='display: grid; gap: 1rem;'>
        """

        for idx, alt in enumerate(envelope.alternatives, 1):
            # Create expandable alternative card with details
            alt_romans = (
                " - ".join(getattr(alt, "roman_numerals", []))
                if hasattr(alt, "roman_numerals") and alt.roman_numerals
                else "N/A"
            )
            alt_mode = getattr(alt, "mode", "N/A") or "N/A"
            alt_key = getattr(alt, "key_signature", "N/A") or "N/A"
            alt_reasoning = getattr(alt, "reasoning", "") or ""

            html += f"""
            <details style='background: white; border-radius: 8px; border-left: 3px solid #6366f1; overflow: hidden;'>
                <summary style='padding: 0.75rem 1rem; cursor: pointer; display: flex; justify-content: space-between; align-items: center; background: rgba(99, 102, 241, 0.05);'>
                    <span><strong>#{idx}</strong> {alt.type.value.title()}</span>
                    <span>{format_confidence_badge(alt.confidence)}</span>
                </summary>
                <div style='padding: 1rem; border-top: 1px solid #e5e7eb;'>
                    <div style='display: grid; gap: 0.5rem;'>
                        <div><strong>Key:</strong> {alt_key}</div>
                        <div><strong>Mode:</strong> {alt_mode}</div>
                        <div><strong>Roman Numerals:</strong> <code style='background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-family: monospace;'>{alt_romans}</code></div>
                        {f'<div><strong>Analysis:</strong> <em>{alt_reasoning}</em></div>' if alt_reasoning else ''}
                    </div>
                </div>
            </details>
            """

        html += "</div></div>"

    html += "</div>"  # End white background section for primary content

    # Enhanced Evidence section with rich cards
    html += generate_enhanced_evidence_cards(envelope)

    # Code snippet section
    if hasattr(envelope, "chord_symbols") and envelope.chord_symbols:
        # Extract analysis parameters for code generation
        chord_symbols = envelope.chord_symbols
        profile = "classical"  # Default, could be enhanced to detect from analysis
        key_hint = primary.key_signature if primary.key_signature else None

        async_code, sync_code, api_code = generate_code_snippet(
            chord_symbols, profile, key_hint, envelope
        )

        html += f"""
        <div style='margin-top: 1.5rem;'>
            <div style='opacity: 0.9; font-size: 1rem; margin-bottom: 1rem; font-weight: 600; color: white;'>
                💻 Code Examples
            </div>

            <!-- Code snippet tabs -->
            <div style='background: rgba(255, 255, 255, 0.95); border-radius: 12px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                <div style='display: flex; margin-bottom: 1rem; border-bottom: 2px solid #e5e7eb;'>
                    <button onclick='showCodeTab("async")' id='async-tab'
                            style='padding: 0.5rem 1rem; border: none; background: #4f46e5; color: white;
                                   border-radius: 8px 8px 0 0; cursor: pointer; font-weight: 600; margin-right: 2px;'>
                        Async
                    </button>
                    <button onclick='showCodeTab("sync")' id='sync-tab'
                            style='padding: 0.5rem 1rem; border: none; background: #e5e7eb; color: #374151;
                                   border-radius: 8px 8px 0 0; cursor: pointer; font-weight: 600; margin-right: 2px;'>
                        Sync
                    </button>
                    <button onclick='showCodeTab("api")' id='api-tab'
                            style='padding: 0.5rem 1rem; border: none; background: #e5e7eb; color: #374151;
                                   border-radius: 8px 8px 0 0; cursor: pointer; font-weight: 600;'>
                        API
                    </button>
                </div>

                <div id='async-code' style='display: block;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                        <h4 style='margin: 0; color: #374151;'>Async Python Code</h4>
                        <button onclick='copyCode("async")'
                                style='background: #4f46e5; color: white; border: none; padding: 0.25rem 0.75rem;
                                       border-radius: 6px; cursor: pointer; font-size: 0.85rem;'>
                            📋 Copy
                        </button>
                    </div>
                    <pre id='async-code-content' style='background: #f8fafc; padding: 1rem; border-radius: 8px;
                                                          overflow-x: auto; margin: 0; font-family: "SF Mono", Monaco, monospace;
                                                          font-size: 0.85rem; line-height: 1.4; color: #1e293b;'>{async_code}</pre>
                </div>

                <div id='sync-code' style='display: none;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                        <h4 style='margin: 0; color: #374151;'>Sync Python Code</h4>
                        <button onclick='copyCode("sync")'
                                style='background: #4f46e5; color: white; border: none; padding: 0.25rem 0.75rem;
                                       border-radius: 6px; cursor: pointer; font-size: 0.85rem;'>
                            📋 Copy
                        </button>
                    </div>
                    <pre id='sync-code-content' style='background: #f8fafc; padding: 1rem; border-radius: 8px;
                                                       overflow-x: auto; margin: 0; font-family: "SF Mono", Monaco, monospace;
                                                       font-size: 0.85rem; line-height: 1.4; color: #1e293b;'>{sync_code}</pre>
                </div>

                <div id='api-code' style='display: none;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                        <h4 style='margin: 0; color: #374151;'>API Integration</h4>
                        <button onclick='copyCode("api")'
                                style='background: #4f46e5; color: white; border: none; padding: 0.25rem 0.75rem;
                                       border-radius: 6px; cursor: pointer; font-size: 0.85rem;'>
                            📋 Copy
                        </button>
                    </div>
                    <pre id='api-code-content' style='background: #f8fafc; padding: 1rem; border-radius: 8px;
                                                      overflow-x: auto; margin: 0; font-family: "SF Mono", Monaco, monospace;
                                                      font-size: 0.85rem; line-height: 1.4; color: #1e293b;'>{api_code}</pre>
                </div>
            </div>
        </div>

        <script>
        function showCodeTab(tabName) {{
            // Hide all code sections
            document.getElementById('async-code').style.display = 'none';
            document.getElementById('sync-code').style.display = 'none';
            document.getElementById('api-code').style.display = 'none';

            // Reset all tab styles
            document.getElementById('async-tab').style.background = '#e5e7eb';
            document.getElementById('async-tab').style.color = '#374151';
            document.getElementById('sync-tab').style.background = '#e5e7eb';
            document.getElementById('sync-tab').style.color = '#374151';
            document.getElementById('api-tab').style.background = '#e5e7eb';
            document.getElementById('api-tab').style.color = '#374151';

            // Show selected tab
            document.getElementById(tabName + '-code').style.display = 'block';
            document.getElementById(tabName + '-tab').style.background = '#4f46e5';
            document.getElementById(tabName + '-tab').style.color = 'white';
        }}

        function copyCode(tabName) {{
            const codeElement = document.getElementById(tabName + '-code-content');
            const text = codeElement.textContent;

            if (navigator.clipboard) {{
                navigator.clipboard.writeText(text).then(function() {{
                    // Show success feedback
                    const button = event.target;
                    const originalText = button.textContent;
                    button.textContent = '✅ Copied!';
                    button.style.background = '#22c55e';
                    setTimeout(() => {{
                        button.textContent = originalText;
                        button.style.background = '#4f46e5';
                    }}, 2000);
                }});
            }} else {{
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);

                const button = event.target;
                const originalText = button.textContent;
                button.textContent = '✅ Copied!';
                setTimeout(() => {{
                    button.textContent = originalText;
                }}, 2000);
            }}
        }}
        </script>
        """

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

        # Scale Summary (NEW in iteration 14-a)
        if hasattr(primary, "scale_summary") and primary.scale_summary:
            scale_summary = primary.scale_summary
            lines.append("")
            lines.append("=== Scale Analysis ===")
            if scale_summary.detected_mode:
                lines.append(f"Mode           : {scale_summary.detected_mode}")
            if scale_summary.parent_key:
                lines.append(f"Parent Key     : {scale_summary.parent_key}")
            if scale_summary.characteristic_notes:
                lines.append(
                    f"Characteristics: {', '.join(scale_summary.characteristic_notes)}"
                )
            if scale_summary.notes:
                lines.append(f"Scale Notes    : {' - '.join(scale_summary.notes)}")
            if scale_summary.degrees:
                lines.append(
                    f"Degrees        : {', '.join(map(str, scale_summary.degrees))}"
                )

        # Melody Summary (NEW in iteration 14-a)
        if hasattr(primary, "melody_summary") and primary.melody_summary:
            melody_summary = primary.melody_summary
            lines.append("")
            lines.append("=== Melody Analysis ===")
            if melody_summary.contour:
                lines.append(f"Contour        : {melody_summary.contour.title()}")
            if melody_summary.range_semitones is not None:
                lines.append(
                    f"Range          : {melody_summary.range_semitones} semitones"
                )
            if melody_summary.intervals:
                intervals_str = ", ".join(
                    [f"{'+' if i > 0 else ''}{i}" for i in melody_summary.intervals]
                )
                lines.append(f"Intervals      : {intervals_str}")
            if melody_summary.leading_tone_resolutions > 0:
                lines.append(
                    f"Leading Tones  : {melody_summary.leading_tone_resolutions} resolutions"
                )
            if melody_summary.melodic_characteristics:
                lines.append(
                    f"Characteristics: {', '.join(melody_summary.melodic_characteristics)}"
                )
            if melody_summary.chromatic_notes:
                lines.append(
                    f"Chromatic Notes: {', '.join(melody_summary.chromatic_notes)}"
                )

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
        try:
            result_dict = envelope.to_dict()
            lines.append(json.dumps(result_dict, indent=2, default=str))
        except Exception as e:
            lines.append(f"Raw envelope serialization error: {e}")
            lines.append(f"Envelope type: {type(envelope)}")
            lines.append("Available envelope attributes:")
            for attr in dir(envelope):
                if not attr.startswith("_"):
                    lines.append(f"  - {attr}: {type(getattr(envelope, attr, None))}")

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


async def run_analysis_async(
    chord_symbols: List[str], profile: str, key_hint: Optional[str]
):
    service = get_service()
    return await service.analyze_with_patterns_async(
        chord_symbols=chord_symbols, profile=profile, key_hint=key_hint
    )


def run_analysis_sync(chord_symbols: List[str], profile: str, key_hint: Optional[str]):
    """Synchronous wrapper for CLI usage."""
    return asyncio.run(run_analysis_async(chord_symbols, profile, key_hint))


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
                    chords=request.chords,
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


def launch_gradio_demo(default_key: Optional[str], default_profile: str) -> None:
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

            # For now, prioritize chord analysis with new service
            if chords and chords.strip():
                chord_list = validate_list("chord", parse_csv(chords))
                envelope = run_analysis_sync(chord_list, profile, normalized_key)
                html_output = format_analysis_html(envelope)
                return html_output

            # Fall back to legacy pattern for other analysis types
            context = analyze_progression(
                key=normalized_key,
                profile=profile,
                chords_text=chords,
                romans_text=romans,
                melody_text=melody,
                scales_input=scales,
            )
            # For legacy analysis, we need to handle it differently
            # This is a placeholder - will be fully implemented in next phase
            return """
            <div style='background: #fef2f2; border: 2px solid #f87171; border-radius: 12px; padding: 1.5rem; color: #991b1b; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);'>
                <div style='display: flex; align-items: center; margin-bottom: 1rem;'>
                    <span style='font-size: 1.5rem; margin-right: 0.75rem; color: #dc2626;'>⚠️</span>
                    <strong style='color: #991b1b; font-weight: 700; font-size: 1.2rem;'>Analysis Type Not Yet Supported</strong>
                </div>
                <div style='margin-bottom: 1rem;'>
                    <p style='margin: 0; color: #7f1d1d; font-weight: 500; line-height: 1.6;'>
                        Roman numeral, melody, and scale analysis are not yet migrated to the new service.
                    </p>
                </div>
                <div style='background: rgba(255, 255, 255, 0.9); padding: 1rem; border-radius: 8px; border-left: 4px solid #4f46e5;'>
                    <strong style='color: #4f46e5; font-weight: 600;'>💡 Try using chord symbols instead:</strong>
                    <div style='margin-top: 0.5rem; font-family: "SF Mono", Monaco, monospace; background: #f8fafc; padding: 0.5rem; border-radius: 4px; color: #1e293b;'>
                        Chords: Am Dm G C<br>
                        Key: C major
                    </div>
                </div>
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

        search_btn.click(
            search_glossary_term, inputs=[glossary_search], outputs=[glossary_output]
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
                    chords=chords, profile=args.profile, key_hint=key_hint
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
