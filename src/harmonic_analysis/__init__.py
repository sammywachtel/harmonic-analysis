"""Music Theory Analysis Library.

A comprehensive Python library for music theory analysis, providing sophisticated
algorithms for functional harmony, modal analysis, and chromatic harmony detection.

This is the main API layer providing essential functions for 90% of users.
For specialized functionality, see:
- harmonic_analysis.chromatic - Advanced chromatic analysis
- harmonic_analysis.midi - MIDI integration and chord parsing
- harmonic_analysis.scales - Complete scale matrix system
- harmonic_analysis.theory - Music theory utilities
- harmonic_analysis.algorithms - Advanced algorithmic analysis
"""

__version__ = "0.2.0rc3"

# =============================================================================
# LAYER 1: MAIN API - Essential Functions for 90% of Users
# =============================================================================

# Core analysis functions (4)
from .analysis import analyze_chord_progression, analyze_melody, analyze_scale

# Utility functions (4)
from .scale_melody_analysis import ScaleMelodyAnalysisResult, analyze_scale_melody

# Common result types (6)
from .services.multiple_interpretation_service import (
    AlternativeAnalysis,
    InterpretationAnalysis,
    MultipleInterpretationResult,
    PedagogicalLevel,
    analyze_progression_multiple,
)

# Configuration (2)
from .types import AnalysisOptions, AnalysisSuggestions, KeySuggestion
from .utils.analysis_helpers import describe_contour

# Constants (4)
from .utils.music_theory_constants import (
    ALL_MAJOR_KEYS,
    ALL_MINOR_KEYS,
    ALL_MODES,
    MODAL_CHARACTERISTICS,
    get_interval_name,
    get_modal_characteristics,
)

__all__ = [
    # Version
    "__version__",
    # Core analysis functions (4)
    "analyze_chord_progression",
    "analyze_melody",
    "analyze_scale",
    "analyze_progression_multiple",
    # Configuration (2)
    "AnalysisOptions",
    "PedagogicalLevel",
    # Common result types (6)
    "MultipleInterpretationResult",
    "InterpretationAnalysis",
    "AlternativeAnalysis",
    "ScaleMelodyAnalysisResult",
    "AnalysisSuggestions",
    "KeySuggestion",
    # Utility functions (4)
    "analyze_scale_melody",
    "get_interval_name",
    "get_modal_characteristics",
    "describe_contour",
    # Constants (4)
    "ALL_MAJOR_KEYS",
    "ALL_MINOR_KEYS",
    "ALL_MODES",
    "MODAL_CHARACTERISTICS",
]
