"""
Test Suite for Stage C Voice-Leading Event Detection

Comprehensive tests for voice-leading inference, melody-chord alignment,
and MelodicEvents data structures.
"""

import pathlib
import sys

import pytest

# Ensure project root on sys.path
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harmonic_analysis.analysis_types import (  # noqa: E402
    MelodicEvents,
    MelodyEvent,
    MelodyTrack,
)
from harmonic_analysis.api.musical_data import (  # noqa: E402
    align_melody_to_chords,
    soprano_degrees_per_chord,
)
from harmonic_analysis.core.pattern_engine.low_level_events import (  # noqa: E402
    LowLevelEventExtractor,
)

# =============================================================================
# TEST DATA: Voice-Leading Inference Test Cases
# =============================================================================

VOICE_LEADING_TEST_CASES = [
    {
        "name": "4_to_3_suspension_cadential_64",
        "description": "Classic 4→3 suspension from cadential 6/4",
        "chord_symbols": ["C/G", "G7", "C"],
        "tokens": [
            {"roman": "I64", "role": "T"},
            {"roman": "V7", "role": "D"},
            {"roman": "I", "role": "T"},
        ],
        "expected_voice_4_to_3": [False, True, False],
        "resolution_position": 1,
        "pattern_type": "suspension",
    },
    {
        "name": "7_to_1_leading_tone_resolution",
        "description": "Leading tone resolution in V7→I",
        "chord_symbols": ["F", "G7", "C"],
        "tokens": [
            {"roman": "IV", "role": "PD"},
            {"roman": "V7", "role": "D"},
            {"roman": "I", "role": "T"},
        ],
        "expected_voice_7_to_1": [False, False, True],
        "resolution_position": 2,
        "pattern_type": "leading_tone",
    },
    {
        "name": "augmented_sixth_resolution",
        "description": "♯4→5 resolution from Italian augmented sixth",
        "chord_symbols": ["C", "It+6", "G7", "C"],
        "tokens": [
            {"roman": "I", "role": "T"},
            {"roman": "It+6", "role": "PD"},
            {"roman": "V7", "role": "D"},
            {"roman": "I", "role": "T"},
        ],
        "expected_fi_to_sol": [False, False, True, False],
        "resolution_position": 2,
        "pattern_type": "augmented_sixth",
    },
    {
        "name": "phrygian_resolution_minor",
        "description": "♭6→5 resolution from Phrygian ii6 in minor",
        "chord_symbols": ["Am", "Dm/F", "E7", "Am"],
        "tokens": [
            {"roman": "i", "role": "T"},
            {"roman": "ii6", "role": "PD"},
            {"roman": "V7", "role": "D"},
            {"roman": "i", "role": "T"},
        ],
        "expected_le_to_sol": [False, False, True, False],
        "resolution_position": 2,
        "pattern_type": "phrygian",
        "key": "A minor",
    },
    {
        "name": "french_augmented_sixth",
        "description": "♯4→5 resolution from French augmented sixth",
        "chord_symbols": ["C", "Fr+6", "G", "C"],
        "tokens": [
            {"roman": "I", "role": "T"},
            {"roman": "Fr+6", "role": "PD"},
            {"roman": "V", "role": "D"},
            {"roman": "I", "role": "T"},
        ],
        "expected_fi_to_sol": [False, False, True, False],
        "resolution_position": 2,
        "pattern_type": "augmented_sixth",
    },
    {
        "name": "german_augmented_sixth",
        "description": "♯4→5 resolution from German augmented sixth",
        "chord_symbols": ["Bb", "Ger+6", "F", "Bb"],
        "tokens": [
            {"roman": "I", "role": "T"},
            {"roman": "Ger+6", "role": "PD"},
            {"roman": "V", "role": "D"},
            {"roman": "I", "role": "T"},
        ],
        "expected_fi_to_sol": [False, False, True, False],
        "resolution_position": 2,
        "pattern_type": "augmented_sixth",
    },
    {
        "name": "multiple_voice_leading_events",
        "description": "Complex progression with multiple voice-leading events",
        "chord_symbols": ["C/G", "G7", "C", "Fr+6", "G7", "C"],
        "tokens": [
            {"roman": "I64", "role": "T"},
            {"roman": "V7", "role": "D"},
            {"roman": "I", "role": "T"},
            {"roman": "Fr+6", "role": "PD"},
            {"roman": "V7", "role": "D"},
            {"roman": "I", "role": "T"},
        ],
        "expected_voice_4_to_3": [False, True, False, False, False, False],
        "expected_voice_7_to_1": [False, False, True, False, False, True],
        "expected_fi_to_sol": [False, False, False, False, True, False],
        "pattern_type": "complex",
    },
]

