#!/usr/bin/env python3
"""Interactive demo for the unified harmonic-analysis pattern engine."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import sys
import warnings
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

# Roman numeral and note validation (library doesn't own these yet)
ROMAN_RE = re.compile(r"^[ivIV]+(?:[#b♯♭]?[ivIV]+)?(?:[°ø+]?)(?:\d+)?$")
NOTE_RE = re.compile(r"^[A-Ga-g](?:#|b)?(?:\d+)?$")


# ============================================================================
# Chord Detection Helper (comprehensive from legacy chord_parser.py)
# ============================================================================

NOTE_NAMES_FOR_DETECTION = [
    "C",
    "C#",
    "D",
    "Eb",
    "E",
    "F",
    "F#",
    "G",
    "Ab",
    "A",
    "Bb",
    "B",
]

# Comprehensive chord templates (from legacy chord_parser.py)
CHORD_TEMPLATES = {
    # Basic triads
    "major": {"intervals": [0, 4, 7], "symbol": "", "min_notes": 3, "confidence": 1.0},
    "minor": {"intervals": [0, 3, 7], "symbol": "m", "min_notes": 3, "confidence": 1.0},
    "diminished": {
        "intervals": [0, 3, 6],
        "symbol": "dim",
        "min_notes": 3,
        "confidence": 1.0,
    },
    "augmented": {
        "intervals": [0, 4, 8],
        "symbol": "aug",
        "min_notes": 3,
        "confidence": 1.0,
    },
    # Suspended chords (complete)
    "sus2": {
        "intervals": [0, 2, 7],
        "symbol": "sus2",
        "min_notes": 3,
        "confidence": 1.0,
    },
    "sus4": {
        "intervals": [0, 5, 7],
        "symbol": "sus4",
        "min_notes": 3,
        "confidence": 1.0,
    },
    # Partial suspended chords (2-note combinations)
    "sus2Partial": {
        "intervals": [0, 2],
        "symbol": "sus2(no5)",
        "min_notes": 2,
        "confidence": 0.75,
    },
    "sus4Partial": {
        "intervals": [0, 5],
        "symbol": "sus4(no5)",
        "min_notes": 2,
        "confidence": 0.75,
    },
    # Partial triads (2-note combinations)
    "majorPartial": {
        "intervals": [0, 4],
        "symbol": "(no5)",
        "min_notes": 2,
        "confidence": 0.70,
    },
    "minorPartial": {
        "intervals": [0, 3],
        "symbol": "m(no5)",
        "min_notes": 2,
        "confidence": 0.70,
    },
    "fifthPartial": {
        "intervals": [0, 7],
        "symbol": "5",
        "min_notes": 2,
        "confidence": 0.85,
    },
    # Partial seventh chords (3-note combinations missing one tone)
    "dom7NoFifth": {
        "intervals": [0, 4, 10],
        "symbol": "7(no5)",
        "min_notes": 3,
        "confidence": 0.80,
    },
    "min7NoFifth": {
        "intervals": [0, 3, 10],
        "symbol": "m7(no5)",
        "min_notes": 3,
        "confidence": 0.80,
    },
    "maj7NoFifth": {
        "intervals": [0, 4, 11],
        "symbol": "maj7(no5)",
        "min_notes": 3,
        "confidence": 0.80,
    },
    # Incomplete sus chords with extensions
    "sus2Add7": {
        "intervals": [0, 2, 10],
        "symbol": "sus2(add7)",
        "min_notes": 3,
        "confidence": 0.75,
    },
    "sus4Add7": {
        "intervals": [0, 5, 10],
        "symbol": "sus4(add7)",
        "min_notes": 3,
        "confidence": 0.75,
    },
    # Add chords (retaining 3rd + added note)
    "majorAdd4": {
        "intervals": [0, 4, 5],
        "symbol": "add4",
        "min_notes": 3,
        "confidence": 0.85,
    },
    "minorAdd4": {
        "intervals": [0, 3, 5],
        "symbol": "madd4",
        "min_notes": 3,
        "confidence": 0.85,
    },
    # Seventh chords (4-note combinations)
    "major7": {
        "intervals": [0, 4, 7, 11],
        "symbol": "maj7",
        "min_notes": 4,
        "confidence": 1.0,
    },
    "minor7": {
        "intervals": [0, 3, 7, 10],
        "symbol": "m7",
        "min_notes": 4,
        "confidence": 1.0,
    },
    "dominant7": {
        "intervals": [0, 4, 7, 10],
        "symbol": "7",
        "min_notes": 4,
        "confidence": 1.0,
    },
    "diminished7": {
        "intervals": [0, 3, 6, 9],
        "symbol": "dim7",
        "min_notes": 4,
        "confidence": 1.0,
    },
    "halfDiminished7": {
        "intervals": [0, 3, 6, 10],
        "symbol": "m7b5",
        "min_notes": 4,
        "confidence": 1.0,
    },
    "augmented7": {
        "intervals": [0, 4, 8, 10],
        "symbol": "aug7",
        "min_notes": 4,
        "confidence": 1.0,
    },
    "minorMaj7": {
        "intervals": [0, 3, 7, 11],
        "symbol": "m(maj7)",
        "min_notes": 4,
        "confidence": 1.0,
    },
    # Extended chords with 4th (sus4 with extra notes)
    "sus4With3rd": {
        "intervals": [0, 4, 5, 7],
        "symbol": "sus4",
        "min_notes": 4,
        "confidence": 0.90,
    },
}


def detect_chord_from_pitches(pitches: List[int]) -> str:
    """
    Detect chord symbol from MIDI pitches with comprehensive chord recognition.

    Full chord detection logic from legacy src/harmonic_analysis/utils/chord_parser.py
    Supports complex chords including sus4, add4, 7ths, and partial chords.

    Args:
        pitches: List of MIDI note numbers

    Returns:
        Chord symbol string with slash notation for inversions (e.g., "Asus4/C#", "Cadd4/E")
    """
    if len(pitches) < 2:
        return "Unknown"

    # Find the lowest MIDI note (bass note)
    lowest_midi = min(pitches)
    bass_note = lowest_midi % 12

    # Convert to pitch classes and remove duplicates
    pitch_classes = list(set(p % 12 for p in pitches))
    pitch_classes.sort()

    # Try each pitch class as potential root
    best_match = None
    best_root = None
    best_confidence = 0.0

    for root in pitch_classes:
        # Calculate intervals from this root
        intervals = [(p - root) % 12 for p in pitch_classes]
        intervals.sort()

        # Check against each chord template
        for chord_type, template in CHORD_TEMPLATES.items():
            template_intervals = template["intervals"]
            min_notes = template["min_notes"]

            # Skip if we don't have enough notes
            if len(pitches) < min_notes:
                continue

            # Check if all template intervals are present
            if all(interval in intervals for interval in template_intervals):
                # Calculate confidence
                confidence = _calculate_confidence(
                    intervals, template_intervals, len(pitches), template["confidence"]
                )

                if confidence > best_confidence:
                    best_confidence = confidence
                    root_name = NOTE_NAMES_FOR_DETECTION[root]
                    best_root = root
                    best_match = f"{root_name}{template['symbol']}"

    if not best_match:
        return "Unknown"

    # Check for inversion - add slash notation if bass != root
    if bass_note != best_root:
        bass_name = NOTE_NAMES_FOR_DETECTION[bass_note]
        best_match = f"{best_match}/{bass_name}"

    return best_match


def _calculate_confidence(
    played_intervals: List[int],
    template_intervals: List[int],
    note_count: int,
    base_confidence: float,
) -> float:
    """Calculate confidence score for chord match."""
    total_template_notes = len(template_intervals)
    extra_notes = len(played_intervals) - total_template_notes

    # Start with base confidence
    confidence = base_confidence

    # Penalize for extra notes
    if extra_notes > 0:
        confidence -= extra_notes * 0.08

    # Bonus for exact match
    if len(played_intervals) == total_template_notes:
        confidence += 0.1

    # Clamp between 0 and 1
    return max(0.0, min(1.0, confidence))


def detect_chord_with_music21(chord_element) -> str:
    """
    Use music21's sophisticated chord detection to identify complex chords.

    music21 has extensive chord analysis capabilities including:
    - Quality detection (major, minor, diminished, augmented)
    - Seventh chord detection
    - Suspended chord detection
    - Add chord detection
    - Inversion notation

    Args:
        chord_element: music21.chord.Chord object

    Returns:
        Chord symbol string (e.g., "Asus4/C#", "Cadd4", "Dm7b5")
    """
    try:
        # Get root and bass notes
        root = chord_element.root()
        bass = chord_element.bass()
        root_name = root.name

        # Get pitch classes for interval analysis
        pitches = sorted([p.midi % 12 for p in chord_element.pitches])
        root_pc = root.pitchClass
        intervals = sorted([(p - root_pc) % 12 for p in pitches])

        # Determine chord quality using music21's built-in detection
        quality = ""

        # Check for suspended chords first (no 3rd)
        has_third = any(interval in [3, 4] for interval in intervals)
        has_fourth = 5 in intervals
        has_second = 2 in intervals
        has_fifth = 7 in intervals

        if not has_third:
            if has_fourth and has_fifth:
                quality = "sus4"
            elif has_second and has_fifth:
                quality = "sus2"
            elif has_fourth:
                quality = "sus4(no5)"
            elif has_second:
                quality = "sus2(no5)"
            elif has_fifth:
                quality = "5"  # Power chord

        # If we have a third, check for standard qualities
        if quality == "":
            if chord_element.isMinorTriad():
                quality = "m"
            elif chord_element.isMajorTriad():
                quality = ""  # Major is default
            elif chord_element.isDiminishedTriad():
                quality = "dim"
            elif chord_element.isAugmentedTriad():
                quality = "aug"

            # Check for seventh chords
            if chord_element.seventh is not None:
                if chord_element.isDominantSeventh():
                    quality = "7"
                elif chord_element.isMajorSeventh():
                    quality = "maj7"
                elif chord_element.isMinorSeventh():
                    quality = "m7"
                elif chord_element.isDiminishedSeventh():
                    quality = "dim7"
                elif chord_element.isHalfDiminishedSeventh():
                    quality = "m7b5"

        # Check for add chords (has 3rd + 4th)
        if has_third and has_fourth and quality in ["", "m"]:
            if quality == "m":
                quality = "madd4"
            else:
                quality = "add4"

        # Build chord symbol
        chord_symbol = f"{root_name}{quality}"

        # Add inversion notation if bass != root
        if bass.pitchClass != root.pitchClass:
            bass_name = bass.name
            chord_symbol = f"{chord_symbol}/{bass_name}"

        return chord_symbol

    except Exception as e:
        # Fallback to basic pitchedCommonName
        try:
            return chord_element.pitchedCommonName
        except:
            return "Unknown"


def generate_osmd_html_file(musicxml_path: str) -> str:
    """Generate standalone HTML file with OSMD viewer.

    Args:
        musicxml_path: Path to MusicXML file to display

    Returns:
        Path to generated HTML file
    """
    import base64
    import os
    import tempfile

    # Read the MusicXML file content
    try:
        with open(musicxml_path, "rb") as f:
            xml_content = f.read()
        xml_base64 = base64.b64encode(xml_content).decode("utf-8")
        print(f"DEBUG: Encoded MusicXML ({len(xml_content)} bytes) for OSMD")
    except Exception as e:
        print(f"ERROR: Failed to read MusicXML: {e}")
        # Return a simple error HTML file
        error_html = f"""<!DOCTYPE html>
