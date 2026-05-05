"""Synthetic WAV fixtures for the audio test suite.

We generate fixtures at test time rather than checking in binary blobs —
keeps the repo lean and lets us tune content (frequencies, durations,
harmonic stack) when AC thresholds shift. The two fixtures below cover
the two integration-test scenarios called out in the iteration plan:

* ``synthetic_a_major_wav`` — 5 seconds of A-major (A4 + C#5 + E5 partial
  stack). Long enough to exceed ``MIN_SAMPLES_FOR_CQT`` comfortably and
  short enough that the in-memory local path runs (no streaming). The
  3-partial stack is deliberate: a pure 440 Hz sine has chroma energy
  concentrated in pitch class A, and Krumhansl-Schmuckler can lock onto
  A minor (Aeolian) about as easily as A major (Ionian) when the third
  is missing. Adding C#5 (the major third) and E5 (the fifth) tilts the
  K-S correlation cleanly toward Ionian and is what gets the AC5 floor
  ``confidence > 0.7`` reliably.
* ``synthetic_3min_wav`` — 180 seconds of low-frequency tonal content.
  Used by the AC6 segment-windowing test; we only care that segment
  bounds round-trip correctly, not that K-S agrees with itself, so the
  signal is intentionally bland.

Both fixtures pull ``librosa`` / ``soundfile`` lazily — if the deps
aren't installed, the fixture is skipped via ``pytest.importorskip`` so
the test collection step still works in a stripped-down dev env.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest


def _generate_a_major_wav(
    path: Path, duration_sec: float = 5.0, sr: int = 22050
) -> Path:
    """Write an A-major sinusoidal stack to ``path`` and return ``path``."""
    sf = pytest.importorskip("soundfile")

    t = np.linspace(0.0, duration_sec, int(sr * duration_sec), endpoint=False)

    # 3-partial stack: tonic A4 (440 Hz), major third C#5 (~554 Hz),
    # perfect fifth E5 (~659 Hz). Equal weights — we don't need pristine
    # voice leading, just enough overtone content to bias K-S toward
    # Ionian over Aeolian. Magic constants from concert tuning.
    a4 = np.sin(2 * np.pi * 440.0 * t)
    cs5 = np.sin(2 * np.pi * 554.37 * t)
    e5 = np.sin(2 * np.pi * 659.25 * t)
    signal = (a4 + cs5 + e5) / 3.0  # mean to avoid clipping when scaled

    # Modest amplitude — leaves headroom for soundfile's PCM_16 encoding.
    signal = (signal * 0.5).astype(np.float32)
    sf.write(str(path), signal, sr)
    return path


def _generate_long_wav(
    path: Path, duration_sec: float = 180.0, sr: int = 22050
) -> Path:
    """Write a long bland tonal signal to ``path``. Not for K-S accuracy."""
    sf = pytest.importorskip("soundfile")

    t = np.linspace(0.0, duration_sec, int(sr * duration_sec), endpoint=False)
    # Single tone — keeps the file small enough to generate in CI without
    # eating disk and avoids any K-S surprises (we don't assert on key
    # for this fixture).
    signal = (0.3 * np.sin(2 * np.pi * 261.63 * t)).astype(np.float32)  # C4
    sf.write(str(path), signal, sr)
    return path


@pytest.fixture
def synthetic_a_major_wav(tmp_path: Path) -> Path:
    """Path to a 5s A-major WAV with C#5 + E5 partials.

    Used for AC5: ``await analyze_audio_async(fixture)`` should recover
    ``global_key.tonic == "A"`` with confidence > 0.7. The 3-partial
    harmonic stack is what makes the > 0.7 floor reliable; a pure 440 Hz
    sine drops the K-S confidence into the 0.5–0.6 band and flunks the
    test.
    """
    path = tmp_path / "a_major_5s.wav"
    return _generate_a_major_wav(path)


@pytest.fixture
def synthetic_3min_wav(tmp_path: Path) -> Path:
    """Path to a 180-second bland tonal WAV.

    Used for AC6 segment windowing — we only assert that
    ``segment_start == 30.0`` and ``segment_end == 90.0`` round-trip
    correctly, so the signal content is intentionally trivial (a single
    C4 sine wave).
    """
    path = tmp_path / "long_3min.wav"
    return _generate_long_wav(path)
