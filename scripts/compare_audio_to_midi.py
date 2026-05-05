#!/usr/bin/env python3
"""Compare audio chord estimation against a MIDI ground truth.

For each ChordEvent the audio analyzer produces (or for a fixed time grid),
read the simultaneous MIDI notes, infer their chord identity from the
pitch-class set, and report agreement vs disagreement.

Usage:
    python scripts/compare_audio_to_midi.py audio.mp3 ground.mid
    python scripts/compare_audio_to_midi.py audio.mp3 ground.mid --bass-chroma
    python scripts/compare_audio_to_midi.py audio.mp3 ground.mid --grid 0.25

The "chord identity from MIDI" inference is intentionally simple:
    1. Take pitch classes of all notes sounding in the window.
    2. Try every (root × {major, minor}) template; pick the best fit.
    3. Bias toward the template that includes the lowest-MIDI note as root.
That's not a full chord-recognition system — it's just "what triad best
fits the notes that are sounding right now," which is what we want to
compare against the audio's template-matching estimator.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Callable, List, Optional, Tuple

# Pitch class names — keep in sync with PITCH_CLASSES in audio/_profiles.py
PCS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Triad templates: root index → set of pitch class indices
MAJ = {0, 4, 7}
MIN = {0, 3, 7}

# DTW frame rate — coarser than audio's chroma analysis but plenty for
# alignment. 50ms hops at 22050 Hz with hop_length=1102 ≈ 20 fps. Tuning
# coarser than this risks missing fast chord changes; finer than this
# inflates the DTW matrix to no useful end. Magic number lifted from
# typical MIR alignment papers.
DTW_HOP_SEC = 0.05


def _midi_pitch_class(midi: int) -> int:
    """MIDI note number → pitch class 0-11."""
    return midi % 12


def _label_for_root(root_pc: int, quality: str) -> str:
    """Build a chord label like 'D' or 'Bm'."""
    return PCS[root_pc] + ("m" if quality == "minor" else "")


def _midi_chord_at(
    midi_notes: List[Tuple[float, float, int]],
    t_start: float,
    t_end: float,
) -> Optional[str]:
    """Best-fit major/minor triad over notes sounding in [t_start, t_end].

    Args:
        midi_notes: List of (start_sec, end_sec, midi_pitch).
        t_start: Window start in seconds.
        t_end: Window end in seconds.

    Returns:
        Chord label (e.g. 'Bm', 'D') or None if no notes are sounding.
    """
    # Notes that overlap the window
    sounding = [(s, e, p) for s, e, p in midi_notes if s < t_end and e > t_start]
    if not sounding:
        return None

    # Pitch class set, weighted by how much each note overlaps the window.
    # A held note covering the whole window counts more than a brief one.
    pc_weight = [0.0] * 12
    for s, e, p in sounding:
        overlap = max(0.0, min(e, t_end) - max(s, t_start))
        pc_weight[_midi_pitch_class(p)] += overlap

    # Lowest sounding note → bias toward triads where it's the root
    lowest_pc = _midi_pitch_class(min(p for _, _, p in sounding))

    # Score every (root, quality) triad by weighted PC match
    best_score = -1.0
    best_label = None
    for root in range(12):
        for quality, intervals in (("major", MAJ), ("minor", MIN)):
            triad_pcs = {(root + i) % 12 for i in intervals}
            score = sum(pc_weight[pc] for pc in triad_pcs)
            # Bonus when the bass note is the root (the inversion-aware nudge)
            if root == lowest_pc:
                score += 0.3 * sum(pc_weight)
            if score > best_score:
                best_score = score
                best_label = _label_for_root(root, quality)
    return best_label


def _midi_total_duration(midi_notes: List[Tuple[float, float, int]]) -> float:
    """End-time of the last sounding note. Zero if the file is empty."""
    return max((end for _, end, _ in midi_notes), default=0.0)


def _load_midi(midi_path: Path) -> List[Tuple[float, float, int]]:
    """Parse a MIDI file → list of (start_sec, end_sec, midi_pitch).

    Uses music21 (already a project dep). Tempo is taken from the first
    MetronomeMark; if absent, defaults to 120. Tempo changes inside the
    file aren't honored — fine for short pieces, lossy for long ones.
    """
    from music21 import chord as m21chord
    from music21 import converter
    from music21 import note as m21note

    s = converter.parse(str(midi_path))
    flat = s.flatten().notes

    # Tempo for beat→seconds conversion. music21 stores offsets in
    # quarter-note beats; multiply by (60 / bpm) for seconds.
    mm = s.flatten().getElementsByClass("MetronomeMark")
    bpm = float(mm[0].number) if mm else 120.0
    sec_per_beat = 60.0 / bpm

    out: List[Tuple[float, float, int]] = []
    for elem in flat:
        start_sec = float(elem.offset) * sec_per_beat
        dur_sec = float(elem.duration.quarterLength) * sec_per_beat
        end_sec = start_sec + dur_sec
        if isinstance(elem, m21note.Note):
            out.append((start_sec, end_sec, elem.pitch.midi))
        elif isinstance(elem, m21chord.Chord):
            for p in elem.pitches:
                out.append((start_sec, end_sec, p.midi))
    return out


def _format_label(label: Optional[str]) -> str:
    return label if label else "—"


def _synthesize_midi_chroma(
    midi_notes: List[Tuple[float, float, int]],
    total_duration: float,
    hop_sec: float = DTW_HOP_SEC,
) -> "np.ndarray":  # type: ignore[name-defined]  # noqa: F821
    """Build a per-frame chroma matrix from MIDI note events.

    For each frame, sum a 1.0 contribution per sounding note's pitch class,
    plus a 0.5 contribution at the octave (same PC) to model the first
    harmonic. That's not a full physical model, but it's enough to give
    DTW the smooth chroma shape it needs for cosine-distance alignment.

    Args:
        midi_notes: List of (start_sec, end_sec, midi_pitch) tuples.
        total_duration: Length of the MIDI in seconds.
        hop_sec: Frame hop size.

    Returns:
        ``np.ndarray`` shape ``(12, n_frames)``, L2-normalized per column.
    """
    import numpy as np

    n_frames = int(total_duration / hop_sec) + 2
    chroma = np.zeros((12, n_frames), dtype=np.float64)

    for start_s, end_s, pitch in midi_notes:
        f0 = max(0, int(start_s / hop_sec))
        f1 = min(n_frames, int(end_s / hop_sec) + 1)
        if f1 <= f0:
            continue
        pc = pitch % 12
        # Fundamental contribution
        chroma[pc, f0:f1] += 1.0
        # First harmonic at the octave — same PC, slightly weaker.
        # Mostly a fail-safe; if a note is held the chroma value already
        # accumulates, so this is mainly relevant for staccato playing.
        chroma[pc, f0:f1] += 0.5

    # L2-normalize each column. Silent frames (norm=0) stay zero — DTW's
    # cosine metric handles that fine (cosine of zero vector is undefined,
    # but librosa's cosine-distance treats it as max distance).
    # Replace zero norms with 1 BEFORE dividing — np.where doesn't
    # short-circuit, and ``chroma / norms`` still produces NaN for any
    # column with norm 0 even if the where-clause discards it.
    norms = np.linalg.norm(chroma, axis=0, keepdims=True)
    safe_norms = np.where(norms > 0, norms, 1.0)
    chroma = chroma / safe_norms
    return chroma


def _compute_audio_chroma(
    audio_path: Path, hop_sec: float = DTW_HOP_SEC
) -> "np.ndarray":  # type: ignore[name-defined]  # noqa: F821
    """Extract chroma_cqt from an audio file at the given frame rate.

    librosa's hop_length is in samples, so we convert: hop_length =
    int(hop_sec * sr). Slightly fudged for sr=22050 (≈ 1102 samples per
    50ms frame) — librosa's CQT internally rounds to power-of-two-ish
    boundaries but the hop is honored.
    """
    import librosa
    import numpy as np

    y, sr = librosa.load(str(audio_path), sr=22050, mono=True)
    hop_length = int(round(hop_sec * sr))
    chroma: "np.ndarray" = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
    # L2-normalize for cosine-distance DTW
    # Replace zero norms with 1 BEFORE dividing — np.where doesn't
    # short-circuit, and ``chroma / norms`` still produces NaN for any
    # column with norm 0 even if the where-clause discards it.
    norms = np.linalg.norm(chroma, axis=0, keepdims=True)
    safe_norms = np.where(norms > 0, norms, 1.0)
    chroma = chroma / safe_norms
    return chroma


def _build_dtw_warp(
    audio_path: Path,
    midi_notes: List[Tuple[float, float, int]],
    midi_total_duration: float,
    hop_sec: float = DTW_HOP_SEC,
) -> Callable[[float], float]:
    """DTW-align audio chroma to MIDI chroma; return a warping function.

    The returned function maps audio time (seconds) → MIDI time (seconds).
    librosa's DTW with ``subseq=True`` lets the audio sequence start
    anywhere in the MIDI sequence, which is exactly what we want when the
    audio has lead-in silence.

    Implementation note: the warping path comes back as a (P, 2) array of
    (audio_frame, midi_frame) pairs in reverse order. We flip it, convert
    frames to seconds, and use ``np.interp`` for piecewise-linear
    interpolation between path nodes.
    """
    import librosa
    import numpy as np

    audio_chroma = _compute_audio_chroma(audio_path, hop_sec=hop_sec)
    midi_chroma = _synthesize_midi_chroma(
        midi_notes, total_duration=midi_total_duration, hop_sec=hop_sec
    )
    print(
        f"  DTW: audio {audio_chroma.shape[1]} frames, "
        f"MIDI {midi_chroma.shape[1]} frames, hop={hop_sec}s"
    )

    # Cost matrix + warping path. subseq=True means the start of the
    # MIDI sequence can match anywhere along the audio sequence — this
    # is what lets us handle lead-in silence cleanly without having to
    # pre-compute a constant offset.
    #
    # Metric note: cosine distance on L2-normalized chroma is the natural
    # similarity metric, but cosine is undefined on zero vectors (silent
    # frames) and produces NaNs in the cost matrix that DTW then refuses.
    # Euclidean distance on the same L2-normalized features gives a
    # monotonically equivalent ordering — the DTW path is the same up to
    # rounding — and well-defined everywhere. Lessons hard-won from a
    # NaN cost matrix.
    _, wp = librosa.sequence.dtw(
        X=midi_chroma, Y=audio_chroma, subseq=True, metric="euclidean"
    )

    # wp shape (P, 2): each row is (midi_frame, audio_frame). Reverse so
    # rows are in increasing time order.
    wp = wp[::-1]
    midi_frames = wp[:, 0].astype(np.float64)
    audio_frames = wp[:, 1].astype(np.float64)
    audio_times = audio_frames * hop_sec
    midi_times = midi_frames * hop_sec

    # Sort by audio time (DTW path is monotonic but may have plateau
    # ties; the sort is just defensive).
    order = np.argsort(audio_times)
    audio_times = audio_times[order]
    midi_times = midi_times[order]

    # Drop duplicates so np.interp's xp is strictly increasing
    unique_mask = np.concatenate(([True], np.diff(audio_times) > 0))
    audio_times = audio_times[unique_mask]
    midi_times = midi_times[unique_mask]

    def warp(audio_t: float) -> float:
        # np.interp clamps at the endpoints, which is the right behavior
        # for audio outside the DTW window (lead-in / trail-out silence).
        return float(np.interp(audio_t, audio_times, midi_times))

    return warp


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path, help="Audio file (WAV/MP3)")
    parser.add_argument("midi", type=Path, help="MIDI ground truth")
    parser.add_argument(
        "--bass-chroma",
        action="store_true",
        dest="bass_chroma",
        help="enable bass-aware chord estimation in the audio analyzer",
    )
    parser.add_argument(
        "--bass-bonus",
        type=float,
        default=0.3,
        dest="bass_bonus",
    )
    parser.add_argument(
        "--tonal-bias",
        type=float,
        default=0.15,
        dest="tonal_bias",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=30,
        help="show first N comparisons (default 30)",
    )
    parser.add_argument(
        "--offset",
        type=float,
        default=None,
        help="audio→MIDI time offset in seconds (auto-detected if omitted). "
        "audio time T corresponds to MIDI time T - offset.",
    )
    parser.add_argument(
        "--energy-threshold",
        type=float,
        default=0.01,
        dest="energy_threshold",
        help="amplitude threshold for auto-detecting audio start (default 0.01)",
    )
    parser.add_argument(
        "--dtw",
        action="store_true",
        help="use Dynamic Time Warping to align audio→MIDI time. "
        "Handles tempo drift / rubato that constant offset can't.",
    )
    args = parser.parse_args()

    if not args.audio.exists():
        print(f"error: no such file: {args.audio}", file=sys.stderr)
        return 2
    if not args.midi.exists():
        print(f"error: no such file: {args.midi}", file=sys.stderr)
        return 2

    print(f"loading MIDI: {args.midi}")
    midi_notes = _load_midi(args.midi)
    print(f"  {len(midi_notes)} note events")

    # Build the audio→MIDI time mapping. Three modes, in order of
    # robustness: --dtw (handles rubato + lead-in), --offset (constant
    # offset), or auto-detect from first audible sample (constant offset
    # too, but inferred from the audio).
    warp: Callable[[float], float]
    if args.dtw:
        midi_dur = _midi_total_duration(midi_notes)
        print(f"DTW alignment (MIDI duration: {midi_dur:.2f}s)")
        warp = _build_dtw_warp(args.audio, midi_notes, midi_dur)
        print(
            f"  warp samples: 0.0s→{warp(0.0):.2f}s, "
            f"5.0s→{warp(5.0):.2f}s, "
            f"100.0s→{warp(100.0):.2f}s"
        )
    elif args.offset is not None:
        offset_const = float(args.offset)
        print(f"using explicit offset: {offset_const:.3f}s (constant)")
        warp = lambda t: t - offset_const  # noqa: E731
    else:
        import numpy as np
        import soundfile as sf

        y, sr = sf.read(str(args.audio))
        y_mono = y if y.ndim == 1 else y.mean(axis=1)
        energy = np.abs(y_mono)
        first_idx = int(np.argmax(energy > args.energy_threshold))
        offset_const = first_idx / float(sr)
        print(
            f"auto-detected offset: {offset_const:.3f}s "
            f"(first sample > {args.energy_threshold} amplitude, constant)"
        )
        warp = lambda t: t - offset_const  # noqa: E731

    print(f"analyzing audio: {args.audio}  (bass_chroma={args.bass_chroma})")
    from harmonic_analysis import analyze_audio_async

    result = await analyze_audio_async(
        args.audio,
        use_bass_chroma=args.bass_chroma,
        bass_bonus=args.bass_bonus,
        tonal_bias=args.tonal_bias,
    )
    audio_chords = result.chords
    print(f"  global key: {result.global_key.tonic} {result.global_key.mode}")
    print(f"  {len(audio_chords)} chord events")
    print()

    # Compare every audio chord event against the MIDI ground truth at the
    # same time window. "Match" allows enharmonic equivalents (D# == Eb)
    # because we labeled both sides with sharps.
    print(
        f"{'audio time':>14}  {'midi time':>14}  "
        f"{'audio':>8}  {'midi':>8}  {'match'}"
    )
    print("-" * 64)
    matches = 0
    total = 0
    shown = 0
    mismatches: List[Tuple[float, float, str, str]] = []
    for ce in audio_chords:
        # Audio time T maps to MIDI time warp(T). DTW or constant offset.
        midi_t_start = warp(ce.start_time)
        midi_t_end = warp(ce.end_time)
        # Skip events that fall before the MIDI starts (e.g., events
        # entirely in the audio's lead-in silence).
        if midi_t_end <= 0:
            continue
        midi_label = _midi_chord_at(midi_notes, midi_t_start, midi_t_end)
        is_match = midi_label is not None and midi_label == ce.chord_label
        if midi_label is not None:
            total += 1
            if is_match:
                matches += 1
            else:
                mismatches.append(
                    (ce.start_time, ce.end_time, ce.chord_label, midi_label)
                )
        if shown < args.limit:
            mark = "ok" if is_match else ("? " if midi_label is None else "no")
            print(
                f"  {ce.start_time:6.2f}-{ce.end_time:6.2f}  "
                f"{midi_t_start:6.2f}-{midi_t_end:6.2f}  "
                f"{ce.chord_label:>8}  {_format_label(midi_label):>8}  {mark}"
            )
            shown += 1

    print()
    print(
        f"matches: {matches}/{total} = {100.0 * matches / total:.1f}%"
        if total
        else "no overlapping events"
    )

    # Top mismatches grouped by (audio_label, midi_label) pair
    if mismatches:
        print()
        print("mismatch frequency (audio → midi):")
        from collections import Counter

        pair_counts = Counter((a, m) for _, _, a, m in mismatches)
        for (audio_lbl, midi_lbl), count in pair_counts.most_common(10):
            print(f"  {audio_lbl:>6} → {midi_lbl:<6}  ({count}×)")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
