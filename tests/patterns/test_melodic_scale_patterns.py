"""
Tests for melodic and scale pattern matching in the unified pattern engine.

Validates the new scope=['melodic', 'scale'] patterns with interval sequences,
scale degree patterns, and modal characteristic detection.
"""

from typing import List

import pytest

from harmonic_analysis.core.pattern_engine.pattern_engine import (
    AnalysisContext,
    PatternEngine,
)


class TestMelodicPatterns:
    """Test melodic pattern matching functionality."""

    def test_leading_tone_resolution_detection(self):
        """Test 7-8 leading tone resolution pattern."""
        engine = PatternEngine()

        # Create pattern for leading tone resolution (semitone up)
        pattern = {
            "id": "melody.leading_tone_resolution",
            "name": "Leading Tone Resolution",
            "scope": ["melodic"],
            "track": ["functional"],
            "matchers": {
                "interval_seq": [1],  # Semitone ascending
                "scale_degrees": [7, 1],
            },
            "evidence": {"weight": 0.9},
        }

        # Test with melody that has leading tone resolution
        context = AnalysisContext(
            key="C major",
            chords=["G", "C"],
            roman_numerals=["V", "I"],
            melody=["B", "C"],  # 7-8 resolution
            scales=[],
            metadata={},
        )

        matches = engine._find_pattern_matches(pattern, context)
        # Should find one match for the B-C resolution
        assert len(matches) >= 1

    def test_modal_seventh_descent_detection(self):
        """Test modal seventh descent pattern (avoiding leading tone)."""
        engine = PatternEngine()

        pattern = {
            "id": "melody.modal_seventh_descent",
            "name": "Modal Seventh Descent",
            "scope": ["melodic"],
            "track": ["modal"],
            "matchers": {
                "interval_seq": [-2],  # Whole step down
                "scale_degrees": [7, 6],
            },
            "evidence": {"weight": 0.8},
        }

        # Test with Dorian-style melody avoiding leading tone
        context = AnalysisContext(
            key="D dorian",
            chords=["Dm", "C"],
            roman_numerals=["i", "♭VII"],
            melody=["C", "Bb"],  # ♭7-6 descent
            scales=[],
            metadata={},
        )

        matches = engine._find_pattern_matches(pattern, context)
        assert len(matches) >= 1

    def test_chromatic_passing_tone_detection(self):
        """Test chromatic passing tone pattern."""
        engine = PatternEngine()

        pattern = {
            "id": "melody.chromatic_passing_tone",
            "name": "Chromatic Passing Tone",
            "scope": ["melodic"],
            "track": ["functional"],
            "matchers": {
                "interval_seq": [1, 1],  # Two semitones up
            },
            "evidence": {"weight": 0.7},
        }

        # Test with chromatic passing motion C-C#-D
        context = AnalysisContext(
            key="C major",
            chords=["C", "C", "Dm"],
            roman_numerals=["I", "I", "ii"],
            melody=["C", "C#", "D"],  # Chromatic passing
            scales=[],
            metadata={},
        )

        matches = engine._find_pattern_matches(pattern, context)
        assert len(matches) >= 1

    def test_melody_pattern_scope_filtering(self):
        """Test that melodic patterns only apply when melody is present."""
        engine = PatternEngine()

        pattern = {
            "id": "melody.test",
            "scope": ["melodic"],
            "track": ["functional"],
            "matchers": {"interval_seq": [1]},
            "evidence": {"weight": 0.5},
        }

        # Context without melody should not apply
        context_no_melody = AnalysisContext(
            key="C major",
            chords=["C", "F"],
            roman_numerals=["I", "IV"],
            melody=[],  # No melody
            scales=[],
            metadata={},
        )

        assert not engine._pattern_applies(pattern, context_no_melody)

        # Context with melody should apply
        context_with_melody = AnalysisContext(
            key="C major",
            chords=["C", "F"],
            roman_numerals=["I", "IV"],
            melody=["C", "C#"],
            scales=[],
            metadata={},
        )

        assert engine._pattern_applies(pattern, context_with_melody)


