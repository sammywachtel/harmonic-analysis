"""Music Theory Analysis Library.

A comprehensive Python library for music theory analysis, providing sophisticated
algorithms for functional harmony, modal analysis, and chromatic harmony detection.

🆕 Advanced Pattern Matching Engine
For chord progression analysis, choose between:

Legacy Service (stable):
    from harmonic_analysis import PatternAnalysisService

Next-Generation Unified Engine (recommended for new projects):
    from harmonic_analysis import UnifiedPatternService

User-Facing API:
This module exports only user-facing functionality. Internal components
(pattern engine internals, calibration, corpus mining) are not exposed.

Exported functionality:
- Analysis Services (PatternAnalysisService, UnifiedPatternService)
- Simple Analysis Functions (analyze_melody, analyze_scale)
- Music Theory Constants (MODAL_CHARACTERISTICS, ALL_KEYS, etc.)
- Character & Emotional Analysis (get_mode_emotional_profile, etc.)
- Musical Data Access (get_scale_notes, get_circle_of_fifths, etc.)
- Result Types (AnalysisEnvelope, AnalysisSummary, etc.)

Optional Features (separate imports):
- Educational Content: from harmonic_analysis.educational import EducationalService
- File Integration: from harmonic_analysis.integrations import Music21Adapter
"""

__version__ = "0.3.0"

# =============================================================================
# LAYER 1: MAIN API - Essential Functions for 90% of Users
# =============================================================================

# Configuration types
# Import common result types
from .analysis_types import (
    AnalysisOptions,
    AnalysisSuggestions,
    KeySuggestion,
    PedagogicalLevel,
)

# Import all user-facing APIs from the api package
# Core analysis functions
from .api.analysis import analyze_melody, analyze_scale

# Character and emotional analysis
from .api.character import (
    CharacterSuggestion,
    EmotionalProfile,
    ProgressionCharacter,
    analyze_progression_character,
    describe_emotional_contour,
    get_character_suggestions,
    get_mode_emotional_profile,
    get_modes_by_brightness,
)

# Musical data access
from .api.musical_data import (
    get_all_degree_to_mode_mappings,
    get_all_notes,
    get_all_scale_systems,
    get_circle_of_fifths,
    get_complete_musical_reference,
    get_degree_to_mode_mapping,
    get_interval_names,
    get_mode_popularity_ranking,
    get_mode_to_scale_family_mapping,
    get_note_to_pitch_class_mapping,
    get_parent_key_indices,
    get_parent_key_mapping,
    get_pitch_class_to_note_mapping,
    get_relative_major_minor_pairs,
    get_scale_notes,
    get_scale_reference_for_frontend,
    get_scale_system_info,
    get_scale_system_names,
    normalize_note_name,
    note_to_pitch_class,
    pitch_class_to_note,
    validate_musical_input,
)

# Import result types from core analysis
from .core.scale_melody_analysis import ScaleMelodyAnalysisResult

# Music theory constants
from .core.utils.music_theory_constants import (
    ALL_KEYS,
    ALL_MAJOR_KEYS,
    ALL_MINOR_KEYS,
    ALL_MODES,
    CANONICAL_KEY_MAP,
    INTERVAL_ABBREVIATIONS,
    MODAL_CHARACTERISTICS,
    SCALE_TO_CHORD_MAPPINGS,
    SEMITONE_TO_INTERVAL_NAME,
    ScaleDegree,
    canonicalize_key_signature,
    describe_step_pattern,
    get_characteristic_degrees,
    get_harmonic_implications,
    get_interval_name,
    get_modal_characteristics,
    get_scale_applications,
)

# Scale and pitch constants
from .core.utils.scales import (
    HARMONIC_MINOR_MODES,
    MAJOR_SCALE_MODES,
    MELODIC_MINOR_MODES,
    MODAL_PARENT_KEYS,
    NOTE_TO_PITCH_CLASS,
    PITCH_CLASS_NAMES,
)

# Import DTO types for pattern analysis
from .dto import (
    AnalysisEnvelope,
    AnalysisSummary,
    AnalysisType,
    ChromaticElementDTO,
    ChromaticSummaryDTO,
    PatternMatchDTO,
    SectionDTO,
)

# Import Pattern Analysis Services
from .services.pattern_analysis_service import PatternAnalysisService

# 🆕 Import Unified Pattern Service (Next Generation)
from .services.unified_pattern_service import UnifiedPatternService

# Utility functions
from .utils.analysis_helpers import describe_contour

# =============================================================================
# Optional: Audio analysis surface (requires the [audio] extra)
# =============================================================================
# Guarded re-export. The bare `import harmonic_analysis` must succeed even
# when librosa/soundfile aren't installed (AC3). We always try the import;
# on AudioImportError (deps missing), we fall back to lightweight stubs that
# raise on first use, so symbol names stay grep-able from the top level.
try:
    from .integrations.audio_adapter import (
        AudioAdapter,
        AudioAnalysisResult,
        AudioImportError,
        ChordEvent,
        analyze_audio,
        analyze_audio_async,
    )
