"""Sanity checks for the K-S profile constants.

Cheap tests, but they catch dumb mistakes — like editing PITCH_CLASSES and
silently breaking pitch-class arithmetic everywhere downstream.
"""

from __future__ import annotations

from harmonic_analysis.audio._profiles import KS_PROFILES, PITCH_CLASSES


def test_pitch_classes_length_is_twelve() -> None:
    assert len(PITCH_CLASSES) == 12


def test_pitch_classes_ordering_is_canonical() -> None:
    # Sharps only (C# not Db). Verbatim toolkit ordering — anything else
    # breaks PITCH_CLASSES.index(...) lookups in _cadence.py.
    expected = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    assert PITCH_CLASSES == expected


def test_ks_profiles_have_major_and_minor() -> None:
    assert set(KS_PROFILES.keys()) == {"major", "minor"}


def test_ks_profile_shapes_are_twelve_floats() -> None:
    for mode, profile in KS_PROFILES.items():
        assert len(profile) == 12, f"{mode} profile has wrong length"
        for value in profile:
            assert isinstance(value, float), f"{mode} contains non-float"


def test_ks_major_tonic_weight_is_dominant() -> None:
    # Krumhansl-Schmuckler's signature: tonic gets the heaviest weight in
    # each profile. If this ever fails, someone scrambled the constants.
    major = KS_PROFILES["major"]
    minor = KS_PROFILES["minor"]
    assert major[0] == max(major)
    assert minor[0] == max(minor)
