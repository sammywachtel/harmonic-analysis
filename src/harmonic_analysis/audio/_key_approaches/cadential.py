"""Cadential V→i / V→I scoring approach.

Cadences are the strongest functional signal in tonal music — they're
literally the harmonic punctuation that establishes "here's the tonic."
Scanning the chord event sequence for V→I (major key) and V→i (minor
key) transitions, then scoring each candidate key by how many of its
diagnostic cadences appear, is one of the most musically grounded ways
to break a relative-pair tie.

Limitations honestly disclosed:
    * The chord estimator only recognizes major/minor triads. No V7
      (which would be a stronger cadential signal). No diminished VII°
      either.
    * We score perfect cadences (V→I or V→i) only. Plagal (IV→I),
      deceptive (V→vi), and half-cadences are treated as non-events
      because they're ambiguous between candidate keys.

iteration_01_a fix — mode-agnostic crediting:
    Cadential's job is to identify *which tonic root* receives a
    cadential resolution. It is NOT cadential's job to pre-decide major
    vs. minor — that's what the synthesizer + bass_dominance + K-S
    template fit do, with orthogonal evidence. The previous code
    branched on the tonic chord's quality and credited only the matching
    mode (Ionian for major tonic, Aeolian for minor tonic), which
    produced a silent major-bias bug: F#→Bm (a textbook minor authentic
    cadence — V in minor is always major) scored zero for B Aeolian on
    real recordings. We now credit BOTH Ionian and Aeolian slots equally
    when a major-V resolves to any tonic chord; the rest of the ensemble
    sorts mode out.

Empty chord_events: returns an empty ranked list — graceful degradation
contract.
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


def _root_pitch_class(chord_label: str) -> Optional[int]:
    """Extract pitch-class index from a chord label, or None.

    Handles every label the chord estimator can emit: 'C', 'C#', 'Cm',
    'C7', 'Cm7', 'Cmaj7', 'Cdim7', 'Cm7b5', etc.
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
    """True if the chord cannot function as a major dominant.

    Cadential V→I detection wants to know "is the V chord NOT a major
    or dominant-7 triad?" — minor V's, diminished V's, half-dim V's
    don't count as standard authentic cadences. So 'Cm', 'Cm7', 'Cdim',
    'Cdim7', 'Cm7b5' return True; 'C', 'C7', 'Cmaj7' return False.
    """
    if not chord_label:
        return False
    suffix = (
        chord_label[2:]
        if len(chord_label) >= 2 and chord_label[1] == "#"
        else chord_label[1:]
    )
    if suffix.startswith("maj"):
        return False  # 'Cmaj7' — major, OK as V
    if suffix == "" or suffix == "7":
        return False  # 'C', 'C7' — major or dominant, OK as V
    # Anything else ('m', 'm7', 'dim', 'dim7', 'm7b5') — not a major V.
    return True


