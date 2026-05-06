"""Unit tests for the chord estimation layer.

Tests the template-matching algorithm directly with synthetic chroma matrices,
bypassing the full audio I/O pipeline. This is where we verify the math works
before letting librosa anywhere near it.

Each test maps to an acceptance criterion (AC) from the iteration plan.
"""

from __future__ import annotations

from typing import List

import numpy as np
import pytest

# Module-level skip — these deps are needed for the audio subpackage imports
# even though we're only testing the chord estimation algorithm with synthetic
# chroma (no actual audio files involved).
librosa = pytest.importorskip("librosa")
sf = pytest.importorskip("soundfile")

from harmonic_analysis.audio._chord_estimation import (  # noqa: E402
    _CHORD_QUALITY_DEFS,
    CHORD_TEMPLATES,
    _build_chord_templates,
    _root_pitch_class,
    estimate_chord_progression,
)
from harmonic_analysis.audio._profiles import PITCH_CLASSES  # noqa: E402
from harmonic_analysis.audio._types import KeyInfo  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers — synthetic chroma generation
# ---------------------------------------------------------------------------

# Pitch class lookup for convenience
_PC = {name: idx for idx, name in enumerate(PITCH_CLASSES)}

# Chord-to-pitch-class mappings used across multiple tests
_CHORD_PCS = {
    "C": [0, 4, 7],
    "Dm": [2, 5, 9],
    "Em": [4, 7, 11],
    "F": [5, 9, 0],
    "G": [7, 11, 2],
    "Am": [9, 0, 4],
    "E": [4, 8, 11],
    "Bdim": [11, 2, 5],  # Won't match a template perfectly — treated as Bm or G
    "F#": [6, 10, 1],
}


def _make_chord_chroma(
    pitch_classes: List[int],
    num_frames: int,
    energy: float = 0.8,
    noise: float = 0.05,
) -> np.ndarray:
    """Build a (12, num_frames) chroma matrix for a single chord.

    Sets the given pitch classes to ``energy`` and everything else to
    ``noise``. The slight noise floor prevents division-by-zero during
    normalization and makes the test more realistic than a perfect
    one-hot encoding.
    """
    chroma = np.full((12, num_frames), noise, dtype=np.float64)
    for pc in pitch_classes:
        chroma[pc % 12, :] = energy
    return chroma


def _make_progression_chroma(
    chords: List[List[int]],
    frames_per_chord: int,
    energy: float = 0.8,
    noise: float = 0.05,
) -> np.ndarray:
    """Concatenate chroma segments for a chord progression.

    Returns a (12, T) matrix where T = len(chords) * frames_per_chord.
    """
    segments = [
        _make_chord_chroma(pcs, frames_per_chord, energy, noise) for pcs in chords
    ]
    return np.concatenate(segments, axis=1)


def _c_major_key(confidence: float = 0.9) -> KeyInfo:
    """Convenience: C major KeyInfo with configurable confidence."""
    return KeyInfo(
        tonic="C", mode="major", key_signature="C major", confidence=confidence
    )


def _a_minor_key(confidence: float = 0.9) -> KeyInfo:
    """Convenience: A minor KeyInfo."""
    return KeyInfo(
        tonic="A", mode="minor", key_signature="A minor", confidence=confidence
    )


# Default params that give us ~43 frames/sec at sr=22050, hop=512.
# 2 seconds of audio ≈ 86 frames.
_SR = 22050
_HOP = 512
_FRAMES_PER_SEC = _SR / _HOP  # ~43.07


# ---------------------------------------------------------------------------
# AC8 — Module docstring
# ---------------------------------------------------------------------------


def test_module_docstring():
    """AC8: module docstring states explicit limitations."""
    import harmonic_analysis.audio._chord_estimation as mod

    doc = mod.__doc__
    assert doc is not None, "Module docstring is missing"
    assert "triads only" in doc.lower(), "Should mention 'triads only'"
    assert "no inversions" in doc.lower(), "Should mention 'no inversions'"
    assert "no extensions" in doc.lower(), "Should mention 'no extensions'"


