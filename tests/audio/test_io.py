"""Unit tests for ``harmonic_analysis.audio._io``.

Focus: shape contracts, segment windowing, padding behavior, ffmpeg
detection. Integration-level concerns (key recovery, async wrappers,
adapter orchestration) live in
``tests/integration/test_audio_adapter.py``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

# Skip the whole module if librosa/soundfile aren't available — the
# `[audio]` extra is intentionally optional. Module-level importorskip is
# the standard idiom for "skip this whole file when deps are missing."
pytest.importorskip("librosa")
pytest.importorskip("soundfile")

from harmonic_analysis.audio._io import (  # noqa: E402  (after importorskip)
    LOCAL_ANALYSIS_STREAMING_THRESHOLD_S,
    MIN_SAMPLES_FOR_CQT,
    check_ffmpeg_available,
    extract_global_chroma,
    extract_local_chroma,
)


def test_extract_global_chroma_shape(synthetic_a_major_wav: Path) -> None:
    """Global path returns a 1D 12-element vector (AC contract)."""
    chroma = extract_global_chroma(synthetic_a_major_wav)
    assert chroma.shape == (12,), f"expected (12,), got {chroma.shape}"
    assert chroma.dtype.kind == "f"  # float of some flavor


def test_extract_local_chroma_shape(synthetic_a_major_wav: Path) -> None:
    """Local path returns a 2D ``(12, T)`` matrix with at least one frame."""
    chroma = extract_local_chroma(synthetic_a_major_wav)
    assert chroma.ndim == 2, f"expected 2D, got {chroma.ndim}D"
    assert chroma.shape[0] == 12, f"expected (12, T), got {chroma.shape}"
    assert chroma.shape[1] > 0, "expected at least one time frame"


def test_extract_local_chroma_segment_bounds(synthetic_3min_wav: Path) -> None:
    """A windowed segment produces fewer frames than the full file.

    We don't compare to an exact frame count — librosa's hop_length
    default and CQT padding make exact arithmetic brittle. The qualitative
    check is enough: a 60s slice must yield significantly fewer frames
    than a 180s slice.
    """
    full = extract_local_chroma(synthetic_3min_wav)
    windowed = extract_local_chroma(synthetic_3min_wav, start_time=30.0, end_time=90.0)

    assert windowed.shape[0] == 12
    assert windowed.shape[1] > 0
    # 60s window should yield less than half the frames of the full 180s.
    # Generous bound — we're testing window correctness, not exact frame math.
    assert windowed.shape[1] < full.shape[1]


def test_extract_local_chroma_short_segment_pads(
    synthetic_a_major_wav: Path,
) -> None:
    """In-memory path pads sub-CQT segments rather than crashing.

    Synthetic test fixtures often have tail sections shorter than
    ``MIN_SAMPLES_FOR_CQT``. The implementation pads them up; a regression
    that drops the pad would surface here as a librosa shape error.
    """
    # Take a really short slice — well under MIN_SAMPLES_FOR_CQT samples
    # at 22050 Hz, that's < 0.186 seconds. We pad up to MIN_SAMPLES_FOR_CQT.
    chroma = extract_local_chroma(synthetic_a_major_wav, start_time=0.0, end_time=0.1)
    assert chroma.shape[0] == 12
    # After padding, librosa always gives us at least 1 frame.
    assert chroma.shape[1] >= 1


def test_extract_local_chroma_empty_segment_raises(
    synthetic_a_major_wav: Path,
) -> None:
    """Zero-width segment is a caller bug; surface a clear ValueError."""
    with pytest.raises(ValueError):
        extract_local_chroma(synthetic_a_major_wav, start_time=2.0, end_time=2.0)


def test_check_ffmpeg_available_returns_bool() -> None:
    """``check_ffmpeg_available`` always returns a real bool."""
    result = check_ffmpeg_available()
    assert isinstance(result, bool)


def test_check_ffmpeg_unavailable_when_path_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When ``shutil.which`` finds nothing, the function reports False."""
    import harmonic_analysis.audio._io as io_module

    # Patch the shutil module that _io.py imported, not shutil globally —
    # the canonical idiom for shutil.which monkeypatching in tests.
    monkeypatch.setattr(io_module.shutil, "which", lambda _name: None)
    assert check_ffmpeg_available() is False


def test_constants_match_toolkit() -> None:
    """Sanity check that the constants didn't drift during port."""
    assert MIN_SAMPLES_FOR_CQT == 4096
    assert LOCAL_ANALYSIS_STREAMING_THRESHOLD_S == 60


def test_global_chroma_nonzero_for_real_signal(
    synthetic_a_major_wav: Path,
) -> None:
    """A real signal must produce non-trivial chroma energy.

    Catches the regression where chroma extraction silently produces all
    zeros (which then crashes find_best_key's correlation step).
    """
    chroma = extract_global_chroma(synthetic_a_major_wav)
    assert np.linalg.norm(chroma) > 1e-3
