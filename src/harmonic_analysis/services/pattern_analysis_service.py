"""
Pattern Analysis Service - Backward compatibility facade over UnifiedPatternService.

This service maintains API compatibility with the legacy PatternAnalysisService
while delegating all analysis work to the new unified pattern engine.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from harmonic_analysis.dto import (
    AnalysisEnvelope,
    AnalysisSummary,
    SectionDTO,
)
from .unified_pattern_service import UnifiedPatternService

logger = logging.getLogger(__name__)


class PatternAnalysisService:
    """
    Legacy PatternAnalysisService API maintained for backward compatibility.

    This is now a thin facade over UnifiedPatternService, providing the same
    API surface while delegating all actual analysis to the unified engine.
    """

    def __init__(
        self,
        functional_analyzer: Optional[Any] = None,  # Ignored - compatibility only
        matcher: Optional[Any] = None,  # Ignored - compatibility only
        modal_analyzer: Optional[Any] = None,  # Ignored - compatibility only
        chromatic_analyzer: Optional[Any] = None,  # Ignored - compatibility only
        arbitration_policy: Optional[Any] = None,  # Ignored - compatibility only
        calibration_service: Optional[Any] = None,  # Ignored - compatibility only
        auto_calibrate: bool = True,
    ) -> None:
        """
        Initialize PatternAnalysisService as a facade over UnifiedPatternService.

        Legacy parameters are accepted for compatibility but ignored since the
        unified service handles all analysis internally.

        Args:
            auto_calibrate: Whether to enable quality-gated calibration
            **kwargs: Legacy parameters (ignored)
        """
        # Opening move: delegate everything to the unified pattern service
        self._unified_service = UnifiedPatternService(auto_calibrate=auto_calibrate)

        # Victory lap: log the migration for observability
        logger.info("✅ PatternAnalysisService initialized as facade over UnifiedPatternService")
        if not auto_calibrate:
            logger.debug("🔧 Auto-calibration disabled in unified service")

    async def analyze_with_patterns_async(
        self,
        chord_symbols: List[str],
        profile: str = "classical",
        best_cover: bool = True,  # Ignored - compatibility only
        key_hint: Optional[str] = None,
        sections: Optional[List[SectionDTO]] = None,  # Ignored - compatibility only
    ) -> AnalysisEnvelope:
        """
        Analyze chord progression using unified pattern engine.

        Args:
            chord_symbols: List of chord symbols (e.g., ['C', 'F', 'G', 'C'])
            profile: Analysis profile (passed through to unified service)
            best_cover: Legacy parameter (ignored)
            key_hint: Optional key context for analysis
            sections: Legacy parameter (ignored)

        Returns:
            AnalysisEnvelope with primary and alternative analyses
        """
        # Big play: delegate to unified service with parameter mapping
        return await self._unified_service.analyze_with_patterns_async(
            chords=chord_symbols,
            key_hint=key_hint,
            profile=profile,
            options={"best_cover": best_cover, "sections": sections}  # Pass through for compatibility
        )

    def analyze_with_patterns(
        self,
        chord_symbols: List[str],
        profile: str = "classical",
        best_cover: bool = True,  # Ignored - compatibility only
        key_hint: Optional[str] = None,
        sections: Optional[List[SectionDTO]] = None,  # Ignored - compatibility only
    ) -> AnalysisEnvelope:
        """
        Synchronous wrapper for analyze_with_patterns_async.

        This looks odd, but it saves us from async complexity in sync contexts.
        """
        # Time to tackle the tricky bit: delegate to unified service sync method
        return self._unified_service.analyze_with_patterns(
            chords=chord_symbols,
            key_hint=key_hint,
            profile=profile,
            options={"best_cover": best_cover, "sections": sections}
        )

    def get_analysis_summary(self, envelope: AnalysisEnvelope) -> AnalysisSummary:
        """Generate analysis summary from envelope (compatibility method)."""
        # Final whistle: delegate summary generation to unified service
        return self._unified_service.get_analysis_summary(envelope)

    # Legacy property access for backward compatibility
    @property
    def calibrator(self):
        """Access to calibrator for backward compatibility."""
        return self._unified_service.calibrator

    @property
    def calibration_mapping(self):
        """Access to calibration mapping for backward compatibility."""
        return self._unified_service.calibration_mapping

    @property
    def glossary_service(self):
        """Access to glossary service for backward compatibility."""
        # Import here to avoid circular dependencies
        from ..core.pattern_engine.glossary_service import GlossaryService
        if not hasattr(self, '_glossary_service'):
            self._glossary_service = GlossaryService()
        return self._glossary_service