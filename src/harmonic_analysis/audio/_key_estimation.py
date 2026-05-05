"""Krumhansl-Schmuckler key estimation from a 12-bin chroma vector.

Direct port of the toolkit's ``find_best_key`` (utils.py:45–81) with two
deliberate changes:

1. Returns a ``KeyInfo`` dataclass instead of a dict — the rest of the audio
   pipeline expects a typed object.
2. No external theory-library dependency. The toolkit's reference
   implementation didn't actually call out to one in this function, but
   downstream callers did via the dict it returned. Now everything stays
   inside the audio subpackage.

K-S profiles only know "major" and "minor" — i.e. Ionian and Aeolian. The
mode_map below preserves the toolkit's labels (so callers see "Ionian", not
"major"). Modal scales beyond Ionian/Aeolian are a WU3 problem.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._profiles import KS_PROFILES, PITCH_CLASSES
from ._types import KeyInfo

# Toolkit labels major/minor as Ionian/Aeolian on output. Preserved verbatim
# so the rest of the pipeline doesn't have to translate.
_MODE_MAP: Dict[str, str] = {"major": "Ionian", "minor": "Aeolian"}


def find_best_key(chroma_vector: np.ndarray) -> KeyInfo:
    """Estimate the best-fitting key for a 12-bin chroma vector.

    Args:
        chroma_vector: 12-element float array of pitch-class energies.

    Returns:
        ``KeyInfo`` with tonic, mode (Ionian/Aeolian), full key_signature
        string ("C major"-style — note: still uses the K-S "major"/"minor"
        labels for round-trip compatibility with the toolkit), and a
        confidence in [0.0, 1.0]. Zero-energy input returns an N/A sentinel.
    """
    # Zero-energy guard. Without this, np.corrcoef returns NaN against any
    # constant input and downstream confidence math goes sideways.
    if np.linalg.norm(chroma_vector) < 1e-6:
        return KeyInfo(
            tonic="N/A",
            mode="N/A",
            key_signature="N/A",
            confidence=0.0,
        )

    correlations: Dict[str, float] = {}
    for tonic_pc, tonic_name in enumerate(PITCH_CLASSES):
        for mode_name, profile_data in KS_PROFILES.items():
            # Roll the K-S profile so position 0 sits on this candidate tonic.
            profile = np.roll(np.asarray(profile_data, dtype=float), tonic_pc)
            corr = float(np.corrcoef(chroma_vector, profile)[0, 1])
            correlations[f"{tonic_name} {mode_name}"] = corr

    # max() with key= over a dict iterates keys; pick the one with the
    # highest correlation. Ties broken by dict insertion order — fine for
    # K-S, the 24-key search rarely has exact ties on real chroma.
    best_key = max(correlations, key=lambda k: correlations[k])
    raw_corr = correlations[best_key]

    # Pearson correlation lives in [-1, 1]; map to [0, 1] for an interpretable
    # "confidence." Second NaN guard catches the edge case where chroma had
    # nonzero norm but matched zero-variance somehow (constant chroma).
    if np.isnan(raw_corr):
        confidence = 0.0
    else:
        confidence = (raw_corr + 1.0) / 2.0

    tonic_name, mode_name = best_key.split()
    return KeyInfo(
        tonic=tonic_name,
        mode=_MODE_MAP.get(mode_name, mode_name),
        key_signature=best_key,
        confidence=round(confidence, 4),
    )
