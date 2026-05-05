"""Unit tests for the boundary_chords approach.

AC-03 row 2 (Bm boundaries → B Aeolian wins) and row 3 (empty events →
graceful empty verdict). Plus a major-key sanity check (C-major
boundaries → C Ionian wins).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from harmonic_analysis.audio._key_approaches.boundary_chords import (
    BoundaryChordsApproach,
)
from harmonic_analysis.audio._key_ensemble import KeyDetectionContext


@dataclass
class _FakeChordEvent:
    """Minimal chord-event stub. The approach only reads chord_label."""

    chord_label: str
    start_time: float = 0.0
    end_time: float = 1.0
    confidence: float = 0.9
    is_diatonic: bool = True


def _chroma_stub() -> np.ndarray:
    """A 12-vector that's nonzero so contexts don't accidentally trip a
    chroma-related code path. The approach doesn't actually consult it."""
    return np.ones(12, dtype=float) / 12.0


def test_bm_boundaries_score_b_aeolian_top() -> None:
    """First and last chord = Bm → B Aeolian should win."""
    events = [
        _FakeChordEvent("Bm"),
        _FakeChordEvent("D"),
        _FakeChordEvent("A"),
        _FakeChordEvent("G"),
        _FakeChordEvent("Bm"),
    ]
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), chord_events=events)

    verdict = BoundaryChordsApproach().detect(ctx)

    assert verdict.name == "boundary_chords"
    assert len(verdict.ranked) > 0
    top_key, top_score = verdict.ranked[0]
    assert top_key.tonic == "B"
    assert top_key.mode == "Aeolian"
    assert top_score > 0.0


def test_c_major_boundaries_score_c_ionian_top() -> None:
    """V→I bookending in C major: opener and closer both C → C Ionian wins."""
    events = [
        _FakeChordEvent("C"),
        _FakeChordEvent("F"),
        _FakeChordEvent("G"),
        _FakeChordEvent("C"),
    ]
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), chord_events=events)

    verdict = BoundaryChordsApproach().detect(ctx)

    top_key, _ = verdict.ranked[0]
    assert top_key.tonic == "C"
    assert top_key.mode == "Ionian"


def test_empty_chord_events_graceful_empty_verdict() -> None:
    """Empty chord events → empty ranked list; no crash."""
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), chord_events=[])

    verdict = BoundaryChordsApproach().detect(ctx)

    assert verdict.name == "boundary_chords"
    assert verdict.ranked == []
    assert verdict.meta is not None


def test_none_chord_events_graceful_empty_verdict() -> None:
    """chord_events=None (stage 1 of two-stage pipeline) → empty verdict."""
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), chord_events=None)

    verdict = BoundaryChordsApproach().detect(ctx)

    assert verdict.ranked == []


def test_dominant_match_scores_lower_than_tonic_match() -> None:
    """V on the boundary should score lower than I on the boundary."""
    # First and last = G (dominant of C major)
    events_v = [_FakeChordEvent("G"), _FakeChordEvent("C"), _FakeChordEvent("G")]
    # First and last = C (tonic of C major)
    events_i = [_FakeChordEvent("C"), _FakeChordEvent("G"), _FakeChordEvent("C")]

    chroma = _chroma_stub()
    v_verdict = BoundaryChordsApproach().detect(
        KeyDetectionContext(chroma_1d=chroma, chord_events=events_v)
    )
    i_verdict = BoundaryChordsApproach().detect(
        KeyDetectionContext(chroma_1d=chroma, chord_events=events_i)
    )

    # Find C major's score in each
    v_c_score = next(
        s for k, s in v_verdict.ranked if k.tonic == "C" and k.mode == "Ionian"
    )
    i_c_score = next(
        s for k, s in i_verdict.ranked if k.tonic == "C" and k.mode == "Ionian"
    )
    assert i_c_score > v_c_score


def test_returns_24_ranked_entries() -> None:
    """Every key in the 24-key universe gets a row."""
    events = [_FakeChordEvent("Bm"), _FakeChordEvent("Bm")]
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), chord_events=events)

    verdict = BoundaryChordsApproach().detect(ctx)

    assert len(verdict.ranked) == 24


# ---------------------------------------------------------------------------
# iteration_01_a: filtering of garbage edge events. The chord estimator
# emits events for silent lead-in / decay-tail with low confidence and/or
# short duration — those are not real played chords. Without filtering
# the approach would mis-identify the boundaries on real audio.
# ---------------------------------------------------------------------------


