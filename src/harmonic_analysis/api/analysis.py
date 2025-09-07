"""
Main analysis functions for harmonic analysis.

This module provides the primary user-facing API for chord progression analysis,
scale analysis, and melody analysis.
"""

import warnings
from typing import List, Optional

from ..core.scale_melody_analysis import ScaleMelodyAnalysisResult
from ..core.scale_melody_analysis import analyze_scale_melody as _analyze_scale_melody
from ..services.multiple_interpretation_service import (
    MultipleInterpretationResult,
)
from ..services.multiple_interpretation_service import (
    analyze_progression_multiple as _analyze_progression_multiple,
)
from ..analysis_types import AnalysisOptions


async def analyze_chord_progression(
    chords: List[str], options: Optional[AnalysisOptions] = None
) -> MultipleInterpretationResult:
    """
    Analyze a chord progression with multiple interpretations.

    .. deprecated:: 0.3.0
        Use :class:`harmonic_analysis.services.pattern_analysis_service.PatternAnalysisService`
        for advanced pattern-based analysis with better accuracy and detailed pattern recognition.

    This function is now deprecated in favor of the new Pattern Analysis Engine.
    The new system provides:
    - More accurate pattern recognition with evidence-based matching
    - Style-aware analysis (classical/jazz/pop profiles)
    - Detailed confidence scoring for each detected pattern
    - Event-based validation using bass motion and harmonic texture

    For new code, use::

        from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService
        service = PatternAnalysisService()
        result = await service.analyze_with_patterns(
            chord_symbols=chords,
            profile='classical',
            key_hint='C major'
        )

    Args:
        chords: List of chord symbols (e.g., ['C', 'Am', 'F', 'G'])
        options: Analysis options including parent key, confidence thresholds

    Returns:
        Multiple interpretation result with primary and alternative analyses

    Example:
        >>> result = await analyze_chord_progression(['C', 'Am', 'F', 'G'])
        >>> print(result.primary_analysis.analysis)
        'Functional progression: I - vi - IV - V'
    """
    warnings.warn(
        "analyze_chord_progression() is deprecated. Use PatternAnalysisService for "
        "advanced pattern-based analysis with better accuracy. See: "
        "https://github.com/sammywachtel/harmonic-analysis-py#new-pattern-matching-engine",
        DeprecationWarning,
        stacklevel=2
    )
    return await _analyze_progression_multiple(chords, options)


async def analyze_scale(
    notes: List[str], key: Optional[str] = None
) -> ScaleMelodyAnalysisResult:
    """
    Analyze a scale to identify modes and harmonic implications.

    Args:
        notes: List of note names (e.g., ['C', 'D', 'E', 'F', 'G', 'A', 'B'])
        key: Optional key context for better classification

    Returns:
        Scale analysis result with modal labels and contextual classification

    Example:
        >>> result = await analyze_scale(['D', 'E', 'F', 'G', 'A', 'B', 'C'])
        >>> print(result.modal_labels['D'])
        'D Dorian'
    """
    return _analyze_scale_melody(notes, key, melody=False)


async def analyze_melody(
    notes: List[str], key: Optional[str] = None
) -> ScaleMelodyAnalysisResult:
    """
    Analyze a melodic sequence with tonic inference.

    Args:
        notes: List of note names representing a melody
        key: Optional key context

    Returns:
        Melody analysis result with suggested tonic and confidence

    Example:
        >>> result = await analyze_melody(['G', 'A', 'B', 'C', 'D'])
        >>> print(f"Suggested tonic: {result.suggested_tonic}")
        'Suggested tonic: G'
    """
    return _analyze_scale_melody(notes, key, melody=True)
