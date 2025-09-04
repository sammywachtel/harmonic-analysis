#!/usr/bin/env python3
"""
Debug script for Backdoor cadence recognition.
"""

import sys
import os
import asyncio

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from harmonic_analysis.core.functional_harmony import FunctionalHarmonyAnalyzer
from harmonic_analysis.core.pattern_engine.token_converter import TokenConverter


async def debug_backdoor():
    print("🔍 Debug Backdoor Cadence Recognition")
    print("=" * 50)

    # Test the functional analyzer directly
    analyzer = FunctionalHarmonyAnalyzer()
    converter = TokenConverter()

    chord_symbols = ["Fm7", "Bb7", "Cmaj7"]
    key_hint = "C major"

    print(f"Chord symbols: {chord_symbols}")
    print(f"Key hint: {key_hint}")

    # Test functional analysis
    print("\n🎵 Functional Analysis:")
    result = await analyzer.analyze_functionally(
        chord_symbols, key_hint=key_hint, lock_key=True
    )

    print(f"Key center: {result.key_center}")
    print(f"Key source: {result.key_source}")
    print(f"Key locked: {result.key_locked}")
    print(f"Mode: {result.mode}")

    print("\nChord analysis:")
    for i, chord in enumerate(result.chords):
        print(f"  {i+1}. {chord.chord_symbol} → {chord.roman_numeral} ({chord.function})")

    # Test token conversion
    print("\n🎯 Token Conversion:")
    tokens = converter.convert_analysis_to_tokens(chord_symbols, result)

    for i, token in enumerate(tokens):
        print(f"  {i+1}. Roman: {token.roman}, Role: {token.role}, Flags: {token.flags}")

    # Manual theory check
    print("\n🧮 Music Theory Check:")
    print("In C major:")
    print("  F = 4th degree = iv (minor fourth)")
    print("  Bb = b7th degree = bVII (flat seventh)")
    print("  C = 1st degree = I (tonic)")
    print("\nExpected romans: iv7 - bVII7 - Imaj7")
    print(f"Actual romans:   {' - '.join([t.roman for t in tokens])}")


if __name__ == "__main__":
    asyncio.run(debug_backdoor())
