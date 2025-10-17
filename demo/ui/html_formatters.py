"""HTML formatting functions for the harmonic analysis demo.

This module contains all HTML generation and formatting utilities used to
display harmonic analysis results in the Gradio interface. Functions handle
everything from OSMD music notation rendering to evidence cards and code snippets.

Musical Metaphor: Think of this module as the concert hall stage crew—setting up
the perfect visual presentation so the harmonic analysis performance shines.
"""

from __future__ import annotations

import base64
import json
import os
import tempfile
import uuid
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# OSMD (OpenSheetMusicDisplay) HTML Generation
# ---------------------------------------------------------------------------


def generate_osmd_html_file(musicxml_path: str) -> str:
    """Generate standalone HTML file with OSMD viewer.

    Opening move: Create a complete, self-contained HTML file that can render
    MusicXML notation in any browser. We embed the MusicXML as base64 to avoid
    file path issues—this is how we keep the viewer portable.

    Args:
        musicxml_path: Path to MusicXML file to display

    Returns:
        Path to generated HTML file (saved in temp directory)

    Main play: The HTML includes OSMD from CDN, zoom controls, and robust
    error handling. We use base64 encoding because passing raw XML through
    HTML/JavaScript is a recipe for parsing nightmares.
    """
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

    # Victory lap: Save to temp file and return the path
    html_path = os.path.join(
        tempfile.gettempdir(), f"osmd_viewer_{os.path.basename(musicxml_path)}.html"
    )
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return html_path


def generate_osmd_viewer(musicxml_path: str) -> str:
    """Generate HTML for OpenSheetMusicDisplay viewer (embeddable version).

    Time to tackle the embedded viewer: Unlike the standalone file version,
    this creates an HTML snippet that can be injected into Gradio. We use
    unique IDs to avoid conflicts when multiple viewers exist on the same page.

    Args:
        musicxml_path: Path to MusicXML file to display

    Returns:
        HTML string with embedded OSMD viewer (not a file path)

    This looks odd but it saves us from viewer ID conflicts: Each instance gets
    a unique UUID-based ID so multiple OSMD viewers can coexist peacefully in
    the same Gradio interface without stepping on each other's JavaScript.
    """
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


# ---------------------------------------------------------------------------
# File Analysis HTML Formatting
# ---------------------------------------------------------------------------


