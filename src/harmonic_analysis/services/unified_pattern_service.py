"""
Unified Pattern Service - Compatibility wrapper for PatternAnalysisService.

This service provides a drop-in replacement for PatternAnalysisService using
the new unified pattern engine while maintaining complete API compatibility.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from harmonic_analysis.dto import AnalysisEnvelope, AnalysisSummary, AnalysisType

from ..core.pattern_engine.aggregator import Aggregator
from ..core.pattern_engine.calibration import CalibrationMapping, Calibrator
from ..core.pattern_engine.pattern_engine import AnalysisContext, PatternEngine
from ..core.pattern_engine.pattern_loader import PatternLoader
from ..core.pattern_engine.plugin_registry import PluginRegistry
from ..core.pattern_engine.token_converter import romanize_chord
from ..core.telemetry import get_telemetry_collector
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
            patterns_path = (
                Path(__file__).parent.parent
                / "core"
                / "pattern_engine"
                / "patterns_unified.json"
            )
            # Big play: load full structure but provide patterns as expected by engine
            full_data = loader.load(patterns_path)
            patterns_list = full_data.get("patterns", [])
            self.engine._patterns = {"patterns": patterns_list}

            logger.info(
                f"✅ Loaded {len(patterns_list)} unified patterns from {patterns_path}"
            )
        except Exception as e:
            logger.error(f"❌ Failed to load unified patterns: {e}")
            raise

        # Store auto_calibrate setting for compatibility
        self.auto_calibrate = auto_calibrate

        # Modern pattern engine calibration (quality-gated)
        self.calibrator = Calibrator() if auto_calibrate else None
        self.calibration_mapping: Optional[CalibrationMapping] = None

        # Initialize telemetry
        self.telemetry = get_telemetry_collector()

        # Initialize calibration if enabled
        if self.calibrator:
            self._initialize_calibration()

    def _initialize_calibration(self) -> None:
        """Initialize calibration mapping using synthetic training data."""
        try:
            # Big play: collect synthetic calibration data for quality-gated calibration
            raw_scores, targets = self._collect_calibration_data()

            if len(raw_scores) > 0 and self.calibrator is not None:
                # Victory lap: fit calibration mapping with quality gates
                self.calibration_mapping = self.calibrator.fit(raw_scores, targets)

                if self.calibration_mapping and self.calibration_mapping.passed_gates:
                    mapping_type = (
                        self.calibration_mapping.mapping_type
                        if self.calibration_mapping
                        else "unknown"
                    )
                    logger.info(
                        f"✅ Quality-gated calibration initialized: {mapping_type}"
                    )
                else:
                    logger.info(
                        "⚠️ Calibration quality gates failed - using identity mapping"
                    )
            else:
                logger.warning(
                    "❌ No calibration data available - calibration disabled"
                )

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
        raw_scores: List[float] = []
        targets: List[float] = []

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
        chords: Optional[List[str]] = None,
        key_hint: Optional[str] = None,
        profile: str = "classical",
        options: Optional[Any] = None,
        romans: Optional[List[str]] = None,  # NEW: Roman numeral input support
        notes: Optional[List[str]] = None,  # NEW: Scale notes input support
        melody: Optional[List[str]] = None,  # NEW: Melody input support
    ) -> AnalysisEnvelope:
        """
        Analyze chord progression using unified pattern engine.

        Args:
            chords: List of chord symbols (e.g., ['C', 'F', 'G', 'C'])
            key_hint: Optional key context (required for roman/scale/melody inputs)
            profile: Analysis profile (currently ignored)
            options: Additional analysis options (supports "sections" for
                   section-aware analysis)
            romans: List of roman numerals (e.g., ['I', 'vi', 'IV', 'V'])
                   Mutually exclusive with other inputs; requires key_hint
            notes: List of scale notes (e.g., ['C', 'D', 'E', 'F', 'G', 'A', 'B'])
                   Mutually exclusive with other inputs; requires key_hint
            melody: List of melodic notes (e.g., ['G4', 'A4', 'B4', 'C5'])
                   Mutually exclusive with other inputs; requires key_hint

        Returns:
            AnalysisEnvelope with primary and alternative analyses
        """
        import time

        start_time = time.perf_counter()

        # Opening move: start telemetry session
        context_placeholder = type(
            "obj",
            (object,),
            {
                "chords": chords,
                "melody": melody,
                "scales": [notes] if notes else [],
                "roman_numerals": romans,
            },
        )()
        session_id = self.telemetry.log_analysis_start(context_placeholder)

        # Opening move: validate input exclusivity
        input_count = sum(1 for x in [chords, romans, notes, melody] if x is not None)
        if input_count > 1:
            raise ValueError(
                "Cannot provide multiple input types - "
                "choose one: chords, romans, notes, or melody"
            )

        # Initialize data containers for scale/melody summary enhancement
        scale_analysis_data: Optional[Dict[str, Any]] = None
        scale_context_data: Optional[Dict[str, Any]] = None
        melody_analysis_data: Optional[Dict[str, Any]] = None

        # Big play: handle scale notes input using our new normalize_scale_input
        if notes:
            if not key_hint:
                raise ValueError("Scale analysis requires key_hint parameter")

            # Main play: normalize and validate scale input
            from ..core.pattern_engine.token_converter import normalize_scale_input

            try:
                scale_data = normalize_scale_input(notes, key_hint)
                scale_analysis_data = scale_data  # Store for summary enhancement

                if not scale_data["is_valid"]:
                    error_msg = "; ".join(scale_data["validation_errors"])
                    if not error_msg:
                        error_msg = (
                            "Scale does not match any known mode "
                            "or contains insufficient data"
                        )
                    raise ValueError(f"Invalid scale input: {error_msg}")

                # Victory lap: extract normalized data for analysis context
                canonical_notes = scale_data["canonical_notes"]
                scale_degrees = scale_data["scale_degrees"]
                detected_mode = scale_data["detected_mode"]

                logger.debug(
                    f"🎼 Processed scale: {notes} → {canonical_notes} "
                    f"(degrees: {scale_degrees}, mode: {detected_mode})"
                )

                # Store scale context data for pattern engine
                scale_context_data = {
                    "notes": canonical_notes,
                    "degrees": scale_degrees,
                    "mode": detected_mode,
                    "intervals": scale_data["intervals"],
                }
                # Keep full scale_data for summary enhancement

            except Exception as e:
                logger.error(f"❌ Scale analysis failed: {e}")
                raise ValueError(f"Scale analysis failed: {e}")

        # Big play: handle melody input using our new normalize_melody_input
        elif melody:
            if not key_hint:
                raise ValueError("Melody analysis requires key_hint parameter")

            # Main play: normalize and validate melody input
            from ..core.pattern_engine.token_converter import normalize_melody_input

            try:
                melody_data = normalize_melody_input(melody, key_hint)
                melody_analysis_data = melody_data  # Store for summary enhancement

                if not melody_data["is_valid"]:
                    error_msg = "; ".join(melody_data["validation_errors"])
                    logger.warning(f"⚠️ Melody validation issues: {error_msg}")
                    # Continue with fallback - empty melody for degradation
                    melody_context_data = {
                        "notes": melody_data["canonical_notes"],
                        "degrees": [],
                        "intervals": [],
                        "contour": [],
                    }
                    # Update analysis data for summary enhancement
                    melody_analysis_data = melody_context_data
                else:
                    # Victory lap: extract normalized data for analysis context
                    canonical_notes = melody_data["canonical_notes"]
                    note_degrees = melody_data["note_degrees"]
                    intervals = melody_data["intervals"]
                    contour = melody_data["contour"]

                    logger.debug(
                        f"🎵 Processed melody: {melody} → {canonical_notes} "
                        f"(degrees: {note_degrees}, intervals: {intervals})"
                    )

                    # Store melody analysis data for pattern engine
                    melody_context_data = {
                        "notes": canonical_notes,
                        "degrees": note_degrees,
                        "intervals": intervals,
                        "contour": contour,
                    }
                    # Update analysis data for summary enhancement
                    melody_analysis_data = melody_context_data

            except Exception as e:
                logger.error(f"❌ Melody analysis failed: {e}")
                raise ValueError(f"Melody analysis failed: {e}")

        # Handle roman numeral input conversion
        elif romans:
            if not key_hint:
                raise ValueError("Roman numeral analysis requires key_hint parameter")

            # Main play: convert romans to chords using our converter
            from ..core.pattern_engine.token_converter import roman_to_chord

            chords = []
            for roman in romans:
                try:
                    chord = roman_to_chord(roman, key_hint)
                    chords.append(chord)
                except Exception as e:
                    logger.warning(
                        f"⚠️ Failed to convert roman '{roman}' "
                        f"in key '{key_hint}': {e}"
                    )
                    # Fallback: use roman as-is (will likely fail pattern
                    # matching but won't crash)
                    chords.append(roman)

            logger.debug(
                f"🎵 Converted romans to chords: {romans} → {chords} "
                f"(key: {key_hint})"
            )

        elif chords is None:
            raise ValueError("Must provide one of: chords, romans, or notes parameter")

        # Time to tackle the tricky bit: convert to unified engine format
        # Big play: derive roman numerals from chords and key hint
        roman_numerals = []
        inferred_key = key_hint

        # Special handling: if romans were provided, use them directly
        if romans:
            # Victory lap: normalize provided romans for pattern matching
            # compatibility
            roman_numerals = [roman.replace("b", "♭") for roman in romans]
            logger.debug(f"🎵 Using provided romans: {romans} → {roman_numerals}")
        else:
            # Standard chord-to-roman conversion path
            # Iteration 9B: Advanced key inference analyzing chord quality
            # and modal signatures
            if not key_hint and chords:
                inferred_key = self._infer_key_from_progression(chords)
                logger.debug(f"🔍 Inferred key: {inferred_key}")

            if inferred_key and chords:
                try:
                    for chord in chords:
                        roman = romanize_chord(chord, inferred_key, profile)
                        # Victory lap: normalize 'b' to '♭' for pattern
                        # matching compatibility
                        roman = roman.replace("b", "♭")
                        roman_numerals.append(roman)
                    logger.debug(
                        f"🎵 Derived romans with key {inferred_key}: "
                        f"{chords} → {roman_numerals}"
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Failed to derive roman numerals: {e}")
                    roman_numerals = []

        # Iteration 9A: Apply Lydian roman numeral normalization (♭V → ♯IV)
        roman_numerals = self._normalize_lydian_romans(roman_numerals, inferred_key)

        # Iteration 9A: Detect mode and add to metadata
        mode_label = self._detect_mode_label(roman_numerals, inferred_key, chords or [])
        metadata = {"profile": profile}
        if mode_label:
            metadata["mode"] = mode_label
            logger.debug(f"🎵 Detected mode: {mode_label}")

        # Iteration 9C: Extract sections from options for section-aware analysis
        sections: List[Any] = []
        if options and isinstance(options, dict) and "sections" in options:
            sections = options["sections"] or []
            logger.debug(f"🎭 Section-aware analysis with {len(sections)} sections")

        # Big play: prepare scale data for context
        scales_data = []
        if notes and scale_analysis_data:
            scales_data = [scale_context_data]
            logger.debug("🎼 Including scale data in analysis context")

        # Big play: prepare melody data for context
        melody_context_list = []
        if melody_analysis_data:
            melody_context_list = [melody_analysis_data]
            logger.debug("🎵 Including melody data in analysis context")

        context = AnalysisContext(
            key=inferred_key or "",
            chords=chords or [],  # Empty list for scale-only analysis
            roman_numerals=roman_numerals,
            melody=melody_context_list,
            scales=scales_data,
            metadata=metadata,
            sections=sections,
        )

        # Big play: run the unified engine analysis
        envelope = self.engine.analyze(context)

        # Iteration 9F: Conditional modal parent key conversion (only when
        # modal > functional confidence AND no explicit key hint)
        if mode_label and envelope.primary:
            # Always preserve modal parent key info in metadata for reporting
            modal_parent_key = self._convert_to_modal_parent_key(
                mode_label, context.key or "C major"
            )
            if modal_parent_key != context.key:
                # Store modal parent key in terms for reference
                envelope.primary.terms["modal_parent_key"] = modal_parent_key
                logger.debug(
                    f"📝 Stored modal parent key {modal_parent_key} "
                    f"in terms (key hint: {key_hint})"
                )

            # Selective modal parent key conversion: Only when strong modal
            # evidence AND no key hint. Avoid conversion for ambiguous cases
            # that could be analyzed functionally
            if not key_hint:
                modal_conf = getattr(envelope.primary, "modal_confidence", 0.0) or 0.0
                func_conf = (
                    getattr(envelope.primary, "functional_confidence", 0.0) or 0.0
                )

                # Only convert for specific modal patterns that clearly benefit
                # from parent key context
                # Avoid conversion for ambiguous patterns that could be
                # analyzed functionally
                should_convert = (
                    modal_conf > 0.6
                    and func_conf < 0.1  # Strong modal evidence, weak functional
                    and any(
                        pattern in str(envelope.primary.patterns)
                        for pattern in ["phrygian", "dorian"]
                    )  # Specific modal patterns
                    and len(chords or [])
                    <= 3  # Short progressions that clearly establish mode
                )
                if should_convert:
                    modal_parent_key = self._convert_to_modal_parent_key(
                        mode_label, context.key or "C major"
                    )
                    if modal_parent_key != context.key:
                        logger.debug(
                            f"🎭 Applying conditional modal parent key conversion: "
                            f"{context.key} → {modal_parent_key} "
                            f"(modal_conf={modal_conf:.2f} > "
                            f"func_conf={func_conf:.2f})"
                        )

                        # Re-analyze with corrected parent key
                        try:
                            # Re-derive roman numerals with corrected parent key
                            modal_romans = []
                            for chord in chords or []:
                                roman = romanize_chord(chord, modal_parent_key, profile)
                                roman = roman.replace("b", "♭")
                                modal_romans.append(roman)

                            # Create new context with modal parent key
                            modal_context = AnalysisContext(
                                key=modal_parent_key,
                                chords=chords or [],
                                roman_numerals=modal_romans,
                                melody=context.melody,
                                scales=context.scales,
                                metadata=context.metadata,
                                sections=context.sections,
                            )

                            # Re-run analysis with modal parent key
                            modal_envelope = self.engine.analyze(modal_context)
                            if modal_envelope.primary:
                                envelope = modal_envelope
                                logger.debug(
                                    f"🎵 Re-analyzed with modal parent "
                                    f"{modal_parent_key}: {chords} → {modal_romans}"
                                )

                        except Exception as e:
                            logger.warning(
                                f"⚠️ Failed to re-analyze with modal parent key: {e}"
                            )
                            # Keep original analysis if re-analysis fails

        # Victory lap: apply quality-gated calibration if available
        if self.calibrator and self.calibration_mapping and envelope.primary:
            try:
                # Apply modern calibration with quality gates
                calibrated_confidence = self.calibration_mapping.apply(
                    envelope.primary.confidence
                )
                envelope.primary.confidence = calibrated_confidence
                logger.debug(
                    f"🎯 Applied quality-gated calibration: "
                    f"{envelope.primary.confidence:.3f}"
                )
            except Exception as e:
                logger.warning(f"⚠️ Quality-gated calibration failed: {e}")

        # Final enhancement: populate scale/melody summaries if available
        if envelope.primary:
            envelope.primary = self._enhance_summary_with_scale_melody(
                envelope.primary, scale_analysis_data, melody_analysis_data
            )

        # Victory lap: log telemetry for completed analysis
        end_time = time.perf_counter()
        analysis_time_ms = (end_time - start_time) * 1000

        # Log scale/melody summary generation
        if envelope.primary:
            if (
                hasattr(envelope.primary, "scale_summary")
                and envelope.primary.scale_summary
            ):
                self.telemetry.log_scale_summary_generation(
                    session_id, envelope.primary.scale_summary
                )
            if (
                hasattr(envelope.primary, "melody_summary")
                and envelope.primary.melody_summary
            ):
                self.telemetry.log_melody_summary_generation(
                    session_id, envelope.primary.melody_summary
                )

            # Log confidence scores
            self.telemetry.log_confidence_scores(session_id, envelope.primary)

        # Log evidence generation
        if envelope.evidence:
            self.telemetry.log_evidence_generation(session_id, envelope.evidence)

        # Log completion
        self.telemetry.log_analysis_complete(session_id, analysis_time_ms, envelope)

        return envelope

    def analyze_with_patterns(
        self,
        chords: Optional[List[str]] = None,
        key_hint: Optional[str] = None,
        profile: str = "classical",
        options: Optional[Any] = None,
        romans: Optional[List[str]] = None,
        notes: Optional[List[str]] = None,
        melody: Optional[List[str]] = None,
    ) -> AnalysisEnvelope:
        """
        Synchronous wrapper for analyze_with_patterns_async.

        This looks odd, but it saves us from async complexity in sync contexts.
        """
        import asyncio

        # Opening move: check if we're already in an event loop
        try:
            asyncio.get_running_loop()
            # If we're in a loop, we need to run in a thread to avoid blocking
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.analyze_with_patterns_async(
                        chords, key_hint, profile, options, romans, notes, melody
                    ),
                )
                return future.result()
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            return asyncio.run(
                self.analyze_with_patterns_async(
                    chords, key_hint, profile, options, romans, notes, melody
                )
            )

    # Additional compatibility methods can be added here as needed
    # These would delegate to the unified engine with appropriate conversions

    def get_analysis_summary(self, envelope: AnalysisEnvelope) -> AnalysisSummary:
        """Generate analysis summary from envelope (compatibility method)."""
        if not envelope.primary:
            return AnalysisSummary(
                type=AnalysisType.FUNCTIONAL, roman_numerals=[], confidence=0.0
            )

        # Opening move: use correct AnalysisSummary constructor based on DTO definition
        return AnalysisSummary(
            type=envelope.primary.type,
            roman_numerals=getattr(envelope.primary, "roman_numerals", []),
            confidence=envelope.primary.confidence,
            key_signature=getattr(envelope.primary, "key_signature", None),
            mode=getattr(envelope.primary, "mode", None),
            reasoning=getattr(envelope.primary, "reasoning", None),
            patterns=getattr(envelope.primary, "patterns", []),
            chromatic_elements=getattr(envelope.primary, "chromatic_elements", []),
            modal_characteristics=getattr(
                envelope.primary, "modal_characteristics", []
            ),
        )

    def _detect_mode_label(
        self, roman_numerals: List[str], key: Optional[str], chords: List[str]
    ) -> Optional[str]:
        """
        Iteration 9B: Enhanced modal tonic detection and mode labeling.

        Analyzes both roman numeral signatures and chord progressions to detect
        the actual modal tonic and generate accurate mode labels.

        Args:
            roman_numerals: List of roman numerals
            key: Inferred key signature (parent key)
            chords: Original chord progression

        Returns:
            Mode label string or None if no clear modal signature detected
        """
        if not roman_numerals or not key or not chords:
            return None

        # Opening move: extract parent key information
        key_parts = key.split()
        if len(key_parts) < 2:
            return None

        key_type = key_parts[1].lower()  # "major" or "minor"

        # Big play: detect modal tonic from chord progression
        modal_tonic = self._detect_modal_tonic(chords, roman_numerals, key)

        # Join roman numerals for signature detection
        # Keep original case for contextless patterns
        roman_signature_upper = " ".join(roman_numerals).upper()

        # Time to tackle the tricky bit: enhanced modal signature detection
        mode_signatures = {
            "mixolydian": ["♭VII", "BVII"],
            "dorian": [
                "VI",
                "♯VI",
                "II",
                "IV",
            ],  # Natural 6, raised 2 (IV not iv for uppercase)
            "phrygian": ["♭II", "BII", "♭III"],  # Fixed case consistency
            "lydian": ["♭V", "BV", "♯IV", "#IV"],
            "aeolian": ["V", "♭VI", "♭VII"],  # Natural minor characteristics (V not v)
            "locrian": [
                "♭II",
                "♭V",
                "II°",
                "V°",
            ],  # Diminished characteristics (uppercase)
        }

        # Victory lap: detect mode based on signatures and context
        # Split roman signature into individual numerals for exact matching
        roman_numerals_upper = [r.strip() for r in roman_signature_upper.split()]
        for mode_name, signatures in mode_signatures.items():
            if any(sig in roman_numerals_upper for sig in signatures):
                # Additional context checks for accuracy
                if mode_name == "mixolydian":
                    if key_type == "major" and (
                        "I" in roman_signature_upper
                        or any("m" not in c for c in chords[:2])
                    ):
                        return f"{modal_tonic} Mixolydian"
                elif mode_name == "dorian":
                    if any(r == "i" for r in roman_numerals) or any(
                        "m" in c and "maj" not in c for c in chords[:2]
                    ):
                        return f"{modal_tonic} Dorian"
                elif mode_name == "phrygian":
                    if key_type == "minor" or any(
                        "m" in c and "maj" not in c for c in chords[:2]
                    ):
                        return f"{modal_tonic} Phrygian"
                elif mode_name == "lydian":
                    if key_type == "major" and (
                        "I" in roman_signature_upper
                        or any("m" not in c for c in chords[:2])
                    ):
                        return f"{modal_tonic} Lydian"
                elif mode_name == "aeolian":
                    if key_type == "minor" and any(r == "i" for r in roman_numerals):
                        return f"{modal_tonic} Aeolian"
                elif mode_name == "locrian":
                    if "♭II" in roman_signature_upper and (
                        "♭V" in roman_signature_upper or "V°" in roman_signature_upper
                    ):
                        return f"{modal_tonic} Locrian"

        # Check for simple modal loops (contextless patterns)
        if len(roman_numerals) <= 4 and len(set(roman_numerals)) <= 3:
            if any(r == "I" for r in roman_numerals_upper) and any(
                r == "♭VII" for r in roman_numerals_upper
            ):
                return f"{modal_tonic} Mixolydian"
            elif any(r == "i" for r in roman_numerals) and any(
                r == "♭II" for r in roman_numerals_upper
            ):
                return f"{modal_tonic} Phrygian"
            elif any(r == "I" for r in roman_numerals_upper) and any(
                r == "♭II" for r in roman_numerals_upper
            ):
                return f"{modal_tonic} Locrian"
            elif any(r == "i" for r in roman_numerals) and any(
                r == "IV" for r in roman_numerals_upper
            ):
                return f"{modal_tonic} Dorian"
            elif any(r == "I" for r in roman_numerals_upper) and any(
                r == "♯IV" for r in roman_numerals_upper
            ):
                return f"{modal_tonic} Lydian"

        return None

    def _convert_to_modal_parent_key(self, mode_label: str, current_key: str) -> str:
        """
        Convert a local key to the appropriate modal parent key.

        For example:
        - "E Phrygian" with current_key "E minor" → "C major" (E is 3rd of C)
        - "G Mixolydian" with current_key "G major" → "C major" (G is 5th of C)
        - "D Dorian" with current_key "D minor" → "C major" (D is 2nd of C)

        Args:
            mode_label: Mode string like "E Phrygian", "G Mixolydian"
            current_key: Current inferred key like "E minor", "G major"

        Returns:
            Modal parent key (e.g., "C major")
        """
        if not mode_label or not current_key:
            return current_key

        try:
            # Extract modal tonic and mode name
            parts = mode_label.split()
            if len(parts) < 2:
                return current_key

            modal_tonic = parts[0].replace(
                "°", ""
            )  # Remove diminished symbol if present
            mode_name = parts[1].lower()

            # Mode interval mappings (semitones to subtract from modal
            # tonic to get parent tonic)
            mode_intervals = {
                "ionian": 0,  # C Ionian = C major (C - 0 = C)
                "dorian": 2,  # D Dorian = C major (D - 2 = C)
                "phrygian": 4,  # E Phrygian = C major (E - 4 = C)
                "lydian": 5,  # F Lydian = C major (F - 5 = C)
                "mixolydian": 7,  # G Mixolydian = C major (G - 7 = C)
                "aeolian": 9,  # A Aeolian = C major (A - 9 = C)
                "locrian": 11,  # B Locrian = C major (B - 11 = C)
            }

            if mode_name not in mode_intervals:
                return current_key

            # Convert modal tonic to parent tonic
            interval = mode_intervals[mode_name]
            parent_tonic = self._transpose_note(
                modal_tonic, -interval
            )  # Subtract semitones

            # Modal analysis always uses major parent keys in our system

            parent_key = f"{parent_tonic} major"
            return canonicalize_key_signature(parent_key)

        except Exception as e:
            logger.warning(
                f"⚠️ Failed to convert modal parent key for {mode_label}: {e}"
            )
            return current_key

    def _detect_modal_tonic(
        self, chords: List[str], roman_numerals: List[str], key: str
    ) -> str:
        """
        Detect the actual modal tonic from chord progression.

        Args:
            chords: Chord progression
            roman_numerals: Roman numeral analysis
            key: Parent key signature

        Returns:
            Modal tonic note
        """
        if not chords:
            # Fallback to parent key tonic
            return key.split()[0] if key else "C"

        # Opening move: start with first chord as potential tonic
        first_chord = chords[0]
        first_root = (
            first_chord.split("/")[0]
            .replace("m", "")
            .split("7")[0]
            .split("sus")[0]
            .strip()
        )

        # Big play: look for tonic indicators
        # 1. First chord often indicates tonic in modal progressions
        # 2. Repeated or emphasized chords
        # 3. Harmonic stability patterns

        chord_counts: Dict[str, int] = {}
        for chord in chords:
            root = (
                chord.split("/")[0]
                .replace("m", "")
                .split("7")[0]
                .split("sus")[0]
                .strip()
            )
            chord_counts[root] = chord_counts.get(root, 0) + 1

        # Most frequent chord root is likely tonic
        most_frequent = max(chord_counts.items(), key=lambda x: x[1])[0]

        # Prefer first chord if it's reasonably frequent
        if chord_counts.get(first_root, 0) >= max(1, len(chords) // 3):
            return first_root
        else:
            return most_frequent

    def _normalize_lydian_romans(
        self, roman_numerals: List[str], key: Optional[str]
    ) -> List[str]:
        """
        Iteration 9B: Context-aware modal roman numeral normalization.

        Transforms roman numerals based on modal context:
        - Lydian: ♭V → ♯IV when context indicates #4
        - Locrian: Preserves ♭II/♭V for pattern matching
        - Other modes: Preserves original spelling

        Args:
            roman_numerals: List of roman numerals to normalize
            key: Key signature context

        Returns:
            Normalized roman numerals with mode-appropriate spelling
        """
        if not roman_numerals or not key:
            return roman_numerals

        # Opening move: detect modal context from roman signatures
        modal_context = self._detect_modal_context(roman_numerals, key)

        normalized = []
        for roman in roman_numerals:
            # Big play: apply context-aware transformations
            if modal_context == "lydian":
                # Transform ♭V to ♯IV for Lydian pattern matching
                if roman == "♭V" or roman == "bV":
                    normalized_roman = "♯IV"
                    normalized.append(normalized_roman)
                    logger.debug(
                        f"🎼 Lydian normalization: {roman} → {normalized_roman}"
                    )
                elif (
                    roman.startswith("♭V")
                    and len(roman) > 2
                    and not roman.startswith("♭VII")
                ):
                    extensions = roman[2:]
                    normalized_roman = f"♯IV{extensions}"
                    normalized.append(normalized_roman)
                    logger.debug(
                        f"🎼 Lydian normalization: {roman} → {normalized_roman}"
                    )
                elif (
                    roman.startswith("bV")
                    and len(roman) > 2
                    and not roman.startswith("bVII")
                ):
                    extensions = roman[2:]
                    normalized_roman = f"♯IV{extensions}"
                    normalized.append(normalized_roman)
                    logger.debug(
                        f"🎼 Lydian normalization: {roman} → {normalized_roman}"
                    )
                else:
                    normalized.append(roman)
            elif modal_context == "locrian":
                # Preserve ♭II/♭V spelling for Locrian patterns
                # Ensure consistent flat notation
                if roman.startswith("bII"):
                    normalized.append(roman.replace("bII", "♭II", 1))
                elif roman.startswith("bV") and not roman.startswith("bVII"):
                    normalized.append(roman.replace("bV", "♭V", 1))
                else:
                    normalized.append(roman)
            else:
                # Other modal contexts or functional - preserve original
                normalized.append(roman)

        return normalized

    def _detect_modal_context(
        self, roman_numerals: List[str], key: Optional[str]
    ) -> Optional[str]:
        """
        Detect modal context from roman numeral patterns.

        Args:
            roman_numerals: List of roman numerals
            key: Key signature

        Returns:
            Modal context name or None
        """
        if not roman_numerals:
            return None

        roman_signature = " ".join(roman_numerals).upper()
        key_parts = key.split() if key else []
        key_type = key_parts[1].lower() if len(key_parts) > 1 else "major"

        # Time to tackle the tricky bit: context detection
        if key_type == "major":
            # Check for Lydian signatures (#4)
            if (
                any(sig in roman_signature for sig in ["♭V", "BV"])
                and "I" in roman_signature
            ):
                return "lydian"
            # Check for Locrian signatures (from major parent)
            elif any(sig in roman_signature for sig in ["VII", "♭II"]) and not any(
                sig in roman_signature for sig in ["♭VII"]
            ):
                return "locrian"
        else:  # minor key
            # Check for Locrian from minor context
            if (
                any(sig in roman_signature for sig in ["♭II", "♭V"])
                and "i" in roman_signature
            ):
                return "locrian"

        return None

    def _infer_key_from_progression(self, chords: List[str]) -> str:
        """
        Iteration 9B: Advanced key inference analyzing chord quality
        and modal signatures.

        Analyzes the opening chord quality and looks for modal signatures
        to infer the most appropriate key context, keeping modal vamps
        rooted on their tonic.

        Args:
            chords: List of chord symbols

        Returns:
            Inferred key signature string (e.g., "D minor", "C major")
        """
        if not chords:
            return "C major"

        first_chord = chords[0]
        common_keys = ["C", "F", "G", "D", "A", "E", "Bb", "Eb", "Ab", "Db", "F#", "B"]

        # Opening move: analyze first chord quality
        def extract_root_and_quality(chord: str) -> tuple[str, str]:
            """Extract root note and quality from chord symbol."""
            # Handle slash chords (e.g., A/C)
            base_chord = chord.split("/")[0]

            # Check for explicit minor
            if "m" in base_chord and "maj" not in base_chord.lower():
                # Extract root by removing 'm' and any numbers/extensions
                root = (
                    base_chord.replace("m", "")
                    .split("7")[0]
                    .split("9")[0]
                    .split("11")[0]
                    .split("13")[0]
                )
                return root.strip(), "minor"
            else:
                # Major or unspecified (treat as major)
                root = (
                    base_chord.split("7")[0]
                    .split("9")[0]
                    .split("maj")[0]
                    .split("sus")[0]
                    .split("add")[0]
                )
                return root.strip(), "major"

        first_root, first_quality = extract_root_and_quality(first_chord)

        # Big play: look for modal signatures in the progression
        modal_signatures = self._detect_modal_signatures(chords)

        # Time to tackle the tricky bit: key inference based on chord analysis
        if first_quality == "minor" and first_root in common_keys:
            # Iteration 9C: Enhanced functional vs modal detection for
            # minor opening chords

            # Check if this might be a functional progression in a major key
            functional_major_key = self._detect_functional_major_key(chords)

            if functional_major_key:
                # Strong evidence for functional progression in major key
                inferred_key = functional_major_key
            elif "lydian" in modal_signatures or any(
                "b" in c.lower() or "#" in c.lower() for c in chords[1:]
            ):
                # Evidence of modal alteration - use minor key context
                inferred_key = f"{first_root} minor"
            else:
                # Simple minor context (could be modal or functional minor)
                inferred_key = f"{first_root} minor"
        elif modal_signatures:
            # Modal signatures detected - but check for functional patterns first

            # Iteration 9C: Even with modal signatures, check for functional patterns
            functional_major_key = self._detect_functional_major_key(chords)

            if functional_major_key:
                # Strong evidence for functional progression overrides
                # weak modal signatures
                inferred_key = functional_major_key
            else:
                # Use modal signature heuristics
                if first_root in common_keys:
                    if "lydian" in modal_signatures or "mixolydian" in modal_signatures:
                        # Use major parent for Lydian/Mixolydian
                        inferred_key = f"{first_root} major"
                    else:
                        # Use minor parent for Dorian/Phrygian
                        inferred_key = f"{first_root} minor"
                else:
                    # Fallback to C major
                    inferred_key = "C major"
        else:
            # No clear modal signatures - use conventional heuristics

            # Iteration 9C: Check for functional patterns (including those
            # starting with major chords)
            functional_major_key = self._detect_functional_major_key(chords)

            if functional_major_key:
                # Strong evidence for functional progression in major key
                inferred_key = functional_major_key
            else:
                # Fall back to conventional heuristics
                last_chord = chords[-1] if len(chords) > 1 else chords[0]
                last_root, last_quality = extract_root_and_quality(last_chord)

                if last_root in common_keys and last_quality == "major":
                    # Final chord heuristic for functional progressions
                    inferred_key = f"{last_root} major"
                elif first_root in common_keys:
                    # First chord heuristic
                    quality = "minor" if first_quality == "minor" else "major"
                    inferred_key = f"{first_root} {quality}"
                else:
                    # Default fallback
                    inferred_key = "C major"

        return inferred_key

    def _detect_modal_signatures(self, chords: List[str]) -> List[str]:
        """
        Detect modal signatures in chord progression.

        Args:
            chords: List of chord symbols

        Returns:
            List of detected modal signature names
        """
        signatures = []

        # Look for specific modal indicators
        chord_str = " ".join(chords).upper()

        # Lydian signatures: #4 intervals (represented as b5 from root)
        if "GB" in chord_str and "C" in chord_str:  # Gb in C context suggests Lydian
            signatures.append("lydian")

        # Mixolydian signatures: b7 intervals
        if any(
            pair in [("C", "BB"), ("G", "F"), ("D", "C")]
            for pair in zip(chords, chords[1:])
            if len(chords) > 1
        ):
            signatures.append("mixolydian")

        # Dorian signatures: natural 6 in minor context
        minor_chords = [c for c in chords if "m" in c and "maj" not in c.lower()]
        if minor_chords:
            signatures.append("dorian")

        # Phrygian signatures: b2 intervals
        if any(
            pair in [("AM", "BB"), ("DM", "EB")]
            for pair in zip(chords, chords[1:])
            if len(chords) > 1
        ):
            signatures.append("phrygian")

        return signatures

    def _detect_functional_major_key(self, chords: List[str]) -> Optional[str]:
        """
        Iteration 9C: Detect if a minor-opening progression is actually
        functional in a major key.

        Analyzes chord progressions starting with minor chords to determine
        if they're better understood as functional progressions in a related
        major key.

        Args:
            chords: List of chord symbols

        Returns:
            Major key signature if functional evidence found, None otherwise
        """
        if len(chords) < 3:
            return None  # Need at least 3 chords for functional analysis

        # Extract chord roots for analysis
        def get_root(chord: str) -> str:
            return (
                chord.split("/")[0].replace("m", "").split("7")[0].split("9")[0].strip()
            )

        roots = [get_root(chord) for chord in chords]

        # Common functional patterns starting with minor chords:
        # 1. vi-ii-V-I: minor chord followed by ii-V-I cadence
        # 2. vi-IV-I-V: minor chord followed by plagal motion
        # 3. vi-V-I: minor chord to dominant resolution

        # Look for cadential motion patterns
        if len(chords) >= 4:
            # Pattern: vi-ii-V-I (Am-Dm-G-C = vi-ii-V-I in C major)
            if self._matches_vi_ii_V_I_pattern(roots):
                # Last chord is likely tonic of major key
                return f"{roots[-1]} major"

            # Pattern: vi-IV-I-V (F#m-D-A-E = vi-IV-I-V in A major)
            if self._matches_vi_IV_I_V_pattern(roots):
                # Third chord is likely tonic of major key
                return f"{roots[2]} major"

        if len(chords) >= 3:
            # Pattern: vi-V-I (Am-G-C = vi-V-I in C major)
            if self._matches_vi_V_I_pattern(roots):
                return f"{roots[-1]} major"

            # Pattern: vi-IV-I (Am-F-C = vi-IV-I in C major)
            if self._matches_vi_IV_I_pattern(roots):
                return f"{roots[-1]} major"

            # Pattern: IV-V-vi (F-G-Am = IV-V-vi in C major - deceptive cadence)
            if self._matches_IV_V_vi_pattern(roots):
                # The vi chord (Am) is the 6th degree, so tonic is up a minor 3rd
                minor_third_up = self._transpose_note(
                    roots[-1], 3
                )  # 3 semitones = minor 3rd
                return f"{minor_third_up} major"

        return None

    def _matches_vi_ii_V_I_pattern(self, roots: List[str]) -> bool:
        """Check if roots match vi-ii-V-I pattern in some major key."""
        if len(roots) < 4:
            return False

        # Check if it follows circle of fifths: vi -> ii -> V -> I
        # Example: A -> D -> G -> C (vi-ii-V-I in C major)
        try:
            # Calculate intervals (in semitones)
            def note_to_semitone(note: str) -> int:
                notes = {
                    "C": 0,
                    "C#": 1,
                    "DB": 1,
                    "D": 2,
                    "D#": 3,
                    "EB": 3,
                    "E": 4,
                    "F": 5,
                    "F#": 6,
                    "GB": 6,
                    "G": 7,
                    "G#": 8,
                    "AB": 8,
                    "A": 9,
                    "A#": 10,
                    "BB": 10,
                    "B": 11,
                }
                return notes.get(note.upper(), 0)

            # vi-ii: should be up a perfect 4th (5 semitones)
            interval1 = (note_to_semitone(roots[1]) - note_to_semitone(roots[0])) % 12
            # ii-V: should be up a perfect 4th (5 semitones)
            interval2 = (note_to_semitone(roots[2]) - note_to_semitone(roots[1])) % 12
            # V-I: should be up a perfect 4th (5 semitones)
            interval3 = (note_to_semitone(roots[3]) - note_to_semitone(roots[2])) % 12

            return interval1 == 5 and interval2 == 5 and interval3 == 5

        except (KeyError, IndexError):
            return False

    def _matches_vi_IV_I_V_pattern(self, roots: List[str]) -> bool:
        """Check if roots match vi-IV-I-V pattern in some major key."""
        if len(roots) < 4:
            return False

        # Check relative positions for vi-IV-I-V
        # Example: F# -> D -> A -> E (vi-IV-I-V in A major)
        try:

            def note_to_semitone(note: str) -> int:
                notes = {
                    "C": 0,
                    "C#": 1,
                    "DB": 1,
                    "D": 2,
                    "D#": 3,
                    "EB": 3,
                    "E": 4,
                    "F": 5,
                    "F#": 6,
                    "GB": 6,
                    "G": 7,
                    "G#": 8,
                    "AB": 8,
                    "A": 9,
                    "A#": 10,
                    "BB": 10,
                    "B": 11,
                }
                return notes.get(note.upper(), 0)

            # vi-IV: should be down a minor 6th (8 semitones up = 4 down)
            interval1 = (note_to_semitone(roots[1]) - note_to_semitone(roots[0])) % 12
            # IV-I: should be up a perfect 5th (7 semitones)
            interval2 = (note_to_semitone(roots[2]) - note_to_semitone(roots[1])) % 12
            # I-V: should be up a perfect 5th (7 semitones)
            interval3 = (note_to_semitone(roots[3]) - note_to_semitone(roots[2])) % 12

            return interval1 == 8 and interval2 == 7 and interval3 == 7

        except (KeyError, IndexError):
            return False

    def _matches_vi_V_I_pattern(self, roots: List[str]) -> bool:
        """Check if roots match vi-V-I pattern in some major key."""
        if len(roots) < 3:
            return False

        try:

            def note_to_semitone(note: str) -> int:
                notes = {
                    "C": 0,
                    "C#": 1,
                    "DB": 1,
                    "D": 2,
                    "D#": 3,
                    "EB": 3,
                    "E": 4,
                    "F": 5,
                    "F#": 6,
                    "GB": 6,
                    "G": 7,
                    "G#": 8,
                    "AB": 8,
                    "A": 9,
                    "A#": 10,
                    "BB": 10,
                    "B": 11,
                }
                return notes.get(note.upper(), 0)

            # vi-V: should be down a major 2nd (10 semitones up = 2 down)
            interval1 = (note_to_semitone(roots[1]) - note_to_semitone(roots[0])) % 12
            # V-I: should be up a perfect 4th (5 semitones)
            interval2 = (note_to_semitone(roots[2]) - note_to_semitone(roots[1])) % 12

            return interval1 == 10 and interval2 == 5

        except (KeyError, IndexError):
            return False

    def _matches_vi_IV_I_pattern(self, roots: List[str]) -> bool:
        """Check if roots match vi-IV-I pattern in some major key."""
        if len(roots) < 3:
            return False

        try:

            def note_to_semitone(note: str) -> int:
                notes = {
                    "C": 0,
                    "C#": 1,
                    "DB": 1,
                    "D": 2,
                    "D#": 3,
                    "EB": 3,
                    "E": 4,
                    "F": 5,
                    "F#": 6,
                    "GB": 6,
                    "G": 7,
                    "G#": 8,
                    "AB": 8,
                    "A": 9,
                    "A#": 10,
                    "BB": 10,
                    "B": 11,
                }
                return notes.get(note.upper(), 0)

            # vi-IV: should be down a minor 6th (8 semitones up = 4 down)
            interval1 = (note_to_semitone(roots[1]) - note_to_semitone(roots[0])) % 12
            # IV-I: should be up a perfect 5th (7 semitones)
            interval2 = (note_to_semitone(roots[2]) - note_to_semitone(roots[1])) % 12

            return interval1 == 8 and interval2 == 7

        except (KeyError, IndexError):
            return False

    def _matches_IV_V_vi_pattern(self, roots: List[str]) -> bool:
        """Check if roots match IV-V-vi pattern in some major key
        (deceptive cadence)."""
        if len(roots) < 3:
            return False

        try:

            def note_to_semitone(note: str) -> int:
                notes = {
                    "C": 0,
                    "C#": 1,
                    "DB": 1,
                    "D": 2,
                    "D#": 3,
                    "EB": 3,
                    "E": 4,
                    "F": 5,
                    "F#": 6,
                    "GB": 6,
                    "G": 7,
                    "G#": 8,
                    "AB": 8,
                    "A": 9,
                    "A#": 10,
                    "BB": 10,
                    "B": 11,
                }
                return notes.get(note.upper(), 0)

            # IV-V: should be up a whole step (2 semitones)
            interval1 = (note_to_semitone(roots[1]) - note_to_semitone(roots[0])) % 12
            # V-vi: should be up a whole step (2 semitones)
            interval2 = (note_to_semitone(roots[2]) - note_to_semitone(roots[1])) % 12

            return interval1 == 2 and interval2 == 2

        except (KeyError, IndexError):
            return False

    def _transpose_note(self, note: str, semitones: int) -> str:
        """
        Transpose a note by a given number of semitones.

        TODO: get this hardcoding out of here and into the constants utils or just
        remove it if it's not needed.
        """
        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        note_to_index = {
            "C": 0,
            "C#": 1,
            "DB": 1,
            "D": 2,
            "D#": 3,
            "EB": 3,
            "E": 4,
            "F": 5,
            "F#": 6,
            "GB": 6,
            "G": 7,
            "G#": 8,
            "AB": 8,
            "A": 9,
            "A#": 10,
            "BB": 10,
            "B": 11,
        }

        current_index = note_to_index.get(note.upper(), 0)
        new_index = (current_index + semitones) % 12
        return notes[new_index]

    def _enhance_summary_with_scale_melody(
        self,
        summary: AnalysisSummary,
        scale_data: Optional[Dict[str, Any]] = None,
        melody_data: Optional[Dict[str, Any]] = None,
    ) -> AnalysisSummary:
        """
        Enhance AnalysisSummary with scale and melody summaries when available.

        Args:
            summary: Original analysis summary
            scale_data: Scale analysis data from normalize_scale_input
            melody_data: Melody analysis data from normalize_melody_input

        Returns:
            Enhanced summary with scale_summary and melody_summary populated
        """
        from harmonic_analysis.dto import MelodySummaryDTO, ScaleSummaryDTO

        # Battle-hardened defense: avoid mutation, create new summary
        enhanced_summary = AnalysisSummary(
            type=summary.type,
            roman_numerals=summary.roman_numerals,
            confidence=summary.confidence,
            key_signature=summary.key_signature,
            mode=summary.mode,
            reasoning=summary.reasoning,
            functional_confidence=summary.functional_confidence,
            modal_confidence=summary.modal_confidence,
            chromatic_confidence=summary.chromatic_confidence,
            terms=summary.terms,
            patterns=summary.patterns,
            chromatic_elements=summary.chromatic_elements,
            chromatic_summary=summary.chromatic_summary,
            chords=summary.chords,
            modal_characteristics=summary.modal_characteristics,
            modal_evidence=summary.modal_evidence,
            sections=summary.sections,
            terminal_cadences=summary.terminal_cadences,
            final_cadence=summary.final_cadence,
        )

        # Main play: populate scale summary if scale data available
        if scale_data and scale_data.get("is_valid"):
            # Extract mode and parent key from key_info structure
            key_info = scale_data.get("key_info", {})
            detected_mode = scale_data.get("detected_mode") or key_info.get("mode")

            enhanced_summary.scale_summary = ScaleSummaryDTO(
                detected_mode=detected_mode,
                parent_key=key_info.get("parent_key"),
                degrees=scale_data.get("scale_degrees", []),
                characteristic_notes=self._extract_characteristic_notes(scale_data),
                notes=scale_data.get("canonical_notes", []),
            )

        # Follow-up play: populate melody summary if melody data available
        if melody_data and melody_data.get("notes"):
            enhanced_summary.melody_summary = MelodySummaryDTO(
                intervals=melody_data.get("intervals", []),
                contour=self._determine_melodic_contour(
                    melody_data.get("intervals", [])
                ),
                range_semitones=self._calculate_melodic_range(
                    melody_data.get("intervals", [])
                ),
                leading_tone_resolutions=self._count_leading_tone_resolutions(
                    melody_data
                ),
                melodic_characteristics=self._extract_melodic_characteristics(
                    melody_data
                ),
            )

        return enhanced_summary

    def _extract_characteristic_notes(self, scale_data: Dict[str, Any]) -> List[str]:
        """Extract characteristic intervallic features from scale data."""
        characteristics = []
        # Get mode from multiple possible sources
        key_info = scale_data.get("key_info", {})
        mode = (
            scale_data.get("detected_mode")
            or key_info.get("mode")
            or scale_data.get("mode", "")
        ).lower()

        # Victory lap: map mode-specific characteristic intervals
        if "dorian" in mode:
            characteristics.append("♭3")
            characteristics.append("♮6")
        elif "phrygian" in mode:
            characteristics.append("♭2")
            characteristics.append("♭3")
        elif "mixolydian" in mode:
            characteristics.append("♭7")
        elif "lydian" in mode:
            characteristics.append("♯4")
        elif "aeolian" in mode:
            characteristics.append("♭3")
            characteristics.append("♭6")
            characteristics.append("♭7")
        elif "locrian" in mode:
            characteristics.append("♭2")
            characteristics.append("♭5")

        return characteristics

    def _determine_melodic_contour(self, intervals: List[int]) -> str:
        """Analyze melodic contour from interval sequence."""
        if not intervals:
            return "static"

        positive_count = sum(1 for i in intervals if i > 0)
        negative_count = sum(1 for i in intervals if i < 0)

        if positive_count > negative_count * 2:
            return "ascending"
        elif negative_count > positive_count * 2:
            return "descending"
        elif abs(positive_count - negative_count) <= 1:
            return "wave"
        else:
            return "arch" if positive_count > negative_count else "valley"

    def _calculate_melodic_range(self, intervals: List[int]) -> int:
        """Calculate total melodic range in semitones."""
        if not intervals:
            return 0

        # Track cumulative position and find min/max
        position = 0
        min_pos = 0
        max_pos = 0

        for interval in intervals:
            position += interval
            min_pos = min(min_pos, position)
            max_pos = max(max_pos, position)

        return max_pos - min_pos

    def _count_leading_tone_resolutions(self, melody_data: Dict[str, Any]) -> int:
        """Count semitone upward resolutions (leading tone patterns)."""
        intervals = melody_data.get("intervals", [])
        return sum(1 for interval in intervals if interval == 1)

    def _extract_melodic_characteristics(
        self, melody_data: Dict[str, Any]
    ) -> List[str]:
        """Extract melodic characteristics from analysis data."""
        characteristics = []
        intervals = melody_data.get("intervals", [])

        if not intervals:
            return characteristics

        # Stepwise motion analysis
        stepwise_count = sum(1 for i in intervals if abs(i) <= 2)
        if stepwise_count / len(intervals) > 0.7:
            characteristics.append("stepwise motion")

        # Leap emphasis analysis
        leap_count = sum(1 for i in intervals if abs(i) >= 3)
        if leap_count / len(intervals) > 0.3:
            characteristics.append("leap emphasis")

        # Chromatic motion analysis
        chromatic_count = sum(1 for i in intervals if abs(i) == 1)
        if chromatic_count / len(intervals) > 0.4:
            characteristics.append("chromatic motion")

        return characteristics