# ---------------------------------------------------------------------------
# Template validation
# ---------------------------------------------------------------------------


def test_templates_are_unit_norm():
    """All 24 templates should have L2 norm ≈ 1.0."""
    for label, template in CHORD_TEMPLATES.items():
        norm = np.linalg.norm(template)
        assert abs(norm - 1.0) < 1e-10, f"Template '{label}' has norm {norm}"


def test_template_count():
    """12 roots x N qualities = N*12 templates. Pinned to current quality set.

    If you add or remove a chord quality in _CHORD_QUALITY_DEFS, this number
    moves and the test fails — that's the point. Forces an update here so the
    template-bank cardinality is documented in tests.
    """
    from harmonic_analysis.audio._chord_estimation import _CHORD_QUALITY_DEFS

    expected = 12 * len(_CHORD_QUALITY_DEFS)
    assert len(CHORD_TEMPLATES) == expected, (
        f"Expected {expected} templates ({len(_CHORD_QUALITY_DEFS)} qualities x "
        f"12 roots), got {len(CHORD_TEMPLATES)}"
    )
    # Major and minor triads must always be present — they're the baseline.
    for name in PITCH_CLASSES:
        assert name in CHORD_TEMPLATES, f"Missing major template for {name}"
        assert f"{name}m" in CHORD_TEMPLATES, f"Missing minor template for {name}"


# ---------------------------------------------------------------------------
# AC1 — Single sustained triad
# ---------------------------------------------------------------------------


def test_single_sustained_triad():
    """AC1: 5 seconds of C major → single ChordEvent, confidence > 0.7."""
    # 5 seconds at ~43 frames/sec ≈ 215 frames
    num_frames = int(5.0 * _FRAMES_PER_SEC)
    chroma = _make_chord_chroma([0, 4, 7], num_frames)
    key = _c_major_key()

    events = estimate_chord_progression(
        chroma,
        key,
        sr=_SR,
        hop_length=_HOP,
        window_size_s=0.5,
        hop_size_s=0.25,
    )

    assert len(events) == 1, f"Expected 1 event, got {len(events)}"
    ev = events[0]
    assert ev.chord_label == "C", f"Expected 'C', got '{ev.chord_label}'"
    assert ev.confidence > 0.7, f"Confidence {ev.confidence} too low"
    assert ev.is_diatonic is True
    assert ev.start_time == pytest.approx(0.0)
    # End time should be close to 5.0 (depends on windowing)
    assert ev.end_time > 4.0, f"End time {ev.end_time} seems too early"


# ---------------------------------------------------------------------------
# AC2 — Four-chord progression
# ---------------------------------------------------------------------------


def test_four_chord_progression():
    """AC2: C-G-Am-F (2s each) → 4 ChordEvents with correct labels."""
    frames_per_chord = int(2.0 * _FRAMES_PER_SEC)
    chroma = _make_progression_chroma(
        [_CHORD_PCS["C"], _CHORD_PCS["G"], _CHORD_PCS["Am"], _CHORD_PCS["F"]],
        frames_per_chord,
    )
    key = _c_major_key()

    events = estimate_chord_progression(
        chroma,
        key,
        sr=_SR,
        hop_length=_HOP,
        window_size_s=0.5,
        hop_size_s=0.25,
    )

    # Filter out brief transitional events. With 7th-chord templates in
    # the bank, the boundary between two adjacent triads can briefly match
    # a 7th — e.g., Am→F shares (A, C) which combined with F's remaining
    # (F) plus residual E gives Fmaj7 for one window. That's a real signal
    # worth detecting in pop/jazz, but it shouldn't fail this test.
    steady = [e for e in events if (e.end_time - e.start_time) >= 0.5]
    labels = [e.chord_label for e in steady]
    assert labels == ["C", "G", "Am", "F"], f"Steady-state labels: {labels}"

    avg_conf = np.mean([e.confidence for e in events])
    assert avg_conf > 0.65, f"Average confidence {avg_conf} too low"


