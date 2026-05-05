"""Bass-dominance scoring approach.

The bass register tells you what the listener perceives as the tonic
much more reliably than the time-averaged full-spectrum chroma. K-S
sees Bm and D major as identical pitch-class sets — both contain
{B, D, F#, ...}. The bass register, on the other hand, screams "B" in
the Bm case and "D" in the D-major case.

This approach takes the bass chroma vector (already extracted by
``_io.extract_local_bass_chroma`` and time-averaged), normalizes it,
and scores each key by how much the tonic and dominant pitch classes
dominate. A pure single-bass-note recording produces a sharp peak; a
walking-bass-line recording produces a more diffuse pattern.

Empty bass_chroma_1d: returns an empty ranked list. Synthesizer treats
this as "no opinion" — same contract as the other approaches.
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np

from .._key_ensemble import (
    KeyDetectionApproach,
    KeyDetectionContext,
    KeyDetectionVerdict,
)
from .._profiles import PITCH_CLASSES
from .._types import KeyInfo

# Bass scoring weights. Tonic is the dominant signal in the bass; the
# perfect 5th below tonic (= dominant) is the second strongest. Mediant
# bass tones happen but rarely dominate.
_TONIC_BASS_WEIGHT = 1.0
_DOMINANT_BASS_WEIGHT = 0.4


class BassDominanceApproach(KeyDetectionApproach):
    """Score keys by how strongly the bass emphasizes tonic + dominant.

    The bass chroma is already 12-bin (octaves collapsed). Each candidate
    key receives a score = tonic_weight * bass[tonic_pc] + dominant_weight
    * bass[dominant_pc], normalized by the bass vector's L1 norm so the
    output sits in [0, 1].
    """

    name: str = "bass_dominance"

    def detect(self, ctx: KeyDetectionContext) -> KeyDetectionVerdict:
        """Score each of 24 keys by bass-chroma weighting.

        Args:
            ctx: KeyDetectionContext. Consults ``bass_chroma_1d`` only.

        Returns:
            KeyDetectionVerdict with up to 24 ranked candidates. When
            ``bass_chroma_1d`` is None, returns an empty ranked list.
        """
        bass = ctx.bass_chroma_1d
        if bass is None:
            return KeyDetectionVerdict(
                name=self.name,
                ranked=[],
                meta={"reason": "no_bass_chroma"},
            )

        bass_arr = np.asarray(bass, dtype=float)
        if bass_arr.shape != (12,):
            # Defensive — caller passed something other than a 12-vector.
            # Don't crash the whole ensemble; downgrade to "no opinion".
            return KeyDetectionVerdict(
                name=self.name,
                ranked=[],
                meta={"reason": f"bad_bass_shape:{bass_arr.shape}"},
            )

        # Normalize so scoring is invariant to overall bass loudness.
        # Some bass-quiet recordings still have a perfectly clear bass
        # *pattern* — we want the relative emphasis, not absolute energy.
        total = float(bass_arr.sum())
        if total <= 0:
            return KeyDetectionVerdict(
                name=self.name,
                ranked=[],
                meta={"reason": "zero_bass_energy"},
            )
        normalized = bass_arr / total

        ranked: List[Tuple[KeyInfo, float]] = []

        # Max raw score = sum of weights (tonic and dominant fully claimed).
        max_raw = _TONIC_BASS_WEIGHT + _DOMINANT_BASS_WEIGHT

        for tonic_pc, tonic_name in enumerate(PITCH_CLASSES):
            dominant_pc = (tonic_pc + 7) % 12

            tonic_share = float(normalized[tonic_pc])
            dominant_share = float(normalized[dominant_pc])

            raw_score = (
                _TONIC_BASS_WEIGHT * tonic_share
                + _DOMINANT_BASS_WEIGHT * dominant_share
            )
            score = raw_score / max_raw if max_raw > 0 else 0.0

            for mode_label in ("Ionian", "Aeolian"):
                key_is_minor = mode_label == "Aeolian"
                key_str = f"{tonic_name} {'major' if not key_is_minor else 'minor'}"
                key_info = KeyInfo(
                    tonic=tonic_name,
                    mode=mode_label,
                    key_signature=key_str,
                    confidence=round(score, 4),
                )
                ranked.append((key_info, score))

        ranked.sort(key=lambda pair: pair[1], reverse=True)

        return KeyDetectionVerdict(
            name=self.name,
            ranked=ranked,
            meta={
                "dominant_bass_pc": int(np.argmax(normalized)),
                "bass_distribution": normalized.tolist(),
            },
        )
