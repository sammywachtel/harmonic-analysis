"""
Pattern Engine - JSON-driven harmonic pattern recognition system.

This module implements a hierarchical pattern detection system that identifies
common harmonic progressions, cadences, and functional patterns in music analysis.
"""

from .glossary_service import GlossaryService
from .matcher import Matcher, Pattern, PatternLibrary, Token, load_library
from .token_converter import TokenConverter

__all__ = [
    "Token",
    "Pattern",
    "PatternLibrary",
    "Matcher",
    "load_library",
    "TokenConverter",
    "GlossaryService",
]
