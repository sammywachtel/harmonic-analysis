"""
Test helpers for pattern DSL testing.

Provides utilities for building normalized contexts, creating test fixtures,
and validating pattern matching behavior across transpositions.
"""

import pytest
from typing import List, Dict, Any, Optional
from harmonic_analysis.core.pattern_engine.pattern_engine import AnalysisContext


@pytest.fixture
def sample_context():
    """Basic test context for pattern matching."""
    return AnalysisContext(
        key="C major",
        chords=["C", "F", "G", "C"],
        roman_numerals=["I", "IV", "V", "I"],
        melody=[],
        scales=[],
        metadata={}
    )


@pytest.fixture
def dorian_context():
    """Context for Dorian pattern testing."""
    return AnalysisContext(
        key="D dorian",
        chords=["Dm", "C", "Dm"],
        roman_numerals=["i", "♭VII", "i"],
        melody=[],
        scales=["D dorian"],
        metadata={"mode": "dorian"}
    )


def build_context(
    key: str,
    chords: List[str],
    roman_numerals: Optional[List[str]] = None,
    melody: Optional[List[Any]] = None,
    scales: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> AnalysisContext:
    """
    Build a normalized analysis context for testing.

    Args:
        key: Key signature (e.g., "C major", "A minor")
        chords: Chord symbols
        roman_numerals: Roman numeral analysis (optional)
        melody: Melodic content (optional)
        scales: Detected scales (optional)
        metadata: Additional context (optional)

    Returns:
        AnalysisContext ready for pattern matching
    """
    return AnalysisContext(
        key=key,
        chords=chords,
        roman_numerals=roman_numerals or [],
        melody=melody or [],
        scales=scales or [],
        metadata=metadata or {}
    )


def transpose_context(context: AnalysisContext, semitones: int) -> AnalysisContext:
    """
    Transpose context by given semitones for transposition invariance testing.

    This is a simplified transposition for testing - in reality this would
    use the full harmonic analysis transposition utilities.

    Args:
        context: Original context
        semitones: Semitones to transpose (+/-)

    Returns:
        Transposed context
    """
    # Simple key transposition mapping for testing
    major_keys = ["C", "D♭", "D", "E♭", "E", "F", "F#", "G", "A♭", "A", "B♭", "B"]
    minor_keys = ["A", "B♭", "B", "C", "C#", "D", "E♭", "E", "F", "F#", "G", "G#"]

    new_key = context.key
    if context.key and "major" in context.key.lower():
        # Extract root and transpose
        root = context.key.split()[0]
        if root in major_keys:
            idx = major_keys.index(root)
            new_root = major_keys[(idx + semitones) % 12]
            new_key = f"{new_root} major"
    elif context.key and "minor" in context.key.lower():
        root = context.key.split()[0]
        if root in minor_keys:
            idx = minor_keys.index(root)
            new_root = minor_keys[(idx + semitones) % 12]
            new_key = f"{new_root} minor"

    # For testing purposes, keep chord symbols and roman numerals unchanged
    # In real implementation, these would be transposed properly
    return AnalysisContext(
        key=new_key,
        chords=context.chords,  # Would transpose in real implementation
        roman_numerals=context.roman_numerals,  # Roman numerals are transposition-invariant
        melody=context.melody,
        scales=context.scales,  # Would transpose in real implementation
        metadata=context.metadata
    )


@pytest.fixture
def transposition_test_keys():
    """Standard keys for transposition testing."""
    return [
        ("C major", 0),
        ("D major", 2),
        ("E♭ major", 3),
        ("F# major", 6),
        ("A minor", 0),
        ("B minor", 2),
        ("F minor", -4)
    ]