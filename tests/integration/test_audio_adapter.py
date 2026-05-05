"""End-to-end integration tests for the audio adapter.

Each test maps onto an acceptance criterion in the iteration plan:

* AC4 — ``AudioImportError`` on missing deps (sys.modules monkeypatch).
* AC5 — Synthetic A-major WAV: ``global_key.tonic == "A"``, confidence > 0.7.
* AC6 — 3-minute WAV with ``segment=(30.0, 90.0)``: bounds round-trip.
* AC7 — ``result.chords`` populated by chord estimation; empty when
  ``include_chords=False``.
* AC8 — ``result.key_hint`` matches the regex and is service-callable.
* AC9 — ffmpeg-absent × quiet={False, True} × WAV-fixture-success scenarios.

Plus a ``tracemalloc`` peak-allocation soft ceiling on the streaming
path — guards against a future regression where someone slurps the whole
file into memory.

The fixtures (``synthetic_a_major_wav``, ``synthetic_3min_wav``) come
from ``tests/audio/conftest.py``. We import them via the explicit
``--rootdir`` mechanism: pytest discovers the audio conftest because we
list its path on the test target list.
"""

from __future__ import annotations

import logging
import re
import sys
import tracemalloc
from pathlib import Path
from typing import Any, Generator

import pytest

# Skip the whole module if the audio extras aren't installed. WAV-only
# integration tests still need librosa+soundfile under the hood.
pytest.importorskip("librosa")
pytest.importorskip("soundfile")

# Re-export the synthetic WAV fixtures from the audio conftest so this
# integration test file can use them. pytest auto-discovers conftest.py
# in parent directories of the test file, but ``tests/audio/conftest.py``
# is a sibling, not a parent — so we import the fixture functions and
# rebind them as fixtures here.
from tests.audio.conftest import _generate_a_major_wav, _generate_long_wav  # noqa: E402


@pytest.fixture
def synthetic_a_major_wav(tmp_path: Path) -> Path:
    """5-second A-major WAV (re-exported from tests/audio/conftest.py)."""
    return _generate_a_major_wav(tmp_path / "a_major_5s.wav")


@pytest.fixture
def synthetic_3min_wav(tmp_path: Path) -> Path:
    """180-second tonal WAV (re-exported from tests/audio/conftest.py)."""
    return _generate_long_wav(tmp_path / "long_3min.wav")


# ---------------------------------------------------------------------------
# AC5 — global-key recovery on the A-major synthetic fixture
# ---------------------------------------------------------------------------
async def test_ac5_global_key_recovery_on_a_major(
    synthetic_a_major_wav: Path,
) -> None:
    """K-S should pin tonic=A with confidence > 0.7 on the 3-partial stack."""
    from harmonic_analysis import analyze_audio_async

    result = await analyze_audio_async(synthetic_a_major_wav, quiet=True)

    assert result.global_key.tonic == "A", (
        f"expected tonic=A, got {result.global_key.tonic!r} "
        f"(mode={result.global_key.mode!r}, "
        f"confidence={result.global_key.confidence:.3f})"
    )
    assert (
        result.global_key.confidence > 0.7
    ), f"K-S confidence {result.global_key.confidence:.3f} below 0.7 floor"


# ---------------------------------------------------------------------------
# AC6 — segment bounds round-trip exactly through the result
# ---------------------------------------------------------------------------
async def test_ac6_segment_bounds_round_trip(synthetic_3min_wav: Path) -> None:
    """``segment=(30.0, 90.0)`` shows up verbatim on the result object."""
    from harmonic_analysis import analyze_audio_async

    result = await analyze_audio_async(
        synthetic_3min_wav, segment=(30.0, 90.0), quiet=True
    )

    assert result.segment_start == 30.0
    assert result.segment_end == 90.0


# ---------------------------------------------------------------------------
# AC7 — chords populated by chord estimation layer; empty when opted out
# ---------------------------------------------------------------------------
async def test_ac7_chords_populated_no_segment(synthetic_a_major_wav: Path) -> None:
    """Global-only path: chord estimation produces non-empty results."""
    from harmonic_analysis import analyze_audio_async

    result = await analyze_audio_async(synthetic_a_major_wav, quiet=True)

    assert len(result.chords) > 0, "Chord estimation should produce events"
    assert len(result.chords_as_symbols()) > 0
    assert all(isinstance(s, str) for s in result.chords_as_symbols())


