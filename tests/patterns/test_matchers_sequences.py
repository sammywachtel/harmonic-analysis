"""
Tests for sequence matchers in the pattern engine.

Tests the core sequence matching logic for roman numerals, chord symbols,
and melodic intervals with windowing and constraint handling.
"""


from harmonic_analysis.core.pattern_engine.pattern_engine import (
    AnalysisContext,
    PatternEngine,
)


class TestSequenceMatchers:
    """Test sequence matching functionality."""

    def test_exact_roman_sequence_match(self, sample_context):
        """Test exact matching of roman numeral sequences."""
        engine = PatternEngine()

        # Create pattern that matches V-I
        pattern = {
            "id": "test.cadence",
            "name": "Test Cadence",
            "scope": ["harmonic"],
            "track": ["functional"],
            "matchers": {"roman_seq": ["V", "I"]},
            "evidence": {"weight": 0.9},
        }

        # Should find match at positions 2-4 (G-C = V-I)
        matches = engine._find_pattern_matches(pattern, sample_context)
        assert len(matches) == 1
        assert matches[0] == (2, 4)

    def test_exact_chord_sequence_match(self, sample_context):
        """Test exact matching of chord symbol sequences."""
        engine = PatternEngine()

        pattern = {
            "id": "test.progression",
            "name": "Test Progression",
            "scope": ["harmonic"],
            "track": ["functional"],
            "matchers": {"chord_seq": ["C", "F"]},
            "evidence": {"weight": 0.8},
        }

        # Should find match at positions 0-2 (C-F)
        matches = engine._find_pattern_matches(pattern, sample_context)
        assert len(matches) == 1
        assert matches[0] == (0, 2)

    def test_multi_occurrence_matching(self):
        """Test finding multiple occurrences of the same pattern."""
        engine = PatternEngine()
        context = AnalysisContext(
            key="C major",
            chords=["C", "F", "C", "F", "C"],
            roman_numerals=["I", "IV", "I", "IV", "I"],
            melody=[],
            scales=[],
            metadata={},
        )

        pattern = {
            "id": "test.repeat",
            "name": "Test Repeat",
            "scope": ["harmonic"],
            "track": ["functional"],
            "matchers": {"roman_seq": ["I", "IV"]},
            "evidence": {"weight": 0.7},
        }

        matches = engine._find_pattern_matches(pattern, context)
        assert len(matches) == 2
        assert (0, 2) in matches  # First I-IV
        assert (2, 4) in matches  # Second I-IV

    def test_no_match_when_pattern_not_found(self, sample_context):
        """Test that non-existent patterns return no matches."""
        engine = PatternEngine()

        pattern = {
            "id": "test.nonexistent",
            "name": "Test Non-existent",
            "scope": ["harmonic"],
            "track": ["functional"],
            "matchers": {"roman_seq": ["vi", "ii"]},  # Not in sample context
            "evidence": {"weight": 0.5},
        }

        matches = engine._find_pattern_matches(pattern, sample_context)
        assert len(matches) == 0

    def test_partial_match_not_found(self, sample_context):
        """Test that partial matches are not returned."""
        engine = PatternEngine()

        pattern = {
            "id": "test.partial",
            "name": "Test Partial",
            "scope": ["harmonic"],
            "track": ["functional"],
            "matchers": {"roman_seq": ["V", "I", "vi"]},  # Third element not present
            "evidence": {"weight": 0.6},
        }

        matches = engine._find_pattern_matches(pattern, sample_context)
        assert len(matches) == 0

    def test_case_sensitive_matching(self):
        """Test that matching is case-sensitive for roman numerals."""
        engine = PatternEngine()
        context = AnalysisContext(
            key="A minor",
            chords=["Am", "F", "G", "Am"],
            roman_numerals=["i", "VI", "VII", "i"],
            melody=[],
            scales=[],
            metadata={},
        )

        # Lowercase 'i' should not match uppercase 'I'
        pattern = {
            "id": "test.case",
            "name": "Test Case",
            "scope": ["harmonic"],
            "track": ["modal"],
            "matchers": {"roman_seq": ["I", "VI"]},
            "evidence": {"weight": 0.5},
        }

        matches = engine._find_pattern_matches(pattern, context)
        assert len(matches) == 0

        # But lowercase 'i' should match lowercase 'i'
        pattern["matchers"]["roman_seq"] = ["i", "VI"]
        matches = engine._find_pattern_matches(pattern, context)
        assert len(matches) == 1

    def test_regex_pattern_matching(self):
        """Test regex patterns in sequence matching."""
        engine = PatternEngine()
        context = AnalysisContext(
            key="C major",
            chords=["C", "Am", "F", "G"],
            roman_numerals=["I", "vi", "IV", "V"],
            melody=[],
            scales=[],
            metadata={},
        )

        # Match any secondary dominant (V/x pattern)
        pattern = {
            "id": "test.regex",
            "name": "Test Regex",
            "scope": ["harmonic"],
            "track": ["chromatic"],
            "matchers": {
                "roman_seq": ["V/.*", ".*"]
            },  # V/anything followed by anything
            "evidence": {"weight": 0.8},
        }

        # No V/x in this progression, should return no matches
        matches = engine._find_pattern_matches(pattern, context)
        assert len(matches) == 0

        # Add a secondary dominant
        context.roman_numerals[1] = "V/vi"
        context.chords[1] = "E"

        matches = engine._find_pattern_matches(pattern, context)
        assert len(matches) == 1
        assert matches[0] == (1, 3)  # V/vi to F

    def test_empty_sequence_handling(self):
        """Test handling of empty sequences."""
        engine = PatternEngine()
        context = AnalysisContext(
            key="C major",
            chords=[],
            roman_numerals=[],
            melody=[],
            scales=[],
            metadata={},
        )

        pattern = {
            "id": "test.empty",
            "name": "Test Empty",
            "scope": ["harmonic"],
            "track": ["functional"],
            "matchers": {"roman_seq": ["I", "V"]},
            "evidence": {"weight": 0.5},
        }

        matches = engine._find_pattern_matches(pattern, context)
        assert len(matches) == 0

    def test_single_element_pattern(self, sample_context):
        """Test matching single-element patterns."""
        engine = PatternEngine()

        pattern = {
            "id": "test.single",
            "name": "Test Single",
            "scope": ["harmonic"],
            "track": ["functional"],
            "matchers": {"roman_seq": ["I"]},
            "evidence": {"weight": 0.3},
        }

        matches = engine._find_pattern_matches(pattern, sample_context)
        assert len(matches) == 2  # Two 'I' chords at positions 0 and 3
        assert (0, 1) in matches
        assert (3, 4) in matches

    def test_overlapping_matches_allowed_by_default(self):
        """Test that overlapping matches are found by default."""
        engine = PatternEngine()
        context = AnalysisContext(
            key="C major",
            chords=["C", "F", "G", "C"],
            roman_numerals=["I", "IV", "V", "I"],
            melody=[],
            scales=[],
            metadata={},
        )

        pattern = {
            "id": "test.overlap",
            "name": "Test Overlap",
            "scope": ["harmonic"],
            "track": ["functional"],
            "matchers": {"roman_seq": ["IV", "V"]},
            "evidence": {"weight": 0.7},
        }

        matches = engine._find_pattern_matches(pattern, context)
        assert len(matches) == 1
        assert matches[0] == (1, 3)  # F-G progression

    def test_pattern_longer_than_context(self):
        """Test handling when pattern is longer than available context."""
        engine = PatternEngine()
        context = AnalysisContext(
            key="C major",
            chords=["C", "F"],
            roman_numerals=["I", "IV"],
            melody=[],
            scales=[],
            metadata={},
        )

        pattern = {
            "id": "test.long",
            "name": "Test Long",
            "scope": ["harmonic"],
            "track": ["functional"],
            "matchers": {"roman_seq": ["I", "IV", "V", "I"]},  # Longer than context
            "evidence": {"weight": 0.8},
        }

        matches = engine._find_pattern_matches(pattern, context)
        assert len(matches) == 0  # No matches possible


