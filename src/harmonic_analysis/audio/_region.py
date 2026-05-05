"""Region classification: stable / modulation / modal_shift.

Port of the toolkit's ``classify_region_type`` (utils.py:110–151). The
second and final library substitution lives here: where the toolkit asked
its theory library for the scale pitches, we now read
``key_info.diatonic_pitch_classes`` straight off the dataclass — same
information, no library round-trip.

Three outcomes:

* ``stable`` — global and local key match by name.
* ``modulation`` — local key strongly established with a real cadence.
* ``modal_shift`` — borrowed harmony without a full key change (the
  fallback bucket).

The thresholds (0.80 confidence, 0.60 cadence strength, 0.15 borrowed-note
penalty) are heuristic constants from the toolkit. They're not "correct"
in any deep sense — they're tuned empirically for the toolkit's chroma
front-end and preserved verbatim for behavioral parity.
"""

from __future__ import annotations

import numpy as np

from ._profiles import PITCH_CLASSES
from ._types import CadenceInfo, KeyInfo, RegionInfo


def classify_region_type(
    global_key: KeyInfo,
    local_key: KeyInfo,
    local_key_confidence: float,
    local_cadence: CadenceInfo,
) -> RegionInfo:
    """Classify a local segment relative to the global key.

    Args:
        global_key: The piece-level key estimate.
        local_key: The segment-level key estimate.
        local_key_confidence: Confidence in the local key — usually
            ``local_key.confidence``, but exposed separately so callers can
            override (e.g. blend with a temporal smoothing factor).
        local_cadence: Cadence info for the local segment.

    Returns:
        ``RegionInfo(type, confidence, borrowed)``. ``borrowed`` is the list
        of pitch-class names found in the local key but not the global key.
    """
    # Stable: same key by name. Skip the set math entirely — borrowed list
    # is empty by definition.
    if global_key.key_signature == local_key.key_signature:
        return RegionInfo(type="stable", confidence=0.95, borrowed=[])

    # Second library substitution: read the precomputed diatonic pitch-class
    # set off KeyInfo instead of asking the upstream theory library for the
    # scale pitches.
    borrowed_pcs = local_key.diatonic_pitch_classes - global_key.diatonic_pitch_classes
    # Sort for stable output — frozenset iteration order is undefined and
    # tests want deterministic results.
    borrowed_notes = [PITCH_CLASSES[pc] for pc in sorted(borrowed_pcs)]

    # Modulation criteria — strongly-established new key with a real cadence.
    is_modulation = (
        local_key_confidence > 0.80
        and local_cadence.detected
        and local_cadence.strength > 0.60
    )

    if is_modulation:
        # 50/50 weighted average of key confidence and cadence strength.
        confidence = (local_key_confidence * 0.5) + (local_cadence.strength * 0.5)
        return RegionInfo(
            type="modulation",
            confidence=float(np.round(confidence, 2)),
            borrowed=borrowed_notes,
        )

    # Fallback: borrowed harmony without a confirmed key change. Confidence
    # decays with each borrowed note (more outside-key tones = noisier
    # classification), floored at 0.5 so we never claim a coin-flip.
    confidence = max(0.5, 1.0 - (len(borrowed_notes) * 0.15))
    return RegionInfo(
        type="modal_shift",
        confidence=float(np.round(confidence, 2)),
        borrowed=borrowed_notes,
    )
