#!/usr/bin/env python3
"""Debug script to understand pattern matching results."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService
import json


def main():
    print("🔍 Pattern Engine Debug Analysis")
    print("=" * 50)

    service = PatternAnalysisService()

    test_cases = [
        {
            "name": "vi-IV-I-V Pop Progression",
            "chords": ["Am", "F", "C", "G"]
        },
        {
            "name": "ii-V-I Jazz Progression",
            "chords": ["Dm7", "G7", "Cmaj7"]
        },
        {
            "name": "Perfect Authentic Cadence",
            "chords": ["F", "G7", "C"]
        }
    ]

    for test_case in test_cases:
        print(f"\n🎼 Analyzing: {test_case['name']}")
        print(f"   Chords: {test_case['chords']}")

        try:
            result = service.analyze_with_patterns(test_case["chords"])

            print(f"   Key detected: {result.get('functional_analysis', {}).get('key_center', 'unknown')}")

            # Show tokens with detailed function info
            tokens = result.get('tokens', [])
            functional = result.get('functional_analysis', {})
            chords_analysis = functional.get('chords', [])

            print(f"   Tokens generated: {len(tokens)}")
            for i, (token, chord_analysis) in enumerate(zip(tokens, chords_analysis)):
                function_str = chord_analysis.get('function', 'unknown') if i < len(chords_analysis) else 'unknown'
                print(f"     {i+1}. {token.get('roman', '?')} ({token.get('role', '?')}) - function={function_str} - {token.get('flags', [])}")

            # Show pattern matches
            matches = result.get('pattern_matches', [])
            print(f"   Pattern matches: {len(matches)}")
            for match in matches:
                print(f"     - {match.get('name', 'Unknown')}: score={match.get('score', 0):.2f}")
                print(f"       family={match.get('family', 'unknown')}, start={match.get('start', 0)}, end={match.get('end', 0)}")
                if 'evidence' in match:
                    print(f"       evidence={match['evidence']}")

            # Show functional analysis details
            functional = result.get('functional_analysis', {})
            print(f"   Functional analysis:")
            print(f"     confidence: {functional.get('confidence', 0):.2f}")
            print(f"     explanation: {functional.get('explanation', 'none')}")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
