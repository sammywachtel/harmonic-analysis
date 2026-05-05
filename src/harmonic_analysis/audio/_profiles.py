"""Krumhansl-Schmuckler key profiles and pitch-class names.

Verbatim port of the toolkit's constants. Sharps only ("C#"), no flats —
preserved as the project convention. Integer pitch-class arithmetic doesn't
care about spelling, but every consumer here assumes this exact ordering.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

# Pitch-class names indexed 0..11 (C..B). Sharps only — match toolkit verbatim.
PITCH_CLASSES: List[str] = [
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B",
]

# Krumhansl-Schmuckler empirical profiles. These are the canonical 1990
# probe-tone weights — don't tune them, that's a research project.
KS_PROFILES: Dict[str, Tuple[float, ...]] = {
    "major": (
        6.35,
        2.23,
        3.48,
        2.33,
        4.38,
        4.09,
        2.52,
        5.19,
        2.39,
        3.66,
        2.29,
        2.88,
    ),
    "minor": (
        6.33,
        2.68,
        3.52,
        5.38,
        2.60,
        3.53,
        2.54,
        4.75,
        3.98,
        2.69,
        3.34,
        3.17,
    ),
}
