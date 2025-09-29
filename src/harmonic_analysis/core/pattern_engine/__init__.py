"""
Pattern Engine - Unified pattern-based harmonic analysis system.

This module implements a unified pattern detection and analysis engine that
combines functional and modal analysis through a single, configurable pipeline
with corpus-based calibration and quality gates.
"""

# New unified engine components
from .aggregator import Aggregator
from .calibration import CalibrationMapping, CalibrationMetrics, Calibrator
from .evidence import Evidence

# Legacy components (to be migrated)
from .glossary_service import GlossaryService
from .matcher import Matcher, Pattern, PatternLibrary, Token, load_library
from .pattern_engine import AnalysisContext, PatternEngine
from .pattern_loader import PatternLoader
from .plugin_registry import PatternEvaluator, PluginRegistry
from .target_builder_unified import (
    TargetAnnotation,
)
from .target_builder_unified import UnifiedTargetBuilder as TargetBuilder
from .token_converter import TokenConverter

__all__ = [
    # Legacy (for backwards compatibility during migration)
    "Token",
    "Pattern",
    "PatternLibrary",
    "Matcher",
    "load_library",
    "TokenConverter",
    "GlossaryService",
    # New unified engine
    "PatternEngine",
    "AnalysisContext",
    "Evidence",
    "PatternLoader",
    "PluginRegistry",
    "PatternEvaluator",
    "Aggregator",
    "Calibrator",
    "CalibrationMapping",
    "CalibrationMetrics",
    "TargetBuilder",
    "TargetAnnotation",
]
