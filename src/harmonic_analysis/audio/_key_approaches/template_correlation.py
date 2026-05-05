"""Krumhansl-Schmuckler template correlation as a KeyDetectionApproach.

Direct port of ``find_best_key`` from ``_key_estimation.py``. The behavior
must be bit-identical — AC-02 asserts that ``key_detection="ks_only"``
produces the same KeyInfo (to 4 decimal places) as the pre-ensemble code
path. Don't get clever with the math here. The thin wrapper in
``_key_estimation.py`` calls this class's ``detect()`` and pulls out the
top-1; if anything drifts, both that wrapper and AC-02 will tell us.

The K-S profiles only know "major" and "minor" — i.e. Ionian and Aeolian.
That's the whole point of ensembling: this approach can't tell relative
pairs apart, so we let the others vote.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np

from .._key_ensemble import (
    KeyDetectionApproach,
    KeyDetectionContext,
    KeyDetectionVerdict,
)
from .._profiles import KS_PROFILES, PITCH_CLASSES
from .._types import KeyInfo

# Same map as _key_estimation.py uses. Output uses Ionian/Aeolian for
# round-trip compatibility with the toolkit.
_MODE_MAP: Dict[str, str] = {"major": "Ionian", "minor": "Aeolian"}


class TemplateCorrelationApproach(KeyDetectionApproach):
    """Pure K-S correlation, packaged as a protocol-conformant approach.

    Computes Pearson correlation between the chroma vector and each of
    the 24 rolled K-S profiles. Returns all 24 candidates ranked by
    score — downstream synthesis decides how many actually matter.
    Returning the full ranking (not just top-K) lets the synthesizer
    accumulate per-approach evidence across all candidates instead of
    losing tail signal.
    """

    name: str = "template_correlation"

    def detect(self, ctx: KeyDetectionContext) -> KeyDetectionVerdict:
        """Score all 24 keys via K-S correlation.

        Args:
            ctx: KeyDetectionContext. Only ``chroma_1d`` is consulted.

        Returns:
            KeyDetectionVerdict with all 24 (KeyInfo, score) pairs sorted
            highest-score-first. Confidence in each KeyInfo is the per-key
            raw correlation mapped to [0,1] — same ``round(c, 4)``
            quantization as the original to preserve bit-identity.
        """
        chroma_vector = np.asarray(ctx.chroma_1d, dtype=float)

        # Zero-energy guard — without this, np.corrcoef returns NaN against
        # any constant input and downstream confidence math goes sideways.
        # Match the original's behavior exactly.
        if np.linalg.norm(chroma_vector) < 1e-6:
            na_key = KeyInfo(
                tonic="N/A",
                mode="N/A",
                key_signature="N/A",
                confidence=0.0,
            )
            # Single N/A entry. Synthesizer treats this as "no signal" but
            # a non-empty ranked list still satisfies AC-03's contract.
            return KeyDetectionVerdict(
                name=self.name,
                ranked=[(na_key, 0.0)],
                meta={"zero_energy": True},
            )

        # Compute all 24 correlations in the same order as the original.
        # This ordering is load-bearing for tie-breaking — the original
        # ``max(correlations, key=...)`` picks the first key encountered
        # on a tie, which is dict-insertion order: tonic-major-then-minor
        # for each pitch class C through B.
        correlations: Dict[str, float] = {}
        candidate_keys: Dict[str, KeyInfo] = {}

        for tonic_pc, tonic_name in enumerate(PITCH_CLASSES):
            for mode_name, profile_data in KS_PROFILES.items():
                profile = np.roll(np.asarray(profile_data, dtype=float), tonic_pc)
                corr = float(np.corrcoef(chroma_vector, profile)[0, 1])
                key_str = f"{tonic_name} {mode_name}"
                correlations[key_str] = corr

                # Per-key confidence — same Pearson-to-[0,1] mapping the
                # original applied to the winner. Each candidate's
                # KeyInfo carries its own confidence value, which is what
                # appears in the diagnostic panel.
                if np.isnan(corr):
                    confidence = 0.0
                else:
                    confidence = (corr + 1.0) / 2.0
                candidate_keys[key_str] = KeyInfo(
                    tonic=tonic_name,
                    mode=_MODE_MAP.get(mode_name, mode_name),
                    key_signature=key_str,
                    confidence=round(confidence, 4),
                )

        # Build the ranked list. We sort by the RAW correlation (not the
        # rounded confidence) so ties come out in the same order as the
        # original ``max(correlations, key=...)`` — the rounding to 4
        # decimal places would otherwise create false ties between keys
        # whose correlations differ in the 5th decimal. Bit-identity is
        # the AC-02 contract; this is how we keep it.
        #
        # The score handed to the synthesizer is the rounded confidence
        # (in [0,1]) because raw correlations can be negative and the
        # synthesizer's weighted-sum logic doesn't want to subtract from
        # other approaches' positive votes.
        decorated: List[Tuple[float, str, KeyInfo]] = []
        for key_str, corr in correlations.items():
            key_info = candidate_keys[key_str]
            # NaN correlations sort to the bottom — they're zero-confidence.
            sort_corr = corr if not np.isnan(corr) else float("-inf")
            decorated.append((sort_corr, key_str, key_info))

        # Stable sort on raw correlation, descending. Python's sort is
        # stable, so the dict-insertion order breaks ties — matches the
        # original ``max()`` semantics exactly.
        decorated.sort(key=lambda x: x[0], reverse=True)
        ranked: List[Tuple[KeyInfo, float]] = [
            (ki, ki.confidence) for _, _, ki in decorated
        ]

        return KeyDetectionVerdict(
            name=self.name,
            ranked=ranked,
            meta={"raw_correlations": correlations},
        )
