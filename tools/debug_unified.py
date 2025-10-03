#!/usr/bin/env python3
"""
Unified Debug Tool - Consolidates all debug capabilities

Replaces individual debug scripts with a comprehensive tool that can:
- Analyze patterns (debug_patterns.py functionality)
- Analyze Stage B events (debug_stage_b.py functionality)
- Analyze backdoor progressions (debug_backdoor.py functionality)
- Analyze intervals (debug_intervals.py functionality)
- Work with all existing test infrastructure

Usage:
    python tools/debug_unified.py --progression "Am F C G" --all
    python tools/debug_unified.py --case pop_vi_IV_I_V --patterns --stage-b
    python tools/debug_unified.py --interactive
    python tools/debug_unified.py --test-failure test_vi_IV_I_V "Am F C G"
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List, Optional

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))  # Add project root for tests.utils imports

from tests.utils import (
    COMMON_DEBUG_CASES,
    DebugCase,
    DebugConfig,
    PatternDebugger,
    UnifiedDebugger,
    debug_progression,
    debug_test_failure,
    get_case_by_name,
    list_available_cases,
    run_debug_case,
)


def parse_chord_string(chord_string: str) -> List[str]:
    """Parse chord string like 'Am F C G' into list."""
    return [c.strip() for c in chord_string.replace(",", " ").split() if c.strip()]


def interactive_debug():
    """Interactive debugging session."""
    print("\n🎵 UNIFIED INTERACTIVE DEBUG SESSION")
    print("=" * 50)

    # Get chord progression
    chord_input = input("Enter chord progression (e.g., 'Am F C G'): ").strip()
    if not chord_input:
        print("❌ No chords provided.")
        return

    chords = parse_chord_string(chord_input)
    print(f"Chords: {chords}")

    # Get profile
    profile = input("Profile [classical/pop/jazz]: ").strip() or "classical"

    # Get key hint
    key_hint = input("Key hint (optional): ").strip() or None

    # Get analysis options
    print("\nAnalysis options:")
    analyze_patterns = input("Analyze patterns? [Y/n]: ").strip().lower() not in [
        "n",
        "no",
    ]
    analyze_tokens = input("Analyze tokens? [Y/n]: ").strip().lower() not in ["n", "no"]
    analyze_stage_b = input("Analyze Stage B events? [y/N]: ").strip().lower() in [
        "y",
        "yes",
    ]
    analyze_backdoor = input(
        "Analyze backdoor progressions? [y/N]: "
    ).strip().lower() in ["y", "yes"]
    analyze_intervals = input("Analyze intervals? [y/N]: ").strip().lower() in [
        "y",
        "yes",
    ]
    trace_patterns = input("Enable pattern tracing? [y/N]: ").strip().lower() in [
        "y",
        "yes",
    ]

    # Create debugger with configuration
    config = DebugConfig(
        enabled=True,
        trace_patterns=trace_patterns,
        analyze_tokens=analyze_tokens,
        analyze_intervals=analyze_intervals,
        analyze_stage_b_events=analyze_stage_b,
        analyze_backdoor=analyze_backdoor,
        verbose=True,
    )

    debugger = UnifiedDebugger(config)

    print(f"\n🔍 Running comprehensive analysis...")
    debug_info = debugger.analyze_comprehensive(
        chords=chords,
        profile=profile,
        key_hint=key_hint,
        test_name="interactive_session",
    )

    debugger.print_debug_summary(debug_info)

    # Ask if user wants to save results
    save = input("\nSave debug results to file? [y/N]: ").strip().lower() in [
        "y",
        "yes",
    ]
    if save:
        filename = (
            input("Filename [debug_results.txt]: ").strip() or "debug_results.txt"
        )
        with open(filename, "w") as f:
            f.write(f"Debug Results for {chords}\n")
            f.write("=" * 50 + "\n")
            f.write(str(debug_info))
        print(f"✅ Results saved to {filename}")


def run_common_case(case_name: str, **overrides):
    """Run a common debug case with optional overrides."""
    case = get_case_by_name(case_name)
    if not case:
        print(f"❌ Case '{case_name}' not found.")
        print(f"Available cases: {list_available_cases()}")
        return

    # Apply any overrides (only valid DebugCase fields)
    import dataclasses

    valid_fields = {f.name for f in dataclasses.fields(DebugCase)}
    case_overrides = {k: v for k, v in overrides.items() if k in valid_fields}
    if case_overrides:
        case = dataclasses.replace(case, **case_overrides)

    print(f"\n🎵 RUNNING CASE: {case.name}")
    print("=" * 50)
    print(f"Description: {case.description}")

    # Run with pattern debugger (preserving original behavior)
    result = run_debug_case(case, verbose=True)

    # Also run unified analysis if advanced options requested
    advanced_options = ["analyze_stage_b", "analyze_backdoor", "analyze_intervals"]
    if any(overrides.get(opt, False) for opt in advanced_options):
        print(f"\n🔬 UNIFIED ANALYSIS:")
        print("-" * 30)

        config = DebugConfig(
            enabled=True,
            trace_patterns=overrides.get("trace", case.trace),
            analyze_tokens=True,
            analyze_intervals=overrides.get("analyze_intervals", False),
            analyze_stage_b_events=overrides.get("analyze_stage_b", False),
            analyze_backdoor=overrides.get("analyze_backdoor", False),
            verbose=True,
        )

        debugger = UnifiedDebugger(config)
        unified_result = debugger.analyze_comprehensive(
            chords=case.chords,
            profile=case.profile,
            key_hint=case.key_hint,
            test_name=case.name,
        )
        debugger.print_debug_summary(unified_result)


def run_test_failure_debug(test_name: str, chord_string: str, **kwargs):
    """Debug a test failure with full analysis."""
    chords = parse_chord_string(chord_string)

    print(f"\n🧪 DEBUGGING TEST FAILURE: {test_name}")
    print("=" * 50)
    print(f"Chords: {chords}")

    debug_info = debug_test_failure(test_name=test_name, chords=chords, **kwargs)

    print(
        f"\n✅ Debug analysis complete. Found {len(debug_info.get('analyses', {}))} analysis types."
    )


def run_progression_debug(chord_string: str, **kwargs):
    """Debug a chord progression with specified options."""
    chords = parse_chord_string(chord_string)

    print(f"\n🎵 DEBUGGING PROGRESSION: {chords}")
    print("=" * 50)

    debug_info = debug_progression(chords=chords, **kwargs)

    return debug_info


def list_all_capabilities():
    """List all available debug capabilities."""
    print("\n🛠️  UNIFIED DEBUG CAPABILITIES")
    print("=" * 50)

    print("\n📊 ANALYSIS TYPES:")
    print("  • patterns      - Pattern detection and matching")
    print("  • tokens        - Token stream analysis")
    print("  • stage-b       - Stage B event detection (Neapolitan, cadential 6/4)")
    print("  • backdoor      - Backdoor progression analysis (♭iv7-♭VII7-I)")
    print("  • intervals     - Interval and voice-leading analysis")
    print("  • trace         - Detailed pattern matching traces")

    print("\n🎵 COMMON DEBUG CASES:")
    for case_name in list_available_cases():
        case = get_case_by_name(case_name)
        print(f"  • {case_name:<20} - {case.description}")

    print("\n🧪 TEST INTEGRATION:")
    print("  • @debug_on_failure  - Auto-debug when test fails")
    print("  • @debug_always      - Always debug test")
    print("  • unified_debugger   - Pytest fixture")

    print("\n📁 LEGACY TOOLS (consolidated):")
    print("  • debug_patterns.py  -> patterns, tokens, trace")
    print("  • debug_stage_b.py   -> stage-b analysis")
    print("  • debug_backdoor.py  -> backdoor analysis")
    print("  • debug_intervals.py -> intervals analysis")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Unified Debug Tool for Harmonic Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Debug a chord progression with all analysis
  python tools/debug_unified.py --progression "Am F C G" --all

  # Run common debug case with additional analysis
  python tools/debug_unified.py --case pop_vi_IV_I_V --stage-b --backdoor

  # Debug test failure
  python tools/debug_unified.py --test-failure test_vi_IV_I_V "Am F C G" --profile pop

  # Interactive debugging
  python tools/debug_unified.py --interactive

  # List all capabilities
  python tools/debug_unified.py --list-capabilities
        """,
    )

    # Input modes (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--progression", "-p", help="Chord progression to debug (e.g., 'Am F C G')"
    )
    input_group.add_argument("--case", "-c", help="Run a common debug case by name")
    input_group.add_argument(
        "--test-failure",
        "-t",
        nargs=2,
        metavar=("TEST_NAME", "CHORDS"),
        help="Debug a test failure: test_name 'chord progression'",
    )
    input_group.add_argument(
        "--interactive", "-i", action="store_true", help="Interactive debugging session"
    )
    input_group.add_argument(
        "--list-cases", action="store_true", help="List available common debug cases"
    )
    input_group.add_argument(
        "--list-capabilities", action="store_true", help="List all debug capabilities"
    )

    # Analysis options
    parser.add_argument(
        "--profile",
        default="classical",
        choices=["classical", "pop", "jazz"],
        help="Analysis profile (default: classical)",
    )
    parser.add_argument("--key-hint", "-k", help="Key hint (e.g., 'C major')")

    # Analysis types
    parser.add_argument(
        "--patterns",
        action="store_true",
        help="Enable pattern analysis (default for progressions)",
    )
    parser.add_argument(
        "--tokens", action="store_true", help="Enable token stream analysis"
    )
    parser.add_argument(
        "--stage-b", action="store_true", help="Enable Stage B event analysis"
    )
    parser.add_argument(
        "--backdoor", action="store_true", help="Enable backdoor progression analysis"
    )
    parser.add_argument(
        "--intervals", action="store_true", help="Enable interval analysis"
    )
    parser.add_argument(
        "--trace", action="store_true", help="Enable detailed pattern tracing"
    )
    parser.add_argument("--all", action="store_true", help="Enable all analysis types")

    # Output options
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress verbose output"
    )
    parser.add_argument("--output", "-o", help="Save results to file")

    args = parser.parse_args()

    # Handle list commands
    if args.list_cases:
        print("Available debug cases:")
        for name in list_available_cases():
            case = get_case_by_name(name)
            print(f"  {name}: {case.description}")
        return

    if args.list_capabilities:
        list_all_capabilities()
        return

    # Set analysis flags
    if args.all:
        analyze_patterns = analyze_tokens = analyze_stage_b = True
        analyze_backdoor = analyze_intervals = args.trace = True
    else:
        analyze_patterns = args.patterns or args.progression or args.case
        analyze_tokens = args.tokens or args.progression or args.test_failure
        analyze_stage_b = args.stage_b
        analyze_backdoor = args.backdoor
        analyze_intervals = args.intervals

    # Handle different input modes
    if args.interactive:
        interactive_debug()

    elif args.progression:
        run_progression_debug(
            args.progression,
            profile=args.profile,
            key_hint=args.key_hint,
            trace=args.trace,
            analyze_all=args.all,
        )

    elif args.case:
        run_common_case(
            args.case,
            profile=args.profile,
            key_hint=args.key_hint,
            trace=args.trace,
            analyze_stage_b=analyze_stage_b,
            analyze_backdoor=analyze_backdoor,
            analyze_intervals=analyze_intervals,
        )

    elif args.test_failure:
        test_name, chord_string = args.test_failure
        run_test_failure_debug(
            test_name=test_name,
            chord_string=chord_string,
            profile=args.profile,
            key_hint=args.key_hint,
        )


if __name__ == "__main__":
    main()
