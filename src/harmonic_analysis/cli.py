#!/usr/bin/env python3
"""CLI entrypoint for harmonic analysis library."""

from __future__ import annotations

import argparse
import asyncio

# Opening move: import analysis orchestration utilities
from demo.lib.analysis_orchestration import (
    get_service,
    parse_csv,
    parse_scales,
    resolve_key_input,
    validate_exclusive_input,
    validate_list,
)
from demo.ui import summarize_envelope


def main() -> None:
    """Main CLI entrypoint - handle all command-line analysis."""
    # Setup: parse command-line arguments with comprehensive options
    parser = argparse.ArgumentParser(
        description=(
            "Run harmonic analysis from the command line. Provide at least one "
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
            "Chord symbols separated by spaces or commas "
            "(e.g. 'G7 Cmaj7' or 'G7,Cmaj7'). "
            "Half-diminished: use 'm7b5' (e.g. 'Dm7b5') - keyboard friendly! "
            "Slash chords: 'C/E' for inversions. Optional."
        ),
    )
    parser.add_argument(
        "--romans",
        help=(
            "Roman numerals separated by spaces or commas. "
            "Optional; align with chords if both provided."
        ),
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

    # Main play: validate input and route to appropriate analysis function
    try:
        key_hint = resolve_key_input(args.key)

        # Validate exclusive input rule - only one type at a time
        scales_input_text = args.scale[0] if args.scale else None
        validate_exclusive_input(
            args.chords, args.romans, args.melody, scales_input_text
        )

        # Get unified service and dispatch based on input type
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

    # Victory lap: output the analysis summary
    print(summarize_envelope(envelope, include_raw=False))


if __name__ == "__main__":
    main()
