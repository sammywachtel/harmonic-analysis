"""
Pattern Analysis Service - Backward compatibility facade over UnifiedPatternService.

This service maintains API compatibility with the legacy PatternAnalysisService
while delegating all analysis work to the new unified pattern engine.
"""

from __future__ import annotations

import logging
import os
from typing import Any, List, Optional

from harmonic_analysis.dto import (
    AnalysisEnvelope,
    AnalysisSummary,
    AnalysisType,
    SectionDTO,
)

from .analysis_arbitration_service import AnalysisArbitrationService
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
        arbitration_policy: Optional[Any] = None,  # Used for arbitration service
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

        # Store arbitration policy for iteration 9 arbitration support
        self._arbitration_service = None
        if arbitration_policy is not None:
            self._arbitration_service = AnalysisArbitrationService(
                policy=arbitration_policy
            )
            logger.info("✅ AnalysisArbitrationService enabled with policy")

        # Victory lap: log the migration for observability
        logger.info(
            "✅ PatternAnalysisService initialized as facade over UnifiedPatternService"
        )
        if not auto_calibrate:
            logger.debug("🔧 Auto-calibration disabled in unified service")

    async def analyze_with_patterns_async(
        self,
        chord_symbols: Optional[List[str]] = None,
        profile: str = "classical",
        best_cover: bool = True,  # Ignored - compatibility only
        key_hint: Optional[str] = None,
        sections: Optional[List[SectionDTO]] = None,  # Ignored - compatibility only
        romans: Optional[List[str]] = None,  # NEW: Roman numeral input support
    ) -> AnalysisEnvelope:
        """
        Analyze chord progression using unified pattern engine.

        Args:
            chord_symbols: List of chord symbols (e.g., ['C', 'F', 'G', 'C'])
            profile: Analysis profile (passed through to unified service)
            best_cover: Legacy parameter (ignored)
            key_hint: Optional key context for analysis (required for roman inputs)
            sections: Legacy parameter (ignored)
            romans: List of roman numerals (e.g., ['I', 'vi', 'IV', 'V'])
                   Mutually exclusive with chord_symbols; requires key_hint

        Returns:
            AnalysisEnvelope with primary and alternative analyses

        Raises:
            ValueError: If both chord_symbols and romans are provided, or if
                       romans are provided without key_hint
        """
        # Opening move: validate input exclusivity and requirements
        if chord_symbols and romans:
            raise ValueError(
                "Cannot provide both chord_symbols and romans - choose one input type"
            )

        # Special case: empty chord_symbols list is allowed for backward compatibility
        if chord_symbols is None and not romans:
            raise ValueError("Must provide either chord_symbols or romans")

        if romans and not key_hint:
            raise ValueError("Roman numeral analysis requires key_hint parameter")

        # Big play: delegate to unified service with parameter mapping
        envelope = await self._unified_service.analyze_with_patterns_async(
            chords=chord_symbols,
            romans=romans,
            key_hint=key_hint,
            profile=profile,
            options={
                "best_cover": best_cover,
                "sections": sections,
            },  # Pass through for compatibility
        )

        # Iteration 9: Apply arbitration if arbitration service is configured
        if self._arbitration_service and envelope.primary:
            try:
                # Create separate functional and modal summaries for arbitration
                primary = envelope.primary

                # Create functional summary (always available)
                functional_summary = AnalysisSummary(
                    type=AnalysisType.FUNCTIONAL,
                    roman_numerals=getattr(primary, "roman_numerals", []),
                    confidence=getattr(primary, "functional_confidence", 0.0),
                    key_signature=getattr(primary, "key_signature", None),
                    mode=getattr(primary, "mode", None),
                    reasoning=getattr(primary, "reasoning", ""),
                    patterns=getattr(primary, "patterns", []),
                )

                # Create modal summary if modal confidence exists
                modal_summary = None
                if getattr(primary, "modal_confidence", 0.0) > 0.0:
                    modal_summary = AnalysisSummary(
                        type=AnalysisType.MODAL,
                        roman_numerals=getattr(primary, "roman_numerals", []),
                        confidence=getattr(primary, "modal_confidence", 0.0),
                        key_signature=getattr(primary, "key_signature", None),
                        mode=getattr(primary, "mode", None),
                        reasoning=getattr(primary, "reasoning", ""),
                        patterns=getattr(primary, "patterns", []),
                        modal_characteristics=getattr(
                            primary, "modal_characteristics", []
                        ),
                        modal_evidence=getattr(
                            primary, "modal_evidence", []
                        ),  # Iteration 9A: Pass modal evidence
                    )

                # Apply arbitration
                arbitration_result = self._arbitration_service.arbitrate(
                    functional_summary=functional_summary,
                    modal_summary=modal_summary,
                    chord_symbols=chord_symbols,
                )

                # Iteration 9: Enhanced arbitration diagnostics
                if "arbitration" in (os.getenv("HARMONIC_ANALYSIS_DEBUG", "").lower()):
                    logger.debug(
                        f"🎯 ARBITRATION DIAGNOSTIC:\n"
                        f"  Input: {chord_symbols}\n"
                        f"  Functional conf: {functional_summary.confidence:.3f}\n"
                        f"  Modal conf: {modal_summary.confidence if modal_summary else 'N/A'}\n"
                        f"  Result: {arbitration_result.primary.type}\n"
                        f"  Confidence gap: {arbitration_result.confidence_gap:.3f}\n"
                        f"  Rationale: {arbitration_result.rationale}\n"
                        f"  Policy thresholds: func_min={self._arbitration_service.policy.min_functional_confidence}, "
                        f"modal_min={self._arbitration_service.policy.min_modal_confidence}"
                    )

                # Update envelope with arbitration result
                envelope.primary = arbitration_result.primary
                envelope.alternatives = arbitration_result.alternatives

                logger.debug(
                    f"🎯 Arbitration applied: {arbitration_result.primary.type} (gap: {arbitration_result.confidence_gap:.3f})"
                )

            except Exception as e:
                logger.warning(
                    f"⚠️ Arbitration failed: {e} - using unified service result"
                )

        return envelope

    def analyze_with_patterns(
        self,
        chord_symbols: Optional[List[str]] = None,
        profile: str = "classical",
        best_cover: bool = True,  # Ignored - compatibility only
        key_hint: Optional[str] = None,
        sections: Optional[List[SectionDTO]] = None,  # Ignored - compatibility only
        romans: Optional[List[str]] = None,  # NEW: Roman numeral input support
    ) -> AnalysisEnvelope:
        """
        Synchronous wrapper for analyze_with_patterns_async.

        This looks odd, but it saves us from async complexity in sync contexts.
        """
        import asyncio

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            envelope = asyncio.run(
                self.analyze_with_patterns_async(
                    chord_symbols=chord_symbols,
                    romans=romans,
                    key_hint=key_hint,
                    profile=profile,
                    best_cover=best_cover,
                    sections=sections,
                )
            )
        else:
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.analyze_with_patterns_async(
                        chord_symbols=chord_symbols,
                        romans=romans,
                        key_hint=key_hint,
                        profile=profile,
                        best_cover=best_cover,
                        sections=sections,
                    ),
                )
                envelope = future.result()

        primary = envelope.primary
        if primary and getattr(primary, "chromatic_elements", None):
            summary_str = ", ".join(str(el) for el in primary.chromatic_elements)
            logger.info("Chromatic: %s", summary_str)
        elif primary:
            logger.debug("Chromatic: No chromatic elements detected")

        return envelope

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

        if not hasattr(self, "_glossary_service"):
            self._glossary_service = GlossaryService()
        return self._glossary_service
