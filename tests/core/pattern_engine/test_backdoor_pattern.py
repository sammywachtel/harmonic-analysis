#!/usr/bin/env python3
"""
Test script to validate Backdoor cadence recognition.
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService


def test_backdoor():
    print("🎵 Testing Backdoor Cadence Recognition")
    print("=" * 50)

    service = PatternAnalysisService()

    # Test case from the plan
    test_progression = ["Fm7", "Bb7", "Cmaj7"]
    key_hint = "C major"
    profile = "jazz"

    print(f"Testing: {test_progression}")
    print(f"Key hint: {key_hint}")
    print(f"Profile: {profile}")

    try:
        result = service.analyze_with_patterns(
            chord_symbols=test_progression,
            profile=profile,
            best_cover=False,  # Show all matches
            key_hint=key_hint
        )

        print(f"\n🔍 Analysis Results:")
        print(f"Key detected: {result.get('functional_analysis', {}).get('key_center', 'unknown')}")
        print(f"Patterns found: {len(result.get('pattern_matches', []))}")

        # Look for backdoor pattern
        backdoor_found = False
        for match in result.get('pattern_matches', []):
            pattern_name = match.get('name', '').lower()
            pattern_id = match.get('id', '')
            if 'backdoor' in pattern_name or pattern_id == 'cadence_backdoor':
                print(f"✅ Found Backdoor: {match.get('name')} (ID: {pattern_id})")
                print(f"   Score: {match.get('score', 0):.2f}")
                backdoor_found = True

        if not backdoor_found:
            print("❌ Backdoor pattern not found!")
            print("\nAll patterns found:")
            for match in result.get('pattern_matches', []):
                print(f"   - {match.get('name', 'Unknown')}: {match.get('score', 0):.2f}")

        print(f"\n🎯 Tokens:")
        for i, token in enumerate(result.get('tokens', [])):
            print(f"   {i+1}. {token.get('roman', '?')} - {token.get('role', '?')}")

        return backdoor_found

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


if __name__ == "__main__":
    success = test_backdoor()
    sys.exit(0 if success else 1)
