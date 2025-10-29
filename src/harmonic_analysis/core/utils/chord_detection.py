"""
Chord detection from MIDI pitches.

Comprehensive chord recognition supporting:
- Basic triads (major, minor, diminished, augmented)
- Suspended chords (sus2, sus4)
- Seventh chords (maj7, m7, 7, dim7, m7b5, etc.)
- Add chords (add4, madd4)
- Partial chords (no5 variations)
- Inversion detection with slash notation

Ported from demo/lib/chord_detection.py for library-wide use.
"""

from typing import Any, Dict, List

# ============================================================================
# Music Theory Constants
# ============================================================================

# Note names for detection (prefer enharmonics avoiding double-sharps/flats)
NOTE_NAMES_FOR_DETECTION = [
    "C",
    "C#",
    "D",
    "Eb",
    "E",
    "F",
    "F#",
    "G",
    "Ab",
    "A",
    "Bb",
    "B",
]

# ============================================================================
# Chord Templates
# ============================================================================

# Opening move: Define comprehensive chord templates with confidence scores
# These patterns match pitch class intervals (semitones from root)
# min_notes ensures we have enough information to identify the chord
CHORD_TEMPLATES: Dict[str, Dict[str, Any]] = {
    # Basic triads
    "major": {"intervals": [0, 4, 7], "symbol": "", "min_notes": 3, "confidence": 1.0},
    "minor": {"intervals": [0, 3, 7], "symbol": "m", "min_notes": 3, "confidence": 1.0},
    "diminished": {
        "intervals": [0, 3, 6],
        "symbol": "dim",
        "min_notes": 3,
        "confidence": 1.0,
    },
    "augmented": {
        "intervals": [0, 4, 8],
        "symbol": "aug",
        "min_notes": 3,
        "confidence": 1.0,
    },
    # Suspended chords (complete)
    "sus2": {
        "intervals": [0, 2, 7],
        "symbol": "sus2",
        "min_notes": 3,
        "confidence": 1.0,
    },
    "sus4": {
        "intervals": [0, 5, 7],
        "symbol": "sus4",
        "min_notes": 3,
        "confidence": 1.0,
    },
    # Partial suspended chords (2-note combinations)
    "sus2Partial": {
        "intervals": [0, 2],
        "symbol": "sus2(no5)",
        "min_notes": 2,
        "confidence": 0.75,
    },
    "sus4Partial": {
        "intervals": [0, 5],
        "symbol": "sus4(no5)",
        "min_notes": 2,
        "confidence": 0.75,
    },
    # Partial triads (2-note combinations)
    "majorPartial": {
        "intervals": [0, 4],
        "symbol": "(no5)",
        "min_notes": 2,
        "confidence": 0.70,
    },
    "minorPartial": {
        "intervals": [0, 3],
        "symbol": "m(no5)",
        "min_notes": 2,
        "confidence": 0.70,
    },
    "fifthPartial": {
        "intervals": [0, 7],
        "symbol": "5",
        "min_notes": 2,
        "confidence": 0.85,
    },
    # Partial seventh chords (3-note combinations missing one tone)
    "dom7NoFifth": {
        "intervals": [0, 4, 10],
        "symbol": "7(no5)",
        "min_notes": 3,
        "confidence": 0.80,
    },
    "min7NoFifth": {
        "intervals": [0, 3, 10],
        "symbol": "m7(no5)",
        "min_notes": 3,
        "confidence": 0.80,
    },
    "maj7NoFifth": {
        "intervals": [0, 4, 11],
        "symbol": "maj7(no5)",
        "min_notes": 3,
        "confidence": 0.80,
    },
    # Incomplete sus chords with extensions
    "sus2Add7": {
        "intervals": [0, 2, 10],
        "symbol": "sus2(add7)",
        "min_notes": 3,
        "confidence": 0.75,
    },
    "sus4Add7": {
        "intervals": [0, 5, 10],
        "symbol": "sus4(add7)",
        "min_notes": 3,
        "confidence": 0.75,
    },
    # Add chords (retaining 3rd + added note)
    "majorAdd4": {
        "intervals": [0, 4, 5],
        "symbol": "add4",
        "min_notes": 3,
        "confidence": 0.85,
    },
    "minorAdd4": {
        "intervals": [0, 3, 5],
        "symbol": "madd4",
        "min_notes": 3,
        "confidence": 0.85,
    },
    # Seventh chords (4-note combinations)
    "major7": {
        "intervals": [0, 4, 7, 11],
        "symbol": "maj7",
        "min_notes": 4,
        "confidence": 1.0,
    },
    "minor7": {
        "intervals": [0, 3, 7, 10],
        "symbol": "m7",
        "min_notes": 4,
        "confidence": 1.0,
    },
    "dominant7": {
        "intervals": [0, 4, 7, 10],
        "symbol": "7",
        "min_notes": 4,
        "confidence": 1.0,
    },
    "diminished7": {
        "intervals": [0, 3, 6, 9],
        "symbol": "dim7",
        "min_notes": 4,
        "confidence": 1.0,
    },
    "halfDiminished7": {
        "intervals": [0, 3, 6, 10],
        "symbol": "m7b5",
        "min_notes": 4,
        "confidence": 1.0,
    },
    "augmented7": {
        "intervals": [0, 4, 8, 10],
        "symbol": "aug7",
        "min_notes": 4,
        "confidence": 1.0,
    },
    "minorMaj7": {
        "intervals": [0, 3, 7, 11],
        "symbol": "m(maj7)",
        "min_notes": 4,
        "confidence": 1.0,
    },
    # Extended chords with 4th (sus4 with extra notes)
    "sus4With3rd": {
        "intervals": [0, 4, 5, 7],
        "symbol": "sus4",
        "min_notes": 4,
        "confidence": 0.90,
    },
}


