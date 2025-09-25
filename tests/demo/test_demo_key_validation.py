import pytest

from demo.full_library_demo import (
    MISSING_MELODY_KEY_MSG,
    MISSING_SCALE_KEY_MSG,
    analyze_progression,
)


def test_analyze_progression_requires_key_for_scales():
    with pytest.raises(ValueError, match=MISSING_SCALE_KEY_MSG):
        analyze_progression(
            key=None,
            profile="classical",
            chords_text=None,
            romans_text=None,
            melody_text=None,
            scales_input="A,B,C,D,E,F,G",
        )


def test_analyze_progression_requires_key_for_melody():
    with pytest.raises(ValueError, match=MISSING_MELODY_KEY_MSG):
        analyze_progression(
            key=None,
            profile="classical",
            chords_text=None,
            romans_text=None,
            melody_text="C4, E4, G4",
            scales_input=None,
        )
