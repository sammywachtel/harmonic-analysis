"""Boundary-chord scoring approach.

Music theory's most reliable signal for "what key is this in" is what
the piece starts and ends on. The first and last chord events of a tonal
piece are usually i/I (with a v-i or V-I just before the close). Real
recordings violate this — anacruses, fade-outs, modal pivots — but the
first/last sample is still strong evidence on aggregate.

This approach scores each candidate (tonic, mode) by checking whether the
first and last chord events match either the tonic or the dominant of
that key. Tonic match gets the full score; dominant match gets a smaller
bonus (the V→i bookend pattern is common, especially in classical).

Empty chord_events: returns an empty ranked list. The synthesizer treats
this as "no opinion" and the approach contributes nothing to the total.
This is the graceful-degradation contract documented in
KeyDetectionApproach.

Real-audio gotcha (iteration_01_a fix): the chord estimator faithfully
emits events for silent lead-in and trailing decay, where it has no real
harmonic content to score. Those low-confidence/short-duration events
reflect tonal_bias defaulting to the global K-S key, not actual played
chords. We filter by ``min_confidence`` and ``min_duration_s`` before
selecting boundaries so the approach scores on chords the performer
actually played, not the chord estimator's nervous tic on room tone.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from .._key_ensemble import (
    KeyDetectionApproach,
    KeyDetectionContext,
    KeyDetectionVerdict,
)
from .._profiles import PITCH_CLASSES
from .._types import KeyInfo

# Score weights for the boundary check. Tonic match is worth more than
# dominant match — a tonic ending is the canonical resolution. These
# values are intuition-derived; they only need to be relative since the
# synthesizer applies the per-approach weight on top.
_TONIC_BONUS = 1.0
_DOMINANT_BONUS = 0.4

# Default thresholds for filtering boundary-eligible events. Surfaced
# as instance fields so callers can tune them without source edits.
# 0.85 sits well above the ~0.82 of silent-lead-in K-S fallback artifacts
# and well below the 0.94+ of real sustained chords. 0.5s filters
# momentary decay-tail events without rejecting legitimately brief endings.
_DEFAULT_MIN_CONFIDENCE = 0.85
_DEFAULT_MIN_DURATION_S = 0.5


def _root_pitch_class(chord_label: str) -> Optional[int]:
    """Extract pitch-class index from a chord label.

    Handles every label the chord estimator can emit: 'C', 'C#', 'Cm',
    'C#m', 'Bm', 'C7', 'Cm7', 'Cmaj7', 'Cdim', 'Cdim7', 'Cm7b5', etc.
    Returns None for unparseable labels so callers don't have to wrap
    in try/except.
    """
    if not chord_label:
        return None
    if len(chord_label) >= 2 and chord_label[1] == "#":
        root_name = chord_label[:2]
    else:
        root_name = chord_label[:1]
    try:
        return PITCH_CLASSES.index(root_name)
    except ValueError:
        return None


def _is_minor_label(chord_label: str) -> bool:
    """True if the chord is functionally minor.

    'Cm', 'Am', 'F#m' → True. 'Cm7', 'Am7' → True (still minor).
    'C', 'G7', 'Cmaj7' → False (major). 'Cdim', 'Cdim7', 'Cm7b5' →
    False (diminished/half-dim aren't really minor for boundary
    purposes — they wouldn't function as a minor tonic).
    """
    if not chord_label:
        return False
    suffix = (
        chord_label[2:]
        if len(chord_label) >= 2 and chord_label[1] == "#"
        else chord_label[1:]
    )
    # 'maj7' starts with 'm' but is decidedly major — special-case it.
    if suffix.startswith("maj"):
        return False
    # Plain 'm' or 'm' followed by '7' / nothing → minor.
    # 'm7b5' is half-diminished, not minor in the boundary sense.
    if suffix == "m" or suffix == "m7":
        return True
    return False


class BoundaryChordsApproach(KeyDetectionApproach):
    """Score keys by first/last chord event matching tonic or dominant.

    The "first" event is the first chord_events entry that meets both
    ``min_confidence`` AND ``min_duration_s`` thresholds; "last" is the
    last such entry. Pre-filtering keeps the chord estimator's silent-
    lead-in and trailing-decay artifacts from poisoning the boundary
    signal — those events have low confidence (~0.82) and/or short
    duration (<0.5s) compared to legitimately played chords (>=0.94
    confidence, >=1s sustained).

    We do NOT respect the time bounds beyond duration filtering because
    the chord estimator already consolidates consecutive identical
    labels, so the first qualifying event IS the opening section's
    chord (post-silence).
    """

    name: str = "boundary_chords"
    # Instance-level configuration. Defaults match the locked spec from
    # the iteration_01_a fix; subclasses or call sites can override
    # without rewriting this module.
    min_confidence: float = _DEFAULT_MIN_CONFIDENCE
    min_duration_s: float = _DEFAULT_MIN_DURATION_S

    def __init__(
        self,
        min_confidence: float = _DEFAULT_MIN_CONFIDENCE,
        min_duration_s: float = _DEFAULT_MIN_DURATION_S,
    ) -> None:
        """Construct with optional threshold overrides.

        Args:
            min_confidence: Minimum chord-event confidence to qualify
                as a boundary signal. Default 0.85 — above silent-
                lead-in artifacts (~0.82), below real chords (>=0.94).
            min_duration_s: Minimum sustained duration (end - start)
                in seconds to qualify. Default 0.5s — filters momentary
                decay-tail noise without rejecting legitimate brief
                endings.
        """
        self.min_confidence = min_confidence
        self.min_duration_s = min_duration_s

    def detect(self, ctx: KeyDetectionContext) -> KeyDetectionVerdict:
        """Score each of 24 keys by boundary-chord match.

        Args:
            ctx: KeyDetectionContext. Consults ``chord_events`` only.

        Returns:
            KeyDetectionVerdict with up to 24 ranked candidates. When
            chord_events is None, empty, or has no events meeting
            both threshold filters, returns an empty ranked list with
            ``meta["reason"]`` populated (synthesizer treats this as
            "no opinion").
        """
        events = ctx.chord_events
        if not events:
            # Graceful degradation — empty list, not a crash.
            return KeyDetectionVerdict(
                name=self.name,
                ranked=[],
                meta={"reason": "no_chord_events"},
            )

        # Filter to events that look like real played chords. We compute
        # duration on the fly because ChordEvent doesn't carry a
        # duration_s attribute — it's just (end - start). getattr() with
        # defaults keeps the protocol structural; fakes in tests don't
        # need to grow new fields to pass.
        qualifying = [
            e
            for e in events
            if getattr(e, "confidence", 0.0) >= self.min_confidence
            and (getattr(e, "end_time", 0.0) - getattr(e, "start_time", 0.0))
            >= self.min_duration_s
        ]

        if not qualifying:
            # All events failed at least one threshold — typical of an
            # all-noise input or a recording where the chord estimator
            # was running on near-silent chroma the whole time.
            return KeyDetectionVerdict(
                name=self.name,
                ranked=[],
                meta={
                    "reason": "no_qualifying_events",
                    "min_confidence": self.min_confidence,
                    "min_duration_s": self.min_duration_s,
                    "events_seen": len(events),
                },
            )

        # Pull off the first and last QUALIFYING events. Single-event
        # qualifying sequences mean opener == closer, which is fine —
        # the score just doubles the tonic match for that one chord.
        first_chord = qualifying[0]
        last_chord = qualifying[-1]

        first_label = getattr(first_chord, "chord_label", None)
        last_label = getattr(last_chord, "chord_label", None)

        first_pc = _root_pitch_class(first_label) if first_label else None
        last_pc = _root_pitch_class(last_label) if last_label else None
        first_minor = _is_minor_label(first_label) if first_label else False
        last_minor = _is_minor_label(last_label) if last_label else False

        # Normalize raw scores into [0,1] for the synthesizer. Max
        # possible raw score is 2 * _TONIC_BONUS (both ends match tonic
        # AND quality) — see scoring loop below.
        max_raw = 2 * (_TONIC_BONUS + _DOMINANT_BONUS)

        ranked: List[Tuple[KeyInfo, float]] = []

        for tonic_pc, tonic_name in enumerate(PITCH_CLASSES):
            for mode_label in ("Ionian", "Aeolian"):
                key_is_minor = mode_label == "Aeolian"
                # Dominant pitch class is the perfect 5th above tonic.
                # Pop convention; works for both major and minor keys.
                dominant_pc = (tonic_pc + 7) % 12

                raw = 0.0

                # First-chord scoring
                if first_pc is not None:
                    if first_pc == tonic_pc:
                        # Bonus is full when the chord quality also matches
                        # the key's tonic chord (major key → major chord,
                        # minor key → minor chord). Wrong-quality matches
                        # still count — Picardy thirds and modal pivots
                        # exist — but at reduced weight.
                        if first_minor == key_is_minor:
                            raw += _TONIC_BONUS
                        else:
                            raw += _TONIC_BONUS * 0.5
                    elif first_pc == dominant_pc:
                        # Dominant openings are rarer but happen (V-I-IV
                        # sequences). Quality match check less strict —
                        # V is major in both keys.
                        raw += _DOMINANT_BONUS

                # Last-chord scoring (mirror of first)
                if last_pc is not None:
                    if last_pc == tonic_pc:
                        if last_minor == key_is_minor:
                            raw += _TONIC_BONUS
                        else:
                            raw += _TONIC_BONUS * 0.5
                    elif last_pc == dominant_pc:
                        raw += _DOMINANT_BONUS

                normalized = raw / max_raw if max_raw > 0 else 0.0

                key_str = f"{tonic_name} {'major' if not key_is_minor else 'minor'}"
                key_info = KeyInfo(
                    tonic=tonic_name,
                    mode=mode_label,
                    key_signature=key_str,
                    confidence=round(normalized, 4),
                )
                ranked.append((key_info, normalized))

        ranked.sort(key=lambda pair: pair[1], reverse=True)

        return KeyDetectionVerdict(
            name=self.name,
            ranked=ranked,
            meta={
                # These reflect the QUALIFYING boundaries used for
                # scoring, not the raw events[0] / events[-1]. The
                # diagnostic panel's job is to show what the approach
                # actually scored against, otherwise the silent-lead-in
                # bug we just fixed becomes invisible again.
                "first_chord": first_label,
                "last_chord": last_label,
                "qualifying_count": len(qualifying),
                "events_seen": len(events),
            },
        )