# =============================================================================
# TEST DATA: Melody-Chord Alignment Test Cases
# =============================================================================

MELODY_ALIGNMENT_TEST_CASES = [
    {
        "name": "simple_melody_alignment",
        "description": "Basic melody aligned to chord changes",
        "melody_events": [
            {"onset": 0.0, "pitch": 60, "duration": 1.0},  # C
            {"onset": 1.0, "pitch": 64, "duration": 1.0},  # E
            {"onset": 2.0, "pitch": 67, "duration": 1.0},  # G
        ],
        "chords": ["C", "F", "G"],
        "chord_starts": [0.0, 1.0, 2.0],
        "chord_ends": [1.0, 2.0, 3.0],
        "expected_alignment": [1, 1, 1],  # events per chord
        "expected_degrees": [1, 3, 5],  # scale degrees in C major (C=1, E=3, G=5)
        "key": "C major",
    },
    {
        "name": "overlapping_melody_events",
        "description": "Melody events overlapping chord boundaries",
        "melody_events": [
            {"onset": 0.5, "pitch": 67, "duration": 1.0},  # G overlaps chords 1&2
            {"onset": 1.5, "pitch": 72, "duration": 1.5},  # C overlaps chords 2&3
        ],
        "chords": ["C", "Am", "F"],
        "chord_starts": [0.0, 1.0, 2.0],
        "chord_ends": [1.0, 2.0, 3.0],
        "expected_alignment": [1, 2, 1],  # events per chord (overlap counted twice)
        "expected_degrees": [5, 1, 1],  # highest pitch per chord
        "key": "C major",
    },
    {
        "name": "complex_rhythm_melody",
        "description": "Complex rhythmic melody with multiple events per chord",
        "melody_events": [
            {"onset": 0.0, "pitch": 60, "duration": 0.5},  # C
            {"onset": 0.5, "pitch": 64, "duration": 0.5},  # E
            {"onset": 1.0, "pitch": 67, "duration": 0.25},  # G
            {"onset": 1.25, "pitch": 72, "duration": 0.75},  # C
            {"onset": 2.0, "pitch": 69, "duration": 1.0},  # A
        ],
        "chords": ["C", "F", "Am"],
        "chord_starts": [0.0, 1.0, 2.0],
        "chord_ends": [1.0, 2.0, 3.0],
        "expected_alignment": [2, 2, 1],  # events per chord
        "expected_degrees": [3, 1, 6],  # scale degrees (E, C, A)
        "key": "C major",
    },
    {
        "name": "empty_melody_handling",
        "description": "Handling empty or None melody gracefully",
        "melody_events": [],
        "chords": ["C", "F", "G"],
        "chord_starts": [0.0, 1.0, 2.0],
        "chord_ends": [1.0, 2.0, 3.0],
        "expected_alignment": [0, 0, 0],
        "expected_degrees": [None, None, None],
        "key": "C major",
    },
]


# =============================================================================
# TEST UTILITIES
# =============================================================================


class MockToken:
    """Mock token for testing voice-leading inference."""

    def __init__(self, roman: str, role: str):
        self.roman = roman
        self.role = role
        # Add default attributes that LowLevelEventExtractor expects
        self.bass_motion_from_prev = None
        self.flags = []
        self.mode = None
        self.secondary_of = None
        self.soprano_degree = None


def create_mock_tokens(token_specs):
    """Create list of mock tokens from specifications."""
    return [MockToken(spec["roman"], spec["role"]) for spec in token_specs]


def create_melody_track(event_specs):
    """Create MelodyTrack from event specifications."""
    events = [
        MelodyEvent(onset=spec["onset"], pitch=spec["pitch"], duration=spec["duration"])
        for spec in event_specs
    ]
    return MelodyTrack(events)


# =============================================================================
# VOICE-LEADING INFERENCE TESTS
# =============================================================================


