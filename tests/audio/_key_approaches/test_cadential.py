"""Unit tests for the cadential approach.

AC-03 rows 6 (V→i in Bm → B Aeolian wins), 7 (V→I in C major → C Ionian
wins), and 8 (no cadence pattern → graceful empty verdict).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from harmonic_analysis.audio._key_approaches.cadential import CadentialApproach
from harmonic_analysis.audio._key_ensemble import KeyDetectionContext


@dataclass
class _FakeChordEvent:
    chord_label: str
    start_time: float = 0.0
    end_time: float = 1.0
    confidence: float = 0.9
    is_diatonic: bool = True


def _chroma_stub() -> np.ndarray:
    return np.ones(12, dtype=float) / 12.0


def test_v_to_i_in_b_minor_scores_b_aeolian() -> None:
    """F# → Bm cadence (V→i in B minor) → B is the top tonic root.

    iteration_01_a contract relaxation: cadential is now mode-agnostic.
    Both B Ionian and B Aeolian receive equal credit for any major-V →
    B-rooted cadence. The previous assertion (`mode == "Aeolian"`)
    encoded the BUGGY pre-fix behavior where cadential pre-decided mode
    based on the resolved chord's quality; that's exactly what the
    iteration_01_a fix eliminates. The relaxed assertion still pins
    down the load-bearing claim — the cadence identifies B as the
    tonic root — without re-asserting the bug.
    """
    events = [
        _FakeChordEvent("D"),
        _FakeChordEvent("F#"),  # V
        _FakeChordEvent("Bm"),  # i
    ]
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), chord_events=events)

    verdict = CadentialApproach().detect(ctx)

    assert verdict.name == "cadential"
    assert len(verdict.ranked) > 0
    top_key, top_score = verdict.ranked[0]
    assert (
        top_key.tonic == "B"
    ), f"Expected B as top tonic root, got {top_key.tonic} {top_key.mode}"
    assert top_key.mode in ("Ionian", "Aeolian"), (
        f"Top mode should be one of Ionian/Aeolian after dual-credit; "
        f"got {top_key.mode}"
    )
    assert top_score > 0.0


def test_v_to_capital_i_in_c_major_scores_c_ionian() -> None:
    """G → C cadence (V→I in C major) → C is the top tonic root.

    iteration_01_a contract relaxation: cadential is mode-agnostic.
    Both C Ionian and C Aeolian receive equal credit for the G→C cadence.
    This test still pins down tonic-root identification (the only thing
    cadential is responsible for) — the rest of the ensemble decides
    Ionian vs Aeolian via K-S template fit and bass_dominance.
    """
    events = [
        _FakeChordEvent("F"),
        _FakeChordEvent("G"),  # V
        _FakeChordEvent("C"),  # I
    ]
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), chord_events=events)

    verdict = CadentialApproach().detect(ctx)

    top_key, _ = verdict.ranked[0]
    assert (
        top_key.tonic == "C"
    ), f"Expected C as top tonic root, got {top_key.tonic} {top_key.mode}"
    assert top_key.mode in ("Ionian", "Aeolian"), (
        f"Top mode should be one of Ionian/Aeolian after dual-credit; "
        f"got {top_key.mode}"
    )


def test_no_cadence_pattern_returns_empty_verdict() -> None:
    """vi-IV-I-V-style loop with no V→I → empty verdict, no crash."""
    events = [
        _FakeChordEvent("Am"),
        _FakeChordEvent("F"),
        _FakeChordEvent("C"),
        _FakeChordEvent("G"),  # ends on V, no V→I transition (G→Am earlier)
    ]
    # Note: Am→F has no cadential motion (vi→IV). F→C is plagal (IV→I)
    # which we don't credit. C→G is anti-cadential (I→V).
    # Only V→I (G→C) cadences count, and there isn't one in this sequence.
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), chord_events=events)

    verdict = CadentialApproach().detect(ctx)

    # Per the prepare-doc spec, "no V→i or V→I transition" → graceful
    # empty/zero verdict. Empty ranked list is the chosen graceful form.
    assert verdict.ranked == []


def test_empty_chord_events_graceful() -> None:
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), chord_events=[])
    verdict = CadentialApproach().detect(ctx)
    assert verdict.ranked == []


def test_single_chord_returns_empty_verdict() -> None:
    """One chord can't cadence — needs a transition."""
    events = [_FakeChordEvent("C")]
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), chord_events=events)

    verdict = CadentialApproach().detect(ctx)
    assert verdict.ranked == []