except ImportError as _audio_exc:  # pragma: no cover — env-dependent path
    # The audio_adapter module itself imports cleanly; only construction
    # raises. So a real ImportError here means *something else* is wrong
    # (audio_adapter.py was deleted, or a syntactical breakage). Surface
    # actionable stubs anyway — never break the top-level import.
    from typing import Any as _Any

    class AudioImportError(ImportError):  # type: ignore[no-redef]
        """Stub raised when the [audio] extra isn't installed."""

        pass

    _AUDIO_ERR_MSG = (
        "The audio extra is required for audio analysis. "
        f"Install with: pip install harmonic-analysis[audio]. "
        f"(underlying error: {_audio_exc})"
    )

    def _audio_unavailable(*_args: _Any, **_kwargs: _Any) -> _Any:
        raise AudioImportError(_AUDIO_ERR_MSG)

    # Stubs that raise on first use. Type-ignore on the assignments
    # because we're rebinding names that mypy tracked from the try-branch.
    AudioAdapter = _audio_unavailable  # type: ignore[assignment,misc]
    AudioAnalysisResult = _audio_unavailable  # type: ignore[assignment,misc]
    ChordEvent = _audio_unavailable  # type: ignore[assignment,misc]
    analyze_audio = _audio_unavailable
    analyze_audio_async = _audio_unavailable


__all__ = [
    # Version
    "__version__",
    # 🆕 Advanced Pattern Analysis Services
    "PatternAnalysisService",  # Legacy service
    "UnifiedPatternService",  # Next-generation unified engine
    # DTO types for pattern analysis
    "AnalysisEnvelope",
    "AnalysisSummary",
    "AnalysisType",
    "ChromaticElementDTO",
    "ChromaticSummaryDTO",
    "PatternMatchDTO",
    "SectionDTO",
    # Core analysis functions
    "analyze_melody",
    "analyze_scale",
    # Configuration
    "AnalysisOptions",
    "PedagogicalLevel",
    # Common result types
    "ScaleMelodyAnalysisResult",
    "AnalysisSuggestions",
    "KeySuggestion",
    # Music Theory Utility Functions
    "get_interval_name",
    "get_modal_characteristics",
    "get_characteristic_degrees",
    "get_harmonic_implications",
    "get_scale_applications",
    "describe_step_pattern",
    "canonicalize_key_signature",
    "describe_contour",
    # Character and Emotional Analysis
    "EmotionalProfile",
    "ProgressionCharacter",
    "CharacterSuggestion",
    "get_mode_emotional_profile",
    "analyze_progression_character",
    "get_character_suggestions",
    "get_modes_by_brightness",
    "describe_emotional_contour",
    # Music Theory Constants
    "ALL_KEYS",
    "ALL_MAJOR_KEYS",
    "ALL_MINOR_KEYS",
    "ALL_MODES",
    "MODAL_CHARACTERISTICS",
    "CANONICAL_KEY_MAP",
    "SEMITONE_TO_INTERVAL_NAME",
    "INTERVAL_ABBREVIATIONS",
    "SCALE_TO_CHORD_MAPPINGS",
    "ScaleDegree",
    # Scale and Pitch Constants
    "NOTE_TO_PITCH_CLASS",
    "PITCH_CLASS_NAMES",
    "MAJOR_SCALE_MODES",
    "MELODIC_MINOR_MODES",
    "HARMONIC_MINOR_MODES",
    "MODAL_PARENT_KEYS",
    # Musical Data API (comprehensive data access)
    "get_all_degree_to_mode_mappings",
    "get_all_notes",
    "get_all_scale_systems",
    "get_circle_of_fifths",
    "get_complete_musical_reference",
    "get_degree_to_mode_mapping",
    "get_interval_names",
    "get_mode_popularity_ranking",
    "get_mode_to_scale_family_mapping",
    "get_note_to_pitch_class_mapping",
    "get_parent_key_indices",
    "get_parent_key_mapping",
    "get_pitch_class_to_note_mapping",
    "get_relative_major_minor_pairs",
    "get_scale_notes",
    "get_scale_reference_for_frontend",
    "get_scale_system_info",
    "get_scale_system_names",
    "normalize_note_name",
    "note_to_pitch_class",
    "pitch_class_to_note",
    "validate_musical_input",
    # Audio analysis (requires [audio] extra; stubs raise AudioImportError if absent)
    "AudioAdapter",
    "AudioAnalysisResult",
    "AudioImportError",
    "ChordEvent",
    "analyze_audio",
    "analyze_audio_async",
]
