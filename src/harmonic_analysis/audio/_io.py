"""Streaming chroma extraction from audio files.

This module owns the I/O surface of the audio pipeline. Everything in here is
a pure module-level function — no class state, no globals to mutate, just
``filepath in, np.ndarray out``. The adapter layer (``audio_adapter.py``) is
the only consumer, and it imports this module lazily (after confirming
librosa + soundfile are installed) so a bare ``import harmonic_analysis``
never pulls in the audio stack.

Streaming model
---------------
Big files are the enemy of memory. We read audio in 5-second blocks via
``soundfile.SoundFile.blocks``, run librosa's CQT chroma on each block, and
either accumulate a weighted average (global path → 1D ``(12,)``) or
concatenate frame-wise (local path → 2D ``(12, T)``). The
``LOCAL_ANALYSIS_STREAMING_THRESHOLD_S`` constant gates when the local path
switches from "read the whole segment in one go" to "stream it." 60 seconds
is the toolkit's empirical sweet spot — short segments fit comfortably in
RAM and the streaming overhead isn't worth it; long segments would blow up
the heap on a 1080p workstation, never mind a CI runner.

Padding
-------
``MIN_SAMPLES_FOR_CQT = 4096`` is librosa's default ``n_fft`` for chroma_cqt.
A chunk shorter than this raises a librosa error if you don't pad it. Final
chunks of streamed audio routinely come in short, so we zero-pad them up
before calling chroma_cqt. This is the "pretty-but-broken" alternative
versus dropping the tail; the toolkit pads, we pad.

Shape contract
--------------
* ``extract_global_chroma`` → ``np.ndarray`` shape ``(12,)``. Already
  averaged across time; pass directly to ``find_best_key``.
* ``extract_local_chroma`` → ``np.ndarray`` shape ``(12, T)``. Pre-reduce
  with ``.mean(axis=1)`` before ``find_best_key``; pass raw to
  ``detect_cadences`` (it does its own averaging).

This mismatch is deliberate — preserving the time axis lets WU3 do
frame-level chord detection without re-reading the audio.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Optional, Union

import librosa
import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)

# librosa's default n_fft for chroma_cqt. Chunks shorter than this need
# padding or chroma_cqt errors out. Magic constant lifted verbatim from the
# toolkit.
MIN_SAMPLES_FOR_CQT = 4096

# Local-segment chunking threshold. Segments longer than this stream their
# chroma in 5s blocks; shorter segments read in one shot. Tuned empirically
# by the toolkit — short paths win on speed, long paths win on memory.
LOCAL_ANALYSIS_STREAMING_THRESHOLD_S = 60

# Internal block size — 5 seconds per chunk. Constant in the toolkit's
# implementation; if you change it, also retest the AC5 confidence floor.
_CHUNK_SIZE_SECONDS = 5

# Type alias for filepath args — accept str or Path interchangeably.
PathLike = Union[str, Path]


def check_ffmpeg_available() -> bool:
    """Return True iff ``ffmpeg`` is on PATH.

    librosa needs ffmpeg under the hood to decode MP3/AAC/OGG. WAV works
    without it (soundfile/libsndfile handles WAV directly). The adapter
    uses this to emit a single WARNING at construction time when a user
    is likely to hit the "decode failed" cliff later.

    Returns:
        ``True`` if ``shutil.which("ffmpeg")`` finds the binary, else
        ``False``. No exceptions; missing PATH is "not available."
    """
    return shutil.which("ffmpeg") is not None


def extract_global_chroma(filepath: PathLike) -> np.ndarray:
    """Stream the whole file through chroma_cqt and return a 12-bin vector.

    Memory footprint is bounded by the 5-second block size, regardless of
    file length. Each block contributes a weighted sum to the running
    chroma total, and the final divide produces the time-averaged
    pitch-class energy distribution.

    Args:
        filepath: Path to an audio file readable by ``soundfile.SoundFile``
            (WAV directly; MP3/AAC/OGG via ffmpeg).

    Returns:
        ``np.ndarray`` shape ``(12,)``, dtype float. Each element is the
        average energy in one of the 12 pitch classes (C, C#, ..., B)
        across the entire file. Pass directly to ``find_best_key``.

    Raises:
        ValueError: If the file is too short to produce any chroma frames
            (less than ``MIN_SAMPLES_FOR_CQT`` samples total, after padding
            tries).
        RuntimeError: Surfaced from soundfile/librosa for unreadable files.
    """
    weighted_chroma_sum = np.zeros(12, dtype=np.float32)
    total_frames = 0

    with sf.SoundFile(str(filepath), "r") as f:
        sr = f.samplerate
        chunk_size = sr * _CHUNK_SIZE_SECONDS

        for block in f.blocks(blocksize=chunk_size, dtype="float32", always_2d=True):
            # Mono-mix the block. Multi-channel input averages down here so
            # downstream librosa always sees a 1D y array.
            y_chunk = np.mean(block.T, axis=0)
            chunk_len = len(y_chunk)

            if chunk_len == 0:
                continue

            if chunk_len < MIN_SAMPLES_FOR_CQT:
                # Final tail-end chunk — pad up rather than drop, otherwise
                # we silently lose audio that might contain the cadence.
                logger.warning(
                    "Padding final global chunk of length %d to %d samples "
                    "to meet chroma_cqt requirements.",
                    chunk_len,
                    MIN_SAMPLES_FOR_CQT,
                )
                pad_width = MIN_SAMPLES_FOR_CQT - chunk_len
                y_chunk = np.pad(y_chunk, (0, pad_width), "constant")

            chunk_chroma = librosa.feature.chroma_cqt(y=y_chunk, sr=sr)
            weighted_chroma_sum += np.sum(chunk_chroma, axis=1)
            total_frames += chunk_chroma.shape[1]

    if total_frames == 0:
        # Shouldn't happen with the padding step above unless the file is
        # genuinely empty. Surface a useful message anyway.
        with sf.SoundFile(str(filepath), "r") as f:
            min_seconds = MIN_SAMPLES_FOR_CQT / float(f.samplerate)
        raise ValueError(
            f"Audio file is too short for analysis. "
            f"Minimum duration is ~{min_seconds:.2f} seconds."
        )

    global_avg_chroma: np.ndarray = weighted_chroma_sum / total_frames
    return global_avg_chroma


def extract_local_chroma(
    filepath: PathLike,
    *,
    start_time: float = 0.0,
    end_time: Optional[float] = None,
) -> np.ndarray:
    """Extract a 2D chroma matrix for a time window of the file.

    Two paths inside: short segments read entirely in-memory (faster, more
    accurate at the boundaries); long segments stream in 5-second blocks
    with the same padding behavior as ``extract_global_chroma``. The
    crossover is ``LOCAL_ANALYSIS_STREAMING_THRESHOLD_S``.

    Args:
        filepath: Path to an audio file readable by soundfile.
        start_time: Segment start in seconds (default 0.0). Must be ≥ 0.
        end_time: Segment end in seconds. If ``None``, reads to the end of
            the file. If beyond file duration, clamped to file duration.

    Returns:
        ``np.ndarray`` shape ``(12, T)``, dtype float. Time-axis frames
        depend on librosa's hop_length default (512) and segment length.
        Pass raw to ``detect_cadences``; pre-reduce with ``.mean(axis=1)``
        before ``find_best_key``.

    Raises:
        ValueError: If the segment is empty (start ≥ end), or if a
            non-streamed segment is shorter than ``MIN_SAMPLES_FOR_CQT``
            samples (the streaming path pads its tail; the in-memory path
            requires real signal length to avoid silent confidence
            collapse).
        RuntimeError: Surfaced from soundfile/librosa for unreadable files.
    """
    with sf.SoundFile(str(filepath), "r") as f:
        sr = f.samplerate
        file_duration_sec = len(f) / float(sr)

    # Resolve segment window — clamp end_time to file duration so callers
    # can pass a generous upper bound without thinking about it.
    segment_start_sec = float(start_time)
    if end_time is not None and end_time <= file_duration_sec:
        segment_end_sec = float(end_time)
    else:
        segment_end_sec = file_duration_sec
    segment_duration_sec = segment_end_sec - segment_start_sec

    if segment_duration_sec <= 0:
        raise ValueError("The specified segment is empty or out of bounds.")

    start_sample = librosa.time_to_samples(segment_start_sec, sr=sr)
    end_sample = librosa.time_to_samples(segment_end_sec, sr=sr)
    num_samples_to_read = int(end_sample - start_sample)

    if num_samples_to_read <= 0:
        raise ValueError("The specified segment is empty or out of bounds.")

    chunk_size = sr * _CHUNK_SIZE_SECONDS
    local_chroma: Optional[np.ndarray] = None

    if segment_duration_sec > LOCAL_ANALYSIS_STREAMING_THRESHOLD_S:
        # Long segment — stream it. Same padding pattern as the global path.
        logger.info(
            "Local segment is %.1fs (> %ds threshold). Streaming chroma.",
            segment_duration_sec,
            LOCAL_ANALYSIS_STREAMING_THRESHOLD_S,
        )
        local_chroma_list: list[np.ndarray] = []

        with sf.SoundFile(str(filepath), "r") as f:
            f.seek(int(start_sample))
            samples_processed = 0
            while samples_processed < num_samples_to_read:
                samples_this_chunk = min(
                    chunk_size, num_samples_to_read - samples_processed
                )
                block = f.read(samples_this_chunk, dtype="float32", always_2d=True)
                if not block.size:
                    break

                y_chunk = np.mean(block.T, axis=0)
                samples_processed += len(block)
                chunk_len = len(y_chunk)

                if chunk_len == 0:
                    continue

                if chunk_len < MIN_SAMPLES_FOR_CQT:
                    logger.warning(
                        "Padding final local chunk of length %d to %d samples "
                        "to meet chroma_cqt requirements.",
                        chunk_len,
                        MIN_SAMPLES_FOR_CQT,
                    )
                    pad_width = MIN_SAMPLES_FOR_CQT - chunk_len
                    y_chunk = np.pad(y_chunk, (0, pad_width), "constant")

                chunk_chroma = librosa.feature.chroma_cqt(y=y_chunk, sr=sr)
                local_chroma_list.append(chunk_chroma)

        if not local_chroma_list:
            raise ValueError("Could not process the local segment (no audio read).")

        local_chroma = np.concatenate(local_chroma_list, axis=1)
    else:
        # Short segment — read it whole. Padding only applies to the
        # streamed path; if the in-memory segment is sub-CQT, the caller
        # passed in something we genuinely can't analyze.
        logger.info(
            "Local segment is %.1fs (≤ %ds). Reading direct.",
            segment_duration_sec,
            LOCAL_ANALYSIS_STREAMING_THRESHOLD_S,
        )
        with sf.SoundFile(str(filepath), "r") as f:
            f.seek(int(start_sample))
            y_segment_frames = f.read(
                num_samples_to_read, dtype="float32", always_2d=True
            )
            y_segment = np.mean(y_segment_frames.T, axis=0)
            segment_len = len(y_segment)

            if segment_len < MIN_SAMPLES_FOR_CQT:
                # Pad the in-memory short-path too — short synthetic
                # fixtures (test WAVs) routinely come in under 4096 samples
                # at the tail. Better to pad and analyze than fail loudly.
                logger.warning(
                    "Padding short in-memory segment of length %d to %d samples.",
                    segment_len,
                    MIN_SAMPLES_FOR_CQT,
                )
                pad_width = MIN_SAMPLES_FOR_CQT - segment_len
                y_segment = np.pad(y_segment, (0, pad_width), "constant")

            local_chroma = librosa.feature.chroma_cqt(y=y_segment, sr=sr)

    # Both branches above assign local_chroma; this assert satisfies mypy
    # without runtime overhead on the happy path.
    assert local_chroma is not None, "local_chroma unset — neither branch ran"
    return local_chroma


def extract_local_rms_envelope(
    filepath: PathLike,
    *,
    start_time: float = 0.0,
    end_time: Optional[float] = None,
    hop_length: int = 512,
    frame_length: int = 2048,
) -> np.ndarray:
    """Per-frame RMS envelope for the same window as ``extract_local_chroma``.

    Output is frame-aligned with ``chroma_cqt`` at the same ``hop_length``,
    so callers can index with the same window arithmetic. Used by the chord
    estimator to gate silent windows by *audio energy* — chroma_cqt's
    inf-norm output makes its L2 norm useless as a silence proxy (a -55 dBFS
    noise tail still produces ~unit-norm chroma vectors).

    Same streaming/in-memory split as ``extract_local_chroma``: short
    segments read in one shot, long segments stream in 5-second blocks.

    Args:
        filepath: Path to a soundfile-readable audio file.
        start_time: Segment start in seconds (default 0.0).
        end_time: Segment end in seconds. ``None`` or beyond file duration
            clamps to the file end.
        hop_length: Samples between successive RMS frames. Match this to
            the chroma extraction's hop_length for frame alignment.
        frame_length: Window length in samples for each RMS measurement.
            Default 2048 matches librosa's chroma_cqt default.

    Returns:
        ``np.ndarray`` shape ``(T,)``, dtype float32. Each element is the
        RMS amplitude of the corresponding chroma frame. T matches
        ``chroma_cqt(..., hop_length=hop_length).shape[1]``.

    Raises:
        ValueError: If the segment is empty (start ≥ end).
        RuntimeError: Surfaced from soundfile/librosa.
    """
    with sf.SoundFile(str(filepath), "r") as f:
        sr = f.samplerate
        file_duration_sec = len(f) / float(sr)

    segment_start_sec = float(start_time)
    if end_time is not None and end_time <= file_duration_sec:
        segment_end_sec = float(end_time)
    else:
        segment_end_sec = file_duration_sec
    segment_duration_sec = segment_end_sec - segment_start_sec

    if segment_duration_sec <= 0:
        raise ValueError("The specified segment is empty or out of bounds.")

    start_sample = librosa.time_to_samples(segment_start_sec, sr=sr)
    end_sample = librosa.time_to_samples(segment_end_sec, sr=sr)
    num_samples_to_read = int(end_sample - start_sample)

    if num_samples_to_read <= 0:
        raise ValueError("The specified segment is empty or out of bounds.")

    chunk_size = sr * _CHUNK_SIZE_SECONDS
    rms_arrays: list[np.ndarray] = []

    if segment_duration_sec > LOCAL_ANALYSIS_STREAMING_THRESHOLD_S:
        # Stream — long files would otherwise blow up the heap on weak
        # boxes. RMS itself is cheap, but the underlying audio buffer is
        # the memory pressure point, not the feature math.
        with sf.SoundFile(str(filepath), "r") as f:
            f.seek(int(start_sample))
            samples_processed = 0
            while samples_processed < num_samples_to_read:
                samples_this_chunk = min(
                    chunk_size, num_samples_to_read - samples_processed
                )
                block = f.read(samples_this_chunk, dtype="float32", always_2d=True)
                if not block.size:
                    break
                y_chunk = np.mean(block.T, axis=0)
                samples_processed += len(block)
                if len(y_chunk) == 0:
                    continue
                # Pad short tails the same way chroma extraction does, so
                # the frame counts stay aligned across both passes.
                if len(y_chunk) < MIN_SAMPLES_FOR_CQT:
                    pad_width = MIN_SAMPLES_FOR_CQT - len(y_chunk)
                    y_chunk = np.pad(y_chunk, (0, pad_width), "constant")
                chunk_rms = librosa.feature.rms(
                    y=y_chunk,
                    frame_length=frame_length,
                    hop_length=hop_length,
                )[0]
                rms_arrays.append(chunk_rms)
        if not rms_arrays:
            raise ValueError("Could not process the local segment (no audio read).")
        return np.concatenate(rms_arrays).astype(np.float32)

    # Short segment — read whole.
    with sf.SoundFile(str(filepath), "r") as f:
        f.seek(int(start_sample))
        y_segment_frames = f.read(num_samples_to_read, dtype="float32", always_2d=True)
        y_segment = np.mean(y_segment_frames.T, axis=0)
        if len(y_segment) < MIN_SAMPLES_FOR_CQT:
            pad_width = MIN_SAMPLES_FOR_CQT - len(y_segment)
            y_segment = np.pad(y_segment, (0, pad_width), "constant")
        rms = librosa.feature.rms(
            y=y_segment,
            frame_length=frame_length,
            hop_length=hop_length,
        )[0]
        return np.asarray(rms.astype(np.float32))


# C2 is roughly 65 Hz, B3 is roughly 245 Hz — that's two octaves of bass
# register, which covers electric/acoustic bass guitar, piano left hand,
# upright bass, kick-drum tonals, and most synth bass voices. Going lower
# than C2 starts catching room rumble and HVAC; going higher than B3 starts
# catching guitar voicings and weakens the "this is the chord root"
# inference. Both magic constants come from MIR literature on bass chroma.
_BASS_FMIN_NOTE = "C2"
_BASS_N_OCTAVES = 2


def extract_local_bass_chroma(
    filepath: PathLike,
    *,
    start_time: float = 0.0,
    end_time: Optional[float] = None,
) -> np.ndarray:
    """Bass-register chroma for the same time window as ``extract_local_chroma``.

    Computes ``chroma_cqt`` with ``fmin`` set to C2 and ``n_octaves`` set to
    2, focusing the analysis on the bass register where chord roots
    actually live. Same streaming/in-memory split, same padding behavior,
    same hop length — frames align with ``extract_local_chroma`` output so
    you can index into both with the same window indices.

    Why a separate function instead of an option on ``extract_local_chroma``:
    keeping the two-pass shape explicit at the call site means the chord
    estimator's "I want both" intent is obvious, and it avoids regressing
    callers that only need the full-spectrum chroma. The cost is a second
    pass through the file — measurable on long files but typically <100 ms
    for songs under ~5 minutes. See `process/audio-chord-estimation.md`
    for the algorithm rationale.

    Args:
        filepath: Same as ``extract_local_chroma``.
        start_time: Same.
        end_time: Same.

    Returns:
        ``np.ndarray`` shape ``(12, T)``. Same time axis as
        ``extract_local_chroma`` for the same ``(start_time, end_time)``.
        Each column is the bass-register chroma at one frame.

    Raises:
        Same as ``extract_local_chroma`` — passes through the underlying
        librosa/soundfile errors and the empty-segment ValueError.
    """
    bass_fmin = float(librosa.note_to_hz(_BASS_FMIN_NOTE))

    with sf.SoundFile(str(filepath), "r") as f:
        sr = f.samplerate
        file_duration_sec = len(f) / float(sr)

    segment_start_sec = float(start_time)
    if end_time is not None and end_time <= file_duration_sec:
        segment_end_sec = float(end_time)
    else:
        segment_end_sec = file_duration_sec
    segment_duration_sec = segment_end_sec - segment_start_sec

    if segment_duration_sec <= 0:
        raise ValueError("The specified segment is empty or out of bounds.")

    start_sample = librosa.time_to_samples(segment_start_sec, sr=sr)
    end_sample = librosa.time_to_samples(segment_end_sec, sr=sr)
    num_samples_to_read = int(end_sample - start_sample)

    if num_samples_to_read <= 0:
        raise ValueError("The specified segment is empty or out of bounds.")

    chunk_size = sr * _CHUNK_SIZE_SECONDS
    bass_chroma: Optional[np.ndarray] = None

    if segment_duration_sec > LOCAL_ANALYSIS_STREAMING_THRESHOLD_S:
        bass_chroma_list: list[np.ndarray] = []
        with sf.SoundFile(str(filepath), "r") as f:
            f.seek(int(start_sample))
            samples_processed = 0
            while samples_processed < num_samples_to_read:
                samples_this_chunk = min(
                    chunk_size, num_samples_to_read - samples_processed
                )
                block = f.read(samples_this_chunk, dtype="float32", always_2d=True)
                if not block.size:
                    break
                y_chunk = np.mean(block.T, axis=0)
                samples_processed += len(block)
                chunk_len = len(y_chunk)
                if chunk_len == 0:
                    continue
                if chunk_len < MIN_SAMPLES_FOR_CQT:
                    pad_width = MIN_SAMPLES_FOR_CQT - chunk_len
                    y_chunk = np.pad(y_chunk, (0, pad_width), "constant")
                chunk_chroma = librosa.feature.chroma_cqt(
                    y=y_chunk,
                    sr=sr,
                    fmin=bass_fmin,
                    n_octaves=_BASS_N_OCTAVES,
                )
                bass_chroma_list.append(chunk_chroma)
        if not bass_chroma_list:
            raise ValueError("Could not process the local segment (no audio read).")
        bass_chroma = np.concatenate(bass_chroma_list, axis=1)
    else:
        with sf.SoundFile(str(filepath), "r") as f:
            f.seek(int(start_sample))
            y_segment_frames = f.read(
                num_samples_to_read, dtype="float32", always_2d=True
            )
            y_segment = np.mean(y_segment_frames.T, axis=0)
            segment_len = len(y_segment)
            if segment_len < MIN_SAMPLES_FOR_CQT:
                pad_width = MIN_SAMPLES_FOR_CQT - segment_len
                y_segment = np.pad(y_segment, (0, pad_width), "constant")
            bass_chroma = librosa.feature.chroma_cqt(
                y=y_segment,
                sr=sr,
                fmin=bass_fmin,
                n_octaves=_BASS_N_OCTAVES,
            )

    assert bass_chroma is not None, "bass_chroma unset — neither branch ran"
    return bass_chroma
