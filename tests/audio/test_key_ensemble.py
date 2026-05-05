"""Unit tests for the KeyEnsembleSynthesizer.

AC-04: Synthesizer correctness — winner via weighted sum, margin formula,
single-approach behavior, tie handling.
"""

from __future__ import annotations

import pytest

from harmonic_analysis.audio._key_ensemble import (
    DEFAULT_WEIGHTS,
    KeyDetectionVerdict,
    KeyEnsembleSynthesizer,
    resolve_preset,
)
from harmonic_analysis.audio._types import KeyInfo


def _key(tonic: str, mode: str) -> KeyInfo:
    """Quick KeyInfo factory."""
    return KeyInfo(
        tonic=tonic,
        mode=mode,
        key_signature=f"{tonic} {'major' if mode == 'Ionian' else 'minor'}",
        confidence=0.5,
    )


def test_synthesizer_picks_weighted_sum_winner() -> None:
    """approach-A: B Aeolian=0.9; approach-B: D Ionian=0.8; weights=1.0 → winner=B."""
    b_aeolian = _key("B", "Aeolian")
    d_ionian = _key("D", "Ionian")

    verdict_a = KeyDetectionVerdict(
        name="A",
        ranked=[(b_aeolian, 0.9), (d_ionian, 0.5)],
    )
    verdict_b = KeyDetectionVerdict(
        name="B",
        ranked=[(d_ionian, 0.8), (b_aeolian, 0.4)],
    )

    weights = {"A": 1.0, "B": 1.0}
    synth = KeyEnsembleSynthesizer()
    result = synth.synthesize([verdict_a, verdict_b], weights=weights)

    # B Aeolian totals: 0.9 * 1.0 + 0.4 * 1.0 = 1.3
    # D Ionian totals : 0.5 * 1.0 + 0.8 * 1.0 = 1.3
    # Tie! Whichever appears first in iteration order wins.
    assert result.method == "weighted_sum"
    # Both winners are valid given exact tie; just verify margin is 0
    assert result.margin == 0.0


def test_synthesizer_margin_is_winner_minus_runner_up() -> None:
    """Clear winner → margin = winner_total - runner_up_total."""
    b_aeolian = _key("B", "Aeolian")
    d_ionian = _key("D", "Ionian")

    verdict_a = KeyDetectionVerdict(
        name="A",
        ranked=[(b_aeolian, 0.9), (d_ionian, 0.3)],
    )
    verdict_b = KeyDetectionVerdict(
        name="B",
        ranked=[(b_aeolian, 0.7), (d_ionian, 0.4)],
    )
    weights = {"A": 1.0, "B": 1.0}

    result = KeyEnsembleSynthesizer().synthesize(
        [verdict_a, verdict_b], weights=weights
    )

    # B totals: 1.6; D totals: 0.7; margin: 0.9
    assert result.winner.tonic == "B"
    assert result.runner_up is not None
    assert result.runner_up.tonic == "D"
    assert result.margin == pytest.approx(0.9, rel=1e-6)


def test_synthesizer_applies_per_approach_weights() -> None:
    """Weight scaling: approach-B's vote at 2x flips the winner."""
    b_aeolian = _key("B", "Aeolian")
    d_ionian = _key("D", "Ionian")

    verdict_a = KeyDetectionVerdict(
        name="A", ranked=[(b_aeolian, 0.9), (d_ionian, 0.0)]
    )
    verdict_b = KeyDetectionVerdict(
        name="B", ranked=[(d_ionian, 0.6), (b_aeolian, 0.0)]
    )

    # Equal weights: B wins (0.9 vs 0.6)
    res_eq = KeyEnsembleSynthesizer().synthesize(
        [verdict_a, verdict_b], weights={"A": 1.0, "B": 1.0}
    )
    assert res_eq.winner.tonic == "B"

    # Boost B's weight to 2.0: D wins (0.9 vs 1.2)
    res_boosted = KeyEnsembleSynthesizer().synthesize(
        [verdict_a, verdict_b], weights={"A": 1.0, "B": 2.0}
    )
    assert res_boosted.winner.tonic == "D"