def format_file_analysis_html(
    analysis_result: Dict[str, Any], chord_data: list, key_hint: Optional[str] = None
) -> str:
    """Format harmonic analysis results for uploaded files with structured display.

    Connects roman numerals to actual chord symbols in a readable table format.
    This function handles MusicXML uploads where we have measure numbers and
    structural information—much richer than just a chord symbol list.

    Args:
        analysis_result: Analysis results dict from PatternAnalysisService
        chord_data: List of dicts with 'measure', 'chord', 'offset' keys, or
                    list of chord strings (backward compatibility)
        key_hint: Optional key signature hint from file metadata

    Returns:
        Styled HTML string with analysis results in table format

    Here's where we connect the dots: The analysis engine gives us roman numerals,
    the file parser gives us chord symbols + measure numbers, and this function
    weaves them together into a coherent visual story.
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

    # Main play: Create table rows connecting chord symbols to roman numerals
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


# ---------------------------------------------------------------------------
# Helper Functions for Chord Analysis
# ---------------------------------------------------------------------------


def get_chord_function_description(roman: str, key: str) -> str:
    """Provide a brief functional description for a roman numeral.

    Quick lookup table: Map roman numerals to their common functional roles.
    This isn't comprehensive music theory—it's practical labeling for the UI.

    Args:
        roman: Roman numeral string (e.g., "I", "V7", "ii")
        key: Key context (for display purposes)

    Returns:
        Human-readable function description

    Simple heuristics for common functions: We use uppercase/lowercase and
    quality markers to infer function. Not perfect, but good enough for
    80% of real-world progressions.
    """
    # Check longer patterns first to avoid false matches
    upper = roman.upper()

    if upper.startswith("VII"):
        if "dim" in roman.lower() or "°" in roman:
            return "Leading tone diminished"
        return "Leading tone"
    elif upper.startswith("VI"):
        return "Submediant (relative minor)" if roman.startswith("vi") else "Submediant"
    elif upper.startswith("V"):
        if "7" in roman:
            return "Dominant 7th (tension)"
        return "Dominant (leading to tonic)"
    elif upper.startswith("IV"):
        return "Subdominant (pre-dominant)"
    elif upper.startswith("III"):
        return "Mediant"
    elif upper.startswith("II"):
        return "Supertonic (pre-dominant)"
    elif upper.startswith("I"):
        if roman == "I":
            return "Tonic (home)"
        return "Tonic variant"
    else:
        return "—"


def format_confidence_badge(confidence: float) -> str:
    """Create a colored confidence badge based on value.

    Color-coded confidence display: Visual feedback helps users quickly
    assess reliability. We use traffic light colors—green means trust it,
    red means take it with a grain of salt.

    Args:
        confidence: Float between 0 and 1

    Returns:
        HTML span with colored badge
    """
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


# ---------------------------------------------------------------------------
# Code Snippet Generation
# ---------------------------------------------------------------------------


def generate_code_snippet(
    chord_symbols: List[str], profile: str, key_hint: Optional[str], envelope: Any
) -> tuple[str, str, str]:
    """Generate Python code snippets to reproduce the analysis.

    Here's where we help users take the library home: Generate ready-to-run
    code examples showing how to recreate this analysis in their own projects.
    We provide async, sync, and API versions to match different use cases.

    Args:
        chord_symbols: List of chord symbols analyzed
        profile: Analysis profile used (classical, jazz, etc.)
        key_hint: Optional key hint provided
        envelope: Analysis result envelope (for context)

    Returns:
        Tuple of (async_code, sync_code, api_code) strings

    Escape hatches prevent code injection: We escape quotes in user inputs
    before embedding them in code strings. This looks paranoid but saves us
    from weird edge cases when chord symbols contain quotes.
    """
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


# ---------------------------------------------------------------------------
# Evidence and Pattern Display
# ---------------------------------------------------------------------------


def generate_enhanced_evidence_cards(envelope: Any) -> str:
    """Generate enhanced evidence display with rich cards and visualizations.

    Time to show our work: The analysis engine collects evidence from various
    pattern recognizers. This function transforms that raw evidence into
    beautiful, color-coded cards that help users understand WHY we arrived
    at a particular interpretation.

    Args:
        envelope: Analysis result envelope containing evidence list

    Returns:
        HTML string with styled evidence cards

    Color coding by pattern family: Cadence patterns get purple, modal patterns
    get cyan, functional harmony gets green, chromatic gets amber. This visual
    categorization helps users quickly scan for the evidence types they care about.
    """
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


def generate_chord_progression_display(envelope: Any) -> str:
    """Generate enhanced chord progression display with music notation styling.

    Big play: Create an interactive, color-coded display of the chord progression
    with hover effects. Each chord gets a card colored by its quality (major green,
    minor blue, diminished red, etc.) with both the chord symbol and roman numeral.

    Args:
        envelope: Analysis result envelope with chord_symbols and primary interpretation

    Returns:
        HTML string with styled chord progression display

    This is how we make chord progressions visually scannable: Color by quality,
    arrows between chords, hover effects for interactivity. The result feels more
    like a music notation app than a static report.
    """
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


def format_evidence_html(evidence_list: List[Any]) -> str:
    """Format evidence list as styled HTML.

    Simpler evidence display: When we don't need the full enhanced cards,
    this function provides a cleaner, more compact list view of evidence
    patterns. Good for alternative interpretations where screen space is limited.

    Args:
        evidence_list: List of evidence objects from analysis

    Returns:
        HTML string with compact evidence display
    """
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


# ---------------------------------------------------------------------------
# Complete Analysis HTML Formatting (Main Display)
# ---------------------------------------------------------------------------


def format_analysis_html(envelope: Any) -> str:
    """Format the analysis envelope as rich HTML with interactive glossary.

    Final whistle: This is the big kahuna—the main analysis display that pulls
    everything together. Primary interpretation, alternatives, evidence, chord
    progression display, and code snippets all in one comprehensive view.

    Args:
        envelope: Complete analysis result envelope

    Returns:
        HTML string with full analysis display

    Victory lap: We use collapsible sections (details/summary) to manage complexity,
    tabbed code examples for different use cases, and modal glossary popups for
    terminology. The result is information-dense but not overwhelming.
    """
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


# ---------------------------------------------------------------------------
# Text Summarization (Non-HTML Formatting)
# ---------------------------------------------------------------------------


def summarize_envelope(envelope: Any, include_raw: bool = True) -> str:
    """Summarize analysis envelope as plain text.

    Plain text fallback: When HTML isn't appropriate (CLI output, logs, debugging),
    this function provides a clean text representation of the analysis results.

    Args:
        envelope: Analysis result envelope
        include_raw: Whether to include raw JSON dump at the end

    Returns:
        Plain text summary string

    Final whistle: Format everything as human-readable text with clear sections
    and consistent indentation. Perfect for console output or text logs.
    """
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