class CadentialApproach(KeyDetectionApproach):
    """Score keys by counting major-V → tonic resolutions (mode-agnostic).

    Walks the chord_events list looking for adjacent (a, b) pairs where
    ``a`` is a major triad whose root is the dominant of ``b``'s root.
    When found, both Ionian and Aeolian candidates of the resolved tonic
    receive equal credit — cadential identifies that there's a cadence
    on this tonic root, not which parallel-mode the piece is in.

    For each (major V → tonic) pair we credit:
        cadence_counts[tonic_pc * 2]     += 1   # Ionian slot
        cadence_counts[tonic_pc * 2 + 1] += 1   # Aeolian slot

    The score is the cadence count divided by the maximum observed count
    across all keys, normalized to [0, 1]. A key with no cadences scores
    zero; the key with the most cadences scores 1.0. Because Ionian and
    Aeolian of the same tonic always increment together, they always
    appear with equal score in the ranked output — the synthesizer +
    bass_dominance + K-S sort out which mode is actually right.
    """

    name: str = "cadential"

    def detect(self, ctx: KeyDetectionContext) -> KeyDetectionVerdict:
        """Score each of 24 keys by cadential evidence.

        Args:
            ctx: KeyDetectionContext. Consults ``chord_events`` only.

        Returns:
            KeyDetectionVerdict. Empty ranked list when chord_events is
            absent or empty.
        """
        events = ctx.chord_events
        if not events or len(events) < 2:
            # Need at least a transition. One chord can't cadence.
            return KeyDetectionVerdict(
                name=self.name,
                ranked=[],
                meta={"reason": "insufficient_chord_events"},
            )

        # Pre-extract (root_pc, is_minor) pairs for every event we can
        # parse. Unparseable labels become None and don't contribute to
        # any cadence pair.
        parsed: List[Optional[Tuple[int, bool]]] = []
        for ev in events:
            label = getattr(ev, "chord_label", None)
            if not label:
                parsed.append(None)
                continue
            pc = _root_pitch_class(label)
            if pc is None:
                parsed.append(None)
                continue
            parsed.append((pc, _is_minor_label(label)))

        # Score per (tonic_pc, mode) candidate. Stored in a 24-element
        # array indexed (tonic_pc * 2 + minor_flag).
        cadence_counts: List[int] = [0] * 24

        for i in range(len(parsed) - 1):
            a = parsed[i]
            b = parsed[i + 1]
            if a is None or b is None:
                continue

            a_pc, a_minor = a
            b_pc, _b_minor = b  # b's quality intentionally ignored — see below

            # Walk all 12 tonic candidates; credit when a is a fifth
            # above b (the V→I dominant relationship). The credit
            # depends on whether a is major or minor:
            #
            # - **Major V → I/i** (e.g., F#→Bm or F#→B): canonical
            #   tonal cadence. Credit BOTH Ionian and Aeolian of the
            #   tonic equally — a single major-V cadence doesn't
            #   distinguish parallel modes (B major vs B minor with
            #   raised leading tone), so let the rest of the ensemble
            #   vote on mode.
            #
            # - **Minor v → i** (e.g., F#m→Bm): the natural-minor /
            #   Aeolian cadence. Credit ONLY Aeolian of the tonic. A
            #   minor v specifically rules out the major-mode reading
            #   (Ionian's V is always major), so it's a strong Aeolian
            #   signal. Without this case, modal songs that don't
            #   raise the leading tone (most rock, folk, and a lot of
            #   contemporary pop) get no cadential credit and lose
            #   their tonic to whichever relative-major sibling
            #   happens to share chord transitions.
            for tonic_pc in range(12):
                expected_dominant_pc = (tonic_pc + 7) % 12
                if a_pc != expected_dominant_pc or b_pc != tonic_pc:
                    continue

                if a_minor:
                    # Minor v → i: Aeolian-only credit.
                    cadence_counts[tonic_pc * 2 + 1] += 1
                else:
                    # Major V → I/i: dual credit, modes argued out
                    # downstream.
                    cadence_counts[tonic_pc * 2] += 1  # Ionian slot
                    cadence_counts[tonic_pc * 2 + 1] += 1  # Aeolian slot

        max_count = max(cadence_counts)
        if max_count == 0:
            # No cadences detected — return empty ranked list. Cadential
            # has nothing to say about non-cadential progressions.
            return KeyDetectionVerdict(
                name=self.name,
                ranked=[],
                meta={"reason": "no_cadences_detected"},
            )

        ranked: List[Tuple[KeyInfo, float]] = []

        for tonic_pc, tonic_name in enumerate(PITCH_CLASSES):
            for slot_offset, mode_label in enumerate(("Ionian", "Aeolian")):
                count = cadence_counts[tonic_pc * 2 + slot_offset]
                normalized = count / max_count

                key_is_minor = mode_label == "Aeolian"
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
            meta={"max_cadence_count": max_count},
        )
