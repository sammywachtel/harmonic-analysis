"""Krumhansl-Schmuckler key estimation (thin backward-compat wrapper).

The K-S logic moved to ``_key_approaches/template_correlation.py`` as
part of the audio_score_alignment-02 ensemble. This file is now a thin
shim — it preserves the ``find_best_key`` import path for any caller
(internal or external) that still expects to call into this module.

Migration notes:
    Old code:
        from harmonic_analysis.audio._key_estimation import find_best_key
        result = find_best_key(chroma_vector)

    New code (with ensemble):
        # Backward-compat — same behavior as before
        result = find_best_key(chroma_vector)

        # Or via the adapter for the full ensemble:
        from harmonic_analysis import analyze_audio_async
        result = await analyze_audio_async(filepath, key_detection="default")
        # ...where key_detection="ks_only" recovers the old behavior.

The wrapper is deliberately a one-liner. AC-02 of the ensemble scope
asserts bit-identical behavior between this function and the
pre-ensemble code path, to 4 decimal places. Any cleverness here
(rounding, normalization, mode mapping) would break that assertion.
The ``TemplateCorrelationApproach.detect()`` does the K-S math; we
just unpack its top-1 KeyInfo and return it.
"""

from __future__ import annotations

import numpy as np

from ._key_approaches.template_correlation import TemplateCorrelationApproach
from ._key_ensemble import KeyDetectionContext
from ._types import KeyInfo


def find_best_key(chroma_vector: np.ndarray) -> KeyInfo:
    """Estimate the best-fitting key for a 12-bin chroma vector.

    Thin wrapper around ``TemplateCorrelationApproach.detect()``. The
    K-S correlation logic, zero-energy guard, and confidence rounding
    all live in the approach class — this function just delegates.

    Args:
        chroma_vector: 12-element float array of pitch-class energies.

    Returns:
        ``KeyInfo`` with tonic, mode (Ionian/Aeolian), full key_signature
        string ("C major"-style), and a confidence in [0.0, 1.0].
        Zero-energy input returns the N/A sentinel.
    """
    # One-liner delegation — no intermediate logic. AC-02 demands
    # bit-identity with the pre-ensemble path; this wrapper is the
    # contract surface that backward-compat callers see.
    return (
        TemplateCorrelationApproach()
        .detect(KeyDetectionContext(chroma_1d=chroma_vector))
        .ranked[0][0]
    )