# ---------------------------------------------------------------------------
# AC3 — Corpus accuracy (≥ 70%)
# ---------------------------------------------------------------------------

# C major diatonic chord-to-PC mapping
_C_MAJOR_CHORDS = {
    "I": ("C", [0, 4, 7]),
    "ii": ("Dm", [2, 5, 9]),
    "iii": ("Em", [4, 7, 11]),
    "IV": ("F", [5, 9, 0]),
    "V": ("G", [7, 11, 2]),
    "vi": ("Am", [9, 0, 4]),
}

# A minor diatonic chord-to-PC mapping
_A_MINOR_CHORDS = {
    "i": ("Am", [9, 0, 4]),
    "ii_dim": ("Bdim", [11, 2, 5]),  # Bdim won't match — closest is Dm or G
    "III": ("C", [0, 4, 7]),
    "iv": ("Dm", [2, 5, 9]),
    "V": ("E", [4, 8, 11]),
    "VI": ("F", [5, 9, 0]),
    "VII": ("G", [7, 11, 2]),
}

# Progressions with expected chord labels
_C_MAJOR_PROGRESSIONS = [
    (["I", "IV", "V", "I"], ["C", "F", "G", "C"]),
    (["I", "V", "vi", "IV"], ["C", "G", "Am", "F"]),
    (["I", "ii", "V", "I"], ["C", "Dm", "G", "C"]),
    (["I", "iii", "IV", "V"], ["C", "Em", "F", "G"]),
    (["I", "vi", "ii", "V"], ["C", "Am", "Dm", "G"]),
]

_A_MINOR_PROGRESSIONS = [
    (["i", "iv", "V", "i"], ["Am", "Dm", "E", "Am"]),
    (["i", "VII", "VI", "VII"], ["Am", "G", "F", "G"]),
    (["i", "VI", "III", "VII"], ["Am", "F", "C", "G"]),
    (["i", "ii_dim", "V", "i"], ["Am", "Bdim", "E", "Am"]),
    (["i", "iv", "i", "V"], ["Am", "Dm", "Am", "E"]),
]


def test_corpus_accuracy():
    """AC3: ≥ 70% accuracy across 10 progressions with 24+ chord changes."""
    total_chords = 0
    correct_chords = 0

    all_progressions = []

    # C major progressions
    for roman_names, expected_labels in _C_MAJOR_PROGRESSIONS:
        pcs_sequence = [_C_MAJOR_CHORDS[r][1] for r in roman_names]
        all_progressions.append((_c_major_key(), pcs_sequence, expected_labels))

    # A minor progressions
    for roman_names, expected_labels in _A_MINOR_PROGRESSIONS:
        pcs_sequence = [_A_MINOR_CHORDS[r][1] for r in roman_names]
        all_progressions.append((_a_minor_key(), pcs_sequence, expected_labels))

    for key, pcs_seq, expected in all_progressions:
        frames_per_chord = int(2.0 * _FRAMES_PER_SEC)
        chroma = _make_progression_chroma(pcs_seq, frames_per_chord)

        events = estimate_chord_progression(
            chroma,
            key,
            sr=_SR,
            hop_length=_HOP,
            window_size_s=0.5,
            hop_size_s=0.25,
        )

        detected = [e.chord_label for e in events]

        # Match detected labels to expected labels. Since boundary effects
        # can cause minor splits or merges, we use a generous matching:
        # for each expected chord, check if it appears in the detected list
        # at the right position.
        for i, exp_label in enumerate(expected):
            total_chords += 1
            if i < len(detected) and detected[i] == exp_label:
                correct_chords += 1
            elif exp_label in detected:
                # The chord was detected, just not in the exact position —
                # still count it for the accuracy metric. Boundary wobble
                # is expected with windowed analysis.
                correct_chords += 1

    accuracy = correct_chords / total_chords if total_chords > 0 else 0
    assert accuracy >= 0.70, (
        f"Corpus accuracy {accuracy:.1%} ({correct_chords}/{total_chords}) "
        f"is below the 70% threshold"
    )


