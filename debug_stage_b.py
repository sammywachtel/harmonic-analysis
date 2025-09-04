#!/usr/bin/env python3
"""
Debug Stage B Event Detection
"""

import sys
import os
import asyncio

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from harmonic_analysis.core.functional_harmony import FunctionalHarmonyAnalyzer
from harmonic_analysis.core.pattern_engine.token_converter import TokenConverter
from harmonic_analysis.core.pattern_engine.low_level_events import LowLevelEventExtractor, get_circle_of_fifths_descriptor


async def debug_neapolitan():
    print("🔍 Debug Neapolitan Cadence Events")
    print("=" * 50)

    analyzer = FunctionalHarmonyAnalyzer()
    converter = TokenConverter()
    event_extractor = LowLevelEventExtractor()

    chord_symbols = ["Db", "G7", "C"]  # True Neapolitan: ♭II6 = Db with F in bass, but let's try simple ♭II
    key_hint = "C major"

    print(f"Chord symbols: {chord_symbols}")
    print(f"Key: {key_hint}")

    # Get functional analysis
    result = await analyzer.analyze_functionally(
        chord_symbols, key_hint=key_hint, lock_key=True
    )

    # Convert to tokens
    tokens = converter.convert_analysis_to_tokens(chord_symbols, result)

    # Extract events
    events = event_extractor.extract_events(tokens, chord_symbols, result.key_center)

    print(f"\n🎵 Functional Analysis:")
    for i, chord in enumerate(result.chords):
        print(f"  {i+1}. {chord.chord_symbol} → {chord.roman_numeral}")

    print(f"\n🎯 Tokens:")
    for i, token in enumerate(tokens):
        print(f"  {i+1}. Roman: {token.roman}, Role: {token.role}")

    print(f"\n📊 Events:")
    print(f"Bass degrees: {events.bass_degree}")
    print(f"Root motion: {events.root_motion}")
    print(f"Cadential 64: {events.has_cadential64}")

    # Check if ♭2 in bass is detected
    has_flat2 = '♭2' in events.bass_degree
    print(f"\n🎵 Neapolitan Analysis:")
    print(f"Has ♭2 in bass: {has_flat2}")
    if has_flat2:
        pos = events.bass_degree.index('♭2')
        print(f"♭2 at position: {pos}")


async def debug_circle_of_fifths():
    print("\n🔍 Debug Circle of Fifths Events")
    print("=" * 50)

    analyzer = FunctionalHarmonyAnalyzer()
    converter = TokenConverter()
    event_extractor = LowLevelEventExtractor()

    chord_symbols = ["Am", "Dm", "G7", "C"]
    key_hint = "C major"

    print(f"Chord symbols: {chord_symbols}")
    print(f"Key: {key_hint}")

    # Get functional analysis
    result = await analyzer.analyze_functionally(
        chord_symbols, key_hint=key_hint, lock_key=True
    )

    # Convert to tokens
    tokens = converter.convert_analysis_to_tokens(chord_symbols, result)

    # Extract events
    events = event_extractor.extract_events(tokens, chord_symbols, result.key_center)

    print(f"\n🎵 Functional Analysis:")
    for i, chord in enumerate(result.chords):
        print(f"  {i+1}. {chord.chord_symbol} → {chord.roman_numeral}")

    print(f"\n🎯 Tokens:")
    for i, token in enumerate(tokens):
        print(f"  {i+1}. Roman: {token.roman}, Role: {token.role}, Bass motion: {token.bass_motion_from_prev}")

    print(f"\n📊 Events:")
    print(f"Root motion: {events.root_motion}")

    # Test circle of fifths descriptor
    descriptor = get_circle_of_fifths_descriptor(events, min_length=3)
    print(f"\n🎵 Circle of Fifths Analysis:")
    print(f"Descriptor: {descriptor}")


async def debug_cadential_64():
    print("\n🔍 Debug Cadential 6/4 Events (Working)")
    print("=" * 50)

    analyzer = FunctionalHarmonyAnalyzer()
    converter = TokenConverter()
    event_extractor = LowLevelEventExtractor()

    chord_symbols = ["C/G", "G7", "C"]
    key_hint = "C major"

    print(f"Chord symbols: {chord_symbols}")
    print(f"Key: {key_hint}")

    # Get functional analysis
    result = await analyzer.analyze_functionally(
        chord_symbols, key_hint=key_hint, lock_key=True
    )

    # Convert to tokens
    tokens = converter.convert_analysis_to_tokens(chord_symbols, result)

    # Extract events
    events = event_extractor.extract_events(tokens, chord_symbols, result.key_center)

    print(f"\n🎵 Functional Analysis:")
    for i, chord in enumerate(result.chords):
        print(f"  {i+1}. {chord.chord_symbol} → {chord.roman_numeral}")

    print(f"\n🎯 Tokens:")
    for i, token in enumerate(tokens):
        print(f"  {i+1}. Roman: {token.roman}, Role: {token.role}")

    print(f"\n📊 Events:")
    print(f"Bass degrees: {events.bass_degree}")
    print(f"Cadential 64: {events.has_cadential64}")

    print(f"\n🎵 Cadential 6/4 Analysis:")
    print(f"Expected: I64 with 5th degree in bass and dominant function")


async def main():
    print("🚀 Stage B Event Detection Debug")
    print("=" * 70)

    await debug_neapolitan()
    await debug_circle_of_fifths()
    await debug_cadential_64()


if __name__ == "__main__":
    asyncio.run(main())