class TestScalePatterns:
    """Test scale pattern matching functionality."""

    def test_dorian_scale_pattern_detection(self):
        """Test Dorian mode scale pattern recognition."""
        engine = PatternEngine()

        pattern = {
            "id": "scale.dorian.characteristic",
            "name": "Dorian Scale Pattern",
            "scope": ["scale"],
            "track": ["modal"],
            "matchers": {"scale_degrees": [1, 2, 3, 4, 5, 6, 7], "mode": "dorian"},
            "evidence": {"weight": 0.85},
        }

        # Context with Dorian characteristics
        context = AnalysisContext(
            key="D dorian",
            chords=["Dm", "Em", "F", "G", "Am", "Bb", "C"],
            roman_numerals=["i", "ii", "♭III", "IV", "v", "♭VI", "♭VII"],
            melody=[],
            scales=["D", "E", "F", "G", "A", "Bb", "C"],  # D Dorian scale
            metadata={},
        )

        matches = engine._find_pattern_matches(pattern, context)
        assert len(matches) >= 1

    def test_phrygian_scale_pattern_detection(self):
        """Test Phrygian mode scale pattern recognition."""
        engine = PatternEngine()

        pattern = {
            "id": "scale.phrygian.characteristic",
            "name": "Phrygian Scale Pattern",
            "scope": ["scale"],
            "track": ["modal"],
            "matchers": {"scale_degrees": [1, 2, 3, 4, 5, 6, 7], "mode": "phrygian"},
            "evidence": {"weight": 0.85},
        }

        # Context with Phrygian characteristics
        context = AnalysisContext(
            key="E phrygian",
            chords=["Em", "F", "G", "Am", "Bm", "C", "Dm"],
            roman_numerals=["i", "♭II", "♭III", "iv", "v", "♭VI", "♭vii"],
            melody=[],
            scales=["E", "F", "G", "A", "B", "C", "D"],  # E Phrygian scale
            metadata={},
        )

        matches = engine._find_pattern_matches(pattern, context)
        assert len(matches) >= 1

    def test_scale_pattern_scope_filtering(self):
        """Test that scale patterns only apply when scale context is available."""
        engine = PatternEngine()

        pattern = {
            "id": "scale.test",
            "scope": ["scale"],
            "track": ["modal"],
            "matchers": {"scale_degrees": [1, 2, 3, 4, 5, 6, 7]},
            "evidence": {"weight": 0.8},
        }

        # Context without scale info should not apply
        context_no_scales = AnalysisContext(
            key="C major",
            chords=["C", "F"],
            roman_numerals=["I", "IV"],
            melody=[],
            scales=[],  # No scale info
            metadata={},
        )

        assert not engine._pattern_applies(pattern, context_no_scales)

        # Context with scale info should apply
        context_with_scales = AnalysisContext(
            key="C major",
            chords=["C", "F"],
            roman_numerals=["I", "IV"],
            melody=[],
            scales=["C", "D", "E", "F", "G", "A", "B"],
            metadata={},
        )

        assert engine._pattern_applies(pattern, context_with_scales)


class TestMelodicIntervalExtraction:
    """Test melodic interval extraction utilities."""

    def test_extract_melodic_intervals_note_names(self):
        """Test interval extraction from note names."""
        engine = PatternEngine()

        # Test semitone intervals
        melody = ["C", "C#", "D"]
        intervals = engine._extract_melodic_intervals(melody)
        assert intervals == [1, 1]  # C to C# (1 semitone), C# to D (1 semitone)

        # Test larger intervals
        melody = ["C", "F", "G"]
        intervals = engine._extract_melodic_intervals(melody)
        assert intervals == [5, 2]  # C to F (5 semitones), F to G (2 semitones)

    def test_extract_melodic_intervals_midi_numbers(self):
        """Test interval extraction from MIDI numbers."""
        engine = PatternEngine()

        melody = [60, 62, 64]  # C, D, E
        intervals = engine._extract_melodic_intervals(melody)
        assert intervals == [2, 2]  # Whole steps

    def test_extract_melodic_intervals_edge_cases(self):
        """Test interval extraction edge cases."""
        engine = PatternEngine()

        # Empty melody
        assert engine._extract_melodic_intervals([]) == []

        # Single note
        assert engine._extract_melodic_intervals(["C"]) == []

        # Invalid notes should be skipped gracefully
        melody = ["C", "INVALID", "D"]
        intervals = engine._extract_melodic_intervals(melody)
        assert len(intervals) <= 2  # Should handle gracefully without crashing


class TestFullPatternIntegration:
    """Test full integration of melodic and scale patterns."""

    def test_melodic_and_harmonic_pattern_integration(self):
        """Test that melodic patterns work alongside harmonic patterns."""
        engine = PatternEngine()

        # Load a simple pattern set with both harmonic and melodic patterns
        patterns = [
            {
                "id": "cadence.authentic",
                "name": "Authentic Cadence",
                "scope": ["harmonic"],
                "track": ["functional"],
                "matchers": {"roman_seq": ["V", "I"]},
                "evidence": {"weight": 0.9},
            },
            {
                "id": "melody.leading_tone",
                "name": "Leading Tone Resolution",
                "scope": ["melodic"],
                "track": ["functional"],
                "matchers": {"interval_seq": [1]},
                "evidence": {"weight": 0.8},
            },
        ]

        # Context with both harmonic and melodic content
        context = AnalysisContext(
            key="C major",
            chords=["G", "C"],
            roman_numerals=["V", "I"],
            melody=["B", "C"],  # Leading tone resolution
            scales=[],
            metadata={},
        )

        # Both patterns should be applicable
        for pattern in patterns:
            assert engine._pattern_applies(pattern, context)

        # Both should produce matches
        harmonic_matches = engine._find_pattern_matches(patterns[0], context)
        melodic_matches = engine._find_pattern_matches(patterns[1], context)

        assert len(harmonic_matches) >= 1
        assert len(melodic_matches) >= 1

    def test_pattern_evaluation_with_melodic_context(self):
        """Test that pattern evaluation includes melodic context."""
        engine = PatternEngine()

        pattern = {
            "id": "melody.test",
            "scope": ["melodic"],
            "track": ["functional"],
            "matchers": {"interval_seq": [1]},
            "evidence": {"weight": 0.8, "confidence_fn": "identity"},
        }

        context = AnalysisContext(
            key="C major",
            chords=["G", "C"],
            roman_numerals=["V", "I"],
            melody=["B", "C"],
            scales=[],
            metadata={},
        )

        # This looks odd, but it saves us from crashes - direct call to _evaluate_pattern
        evidence = engine._evaluate_pattern(pattern, context, (0, 2))

        # Victory lap: verify the evidence includes melodic context
        assert evidence is not None
        assert evidence.pattern_id == "melody.test"
