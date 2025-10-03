"""
Corpus Miner - Ground truth generation pipeline for unified pattern engine.

This module provides music21-based corpus extraction, pattern labeling with
adjudication heuristics, and unified target construction for calibration.
"""

from .corpus_extractor import CorpusExtractor, ExtractionConfig, MusicalContext
from .pattern_labeler import (
    AdjudicationRules,
    DifficultyStratum,
    LabeledSample,
    LabelSource,
    PatternLabeler,
    PatternMatch,
)
from .target_builder import (
    CalibrationBucket,
    TargetStatistics,
    UnifiedTargetBuilder,
)

__all__ = [
    # Extraction
    "CorpusExtractor",
    "ExtractionConfig",
    "MusicalContext",
    # Labeling
    "PatternLabeler",
    "AdjudicationRules",
    "LabeledSample",
    "PatternMatch",
    "LabelSource",
    "DifficultyStratum",
    # Target Construction
    "UnifiedTargetBuilder",
    "CalibrationBucket",
    "TargetStatistics",
]
