"""Tonal-context-aware chord template matching for streaming chroma frames.

Converts 2D chroma matrices (12, T) into timestamped ChordEvent instances
by sliding a window over the chroma, computing cosine similarity against a
bank of 24 chord templates (12 roots x {major, minor}), and consolidating
consecutive identical labels into contiguous events.

Explicit limits — read before filing bugs:
    * **triads only** — major and minor. No diminished, augmented, or sus.
    * **no inversions** — root-position templates; first inversion C/E and
      root-position C look identical in chroma space anyway, so this is
      less of a limitation than it sounds.
    * **no extensions** — no 7ths, 9ths, 11ths, 13ths. A Cmaj7 will
      match as either C or Em depending on which template wins the
      similarity race.
    * **no slash chords** — see "no inversions" above.

Quality target: diatonic accuracy on clean audio with stable harmony.
Polyphonic pop/rock with fast chord changes or heavy distortion will
produce plausible-but-noisy results. That's a feature request, not a bug.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

from ._profiles import PITCH_CLASSES
from ._types import KeyInfo

# Bass-confidence threshold for applying the root-match bonus. Below this,
# the bass chroma is too flat (no distinct bass note — silent passage,
# distortion, or instrument with no bass register) and the bonus would
# push noise around. 0.25 is conservative; 0.4+ would only fire on very
# clean bass signals. Tunable per-call via the bass_confidence_threshold
# argument.
_DEFAULT_BASS_CONF_THRESHOLD = 0.25

# Data-driven chord quality definitions. Each entry is (suffix, intervals).
# Adding a new quality here auto-populates templates for all 12 roots — no
# code changes needed. But heads up: _TEMPLATE_LABELS ordering is load-
# bearing for the median smoother, so append-only or retest thoroughly.
#
# Triads: needed for plain pop/rock chords and as the baseline matcher.
# 7ths: secondary dominants (V7/x), vii°7, and any music post-Bach really.
# Without them, a G7 chord in Bach gets called G or Em (3 of 4 notes
# overlap with each), and a F#dim7 secondary leading-tone chord can't be
# named at all — it just becomes whichever triad happens to win.
_CHORD_QUALITY_DEFS: list[tuple[str, tuple[int, ...]]] = [
    ("", (0, 4, 7)),  # major triad
    ("m", (0, 3, 7)),  # minor triad
    ("dim", (0, 3, 6)),  # diminished triad — vii° in major keys
    ("7", (0, 4, 7, 10)),  # dominant 7th — V7, V7/x
    ("m7", (0, 3, 7, 10)),  # minor 7th — common ii7, vi7
    ("maj7", (0, 4, 7, 11)),  # major 7th — Imaj7 in jazz/pop
    ("dim7", (0, 3, 6, 9)),  # fully diminished 7th — vii°7 / leading-tone
    ("m7b5", (0, 3, 6, 10)),  # half-diminished — iiø7 in minor keys
]


def _build_chord_templates() -> Dict[str, np.ndarray]:
    """Build unit-norm 12-bin chord templates for all roots and qualities.

    Each template is a 12-element vector with 1.0 at the pitch classes of the
    triad, then L2-normalized to unit norm. Cosine similarity between a
    unit-norm chroma frame and a unit-norm template reduces to a dot product,
    which is why we bother with the normalization.

    Iterates ``_CHORD_QUALITY_DEFS`` for each root, so the ordering is:
    for each root (C, C#, D, ..., B): emit major then minor. Extending
    ``_CHORD_QUALITY_DEFS`` adds new qualities after minor for each root.

    Naming convention:
        Major: "C", "C#", "D", ..., "B"
        Minor: "Cm", "C#m", "Dm", ..., "Bm"

    Returns:
        Dict mapping chord label to np.ndarray of shape (12,).
    """
    templates: Dict[str, np.ndarray] = {}

    for root_idx, root_name in enumerate(PITCH_CLASSES):
        for suffix, intervals in _CHORD_QUALITY_DEFS:
            vec = np.zeros(12, dtype=np.float64)
            for interval in intervals:
                vec[(root_idx + interval) % 12] = 1.0
            vec /= np.linalg.norm(vec)
            templates[f"{root_name}{suffix}"] = vec

    return templates


# Computed once at import time — 24 templates, immutable after this line.
CHORD_TEMPLATES = _build_chord_templates()


def _build_chord_pc_sets() -> Dict[str, frozenset]:
    """All pitch classes contained in each chord, parallel to CHORD_TEMPLATES.

    Used by the diatonic check to ask "are *all* chord tones in the key?"
    rather than just "is the root in the key?". Root-only mistakes Cm for
    diatonic in C major because C is in the key — even though the Eb isn't.
    """
    pc_sets: Dict[str, frozenset] = {}
    for root_idx, root_name in enumerate(PITCH_CLASSES):
        for suffix, intervals in _CHORD_QUALITY_DEFS:
            label = f"{root_name}{suffix}"
            pc_sets[label] = frozenset((root_idx + i) % 12 for i in intervals)
    return pc_sets


# Parallel to CHORD_TEMPLATES — same keys, different value type. Used for
# the is_diatonic flag and the tonal_bias mask.
CHORD_PC_SETS = _build_chord_pc_sets()

# Pre-compute the template matrix and ordered label list for vectorized
# similarity computation. Rows = templates, columns = pitch classes.
_TEMPLATE_LABELS: List[str] = list(CHORD_TEMPLATES.keys())
_TEMPLATE_MATRIX: np.ndarray = np.array(
    [CHORD_TEMPLATES[label] for label in _TEMPLATE_LABELS], dtype=np.float64
)


def _trailing_mean(arr: np.ndarray, window: int) -> np.ndarray:
    """Trailing-window mean at every index using cumulative sums.

    For index ``i``, returns ``mean(arr[max(0, i - window + 1) : i + 1])``
    — the average over the preceding ``window`` samples (inclusive of
    ``i``). Used by the adaptive (envelope-relative) silence gate so
    each chord-estimation window can compare its own energy to recent
    context without recomputing the average per window.

    O(n) via cumulative sum. Reflects no-history correctly: index 0's
    "trailing mean" is just ``arr[0]``, not zero.
    """
    n = arr.size
    if n == 0:
        return arr.copy().astype(np.float64)
    w = max(1, window)
    if w >= n:
        # Window covers everything — every index gets the prefix mean.
        csum = np.cumsum(arr.astype(np.float64))
        counts = np.arange(1, n + 1, dtype=np.float64)
        return csum / counts
    csum = np.concatenate([[0.0], np.cumsum(arr.astype(np.float64))])
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        start = max(0, i - w + 1)
        out[i] = (csum[i + 1] - csum[start]) / (i + 1 - start)
    return out


def _root_pitch_class(label: str) -> int:
    """Extract the root pitch class (0-11) from a chord label.

    Handles every label the template bank can emit: 'C', 'C#', 'Cm',
    'C#m', 'C7', 'Cm7', 'Cmaj7', 'Cdim', 'Cdim7', 'Cm7b5', etc. The
    root is always 1 letter (A-G) optionally followed by '#'; whatever
    comes after is the quality suffix and is ignored here.

    Raises ValueError on empty or unparseable labels — better to crash
    loudly than silently scramble a key analysis.
    """
    if not label:
        raise ValueError(f"Empty chord label: {label!r}")
    # PITCH_CLASSES is sharps-only (matches the toolkit), so no flat handling.
    if len(label) >= 2 and label[1] == "#":
        root_name = label[:2]
    else:
        root_name = label[:1]
    return PITCH_CLASSES.index(root_name)


def estimate_chord_progression(
    local_chroma_frames: np.ndarray,
    global_key: KeyInfo,
    *,
    sr: int = 22050,
    hop_length: int = 512,
    window_size_s: float = 0.5,
    hop_size_s: float = 0.25,
    tonal_bias: float = 0.15,
    bass_chroma_frames: Optional[np.ndarray] = None,
    bass_bonus: float = 0.3,
    bass_confidence_threshold: float = _DEFAULT_BASS_CONF_THRESHOLD,
    min_chroma_norm: float = 0.05,
    rms_frames: Optional[np.ndarray] = None,
    rms_silence_threshold: float = 0.005,
    trailing_silence_window_s: float = 3.0,
    trailing_silence_ratio: float = 0.10,
    median_kernel: int = 3,
    merge_same_root: bool = True,
    max_merge_duration_s: float = 4.0,
) -> list:
    """Estimate a chord progression from a 2D chroma matrix.

    Slides a window over the chroma frames, computes cosine similarity
    against 24 major/minor triad templates, applies optional tonal bias
    for diatonic chords, optionally applies a bass-aware root-match
    bonus, smooths with a running median, and consolidates consecutive
    identical labels into ChordEvent instances.

    Args:
        local_chroma_frames: Shape ``(12, T)`` full-spectrum chroma matrix
            from librosa.
        global_key: KeyInfo with ``diatonic_pitch_classes`` and
            ``confidence``.
        sr: Sample rate used during chroma extraction.
        hop_length: Hop length used during chroma extraction (librosa
            default: 512).
        window_size_s: Analysis window size in seconds.
        hop_size_s: Analysis hop size in seconds.
        tonal_bias: Bonus added to cosine similarity for diatonic chord
            templates. Set to 0.0 to disable. Auto-zeroed when
            ``global_key.confidence < 0.5``.
        bass_chroma_frames: Optional shape ``(12, T)`` bass-register
            chroma (e.g., from ``extract_local_bass_chroma``). When
            provided, each window's dominant bass pitch class adds a
            per-template bonus to chord templates whose root matches —
            the disambiguator for relative-pair confusions like Bm vs D
            and Am vs C. Must have the same time axis as
            ``local_chroma_frames``; mismatched shapes are silently
            skipped (best-effort fallback to full-spectrum behavior).
        bass_bonus: Maximum bonus added to a template's cosine similarity
            when its root matches the detected bass pitch class. Scaled
            by per-window bass confidence — silent or flat-bass windows
            contribute zero. 0.3 is roughly equal to two diatonic biases;
            0.5 is aggressive; 0.15 is gentle.
        bass_confidence_threshold: Minimum bass-chroma peakiness (max-PC
            value relative to mean) required to apply the bonus. Below
            this, the bass signal is too flat to trust and the window
            falls back to full-spectrum-only matching.
        min_chroma_norm: L2 norm threshold below which a window is
            treated as silence and skipped entirely. Weak as a silence
            check on its own — librosa's chroma_cqt uses inf-norm
            normalization, so even -55 dBFS room noise produces a
            ~unit-norm chroma vector. Pair with ``rms_frames`` for a
            real silence gate. 0.05 is conservative.
        rms_frames: Optional shape ``(T,)`` array of per-frame RMS
            amplitudes, frame-aligned with ``local_chroma_frames``.
            When provided, windows whose mean RMS is below
            ``rms_silence_threshold`` are skipped entirely — closes
            the silent-tail hole that ``min_chroma_norm`` can't.
            Use ``extract_local_rms_envelope`` to build it.
        rms_silence_threshold: Absolute RMS floor below which a window
            is treated as silence (only effective when ``rms_frames``
            is supplied). 0.005 ≈ -46 dBFS — drops the decay tail and
            room-noise floor on typical classical recordings without
            biting into pp passages. Raise to 0.01 (~-40 dBFS) for
            heavily compressed pop, lower to 0.002 (~-54 dBFS) if the
            recording's dynamic range demands it. Pair with the
            trailing-window gate below for fade-out detection.
        trailing_silence_window_s: Length in seconds of the trailing
            window used by the adaptive (envelope-relative) gate. The
            gate compares each window's RMS to the mean RMS over the
            preceding ``trailing_silence_window_s`` seconds — when the
            current window is much quieter than recent context, it's
            treated as silence regardless of the absolute floor. 3.0s
            is the sweet spot for typical pop / classical: long enough
            to average across a few measures, short enough to react to
            actual fade-outs within a few seconds. Set to 0.0 to
            disable adaptive gating (only the absolute floor remains).
        trailing_silence_ratio: Threshold for the adaptive gate as a
            fraction of trailing-window mean RMS. A window is gated
            when ``window_rms < trailing_avg * trailing_silence_ratio``.
            0.10 = "current window is more than 20 dB below the recent
            average" — catches fade-out tails that the absolute floor
            misses, without biting into legitimate quiet passages
            (which usually sit only 6–15 dB below their context).
            Lower values (0.05) are stricter; higher values (0.20)
            cut more aggressively. Set to 0.0 to disable the adaptive
            gate.
        median_kernel: Kernel size for running-median smoothing over
            raw chord labels. Must be odd and >= 1. Larger values
            produce smoother (but laggier) chord sequences. Default
            3 matches original hardcoded behavior.
        merge_same_root: When ``True`` (default), runs a post-processing
            pass that consolidates adjacent events sharing the same root
            but disagreeing on quality (e.g. ``Dm7→D7→Dm7→D7`` collapses
            to a single event). The matcher can ping-pong like this when
            sixteenth-note figuration emphasizes different chord tones at
            different moments within one harmonic area — musically those
            are the same chord, so we treat them as one.
        max_merge_duration_s: Upper cap on the merged event's duration.
            When merging would produce an event longer than this, the
            merge is skipped — preserves real chord changes across bar
            lines (a Dm7 in m9 followed by D7 in m10 is a genuine
            harmonic motion, not ping-pong, and they shouldn't fuse).
            Default 4.0s is roughly one measure at typical classical
            tempos. Tune up for slow ballads, down for fast pop.

    Returns:
        List of ChordEvent instances, sorted by start_time.
    """
    # Lazy import — same pattern as the rest of the audio subpackage. ChordEvent
    # lives in the adapter module which has its own lazy-import dance.
    from harmonic_analysis.integrations.audio_adapter import ChordEvent

    # Validate input shape
    if local_chroma_frames.ndim != 2 or local_chroma_frames.shape[0] != 12:
        return []

    T = local_chroma_frames.shape[1]
    if T == 0:
        return []

    # Convert window/hop sizes from seconds to chroma frames
    frames_per_sec = sr / hop_length
    win_frames = int(window_size_s * frames_per_sec)
    hop_frames = max(1, int(hop_size_s * frames_per_sec))

    # Use the *actual* frame-derived hop time for timestamps. Multiplying
    # by the requested hop_size_s instead drifts: int() truncates the
    # frame count, so 0.25s requested at fps=86.13 becomes 21 frames =
    # 0.244s real, and ~3s of error pile up over a 2-minute file. Use
    # this for *all* chord-event timestamps below.
    frame_hop_seconds = hop_frames / frames_per_sec

    if T < win_frames:
        return []

    # DD6 guard: don't bias toward a key we're not confident about
    effective_tonal_bias = tonal_bias
    if global_key.confidence < 0.5:
        effective_tonal_bias = 0.0

    diatonic_pcs = global_key.diatonic_pitch_classes

    # Pre-compute which templates are diatonic (ALL chord tones in the
    # global key's diatonic set). Root-only would call Cm "diatonic in C
    # major" because C is in the key — even though Eb isn't. Same trap
    # applies to Gm (Bb), Fm (Ab), Bm (F#). Bites both the bias mask
    # *and* the output flag, so we share the calculation.
    template_is_diatonic_bool = np.array(
        [CHORD_PC_SETS[label].issubset(diatonic_pcs) for label in _TEMPLATE_LABELS],
        dtype=bool,
    )
    template_is_diatonic = template_is_diatonic_bool.astype(np.float64)

    # Pre-compute each template's root pitch class for the bass-bonus
    # lookup. Indexed by template position in _TEMPLATE_LABELS. Computed
    # whether or not bass_chroma_frames is provided — cheap and avoids
    # branching the hot loop.
    template_root_pcs = np.array(
        [_root_pitch_class(label) for label in _TEMPLATE_LABELS],
        dtype=np.int64,
    )

    # Bass-aware estimation requires the time axes to match. Misaligned
    # shapes mean the caller mixed window indices that don't correspond —
    # we silently fall back to full-spectrum-only rather than crash, which
    # matches the fail-soft posture of the rest of the audio pipeline.
    use_bass = (
        bass_chroma_frames is not None
        and bass_chroma_frames.ndim == 2
        and bass_chroma_frames.shape == local_chroma_frames.shape
    )

    # RMS envelope is the proper silence gate. The chroma-norm fallback
    # below stays in place as a backstop, but it can't see -55 dBFS room
    # noise — the chroma_cqt inf-norm normalization paints decay tails
    # and HVAC hum as real chroma vectors. We check shape strictly: a
    # mismatched length means somebody mixed time axes and we'd rather
    # ignore the gate than mask the wrong windows.
    use_rms_gate = rms_frames is not None and rms_frames.shape == (T,)

    # Adaptive (envelope-relative) gate: pre-compute a trailing-window
    # mean RMS at every frame so the per-window check below is O(1).
    # Catches fade-outs that are quiet relative to recent context but
    # still above the absolute floor — a song mixed at -10 dBFS whose
    # fade-out drops to -35 dBFS won't trip the static silence threshold
    # (-46 dBFS), but it IS clearly quieter than recent music. Disabled
    # when use_rms_gate is off (no RMS to average) or when the trailing
    # window/ratio params are zeroed (caller opted out).
    use_trailing_gate = (
        use_rms_gate and trailing_silence_window_s > 0 and trailing_silence_ratio > 0
    )
    trailing_rms_arr: Optional[np.ndarray] = None
    if use_trailing_gate:
        assert rms_frames is not None  # mypy hint
        trailing_rms_arr = _trailing_mean(
            rms_frames, int(trailing_silence_window_s * frames_per_sec)
        )

    # --- Sliding window similarity ---
    num_windows = 1 + (T - win_frames) // hop_frames
    raw_labels: List[int] = []  # index into _TEMPLATE_LABELS
    raw_confidences: List[float] = []
    # Track the actual start time of each kept window. After silence
    # skipping, index into raw_labels no longer maps to time via simple
    # arithmetic — this parallel list is the source of truth for timestamps.
    window_start_times: List[float] = []

    for w in range(num_windows):
        start = w * hop_frames
        end = start + win_frames
        window_chroma = local_chroma_frames[:, start:end]

        # Average across the time axis → 12-bin vector
        avg = window_chroma.mean(axis=1)

        # Record the timestamp BEFORE any skip decision — we need it
        # regardless of whether the window survives the norm check.
        # Use frame-derived seconds (frame_hop_seconds) not the requested
        # hop_size_s, otherwise timestamps drift past the audio end.
        w_time = w * frame_hop_seconds

        # RMS gate first — cheaper than norm + tells us about audio
        # energy, not about whatever shape librosa's normalization
        # squeezed the chroma into. Two thresholds:
        #   1. Absolute floor (rms_silence_threshold) — catches true
        #      silence and noise floor.
        #   2. Adaptive (envelope-relative) — current window must be
        #      at least trailing_silence_ratio of the trailing average,
        #      otherwise the chord matcher is averaging across a fade
        #      where chroma_cqt produces meaningless output.
        if use_rms_gate:
            assert rms_frames is not None  # mypy hint; use_rms_gate implies this
            window_rms = float(rms_frames[start:end].mean())
            if window_rms < rms_silence_threshold:
                continue
            if use_trailing_gate:
                assert trailing_rms_arr is not None  # mypy hint
                # Reference at the *start* of the window — the trailing
                # average leading INTO the current window, not including
                # the current window's own (possibly fading) energy.
                ref_idx = max(0, start - 1)
                trailing_avg = float(trailing_rms_arr[ref_idx])
                if (
                    trailing_avg > 0
                    and window_rms < trailing_avg * trailing_silence_ratio
                ):
                    continue

        # L2-normalize. If the window is silent (norm below threshold),
        # skip it entirely — no point asking "which chord is this silence?"
        norm = np.linalg.norm(avg)
        if norm < min_chroma_norm:
            continue
        avg = avg / norm

        # Cosine similarity = dot product (both unit-norm).
        similarities = _TEMPLATE_MATRIX @ avg

        # Tonal bias: bump diatonic templates
        if effective_tonal_bias > 0:
            similarities = similarities + effective_tonal_bias * template_is_diatonic

        # Bass-aware bonus: identify the dominant bass pitch class for
        # this window and bump templates whose root matches. Confidence-
        # gated so silent / flat-bass windows don't push noise into the
        # match. Cheaper to compute peakiness than entropy and good
        # enough for the "is there a clear bass note here?" question.
        if use_bass and bass_bonus > 0:
            assert bass_chroma_frames is not None  # mypy hint; use_bass implies this
            bass_window = bass_chroma_frames[:, start:end]
            bass_avg = bass_window.mean(axis=1)
            bass_norm = np.linalg.norm(bass_avg)
            if bass_norm > 0:
                bass_avg = bass_avg / bass_norm
                bass_max = float(bass_avg.max())
                bass_mean = float(bass_avg.mean())
                # Peakiness: how much the dominant PC sticks out above the
                # mean. Range roughly [0, 1]. A pure single-note bass hits
                # ~0.95; a triad in the bass register sits around 0.4-0.6;
                # a flat (silent or noisy) window stays under 0.2.
                bass_confidence = (
                    (bass_max - bass_mean) / (bass_max + 1e-9) if bass_max > 0 else 0.0
                )
                if bass_confidence >= bass_confidence_threshold:
                    bass_pc = int(bass_avg.argmax())
                    root_match_mask = (template_root_pcs == bass_pc).astype(np.float64)
                    similarities = similarities + (
                        bass_bonus * bass_confidence * root_match_mask
                    )

        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        # Clip confidence to [0, 1]
        best_score = max(0.0, min(1.0, best_score))

        raw_labels.append(best_idx)
        raw_confidences.append(best_score)
        window_start_times.append(w_time)

    if not raw_labels:
        return []

    # --- Running-median smoothing ---
    # Encode labels as integers (already done), pad edges with reflect,
    # apply median, decode back. Pure numpy, no scipy.
    pad_size = median_kernel // 2
    labels_arr = np.array(raw_labels, dtype=np.float64)
    padded = np.pad(labels_arr, pad_size, mode="reflect")
    smoothed = np.empty(len(raw_labels), dtype=np.float64)
    for i in range(len(raw_labels)):
        smoothed[i] = np.median(padded[i : i + median_kernel])
    smoothed_labels = smoothed.astype(int).tolist()

    # --- Consolidate consecutive identical labels ---
    # After silence-skipping, window indices don't map linearly to time
    # anymore. window_start_times is the authoritative time source.
    events: list = []
    run_start_time = window_start_times[0]
    run_label = smoothed_labels[0]
    run_confidences: List[float] = [raw_confidences[0]]

    for i in range(1, len(smoothed_labels)):
        if smoothed_labels[i] == run_label:
            run_confidences.append(raw_confidences[i])
        else:
            # Emit the completed run
            label_str = _TEMPLATE_LABELS[run_label]
            events.append(
                ChordEvent(
                    start_time=run_start_time,
                    end_time=window_start_times[i],
                    chord_label=label_str,
                    confidence=float(np.mean(run_confidences)),
                    is_diatonic=bool(template_is_diatonic_bool[run_label]),
                )
            )
            run_start_time = window_start_times[i]
            run_label = smoothed_labels[i]
            run_confidences = [raw_confidences[i]]

    # Emit the final run. End time extends one hop beyond the last window
    # start — same semantics as the old index-based calculation, but using
    # frame-derived seconds so it doesn't shoot past the audio end.
    label_str = _TEMPLATE_LABELS[run_label]
    events.append(
        ChordEvent(
            start_time=run_start_time,
            end_time=window_start_times[-1] + frame_hop_seconds,
            chord_label=label_str,
            confidence=float(np.mean(run_confidences)),
            is_diatonic=bool(template_is_diatonic_bool[run_label]),
        )
    )

    # Optional post-pass: merge same-root ping-pongs into single events.
    # Done after consolidation (rather than fused into the median smoother)
    # so the merge sees actual durations and confidences, not raw frame
    # counts — the longer event of a pair gets to keep its quality.
    if merge_same_root:
        events = _merge_same_root_events(
            events, max_merge_duration_s=max_merge_duration_s
        )

    return events


def _merge_same_root_events(
    events: list,
    *,
    max_merge_duration_s: float = 4.0,
) -> list:
    """Collapse adjacent same-root chord events into one.

    The chord matcher can flicker between qualities of the same root
    (e.g. ``Dm7 → D7 → Dm7 → D7``) when figuration walks through
    different chord-tone subsets within one harmonic area. Each window
    sees a different snapshot of the same underlying chord and votes
    accordingly. Median smoothing helps for runs of width 1, but a
    longer ping-pong slips through.

    This pass walks the consolidated event list once and merges
    neighbors that share a root. The longer of the two contributes its
    quality (and is_diatonic flag) to the merged event; ties go to the
    higher-confidence side. Confidences are duration-weighted averaged.

    Pure post-processing — doesn't touch the matcher's intermediate
    state, so disabling via ``merge_same_root=False`` recovers the old
    behavior bit-identically.
    """
    if len(events) < 2:
        return list(events)

    from harmonic_analysis.integrations.audio_adapter import ChordEvent

    merged: list = [events[0]]
    for ev in events[1:]:
        prev = merged[-1]
        try:
            prev_root = _root_pitch_class(prev.chord_label)
            curr_root = _root_pitch_class(ev.chord_label)
        except ValueError:
            # Garbage label slipped through — don't merge, keep both.
            merged.append(ev)
            continue

        if prev_root != curr_root:
            merged.append(ev)
            continue

        prev_dur = prev.end_time - prev.start_time
        curr_dur = ev.end_time - ev.start_time

        # Skip the merge when the merged event would exceed the cap.
        # Real chord changes across bar lines (e.g., Dm7 in m9 → D7
        # in m10) shouldn't fuse just because they share a root.
        # *Exception*: if the labels are identical, this is just
        # continuing the same chord (likely after an earlier same-root
        # merge relabeled neighbors) — never apply the cap to those.
        same_label = prev.chord_label == ev.chord_label
        if not same_label and (prev_dur + curr_dur) > max_merge_duration_s:
            merged.append(ev)
            continue
        # Pick the dominant interpretation: longer wins, ties broken by
        # confidence. This preserves the harmonic intent of the area
        # rather than letting whichever event happened to come last
        # define the merged label.
        prev_wins = prev_dur > curr_dur or (
            prev_dur == curr_dur and prev.confidence >= ev.confidence
        )
        winning_label = prev.chord_label if prev_wins else ev.chord_label
        winning_diatonic = prev.is_diatonic if prev_wins else ev.is_diatonic

        total_dur = prev_dur + curr_dur
        if total_dur > 0:
            avg_conf = (
                prev.confidence * prev_dur + ev.confidence * curr_dur
            ) / total_dur
        else:
            avg_conf = max(prev.confidence, ev.confidence)

        merged[-1] = ChordEvent(
            start_time=prev.start_time,
            end_time=ev.end_time,
            chord_label=winning_label,
            confidence=avg_conf,
            is_diatonic=winning_diatonic,
        )

    return merged
