"""Scale Matrix and Analysis Module.

Complete scale matrix system for music theory including all major, natural minor,
harmonic minor, and melodic minor scales with modal analysis.

This module provides comprehensive scale and melody analysis capabilities
including parent scale detection, modal label generation, and contextual classification.
"""

# Re-export all scale and melody analysis functionality
# Main analysis function; Result types; Analyzer class (for power users)
from .scale_melody_analysis import (
    ScaleMelodyAnalysisResult,
    ScaleMelodyAnalyzer,
    analyze_scale_melody,
)

# Scale data and constants
# Data structures; Scale systems; Modal relationships; Constants; Utility functions
from .utils.scales import (
    ALL_SCALE_SYSTEMS,
    BLUES_SCALE_MODES,
    DOUBLE_HARMONIC_MAJOR_MODES,
    HARMONIC_MAJOR_MODES,
    HARMONIC_MINOR_MODES,
    MAJOR_PENTATONIC_MODES,
    MAJOR_SCALE_MODES,
    MELODIC_MINOR_MODES,
    MODAL_PARENT_KEYS,
    NOTE_TO_PITCH_CLASS,
    PITCH_CLASS_NAMES,
    ScaleData,
    generate_scale_notes,
    get_parent_key,
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
    "HARMONIC_MAJOR_MODES",
    "DOUBLE_HARMONIC_MAJOR_MODES",
    "MAJOR_PENTATONIC_MODES",
    "BLUES_SCALE_MODES",
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