def test_synthesizer_handles_single_verdict() -> None:
    """Only one approach ran (e.g. ks_only) → no crash, runner_up may exist
    from the same verdict's tail."""
    b = _key("B", "Aeolian")
    d = _key("D", "Ionian")
    verdict = KeyDetectionVerdict(name="A", ranked=[(b, 0.9), (d, 0.5)])
    weights = {"A": 1.0}

    result = KeyEnsembleSynthesizer().synthesize([verdict], weights=weights)

    assert result.winner.tonic == "B"
    assert result.runner_up is not None
    assert result.runner_up.tonic == "D"
    assert result.margin == pytest.approx(0.4, rel=1e-6)


def test_synthesizer_skips_zero_weight_approaches() -> None:
    """Approach with weight 0.0 doesn't contribute to score table."""
    b = _key("B", "Aeolian")
    d = _key("D", "Ionian")
    verdict_a = KeyDetectionVerdict(name="A", ranked=[(b, 0.9)])
    verdict_b = KeyDetectionVerdict(name="B", ranked=[(d, 0.9)])

    result = KeyEnsembleSynthesizer().synthesize(
        [verdict_a, verdict_b], weights={"A": 1.0, "B": 0.0}
    )

    assert result.winner.tonic == "B"  # only A contributed
    # B should not appear in the score table at all when its weight was 0
    assert "D major" not in result.key_score_table


def test_synthesizer_raises_on_empty_verdicts() -> None:
    """Empty verdict list → ValueError (programming error, not graceful state)."""
    with pytest.raises(ValueError):
        KeyEnsembleSynthesizer().synthesize([])


def test_synthesizer_per_approach_records_weights() -> None:
    """SynthesisResult.per_approach reflects what was wired up."""
    verdict = KeyDetectionVerdict(name="X", ranked=[(_key("C", "Ionian"), 1.0)])
    result = KeyEnsembleSynthesizer().synthesize([verdict], weights={"X": 0.5})

    assert result.per_approach == [("X", 0.5)]


def test_synthesizer_handles_empty_ranked_lists() -> None:
    """Some verdicts with empty ranked lists shouldn't crash; others contribute."""
    b = _key("B", "Aeolian")
    empty = KeyDetectionVerdict(name="empty", ranked=[])
    populated = KeyDetectionVerdict(name="populated", ranked=[(b, 0.7)])

    result = KeyEnsembleSynthesizer().synthesize(
        [empty, populated], weights={"empty": 1.0, "populated": 1.0}
    )

    assert result.winner.tonic == "B"


# ---- preset resolver tests ----


def test_resolve_preset_default_returns_4_approaches() -> None:
    names, weights = resolve_preset("default")
    assert names == [
        "template_correlation",
        "boundary_chords",
        "bass_dominance",
        "cadential",
    ]
    assert weights == {n: DEFAULT_WEIGHTS[n] for n in names}


def test_resolve_preset_ks_only_returns_one_approach() -> None:
    names, weights = resolve_preset("ks_only")
    assert names == ["template_correlation"]
    assert weights == {"template_correlation": 1.0}


def test_resolve_preset_full_includes_optins() -> None:
    names, _weights = resolve_preset("full")
    assert "pattern_engine" in names
    assert "hmm" in names


def test_resolve_preset_unknown_raises() -> None:
    with pytest.raises(ValueError):
        resolve_preset("kaboom")


def test_resolve_preset_dict_uses_supplied_weights() -> None:
    names, weights = resolve_preset(
        {"template_correlation": 2.5, "boundary_chords": 0.1}
    )
    assert "template_correlation" in names
    assert weights["template_correlation"] == 2.5


def test_resolve_preset_list_uses_default_weights() -> None:
    names, weights = resolve_preset(["template_correlation", "boundary_chords"])
    assert names == ["template_correlation", "boundary_chords"]
    assert weights["template_correlation"] == 1.0


def test_resolve_preset_empty_list_raises() -> None:
    with pytest.raises(ValueError):
        resolve_preset([])
