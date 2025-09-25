"""
Unified Pattern Service - Compatibility wrapper for PatternAnalysisService.

This service provides a drop-in replacement for PatternAnalysisService using
the new unified pattern engine while maintaining complete API compatibility.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from harmonic_analysis.dto import (
    AnalysisEnvelope,
    AnalysisSummary,
    AnalysisType,
    ChromaticElementDTO,
    ChromaticSummaryDTO,
    FunctionalChordDTO,
    PatternMatchDTO,
    SectionDTO,
)

from ..core.pattern_engine.pattern_engine import PatternEngine, AnalysisContext
from ..core.pattern_engine.pattern_loader import PatternLoader
from ..core.pattern_engine.aggregator import Aggregator
from ..core.pattern_engine.calibration import Calibrator, CalibrationMapping
from ..core.pattern_engine.plugin_registry import PluginRegistry
from ..core.pattern_engine.token_converter import romanize_chord
from ..core.utils.music_theory_constants import canonicalize_key_signature

logger = logging.getLogger(__name__)


class UnifiedPatternService:
    """Unified pattern service using the new pattern engine architecture.

    Drop-in replacement for PatternAnalysisService with identical API.
    """

    def __init__(
        self,
        functional_analyzer: Optional[Any] = None,  # Ignored for compatibility
        matcher: Optional[Any] = None,  # Ignored for compatibility
        modal_analyzer: Optional[Any] = None,  # Ignored for compatibility
        chromatic_analyzer: Optional[Any] = None,  # Ignored for compatibility
        arbitration_policy: Optional[Any] = None,  # Ignored for compatibility
        calibration_service: Optional[Any] = None,
        auto_calibrate: bool = True,
    ) -> None:
        # Main play: initialize the unified pattern engine
        loader = PatternLoader()
        aggregator = Aggregator()
        plugin_registry = PluginRegistry()
        self.engine = PatternEngine(loader, aggregator, plugin_registry)

        # Load unified patterns using the correct method
        try:
            patterns_path = Path(__file__).parent.parent / "core" / "pattern_engine" / "patterns_unified.json"
            # Big play: load full structure but provide patterns as expected by engine
            full_data = loader.load(patterns_path)
            patterns_list = full_data.get("patterns", [])
            self.engine._patterns = {"patterns": patterns_list}

            logger.info(f"✅ Loaded {len(patterns_list)} unified patterns from {patterns_path}")
        except Exception as e:
            logger.error(f"❌ Failed to load unified patterns: {e}")
            raise

        # Store auto_calibrate setting for compatibility
        self.auto_calibrate = auto_calibrate

        # Modern pattern engine calibration (quality-gated)
        self.calibrator = Calibrator() if auto_calibrate else None
        self.calibration_mapping = None

        # Initialize calibration if enabled
        if self.calibrator:
            self._initialize_calibration()

    def _initialize_calibration(self) -> None:
        """Initialize calibration mapping using synthetic training data."""
        try:
            # Big play: collect synthetic calibration data for quality-gated calibration
            raw_scores, targets = self._collect_calibration_data()

            if len(raw_scores) > 0:
                # Victory lap: fit calibration mapping with quality gates
                self.calibration_mapping = self.calibrator.fit(raw_scores, targets)

                if self.calibration_mapping.passed_gates:
                    logger.info(f"✅ Quality-gated calibration initialized: {self.calibration_mapping.mapping_type}")
                else:
                    logger.info("⚠️ Calibration quality gates failed - using identity mapping")
            else:
                logger.warning("❌ No calibration data available - calibration disabled")

        except Exception as e:
            logger.warning(f"⚠️ Calibration initialization failed: {e}")
            self.calibration_mapping = None

    def _collect_calibration_data(self) -> Tuple[List[float], List[float]]:
        """
        Collect synthetic calibration data for training.

        This method generates representative raw scores and target reliability values
        to train the quality-gated calibration system.

        Returns:
            Tuple of (raw_scores, targets) for calibration training
        """
        import numpy as np

        # Opening move: generate synthetic calibration data
        # This simulates real analysis scenarios with known reliability
        raw_scores = []
        targets = []

        # High confidence scenarios (strong patterns, clear tonality)
        high_conf_base = np.random.uniform(0.7, 0.95, 50)
        high_targets = np.clip(high_conf_base * 0.85 + 0.1, 0.0, 1.0)
        raw_scores.extend(high_conf_base)
        targets.extend(high_targets)

        # Medium confidence scenarios (ambiguous patterns, multiple interpretations)
        med_conf_base = np.random.uniform(0.4, 0.7, 80)
        med_targets = np.clip(med_conf_base * 0.6 + 0.2, 0.0, 1.0)
        raw_scores.extend(med_conf_base)
        targets.extend(med_targets)

        # Low confidence scenarios (weak patterns, chromatic passages)
        low_conf_base = np.random.uniform(0.1, 0.4, 30)
        low_targets = np.clip(low_conf_base * 0.3 + 0.05, 0.0, 1.0)
        raw_scores.extend(low_conf_base)
        targets.extend(low_targets)

        logger.debug(f"🎯 Generated {len(raw_scores)} calibration samples")
        return raw_scores, targets

    async def analyze_with_patterns_async(
        self,
        chords: List[str],
        key_hint: Optional[str] = None,
        profile: str = "classical",
        options: Optional[Any] = None,
    ) -> AnalysisEnvelope:
        """
        Analyze chord progression using unified pattern engine.

        Args:
            chords: List of chord symbols (e.g., ['C', 'F', 'G', 'C'])
            key_hint: Optional key context for analysis
            profile: Analysis profile (currently ignored)
            options: Additional analysis options (currently ignored)

        Returns:
            AnalysisEnvelope with primary and alternative analyses
        """
        # Time to tackle the tricky bit: convert to unified engine format
        # Big play: derive roman numerals from chords and key hint
        roman_numerals = []
        if key_hint and chords:
            try:
                for chord in chords:
                    roman = romanize_chord(chord, key_hint, profile)
                    # Victory lap: normalize 'b' to '♭' for pattern matching compatibility
                    roman = roman.replace('b', '♭')
                    roman_numerals.append(roman)
                logger.debug(f"🎵 Derived romans: {chords} → {roman_numerals}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to derive roman numerals: {e}")
                roman_numerals = []

        context = AnalysisContext(
            key=key_hint or "",
            chords=chords,
            roman_numerals=roman_numerals,
            melody=[],
            scales=[],
            metadata={"profile": profile}
        )

        # Big play: run the unified engine analysis
        envelope = self.engine.analyze(context)

        # Main search: add evidence_details alias for compatibility
        if not hasattr(envelope, 'evidence_details'):
            envelope.evidence_details = envelope.evidence

        # Victory lap: apply quality-gated calibration if available
        if self.calibrator and self.calibration_mapping and envelope.primary:
            try:
                # Apply modern calibration with quality gates
                calibrated_confidence = self.calibration_mapping.apply(envelope.primary.confidence)
                envelope.primary.confidence = calibrated_confidence
                logger.debug(f"🎯 Applied quality-gated calibration: {envelope.primary.confidence:.3f}")
            except Exception as e:
                logger.warning(f"⚠️ Quality-gated calibration failed: {e}")

        return envelope

    def analyze_with_patterns(
        self,
        chords: List[str],
        key_hint: Optional[str] = None,
        profile: str = "classical",
        options: Optional[Any] = None,
    ) -> AnalysisEnvelope:
        """
        Synchronous wrapper for analyze_with_patterns_async.

        This looks odd, but it saves us from async complexity in sync contexts.
        """
        import asyncio

        # Opening move: check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're in a loop, we need to run in a thread to avoid blocking
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.analyze_with_patterns_async(chords, key_hint, profile, options)
                )
                return future.result()
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            return asyncio.run(
                self.analyze_with_patterns_async(chords, key_hint, profile, options)
            )

    # Additional compatibility methods can be added here as needed
    # These would delegate to the unified engine with appropriate conversions

    def get_analysis_summary(self, envelope: AnalysisEnvelope) -> AnalysisSummary:
        """Generate analysis summary from envelope (compatibility method)."""
        if not envelope.primary:
            return AnalysisSummary(
                type=AnalysisType.FUNCTIONAL,
                roman_numerals=[],
                confidence=0.0
            )

        # Opening move: use correct AnalysisSummary constructor based on DTO definition
        return AnalysisSummary(
            type=envelope.primary.type,
            roman_numerals=getattr(envelope.primary, 'roman_numerals', []),
            confidence=envelope.primary.confidence,
            key_signature=getattr(envelope.primary, 'key_signature', None),
            mode=getattr(envelope.primary, 'mode', None),
            reasoning=getattr(envelope.primary, 'reasoning', None),
            patterns=getattr(envelope.primary, 'patterns', []),
            chromatic_elements=getattr(envelope.primary, 'chromatic_elements', []),
            modal_characteristics=getattr(envelope.primary, 'modal_characteristics', [])
        )