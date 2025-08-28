"""Chromatic Analysis Module.

Advanced chromatic harmony analysis including secondary dominants, borrowed chords,
chromatic mediants, and resolution patterns.

This module provides specialized chromatic analysis capabilities for advanced users
who need detailed analysis of complex harmonic techniques.
"""

# Re-export all chromatic analysis functionality
from .core.chromatic_analysis import (
    # Analysis functions
    analyze_chromatic_harmony,

    # Result types
    ChromaticAnalysisResult,

    # Data structures
    SecondaryDominant,
    BorrowedChord,
    ChromaticMediant,
    ResolutionPattern,

    # Enums
    ResolutionType,

    # Analyzer class (for power users)
    ChromaticAnalyzer,
)

# Also re-export modal analysis function for completeness
from .core.enhanced_modal_analyzer import analyze_modal_progression

__all__ = [
    # Analysis functions
    "analyze_chromatic_harmony",
    "analyze_modal_progression",

    # Result types
    "ChromaticAnalysisResult",

    # Data structures
    "SecondaryDominant",
    "BorrowedChord",
    "ChromaticMediant",
    "ResolutionPattern",

    # Enums
    "ResolutionType",

    # Analyzer class
    "ChromaticAnalyzer",
]
