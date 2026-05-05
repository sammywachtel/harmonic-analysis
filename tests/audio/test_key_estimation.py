"""Unit tests for ``find_best_key``.

Covers the AC5 scenarios (dominant key detection, ambiguous resolution,
zero-energy edge case) plus a one-time music21 cross-check that validates
the diatonic-pitch-class derivation against music21's scale machinery for
all 24 keys. The cross-check is skipped cleanly when music21 isn't present.
"""

from __future__ import annotations

import numpy as np
import pytest

from harmonic_analysis.audio._key_estimation import find_best_key
from harmonic_analysis.audio._profiles import KS_PROFILES, PITCH_CLASSES
from harmonic_analysis.audio._types import KeyInfo


def test_find_best_key_returns_keyinfo() -> None:
    # AC4 smoke: pure-numpy callable, returns the dataclass.
    chroma = np.array(KS_PROFILES["major"], dtype=float)
    result = find_best_key(chroma)
    assert isinstance(result, KeyInfo)
    assert isinstance(result.tonic, str)
    assert isinstance(result.mode, str)
    assert 0.0 <= result.confidence <= 1.0


def test_find_best_key_detects_c_major_dominant() -> None:
    # AC5 — dominant key detection. Feed the C-major K-S profile straight
    # in; correlation should peak at C major (mapped to C Ionian on output).
    chroma = np.array(KS_PROFILES["major"], dtype=float)
    result = find_best_key(chroma)
    assert result.tonic == "C"
    assert result.mode == "Ionian"
    assert result.confidence > 0.85  # near-perfect self-correlation


def test_find_best_key_detects_g_major_via_rolled_profile() -> None:
    # Roll the major profile to G (pc 7). K-S should return G Ionian.
    rolled = np.roll(np.array(KS_PROFILES["major"], dtype=float), 7)
    result = find_best_key(rolled)
    assert result.tonic == "G"
    assert result.mode == "Ionian"


def test_find_best_key_ambiguous_relative_keys() -> None:
    # AC5 — ambiguous key resolution. C major and A minor share all seven
    # diatonic pitch classes; a flat 50/50 blend of their profiles should
    # still resolve to one or the other (whichever wins the Pearson
    # correlation tiebreak), but with noticeably lower confidence than the
    # unambiguous case above.
    c_major = np.array(KS_PROFILES["major"], dtype=float)
    a_minor = np.roll(np.array(KS_PROFILES["minor"], dtype=float), 9)
    blended = (c_major + a_minor) / 2.0

    result = find_best_key(blended)
    # Both relative keys are valid answers — we just want a sensible one.
    valid_outcomes = {("C", "Ionian"), ("A", "Aeolian")}
    assert (result.tonic, result.mode) in valid_outcomes
    # Confidence should be lower than the unambiguous self-correlation case.
    unambiguous = find_best_key(c_major)
    assert result.confidence < unambiguous.confidence


def test_find_best_key_silent_chroma_returns_na() -> None:
    # AC5 — edge case: silent / zero-energy chroma. Must not raise, must
    # not return NaN, must return the documented sentinel.
    silent = np.zeros(12, dtype=float)
    result = find_best_key(silent)
    assert result.tonic == "N/A"
    assert result.mode == "N/A"
    assert result.key_signature == "N/A"
    assert result.confidence == 0.0
    # diatonic_pitch_classes for the N/A sentinel should be empty, not
    # raise from PITCH_CLASSES.index("N/A").
    assert result.diatonic_pitch_classes == frozenset()


def test_find_best_key_confidence_is_normalized() -> None:
    # Pearson lives in [-1, 1]; we map to [0, 1]. Sweep a few profiles and
    # check the bounds hold.
    for tonic_pc in range(12):
        for mode in ("major", "minor"):
            chroma = np.roll(np.array(KS_PROFILES[mode], dtype=float), tonic_pc)
            result = find_best_key(chroma)
            assert 0.0 <= result.confidence <= 1.0