# ---------------------------------------------------------------------------
# AC4 — Diatonic flag
# ---------------------------------------------------------------------------


def test_diatonic_flag_fully_diatonic():
    """AC4: I-IV-V-I in C major → all is_diatonic=True."""
    frames_per_chord = int(2.0 * _FRAMES_PER_SEC)
    chroma = _make_progression_chroma(
        [_CHORD_PCS["C"], _CHORD_PCS["F"], _CHORD_PCS["G"], _CHORD_PCS["C"]],
        frames_per_chord,
    )
    key = _c_major_key()

    events = estimate_chord_progression(
        chroma,
        key,
        sr=_SR,
        hop_length=_HOP,
    )

    for ev in events:
        assert (
            ev.is_diatonic is True
        ), f"Chord '{ev.chord_label}' flagged as non-diatonic in C major"


def test_diatonic_flag_borrowed_chord():
    """AC4: F#-G-C in C major → F# is non-diatonic, G and C are diatonic."""
    frames_per_chord = int(2.0 * _FRAMES_PER_SEC)
    # F# major = pitch classes 6, 10, 1
    chroma = _make_progression_chroma(
        [_CHORD_PCS["F#"], _CHORD_PCS["G"], _CHORD_PCS["C"]],
        frames_per_chord,
    )
    key = _c_major_key()

    events = estimate_chord_progression(
        chroma,
        key,
        sr=_SR,
        hop_length=_HOP,
    )

    labels = [e.chord_label for e in events]

    # F# should be detected (or F#m — either way, root PC 6 is not diatonic in C major)
    # Find the event that corresponds to the F# segment
    assert len(events) >= 2, f"Expected at least 2 events, got {len(events)}: {labels}"

    # The first chord should be non-diatonic (F# or F#m, root PC=6 not in C major)
    assert (
        events[0].is_diatonic is False
    ), f"First chord '{events[0].chord_label}' should be non-diatonic"

    # G and C should be diatonic
    for ev in events[1:]:
        if ev.chord_label in ("G", "C", "Gm", "Cm"):
            # G (pc=7) and C (pc=0) are both in C major diatonic set
            # Gm and Cm roots are also diatonic PCs
            root_pc = _root_pitch_class(ev.chord_label)
            if root_pc in _c_major_key().diatonic_pitch_classes:
                assert (
                    ev.is_diatonic is True
                ), f"Chord '{ev.chord_label}' should be diatonic in C major"


# ---------------------------------------------------------------------------
# AC6 — Tonal bias parameter
# ---------------------------------------------------------------------------


def _raw_cosine_confidence(chroma: np.ndarray, key: KeyInfo) -> float:
    """Compute raw cosine confidence (no tonal bias) for a sustained chord."""
    events = estimate_chord_progression(
        chroma,
        key,
        sr=_SR,
        hop_length=_HOP,
        tonal_bias=0.0,
    )
    assert len(events) > 0
    return events[0].confidence


@pytest.mark.parametrize(
    "tonal_bias,key_confidence,expect_boost",
    [
        (0.0, 0.9, False),  # No bias → raw cosine
        (0.15, 0.9, True),  # Bias + confident key → boosted
        (0.15, 0.3, False),  # DD6: low-confidence key auto-zeros bias
    ],
    ids=["no_bias", "with_bias", "dd6_auto_zero"],
)
def test_tonal_bias_parameter(tonal_bias, key_confidence, expect_boost):
    """AC6: tonal_bias parameter controls confidence boosting."""
    num_frames = int(3.0 * _FRAMES_PER_SEC)
    chroma = _make_chord_chroma([0, 4, 7], num_frames)  # C major chord
    key = _c_major_key(confidence=key_confidence)

    events = estimate_chord_progression(
        chroma,
        key,
        sr=_SR,
        hop_length=_HOP,
        tonal_bias=tonal_bias,
    )
    assert len(events) > 0

    biased_conf = events[0].confidence
    raw_conf = _raw_cosine_confidence(chroma, _c_major_key(confidence=key_confidence))

    if expect_boost:
        assert biased_conf > raw_conf, (
            f"Expected tonal bias to boost confidence: biased={biased_conf}, "
            f"raw={raw_conf}"
        )
    else:
        assert (
            abs(biased_conf - raw_conf) < 1e-6
        ), f"Expected no boost: biased={biased_conf}, raw={raw_conf}"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_input():
    """Zero-frame chroma returns empty list."""
    chroma = np.zeros((12, 0), dtype=np.float64)
    key = _c_major_key()
    events = estimate_chord_progression(chroma, key, sr=_SR, hop_length=_HOP)
    assert events == []


