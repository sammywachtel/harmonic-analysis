"""End-to-end integration test: audio → chords → pattern analysis.

AC5: Verifies that the full pipeline chains correctly:
    analyze_audio_async → chords_as_symbols → analyze_with_patterns_async

This is the integration seam test — it proves that ChordEvent objects
produced by the chord estimation layer are compatible with the pattern
analysis service's chord_symbols input. The synthetic WAV is deliberately
simple (sustained C major triad) so that any failure is a wiring bug, not
a signal-processing accuracy problem.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

# Skip the whole module if audio deps aren't installed.
librosa = pytest.importorskip("librosa")
sf = pytest.importorskip("soundfile")


def _generate_c_major_wav(
    path: Path, duration_sec: float = 5.0, sr: int = 22050
) -> Path:
    """Write a C-major triad (C4 + E4 + G4) to a WAV file.

    Three sinusoids at equal amplitude — enough harmonic content for
    librosa's chroma_cqt to pick up the triad clearly. Not a masterpiece,
    but it gets the job done.
    """
    t = np.linspace(0.0, duration_sec, int(sr * duration_sec), endpoint=False)

    # C4=261.63 Hz, E4=329.63 Hz, G4=392.00 Hz
    c4 = np.sin(2 * np.pi * 261.63 * t)
    e4 = np.sin(2 * np.pi * 329.63 * t)
    g4 = np.sin(2 * np.pi * 392.00 * t)
    signal = ((c4 + e4 + g4) / 3.0 * 0.5).astype(np.float32)

    sf.write(str(path), signal, sr)
    return path


@pytest.mark.asyncio
async def test_audio_to_pattern_engine_chain(tmp_path: Path):
    """AC5: Chain analyze_audio_async → chords_as_symbols → analyze_with_patterns_async."""
    from harmonic_analysis.integrations.audio_adapter import analyze_audio_async
    from harmonic_analysis.services.pattern_analysis_service import (
        PatternAnalysisService,
    )

    wav_path = _generate_c_major_wav(tmp_path / "c_major_5s.wav")

    result = await analyze_audio_async(wav_path, quiet=True)

    # Verify chords were populated
    assert len(result.chords) > 0, "Expected at least one ChordEvent from the pipeline"

    chord_symbols = result.chords_as_symbols()
    assert len(chord_symbols) > 0, "chords_as_symbols() should return non-empty list"
    assert all(
        isinstance(s, str) for s in chord_symbols
    ), "All symbols should be strings"

    # Feed into pattern analysis service — this is the real integration test.
    # If the chord labels aren't in a format the service understands, this
    # will raise or return garbage.
    service = PatternAnalysisService()
    envelope = await service.analyze_with_patterns_async(
        chord_symbols=chord_symbols,
        key_hint=result.key_hint,
    )
    assert envelope is not None, "Pattern analysis should return an envelope"
    assert envelope.primary is not None, "Envelope should have a primary interpretation"


@pytest.mark.asyncio
async def test_include_chords_false_skips_estimation(tmp_path: Path):
    """Verify include_chords=False produces empty chord list."""
    from harmonic_analysis.integrations.audio_adapter import analyze_audio_async

    wav_path = _generate_c_major_wav(tmp_path / "c_major_5s.wav")

    result = await analyze_audio_async(wav_path, quiet=True, include_chords=False)
    assert result.chords == [], "include_chords=False should produce empty chords list"
    assert result.chords_as_symbols() == []
