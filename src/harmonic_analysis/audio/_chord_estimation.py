"""Tonal-context-aware chord template matching for streaming chroma frames.

Converts 2D chroma matrices (12, T) into timestamped ChordEvent instances
by sliding a window over the chroma, computing cosine similarity against a
bank of 48 chord templates (12 roots x {major, minor}), and consolidating
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

from typing import Dict, List

import numpy as np

from ._profiles import PITCH_CLASSES
from ._types import KeyInfo


def _build_chord_templates() -> Dict[str, np.ndarray]:
    """Build 48 unit-norm 12-bin chord templates (12 roots x {major, minor}).

    Each template is a 12-element vector with 1.0 at the pitch classes of the
    triad, then L2-normalized to unit norm. Cosine similarity between a
    unit-norm chroma frame and a unit-norm template reduces to a dot product,
    which is why we bother with the normalization.

    Naming convention:
        Major: "C", "C#", "D", ..., "B"
        Minor: "Cm", "C#m", "Dm", ..., "Bm"

    Returns:
        Dict mapping chord label to np.ndarray of shape (12,).
    """
    templates: Dict[str, np.ndarray] = {}

    # Major triad intervals: root, major third, perfect fifth
    major_intervals = [0, 4, 7]
    # Minor triad intervals: root, minor third, perfect fifth
    minor_intervals = [0, 3, 7]

    for root_idx, root_name in enumerate(PITCH_CLASSES):
        # Major template
        maj = np.zeros(12, dtype=np.float64)
        for interval in major_intervals:
            maj[(root_idx + interval) % 12] = 1.0
        maj /= np.linalg.norm(maj)
        templates[root_name] = maj

        # Minor template
        minor = np.zeros(12, dtype=np.float64)
        for interval in minor_intervals:
            minor[(root_idx + interval) % 12] = 1.0
        minor /= np.linalg.norm(minor)
        templates[f"{root_name}m"] = minor

    return templates


# Computed once at import time — 48 templates, immutable after this line.
CHORD_TEMPLATES = _build_chord_templates()

# Pre-compute the template matrix and ordered label list for vectorized
# similarity computation. Rows = templates, columns = pitch classes.
_TEMPLATE_LABELS: List[str] = list(CHORD_TEMPLATES.keys())
_TEMPLATE_MATRIX: np.ndarray = np.array(
    [CHORD_TEMPLATES[label] for label in _TEMPLATE_LABELS], dtype=np.float64
)


def _root_pitch_class(label: str) -> int:
    """Extract the root pitch class (0-11) from a chord label like 'Am' or 'C#'.

    Strips trailing 'm' (if present) and looks up the remaining name in
    PITCH_CLASSES. Raises ValueError if the root name is garbage — we'd
    rather crash than silently return nonsense.
    """
    root_name = label.rstrip("m") if label.endswith("m") else label
    # Edge case: "Cm" → strip "m" → "C", correct. "C#m" → strip "m" → "C#", correct.
    # But "Em" → strip "m" → "E", correct. No false positives in PITCH_CLASSES.
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
) -> list:
    """Estimate a chord progression from a 2D chroma matrix.

    Slides a window over the chroma frames, computes cosine similarity
    against 48 major/minor triad templates, applies optional tonal bias
    for diatonic chords, smooths with a running median, and consolidates
    consecutive identical labels into ChordEvent instances.

    Args:
        local_chroma_frames: Shape ``(12, T)`` chroma matrix from librosa.
        global_key: KeyInfo with ``diatonic_pitch_classes`` and ``confidence``.
        sr: Sample rate used during chroma extraction.
        hop_length: Hop length used during chroma extraction (librosa default: 512).
        window_size_s: Analysis window size in seconds.
        hop_size_s: Analysis hop size in seconds.
        tonal_bias: Bonus added to cosine similarity for diatonic chord templates.
            Set to 0.0 to disable. Auto-zeroed when ``global_key.confidence < 0.5``.

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

    if T < win_frames:
        return []

    # DD6 guard: don't bias toward a key we're not confident about
    effective_tonal_bias = tonal_bias
    if global_key.confidence < 0.5:
        effective_tonal_bias = 0.0

    diatonic_pcs = global_key.diatonic_pitch_classes

    # Pre-compute which templates are diatonic (root PC in global key's
    # diatonic set). This avoids repeating the lookup per window.
    template_is_diatonic = np.array(
        [_root_pitch_class(label) in diatonic_pcs for label in _TEMPLATE_LABELS],
        dtype=np.float64,
    )

    # --- Sliding window similarity ---
    num_windows = 1 + (T - win_frames) // hop_frames
    raw_labels: List[int] = []  # index into _TEMPLATE_LABELS
    raw_confidences: List[float] = []

    for w in range(num_windows):
        start = w * hop_frames
        end = start + win_frames
        window_chroma = local_chroma_frames[:, start:end]

        # Average across the time axis → 12-bin vector
        avg = window_chroma.mean(axis=1)

        # L2-normalize. If the window is silent (all zeros), norm is 0 —
        # produce a zero vector and let the template match be garbage.
        norm = np.linalg.norm(avg)
        if norm > 0:
            avg = avg / norm

        # Cosine similarity = dot product (both unit-norm).
        similarities = _TEMPLATE_MATRIX @ avg

        # Tonal bias: bump diatonic templates
        if effective_tonal_bias > 0:
            similarities = similarities + effective_tonal_bias * template_is_diatonic

        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        # Clip confidence to [0, 1]
        best_score = max(0.0, min(1.0, best_score))

        raw_labels.append(best_idx)
        raw_confidences.append(best_score)

    if not raw_labels:
        return []

    # --- Running-median smoothing (3-window kernel) ---
    # Encode labels as integers (already done), pad edges with reflect,
    # apply median, decode back. Pure numpy, no scipy.
    labels_arr = np.array(raw_labels, dtype=np.float64)
    # Reflect-pad: for kernel size 3, pad 1 on each side
    padded = np.pad(labels_arr, 1, mode="reflect")
    smoothed = np.empty(len(raw_labels), dtype=np.float64)
    for i in range(len(raw_labels)):
        smoothed[i] = np.median(padded[i : i + 3])
    smoothed_labels = smoothed.astype(int).tolist()

    # --- Consolidate consecutive identical labels ---
    events: list = []
    run_start = 0
    run_label = smoothed_labels[0]
    run_confidences: List[float] = [raw_confidences[0]]

    for i in range(1, len(smoothed_labels)):
        if smoothed_labels[i] == run_label:
            run_confidences.append(raw_confidences[i])
        else:
            # Emit the completed run
            label_str = _TEMPLATE_LABELS[run_label]
            root_pc = _root_pitch_class(label_str)
            events.append(
                ChordEvent(
                    start_time=run_start * hop_size_s,
                    end_time=i * hop_size_s,
                    chord_label=label_str,
                    confidence=float(np.mean(run_confidences)),
                    is_diatonic=root_pc in diatonic_pcs,
                )
            )
            run_start = i
            run_label = smoothed_labels[i]
            run_confidences = [raw_confidences[i]]

    # Emit the final run
    label_str = _TEMPLATE_LABELS[run_label]
    root_pc = _root_pitch_class(label_str)
    events.append(
        ChordEvent(
            start_time=run_start * hop_size_s,
            end_time=len(smoothed_labels) * hop_size_s,
            chord_label=label_str,
            confidence=float(np.mean(run_confidences)),
            is_diatonic=root_pc in diatonic_pcs,
        )
    )

    return events