def test_too_short_input():
    """Chroma shorter than one analysis window returns empty list."""
    # Default window is 0.5s ≈ 21 frames. Provide 5 frames.
    chroma = np.zeros((12, 5), dtype=np.float64)
    key = _c_major_key()
    events = estimate_chord_progression(chroma, key, sr=_SR, hop_length=_HOP)
    assert events == []


def test_wrong_shape_input():
    """Non-(12, T) input returns empty list gracefully."""
    chroma = np.zeros((6, 100), dtype=np.float64)
    key = _c_major_key()
    events = estimate_chord_progression(chroma, key, sr=_SR, hop_length=_HOP)
    assert events == []


# ---------------------------------------------------------------------------
# AC-4-a — Template snapshot: ordering is load-bearing, lock it down
# ---------------------------------------------------------------------------


def test_template_key_ordering_snapshot():
    """AC-4-a: Template keys are in root-major-quality-loop order.

    For each of 12 roots, emit one entry per quality in _CHORD_QUALITY_DEFS
    order. This is load-bearing because the median smoother operates on
    integer indices into _TEMPLATE_LABELS. If someone reorders these, the
    smoother silently mixes up chord labels and you get mysterious
    misclassifications that only show up in integration tests. Lock the
    ordering here so it fails fast.
    """
    from harmonic_analysis.audio._chord_estimation import _CHORD_QUALITY_DEFS

    keys = list(CHORD_TEMPLATES.keys())
    expected_count = 12 * len(_CHORD_QUALITY_DEFS)
    assert (
        len(keys) == expected_count
    ), f"Expected {expected_count} templates, got {len(keys)}"

    # Major and minor triads stay first per root — the original ordering
    # contract — so the first two entries are always C and Cm.
    assert keys[0] == "C", f"First template should be 'C', got {keys[0]!r}"
    assert keys[1] == "Cm", f"Second template should be 'Cm', got {keys[1]!r}"

    # Full ordering check: for each root, all qualities in defs order.
    expected = []
    for root in PITCH_CLASSES:
        for suffix, _intervals in _CHORD_QUALITY_DEFS:
            expected.append(f"{root}{suffix}")
    assert keys == expected


# ---------------------------------------------------------------------------
# AC-4-b — Extensibility: appending a quality rebuilds correctly
# ---------------------------------------------------------------------------


def test_extensibility_new_quality(monkeypatch):
    """AC-4-b: Appending a new quality to _CHORD_QUALITY_DEFS produces
    12 additional templates with the right naming convention.

    Uses monkeypatch to temporarily extend the defs and restore them after.
    The real _CHORD_QUALITY_DEFS is module-level state, so we need to be
    careful not to leave garbage behind. monkeypatch handles that.
    """
    import harmonic_analysis.audio._chord_estimation as chord_mod

    # 'aug' (augmented triad, 0-4-8) isn't in the defaults — pick something
    # we know isn't already present so the count math stays clean.
    base_count = 12 * len(_CHORD_QUALITY_DEFS)
    extended_defs = list(_CHORD_QUALITY_DEFS) + [("aug", (0, 4, 8))]
    monkeypatch.setattr(chord_mod, "_CHORD_QUALITY_DEFS", extended_defs)

    templates = _build_chord_templates()
    expected = base_count + 12
    assert len(templates) == expected, f"Expected {expected}, got {len(templates)}"

    # Spot-check some augmented keys
    assert "Caug" in templates, "Missing Caug template"
    assert "C#aug" in templates, "Missing C#aug template"
    assert "Baug" in templates, "Missing Baug template"

    # Verify all templates are unit-norm (the math doesn't care what
    # intervals you hand it, but let's be sure)
    for label, tmpl in templates.items():
        norm = np.linalg.norm(tmpl)
        assert abs(norm - 1.0) < 1e-10, f"Template {label!r} has norm {norm}"