def test_filters_low_confidence_and_short_duration_boundary_events() -> None:
    """Mixed sequence: leading low-conf garbage, valid Bm middle, trailing
    short-duration garbage → boundaries should resolve to the valid Bm
    chords, not the garbage. Mirrors the diagnostic-MP3 failure mode where
    a "D conf 0.82" lead-in and "G dur 0.3s" trail were being treated as
    real boundary signal."""
    events = [
        # Leading garbage: silent-lead-in K-S fallback artifact.
        # Fails confidence threshold (0.82 < 0.85). Duration is fine.
        _FakeChordEvent("D", start_time=0.00, end_time=0.75, confidence=0.82),
        # Valid Bm — well-played, clearly above both thresholds.
        _FakeChordEvent("Bm", start_time=1.00, end_time=2.75, confidence=0.94),
        # Interior content (F#) — also qualifies, so to make the test
        # robust about the *trailing-Bm boundary* claim we tuck the
        # interior content between two Bm events. Mirrors the diagnostic
        # MP3 where multiple Bm regions sandwich the V→i material.
        _FakeChordEvent("F#", start_time=2.75, end_time=4.50, confidence=0.91),
        _FakeChordEvent("Bm", start_time=4.50, end_time=6.50, confidence=0.97),
        # Trailing garbage: trailing-decay tail.
        # Confidence is fine (0.85), but duration fails (0.3s < 0.5s).
        _FakeChordEvent("G", start_time=6.50, end_time=6.80, confidence=0.85),
    ]
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), chord_events=events)

    verdict = BoundaryChordsApproach().detect(ctx)

    # Top key should be B-rooted. Both qualifying boundaries are Bm (a
    # minor chord on B) so B Aeolian gets the full quality-match bonus
    # at both ends — should beat B Ionian (wrong-quality match).
    top_key, _ = verdict.ranked[0]
    assert top_key.tonic == "B", (
        f"Expected B (qualifying boundaries are both Bm), "
        f"got {top_key.tonic} {top_key.mode}"
    )
    assert top_key.mode == "Aeolian", (
        "Both Bm boundaries match Aeolian's minor tonic chord quality, "
        f"so Aeolian should outrank Ionian; got mode={top_key.mode}"
    )

    # Sanity: the meta should reflect the qualifying boundaries (Bm),
    # not the raw garbage events (D / G). If meta still says D/G, the
    # diagnostic panel would invisibly hide the bug we just fixed.
    assert verdict.meta is not None
    assert verdict.meta["first_chord"] == "Bm"
    assert verdict.meta["last_chord"] == "Bm"


def test_filters_garbage_with_explicit_thresholds() -> None:
    """Same garbage-vs-valid pattern but with explicit threshold args.
    Proves the parameters are honored (not silently hardcoded)."""
    events = [
        # At default confidence threshold 0.85, this would be filtered;
        # with min_confidence=0.80, it qualifies. We use this to verify
        # the parameter wires through.
        _FakeChordEvent("C", start_time=0.0, end_time=1.0, confidence=0.82),
        _FakeChordEvent("G", start_time=1.0, end_time=2.0, confidence=0.93),
        _FakeChordEvent("C", start_time=2.0, end_time=3.0, confidence=0.82),
    ]
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), chord_events=events)

    # Loose thresholds: all events qualify, both ends are C → C Ionian wins.
    loose_verdict = BoundaryChordsApproach(
        min_confidence=0.80, min_duration_s=0.5
    ).detect(ctx)
    top_key, _ = loose_verdict.ranked[0]
    assert top_key.tonic == "C"
    assert top_key.mode == "Ionian"

    # Default thresholds: only the middle G qualifies, both boundaries
    # collapse to G → G keys win.
    strict_verdict = BoundaryChordsApproach().detect(ctx)
    top_key, _ = strict_verdict.ranked[0]
    assert (
        top_key.tonic == "G"
    ), f"With strict thresholds only G qualifies; got {top_key.tonic}"


def test_all_garbage_events_returns_empty_verdict() -> None:
    """Every event fails at least one threshold → empty ranked list with
    a populated reason. No exception. Negative case mandated by the spec."""
    events = [
        # Fails confidence (0.82 < 0.85).
        _FakeChordEvent("D", start_time=0.0, end_time=0.75, confidence=0.82),
        # Fails confidence AND duration.
        _FakeChordEvent("C#", start_time=0.75, end_time=1.15, confidence=0.15),
        # Fails duration (0.3s < 0.5s).
        _FakeChordEvent("G", start_time=1.15, end_time=1.45, confidence=0.90),
    ]
    ctx = KeyDetectionContext(chroma_1d=_chroma_stub(), chord_events=events)

    verdict = BoundaryChordsApproach().detect(ctx)

    assert verdict.ranked == []
    assert verdict.meta is not None
    # Reason must be a non-empty string so callers can distinguish "no
    # qualifying events" from "no events at all" / "no chroma" / etc.
    assert verdict.meta.get("reason") == "no_qualifying_events"
