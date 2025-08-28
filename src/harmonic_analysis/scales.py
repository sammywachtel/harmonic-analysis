"""Scale Matrix and Analysis Module.

Complete scale matrix system for music theory including all major, natural minor,
harmonic minor, and melodic minor scales with modal analysis.

This module provides comprehensive scale and melody analysis capabilities
including parent scale detection, modal label generation, and contextual classification.
"""

# Re-export all scale and melody analysis functionality
from .scale_melody_analysis import (
    # Main analysis function
    analyze_scale_melody,

    # Result types
    ScaleMelodyAnalysisResult,

    # Analyzer class (for power users)
    ScaleMelodyAnalyzer,
)

# Scale data and constants
from .utils.scales import (
    # Data structures
    ScaleData,

    # Scale systems
    MAJOR_SCALE_MODES,
    MELODIC_MINOR_MODES,
    HARMONIC_MINOR_MODES,
    ALL_SCALE_SYSTEMS,

    # Modal relationships
    MODAL_PARENT_KEYS,

    # Constants
    NOTE_TO_PITCH_CLASS,
    PITCH_CLASS_NAMES,

    # Utility functions
    get_parent_key,
    generate_scale_notes,
)

__all__ = [
    # Main analysis function
    "analyze_scale_melody",

    # Result types
    "ScaleMelodyAnalysisResult",

    # Analyzer class
    "ScaleMelodyAnalyzer",

    # Data structures
    "ScaleData",

    # Scale systems
    "MAJOR_SCALE_MODES",
    "MELODIC_MINOR_MODES",
    "HARMONIC_MINOR_MODES",
    "ALL_SCALE_SYSTEMS",

    # Modal relationships
    "MODAL_PARENT_KEYS",

    # Constants
    "NOTE_TO_PITCH_CLASS",
    "PITCH_CLASS_NAMES",

    # Utility functions
    "get_parent_key",
    "generate_scale_notes",
]
