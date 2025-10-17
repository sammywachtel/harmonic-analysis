"""
Chord detection logic for the harmonic analysis demo.

Comprehensive chord recognition from MIDI pitches with support for:
- Basic triads (major, minor, diminished, augmented)
- Suspended chords (sus2, sus4)
- Seventh chords (maj7, m7, 7, dim7, m7b5, etc.)
- Add chords (add4, madd4)
- Partial chords (no5 variations)
- Inversion detection with slash notation

Ported from legacy src/harmonic_analysis/utils/chord_parser.py
"""

from typing import List

from demo.lib.constants import NOTE_NAMES_FOR_DETECTION

# ============================================================================
# Chord Templates
# ============================================================================

# Comprehensive chord templates (from legacy chord_parser.py)
CHORD_TEMPLATES = {
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


def detect_chord_from_pitches(pitches: List[int]) -> str:
    """
    Detect chord symbol from MIDI pitches with comprehensive chord recognition.

    Full chord detection logic from legacy src/harmonic_analysis/utils/chord_parser.py
    Supports complex chords including sus4, add4, 7ths, and partial chords.

    Args:
        pitches: List of MIDI note numbers

    Returns:
        Chord symbol string with slash notation for inversions (e.g., "Asus4/C#", "Cadd4/E")
    """
    if len(pitches) < 2:
        return "Unknown"

    # Find the lowest MIDI note (bass note)
    lowest_midi = min(pitches)
    bass_note = lowest_midi % 12

    # Convert to pitch classes and remove duplicates
    pitch_classes = list(set(p % 12 for p in pitches))
    pitch_classes.sort()

    # Try each pitch class as potential root
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

    # Check for inversion - add slash notation if bass != root
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
    """Calculate confidence score for chord match."""
    total_template_notes = len(template_intervals)
    extra_notes = len(played_intervals) - total_template_notes

    # Start with base confidence
    confidence = base_confidence

    # Penalize for extra notes
    if extra_notes > 0:
        confidence -= extra_notes * 0.08

    # Bonus for exact match
    if len(played_intervals) == total_template_notes:
        confidence += 0.1

    # Clamp between 0 and 1
    return max(0.0, min(1.0, confidence))


def detect_chord_with_music21(chord_element) -> str:
    """
    Use music21's sophisticated chord detection to identify complex chords.

    music21 has extensive chord analysis capabilities including:
    - Quality detection (major, minor, diminished, augmented)
    - Seventh chord detection
    - Suspended chord detection
    - Add chord detection
    - Inversion notation

    Args:
        chord_element: music21.chord.Chord object

    Returns:
        Chord symbol string (e.g., "Asus4/C#", "Cadd4", "Dm7b5")
    """
    try:
        # Get root and bass notes
        root = chord_element.root()
        bass = chord_element.bass()
        root_name = root.name

        # Get pitch classes for interval analysis
        pitches = sorted([p.midi % 12 for p in chord_element.pitches])
        root_pc = root.pitchClass
        intervals = sorted([(p - root_pc) % 12 for p in pitches])

        # Determine chord quality using music21's built-in detection
        quality = ""

        # Check for suspended chords first (no 3rd)
        has_third = any(interval in [3, 4] for interval in intervals)
        has_fourth = 5 in intervals
        has_second = 2 in intervals
        has_fifth = 7 in intervals

        if not has_third:
            if has_fourth and has_fifth:
                quality = "sus4"
            elif has_second and has_fifth:
                quality = "sus2"
            elif has_fourth:
                quality = "sus4(no5)"
            elif has_second:
                quality = "sus2(no5)"
            elif has_fifth:
                quality = "5"  # Power chord

        # If we have a third, check for standard qualities
        if quality == "":
            if chord_element.isMinorTriad():
                quality = "m"
            elif chord_element.isMajorTriad():
                quality = ""  # Major is default
            elif chord_element.isDiminishedTriad():
                quality = "dim"
            elif chord_element.isAugmentedTriad():
                quality = "aug"

            # Check for seventh chords
            if chord_element.seventh is not None:
                if chord_element.isDominantSeventh():
                    quality = "7"
                elif chord_element.isMajorSeventh():
                    quality = "maj7"
                elif chord_element.isMinorSeventh():
                    quality = "m7"
                elif chord_element.isDiminishedSeventh():
                    quality = "dim7"
                elif chord_element.isHalfDiminishedSeventh():
                    quality = "m7b5"

        # Check for add chords (has 3rd + 4th)
        if has_third and has_fourth and quality in ["", "m"]:
            if quality == "m":
                quality = "madd4"
            else:
                quality = "add4"

        # Build chord symbol
        chord_symbol = f"{root_name}{quality}"

        # Add inversion notation if bass != root
        if bass.pitchClass != root.pitchClass:
            bass_name = bass.name
            chord_symbol = f"{chord_symbol}/{bass_name}"

        return chord_symbol

    except Exception:
        # Fallback to basic pitchedCommonName
        try:
            return chord_element.pitchedCommonName
        except Exception:
            return "Unknown"