@pytest.mark.parametrize(
    "case", VOICE_LEADING_TEST_CASES, ids=[c["name"] for c in VOICE_LEADING_TEST_CASES]
)
def test_voice_leading_inference(case):
    """Test voice-leading inference from chord progression patterns."""
    extractor = LowLevelEventExtractor()
    tokens = create_mock_tokens(case["tokens"])
    chord_symbols = case["chord_symbols"]

    # Get key for pitch class calculation
    key = case.get("key", "C major")
    tonic_pc = 0 if "C" in key else 9 if "A" in key else 10 if "Bb" in key else 0

    # Run inference
    melodic_events = extractor._infer_voice_leading_events(
        tokens, chord_symbols, tonic_pc
    )

    # Verify source is inference
    assert (
        melodic_events.source == "inference"
    ), f"Expected source='inference', got '{melodic_events.source}'"

    # Check expected voice-leading events
    if "expected_voice_4_to_3" in case:
        assert (
            melodic_events.voice_4_to_3 == case["expected_voice_4_to_3"]
        ), f"4→3 mismatch: expected {case['expected_voice_4_to_3']}, got {melodic_events.voice_4_to_3}"

    if "expected_voice_7_to_1" in case:
        assert (
            melodic_events.voice_7_to_1 == case["expected_voice_7_to_1"]
        ), f"7→1 mismatch: expected {case['expected_voice_7_to_1']}, got {melodic_events.voice_7_to_1}"

    if "expected_fi_to_sol" in case:
        assert (
            melodic_events.fi_to_sol == case["expected_fi_to_sol"]
        ), f"♯4→5 mismatch: expected {case['expected_fi_to_sol']}, got {melodic_events.fi_to_sol}"

    if "expected_le_to_sol" in case:
        assert (
            melodic_events.le_to_sol == case["expected_le_to_sol"]
        ), f"♭6→5 mismatch: expected {case['expected_le_to_sol']}, got {melodic_events.le_to_sol}"

    # Verify resolution occurs at expected position
    if "resolution_position" in case:
        pos = case["resolution_position"]
        pattern_type = case["pattern_type"]

        if pattern_type == "suspension":
            assert melodic_events.voice_4_to_3[
                pos
            ], f"Expected 4→3 resolution at position {pos}"
        elif pattern_type == "leading_tone":
            assert melodic_events.voice_7_to_1[
                pos
            ], f"Expected 7→1 resolution at position {pos}"
        elif pattern_type == "augmented_sixth":
            assert melodic_events.fi_to_sol[
                pos
            ], f"Expected ♯4→5 resolution at position {pos}"
        elif pattern_type == "phrygian":
            assert melodic_events.le_to_sol[
                pos
            ], f"Expected ♭6→5 resolution at position {pos}"


# =============================================================================
# MELODY-CHORD ALIGNMENT TESTS
# =============================================================================


@pytest.mark.parametrize(
    "case",
    MELODY_ALIGNMENT_TEST_CASES,
    ids=[c["name"] for c in MELODY_ALIGNMENT_TEST_CASES],
)
def test_melody_chord_alignment(case):
    """Test melody-chord alignment utilities."""
    melody_track = create_melody_track(case["melody_events"])
    chords = case["chords"]
    starts = case["chord_starts"]
    ends = case["chord_ends"]

    # Test alignment
    aligned = align_melody_to_chords(melody_track, chords, starts, ends)

    # Check alignment structure
    assert len(aligned) == len(
        chords
    ), f"Expected {len(chords)} chord groups, got {len(aligned)}"

    # Check event counts per chord
    actual_counts = [len(group) for group in aligned]
    expected_counts = case["expected_alignment"]
    assert (
        actual_counts == expected_counts
    ), f"Event count mismatch: expected {expected_counts}, got {actual_counts}"

    # Test soprano degree detection
    degrees = soprano_degrees_per_chord(aligned, case["key"])
    expected_degrees = case["expected_degrees"]

    assert len(degrees) == len(
        expected_degrees
    ), f"Degree count mismatch: expected {len(expected_degrees)}, got {len(degrees)}"

    for i, (actual, expected) in enumerate(zip(degrees, expected_degrees)):
        assert (
            actual == expected
        ), f"Degree mismatch at chord {i}: expected {expected}, got {actual}"


# =============================================================================
# DATA STRUCTURE TESTS
# =============================================================================


