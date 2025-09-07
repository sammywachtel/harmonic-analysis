#!/usr/bin/env python3
"""
Test Stage B Low-Level Event Detection

Tests the new event-based constraints for Neapolitan cadence,
cadential 6/4, and circle of fifths detection.
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService


def test_neapolitan_cadence():
    """Test Neapolitan cadence pattern with ♭2 in bass constraint."""
    print("🎵 Testing Neapolitan Cadence (♭2 in bass constraint)")
    print("=" * 60)

    service = PatternAnalysisService()

    # Test case: N6-V-I progression in C major
    # True Neapolitan uses ♭II chord with ♭2 in bass
    test_progression = ["Db", "G7", "C"]  # ♭II in C major
    key_hint = "C major"
    profile = "classical"

    print(f"Testing: {test_progression}")
    print(f"Key: {key_hint}")
    print(f"Profile: {profile}")

    try:
        result = service.analyze_with_patterns(
            chord_symbols=test_progression,
            profile=profile,
            best_cover=False,
            key_hint=key_hint
        )

        print(f"\n🔍 Analysis Results:")
        print(f"Key detected: {result.get('functional_analysis', {}).get('key_center', 'unknown')}")
        print(f"Patterns found: {len(result.get('pattern_matches', []))}")

        # Look for Neapolitan pattern
        neapolitan_found = False
        for match in result.get('pattern_matches', []):
            pattern_name = match.get('name', '').lower()
            pattern_id = match.get('pattern_id', '')
            if 'neapolitan' in pattern_name or pattern_id == 'neapolitan_cadence':
                print(f"✅ Found Neapolitan: {match.get('name')} (ID: {pattern_id})")
                print(f"   Score: {match.get('score', 0):.2f}")
                neapolitan_found = True

        if not neapolitan_found:
            print("❌ Neapolitan pattern not found!")

        # Show all patterns for debugging
        print(f"\n📊 All patterns found:")
        for match in result.get('pattern_matches', []):
            print(f"   - {match.get('name', 'Unknown')}: {match.get('score', 0):.2f}")

        return neapolitan_found

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cadential_64():
    """Test cadential 6/4 pattern with dominant bass constraint."""
    print("\n🎵 Testing Cadential 6/4 (I64 with dominant bass)")
    print("=" * 60)

    service = PatternAnalysisService()

    # Test case: I64-V-I progression in C major
    test_progression = ["C/G", "G7", "C"]  # C major with G in bass
    key_hint = "C major"
    profile = "classical"

    print(f"Testing: {test_progression}")
    print(f"Key: {key_hint}")
    print(f"Profile: {profile}")

    try:
        result = service.analyze_with_patterns(
            chord_symbols=test_progression,
            profile=profile,
            best_cover=False,
            key_hint=key_hint
        )

        print(f"\n🔍 Analysis Results:")
        print(f"Key detected: {result.get('functional_analysis', {}).get('key_center', 'unknown')}")
        print(f"Patterns found: {len(result.get('pattern_matches', []))}")

        # Look for cadential 64 pattern
        cad64_found = False
        for match in result.get('pattern_matches', []):
            pattern_name = match.get('name', '').lower()
            pattern_id = match.get('pattern_id', '')
            if 'cadential' in pattern_name or pattern_id == 'cadential_64_authentic':
                print(f"✅ Found Cadential 6/4: {match.get('name')} (ID: {pattern_id})")
                print(f"   Score: {match.get('score', 0):.2f}")
                cad64_found = True

        if not cad64_found:
            print("❌ Cadential 6/4 pattern not found!")

        # Show all patterns for debugging
        print(f"\n📊 All patterns found:")
        for match in result.get('pattern_matches', []):
            print(f"   - {match.get('name', 'Unknown')}: {match.get('score', 0):.2f}")

        return cad64_found

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_circle_of_fifths():
    """Test circle of fifths sequence with chain descriptor."""
    print("\n🎵 Testing Circle of Fifths (≥3 links)")
    print("=" * 60)

    service = PatternAnalysisService()

    # Test case: classic circle of fifths progression
    test_progression = ["Am", "Dm", "G7", "C"]  # vi-ii-V-I in C major
    key_hint = "C major"
    profile = "classical"

    print(f"Testing: {test_progression}")
    print(f"Key: {key_hint}")
    print(f"Profile: {profile}")

    try:
        result = service.analyze_with_patterns(
            chord_symbols=test_progression,
            profile=profile,
            best_cover=False,
            key_hint=key_hint
        )

        print(f"\n🔍 Analysis Results:")
        print(f"Key detected: {result.get('functional_analysis', {}).get('key_center', 'unknown')}")
        print(f"Patterns found: {len(result.get('pattern_matches', []))}")

        # Look for circle of fifths pattern
        circle5_found = False
        for match in result.get('pattern_matches', []):
            pattern_name = match.get('name', '').lower()
            pattern_id = match.get('pattern_id', '')
            if 'circle' in pattern_name or pattern_id == 'circle_of_fifths_sequence':
                print(f"✅ Found Circle of Fifths: {match.get('name')} (ID: {pattern_id})")
                print(f"   Score: {match.get('score', 0):.2f}")
                circle5_found = True

        if not circle5_found:
            print("❌ Circle of fifths pattern not found!")

        # Show all patterns for debugging
        print(f"\n📊 All patterns found:")
        for match in result.get('pattern_matches', []):
            print(f"   - {match.get('name', 'Unknown')}: {match.get('score', 0):.2f}")

        return circle5_found

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("🚀 Stage B Low-Level Event Detection Tests")
    print("=" * 70)

    # Run all tests
    tests = [
        ("Neapolitan Cadence", test_neapolitan_cadence),
        ("Cadential 6/4", test_cadential_64),
        ("Circle of Fifths", test_circle_of_fifths),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print(f"\n🎯 Test Summary:")
    print("=" * 50)
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1

    print(f"\nOverall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All Stage B tests passed! Event constraints working correctly.")
    else:
        print("⚠️  Some tests failed - check implementation.")

    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
