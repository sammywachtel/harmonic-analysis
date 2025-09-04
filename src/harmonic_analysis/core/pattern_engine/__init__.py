"""
Pattern Engine - JSON-driven harmonic pattern recognition system.

This module implements a hierarchical pattern detection system that identifies
common harmonic progressions, cadences, and functional patterns in music analysis.
"""

from .matcher import Token, Pattern, PatternLibrary, Matcher, load_library
from .token_converter import TokenConverter
from .glossary_service import GlossaryService

__all__ = [
    'Token',
    'Pattern',
    'PatternLibrary',
    'Matcher',
    'load_library',
    'TokenConverter',
    'GlossaryService'
]
