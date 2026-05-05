"""Tests for the rubato preset system and its integration with the audio adapter.

Covers AC-2 scenarios: named presets resolve correctly, float interpolation
does the right thing (including the nearest-odd kernel trick), invalid
presets blow up with a clear error, and the rubato parameter actually shows
up in the signatures that matter.

Generated-at-test-time fixtures only -- no WAV blobs checked in.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

# Module-level skip -- audio deps are optional and we need them even for
# the pure-Python _resolve_rubato tests because the import chain pulls
# in librosa transitively.
librosa = pytest.importorskip("librosa")
sf = pytest.importorskip("soundfile")

from harmonic_analysis.integrations.audio_adapter import (  # noqa: E402
    AudioAdapter,
    _resolve_rubato,
    analyze_audio,
    analyze_audio_async,
)

# ---------------------------------------------------------------------------
# AC-2-a through AC-2-d: Named presets resolve to the documented triples
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "preset,expected",
    [
        ("strict", (0.25, 0.1, 3)),
        ("moderate", (0.5, 0.25, 3)),
        ("loose", (0.75, 0.4, 5)),
        ("free", (1.0, 0.5, 7)),
    ],
    ids=["AC-2-a_strict", "AC-2-b_moderate", "AC-2-c_loose", "AC-2-d_free"],
)
def test_named_preset(preset: str, expected: tuple) -> None:
    """Each named rubato preset maps to exactly one (window, hop, kernel) triple."""
    result = _resolve_rubato(preset)
    assert result == expected, f"{preset!r} resolved to {result}, expected {expected}"


# ---------------------------------------------------------------------------
# AC-2-e through AC-2-g: Float interpolation
# ---------------------------------------------------------------------------


def test_float_zero_returns_strict():
    """AC-2-e: 0.0 is the strict end of the interpolation range."""
    assert _resolve_rubato(0.0) == (0.25, 0.1, 3)


def test_float_one_returns_free():
    """AC-2-f: 1.0 is the free end of the interpolation range."""
    assert _resolve_rubato(1.0) == (1.0, 0.5, 7)


def test_float_midpoint_kernel_is_odd():
    """AC-2-g: 0.5 interpolates to the midpoint, kernel rounded to nearest odd.

    Midpoint: window=0.625, hop=0.3, raw_kernel=5.0 -> 5 (already odd).
    """
    window, hop, kernel = _resolve_rubato(0.5)
    assert window == pytest.approx(0.625, abs=1e-6)
    assert hop == pytest.approx(0.3, abs=1e-6)
    assert kernel == 5
    # Sanity: kernel must always be odd
    assert kernel % 2 == 1, "Kernel must be odd"


# ---------------------------------------------------------------------------
# AC-2-h: Invalid preset raises ValueError
# ---------------------------------------------------------------------------


def test_invalid_preset_raises():
    """AC-2-h: An unrecognized string blows up with a helpful message."""
    with pytest.raises(ValueError, match="Unknown rubato preset"):
        _resolve_rubato("bebop")


# ---------------------------------------------------------------------------
# AC-2-i: Regression -- rubato="moderate" produces identical results to
# explicit chord_window_size_s=0.5, chord_hop_size_s=0.25
# ---------------------------------------------------------------------------


def test_rubato_moderate_matches_explicit_defaults(
    synthetic_a_major_wav: Path,
) -> None:
    """AC-2-i: rubato='moderate' must produce the same chord events as the
    old explicit defaults. If this breaks, someone changed the moderate
    preset without updating the regression expectation -- go fix the
    preset or update this test, but don't just delete it.
    """
    # Run with rubato preset
    result_rubato = analyze_audio(
        synthetic_a_major_wav,
        quiet=True,
        rubato="moderate",
    )

    # Run with the explicit values that "moderate" should resolve to
    result_explicit = analyze_audio(
        synthetic_a_major_wav,
        quiet=True,
        chord_window_size_s=0.5,
        chord_hop_size_s=0.25,
    )

    # Chord event lists should be identical
    assert len(result_rubato.chords) == len(result_explicit.chords), (
        f"Chord count mismatch: rubato={len(result_rubato.chords)}, "
        f"explicit={len(result_explicit.chords)}"
    )

    for i, (cr, ce) in enumerate(zip(result_rubato.chords, result_explicit.chords)):
        assert cr.chord_label == ce.chord_label, (
            f"Chord {i}: rubato label={cr.chord_label!r}, "
            f"explicit label={ce.chord_label!r}"
        )
        assert cr.start_time == pytest.approx(ce.start_time, abs=1e-6)
        assert cr.end_time == pytest.approx(ce.end_time, abs=1e-6)
        assert cr.confidence == pytest.approx(ce.confidence, abs=1e-6)


# ---------------------------------------------------------------------------
# AC-2-j: rubato param exists in the right signatures
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "target",
    [AudioAdapter.__init__, analyze_audio, analyze_audio_async],
    ids=["AudioAdapter.__init__", "analyze_audio", "analyze_audio_async"],
)
def test_rubato_param_in_signature(target) -> None:
    """AC-2-j: The rubato parameter must be present in all three entry points.

    This is a signature-level contract test -- catches accidental removal
    during refactors before the integration tests get a chance to complain.
    """
    sig = inspect.signature(target)
    assert (
        "rubato" in sig.parameters
    ), f"'rubato' parameter missing from {target.__qualname__} signature"
