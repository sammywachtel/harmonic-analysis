"""Krumhansl-Schmuckler key profiles and pitch-class names.

Verbatim port of the toolkit's constants. Sharps only ("C#"), no flats —
preserved as the project convention. Integer pitch-class arithmetic doesn't
care about spelling, but every consumer here assumes this exact ordering.

The audio module uses sharps internally for pitch-class arithmetic, but
real-world music notation prefers flats for most "black-key" major keys
(Bb major, not A# major) and a mix for minor keys. ``canonical_key_spelling``
bridges the two: it produces the spelling that matches the rest of the
library's key-signature handling and what musicians actually use.
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

# Note-name → pitch-class lookup that accepts both sharp and flat spellings.
# ``PITCH_CLASSES.index`` is sharps-only; this dict lets internal helpers
# (e.g. _compute_diatonic_pcs, _cadence) accept Bb / Eb / Db / Gb / Ab tonics
# without crashing once the API surface starts handing them out.
PC_OF_NOTE: Dict[str, int] = {
    "C": 0,
    "B#": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "Fb": 4,
    "F": 5,
    "E#": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
    "Cb": 11,
}


def canonical_key_spelling(tonic: str, mode: str) -> Tuple[str, str]:
    """Return ``(display_tonic, key_signature)`` using music-notation convention.

    The audio module uses sharps-only ``PITCH_CLASSES`` internally for
    pitch-class arithmetic. Real-world notation prefers flat spellings
    for most black-key major roots (``Bb`` major, not ``A#`` major —
    the latter would need 10 sharps) and a mix for minor roots
    depending on which spelling produces fewer accidentals in
    repertoire.

    Convention applied here matches the rest of the library's key-
    signature handling (see ``core/utils/key_signature.py``):

    * **Major**: prefer flats for accidentals — Db, Eb, F#, Ab, Bb.
      The only outlier is F# major; either F#/Gb is fine but F# major
      is more common in standard repertoire.
    * **Minor**: pick by fewest accidentals — C#m (4#), Ebm (6♭), F#m
      (3#), G#m (5#), Bbm (5♭). A# minor is rare in real music; Bb
      minor is the standard.

    Returns ``(tonic, "{tonic} {major|minor}")``. Unknown tonic
    (anything not in the respelling tables, including the natural
    ``C``/``D``/``E``/``F``/``G``/``A``/``B``) passes through unchanged
    with a normalized ``key_signature`` string.
    """
    if tonic == "N/A":
        return ("N/A", "N/A")

    is_minor = mode.lower() in ("aeolian", "minor", "phrygian", "locrian", "dorian")

    # Music-notation convention. Major: prefer flats for black-key tonics.
    # The "A# major" / "G# major" / "D# major" / "C# major" listings in
    # any music-notation context are vanishingly rare — the equivalent
    # flat spelling is the standard.
    major_respell = {
        "C#": "Db",  # C# major is 7 sharps; Db major is 5 flats
        "D#": "Eb",  # D# major doesn't exist in standard notation
        "F#": "F#",  # 6 sharps; either F#/Gb is fine, F# more common
        "G#": "Ab",  # G# major doesn't exist in standard notation
        "A#": "Bb",  # A# major would be 10 sharps; Bb major is 2 flats
    }
    minor_respell = {
        "C#": "C#",  # C# minor is 4 sharps (Db minor would be 8 flats)
        "D#": "Eb",  # 6 sharps vs 6 flats; Eb minor more common
        "F#": "F#",  # F# minor is 3 sharps
        "G#": "G#",  # 5 sharps (Ab minor would be 7 flats)
        "A#": "Bb",  # A# minor is 7 sharps; Bb minor is 5 flats
    }

    table = minor_respell if is_minor else major_respell
    display_tonic = table.get(tonic, tonic)
    suffix = "minor" if is_minor else "major"
    return (display_tonic, f"{display_tonic} {suffix}")


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
