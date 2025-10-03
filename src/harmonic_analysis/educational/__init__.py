"""
Educational content system for harmonic analysis.

This module provides educational context and explanations for musical analysis results,
transforming technical pattern analysis into learning opportunities for musicians.
"""

from .educational_service import EducationalService
from .formatter import EducationalFormatter
from .knowledge_base import KnowledgeBase
from .types import (
    EducationalContext,
    LearningLevel,
    Misconception,
    ProgressionExample,
    RelatedConcept,
    RepertoireExample,
)

__all__ = [
    "EducationalContext",
    "LearningLevel",
    "ProgressionExample",
    "RepertoireExample",
    "Misconception",
    "RelatedConcept",
    "KnowledgeBase",
    "EducationalService",
    "EducationalFormatter",
]
