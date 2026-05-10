import pytest

from harmonic_analysis.core.pattern_engine import TokenConverter


def test_minor_andalusian_spelling():
    # Convention B (scope: minor_roman_label_polish): minor-key flatted
    # degrees ♭III / ♭VI / ♭VII all use Unicode ♭. The Andalusian cadence
    # i-♭VII-♭VI-V is the canonical demonstration — both the subtonic and
    # the ♭6 chord get explicit flat markers, no more mixed-convention
    # 'bVII / VI' spelling.
    tc = TokenConverter()
    key = "A minor"
    seq = ["Am", "G", "F", "E"]
    romans = tc._generate_roman_numerals(seq, key)
    romans = tc._normalize_minor_subtonic(seq, romans, key)
    assert romans == ["i", "♭VII", "♭VI", "V"], romans


def test_backdoor_preference_in_major():
    tc = TokenConverter()
    key = "C major"
    seq = ["Fm7", "Bb7", "Cmaj7"]
    romans = tc._generate_roman_numerals(seq, key)
    romans = tc._normalize_minor_subtonic(seq, romans, key)
    romans = tc._prefer_backdoor_bVII(seq, romans, key, mode="major")
    assert romans == ["iv7", "bVII7", "Imaj7"], romans


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
