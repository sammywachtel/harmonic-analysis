"""Tempo detection for adaptive chord-window sizing.

Auto-rubato uses BPM as a proxy for harmonic rhythm: at slow tempos a
single chord usually spans many seconds, so we want a wider chroma
window to average through figuration; at fast tempos chord changes can
arrive every beat, so we want a narrower window to catch them.

librosa's tempo detector has an octave-error problem (it sometimes locks
onto half-time or double-time — Bach's WTC prelude reads as 129 BPM, not
its musical 65). For window-sizing this mostly doesn't matter: we want a
sensible multiple of the detected beat regardless of whether that beat
is the quarter, eighth, or half. The "2 beats per window" multiplier in
``bpm_to_rubato`` is calibrated to land in a useful window range
(0.4–2.0s) across that octave-error band.

For the variable-tempo case (iteration 2 — coming next), this module
also exposes ``detect_tempo_regions`` which segments the audio into
constant-tempo spans whenever per-frame tempo deviates by more than a
configurable percentage.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

import librosa
import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)

PathLike = Union[str, Path]

# Confidence threshold below which we don't trust the detected BPM enough
# to use it for sizing. 0.3 means "tempo std spans more than ~21 BPM" —
# typical of free-tempo or mostly-silent inputs.
_MIN_TEMPO_CONFIDENCE = 0.3


@dataclass(frozen=True)
class TempoRegion:
    """A constant-tempo span within a longer audio segment.

    Used by variable-tempo analysis to size chord windows differently
    across the file when the music speeds up or slows down. Boundaries
    are in audio time (seconds), inclusive of ``start_time``, exclusive
    of ``end_time``.

    Attributes:
        start_time: Region start in seconds, relative to file start.
        end_time: Region end in seconds.
        bpm: Median BPM over the region.
        confidence: Stability of the per-frame tempo within the region.
            High confidence (>0.7) means BPM was steady throughout.
    """

    start_time: float
    end_time: float
    bpm: float
    confidence: float


@dataclass(frozen=True)
class TempoInfo:
    """BPM detection result for a segment.

    Attributes:
        bpm: Median tempo in beats per minute over the analyzed segment.
            May reflect an octave error vs. the musically-canonical pulse
            — but consistent for sizing analysis windows.
        confidence: Heuristic confidence in [0, 1] based on per-frame
            tempo stability. Below 0.3, callers should treat the BPM as
            unreliable and fall back to defaults.
        regions: Optional list of variable-tempo spans. Empty list when
            the tempo is stable through the segment, multiple regions
            when it changes by more than the detection threshold.
    """

    bpm: float
    confidence: float
    regions: List[TempoRegion] = field(default_factory=list)


def _load_segment(
    filepath: PathLike,
    start_time: float,
    end_time: Optional[float],
) -> tuple[np.ndarray, int]:
    """Read mono audio for a segment. Empty array on degenerate inputs."""
    with sf.SoundFile(str(filepath), "r") as f:
        sr = f.samplerate
        file_duration = len(f) / float(sr)

    seg_end = float(end_time) if end_time is not None else file_duration
    seg_end = min(seg_end, file_duration)
    seg_start = max(0.0, float(start_time))

    if seg_end - seg_start <= 0:
        return np.zeros(0, dtype=np.float32), sr

    start_sample = librosa.time_to_samples(seg_start, sr=sr)
    end_sample = librosa.time_to_samples(seg_end, sr=sr)
    n_samples = int(end_sample - start_sample)
    if n_samples <= 0:
        return np.zeros(0, dtype=np.float32), sr

    with sf.SoundFile(str(filepath), "r") as f:
        f.seek(int(start_sample))
        block = f.read(n_samples, dtype="float32", always_2d=True)
    if block.size == 0:
        return np.zeros(0, dtype=np.float32), sr
    y = np.mean(block.T, axis=0)
    return y, sr


def detect_tempo(
    filepath: PathLike,
    *,
    start_time: float = 0.0,
    end_time: Optional[float] = None,
    detect_regions: bool = False,
    region_change_threshold: float = 0.20,
) -> TempoInfo:
    """Detect global BPM (and optionally tempo regions) for a segment.

    Args:
        filepath: Path to a soundfile-readable audio file.
        start_time: Segment start in seconds.
        end_time: Segment end in seconds, or ``None`` for file end.
        detect_regions: When ``True``, also segment the audio into
            constant-tempo regions (variable-tempo support). When
            ``False``, the returned ``TempoInfo.regions`` is empty.
        region_change_threshold: Minimum fractional BPM change to start
            a new region. 0.20 = 20% change. Default is generous; tighter
            values (0.10) over-segment, looser (0.30) miss real changes.

    Returns:
        ``TempoInfo`` with BPM, confidence, and (optionally) regions.
        Returns ``bpm=0.0, confidence=0.0`` when detection fails — caller
        should treat this as "fall back to defaults".
    """
    y, sr = _load_segment(filepath, start_time, end_time)
    if y.size == 0:
        return TempoInfo(bpm=0.0, confidence=0.0)

    try:
        # aggregate=None gives per-frame tempo; we use the whole envelope
        # for both global BPM and (optionally) regions.
        tempo_array = librosa.feature.tempo(y=y, sr=sr, aggregate=None)
    except Exception as exc:
        # librosa can fail on degenerate inputs (constant signals, very
        # short clips). Don't break the analysis — return a fail sentinel.
        logger.debug("Tempo detection failed: %s", exc)
        return TempoInfo(bpm=0.0, confidence=0.0)

    if tempo_array is None or tempo_array.size == 0:
        return TempoInfo(bpm=0.0, confidence=0.0)

    # Two-step preprocessing before scoring. librosa's onset tempogram
    # has two well-known failure modes on pop/electronic material:
    #
    # 1. **Octave errors** — different sections lock onto different
    #    musical multiples of the same beat (e.g., 84 / 112 / 172 BPM
    #    for the same song). All multiples of each other, but the std
    #    spikes and the confidence collapses. Fold all values into a
    #    one-octave canonical range so doubles/halves merge.
    # 2. **Per-frame jitter** — even within one section, individual
    #    frames flip between adjacent multiples. A moving median
    #    suppresses single-frame spikes without smearing real changes.
    #
    # Order matters: fold first (so smoothing operates on the canonical
    # values), then smooth.
    folded = _fold_octaves(tempo_array)
    smoothed = _moving_median(folded, kernel_size=43)  # ~0.5s @ 86 fps

    bpm = float(np.median(smoothed))
    # Confidence is 1 minus normalized std on the *smoothed-and-folded*
    # curve. Std of 30 BPM is roughly "completely free tempo" →
    # confidence 0; std of 0 is rock-steady → 1.
    std = float(smoothed.std())
    confidence = max(0.0, min(1.0, 1.0 - std / 30.0))

    regions: List[TempoRegion] = []
    if detect_regions and smoothed.size > 1 and confidence > 0.0:
        regions = _segment_tempo(
            smoothed,
            sr=sr,
            segment_start=float(start_time),
            change_threshold=region_change_threshold,
        )

    return TempoInfo(bpm=bpm, confidence=confidence, regions=regions)


def _fold_octaves(
    arr: np.ndarray,
    low: float = 70.0,
    high: float = 140.0,
) -> np.ndarray:
    """Fold tempo values into a one-octave canonical range.

    Iteratively halves anything above ``high`` and doubles anything
    below ``low`` until every value sits in ``[low, high]``. The
    default range ``[70, 140]`` is a perfect octave (140 = 2×70) that
    spans most musical tempi without splitting any common pop or
    classical tempo across the boundary.

    Why this matters: librosa's per-frame tempo can lock onto different
    musical multiples of the same beat in different sections of a song
    (e.g., 84 in the verse, 168 in the chorus, 112 elsewhere — all the
    same underlying tempo, just different beat subdivisions). Without
    folding, the std looks huge and the confidence score collapses.
    With folding, those values collapse to ~84 / ~84 / ~112 — much
    tighter, and confidence reflects actual stability.

    The fold preserves real tempo *changes* within the canonical range
    — a song that genuinely shifts from 95 to 130 BPM still shows that
    shift after folding.
    """
    if arr.size == 0:
        return arr.copy()
    out = arr.astype(np.float64).copy()
    # Bound the loops defensively in case low/high are degenerate.
    if high <= low or low <= 0:
        return out
    # Halve until in range.
    for _ in range(10):  # 10 octaves covers any realistic input
        mask = out > high
        if not np.any(mask):
            break
        out[mask] = out[mask] / 2.0
    # Double until in range.
    for _ in range(10):
        mask = out < low
        if not np.any(mask):
            break
        out[mask] = out[mask] * 2.0
    return out


def _moving_median(arr: np.ndarray, kernel_size: int) -> np.ndarray:
    """Running-median filter over a 1D array, reflecting at edges.

    Used to suppress octave-error spikes in librosa's per-frame tempo
    curve before std/segmentation. Pure numpy, no scipy. Kernel must
    be odd; if it isn't, we round up.
    """
    if arr.size <= 1 or kernel_size <= 1:
        return arr.copy()
    if kernel_size % 2 == 0:
        kernel_size += 1
    pad = kernel_size // 2
    padded = np.pad(arr, pad, mode="reflect")
    out = np.empty_like(arr, dtype=np.float64)
    for i in range(arr.size):
        out[i] = np.median(padded[i : i + kernel_size])
    return out


def _segment_tempo(
    tempo_array: np.ndarray,
    *,
    sr: int,
    segment_start: float,
    change_threshold: float,
    min_region_s: float = 4.0,
    region_merge_threshold: Optional[float] = None,
) -> List[TempoRegion]:
    """Split a per-frame tempo curve into constant-BPM regions.

    Walks the tempo curve; starts a new region whenever the running
    BPM diverges from the current region's mean by more than
    ``change_threshold`` (fractional). Merges regions shorter than
    ``min_region_s`` into their longer neighbors so we don't fragment
    on transient tempo wobble — useful for live performances where one
    rushed bar shouldn't trigger a new tempo region.

    Args:
        tempo_array: 1D array of per-frame BPM estimates from
            ``librosa.feature.tempo(aggregate=None)``.
        sr: Sample rate of the original audio (for time conversion).
        segment_start: Audio time (seconds) corresponding to the first
            element of ``tempo_array``.
        change_threshold: Fractional per-frame divergence from the
            running region mean that triggers a pass-1 split. Tighter
            values (0.10) over-segment on performance jitter, looser
            (0.30) miss real changes.
        min_region_s: Regions shorter than this are merged into the
            longer neighbor. 4 seconds catches single-bar wobble in
            most popular tempos.
        region_merge_threshold: Pass-3 inter-region mean divergence
            below which adjacent regions collapse back into one. Should
            be slightly more lenient than ``change_threshold`` because
            pass 1 detects single-frame outliers while pass 3 evaluates
            sustained means — a region with mean 20.5% off its neighbor
            can be the same musical idea with one outlier frame, but a
            single frame at 20.5% definitely deserves a new region.
            Defaults to ``change_threshold + 0.02`` (so 0.20 → 0.22)
            which empirically resolves Bach's ritardando-at-end (~20.5%
            inter-region diff, should merge) without losing genuine
            section-level tempo bumps (typically 22%+).

    Returns:
        List of ``TempoRegion`` covering the full duration. Always at
        least one region when the input is non-empty.
    """
    # librosa.feature.tempo's frame rate matches its onset envelope —
    # default hop_length=512 → frames_per_sec = sr/512.
    fps = sr / 512.0

    # Pass 3's threshold defaults to slightly more lenient than pass 1's.
    # See the docstring for the full rationale; in short: per-frame
    # outliers shouldn't survive into the final region list.
    if region_merge_threshold is None:
        region_merge_threshold = change_threshold + 0.02

    # First pass: split on any frame where the current frame deviates
    # from the running region mean by more than the threshold.
    raw_regions: List[tuple[int, int, float]] = []  # (start_frame, end_frame, mean_bpm)
    region_start = 0
    running_sum = 0.0
    running_n = 0

    def _flush_region(end_frame: int) -> None:
        nonlocal region_start, running_sum, running_n
        if running_n > 0:
            mean_bpm = running_sum / running_n
            raw_regions.append((region_start, end_frame, mean_bpm))
        region_start = end_frame
        running_sum = 0.0
        running_n = 0

    for i, bpm in enumerate(tempo_array):
        if running_n == 0:
            running_sum = float(bpm)
            running_n = 1
            continue
        running_mean = running_sum / running_n
        if running_mean <= 0:
            running_sum += float(bpm)
            running_n += 1
            continue
        if abs(float(bpm) - running_mean) / running_mean > change_threshold:
            _flush_region(i)
            running_sum = float(bpm)
            running_n = 1
        else:
            running_sum += float(bpm)
            running_n += 1

    _flush_region(len(tempo_array))

    # Second pass: merge tiny regions into larger neighbors. Pure
    # threshold-based segmentation generates spurious 1-2 frame regions
    # at every tempo wobble; this filters out the noise.
    if not raw_regions:
        return []

    min_region_frames = int(min_region_s * fps)
    cleaned: List[tuple[int, int, float]] = [raw_regions[0]]
    for start, end, mean in raw_regions[1:]:
        prev_start, prev_end, prev_mean = cleaned[-1]
        prev_len = prev_end - prev_start
        curr_len = end - start
        if curr_len < min_region_frames or prev_len < min_region_frames:
            # Merge into previous, weighted by length
            new_len = prev_len + curr_len
            new_mean = (prev_mean * prev_len + mean * curr_len) / new_len
            cleaned[-1] = (prev_start, end, new_mean)
        else:
            cleaned.append((start, end, mean))

    # Third pass: merge adjacent regions whose means are within wobble
    # range of each other. Pass 1 starts a new region on a *single*
    # outlier frame even when the long-run mean stays similar (one
    # missed onset, librosa double-counting a syncopation, a single
    # rushed bar). Pass 2 catches the cases where one of the two
    # neighbors is short. But neighbors that both clear ``min_region_s``
    # with similar means still escape — a region split should require
    # a *sustained* tempo change, not a momentary wobble.
    if len(cleaned) > 1:
        coalesced: List[tuple[int, int, float]] = [cleaned[0]]
        for start, end, mean in cleaned[1:]:
            prev_start, prev_end, prev_mean = coalesced[-1]
            if prev_mean <= 0:
                coalesced[-1] = (prev_start, end, mean)
                continue
            mean_diff = abs(mean - prev_mean) / prev_mean
            if mean_diff <= region_merge_threshold:
                prev_len = prev_end - prev_start
                curr_len = end - start
                new_len = prev_len + curr_len
                new_mean = (prev_mean * prev_len + mean * curr_len) / new_len
                coalesced[-1] = (prev_start, end, new_mean)
            else:
                coalesced.append((start, end, mean))
        cleaned = coalesced

    # Convert frames to seconds and compute per-region confidence.
    out: List[TempoRegion] = []
    for start_f, end_f, mean_bpm in cleaned:
        if end_f <= start_f:
            continue
        sub = tempo_array[start_f:end_f]
        std = float(sub.std())
        conf = max(0.0, min(1.0, 1.0 - std / 30.0))
        out.append(
            TempoRegion(
                start_time=segment_start + start_f / fps,
                end_time=segment_start + end_f / fps,
                bpm=float(mean_bpm),
                confidence=conf,
            )
        )

    return out


def bpm_to_rubato(
    bpm: float,
    confidence: float = 1.0,
) -> tuple[float, float, int]:
    """Map detected BPM (and confidence) to (window_s, hop_s, kernel).

    Window scales as ``2 * (60 / bpm)`` — about two beats — clamped to
    ``[0.4, 2.0]`` seconds. Hop is half the window (matches the existing
    presets' 50% overlap). Median kernel widens to 5 when the window is
    long enough that ping-pong smoothing matters.

    Why "2 beats" specifically: librosa's tempo detector frequently locks
    onto a half- or double-time beat, so "1 beat" gives wildly different
    window sizes for musically-equivalent tempi. Two-beat windows are
    less sensitive to which subdivision was detected — at Bach's WTC
    prelude (detected 129 BPM, musical 65 BPM), 2 detected beats =
    0.93s = roughly one quarter at the musical tempo, which is the
    right harmonic-rhythm-spanning window.

    Args:
        bpm: Detected tempo. ``<=0`` triggers the ``moderate`` fallback.
        confidence: Detection confidence in [0, 1]. Below
            ``_MIN_TEMPO_CONFIDENCE``, falls back to ``moderate``.

    Returns:
        ``(window_size_s, hop_size_s, median_kernel)`` tuple, same shape
        as the static rubato presets in ``_profiles.py``.
    """
    if confidence < _MIN_TEMPO_CONFIDENCE or bpm <= 0:
        # Loose fallback — same numbers as the "loose" static preset.
        # Material that defeats BPM detection (heavy reverb, free tempo,
        # busy electronic production) is exactly the material that
        # produces the most chord-event fragmentation under moderate's
        # 0.5s window. Loose's 0.75s window + kernel=5 absorbs the
        # ambiguity better. If the caller wants tight grids despite
        # detection failure, they can pass an explicit static preset.
        return (0.75, 0.4, 5)

    # Cap the auto-window at 1.0s. Two beats is the right multiplier at
    # higher detected tempos (where each "beat" is short), but at slower
    # tempos like 90 BPM it gives a 1.32s window — wide enough to
    # over-smooth piano music with chord-per-beat harmonic rhythm.
    # Brief dominant chords (V before i) get averaged into the
    # surrounding chords, and cadential loses the V→i evidence it
    # needs to identify the tonic. 1.0s is the empirical sweet spot:
    # still catches Bach's sixteenth-note figuration (132 BPM detected
    # → 0.91s, unchanged) but doesn't smear piano transients
    # (90 BPM → was 1.32s, now capped to 1.0s).
    window_s = 2.0 * (60.0 / bpm)
    window_s = max(0.4, min(1.0, window_s))
    hop_s = window_s / 2.0
    # Larger window → more figuration averaged in → ping-pong is rarer
    # but when it does happen, a wider median window is the right
    # antidote. Threshold 0.7s is a soft cliff.
    kernel = 5 if window_s >= 0.7 else 3
    return (window_s, hop_s, kernel)
