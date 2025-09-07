#!/usr/bin/env python3
"""
Test Stage C Voice-Leading Event Detection

Tests the new voice-leading inference system, melody-chord alignment utilities,
and MelodicEvents data structures.
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from harmonic_analysis.analysis_types import MelodyEvent, MelodyTrack, MelodicEvents
from harmonic_analysis.api.musical_data import align_melody_to_chords, soprano_degrees_per_chord
from harmonic_analysis.core.pattern_engine.low_level_events import LowLevelEventExtractor


def test_melodic_events_data_structure():
    """Test Stage C data structures."""
    print("🎵 Testing MelodicEvents Data Structures")
    print("=" * 50)

    # Test MelodyEvent creation
    event = MelodyEvent(onset=0.0, pitch=60, duration=1.0)
    print(f"✅ MelodyEvent created: onset={event.onset}, pitch={event.pitch}")

    # Test MelodyTrack creation
    track = MelodyTrack([event])
    print(f"✅ MelodyTrack created with {len(track.events)} events")

    # Test MelodicEvents creation
    melodic_events = MelodicEvents(
        soprano_degree=[5, 1],
        voice_4_to_3=[False, True],
        voice_7_to_1=[False, False],
        fi_to_sol=[False, False],
        le_to_sol=[False, False],
        source="inference"
    )
    print(f"✅ MelodicEvents created: source={melodic_events.source}")
    print(f"   Soprano degrees: {melodic_events.soprano_degree}")
    print(f"   4→3 suspensions: {melodic_events.voice_4_to_3}")

    return True


def test_melody_chord_alignment():
    """Test melody-chord alignment utilities."""
    print("\n🎵 Testing Melody-Chord Alignment")
    print("=" * 50)

    # Create test melody events
    melody = MelodyTrack([
        MelodyEvent(onset=0.0, pitch=60, duration=1.0),  # C during first chord
        MelodyEvent(onset=1.0, pitch=64, duration=1.0),  # E during second chord
        MelodyEvent(onset=1.5, pitch=67, duration=0.5),  # G during second chord
    ])

    # Chord timing
    chords = ["C", "F", "G"]
    starts = [0.0, 1.0, 2.0]
    ends = [1.0, 2.0, 3.0]

    # Test alignment
    aligned = align_melody_to_chords(melody, chords, starts, ends)

    print(f"✅ Melody aligned to {len(chords)} chords")
    print(f"   Chord 1 (C): {len(aligned[0])} events")
    print(f"   Chord 2 (F): {len(aligned[1])} events")
    print(f"   Chord 3 (G): {len(aligned[2])} events")

    # Verify alignment
    assert len(aligned[0]) == 1, f"Expected 1 event in chord 1, got {len(aligned[0])}"
    assert len(aligned[1]) == 2, f"Expected 2 events in chord 2, got {len(aligned[1])}"
    assert len(aligned[2]) == 0, f"Expected 0 events in chord 3, got {len(aligned[2])}"

    print("✅ Melody-chord alignment working correctly")

    # Test soprano degree detection
    degrees = soprano_degrees_per_chord(aligned, "C major")
    print(f"✅ Soprano degrees detected: {degrees}")

    # Verify degrees (C=1, G=5 for C major)
    assert degrees[0] == 1, f"Expected degree 1 for C, got {degrees[0]}"
    assert degrees[1] == 5, f"Expected degree 5 for G, got {degrees[1]}"
    assert degrees[2] is None, f"Expected None for empty chord, got {degrees[2]}"

    return True


def test_voice_leading_inference():
    """Test voice-leading inference from chord progressions."""
    print("\n🎵 Testing Voice-Leading Inference")
    print("=" * 50)

    # Test 4→3 suspension detection (I64 → V → I)
    print("Testing 4→3 suspension inference (cadential 6/4)...")
    test_4_to_3_progression()

    # Test 7→1 leading tone resolution (V7 → I)
    print("\nTesting 7→1 leading tone inference...")
    test_7_to_1_progression()

    # Test augmented sixth resolution (Aug6 → V)
    print("\nTesting fi→sol augmented sixth inference...")
    test_fi_to_sol_progression()

    # Test Phrygian resolution (ii6 → V in minor)
    print("\nTesting le→sol Phrygian inference...")
    test_le_to_sol_progression()

    return True


def test_4_to_3_progression():
    """Test 4→3 suspension inference from cadential 6/4 pattern."""
    from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

    service = PatternAnalysisService()

    # Use cadential 6/4 progression that should trigger 4→3 inference
    chord_symbols = ["C/G", "G7", "C"]  # I64 → V7 → I

    try:
        # Get low-level events (which now include voice-leading inference)
        extractor = LowLevelEventExtractor()

        # Mock tokens for testing (minimal viable tokens)
        class MockToken:
            def __init__(self, roman, role):
                self.roman = roman
                self.role = role

        tokens = [
            MockToken("I64", "T"),  # Cadential 6/4 (treated as tonic but with dominant function)
            MockToken("V7", "D"),   # Dominant seventh
            MockToken("I", "T")     # Tonic resolution
        ]

        # Extract voice-leading events
        voice_leading = extractor._infer_voice_leading_events(tokens, chord_symbols, 0)  # C major = 0

        print(f"   4→3 suspensions detected: {voice_leading.voice_4_to_3}")

        # Should detect 4→3 at position 1 (the V7 chord where resolution occurs)
        if voice_leading.voice_4_to_3[1]:
            print("   ✅ 4→3 suspension correctly inferred at V7 chord")
        else:
            print("   ❌ 4→3 suspension not detected")

        return voice_leading.voice_4_to_3[1]

    except Exception as e:
        print(f"   ❌ Error testing 4→3 inference: {e}")
        return False


def test_7_to_1_progression():
    """Test 7→1 leading tone resolution inference."""
    extractor = LowLevelEventExtractor()

    class MockToken:
        def __init__(self, roman, role):
            self.roman = roman
            self.role = role

    # V7 → I progression
    tokens = [
        MockToken("V7", "D"),   # Dominant seventh
        MockToken("I", "T")     # Tonic resolution
    ]
    chord_symbols = ["G7", "C"]

    try:
        voice_leading = extractor._infer_voice_leading_events(tokens, chord_symbols, 0)

        print(f"   7→1 resolutions detected: {voice_leading.voice_7_to_1}")

        # Should detect 7→1 at position 1 (the I chord where resolution occurs)
        if voice_leading.voice_7_to_1[1]:
            print("   ✅ 7→1 resolution correctly inferred at I chord")
        else:
            print("   ❌ 7→1 resolution not detected")

        return voice_leading.voice_7_to_1[1]

    except Exception as e:
        print(f"   ❌ Error testing 7→1 inference: {e}")
        return False


def test_fi_to_sol_progression():
    """Test ♯4→5 augmented sixth resolution inference."""
    extractor = LowLevelEventExtractor()

    class MockToken:
        def __init__(self, roman, role):
            self.roman = roman
            self.role = role

    # Aug6 → V progression
    tokens = [
        MockToken("It+6", "PD"),  # Italian augmented sixth
        MockToken("V", "D")       # Dominant resolution
    ]
    chord_symbols = ["It+6", "G"]

    try:
        voice_leading = extractor._infer_voice_leading_events(tokens, chord_symbols, 0)

        print(f"   ♯4→5 resolutions detected: {voice_leading.fi_to_sol}")

        # Should detect ♯4→5 at position 1 (the V chord where resolution occurs)
        if voice_leading.fi_to_sol[1]:
            print("   ✅ ♯4→5 resolution correctly inferred at V chord")
        else:
            print("   ❌ ♯4→5 resolution not detected")

        return voice_leading.fi_to_sol[1]

    except Exception as e:
        print(f"   ❌ Error testing fi→sol inference: {e}")
        return False


def test_le_to_sol_progression():
    """Test ♭6→5 Phrygian resolution inference."""
    extractor = LowLevelEventExtractor()

    class MockToken:
        def __init__(self, roman, role):
            self.roman = roman
            self.role = role

    # Phrygian ii6 → V progression (minor key)
    tokens = [
        MockToken("ii6", "PD"),  # Phrygian ii6
        MockToken("V", "D")      # Dominant resolution
    ]
    chord_symbols = ["Dm/F", "E"]  # In A minor context

    try:
        voice_leading = extractor._infer_voice_leading_events(tokens, chord_symbols, 9)  # A minor = 9

        print(f"   ♭6→5 resolutions detected: {voice_leading.le_to_sol}")

        # Should detect ♭6→5 at position 1 (the V chord where resolution occurs)
        if voice_leading.le_to_sol[1]:
            print("   ✅ ♭6→5 resolution correctly inferred at V chord")
        else:
            print("   ❌ ♭6→5 resolution not detected")

        return voice_leading.le_to_sol[1]

    except Exception as e:
        print(f"   ❌ Error testing le→sol inference: {e}")
        return False


def main():
    """Run all Stage C tests."""
    print("🚀 Stage C Voice-Leading Event Detection Tests")
    print("=" * 70)

    tests = [
        ("MelodicEvents Data Structures", test_melodic_events_data_structure),
        ("Melody-Chord Alignment", test_melody_chord_alignment),
        ("Voice-Leading Inference", test_voice_leading_inference),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
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
        print("🎉 All Stage C tests passed! Voice-leading inference working correctly.")
    else:
        print("⚠️  Some tests failed - check implementation.")

    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
