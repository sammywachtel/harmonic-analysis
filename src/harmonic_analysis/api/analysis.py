"""
Main analysis functions for harmonic analysis.

This module provides the primary user-facing API for scale analysis and melody analysis.
For chord progression analysis, use PatternAnalysisService.
"""

from typing import List, Optional

from ..core.scale_melody_analysis import ScaleMelodyAnalysisResult
from ..core.scale_melody_analysis import analyze_scale_melody as _analyze_scale_melody


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
