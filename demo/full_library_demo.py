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

# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the harmonic analysis CLI demo. Provide at least one "
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
    args = parser.parse_args()

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
