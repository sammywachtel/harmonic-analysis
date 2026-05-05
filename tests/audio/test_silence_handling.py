"""Tests for silence handling in the chord estimation pipeline.

Covers AC-3 scenarios: silent regions produce no chord events, timestamps
survive silence gaps without being shifted to zero, and quiet-but-present
signals still get detected.

All fixtures are generated at test time -- no binary blobs in the repo.
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest

# Module-level skip -- same pattern as the rest of the audio test suite.
librosa = pytest.importorskip("librosa")
sf_mod = pytest.importorskip("soundfile")

from harmonic_analysis.audio._chord_estimation import (  # noqa: E402
    estimate_chord_progression,
)
from harmonic_analysis.audio._types import KeyInfo  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SR = 22050
_HOP = 512
_FRAMES_PER_SEC = _SR / _HOP


def _a_major_key() -> KeyInfo:
    return KeyInfo(tonic="A", mode="major", key_signature="A major", confidence=0.9)


def _generate_silence_then_chord_chroma(
    silence_sec: float = 2.0,
    chord_sec: float = 3.0,
) -> np.ndarray:
    """Build a (12, T) chroma matrix: silence followed by an A major chord.

    The silence region is true zeros -- no noise floor, no nothing. The
    chord region has clean A major (PCs 9, 1, 4) at high energy. This is
    deliberately unrealistic because we're testing the silence detector,
    not the matcher's noise tolerance.
    """
    silence_frames = int(silence_sec * _FRAMES_PER_SEC)
    chord_frames = int(chord_sec * _FRAMES_PER_SEC)

    silence = np.zeros((12, silence_frames), dtype=np.float64)

    # A major: A=9, C#=1, E=4
    chord = np.full((12, chord_frames), 0.02, dtype=np.float64)
    chord[9, :] = 0.8
    chord[1, :] = 0.8
    chord[4, :] = 0.8

    return np.concatenate([silence, chord], axis=1)


def _generate_soft_chord_chroma(
    duration_sec: float = 3.0,
    amplitude: float = 0.1,
) -> np.ndarray:
    """Build a quiet-but-nonzero A major chroma. Should survive the norm check."""
    frames = int(duration_sec * _FRAMES_PER_SEC)
    chroma = np.full((12, frames), 0.005 * amplitude, dtype=np.float64)
    # A major pitch classes at the scaled amplitude
    chroma[9, :] = amplitude
    chroma[1, :] = amplitude
    chroma[4, :] = amplitude
    return chroma


# ---------------------------------------------------------------------------
# AC-3-a: No chord events during silence
# ---------------------------------------------------------------------------


def test_no_chords_during_silence():
    """AC-3-a: Silent region at the start produces zero chord events before 2.0s.

    The first 3 seconds are dead silence (all zeros). With min_chroma_norm=0.05,
    the estimator should skip those windows entirely. We check for events
    before 2.0s (well inside the silence region, clear of windowing boundary
    effects — a 0.5s window starting at 2.5s can straddle into the chord
    region at 3.0s, but nothing starting before 2.0s should).
    """
    chroma = _generate_silence_then_chord_chroma(silence_sec=3.0, chord_sec=3.0)
    key = _a_major_key()

    events = estimate_chord_progression(
        chroma,
        key,
        sr=_SR,
        hop_length=_HOP,
        window_size_s=0.5,
        hop_size_s=0.25,
        min_chroma_norm=0.05,
    )

    early_events = [e for e in events if e.start_time < 2.0]
    assert len(early_events) == 0, (
        f"Found {len(early_events)} chord event(s) during silence: "
        f"{[(e.start_time, e.chord_label) for e in early_events]}"
    )


# ---------------------------------------------------------------------------
# AC-3-b: First post-silence event has correct timestamp
# ---------------------------------------------------------------------------


def test_first_event_timestamp_after_silence():
    """AC-3-b: The first chord event after silence starts near 3.0s, not 0.0s.

    This catches the classic off-by-origin bug where silence-skipped windows
    cause all subsequent timestamps to collapse back to zero. The parallel
    window_start_times list is what prevents this.
    """
    chroma = _generate_silence_then_chord_chroma(silence_sec=3.0, chord_sec=3.0)
    key = _a_major_key()

    events = estimate_chord_progression(
        chroma,
        key,
        sr=_SR,
        hop_length=_HOP,
        window_size_s=0.5,
        hop_size_s=0.25,
        min_chroma_norm=0.05,
    )

    assert len(events) > 0, "Expected at least one chord event after the silence"

    first = events[0]
    # The exact timestamp depends on windowing, but it should be in the
    # neighborhood of 3.0s -- definitely not 0.0s. We allow some slack
    # because the analysis window has nonzero width and the hop might
    # place the first valid window slightly before or after the boundary.
    # A window starting at 2.5s spans 2.5-3.0s and straddles the boundary,
    # so we allow anything >= 2.0s.
    assert first.start_time >= 2.0, (
        f"First event start_time={first.start_time:.2f}s -- "
        f"expected >= 2.0s (near the 3.0s silence boundary)"
    )
    assert first.start_time < 4.5, (
        f"First event start_time={first.start_time:.2f}s -- "
        f"way too late, something is wrong with the windowing"
    )


# ---------------------------------------------------------------------------
# AC-3-c: Soft-attack signals above the threshold still produce chords
# ---------------------------------------------------------------------------


def test_soft_signal_produces_chords():
    """AC-3-c: A quiet signal (amplitude scaled by 0.1) that's still above
    min_chroma_norm should produce chord events. The silence detector
    should let it through -- it's quiet, not silent.
    """
    chroma = _generate_soft_chord_chroma(duration_sec=3.0, amplitude=0.1)
    key = _a_major_key()

    events = estimate_chord_progression(
        chroma,
        key,
        sr=_SR,
        hop_length=_HOP,
        window_size_s=0.5,
        hop_size_s=0.25,
        min_chroma_norm=0.05,
    )

    assert len(events) > 0, (
        "Soft signal (amplitude=0.1) produced no chord events -- "
        "the silence threshold is too aggressive or the soft fixture "
        "is below the norm cutoff"
    )


# ---------------------------------------------------------------------------
# AC-3-d: min_chroma_norm parameter exists in estimate_chord_progression
# ---------------------------------------------------------------------------


def test_min_chroma_norm_in_signature():
    """AC-3-d: The min_chroma_norm parameter must be present. Contract test
    to catch accidental removal during future refactors.
    """
    sig = inspect.signature(estimate_chord_progression)
    assert (
        "min_chroma_norm" in sig.parameters
    ), "'min_chroma_norm' parameter missing from estimate_chord_progression"