def test_multiple_cadences_strengthen_winner() -> None:
    """Multiple V→I cadences on same tonic root → that root normalizes to 1.0.

    iteration_01_a: cadential is mode-agnostic, so both C Ionian and
    C Aeolian sit at score 1.0 after two G→C cadences. The relaxed
    assertion still proves that the cadence-counted tonic root wins
    overall and reaches the normalized maximum.
    """
    events = [
        _FakeChordEvent("G"),  # V
        _FakeChordEvent("C"),  # I
        _FakeChordEvent("F"),
        _FakeChordEvent("G"),  # V
        _FakeChordEvent("C"),  # I
    ]
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), chord_events=events)

    verdict = CadentialApproach().detect(ctx)
    top_key, top_score = verdict.ranked[0]
    assert top_key.tonic == "C"
    assert top_key.mode in ("Ionian", "Aeolian")
    assert top_score == 1.0  # Top score normalized to 1.0


# ---------------------------------------------------------------------------
# iteration_01_a: dual-credit symmetry tests. After the fix, every
# major-V → tonic resolution credits both Ionian and Aeolian of the
# tonic root equally. These tests are the primary regression guard
# against re-introducing the silent major-bias bug.
# ---------------------------------------------------------------------------


def _find_score(verdict, tonic: str, mode: str) -> float:
    """Extract a single (tonic, mode) score from a verdict's ranked list."""
    for k, s in verdict.ranked:
        if k.tonic == tonic and k.mode == mode:
            return s
    raise AssertionError(
        f"Did not find {tonic} {mode} in verdict.ranked — "
        f"got tonics={[(k.tonic, k.mode) for k, _ in verdict.ranked[:6]]}"
    )


def test_v_to_i_minor_credits_both_modes_equally() -> None:
    """F# → Bm cadence (V→i in B minor) credits B Ionian AND B Aeolian
    with equal score. This is the primary regression guard for the
    silent major-bias bug — pre-fix, B Aeolian got zero from this
    progression while D Ionian (a relative-major detour) scored 1.000."""
    events = [
        _FakeChordEvent("F#"),  # major V
        _FakeChordEvent("Bm"),  # minor i
    ]
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), chord_events=events)

    verdict = CadentialApproach().detect(ctx)

    b_ionian = _find_score(verdict, "B", "Ionian")
    b_aeolian = _find_score(verdict, "B", "Aeolian")
    # Equal score — same integer count, same normalizer.
    assert b_ionian == b_aeolian, (
        f"Expected equal credit for B Ionian and B Aeolian after V→i; "
        f"got Ionian={b_ionian}, Aeolian={b_aeolian}"
    )
    # Both should be at the maximum (1.0) since they're the only credited
    # candidates. Locks down the normalization shape, not just symmetry.
    assert b_ionian == 1.0
    assert b_aeolian == 1.0


def test_v_to_capital_i_major_credits_both_modes_equally() -> None:
    """A → D cadence (V→I in D major) credits D Ionian AND D Aeolian
    with equal score. Proves symmetry — the dual-credit isn't biased
    toward minor either; cadential is genuinely mode-agnostic."""
    events = [
        _FakeChordEvent("A"),  # major V
        _FakeChordEvent("D"),  # major I
    ]
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), chord_events=events)

    verdict = CadentialApproach().detect(ctx)

    d_ionian = _find_score(verdict, "D", "Ionian")
    d_aeolian = _find_score(verdict, "D", "Aeolian")
    assert d_ionian == d_aeolian, (
        f"Expected equal credit for D Ionian and D Aeolian after V→I; "
        f"got Ionian={d_ionian}, Aeolian={d_aeolian}"
    )
    assert d_ionian == 1.0
    assert d_aeolian == 1.0


def test_no_v_motion_returns_empty_verdict() -> None:
    """Negative case: a sequence with NO (major V → any tonic) adjacent
    pairs must produce an empty verdict with a populated reason. Cadential
    refuses to fabricate cadences from non-dominant motion.

    Sequence walk-through (each pair must fail the V→tonic test):
        Am (minor) → Em (minor): a is minor, skipped (only major V's
            count as dominants).
        Em (minor) → Am (minor): a is minor, skipped.
        Am (minor) → Dm (minor): a is minor, skipped.
    No major-V dominants in the sequence at all → no cadences.
    """
    events = [
        _FakeChordEvent("Am"),
        _FakeChordEvent("Em"),
        _FakeChordEvent("Am"),
        _FakeChordEvent("Dm"),
    ]
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), chord_events=events)

    verdict = CadentialApproach().detect(ctx)

    assert verdict.ranked == []
    assert verdict.meta is not None
    assert verdict.meta.get("reason") == "no_cadences_detected"
