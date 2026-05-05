"""Unit tests for the bass_dominance approach.

AC-03 rows 4 (B-dominant bass → B winner) and 5 (no bass chroma →
graceful empty verdict).
"""

from __future__ import annotations

import numpy as np

from harmonic_analysis.audio._key_approaches.bass_dominance import BassDominanceApproach
from harmonic_analysis.audio._key_ensemble import KeyDetectionContext


def _chroma_stub() -> np.ndarray:
    return np.ones(12, dtype=float) / 12.0


def _bass_chroma_dominated_by(pc: int) -> np.ndarray:
    """Synthesize a bass chroma vector with strong dominance at pitch class ``pc``."""
    bass = np.full(12, 0.05, dtype=float)
    bass[pc] = 0.9
    return bass


def test_b_dominant_bass_wins_b_keys() -> None:
    """Bass chroma peaked at B (pc 11) → top-ranked tonic should be B."""
    bass = _bass_chroma_dominated_by(11)  # B is pitch class 11
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), bass_chroma_1d=bass)

    verdict = BassDominanceApproach().detect(ctx)

    assert verdict.name == "bass_dominance"
    assert len(verdict.ranked) > 0
    top_key, top_score = verdict.ranked[0]
    assert top_key.tonic == "B"
    assert top_score > 0.0


def test_c_dominant_bass_wins_c_keys() -> None:
    """Bass chroma peaked at C (pc 0) → top-ranked tonic should be C."""
    bass = _bass_chroma_dominated_by(0)
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), bass_chroma_1d=bass)

    verdict = BassDominanceApproach().detect(ctx)

    top_key, _ = verdict.ranked[0]
    assert top_key.tonic == "C"


def test_none_bass_chroma_returns_empty_verdict() -> None:
    """bass_chroma_1d=None (stage 1 path) → empty verdict, no crash."""
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), bass_chroma_1d=None)

    verdict = BassDominanceApproach().detect(ctx)

    assert verdict.ranked == []
    assert verdict.meta is not None


def test_zero_energy_bass_returns_empty_verdict() -> None:
    """Bass chroma all zeros → can't normalize, return empty verdict."""
    bass = np.zeros(12, dtype=float)
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), bass_chroma_1d=bass)

    verdict = BassDominanceApproach().detect(ctx)

    assert verdict.ranked == []


def test_returns_24_ranked_entries_when_bass_present() -> None:
    bass = _bass_chroma_dominated_by(7)  # G
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), bass_chroma_1d=bass)

    verdict = BassDominanceApproach().detect(ctx)
    assert len(verdict.ranked) == 24


def test_bad_shape_bass_returns_empty_verdict() -> None:
    """Wrong-shape bass vector should not crash — degrade to empty."""
    bass = np.array([0.1, 0.2], dtype=float)  # too short
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), bass_chroma_1d=bass)

    verdict = BassDominanceApproach().detect(ctx)
    assert verdict.ranked == []