def test_find_best_key_correctly_identifies_minor_mode() -> None:
    # Minor profile rolled to A (pc 9) → should detect A Aeolian.
    a_minor = np.roll(np.array(KS_PROFILES["minor"], dtype=float), 9)
    result = find_best_key(a_minor)
    assert result.tonic == "A"
    assert result.mode == "Aeolian"


def test_find_best_key_constant_chroma_yields_zero_confidence() -> None:
    # A nonzero but constant chroma vector passes the norm guard yet has
    # zero variance, which makes np.corrcoef return NaN. The second NaN
    # safety net should catch it and return 0.0 confidence instead of
    # propagating NaN downstream.
    constant_chroma = np.full(12, 0.5, dtype=float)
    result = find_best_key(constant_chroma)
    assert not np.isnan(result.confidence)
    assert result.confidence == 0.0


def test_keyinfo_with_unsupported_mode_returns_empty_diatonic_set() -> None:
    # Dorian, Phrygian, etc. aren't in K-S's two-mode universe. The type
    # gracefully degrades to an empty diatonic set rather than guessing —
    # WU3 extends the supported modes.
    ki = KeyInfo(
        tonic="D",
        mode="Dorian",
        key_signature="D dorian",
        confidence=0.5,
    )
    assert ki.diatonic_pitch_classes == frozenset()


def test_wrapper_delegates_to_template_correlation_approach() -> None:
    """AC-02: ``find_best_key`` and ``TemplateCorrelationApproach.detect()``
    must produce identical KeyInfo to 4 decimal places (bit-identity).

    The wrapper is meant to be a literal one-liner — any drift here means
    something is rounding twice or coercing in between.
    """
    from harmonic_analysis.audio._key_approaches.template_correlation import (
        TemplateCorrelationApproach,
    )
    from harmonic_analysis.audio._key_ensemble import KeyDetectionContext

    # Use the rolled-A K-S minor profile — exercises a non-zero pitch class
    # and the minor-mode branch.
    chroma = np.roll(np.array(KS_PROFILES["minor"], dtype=float), 9)

    wrapper_result = find_best_key(chroma)
    approach_result = (
        TemplateCorrelationApproach()
        .detect(KeyDetectionContext(chroma_1d=chroma))
        .ranked[0][0]
    )

    # Bit identity to 4 decimal places per AC-02.
    assert wrapper_result.tonic == approach_result.tonic
    assert wrapper_result.mode == approach_result.mode
    assert wrapper_result.key_signature == approach_result.key_signature
    # Confidence already rounds to 4 dp inside the approach, so equality
    # is the right check (not approx).
    assert wrapper_result.confidence == approach_result.confidence


def test_diatonic_pitch_classes_match_music21_for_all_keys() -> None:
    """One-time cross-check: every (tonic, mode) we support must produce a
    pitch-class set identical to music21's. Skips cleanly when music21 isn't
    installed — we don't want this to be a runtime dep.
    """
    music21 = pytest.importorskip("music21")  # noqa: F841

    from music21 import key as m21_key

    for tonic in PITCH_CLASSES:
        for mode_name in ("major", "minor"):
            # Build via find_best_key's output mapping (Ionian/Aeolian).
            # KeyInfo computes diatonic_pitch_classes in __post_init__.
            ki = KeyInfo(
                tonic=tonic,
                mode="Ionian" if mode_name == "major" else "Aeolian",
                key_signature=f"{tonic} {mode_name}",
                confidence=1.0,
            )
            # Music21 uses flats sometimes (Eb vs D#); pitchClass is what we
            # care about, so we compare integer sets only.
            m21_obj = m21_key.Key(tonic, mode_name)
            expected = frozenset(p.pitchClass for p in m21_obj.getScale().getPitches())
            assert ki.diatonic_pitch_classes == expected, (
                f"Mismatch for {tonic} {mode_name}: "
                f"got {sorted(ki.diatonic_pitch_classes)} vs music21 {sorted(expected)}"
            )