class TestMatcherConstraints:
    """Test constraint handling in pattern matching."""

    def test_window_length_constraint(self, sample_context):
        """Test window length constraints."""
        engine = PatternEngine()

        # Pattern with explicit window length
        pattern = {
            "id": "test.window",
            "name": "Test Window",
            "scope": ["harmonic"],
            "track": ["functional"],
            "matchers": {"roman_seq": ["V", "I"], "window": {"len": 2}},
            "evidence": {"weight": 0.9},
        }

        matches = engine._find_pattern_matches(pattern, sample_context)
        assert len(matches) == 1
        assert matches[0] == (2, 4)

    def test_pattern_applies_scope_checking(self, sample_context):
        """Test that patterns check scope requirements."""
        engine = PatternEngine()

        # Harmonic pattern should apply to harmonic context
        harmonic_pattern = {
            "scope": ["harmonic"],
            "track": ["functional"],
            "matchers": {"roman_seq": ["I"]},
            "evidence": {"weight": 0.5},
        }
        assert engine._pattern_applies(harmonic_pattern, sample_context) is True

        # Melodic pattern should not apply when no melody
        melodic_pattern = {
            "scope": ["melodic"],
            "track": ["functional"],
            "matchers": {"interval_seq": [2, -2]},
            "evidence": {"weight": 0.5},
        }
        assert engine._pattern_applies(melodic_pattern, sample_context) is False

        # Scale pattern should not apply when no scales
        scale_pattern = {
            "scope": ["scale"],
            "track": ["modal"],
            "matchers": {"mode": "dorian"},
            "evidence": {"weight": 0.5},
        }
        assert engine._pattern_applies(scale_pattern, sample_context) is False

    def test_multiple_scope_requirements(self):
        """Test patterns with multiple scope requirements."""
        engine = PatternEngine()

        # Context with harmony and melody
        context = AnalysisContext(
            key="C major",
            chords=["C", "F"],
            roman_numerals=["I", "IV"],
            melody=["C4", "F4"],
            scales=[],
            metadata={},
        )

        # Pattern requiring both harmonic and melodic scope
        multi_scope_pattern = {
            "scope": ["harmonic", "melodic"],
            "track": ["functional"],
            "matchers": {"roman_seq": ["I", "IV"]},
            "evidence": {"weight": 0.7},
        }
        assert engine._pattern_applies(multi_scope_pattern, context) is True

        # Same pattern should not apply when melody is missing
        context.melody = []
        assert engine._pattern_applies(multi_scope_pattern, context) is False
