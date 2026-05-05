"""Unit tests for ``detect_cadences``.

Covers AC5 scenarios for cadence detection: V-I detection, no-cadence,
and the silent-chroma edge case. The detector is intentionally crude —
it asks whether tonic and dominant are both in the top-3 most-prominent
pitch classes of the segment — so the test fixtures are correspondingly
simple.
"""

from __future__ import annotations

import numpy as np

from harmonic_analysis.audio._cadence import detect_cadences
from harmonic_analysis.audio._types import CadenceInfo, KeyInfo


def _make_chroma(*, tonic_pc: int, dominant_pc: int, strong: bool) -> np.ndarray:
    """Build a (12, n_frames) chroma matrix where tonic and dominant
    dominate (or don't, depending on ``strong``).
    """
    chroma = np.full((12, 8), 0.05, dtype=float)
    if strong:
        chroma[tonic_pc, :] = 1.0
        chroma[dominant_pc, :] = 0.9
        # Add one more bump so top-3 is well-defined. Major third — common
        # in real V-I cadences, gives us a sensible "third loudest."
        chroma[(tonic_pc + 4) % 12, :] = 0.4
    return chroma


def _c_major() -> KeyInfo:
    return KeyInfo(
        tonic="C",
        mode="Ionian",
        key_signature="C major",
        confidence=0.9,
    )


def test_detect_cadences_returns_cadenceinfo() -> None:
    # AC4 smoke: pure-numpy callable, returns the dataclass.
    chroma = _make_chroma(tonic_pc=0, dominant_pc=7, strong=True)
    result = detect_cadences(chroma, _c_major())
    assert isinstance(result, CadenceInfo)
    assert isinstance(result.detected, bool)
    assert isinstance(result.strength, float)


def test_detect_cadences_v_to_i_in_c_major() -> None:
    # AC5 — V-I cadence detection. C tonic + G dominant prominent.
    chroma = _make_chroma(tonic_pc=0, dominant_pc=7, strong=True)
    result = detect_cadences(chroma, _c_major())
    assert result.detected is True
    assert 0.0 < result.strength <= 1.0


def test_detect_cadences_no_cadence_when_dominant_absent() -> None:
    # AC5 — no-cadence case. Tonic prominent but dominant suppressed.
    chroma = np.full((12, 8), 0.05, dtype=float)
    chroma[0, :] = 1.0  # C prominent
    # Boost two non-dominant pitch classes instead of G.
    chroma[2, :] = 0.8  # D
    chroma[4, :] = 0.7  # E
    result = detect_cadences(chroma, _c_major())
    assert result.detected is False
    assert result.strength == 0.0


def test_detect_cadences_silent_segment_returns_no_cadence() -> None:
    # Silent (zero-energy) input. Norm guard kicks in, no division by zero.
    silent = np.zeros((12, 8), dtype=float)
    result = detect_cadences(silent, _c_major())
    assert result.detected is False
    assert result.strength == 0.0


def test_detect_cadences_handles_na_keyinfo() -> None:
    # When find_best_key returned the N/A sentinel, cadence detection
    # should bail rather than try to PITCH_CLASSES.index("N/A").
    chroma = _make_chroma(tonic_pc=0, dominant_pc=7, strong=True)
    na_key = KeyInfo(
        tonic="N/A",
        mode="N/A",
        key_signature="N/A",
        confidence=0.0,
    )
    result = detect_cadences(chroma, na_key)
    assert result.detected is False
    assert result.strength == 0.0