<html><body><p style='color: red; padding: 20px;'>Error loading MusicXML: {e}</p></body></html>"""
        error_path = os.path.join(tempfile.gettempdir(), "osmd_error.html")
        with open(error_path, "w") as f:
            f.write(error_html)
        return error_path

    # Generate complete standalone HTML file
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Music Notation</title>
    <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.8.6/build/opensheetmusicdisplay.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background: white;
        }}
        #controls {{
            margin-bottom: 15px;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 4px;
        }}
        button {{
            margin-right: 8px;
            padding: 8px 15px;
            border: 1px solid #ccc;
            background: white;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}
        button:hover {{
            background: #e9e9e9;
        }}
        #osmd-container {{
            overflow: auto;
            max-height: 90vh;
        }}
        #status {{
            margin: 10px 0;
            padding: 10px;
            background: #e3f2fd;
            border-radius: 4px;
            display: none;
        }}
        .error {{
            background: #ffebee !important;
            color: #c62828;
        }}
    </style>
</head>
<body>
    <div id="controls">
        <button onclick="zoomIn()">🔍 Zoom In</button>
        <button onclick="zoomOut()">🔎 Zoom Out</button>
        <button onclick="resetZoom()">↺ Reset</button>
        <span style="margin-left: 20px; color: #666;">Scroll to see all measures</span>
    </div>

    <div id="status">Loading notation...</div>
    <div id="osmd-container"></div>

    <script>
        const statusDiv = document.getElementById('status');

        function showStatus(message, isError) {{
            statusDiv.textContent = message;
            statusDiv.style.display = 'block';
            if (isError) {{
                statusDiv.classList.add('error');
            }} else {{
                statusDiv.classList.remove('error');
            }}
        }}

        showStatus('Initializing OSMD...', false);

        // Wait for OSMD to load
        let retryCount = 0;
        function initOSMD() {{
            if (typeof opensheetmusicdisplay === 'undefined') {{
                retryCount++;
                if (retryCount < 20) {{
                    setTimeout(initOSMD, 500);
                    return;
                }}
                showStatus('Failed to load OSMD library from CDN', true);
                return;
            }}

            try {{
                // Decode MusicXML
                const xmlBase64 = "{xml_base64}";
                const xmlString = atob(xmlBase64);

                showStatus('Rendering notation... (this may take a moment for large files)', false);

                // Set a timeout to catch hangs
                let renderTimeout = setTimeout(() => {{
                    showStatus('Rendering is taking longer than expected. The file may be too complex for browser rendering.', true);
                }}, 10000); // 10 second timeout

                // Initialize OSMD
                const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("osmd-container", {{
                    autoResize: true,
                    backend: "svg",
                    drawTitle: true,
                    drawPartNames: true,
                    drawLyrics: true,
                    drawMeasureNumbers: true,
                    drawTimeSignatures: true,
                    drawKeySignatures: true,
                    pageFormat: "Endless",
                }});

                // Load and render
                osmd.load(xmlString).then(() => {{
                    clearTimeout(renderTimeout);
                    console.log("OSMD: Loaded, now rendering...");
                    return osmd.render();
                }}).then(() => {{
                    clearTimeout(renderTimeout);
                    statusDiv.style.display = 'none';
                    console.log("OSMD: Rendered successfully");
                }}).catch((error) => {{
                    clearTimeout(renderTimeout);
                    showStatus('Error rendering music: ' + error.message + ' - Try downloading the MusicXML file instead.', true);
                    console.error("OSMD Error:", error);
                    console.error("Error stack:", error.stack);
                }});

                // Zoom controls
                let currentZoom = 1.0;
                window.zoomIn = function() {{
                    currentZoom = Math.min(currentZoom + 0.1, 2.0);
                    osmd.zoom = currentZoom;
                    osmd.render();
                }};
                window.zoomOut = function() {{
                    currentZoom = Math.max(currentZoom - 0.1, 0.5);
                    osmd.zoom = currentZoom;
                    osmd.render();
                }};
                window.resetZoom = function() {{
                    currentZoom = 1.0;
                    osmd.zoom = currentZoom;
                    osmd.render();
                }};
            }} catch (error) {{
                showStatus('Error initializing OSMD: ' + error.message, true);
                console.error("Init error:", error);
            }}
        }}

        // Start initialization after page load
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', initOSMD);
        }} else {{
            initOSMD();
        }}
    </script>
</body>
</html>"""

    # Save to temporary file
    html_path = os.path.join(
        tempfile.gettempdir(), f"osmd_viewer_{os.path.basename(musicxml_path)}.html"
    )
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return html_path


