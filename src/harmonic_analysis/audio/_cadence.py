"""V-I cadence detection from a 2-D chroma matrix.

Port of the toolkit's ``detect_cadences`` (utils.py:84–107). The original
took an external theory-library key object and asked it for the tonic
pitch class; we take a ``KeyInfo`` and look up the pitch class via
``PITCH_CLASSES``. That's the entire library elimination on this side —
same arithmetic, same heuristic constants, no library swap.

This is a deliberately simple detector: it asks "are tonic and dominant
both in the top-3 most prominent pitch classes of this segment?" and rates
the strength by their combined normalized energy. A real cadence detector
would walk chord progressions over time; that's WU3+ work.
"""

from __future__ import annotations

import numpy as np

from ._profiles import PC_OF_NOTE, PITCH_CLASSES  # noqa: F401
from ._types import CadenceInfo, KeyInfo


def detect_cadences(chroma: np.ndarray, key_info: KeyInfo) -> CadenceInfo:
    """Detect a V-I cadence-like pattern in a chroma segment.

    Args:
        chroma: 2-D chroma matrix shaped (12, n_frames). The function
            averages across frames internally — callers don't need to
            pre-reduce.
        key_info: ``KeyInfo`` providing the tonic to test against. The mode
            is irrelevant for V-I detection — the dominant is always the
            perfect fifth above the tonic.

    Returns:
        ``CadenceInfo(detected, strength)``. Strength is in [0.0, 1.0] and
        is 0.0 whenever ``detected`` is False or chroma energy is too low
        to draw a conclusion.
    """
    avg_chroma = chroma.mean(axis=1)

    # Same zero-energy guard as find_best_key — silence shouldn't pretend
    # to have a cadence.
    if np.linalg.norm(avg_chroma) < 1e-6:
        return CadenceInfo(detected=False, strength=0.0)

    if key_info.tonic == "N/A":
        # Caller passed in the zero-energy sentinel from find_best_key.
        # Nothing meaningful to detect against.
        return CadenceInfo(detected=False, strength=0.0)

    # First library substitution: integer pitch class via the constant
    # table instead of the upstream theory library's tonic.pitchClass.
    # PC_OF_NOTE accepts both sharp and flat spellings — KeyInfo's tonic
    # may now arrive as "Bb" / "Eb" / "Db" / "Gb" / "Ab" after
    # canonical-spelling respell at the API boundary.
    tonic_pc = PC_OF_NOTE[key_info.tonic]
    dominant_pc = (tonic_pc + 7) % 12

    # Top-3 most-energetic pitch classes. argsort is ascending, so the
    # last three indices are the three loudest.
    top_indices = np.argsort(avg_chroma)[-3:]
    is_cadence_like = bool(tonic_pc in top_indices and dominant_pc in top_indices)

    if not is_cadence_like:
        return CadenceInfo(detected=False, strength=0.0)

    # Combined normalized energy of tonic + dominant, scaled by 2.5 to
    # spread the typical 0.3–0.4 range over something more readable.
    # Capped at 1.0 — magic constant lifted verbatim from the toolkit.
    raw_strength = (avg_chroma[tonic_pc] + avg_chroma[dominant_pc]) / np.sum(avg_chroma)
    strength = float(min(round(raw_strength * 2.5, 2), 1.0))
    return CadenceInfo(detected=True, strength=strength)