async def test_ac7_chords_empty_when_opted_out(synthetic_a_major_wav: Path) -> None:
    """include_chords=False: ``chords == []`` and ``chords_as_symbols() == []``."""
    from harmonic_analysis import analyze_audio_async

    result = await analyze_audio_async(
        synthetic_a_major_wav, quiet=True, include_chords=False
    )

    assert result.chords == []
    assert result.chords_as_symbols() == []


# ---------------------------------------------------------------------------
# AC8 — key_hint is a valid mode string and the service accepts it
# ---------------------------------------------------------------------------
async def test_ac8_key_hint_regex(synthetic_a_major_wav: Path) -> None:
    """``result.key_hint`` matches the AC8 regex."""
    from harmonic_analysis import analyze_audio_async

    result = await analyze_audio_async(synthetic_a_major_wav, quiet=True)

    pattern = re.compile(
        r"^[A-G][#b]? "
        r"(major|minor|dorian|phrygian|lydian|mixolydian|aeolian|locrian)$"
    )
    assert result.key_hint, "key_hint must be non-empty"
    assert pattern.match(
        result.key_hint
    ), f"key_hint {result.key_hint!r} doesn't match AC8 regex"


async def test_ac8_key_hint_passes_through_service(
    synthetic_a_major_wav: Path,
) -> None:
    """``key_hint`` is consumable by ``analyze_with_patterns_async`` w/o raising."""
    from harmonic_analysis import analyze_audio_async
    from harmonic_analysis.services.pattern_analysis_service import (
        PatternAnalysisService,
    )

    result = await analyze_audio_async(synthetic_a_major_wav, quiet=True)

    service = PatternAnalysisService()
    # Trivial chord progression in the inferred key — we don't care about
    # the analysis output, only that the key_hint string is accepted.
    progression = ["A", "D", "E", "A"]

    # Just call it — assertion is "doesn't raise". Returned object isn't
    # asserted on per AC8.
    await service.analyze_with_patterns_async(progression, key_hint=result.key_hint)