# ============================================================================
# Chord Detection Functions
# ============================================================================


def detect_chord_from_pitches(pitches: List[int]) -> str:
    """
    Detect chord symbol from MIDI pitches with comprehensive chord recognition.

    Main play: Try each pitch class as a potential root, calculate intervals,
    and match against chord templates. Pick the best match based on confidence
    scoring that rewards exact matches and penalizes extra notes.

    Supports complex chords including sus4, add4, 7ths, and partial chords.
    Automatically detects inversions and adds slash notation.

    Args:
        pitches: List of MIDI note numbers (e.g., [60, 64, 67] for C major)

    Returns:
        Chord symbol string with slash notation for inversions
        (e.g., "Asus4/C#", "Cadd4/E", "C", "Unknown")

    Examples:
        >>> detect_chord_from_pitches([60, 64, 67])
        'C'
        >>> detect_chord_from_pitches([60, 64, 67, 71])
        'Cmaj7'
        >>> detect_chord_from_pitches([64, 67, 60])  # First inversion
        'C/E'
    """
    # Opening move: validate we have enough notes
    if len(pitches) < 2:
        return "Unknown"

    # Find the lowest MIDI note (bass note) for inversion detection
    lowest_midi = min(pitches)
    bass_note = lowest_midi % 12

    # Convert to pitch classes and remove duplicates
    # Pitch class = MIDI note % 12 (C=0, C#=1, D=2, etc.)
    pitch_classes = list(set(p % 12 for p in pitches))
    pitch_classes.sort()

    # Main play: try each pitch class as potential root
    best_match = None
    best_root = None
    best_confidence = 0.0

    for root in pitch_classes:
        # Calculate intervals from this root
        intervals = [(p - root) % 12 for p in pitch_classes]
        intervals.sort()

        # Check against each chord template
        for chord_type, template in CHORD_TEMPLATES.items():
            template_intervals = template["intervals"]
            min_notes = template["min_notes"]

            # Skip if we don't have enough notes
            if len(pitches) < min_notes:
                continue

            # Check if all template intervals are present
            if all(interval in intervals for interval in template_intervals):
                # Calculate confidence
                confidence = _calculate_confidence(
                    intervals, template_intervals, len(pitches), template["confidence"]
                )

                if confidence > best_confidence:
                    best_confidence = confidence
                    root_name = NOTE_NAMES_FOR_DETECTION[root]
                    best_root = root
                    best_match = f"{root_name}{template['symbol']}"

    if not best_match:
        return "Unknown"

    # Victory lap: check for inversion - add slash notation if bass != root
    if bass_note != best_root:
        bass_name = NOTE_NAMES_FOR_DETECTION[bass_note]
        best_match = f"{best_match}/{bass_name}"

    return best_match


def _calculate_confidence(
    played_intervals: List[int],
    template_intervals: List[int],
    note_count: int,
    base_confidence: float,
) -> float:
    """
    Calculate confidence score for chord match.

    Scoring strategy:
    - Start with base confidence (1.0 for complete chords, 0.7-0.9 for partial)
    - Penalize extra notes that aren't in the template (complexity penalty)
    - Bonus for exact matches (all template notes, no extras)

    Args:
        played_intervals: Intervals present in the played chord
        template_intervals: Expected intervals from chord template
        note_count: Total number of notes in the chord
        base_confidence: Starting confidence from template

    Returns:
        Confidence score clamped between 0.0 and 1.0
    """
    total_template_notes = len(template_intervals)
    extra_notes = len(played_intervals) - total_template_notes

    # Start with base confidence
    confidence = base_confidence

    # Penalize for extra notes (complexity or wrong notes)
    if extra_notes > 0:
        confidence -= extra_notes * 0.08

    # Bonus for exact match (all notes match template, no extras)
    if len(played_intervals) == total_template_notes:
        confidence += 0.1

    # Clamp between 0 and 1
    return max(0.0, min(1.0, confidence))