def test_melody_event_creation():
    """Test MelodyEvent data structure."""
    event = MelodyEvent(onset=0.0, pitch=60, duration=1.0, ppq=480, bar_offset=0.0)
    assert event.onset == 0.0
    assert event.pitch == 60
    assert event.duration == 1.0
    assert event.ppq == 480
    assert event.bar_offset == 0.0


def test_melody_track_creation():
    """Test MelodyTrack data structure."""
    events = [
        MelodyEvent(onset=0.0, pitch=60, duration=1.0),
        MelodyEvent(onset=1.0, pitch=64, duration=1.0),
    ]
    track = MelodyTrack(events)
    assert len(track.events) == 2
    assert track.events[0].pitch == 60
    assert track.events[1].pitch == 64


def test_melodic_events_creation():
    """Test MelodicEvents data structure."""
    melodic_events = MelodicEvents(
        soprano_degree=[1, 3, 5],
        voice_4_to_3=[False, True, False],
        voice_7_to_1=[False, False, True],
        fi_to_sol=[False, False, False],
        le_to_sol=[False, False, False],
        source="inference",
    )

    assert len(melodic_events.soprano_degree) == 3
    assert melodic_events.voice_4_to_3 == [False, True, False]
    assert melodic_events.voice_7_to_1 == [False, False, True]
    assert melodic_events.source == "inference"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


def test_voice_leading_integration_with_low_level_events():
    """Test that voice-leading events integrate properly with LowLevelEvents."""
    from harmonic_analysis.core.pattern_engine.low_level_events import LowLevelEvents

    extractor = LowLevelEventExtractor()

    # Create test tokens
    tokens = [MockToken("I64", "T"), MockToken("V7", "D"), MockToken("I", "T")]
    chord_symbols = ["C/G", "G7", "C"]
    key_center = "C major"

    # Extract all events (including voice-leading)
    events = extractor.extract_events(tokens, chord_symbols, key_center)

    # Verify structure
    assert isinstance(events, LowLevelEvents)
    assert len(events.voice_4_to_3) == len(tokens)
    assert len(events.voice_7_to_1) == len(tokens)
    assert len(events.fi_to_sol) == len(tokens)
    assert len(events.le_to_sol) == len(tokens)

    # Verify voice-leading inference worked
    assert events.voice_4_to_3[1] is True, "Expected 4→3 suspension at V7"
    assert events.voice_7_to_1[2] is True, "Expected 7→1 resolution at I"


def test_empty_input_handling():
    """Test graceful handling of empty inputs."""
    extractor = LowLevelEventExtractor()

    # Empty tokens
    empty_events = extractor._infer_voice_leading_events([], [], 0)
    assert len(empty_events.voice_4_to_3) == 0
    assert len(empty_events.voice_7_to_1) == 0
    assert empty_events.source == "inference"

    # Empty melody alignment
    empty_melody = MelodyTrack([])
    aligned = align_melody_to_chords(empty_melody, ["C", "F"], [0.0, 1.0], [1.0, 2.0])
    assert len(aligned) == 2
    assert all(len(group) == 0 for group in aligned)

    # None melody handling
    aligned_none = align_melody_to_chords(None, ["C"], [0.0], [1.0])
    assert len(aligned_none) == 1
    assert len(aligned_none[0]) == 0


# =============================================================================
# PERFORMANCE AND EDGE CASE TESTS
# =============================================================================


def test_large_sequence_performance():
    """Test performance with large sequences."""
    extractor = LowLevelEventExtractor()

    # Create large sequence
    num_chords = 100
    tokens = [MockToken("I", "T") for _ in range(num_chords)]
    chord_symbols = ["C"] * num_chords

    # Should complete without timeout
    melodic_events = extractor._infer_voice_leading_events(tokens, chord_symbols, 0)
    assert len(melodic_events.voice_4_to_3) == num_chords
    assert melodic_events.source == "inference"


def test_malformed_input_robustness():
    """Test robustness with malformed inputs."""
    extractor = LowLevelEventExtractor()

    # Missing attributes in mock tokens
    class BadToken:
        def __init__(self):
            pass  # No roman or role attributes

    bad_tokens = [BadToken(), BadToken()]

    # Should not crash, just return all False
    try:
        melodic_events = extractor._infer_voice_leading_events(
            bad_tokens, ["C", "F"], 0
        )
        assert len(melodic_events.voice_4_to_3) == 2
        assert all(not x for x in melodic_events.voice_4_to_3)
    except AttributeError:
        # Acceptable to fail gracefully
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