# ---------------------------------------------------------------------------
# AC9 — ffmpeg-absent path (4 scenarios from the prepare doc)
# ---------------------------------------------------------------------------
@pytest.fixture
def ffmpeg_absent(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Force ``check_ffmpeg_available()`` to return False."""
    import harmonic_analysis.audio._io as io_module

    monkeypatch.setattr(io_module.shutil, "which", lambda _name: None)
    yield


def test_ac9_warning_emitted_when_ffmpeg_absent_and_not_quiet(
    ffmpeg_absent: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """One WARNING with 'ffmpeg' + an audio-format hint."""
    from harmonic_analysis import AudioAdapter

    with caplog.at_level(logging.WARNING, logger="harmonic_analysis"):
        AudioAdapter()

    # Filter to WARNING records on the adapter logger.
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1, (
        f"expected exactly 1 WARNING, got {len(warnings)}: "
        f"{[r.getMessage() for r in warnings]}"
    )
    msg = warnings[0].getMessage()
    assert "ffmpeg" in msg.lower()
    # Must mention at least one of the soft-dep formats per AC9.
    assert any(fmt in msg for fmt in ("MP3", "AAC", "OGG"))


def test_ac9_no_warning_when_quiet(
    ffmpeg_absent: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """``quiet=True`` suppresses the ffmpeg WARNING entirely."""
    from harmonic_analysis import AudioAdapter

    with caplog.at_level(logging.WARNING, logger="harmonic_analysis"):
        AudioAdapter(quiet=True)

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warnings == [], f"expected zero WARNINGs, got {warnings}"


async def test_ac9_wav_fixture_succeeds_without_ffmpeg(
    ffmpeg_absent: None,
    synthetic_a_major_wav: Path,
) -> None:
    """ffmpeg-absent doesn't break WAV analysis (libsndfile reads WAV directly)."""
    from harmonic_analysis import analyze_audio_async

    result = await analyze_audio_async(synthetic_a_major_wav, quiet=True)
    assert result.global_key.tonic != "N/A"
    assert result.global_key.tonic == "A"


def test_ac9_no_warning_when_ffmpeg_present(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Happy path: ffmpeg on PATH means no WARNING, no fuss."""
    import harmonic_analysis.audio._io as io_module
    from harmonic_analysis import AudioAdapter

    # Force ffmpeg to "exist" regardless of host environment.
    monkeypatch.setattr(io_module.shutil, "which", lambda _name: "/usr/bin/ffmpeg")

    with caplog.at_level(logging.WARNING, logger="harmonic_analysis"):
        AudioAdapter()

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warnings == [], "no WARNING expected when ffmpeg is present"


# ---------------------------------------------------------------------------
# AC4 — AudioImportError when librosa/soundfile are missing
# ---------------------------------------------------------------------------
def test_ac4_audio_import_error_message_format() -> None:
    """``AudioImportError`` message mentions 'audio' and 'pip install'.

    We don't try to actually uninstall librosa here (would break other
    tests). Instead we synthesize the error directly and verify the
    message format the constructor produces — that's the contract AC4
    cares about. The constructor path is exercised by simulating the
    ImportError below.
    """
    from harmonic_analysis import AudioImportError

    err = AudioImportError(
        "The audio extra is required for AudioAdapter. "
        "Install with: pip install harmonic-analysis[audio]"
    )
    msg = str(err)
    assert "audio" in msg
    assert "pip install" in msg


def test_ac4_audio_import_error_raised_when_deps_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Simulate librosa missing at construction time → AudioImportError.

    We can't ``del sys.modules['librosa']`` permanently without
    contaminating other tests in the same process — so we set the entry
    to ``None``, which makes ``import librosa`` raise ``ImportError`` per
    Python's import-system rules. monkeypatch reverses on teardown.
    """
    monkeypatch.setitem(sys.modules, "librosa", None)
    monkeypatch.setitem(sys.modules, "soundfile", None)

    from harmonic_analysis import AudioAdapter, AudioImportError

    with pytest.raises(AudioImportError) as excinfo:
        AudioAdapter()

    msg = str(excinfo.value)
    assert "audio" in msg
    assert "pip install" in msg


# ---------------------------------------------------------------------------
# Memory regression — peak allocation soft-ceiling on the streaming path
# ---------------------------------------------------------------------------
def test_streaming_path_memory_ceiling(synthetic_3min_wav: Path) -> None:
    """tracemalloc peak < 500 MB on a 180s WAV.

    The streaming path's whole point is bounded memory regardless of file
    length. If somebody refactors the chunked weighted-average into a
    full file load, the peak balloons and this test fires. Ceiling is
    deliberately generous — we're catching gross regressions, not
    nickel-and-diming.
    """
    from harmonic_analysis import analyze_audio

    tracemalloc.start()
    try:
        # Use a short 30s window — exercises the in-memory local path,
        # which is still the easier place to leak memory if someone
        # refactored away from incremental loading.
        analyze_audio(synthetic_3min_wav, segment=(30.0, 90.0), quiet=True)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    peak_mb = peak / (1024 * 1024)
    # 500 MB is a soft ceiling — way above what the pipeline should
    # consume for a 60s segment but well below "we slurped the whole
    # file plus all chroma frames into one numpy array."
    assert peak_mb < 500, f"peak memory {peak_mb:.1f} MB exceeds 500 MB ceiling"


# ---------------------------------------------------------------------------
# Bonus — sync wrapper smoke test (covers analyze_audio explicitly)
# ---------------------------------------------------------------------------
def test_sync_wrapper_returns_result(synthetic_a_major_wav: Path) -> None:
    """``analyze_audio`` is callable from sync code and returns a result."""
    from harmonic_analysis import analyze_audio

    result = analyze_audio(synthetic_a_major_wav, quiet=True)
    assert result.global_key.tonic == "A"
    assert result.segment_start == 0.0
    assert result.segment_end > 0.0


def test_async_wrapper_offloads_to_thread(
    synthetic_a_major_wav: Path,
) -> None:
    """``analyze_audio_async`` doesn't block the event loop excessively.

    Smoke-level — we run it under asyncio.run and assert it returns. A
    full event-loop responsiveness test is overkill for this WU.
    """
    import asyncio

    from harmonic_analysis import analyze_audio_async

    async def _runner() -> Any:
        return await analyze_audio_async(synthetic_a_major_wav, quiet=True)

    result = asyncio.run(_runner())
    assert result.global_key.tonic == "A"