def generate_osmd_viewer(musicxml_path: str) -> str:
    """Generate HTML for OpenSheetMusicDisplay viewer.

    Args:
        musicxml_path: Path to MusicXML file to display

    Returns:
        HTML string with embedded OSMD viewer
    """
    # Read the MusicXML file content
    import base64
    import uuid

    # Generate unique IDs for this instance
    viewer_id = f"osmd-viewer-{uuid.uuid4().hex[:8]}"
    notation_id = f"osmd-notation-{uuid.uuid4().hex[:8]}"

    try:
        with open(musicxml_path, "rb") as f:
            xml_content = f.read()
        xml_base64 = base64.b64encode(xml_content).decode("utf-8")
        print(
            f"DEBUG: Successfully encoded MusicXML ({len(xml_content)} bytes) for OSMD viewer"
        )
    except Exception as e:
        error_msg = f"Error loading MusicXML from {musicxml_path}: {e}"
        print(f"ERROR: {error_msg}")
        return f"<p style='color: red; padding: 20px;'>{error_msg}</p>"

    # Generate HTML with OSMD viewer using unique IDs
    html = f"""
    <div id="{viewer_id}" style="width: 100%; height: 600px; overflow: auto; border: 1px solid #ccc; border-radius: 8px; background: white; padding: 20px;">
        <div style="margin-bottom: 10px; padding: 10px; background: #f5f5f5; border-radius: 4px;">
            <button onclick="window.osmdZoomIn_{viewer_id}()" style="margin-right: 5px; padding: 5px 10px;">🔍 Zoom In</button>
            <button onclick="window.osmdZoomOut_{viewer_id}()" style="margin-right: 5px; padding: 5px 10px;">🔎 Zoom Out</button>
            <button onclick="window.osmdReset_{viewer_id}()" style="padding: 5px 10px;">↺ Reset</button>
            <span style="margin-left: 20px; color: #666;">Scroll to see all measures</span>
        </div>
        <div id="{notation_id}" style="min-height: 400px;"></div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.8.6/build/opensheetmusicdisplay.min.js"></script>
    <script>
    (function() {{
        console.log("OSMD: Script started for viewer {viewer_id}");

        // Retry logic to wait for OSMD library to load
        let retries = 0;
        const maxRetries = 20;

        function initOSMD() {{
            retries++;

            if (typeof opensheetmusicdisplay === 'undefined') {{
                if (retries < maxRetries) {{
                    console.log("OSMD: Waiting for library to load... (attempt " + retries + "/" + maxRetries + ")");
                    setTimeout(initOSMD, 500);
                    return;
                }} else {{
                    console.error("OSMD: Library failed to load after " + maxRetries + " attempts");
                    document.getElementById("{notation_id}").innerHTML =
                        "<p style='color: red; padding: 20px;'>Error: OSMD library failed to load from CDN</p>";
                    return;
                }}
            }}

            console.log("OSMD: Library loaded, initializing viewer {viewer_id}");

        try {{
            // Decode base64 MusicXML
            const xmlBase64 = "{xml_base64}";
            const xmlString = atob(xmlBase64);
            console.log("OSMD: Decoded MusicXML, length:", xmlString.length);

            // Initialize OSMD
            const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("{notation_id}", {{
                autoResize: true,
                backend: "svg",
                drawTitle: true,
                drawSubtitle: false,
                drawComposer: false,
                drawCredits: false,
                drawPartNames: true,
                drawFingerings: true,
                drawLyrics: true,
                drawSlurs: true,
                drawMeasureNumbers: true,
                drawTimeSignatures: true,
                drawKeySignatures: true,
                pageFormat: "Endless",
            }});

            // Load and render
            osmd.load(xmlString).then(() => {{
                osmd.render();
                console.log("OSMD: Sheet music rendered successfully for {viewer_id}");
            }}).catch((error) => {{
                console.error("OSMD Error:", error);
                document.getElementById("{notation_id}").innerHTML =
                    "<p style='color: red; padding: 20px;'>Error rendering music: " + error.message + "</p>";
            }});

            // Zoom controls (attached to window for button access)
            let currentZoom = 1.0;
            window.osmdZoomIn_{viewer_id} = function() {{
                currentZoom = Math.min(currentZoom + 0.1, 2.0);
                osmd.zoom = currentZoom;
                osmd.render();
            }};
            window.osmdZoomOut_{viewer_id} = function() {{
                currentZoom = Math.max(currentZoom - 0.1, 0.5);
                osmd.zoom = currentZoom;
                osmd.render();
            }};
            window.osmdReset_{viewer_id} = function() {{
                currentZoom = 1.0;
                osmd.zoom = currentZoom;
                osmd.render();
            }};
        }} catch (error) {{
            console.error("OSMD: Initialization error:", error);
            document.getElementById("{notation_id}").innerHTML =
                "<p style='color: red; padding: 20px;'>Error initializing OSMD: " + error.message + "</p>";
        }}
        }}

        // Start initialization
        initOSMD();
    }})();
    </script>
    """
    return html


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

    # Opening move: use library's parsers for validation when available
    if kind == "chord":
        # Chord validation uses the library's ChordParser
        from harmonic_analysis.core.utils.chord_logic import ChordParser

        parser = ChordParser()
        invalid = []
        for item in items:
            try:
                parser.parse_chord(item)
            except ValueError:
                invalid.append(item)
        if invalid:
            raise ValueError(f"Invalid {kind} entries: {', '.join(invalid)}")
        return items
    else:
        # Roman numerals and notes still use regex (library doesn't own these)
        validator = {
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


def format_file_analysis_html(
    analysis_result, chord_data: list, key_hint: str = None
) -> str:
    """
    Format harmonic analysis results for uploaded files with structured, measure-aware display.

    Connects roman numerals to actual chord symbols in a readable table format.

    Args:
        analysis_result: Analysis results dict from PatternAnalysisService
        chord_data: List of dicts with 'measure', 'chord', 'offset' keys, or list of chord strings (backward compat)
        key_hint: Optional key signature hint from file
    """
    primary = analysis_result.get("primary", {})

    # Extract key information
    key = primary.get("key_signature") or primary.get("key") or key_hint or "Unknown"
    mode = primary.get("mode", "")
    confidence = primary.get("confidence", 0)
    analysis_type = primary.get("type", "Unknown")
    roman_numerals = primary.get("roman_numerals", [])
    reasoning = primary.get("reasoning", "")

    # Handle both new format (list of dicts) and old format (list of strings)
    if chord_data and isinstance(chord_data[0], dict):
        has_measures = True
    else:
        has_measures = False
        # Convert old format to new format
        chord_data = [
            {"measure": i + 1, "chord": c, "offset": None}
            for i, c in enumerate(chord_data)
        ]

    # Build HTML with modern styling
    html = f"""
    <div style='font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; border-radius: 12px; padding: 1.5rem;'>

        <!-- Header Section -->
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.25rem; border-radius: 8px; margin-bottom: 1.5rem;'>
            <h3 style='margin: 0 0 0.75rem 0; font-size: 1.4rem;'>🎵 Harmonic Analysis Results</h3>
            <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; font-size: 0.95rem;'>
                <div>
                    <div style='opacity: 0.85; margin-bottom: 0.25rem;'>Analysis Type</div>
                    <div style='font-weight: 600;'>{analysis_type}</div>
                </div>
                <div>
                    <div style='opacity: 0.85; margin-bottom: 0.25rem;'>Key</div>
                    <div style='font-weight: 600;'>{key} {mode if mode else ''}</div>
                </div>
                <div>
                    <div style='opacity: 0.85; margin-bottom: 0.25rem;'>Confidence</div>
                    <div style='font-weight: 600;'>{confidence:.1%}</div>
                </div>
                <div>
                    <div style='opacity: 0.85; margin-bottom: 0.25rem;'>Total Chords</div>
                    <div style='font-weight: 600;'>{len(chord_data)}</div>
                </div>
            </div>
        </div>

        <!-- Chord Analysis Table -->
        <div style='background: white; border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>
            <h4 style='margin: 0 0 1rem 0; color: #334155; font-size: 1.1rem;'>📊 Chord-by-Chord Analysis</h4>
            <div style='overflow-x: auto;'>
                <table style='width: 100%; border-collapse: collapse; font-size: 0.95rem;'>
                    <thead>
                        <tr style='background: #f1f5f9; border-bottom: 2px solid #cbd5e1;'>
                            <th style='padding: 0.75rem; text-align: left; font-weight: 600; color: #475569;'>#</th>
                            <th style='padding: 0.75rem; text-align: left; font-weight: 600; color: #475569;'>Measure</th>
                            <th style='padding: 0.75rem; text-align: left; font-weight: 600; color: #475569;'>Chord Symbol</th>
                            <th style='padding: 0.75rem; text-align: left; font-weight: 600; color: #475569;'>Roman Numeral</th>
                            <th style='padding: 0.75rem; text-align: left; font-weight: 600; color: #475569;'>Function in {key}</th>
                        </tr>
                    </thead>
                    <tbody>
    """

    # Create rows connecting chord symbols to roman numerals
    for i, (chord_info, roman) in enumerate(zip(chord_data, roman_numerals), 1):
        chord_symbol = chord_info["chord"]
        measure_num = chord_info["measure"]

        # Determine function/description based on roman numeral
        function = get_chord_function_description(roman, key)

        # Alternate row colors
        row_bg = "#ffffff" if i % 2 == 0 else "#f8fafc"

        html += f"""
                        <tr style='background: {row_bg}; border-bottom: 1px solid #e2e8f0;'>
                            <td style='padding: 0.75rem; color: #64748b;'>{i}</td>
                            <td style='padding: 0.75rem; font-weight: 500; color: #7c3aed;'>{measure_num}</td>
                            <td style='padding: 0.75rem; font-weight: 500; color: #1e293b; font-family: "SF Mono", Monaco, monospace;'>{chord_symbol}</td>
                            <td style='padding: 0.75rem; font-weight: 600; color: #667eea; font-family: "SF Mono", Monaco, monospace;'>{roman}</td>
                            <td style='padding: 0.75rem; color: #475569;'>{function}</td>
                        </tr>
        """

    html += """
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Analysis Reasoning -->
        <details style='background: white; border-radius: 8px; padding: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>
            <summary style='cursor: pointer; font-weight: 600; color: #334155; user-select: none;'>
                🔍 Detailed Analysis Reasoning
            </summary>
            <div style='margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; color: #475569; line-height: 1.7;'>
    """

    # Format reasoning with better line breaks
    if reasoning:
        # Split on common delimiters and add structure
        reasoning_parts = reasoning.replace(";", ";<br>").replace(". ", ".<br>")
        html += f"<div style='white-space: pre-wrap;'>{reasoning_parts}</div>"
    else:
        html += "<em>No detailed reasoning available.</em>"

    html += """
            </div>
        </details>

    </div>
    """

    return html


def convert_key_signature_to_mode(
    key_signature_sharps_flats: int, prefer_minor: bool = False
) -> str:
    """
    Convert a key signature (number of sharps/flats) to a specific major or minor key.

    Args:
        key_signature_sharps_flats: Number of sharps (positive) or flats (negative)
        prefer_minor: If True, return relative minor; if False, return major

    Returns:
        Key name like "D major" or "B minor"

    Examples:
        convert_key_signature_to_mode(2, False) -> "D major"
        convert_key_signature_to_mode(2, True) -> "B minor"
        convert_key_signature_to_mode(-2, False) -> "Bb major"
        convert_key_signature_to_mode(-2, True) -> "G minor"
    """
    # Major keys by sharps/flats
    major_keys = {
        -7: "Cb",
        -6: "Gb",
        -5: "Db",
        -4: "Ab",
        -3: "Eb",
        -2: "Bb",
        -1: "F",
        0: "C",
        1: "G",
        2: "D",
        3: "A",
        4: "E",
        5: "B",
        6: "F#",
        7: "C#",
    }

    # Relative minor keys (3 semitones below major)
    minor_keys = {
        -7: "Ab",
        -6: "Eb",
        -5: "Bb",
        -4: "F",
        -3: "C",
        -2: "G",
        -1: "D",
        0: "A",
        1: "E",
        2: "B",
        3: "F#",
        4: "C#",
        5: "G#",
        6: "D#",
        7: "A#",
    }

    if key_signature_sharps_flats not in major_keys:
        # Unknown key signature, default to C major or A minor
        return "A minor" if prefer_minor else "C major"

    if prefer_minor:
        return f"{minor_keys[key_signature_sharps_flats]} minor"
    else:
        return f"{major_keys[key_signature_sharps_flats]} major"


def parse_key_signature_from_hint(key_hint: str) -> int:
    """
    Parse a key hint string to extract number of sharps/flats.

    Args:
        key_hint: String like "D major", "B minor", "2 sharps", etc.

    Returns:
        Number of sharps (positive) or flats (negative)
    """
    if not key_hint:
        return 0

    key_hint_lower = key_hint.lower()

    # Check for explicit sharp/flat count
    if "sharp" in key_hint_lower:
        try:
            count = int("".join(filter(str.isdigit, key_hint)))
            return count
        except ValueError:
            pass
    elif "flat" in key_hint_lower:
        try:
            count = int("".join(filter(str.isdigit, key_hint)))
            return -count
        except ValueError:
            pass

    # Map key names to sharps/flats (major keys)
    major_key_map = {
        "c": 0,
        "g": 1,
        "d": 2,
        "a": 3,
        "e": 4,
        "b": 5,
        "f#": 6,
        "c#": 7,
        "f": -1,
        "bb": -2,
        "eb": -3,
        "ab": -4,
        "db": -5,
        "gb": -6,
        "cb": -7,
    }

    # Map key names to sharps/flats (minor keys - same as relative major)
    minor_key_map = {
        "a": 0,
        "e": 1,
        "b": 2,
        "f#": 3,
        "c#": 4,
        "g#": 5,
        "d#": 6,
        "a#": 7,
        "d": -1,
        "g": -2,
        "c": -3,
        "f": -4,
        "bb": -5,
        "eb": -6,
        "ab": -7,
    }

    # Extract key name
    for key_name in major_key_map.keys():
        if key_name in key_hint_lower and "major" in key_hint_lower:
            return major_key_map[key_name]

    for key_name in minor_key_map.keys():
        if key_name in key_hint_lower and "minor" in key_hint_lower:
            return minor_key_map[key_name]

    # Default: no sharps or flats
    return 0


def get_chord_function_description(roman: str, key: str) -> str:
    """Provide a brief functional description for a roman numeral."""
    # Simple heuristics for common functions
    if roman.upper().startswith("I") and not roman.upper().startswith("II"):
        if roman == "I":
            return "Tonic (home)"
        return "Tonic variant"
    elif roman.upper().startswith("V"):
        if "7" in roman:
            return "Dominant 7th (tension)"
        return "Dominant (leading to tonic)"
    elif roman.upper().startswith("IV"):
        return "Subdominant (pre-dominant)"
    elif roman.upper().startswith("II"):
        return "Supertonic (pre-dominant)"
    elif roman.upper().startswith("VI"):
        return "Submediant (relative minor)" if roman.startswith("vi") else "Submediant"
    elif roman.upper().startswith("III"):
        return "Mediant"
    elif roman.upper().startswith("VII"):
        if "dim" in roman.lower() or "°" in roman:
            return "Leading tone diminished"
        return "Leading tone"
    else:
        return "—"


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
        # Reasoning with integrated glossary terms
        if primary.reasoning:
            html += f"""
            <div style='margin-bottom: 1rem;'>
                <div style='opacity: 0.8; font-size: 0.9rem; margin-bottom: 0.5rem;'>Analysis Reasoning</div>
                <div style='background: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 8px; font-style: italic;'>
                    {primary.reasoning}
                </div>
            """

            # Add glossary terms right after reasoning if available
            if primary.terms:
                html += """
                <div style='margin-top: 0.75rem;'>
                    <div style='opacity: 0.8; font-size: 0.85rem; margin-bottom: 0.4rem;'>📚 Terms</div>
                    <div style='display: flex; flex-wrap: wrap; gap: 0.4rem;'>
                """

                for key, value in primary.terms.items():
                    if isinstance(value, dict):
                        label = value.get("label", key)
                        tooltip = value.get("tooltip", "")
                    else:
                        label = str(value)
                        tooltip = ""

                    # Create simple glossary chip for now (remove complex onclick)
                    html += f"""
                    <span class='glossary-chip'
                          style='background: rgba(255,255,255,0.15); color: white; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.8rem; border: 1px solid rgba(255,255,255,0.25);'
                          title='{tooltip}'>
                        {label}
                    </span>
                    """
                html += "</div></div>"

            html += "</div>"  # Close reasoning section

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


# Maximum number of measures to include in notation viewer for large files
# (MIDI files can create massive MusicXML that browsers can't handle)
# Reduced to 20 for better OSMD performance with dense piano music
MAX_MEASURES_FOR_DISPLAY = 20


def detect_tempo_from_score(score) -> float:
    """
    Detect tempo from score, either from tempo marking or estimated from note density.

    Returns:
        Tempo in BPM (beats per minute). Defaults to 100 if not found.
    """
    try:
        # First, look for explicit tempo markings
        from music21 import tempo as m21_tempo

        tempo_marks = score.flatten().getElementsByClass(m21_tempo.MetronomeMark)
        if tempo_marks:
            bpm = tempo_marks[0].number
            # Check if bpm is valid (not None)
            if bpm is not None and bpm > 0:
                print(f"DEBUG: Found tempo marking: {bpm} BPM")
                return float(bpm)
            else:
                print(f"DEBUG: Found tempo marking but value is invalid: {bpm}")

        # If no tempo marking, estimate from note density
        # This is a rough heuristic: count notes in first 4 measures
        total_notes = 0
        total_duration = 0.0

        for part in score.parts[:1]:  # Just check first part
            measures = part.getElementsByClass("Measure")
            for measure in measures[:4]:  # First 4 measures
                notes = measure.flatten().notesAndRests
                total_notes += len([n for n in notes if n.isNote or n.isChord])
                total_duration += measure.quarterLength

        if total_duration > 0:
            # Notes per quarter note
            density = total_notes / total_duration
            # Rough estimate: higher density often means faster tempo
            # This is very approximate but better than nothing
            if density > 4:  # Very dense (lots of 16ths)
                estimated_bpm = 140
            elif density > 2:  # Moderate (8ths, some 16ths)
                estimated_bpm = 110
            else:  # Sparse (quarters, halves)
                estimated_bpm = 80

            print(
                f"DEBUG: Estimated tempo from note density: {estimated_bpm} BPM (density={density:.2f} notes/QL)"
            )
            return float(estimated_bpm)

    except Exception as e:
        print(f"DEBUG: Could not detect tempo: {e}")

    # Default fallback
    print("DEBUG: Using default tempo: 100 BPM")
    return 100.0


def calculate_initial_window(tempo_bpm: float) -> float:
    """
    Calculate initial analysis window size based on tempo.

    CRITICAL: Returns only musically sensible note values:
        - 0.5 QL = eighth note
        - 1.0 QL = quarter note
        - 2.0 QL = half note
        - 4.0 QL = whole note

    Args:
        tempo_bpm: Tempo in beats per minute

    Returns:
        Window size quantized to musical note values

    Tempo guidelines:
        - Very fast (>140 BPM): 1.0 QL (quarter note) - Fast jazz, rapid changes
        - Fast (100-140 BPM): 2.0 QL (half note) - Pop, upbeat classical
        - Moderate (60-100 BPM): 2.0 QL (half note) - Ballads, most classical
        - Slow (<60 BPM): 4.0 QL (whole note) - Slow choral, very sustained
    """
    if tempo_bpm > 140:
        window = 1.0
        category = "Very fast"
        note_name = "quarter note"
    elif tempo_bpm > 100:
        window = 2.0
        category = "Fast"
        note_name = "half note"
    elif tempo_bpm > 60:
        window = 2.0
        category = "Moderate"
        note_name = "half note"
    else:
        window = 4.0
        category = "Slow"
        note_name = "whole note"

    print(
        f"DEBUG: Tempo-based window calculation: {tempo_bpm} BPM → {window} QL = {note_name} ({category})"
    )
    return window


def analyze_uploaded_file(
    file_path: str,
    add_chordify: bool = True,
    label_chords: bool = True,
    run_analysis: bool = False,
    profile: str = "classical",
    process_full_file: bool = False,
    auto_window: bool = True,
    manual_window_size: float = 1.0,
    key_mode_preference: str = "Major",
) -> Dict[str, Any]:
    """
    Process uploaded MusicXML/MIDI file with optional chordify and analysis.

    This function tests the music21 integration by:
    1. Parsing uploaded files (MusicXML or MIDI)
    2. Optionally using music21's chordify to extract chord reduction
    3. Detecting chords and comparing music21 vs chord_logic
    4. Generating PNG notation and MusicXML download
    5. Optionally running harmonic analysis on extracted chords

    Args:
        file_path: Path to uploaded file (.xml, .mxl, .mid, .midi)
        add_chordify: Whether to add chordify staff to score
        label_chords: Whether to add chord symbol labels
        run_analysis: Whether to run harmonic analysis on chords
        profile: Analysis profile (classical, jazz, pop, etc.)

    Returns:
        Dictionary containing:
            - chord_symbols: List of detected chord symbols
            - key_hint: Detected key signature
            - metadata: File metadata (title, composer, etc.)
            - comparison: List of chord detection comparisons
            - agreement_rate: Percentage agreement between detections
            - png_path: Path to generated PNG notation
            - download_url: Path to annotated MusicXML file
            - analysis_result: Optional analysis results

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format unsupported or parsing fails
        RuntimeError: If Lilypond is not installed (required for PNG generation)

    Example:
        >>> result = analyze_uploaded_file(
        ...     'tests/data/test_files/simple_progression.xml',
        ...     add_chordify=True,
        ...     label_chords=True,
        ...     run_analysis=True
        ... )
        >>> print(result['chord_symbols'])
        ['C', 'Am', 'F', 'G']
        >>> print(result['agreement_rate'])
        0.95
    """
    # Opening move: import music21 integration and check file exists
    # Capture warnings during file parsing
    import io
    import os
    import tempfile
    import uuid
    from contextlib import redirect_stderr, redirect_stdout

    from harmonic_analysis.integrations.music21_adapter import Music21Adapter

    parsing_logs = []
    is_midi = False

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Validate file extension
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext not in [".xml", ".mxl", ".mid", ".midi"]:
        raise ValueError(
            f"Unsupported file format: {file_ext}. "
            "Expected .xml, .mxl, .mid, or .midi"
        )

    # Track if this is a MIDI file
    is_midi = file_ext in [".mid", ".midi"]

    # Main play: parse the file using Music21Adapter with warning capture
    adapter = Music21Adapter()

    # Capture Python warnings and music21 output during parsing
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always")

        if file_ext in [".xml", ".mxl"]:
            parsing_logs.append(
                f"📄 Parsing MusicXML file: {os.path.basename(file_path)}"
            )
            data = adapter.from_musicxml(file_path)
            parsing_logs.append("✅ MusicXML file parsed successfully")
        else:  # .mid or .midi
            parsing_logs.append(f"🎹 Parsing MIDI file: {os.path.basename(file_path)}")
            parsing_logs.append("⚠️  Note: MIDI → notation conversion is approximate")
            data = adapter.from_midi(file_path)
            parsing_logs.append("✅ MIDI file parsed")

        # Collect any warnings that occurred (filter out irrelevant ones)
        if caught_warnings:
            # Filter warnings - only show music21 and file-parsing related warnings
            irrelevant_categories = {"ResourceWarning", "DeprecationWarning"}
            irrelevant_keywords = {"unclosed event loop", "coroutine", "asyncio"}

            relevant_warnings = []
            for w in caught_warnings:
                warning_msg = str(w.message)
                # Skip if warning category is irrelevant
                if w.category.__name__ in irrelevant_categories:
                    # Check if message contains music-related content
                    if not any(
                        keyword in warning_msg.lower()
                        for keyword in [
                            "music",
                            "note",
                            "chord",
                            "measure",
                            "staff",
                            "voice",
                        ]
                    ):
                        continue
                # Skip if message contains irrelevant keywords
                if any(
                    keyword in warning_msg.lower() for keyword in irrelevant_keywords
                ):
                    continue

                # Truncate very long warnings
                if len(warning_msg) > 200:
                    warning_msg = warning_msg[:200] + "..."
                relevant_warnings.append(f"  • {w.category.__name__}: {warning_msg}")

            # Only add warning section if we have relevant warnings
            if relevant_warnings:
                parsing_logs.append(
                    f"\n⚠️  {len(relevant_warnings)} warning(s) during parsing:"
                )
                parsing_logs.extend(relevant_warnings)

    score = data["score_object"]
    chord_symbols = data["chord_symbols"]
    key_hint = data["key_hint"]
    metadata = data["metadata"]

    # Convert key signature to major or minor based on user preference
    # This ensures analysis uses the correct tonal center (e.g., B minor vs D major for 2 sharps)
    if key_hint and run_analysis:
        sharps_flats = parse_key_signature_from_hint(key_hint)
        prefer_minor = key_mode_preference == "Minor"
        converted_key = convert_key_signature_to_mode(sharps_flats, prefer_minor)
        print(
            f"DEBUG: Key conversion - Original: {key_hint}, Preference: {key_mode_preference}, Converted: {converted_key}"
        )
        key_hint_for_analysis = converted_key
    else:
        key_hint_for_analysis = key_hint

    # Initialize comparison tracking and window info
    comparison: List[Dict[str, Any]] = []
    final_window_size = None  # Will be set if chordify is enabled
    chordified_symbols_with_measures = (
        []
    )  # Will be populated during labeling if chordify+label enabled

    # Big play: chordify and label if requested
    if add_chordify:
        # Adaptive windowing based on harmonic change detection
        # Use fine-grained sampling + intelligent merging when harmony is stable
        from music21 import chord as m21_chord
        from music21 import clef, key
        from music21 import note as m21_note
        from music21 import stream

        # Create chord staff with adaptive windowing
        chordified = stream.Part()
        chordified.partName = "Chord Analysis"

        # Set bass clef for chord analysis staff (chord symbols typically in bass register)
        bass_clef = clef.BassClef()
        chordified.insert(0, bass_clef)
        print("DEBUG: Set bass clef for chord analysis staff")

        # Copy key signature from original score (important: chord staff should match original key)
        try:
            original_key = score.flatten().getElementsByClass("KeySignature")[0]
            print(f"DEBUG: Found original key signature: {original_key.sharps} sharps")
            # Create a NEW KeySignature object to avoid reference issues
            key_copy = key.KeySignature(original_key.sharps)
            print(f"DEBUG: Created new key signature copy: {key_copy.sharps} sharps")
            chordified.insert(0, key_copy)
            print(f"DEBUG: ✓ Inserted key signature into chord staff at offset 0")
        except (IndexError, AttributeError) as e:
            print(f"DEBUG: No key signature found in original score: {e}")

        # CRITICAL: Copy time signature from original score (prevents Dorico signpost issues)
        try:
            from music21 import meter

            original_time = score.flatten().getElementsByClass("TimeSignature")[0]
            # Create a new TimeSignature object to avoid reference issues
            time_sig_copy = meter.TimeSignature(
                f"{original_time.numerator}/{original_time.denominator}"
            )
            chordified.insert(0, time_sig_copy)
            print(
                f"DEBUG: Copied time signature to chord staff: {original_time.numerator}/{original_time.denominator}"
            )
        except (IndexError, AttributeError) as e:
            print(f"DEBUG: No time signature found in original score: {e}")

        # Get the total duration of the piece
        full_duration = score.flatten().highestTime

        # Performance optimization: For large files, only chordify first portion
        # UNLESS user explicitly requested full file processing for download
        measure_count = (
            max(len(part.getElementsByClass("Measure")) for part in score.parts)
            if score.parts
            else 0
        )
        if measure_count > MAX_MEASURES_FOR_DISPLAY and not process_full_file:
            # Calculate duration of first N measures
            try:
                time_sig = score.flatten().getElementsByClass("TimeSignature")[0]
                quarters_per_measure = time_sig.numerator * (4.0 / time_sig.denominator)
            except (IndexError, AttributeError):
                quarters_per_measure = 4.0

            total_duration = MAX_MEASURES_FOR_DISPLAY * quarters_per_measure
            print(
                f"DEBUG: Large file detected - limiting chordify to first {MAX_MEASURES_FOR_DISPLAY} measures ({total_duration} QL instead of {full_duration} QL)"
            )
            print(
                f"       💡 Tip: Enable 'Process Full File' option to include all measures in download"
            )
        else:
            total_duration = full_duration
            if measure_count > MAX_MEASURES_FOR_DISPLAY:
                print(
                    f"DEBUG: Processing full file ({measure_count} measures, {full_duration} QL) - this will take 1-2 minutes"
                )

        # Sample at fine intervals (16th notes) to detect all changes
        sample_interval = 0.25  # Quarter note / 4 = 16th note

        # Determine analysis window size
        if auto_window:
            # Auto mode: calculate based on tempo
            tempo_bpm = detect_tempo_from_score(score)
            initial_window = calculate_initial_window(tempo_bpm)
            analysis_window = initial_window
            print(
                f"DEBUG: AUTO WINDOW MODE - Tempo: {tempo_bpm} BPM → Window: {analysis_window} QL"
            )
        else:
            # Manual mode: use user's setting
            analysis_window = manual_window_size
            print(f"DEBUG: MANUAL WINDOW MODE - User selected: {analysis_window} QL")

        # Store for return value
        final_window_size = analysis_window

        print(
            f"DEBUG: Using adaptive windowing (sample={sample_interval}QL, window={analysis_window}QL)"
        )

        # First pass: collect pitch sets at each sample point
        samples = []
        current_offset = 0.0
        total_samples = int(total_duration / sample_interval)

        # Generate list of offsets to iterate over
        offsets = []
        temp_offset = 0.0
        while temp_offset < total_duration:
            offsets.append(temp_offset)
            temp_offset += sample_interval

        # Use progress tracking with periodic updates
        for idx, current_offset in enumerate(offsets):
            # Collect all notes sounding at this moment
            pitches_at_moment = []

            for part in score.parts:
                for element in part.flatten().notesAndRests:
                    if element.isNote:
                        note_start = element.offset
                        note_end = element.offset + element.duration.quarterLength

                        # Note is sounding if current_offset is within its duration
                        if note_start <= current_offset < note_end:
                            pitches_at_moment.append(element.pitch)
                    elif element.isChord:
                        chord_start = element.offset
                        chord_end = element.offset + element.duration.quarterLength

                        # Chord is sounding at this moment
                        if chord_start <= current_offset < chord_end:
                            pitches_at_moment.extend(element.pitches)

            # Store pitch class set (not MIDI notes) for comparison
            pitch_classes = frozenset(p.pitchClass for p in pitches_at_moment)

            if pitch_classes:  # Only add if there are notes
                samples.append(
                    {
                        "offset": current_offset,
                        "pitch_classes": pitch_classes,
                        "pitches": pitches_at_moment,
                    }
                )

        print(f"DEBUG: Collected {len(samples)} sample points")

        # Second pass: use sliding window to detect chord changes
        # Look ahead to accumulate notes before deciding on boundaries
        merged_regions = []

        if samples:
            i = 0
            total_windows = len(samples)
            windows_processed = 0

            while i < len(samples):
                # Look ahead: collect all notes within the next analysis_window
                window_start = samples[i]["offset"]
                window_end = window_start + analysis_window

                # Accumulate all pitch classes in this window
                window_pitch_classes = set()
                window_pitches = []
                window_samples = 0

                # Collect samples within this window
                j = i
                while j < len(samples) and samples[j]["offset"] < window_end:
                    window_pitch_classes |= samples[j]["pitch_classes"]
                    window_pitches.extend(samples[j]["pitches"])
                    window_samples += 1
                    j += 1

                windows_processed += 1

                if window_pitch_classes:
                    # Detect chord from accumulated window
                    window_chord = detect_chord_from_pitches(
                        [pc for pc in window_pitch_classes]
                    )

                    # Check if this chord is different from previous region
                    if merged_regions:
                        prev_chord = detect_chord_from_pitches(
                            [pc for pc in merged_regions[-1]["pitch_classes"]]
                        )

                        # Compare chord roots (ignore inversions)
                        prev_root = (
                            prev_chord.split("/")[0]
                            if "/" in prev_chord
                            else prev_chord
                        )
                        curr_root = (
                            window_chord.split("/")[0]
                            if "/" in window_chord
                            else window_chord
                        )

                        # If same chord, extend previous region
                        if prev_root == curr_root and curr_root != "Unknown":
                            # Merge with previous region
                            merged_regions[-1]["pitch_classes"] |= window_pitch_classes
                            merged_regions[-1]["pitches"].extend(window_pitches)
                            merged_regions[-1]["end"] = window_end
                            merged_regions[-1]["duration"] = (
                                merged_regions[-1]["end"] - merged_regions[-1]["start"]
                            )
                        else:
                            # Different chord - create new region
                            merged_regions.append(
                                {
                                    "start": window_start,
                                    "end": window_end,
                                    "duration": analysis_window,
                                    "pitch_classes": window_pitch_classes,
                                    "pitches": window_pitches,
                                }
                            )
                    else:
                        # First region
                        merged_regions.append(
                            {
                                "start": window_start,
                                "end": window_end,
                                "duration": analysis_window,
                                "pitch_classes": window_pitch_classes,
                                "pitches": window_pitches,
                            }
                        )

                # Move to next window (advance by full window size - non-overlapping)
                i = j

        print(
            f"DEBUG: Merged into {len(merged_regions)} harmonic regions via sliding windows"
        )

        # CRITICAL: Split regions at measure boundaries
        # Musical convention: each measure should get its own chord instance,
        # even if the harmony continues from the previous measure
        try:
            time_sig = score.flatten().getElementsByClass("TimeSignature")[0]
            quarters_per_measure = time_sig.numerator * (4.0 / time_sig.denominator)
        except (IndexError, AttributeError):
            quarters_per_measure = 4.0  # Default to 4/4 time

        measure_aware_regions = []
        for region in merged_regions:
            # Calculate which measures this region spans
            start_measure = int(region["start"] / quarters_per_measure)
            end_measure = int(
                (region["end"] - 0.001) / quarters_per_measure
            )  # Subtract small amount to handle exact boundaries

            if start_measure == end_measure:
                # Region fits within a single measure - keep as is
                measure_aware_regions.append(region)
            else:
                # Region crosses measure boundary - split it
                for measure_num in range(start_measure, end_measure + 1):
                    measure_start_offset = measure_num * quarters_per_measure
                    measure_end_offset = (measure_num + 1) * quarters_per_measure

                    # Calculate intersection with this measure
                    split_start = max(region["start"], measure_start_offset)
                    split_end = min(region["end"], measure_end_offset)

                    if split_end > split_start:  # Valid intersection
                        measure_aware_regions.append(
                            {
                                "start": split_start,
                                "end": split_end,
                                "duration": split_end - split_start,
                                "pitch_classes": region["pitch_classes"],
                                "pitches": region["pitches"],
                            }
                        )

        print(
            f"DEBUG: Split into {len(measure_aware_regions)} measure-aware regions (respecting barlines)"
        )

        # DEBUG: Show how many chords per measure
        chords_per_measure = {}
        for region in measure_aware_regions:
            measure_num = int(region["start"] / quarters_per_measure) + 1  # 1-indexed
            chords_per_measure[measure_num] = chords_per_measure.get(measure_num, 0) + 1

        # Show first 10 measures
        first_10_measures = sorted([m for m in chords_per_measure.keys() if m <= 10])
        if first_10_measures:
            measure_stats = ", ".join(
                [f"M{m}:{chords_per_measure[m]}" for m in first_10_measures]
            )
            print(f"DEBUG: Chords per measure (first 10): {measure_stats}")

        # Third pass: create chords from measure-aware regions
        for region in measure_aware_regions:
            if region["pitches"]:
                # Remove duplicate pitches (same MIDI note)
                unique_pitches = []
                seen_midi = set()
                for p in region["pitches"]:
                    if p.midi not in seen_midi:
                        unique_pitches.append(p)
                        seen_midi.add(p.midi)

                # Create chord for this region
                window_chord = m21_chord.Chord(unique_pitches)
                window_chord.quarterLength = region["duration"]
                # CRITICAL: Set voice to 1 to prevent MusicXML export warnings
                # Missing voice tags cause Dorico to misinterpret the entire score
                window_chord.voice = 1
                chordified.insert(region["start"], window_chord)

        print(
            f"DEBUG: Created {len(chordified.flatten().notesAndRests)} adaptive chords"
        )

        # Note: We intentionally do NOT call makeMeasures() here
        # music21 will auto-generate measures during MusicXML export
        # Calling makeMeasures() can corrupt the measure structure of the entire score

        # Critical fix: Rebuild score with proper part order
        # Chord staff should appear at BOTTOM (traditional lead sheet style)
        from music21 import instrument, layout, stream

        # Save original parts
        original_parts = list(score.parts)

        # Create new score with metadata preserved
        new_score = stream.Score()
        if score.metadata:
            new_score.metadata = score.metadata

        # Add original parts FIRST (top staves)
        # CRITICAL: Deep copy parts to avoid music21 export modifying them in place
        import copy

        copied_parts = []
        for part in original_parts:
            new_part = copy.deepcopy(part)
            new_score.append(new_part)
            copied_parts.append(new_part)

        # Create a staff group for the original parts (to keep them visually separate from chord analysis)
        if len(copied_parts) > 0:
            # StaffGroup keeps original parts together with bracket
            original_group = layout.StaffGroup(
                copied_parts, name="Original", symbol="bracket"
            )
            new_score.insert(0, original_group)

        # CRITICAL: Set explicit instrument to prevent auto-grouping with piano parts
        # Use a generic instrument to mark this as completely separate
        chord_instrument = instrument.Instrument()
        chord_instrument.instrumentName = "Chord Analysis"
        chord_instrument.instrumentAbbreviation = "Ch."
        chordified.insert(0, chord_instrument)
        print("DEBUG: Set explicit instrument for chord staff to prevent auto-grouping")

        # Add chordified LAST as a completely separate part (no staff group, separate instrument)
        new_score.append(chordified)

        # Replace score
        score = new_score

        print(
            f"DEBUG: Score rebuilt with {len(score.parts)} parts (chord staff as separate instrument at bottom)"
        )

        if label_chords:
            # For each chord in chordified staff, detect and label
            # Need to iterate through the actual chordified part in the score
            chord_part = new_score.parts[-1]  # Last part is chord analysis
            labeled_count = 0

            # Get time signature to calculate measure numbers from offsets
            # Assume 4/4 time if not specified (4 quarter notes per measure)
            try:
                time_sig = score.flatten().getElementsByClass("TimeSignature")[0]
                quarters_per_measure = time_sig.numerator * (4.0 / time_sig.denominator)
            except (IndexError, AttributeError):
                quarters_per_measure = 4.0  # Default to 4/4 time

            print(
                f"DEBUG: Calculating measures with {quarters_per_measure} quarters per measure"
            )

            for element in chord_part.flatten().notesAndRests:
                if element.isChord:
                    # music21's enhanced chord detection with sus4/add4 support
                    try:
                        m21_symbol = detect_chord_with_music21(element)
                    except (AttributeError, Exception) as e:
                        print(f"DEBUG: music21 detection failed: {e}")
                        m21_symbol = "Unknown"

                    # Our detection: extract pitches and detect chord using legacy chord_parser logic
                    try:
                        # Get MIDI pitch numbers from the chord
                        pitches = [p.midi for p in element.pitches]
                        our_symbol = detect_chord_from_pitches(pitches)
                    except (AttributeError, Exception) as e:
                        print(f"DEBUG: chord_logic detection failed: {e}")
                        our_symbol = "Unknown"

                    # Add our labels to the score as lyrics (below staff)
                    element.addLyric(our_symbol)
                    labeled_count += 1

                    # Calculate measure number from offset
                    # Measure numbers start at 1
                    measure_num = int(element.offset / quarters_per_measure) + 1

                    # Store chord symbol with measure for analysis
                    chordified_symbols_with_measures.append(
                        {
                            "measure": measure_num,
                            "chord": our_symbol,
                            "offset": element.offset,
                        }
                    )

                    comparison.append(
                        {
                            "measure": measure_num,
                            "music21": m21_symbol,
                            "chord_logic": our_symbol,
                            "match": "✓" if m21_symbol == our_symbol else "✗",
                        }
                    )

            print(f"DEBUG: Added labels to {labeled_count} chords")
            print(
                f"DEBUG: Collected {len(chordified_symbols_with_measures)} chords with measures for analysis"
            )

    # Generate output files
    # We need TWO files:
    # 1. notation_xml - for OSMD viewer (always truncated to 20 measures)
    # 2. download_xml - for download (full file if requested, preview otherwise)
    temp_dir = tempfile.gettempdir()
    file_uuid = str(uuid.uuid4())

    notation_xml_path = os.path.join(
        temp_dir, f"notation_{file_uuid}.xml"
    )  # For viewer
    download_xml_path = os.path.join(
        temp_dir, f"download_{file_uuid}.xml"
    )  # For download

    # Strip tempo markings to avoid OSMD parsing errors
    # OSMD 1.8.6 has bugs with TempoExpressions
    from music21 import tempo

    removed_count = 0

    # Iterate through all parts and recursively remove tempo elements
    for part in score.parts:
        # Collect tempo elements to remove (can't remove while iterating)
        tempo_elements = []
        for element in part.recurse():
            if isinstance(
                element,
                (tempo.TempoIndication, tempo.MetronomeMark, tempo.MetricModulation),
            ):
                tempo_elements.append(element)

        # Remove collected tempo elements
        for tempo_elem in tempo_elements:
            try:
                # Get the container (measure or part)
                container = tempo_elem.activeSite
                if container:
                    container.remove(tempo_elem)
                    removed_count += 1
            except Exception as e:
                print(f"DEBUG: Could not remove tempo element: {e}")

    if removed_count > 0:
        print(f"DEBUG: Removed {removed_count} tempo markings for OSMD compatibility")
    else:
        print("DEBUG: No tempo markings found to remove")

    # Debug: Check score structure before export
    part_count = len(score.parts) if hasattr(score, "parts") else 0

    # Count measures correctly - check the parts, not flattened score
    # (flattened scores lose measure structure in music21)
    measure_count = 0
    if part_count > 0:
        # Get max measure count from any part
        measure_count = max(
            len(part.getElementsByClass("Measure")) for part in score.parts
        )

    print(
        f"DEBUG: Score structure - {part_count} parts, {measure_count} measures (max in any part)"
    )

    if part_count == 0:
        print("WARNING: Score has no parts! This may cause export issues.")

    # For large MIDI files, create a separate preview for notation viewer
    # while keeping full score for download when requested
    # (MIDI files often generate huge MusicXML that OSMD can't handle)
    notation_score = score  # Default: use full score

    if measure_count > MAX_MEASURES_FOR_DISPLAY:
        print(
            f"DEBUG: Large score detected ({measure_count} measures). Creating preview with first {MAX_MEASURES_FOR_DISPLAY} measures for notation viewer."
        )

        # Create a truncated copy using music21's measure extraction
        # This preserves more context than manual copying
        from music21 import stream

        try:
            # Manual measure extraction is more reliable than score.measures()
            # because it avoids broken activeSite references
            from music21 import stream

            notation_score = stream.Score()
            if score.metadata:
                # CRITICAL: Create a COPY of metadata to avoid modifying original score's metadata
                import copy

                notation_score.metadata = copy.deepcopy(score.metadata)

            # Set a better title if not present (music21 defaults to "Music21 Fragment")
            if (
                not notation_score.metadata
                or not notation_score.metadata.title
                or notation_score.metadata.title == "Music21 Fragment"
            ):
                import os

                filename = os.path.basename(file_path)
                notation_score.metadata.title = (
                    f"{filename} (First {MAX_MEASURES_FOR_DISPLAY} Measures)"
                )

            truncated_parts = 0
            for original_part in score.parts:
                measures = original_part.getElementsByClass("Measure")

                if measures and len(measures) > 0:
                    # Part has explicit measures (normal case)
                    new_part = stream.Part()

                    # Copy part attributes
                    if hasattr(original_part, "partName"):
                        new_part.partName = original_part.partName
                    if hasattr(original_part, "id"):
                        new_part.id = original_part.id

                    # Copy first N measures (creates fresh copies, avoiding activeSite issues)
                    for measure in measures[:MAX_MEASURES_FOR_DISPLAY]:
                        # Deep copy the measure to break old references
                        import copy

                        new_measure = copy.deepcopy(measure)
                        new_part.append(new_measure)

                    notation_score.append(new_part)
                    truncated_parts += 1
                else:
                    # Part has no measures (e.g., chordified staff) - use offset-based slicing
                    # Calculate end offset for first N measures based on time signature
                    try:
                        time_sig = score.flatten().getElementsByClass("TimeSignature")[
                            0
                        ]
                        quarters_per_measure = time_sig.numerator * (
                            4.0 / time_sig.denominator
                        )
                    except (IndexError, AttributeError):
                        quarters_per_measure = 4.0  # Default to 4/4

                    max_offset = MAX_MEASURES_FOR_DISPLAY * quarters_per_measure

                    # Extract elements within offset range
                    new_part = stream.Part()
                    if hasattr(original_part, "partName"):
                        new_part.partName = original_part.partName
                    if hasattr(original_part, "id"):
                        new_part.id = original_part.id

                    # CRITICAL: Copy key signature, time signature, clef from original part
                    # These are at offset 0 and must be preserved
                    import copy

                    for element in original_part.getElementsByOffset(0):
                        # Check if element has isNote attribute (not all elements do, e.g., Instrument)
                        if not hasattr(element, "isNote") or (
                            not element.isNote and not element.isRest
                        ):
                            # Copy non-note elements at offset 0 (clef, key sig, time sig, etc.)
                            new_part.insert(0, copy.deepcopy(element))

                    # Copy notes and rests within the excerpt range
                    for element in original_part.flatten().notesAndRests:
                        if element.offset < max_offset:
                            new_element = copy.deepcopy(element)
                            new_part.insert(element.offset, new_element)

                    if len(new_part.flatten().notesAndRests) > 0:
                        notation_score.append(new_part)
                        truncated_parts += 1
                        print(
                            f"DEBUG: Included offset-based part '{new_part.partName}' with {len(new_part.flatten().notesAndRests)} elements"
                        )

            if truncated_parts > 0:
                print(
                    f"DEBUG: ✓ Created excerpt with {truncated_parts} parts, first {MAX_MEASURES_FOR_DISPLAY} measures each"
                )
            else:
                print(f"DEBUG: Truncation failed, using full score as fallback")
                notation_score = score

        except Exception as e:
            print(f"WARNING: Could not create excerpt: {e}. Using full score.")
            import traceback

            traceback.print_exc()
            notation_score = score

    # Decision: Which score to export for download?
    # - If process_full_file=True: Export full score (all measures with chords)
    # - Otherwise: Export truncated score (first 20 measures for quick preview)
    if process_full_file:
        download_score = score  # Full score with all processing
        print(
            f"DEBUG: Full file processing enabled - download will contain all {measure_count} measures"
        )

        # Set a better title for full download file
        # CRITICAL: Ensure we have metadata object, and fix title if it's missing or wrong
        if not download_score.metadata:
            from music21 import metadata as m21_metadata

            download_score.metadata = m21_metadata.Metadata()

        import os

        filename = os.path.basename(file_path)

        # Always set proper title for full file (it may have "First 20 Measures" from earlier operations)
        if (
            not download_score.metadata.title
            or download_score.metadata.title == "Music21 Fragment"
            or "First" in str(download_score.metadata.title)
        ):
            download_score.metadata.title = (
                f"{filename} (Full - {measure_count} Measures)"
            )
            print(f"DEBUG: Set download title to: {download_score.metadata.title}")
    else:
        download_score = notation_score  # Truncated preview
        print(
            f"DEBUG: Preview mode - download will contain first {MAX_MEASURES_FOR_DISPLAY} measures"
        )

    # Export TWO MusicXML files:
    # 1. Notation file (for OSMD viewer) - always truncated for browser performance
    # 2. Download file (for user) - full or preview depending on checkbox

    # Export notation file (for OSMD viewer)
    try:
        # CRITICAL: Skip makeNotation() and deepcopy to preserve original notation
        # makeNotation() recalculates durations and corrupts the piano parts
        print(
            "DEBUG: Exporting notation file without makeNotation() to preserve MIDI notation"
        )
        notation_score.write("musicxml", fp=notation_xml_path)

        if os.path.exists(notation_xml_path):
            file_size = os.path.getsize(notation_xml_path)
            print(
                f"DEBUG: ✓ Exported notation MusicXML for viewer: {notation_xml_path} ({file_size:,} bytes)"
            )
        else:
            print(
                f"ERROR: Notation MusicXML file was not created at {notation_xml_path}"
            )

    except Exception as e:
        print(f"ERROR: Failed to export notation MusicXML: {e}")
        import traceback

        traceback.print_exc()

    # Export download file (full or preview based on checkbox)
    try:
        # CRITICAL: Skip makeNotation() to preserve original notation
        # makeNotation() recalculates durations and corrupts the piano parts
        # The original MIDI-imported notation is already correct
        print("DEBUG: Skipping makeNotation() to preserve original MIDI notation")
        download_export_score = download_score

        # Try to write MusicXML (export chosen score - full or preview)
        download_export_score.write("musicxml", fp=download_xml_path)

        # Verify export was successful
        if os.path.exists(download_xml_path):
            file_size = os.path.getsize(download_xml_path)
            print(
                f"DEBUG: ✓ Exported download MusicXML: {download_xml_path} ({file_size:,} bytes)"
            )

            # Validate the MusicXML file
            try:
                print("DEBUG: Validating MusicXML file...")
                from music21 import converter

                # Try to parse it back - if it's valid, this should work
                validation_score = converter.parse(download_xml_path)
                part_count = (
                    len(validation_score.parts)
                    if hasattr(validation_score, "parts")
                    else 0
                )
                print(
                    f"DEBUG: ✓ MusicXML validation passed - {part_count} parts parsed successfully"
                )

            except Exception as e:
                print(f"WARNING: MusicXML validation failed: {e}")
                print(
                    f"         The file may not import correctly into some notation software"
                )
                import traceback

                traceback.print_exc()

            if file_size == 0:
                print(
                    f"ERROR: Download MusicXML file is empty! Score may have no content."
                )
            elif file_size > 10_000_000:  # 10MB
                print(
                    f"WARNING: Download MusicXML file is very large ({file_size:,} bytes)."
                )
        else:
            print(
                f"ERROR: Download MusicXML file was not created at {download_xml_path}"
            )

    except Exception as e:
        print(f"ERROR: Failed to export MusicXML: {e}")
        print(f"ERROR: Score type: {type(score)}, Has parts: {hasattr(score, 'parts')}")
        import traceback

        traceback.print_exc()

        # Create a minimal error placeholder file
        error_xml = """<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <part-list>
    <score-part id="P1"><part-name>Error</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>whole</type></note>
    </measure>
  </part>
</score-partwise>"""
        with open(output_xml_path, "w") as f:
            f.write(error_xml)
        print(f"DEBUG: Created placeholder MusicXML file due to export error")

    # Calculate agreement rate
    agreement_rate = 0.0
    if comparison:
        matches = sum(1 for c in comparison if c["match"])
        agreement_rate = matches / len(comparison)

    # Optional: run harmonic analysis
    # CRITICAL: Use chordified symbols if available, otherwise fall back to original
    analysis_result = None
    analysis_chord_data = None  # Will contain chord symbols with measure numbers

    if run_analysis:
        # Use chordified symbols if we created them, otherwise use original
        if chordified_symbols_with_measures:
            analysis_chords = [
                item["chord"] for item in chordified_symbols_with_measures
            ]
            analysis_chord_data = chordified_symbols_with_measures
        elif chord_symbols:
            analysis_chords = chord_symbols
            analysis_chord_data = [
                {"measure": i + 1, "chord": c, "offset": None}
                for i, c in enumerate(chord_symbols)
            ]
        else:
            analysis_chords = []

        if analysis_chords:
            service = get_service()
            try:
                analysis_result = asyncio.run(
                    service.analyze_with_patterns_async(
                        chord_symbols=analysis_chords,
                        key_hint=key_hint_for_analysis,  # Use converted key based on user preference
                        profile=profile,
                    )
                )
            except Exception as e:
                warnings.warn(f"Analysis failed: {e}", UserWarning)

    # Victory lap: return comprehensive results
    return {
        "chord_symbols": chord_symbols,
        "chordified_symbols_with_measures": chordified_symbols_with_measures,  # NEW: chords with measure info
        "key_hint": key_hint,
        "metadata": metadata,
        "comparison": comparison,
        "agreement_rate": agreement_rate,
        "notation_url": notation_xml_path,  # MusicXML file for OSMD viewer (always 20 measures)
        "download_url": download_xml_path,  # MusicXML file for download (full or preview)
        "analysis_result": asdict(analysis_result) if analysis_result else None,
        "measure_count": measure_count,  # Total measures in score
        "truncated_for_display": measure_count
        > MAX_MEASURES_FOR_DISPLAY,  # Whether notation was truncated
        "is_midi": is_midi,  # Flag for MIDI warning display
        "parsing_logs": (
            "\n".join(parsing_logs) if parsing_logs else None
        ),  # Parsing logs and warnings
        "window_size_used": final_window_size,  # Window size used for chord detection (None if no chordify)
    }


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
                        gr.Markdown("### 🎵 Chord Detection Comparison")
                        upload_comparison_output = gr.Dataframe(
                            label="music21 vs chord_logic Detection",
                            headers=["Measure", "music21", "chord_logic", "Match"],
                            datatype=["number", "str", "str", "str"],
                            col_count=(4, "fixed"),
                            row_count=(10, "dynamic"),
                            wrap=True,
                        )

                with gr.Row():
                    upload_agreement_output = gr.Textbox(
                        label="Agreement Rate",
                        interactive=False,
                    )

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
                    {"error": "No file uploaded"},
                    None,
                    "",
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

                # Format comparison dataframe
                comparison_data = None
                if result["comparison"]:
                    comparison_data = [
                        [
                            c["measure"],
                            c["music21"],
                            c["chord_logic"],
                            "✓" if c["match"] else "✗",
                        ]
                        for c in result["comparison"]
                    ]

                # Format agreement rate with truncation notice if applicable
                agreement_text = (
                    f"{result['agreement_rate']:.1%}" if result["comparison"] else "N/A"
                )

                # Add note if notation was truncated for display
                if result.get("truncated_for_display", False):
                    measure_count = result.get("measure_count", 0)
                    agreement_text += f"\n\n⚠️ **Note:** Large file detected ({measure_count} measures). Notation viewer shows first {MAX_MEASURES_FOR_DISPLAY} measures only. Download the complete MusicXML file below."

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
                    comparison_data,
                    agreement_text,
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
                    "",
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
                upload_comparison_output,
                upload_agreement_output,
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
