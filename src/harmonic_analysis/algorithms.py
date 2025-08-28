"""Advanced Algorithmic Analysis Module.

Advanced algorithmic analysis features including bidirectional key suggestions,
pattern detection, and multi-key analysis capabilities.

This module provides sophisticated computational music theory algorithms
for advanced users and applications requiring deeper analytical insight.
"""

# Re-export all algorithmic analysis functionality
from .services.algorithmic_suggestion_engine import (
    # Core engine
    AlgorithmicSuggestionEngine,

    # Result types
    KeyAnalysisResult,
)

from .services.bidirectional_suggestion_engine import (
    # Core engine
    BidirectionalSuggestionEngine,

    # Result types
    BidirectionalSuggestion,
    KeyRelevanceScore,

    # Enums
    SuggestionType,
)

# Import types for suggestion system
from .types import (
    # Configuration
    AnalysisOptions,

    # Result types
    AnalysisSuggestions,
    KeySuggestion,
)

__all__ = [
    # Core engines
    "AlgorithmicSuggestionEngine",
    "BidirectionalSuggestionEngine",

    # Result types
    "KeyAnalysisResult",
    "BidirectionalSuggestion",
    "KeyRelevanceScore",

    # Enums
    "SuggestionType",

    # Configuration types
    "AnalysisOptions",

    # Suggestion types
    "AnalysisSuggestions",
    "KeySuggestion",
]
