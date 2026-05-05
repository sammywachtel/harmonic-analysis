"""Pluggable key-detection ensemble: protocol, context, verdict, synthesizer.

The single-algorithm Krumhansl-Schmuckler estimator can't tell relative pairs
apart (D Ionian vs B Aeolian have identical pitch-class sets). That's a
fundamental limitation of correlating against pitch-class profiles. The fix
isn't a smarter K-S — it's adding orthogonal evidence (boundary chords, bass
dominance, cadential motion) and letting them vote.

This module defines the contract every approach implements (the
``KeyDetectionApproach`` protocol), the data carrier that flows from caller
to approaches (``KeyDetectionContext``), the per-approach output
(``KeyDetectionVerdict``), and the weighted-sum aggregator
(``KeyEnsembleSynthesizer``) that turns N verdicts into one ``SynthesisResult``.

Implementations live in ``_key_approaches/``. The orchestration (which
approaches run, which weights apply, when chord events are available) is in
``integrations/audio_adapter.py``'s ``from_audio()`` — the ensemble doesn't
know how to extract chroma, and chroma extraction doesn't know about the
ensemble. Keeping that separation lets each layer evolve independently.

A note on KeyInfo: it lives in ``_types.py`` and is frozen. Adding fields
to it would break tests locked by audio_score_alignment-01. The new
ensemble result types belong here, not over there.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Tuple, Union

import numpy as np

from ._types import KeyInfo

# Default weights for each approach. Conversation-derived starting points.
# 1.0 / 0.8 / 0.6 / 0.7 / 1.2 / variable — these came from intuition, not
# data. Real-world performance may force tuning. Iteration_02 owns the
# ``pattern_engine`` and ``hmm`` slots; populated here so the table is
# complete at import time and presets can reference all five.
DEFAULT_WEIGHTS: Dict[str, float] = {
    "template_correlation": 1.0,
    "boundary_chords": 0.8,
    "bass_dominance": 0.6,
    "cadential": 0.7,
    "pattern_engine": 0.9,
    "hmm": 0.5,
}

# Approach name groupings keyed by preset string. The "default" set is the
# four iteration_01 defaults. "ks_only" mirrors the pre-ensemble code path
# for backward compat. "full" turns everything on, but in iteration_01 the
# opt-ins haven't shipped yet — the resolver guards against missing
# implementations elsewhere; here we just enumerate names.
_PRESET_APPROACHES: Dict[str, List[str]] = {
    "default": [
        "template_correlation",
        "boundary_chords",
        "bass_dominance",
        "cadential",
    ],
    "ks_only": ["template_correlation"],
    "full": [
        "template_correlation",
        "boundary_chords",
        "bass_dominance",
        "cadential",
        "pattern_engine",
        "hmm",
    ],
}


@dataclass(frozen=True)
class KeyDetectionContext:
    """Pre-computed inputs handed to every approach.

    Optional fields let lightweight approaches (template_correlation only
    needs chroma) ignore expensive inputs they don't use. The two-stage
    pipeline puts chord_events behind None on stage 1 — when only the K-S
    pass has run, the chord-event-dependent approaches will degrade
    gracefully rather than blow up.

    Attributes:
        chroma_1d: Time-averaged 12-bin chroma vector. Required.
        bass_chroma_1d: Optional 12-bin bass-register chroma. None means
            the caller didn't extract it.
        chord_events: Optional list of ChordEvent (typed loosely as object
            to avoid the import dance — adapter passes the real ones).
            None when running before chord estimation.
        hmm_segments: Optional HMM segmentation output. iteration_02 only.
        audio_path: Optional path to the source audio. Some opt-in
            approaches re-extract chroma per segment; defaults rarely care.
    """

    chroma_1d: np.ndarray
    bass_chroma_1d: Optional[np.ndarray] = None
    chord_events: Optional[List[object]] = None
    hmm_segments: Optional[List[object]] = None
    audio_path: Optional[str] = None


@dataclass(frozen=True)
class KeyDetectionVerdict:
    """Output of one approach: ranked candidates with a name tag.

    The ranked list preserves order naturally and matches the diagnostic
    panel's "top_3" display. A dict-of-scores would force a re-sort at
    every consumer.

    Attributes:
        name: Approach identifier (e.g. "template_correlation"). Must
            match a key in DEFAULT_WEIGHTS for the synthesizer to
            apply weight correctly.
        ranked: List of (KeyInfo, score) pairs, sorted highest-score-first.
            Empty list signals "no opinion" (e.g. cadential approach with
            no V-I cadences in the chord events).
        meta: Optional per-approach diagnostic data. Surfaced in the
            details panel when show_analysis_details=True.
    """

    name: str
    ranked: List[Tuple[KeyInfo, float]]
    meta: Optional[Dict[str, object]] = None


@dataclass(frozen=True)
class SynthesisResult:
    """Output of the ensemble synthesizer.

    Attributes:
        method: Synthesis method tag. iteration_01 only ships
            "weighted_sum"; future methods (median, max, etc.) would
            tag themselves here.
        winner: KeyInfo with the highest weighted-sum total.
        runner_up: KeyInfo in second place. None when only one candidate
            received any score (rare — every approach scores 24 keys).
        margin: ``winner_total - runner_up_total``. Confidence proxy for
            "how much did the ensemble agree." Zero when there's a tie.
        key_score_table: All candidates sorted by total weighted score.
            Useful for the diagnostic panel and for debugging weight
            tuning.
        per_approach: List of (approach_name, weight) actually used in
            the synthesis. Reflects what was wired up at runtime, not
            what's in the static DEFAULT_WEIGHTS table.
    """

    method: str
    winner: KeyInfo
    runner_up: Optional[KeyInfo]
    margin: float
    key_score_table: Dict[str, float]
    per_approach: List[Tuple[str, float]] = field(default_factory=list)


class KeyDetectionApproach(Protocol):
    """Contract every key-detection approach must satisfy.

    Each implementation lives in ``_key_approaches/``. The protocol is
    structural — no inheritance required, just a class with a ``name``
    attribute and a ``detect`` method. This keeps tests clean (mock
    objects with the right shape work) and avoids coupling approaches
    to a base class.

    A note on the empty-input contract: every approach must return a
    valid ``KeyDetectionVerdict`` (potentially with an empty ranked list
    or uniform low scores) when its inputs are missing. The two-stage
    pipeline runs some approaches in stage 1 with chord_events=None, and
    we'd rather get a no-op verdict than a crash. Crashes here would
    take down the whole ensemble.
    """

    name: str

    def detect(self, ctx: KeyDetectionContext) -> KeyDetectionVerdict:
        """Score key candidates given the context. Must not raise on
        missing optional context fields — return a low-confidence or
        empty verdict instead.
        """
        ...


class KeyEnsembleSynthesizer:
    """Weighted-sum synthesizer over per-approach verdicts.

    Pure data transformation. No I/O, no chroma extraction — give it
    verdicts plus weights, get back a winner. Testable in isolation with
    constructed mock verdicts (see tests/audio/test_key_ensemble.py).

    Method:
        For each (KeyInfo, score) tuple in each approach's ranked list,
        add ``score * weights[approach_name]`` to that key's running
        total. After all verdicts are processed, the key with the
        highest total wins. Margin is ``winner_total - runner_up_total``.

    Tie-breaking:
        When two keys score identically, the first one encountered in
        the iteration order wins. Pythonic dict ordering (insertion
        order) makes this deterministic per run, even though the actual
        winner depends on which approach voted first. This is a known
        wart we accept for iteration_01 — explicit tie-break rules
        (e.g. "prefer minor on equal score") could be added later.
    """

    method_name: str = "weighted_sum"

    def synthesize(
        self,
        verdicts: List[KeyDetectionVerdict],
        weights: Optional[Dict[str, float]] = None,
    ) -> SynthesisResult:
        """Combine verdicts into a single SynthesisResult.

        Args:
            verdicts: Per-approach verdicts. Empty list raises ValueError —
                synthesis with nothing to synthesize is a programming
                error upstream, not a graceful-degradation case.
            weights: Override weights. None = use DEFAULT_WEIGHTS.
                Approaches with no weight entry default to 0.0 (their
                votes don't count). This is intentional — surfacing an
                unknown approach via a silent skip is safer than
                guessing a default.

        Returns:
            SynthesisResult with winner, runner_up, margin, and the full
            score table for diagnostic display.

        Raises:
            ValueError: If ``verdicts`` is empty.
        """
        if not verdicts:
            raise ValueError(
                "synthesize() requires at least one verdict — empty input "
                "indicates an upstream wiring bug, not a recoverable state."
            )

        effective_weights = weights if weights is not None else DEFAULT_WEIGHTS

        # Running totals keyed by the KeyInfo's key_signature string.
        # We use string keys because KeyInfo is frozen but contains a
        # frozenset (diatonic_pitch_classes) — equality works fine, but
        # using the string key keeps the score table directly serializable
        # for the diagnostic panel.
        score_table: Dict[str, float] = {}
        # Map key_signature back to the canonical KeyInfo for the winner
        # lookup. Multiple approaches may produce slightly different
        # KeyInfo instances (different confidence values per approach);
        # we keep the first one we see.
        key_lookup: Dict[str, KeyInfo] = {}

        per_approach: List[Tuple[str, float]] = []

        for verdict in verdicts:
            weight = effective_weights.get(verdict.name, 0.0)
            per_approach.append((verdict.name, weight))

            # Skip the approach entirely when its weight is zero —
            # avoids polluting the score table with zero contributions
            # and matches the user's mental model of "weight 0 = off."
            if weight == 0.0:
                continue

            for key_info, score in verdict.ranked:
                sig = key_info.key_signature
                score_table[sig] = score_table.get(sig, 0.0) + score * weight
                if sig not in key_lookup:
                    key_lookup[sig] = key_info

        if not score_table:
            # All approaches had weight 0 or empty ranked lists. Best we can
            # do: return the first verdict's first ranked item if any, else
            # an N/A sentinel. Either way the caller has no useful signal.
            for v in verdicts:
                if v.ranked:
                    fallback_key, _ = v.ranked[0]
                    return SynthesisResult(
                        method=self.method_name,
                        winner=fallback_key,
                        runner_up=None,
                        margin=0.0,
                        key_score_table={},
                        per_approach=per_approach,
                    )
            # No ranked entries anywhere — synthesize an N/A sentinel.
            na_key = KeyInfo(
                tonic="N/A",
                mode="N/A",
                key_signature="N/A",
                confidence=0.0,
            )
            return SynthesisResult(
                method=self.method_name,
                winner=na_key,
                runner_up=None,
                margin=0.0,
                key_score_table={},
                per_approach=per_approach,
            )

        # Sort by total score descending. Ties broken by dict insertion
        # order (whichever approach voted first wins) — see class docstring
        # for the ugly truth.
        ranked_keys = sorted(score_table.items(), key=lambda kv: kv[1], reverse=True)

        winner_sig, winner_total = ranked_keys[0]
        winner = key_lookup[winner_sig]

        runner_up: Optional[KeyInfo] = None
        margin = 0.0
        if len(ranked_keys) > 1:
            runner_up_sig, runner_up_total = ranked_keys[1]
            runner_up = key_lookup[runner_up_sig]
            margin = winner_total - runner_up_total

        return SynthesisResult(
            method=self.method_name,
            winner=winner,
            runner_up=runner_up,
            margin=margin,
            key_score_table=dict(ranked_keys),
            per_approach=per_approach,
        )


def resolve_preset(
    spec: Union[str, List[str], Dict[str, float]]
) -> Tuple[List[str], Dict[str, float]]:
    """Translate a key_detection spec into (approach_names, weights).

    Three input shapes:
        * str: preset name from _PRESET_APPROACHES ("default" | "ks_only"
          | "full"). Returns the preset's approach list with default
          weights.
        * list[str]: explicit list of approach names. Uses default weights.
        * dict[str, float]: approach-name → weight mapping. Both the names
          and weights come from the dict; missing approaches are simply
          excluded.

    Args:
        spec: Preset name, name list, or weight dict.

    Returns:
        Tuple of (approach_names, weights_dict).

    Raises:
        ValueError: For unknown preset names or empty lists.
    """
    if isinstance(spec, str):
        if spec not in _PRESET_APPROACHES:
            valid = ", ".join(sorted(_PRESET_APPROACHES))
            raise ValueError(
                f"Unknown key_detection preset {spec!r}. " f"Valid presets: {valid}."
            )
        names = list(_PRESET_APPROACHES[spec])
        weights = {name: DEFAULT_WEIGHTS.get(name, 0.0) for name in names}
        return names, weights

    if isinstance(spec, dict):
        if not spec:
            raise ValueError("key_detection dict is empty — nothing to run.")
        names = list(spec.keys())
        # User-supplied weights win; we don't blend with defaults because
        # that would surprise people who pass a dict expecting it to be
        # the complete spec.
        weights = {k: float(v) for k, v in spec.items()}
        return names, weights

    if isinstance(spec, list):
        if not spec:
            raise ValueError("key_detection list is empty — nothing to run.")
        names = list(spec)
        weights = {name: DEFAULT_WEIGHTS.get(name, 0.0) for name in names}
        return names, weights

    raise ValueError(
        f"key_detection must be str, list, or dict; got {type(spec).__name__}."
    )
