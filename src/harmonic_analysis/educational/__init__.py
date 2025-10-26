"""
Educational content system for harmonic analysis.

This module provides Bernstein-style educational explanations for
detected harmonic patterns. It is an optional feature.

Installation:
    pip install harmonic-analysis[educational]

Usage:
    from harmonic_analysis.educational import EducationalService

    service = EducationalService(level="intermediate")
    content = service.explain_pattern("cadence.authentic.perfect")
"""

from typing import Any

# Opening move: Feature detection for graceful degradation
_EDUCATIONAL_AVAILABLE = True
_IMPORT_ERROR: Exception | None = None

try:
    from .educational_service import EducationalService
    from .formatter import EducationalFormatter
    from .knowledge_base import KnowledgeBase
    from .types import (
        EducationalCard,
        EducationalContext,
        LearningLevel,
        Misconception,
        PatternSummary,
        ProgressionExample,
        RelatedConcept,
        RepertoireExample,
    )

    __all__ = [
        "EducationalService",
        "EducationalFormatter",
        "KnowledgeBase",
        "EducationalContext",
        "EducationalCard",
        "PatternSummary",
        "LearningLevel",
        "ProgressionExample",
        "RepertoireExample",
        "Misconception",
        "RelatedConcept",
        "is_available",
        "get_missing_dependencies",
        "require_educational",
    ]

except ImportError as e:
    _EDUCATIONAL_AVAILABLE = False
    _IMPORT_ERROR = e
    __all__ = [
        "is_available",
        "get_missing_dependencies",
        "require_educational",
    ]

    # Big play: Create helpful error messages for missing installation
    def _raise_educational_import_error(*args: Any, **kwargs: Any) -> Any:
        raise ImportError(
            "Educational features are not installed.\n"
            "Install with: pip install harmonic-analysis[educational]\n"
            "Or full installation: pip install harmonic-analysis[dev]"
        ) from _IMPORT_ERROR

    # Victory lap: Stub classes that raise helpful errors
    EducationalService = _raise_educational_import_error  # type: ignore
    EducationalFormatter = _raise_educational_import_error  # type: ignore
    KnowledgeBase = _raise_educational_import_error  # type: ignore
    EducationalContext = _raise_educational_import_error  # type: ignore
    LearningLevel = _raise_educational_import_error  # type: ignore
    ProgressionExample = _raise_educational_import_error  # type: ignore
    RepertoireExample = _raise_educational_import_error  # type: ignore
    Misconception = _raise_educational_import_error  # type: ignore
    RelatedConcept = _raise_educational_import_error  # type: ignore


# Export availability flag for conditional usage
def is_available() -> bool:
    """
    Check if educational features are available.

    Returns:
        bool: True if educational features can be imported, False otherwise

    Example:
        >>> from harmonic_analysis.educational import is_available
        >>> if is_available():
        ...     print("Educational features ready!")
        ... else:
        ...     print("Install with: pip install harmonic-analysis[educational]")
    """
    return _EDUCATIONAL_AVAILABLE


def get_missing_dependencies() -> list[str]:
    """
    Get list of missing dependencies preventing educational features.

    Returns:
        list[str]: List of missing package names (empty if all available)

    Example:
        >>> from harmonic_analysis.educational import get_missing_dependencies
        >>> missing = get_missing_dependencies()
        >>> if missing:
        ...     print(f"Missing packages: {', '.join(missing)}")
        ... else:
        ...     print("All educational dependencies installed!")
    """
    if _EDUCATIONAL_AVAILABLE:
        return []

    # Main play: Parse import error to identify missing dependencies
    # Currently educational has no external dependencies, but this is future-proof
    missing = []
    if _IMPORT_ERROR:
        error_msg = str(_IMPORT_ERROR).lower()
        # Check for common dependency import failures
        if "jsonschema" in error_msg:
            missing.append("jsonschema")
        if "jinja2" in error_msg:
            missing.append("jinja2")
        if "yaml" in error_msg or "pyyaml" in error_msg:
            missing.append("pyyaml")

    # If we couldn't identify specific packages, return generic message
    if not missing:
        missing = ["educational module dependencies"]

    return missing


def require_educational() -> None:
    """
    Raise ImportError if educational features are not available.

    Raises:
        ImportError: If educational features cannot be imported, with
                    installation instructions

    Example:
        >>> from harmonic_analysis.educational import require_educational
        >>> try:
        ...     require_educational()
        ...     # Safe to use educational features
        ...     from harmonic_analysis.educational import EducationalService
        ... except ImportError as e:
        ...     print(f"Educational not available: {e}")
    """
    if not _EDUCATIONAL_AVAILABLE:
        missing = get_missing_dependencies()
        raise ImportError(
            f"Educational features are not installed.\n"
            f"Missing dependencies: {', '.join(missing)}\n"
            f"Install with: pip install harmonic-analysis[educational]\n"
            f"Or full installation: pip install harmonic-analysis[dev]"
        ) from _IMPORT_ERROR