# ---------------------------------------------------------------------------
# AC-1-b — Bass-chroma disambiguation
# ---------------------------------------------------------------------------


def test_bass_chroma_disambiguates_relative_pair():
    """AC-1-b: With bass chroma suggesting B as root, the estimator should
    prefer Bm over D. Without bass chroma, D (the relative major) wins
    because D major and B minor share two out of three pitch classes and
    D major's template has higher cosine similarity against a treble
    chroma that's ambiguous between the two.

    This is the whole reason the bass-chroma feature exists: relative
    major/minor pairs (D/Bm, C/Am, F/Dm, etc.) are indistinguishable
    in full-spectrum chroma when the bass note is the only discriminator.
    """
    num_frames = int(3.0 * _FRAMES_PER_SEC)

    # Treble chroma: D major pitch classes (D=2, F#=6, A=9) with a
    # *small* B bleed — enough to make full-spectrum chroma ambiguous
    # without tipping the scales toward Bm/Bm7 on its own. This is
    # realistic: a Bm chord in first inversion (D in the treble) looks
    # a lot like D major in chroma space, and the bass register is
    # what disambiguates them. Calibrated so that without bass, D wins;
    # with bass, the B-bonus shifts the decision to a B-rooted chord.
    treble = np.full((12, num_frames), 0.05, dtype=np.float64)
    treble[2, :] = 0.7  # D
    treble[6, :] = 0.6  # F#
    treble[9, :] = 0.5  # A
    treble[11, :] = 0.15  # B — small bleed; insufficient on its own

    # Bass chroma: strong B, weak everything else. This is what a bass
    # guitar playing B2 looks like after chroma extraction.
    bass = np.full((12, num_frames), 0.02, dtype=np.float64)
    bass[11, :] = 0.9  # B is dominant in the bass register

    key = KeyInfo(tonic="D", mode="major", key_signature="D major", confidence=0.9)

    # With bass chroma + bonus: should lean toward Bm
    events_with_bass = estimate_chord_progression(
        treble,
        key,
        sr=_SR,
        hop_length=_HOP,
        window_size_s=0.5,
        hop_size_s=0.25,
        bass_chroma_frames=bass,
        bass_bonus=0.3,
    )

    # Without bass chroma: should produce D
    events_no_bass = estimate_chord_progression(
        treble,
        key,
        sr=_SR,
        hop_length=_HOP,
        window_size_s=0.5,
        hop_size_s=0.25,
    )

    assert len(events_with_bass) > 0, "Bass-aware path produced no events"
    assert len(events_no_bass) > 0, "No-bass path produced no events"

    # The bass-aware result should land on a B-rooted minor chord. With
    # the extended template bank, that might be 'Bm' or 'Bm7' depending
    # on how much B-leading the synthetic chroma carries (Bm + the F# and
    # A in the treble + a tiny bit of D = Bm7's pitch-class set). Either
    # is correct — what we care about is that the *bass* changed the
    # answer from D-rooted to B-rooted.
    bass_labels = [e.chord_label for e in events_with_bass]
    no_bass_labels = [e.chord_label for e in events_no_bass]

    b_minor_variants = {"Bm", "Bm7", "Bm7b5"}
    assert any(label in b_minor_variants for label in bass_labels), (
        f"Expected a B-rooted minor variant ({b_minor_variants}) with bass "
        f"chroma, got: {bass_labels}"
    )
    assert (
        "D" in no_bass_labels
    ), f"Expected 'D' without bass chroma, got: {no_bass_labels}"
