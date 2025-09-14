import pytest

from harmonic_analysis.core.pattern_engine import TokenConverter


def test_minor_andalusian_spelling():
    tc = TokenConverter()
    key = "A minor"
    seq = ["Am", "G", "F", "E"]
    romans = tc._generate_roman_numerals(seq, key)
    romans = tc._normalize_minor_subtonic(seq, romans, key)
    assert romans == ["i", "bVII", "VI", "V"], romans


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
