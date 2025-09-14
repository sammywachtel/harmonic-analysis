"""
Pattern Analysis Service - Clean async-first API with stable DTOs.

Follows the implementation specification from library_audit_todo_impl_details.md
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from typing import Any, Dict, List, Optional

from harmonic_analysis.dto import (
    AnalysisEnvelope,
    AnalysisSummary,
    AnalysisType,
    ChromaticElementDTO,
    FunctionalChordDTO,
    PatternMatchDTO,
    SectionDTO,
)

from ..core.functional_harmony import FunctionalHarmonyAnalyzer
from ..core.pattern_engine import (
    GlossaryService,
    Matcher,
    TokenConverter,
    load_library,
)
from ..core.utils.music_theory_constants import canonicalize_key_signature
from ..resources import load_patterns
from ..services.analysis_arbitration_service import (
    AnalysisArbitrationService,
)
from ..services.calibration_service import CalibrationService
from ..services.modal_analysis_service import ModalAnalysisService

# Set up logging for calibration observability
logger = logging.getLogger(__name__)


class PatternAnalysisService:
    """Service for pattern-based harmonic analysis with stable DTO output."""

    pattern_lib: Optional[Any]
    matcher: Optional[Any]

    def __init__(
        self,
        functional_analyzer: Optional[Any] = None,
        matcher: Optional[Any] = None,
        modal_analyzer: Optional[Any] = None,
        arbitration_policy: Optional[Any] = None,
        calibration_service: Optional[Any] = None,
        auto_calibrate: bool = True,
    ) -> None:
        # Existing wiring with optional dependency injection for testing
        self.functional_analyzer = functional_analyzer or FunctionalHarmonyAnalyzer()
        self.token_converter = TokenConverter()
        self.arbitration_service = AnalysisArbitrationService(arbitration_policy)
        self.glossary_service = GlossaryService()
        self.modal_analyzer = modal_analyzer or ModalAnalysisService()

        # Confidence calibration service integration
        self.calibration_service = calibration_service
        self.auto_calibrate = auto_calibrate

        # Try to load calibration service from default location if not provided
        if self.calibration_service is None and auto_calibrate:
            try:
                from pathlib import Path

                default_calibration_path = (
                    Path(__file__).parent.parent / "assets" / "calibration_mapping.json"
                )
                if default_calibration_path.exists():
                    self.calibration_service = CalibrationService(
                        str(default_calibration_path)
                    )
                    logger.info(
                        f"✅ Loaded calibration service from {default_calibration_path}"
                    )
                else:
                    logger.debug(
                        f"📂 No calibration mapping found at {default_calibration_path}"
                    )
            except Exception as e:
                # Graceful fallback - no calibration service available
                logger.warning(f"⚠️ Failed to load calibration service: {e}")
                self.calibration_service = None
        elif not auto_calibrate:
            logger.debug("🔧 Auto-calibration disabled")
        elif self.calibration_service:
            logger.info("✅ Using provided calibration service")

        # Load pattern library using importlib.resources
        try:
            import json
            import tempfile

            patterns_data = load_patterns()

            # Write patterns to temporary file for load_library to read
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(patterns_data, f)
                temp_path = f.name

            # Use existing load_library function
            self.pattern_lib = load_library(temp_path)
            self.matcher = matcher or Matcher(self.pattern_lib, profile="classical")

            # Clean up temp file
            import os

            os.unlink(temp_path)

        except (FileNotFoundError, ImportError) as e:
            print(f"Warning: Pattern library could not be loaded: {e}")
            self.pattern_lib = None
            self.matcher = None

    def _extract_calibration_features(
        self,
        chord_symbols: List[str],
        analysis_result: Any = None,
        pattern_matches: Optional[List[PatternMatchDTO]] = None,
        key_signature: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract routing features for confidence calibration.

        Args:
            chord_symbols: List of chord symbols analyzed
            analysis_result: Primary analysis result (functional/modal)
            pattern_matches: List of detected patterns
            key_signature: Detected key signature

        Returns:
            Dictionary of features for calibration routing
        """
        features = {
            "chord_count": len(chord_symbols),
            "is_melody": False,  # This service handles harmony analysis
        }

        # Compute outside-key ratio (chromatic elements)
        if key_signature and chord_symbols:
            try:
                # Simple heuristic: count chords with accidentals relative to key
                chord_str = " ".join(chord_symbols).lower()
                accidental_count = chord_str.count("#") + chord_str.count("b")
                features["outside_key_ratio"] = min(
                    1.0, accidental_count / max(1, len(chord_symbols))
                )
            except Exception:
                features["outside_key_ratio"] = 0.0
        else:
            features["outside_key_ratio"] = 0.0

        # Evidence strength based on analysis confidence or pattern count
        if analysis_result and hasattr(analysis_result, "confidence"):
            features["evidence_strength"] = float(analysis_result.confidence)
        elif pattern_matches:
            # Use pattern count as evidence proxy
            features["evidence_strength"] = min(1.0, len(pattern_matches) / 3.0)
        else:
            features["evidence_strength"] = 0.5

        # Detect I-V-I pattern (functional simplicity marker)
        if analysis_result and hasattr(analysis_result, "roman_numerals"):
            romans_str = " ".join(analysis_result.roman_numerals or []).lower()
            features["foil_I_V_I"] = any(
                pattern in romans_str for pattern in ["i v i", "i iv v i"]
            )
        else:
            features["foil_I_V_I"] = False

        # Modal characteristic markers
        chord_symbols_str = " ".join(chord_symbols).lower()
        features["has_flat7"] = "bb" in chord_symbols_str or "b7" in chord_symbols_str
        features["has_flat3"] = "eb" in chord_symbols_str or "b3" in chord_symbols_str
        features["has_flat6"] = "ab" in chord_symbols_str or "b6" in chord_symbols_str
        features["has_flat2"] = "db" in chord_symbols_str or "b2" in chord_symbols_str
        features["has_sharp4"] = "f#" in chord_symbols_str or "#4" in chord_symbols_str
        features["has_flat5"] = "gb" in chord_symbols_str or "b5" in chord_symbols_str

        # Chord density (complexity measure)
        total_chars = sum(len(chord) for chord in chord_symbols)
        features["chord_density"] = (
            total_chars / max(1, len(chord_symbols)) / 4.0
        )  # Normalize by avg chord length

        return features

    def _apply_section_aware_tagging(
        self,
        matches: List[PatternMatchDTO],
        sections: Optional[List[SectionDTO]],
        total_tokens: int,
    ) -> None:
        """Apply section-aware tagging as specified in music-alg-2g.md Section 4."""
        # Create set of section boundaries for efficient lookup
        section_ends = set()
        if sections:
            section_ends = {section.end for section in sections}

        for match in matches:
            # Set section label based on where the pattern ends
            if sections:
                for section in sections:
                    if section.start <= match.end - 1 < section.end:
                        match.section = section.id
                        break

            # Set cadence_role for cadences only
            if match.family and "cadence" in match.family.lower():
                if match.end == total_tokens:
                    match.cadence_role = "final"
                elif section_ends and match.end in section_ends:
                    match.cadence_role = "section-final"
                else:
                    match.cadence_role = "internal"

    def _add_abs_indices(self, matches: List[PatternMatchDTO]) -> None:
        """Add absolute chord indices to evidence for UI highlighting."""
        for m in matches:
            for ev in m.evidence:
                if isinstance(ev.get("step_index"), int):
                    ev["abs_index"] = m.start + ev["step_index"]

    def _attach_sections_and_resolve_cadences(
        self,
        matches: List[PatternMatchDTO],
        sections: Optional[List[SectionDTO]],
        total_len: int,
    ) -> tuple[List[PatternMatchDTO], Optional[PatternMatchDTO]]:
        """
        Returns (terminal_cadences, final_cadence)
        - Assigns section_id and closes_section on each match (in place).
        - terminal_cadences contains all cadence matches that close a section.
        - final_cadence is the cadence that ends on the last chord
          (max score tie-break).
        """

        # Section assignment is now handled by _apply_section_aware_tagging

        # Terminal cadences: cadential family + section-final or final cadence_role
        terminal = [m for m in matches if m.cadence_role in ["section-final", "final"]]

        # Final cadence: cadence ending at total_len
        finals = [m for m in matches if m.cadence_role == "final"]
        final_cadence = max(finals, key=lambda x: x.score) if finals else None

        return terminal, final_cadence

    # --- NEW: async entrypoint ---
    async def analyze_with_patterns_async(
        self,
        chord_symbols: List[str],
        profile: str = "classical",
        best_cover: bool = True,
        key_hint: Optional[str] = None,
        sections: Optional[List[SectionDTO]] = None,
    ) -> AnalysisEnvelope:
        """
        Analyze chord progression using pattern engine (async version).

        Args:
            chord_symbols: List of chord symbols (e.g., ['Am', 'F', 'C', 'G'])
            profile: Analysis profile ('classical', 'jazz', 'pop')
            best_cover: If True, return best non-overlapping cover;
                        if False, return all candidates.
            key_hint: Optional key hint to guide analysis
            sections: Optional list of sections to analyze pattern placement

        Returns:
            AnalysisEnvelope containing primary analysis and alternatives
        """
        if not self.matcher:
            raise ValueError("Pattern engine not available")

        t0 = time.time()

        # 1) Functional analysis (await if coroutine, else run in thread)
        func = self.functional_analyzer.analyze_functionally
        if inspect.iscoroutinefunction(func):
            functional_result = await func(
                chord_symbols, key_hint=key_hint, lock_key=True
            )
        else:
            functional_result = await asyncio.to_thread(
                func, chord_symbols, key_hint=key_hint, lock_key=True
            )

        # 2) Convert functional_result into chords + romans
        chords_info: List[Any] = []
        if hasattr(functional_result, "chords") and functional_result.chords:
            chords_info = functional_result.chords
        elif isinstance(functional_result, dict):
            chords_info = functional_result.get("chords", [])

        romans: List[str] = []
        chords_dto: List[FunctionalChordDTO] = []
        for c in chords_info:
            # Handle both object and dict formats
            if hasattr(c, "roman_numeral"):
                rn = c.roman_numeral
                chord_sym = getattr(c, "chord", "") or getattr(c, "chord_symbol", "")
                func_name = getattr(c, "function", None)
                inversion = getattr(c, "inversion", None)
                quality = getattr(c, "quality", None)
                secondary_of = getattr(c, "secondary_of", None)
                is_chromatic = getattr(c, "is_chromatic", None)
                bass_note = getattr(c, "bass_note", None)
            elif isinstance(c, dict):
                rn = c.get("roman_numeral")
                chord_sym = c.get("chord_symbol", "")
                func_name = c.get("function") or c.get("role")
                inversion = c.get("inversion")
                quality = c.get("quality")
                secondary_of = c.get("secondary_of")
                is_chromatic = c.get("is_chromatic")
                bass_note = c.get("bass_note")
            else:
                continue

            if rn:
                romans.append(rn)
            chords_dto.append(
                FunctionalChordDTO(
                    chord_symbol=chord_sym,
                    roman_numeral=rn,
                    function=func_name,
                    inversion=inversion,
                    quality=quality,
                    secondary_of=secondary_of,
                    is_chromatic=is_chromatic,
                    bass_note=bass_note,
                )
            )

        # Extract key info from functional result
        if hasattr(functional_result, "key_center"):
            key_sig = functional_result.key_center
        elif isinstance(functional_result, dict):
            key_sig = functional_result.get("key_center") or functional_result.get(
                "key_signature"
            )
        else:
            key_sig = None

        # Canonicalize the key signature to avoid enharmonic drift
        if key_sig:
            key_sig = canonicalize_key_signature(key_sig)

        if hasattr(functional_result, "mode"):
            mode = functional_result.mode
        elif isinstance(functional_result, dict):
            mode = functional_result.get("mode")
        else:
            mode = None

        if hasattr(functional_result, "confidence"):
            func_conf = functional_result.confidence
        elif isinstance(functional_result, dict):
            func_conf = functional_result.get("confidence")
        else:
            func_conf = None

        if hasattr(functional_result, "explanation"):
            func_reason = functional_result.explanation
        elif isinstance(functional_result, dict):
            func_reason = functional_result.get("explanation")
        else:
            func_reason = None

        # 3) Run pattern matching
        # Convert to tokens first
        tokens = self.token_converter.convert_analysis_to_tokens(
            chord_symbols=chord_symbols,
            analysis_result=functional_result,
        )

        # Update matcher profile if needed
        if profile != "classical" and self.pattern_lib is not None:
            self.matcher = Matcher(self.pattern_lib, profile=profile)

        # Extract low-level events for enhanced pattern constraints
        from ..core.pattern_engine.low_level_events import LowLevelEventExtractor

        event_extractor = LowLevelEventExtractor()
        events = event_extractor.extract_events(
            tokens, chord_symbols, key_sig or "C major"
        )
        self.matcher.constraint_validator.set_events(events)

        # Find pattern matches
        pattern_matches_raw = self.matcher.match(tokens, best_cover=best_cover)
        pattern_matches: List[PatternMatchDTO] = []
        for m in pattern_matches_raw:
            if not isinstance(m, dict):
                continue
            pattern_matches.append(
                PatternMatchDTO(
                    start=m.get("start", 0),
                    end=m.get("end", 0),
                    pattern_id=str(m.get("pattern_id", m.get("id", ""))),
                    name=m.get("name", ""),
                    family=m.get("family", ""),
                    score=float(str(m.get("score") or m.get("confidence") or 0.0)),
                    evidence=m.get("evidence", []) or [],  # type: ignore[arg-type]
                    # Initialize section-aware fields (will be set by postprocessing)
                    section=None,
                    cadence_role=None,
                )
            )

        # NEW: Section-aware processing with cadence role tagging
        self._apply_section_aware_tagging(pattern_matches, sections, len(tokens))
        self._add_abs_indices(pattern_matches)
        terminal_cadences, final_cadence = self._attach_sections_and_resolve_cadences(
            pattern_matches, sections, len(chord_symbols)
        )

        # 4) Chromatic elements (optional mapping if present)
        chroma_raw: List[Any] = []
        if hasattr(functional_result, "chromatic_elements"):
            chroma_raw = functional_result.chromatic_elements or []
        elif isinstance(functional_result, dict):
            chroma_raw = functional_result.get("chromatic_elements", [])

        chroma_dto: List[ChromaticElementDTO] = []
        for ce in chroma_raw:
            if not isinstance(ce, dict):
                continue
            chroma_dto.append(
                ChromaticElementDTO(
                    type=str(ce.get("type", "")),
                    chord_symbol=(
                        (ce.get("chord") or {}).get("chord_symbol")
                        if isinstance(ce.get("chord"), dict)
                        else None
                    ),
                    roman_numeral=(
                        (ce.get("chord") or {}).get("roman_numeral")
                        if isinstance(ce.get("chord"), dict)
                        else None
                    ),
                    resolution_to=(
                        (ce.get("resolution") or {}).get("roman_numeral")
                        if isinstance(ce.get("resolution"), dict)
                        else None
                    ),
                    explanation=ce.get("explanation"),
                )
            )

        # 5) Modal analysis (standard async entrypoint)
        modal_conf = None
        modal_mode = None
        modal_romans: List[str] = []
        modal_reason = None
        modal_characteristics: List[str] = []

        if self.modal_analyzer is not None:
            # Use standardized async modal analysis
            modal_result = await self.modal_analyzer.analyze_async(
                chord_symbols, key_hint or key_sig
            )
            if modal_result:
                modal_conf = modal_result.confidence
                modal_mode = modal_result.inferred_mode
                modal_reason = modal_result.rationale
                modal_characteristics = [c.label for c in modal_result.characteristics]
                # For modal romans, we can reuse functional romans or
                # extract from modal result
                modal_romans = romans  # Same progression, different interpretation

        # 6) Build summaries + arbitration
        functional_summary = AnalysisSummary(
            type=AnalysisType.FUNCTIONAL,
            roman_numerals=romans,
            confidence=float(func_conf or 0.0),
            key_signature=key_sig,
            mode=mode,
            reasoning=func_reason,
            functional_confidence=float(func_conf or 0.0),
            modal_confidence=(
                float(modal_conf or 0.0) if modal_conf is not None else None
            ),
            terms={},
            patterns=pattern_matches,
            chromatic_elements=chroma_dto,
            chords=chords_dto,
            modal_characteristics=[],
            # NEW: Section-aware fields
            sections=list(sections) if sections else [],
            terminal_cadences=terminal_cadences,
            final_cadence=final_cadence,
        )

        modal_summary: Optional[AnalysisSummary] = None
        if modal_conf is not None:
            modal_summary = AnalysisSummary(
                type=AnalysisType.MODAL,
                roman_numerals=modal_romans,
                confidence=float(modal_conf or 0.0),
                key_signature=key_sig,
                mode=modal_mode,
                reasoning=modal_reason,
                functional_confidence=(
                    float(func_conf or 0.0) if func_conf is not None else None
                ),
                modal_confidence=float(modal_conf or 0.0),
                chords=chords_dto,
                patterns=pattern_matches,
                modal_characteristics=modal_characteristics,
                # NEW: Section-aware fields
                sections=list(sections) if sections else [],
                terminal_cadences=terminal_cadences,
                final_cadence=final_cadence,
            )

        # Centralized arbitration using dedicated service
        arbitration_result = self.arbitration_service.arbitrate(
            functional_summary=functional_summary,
            modal_summary=modal_summary,
            chord_symbols=chord_symbols,
        )
        primary = arbitration_result.primary
        alternatives = arbitration_result.alternatives

        # Apply confidence calibration if available
        if self.calibration_service and self.auto_calibrate:
            calibration_start = time.time()
            calibration_count = 0

            try:
                logger.info("Starting confidence calibration")

                # Extract features for calibration routing
                features = self._extract_calibration_features(
                    chord_symbols=chord_symbols,
                    analysis_result=primary,
                    pattern_matches=pattern_matches,
                    key_signature=key_sig,
                )
                logger.debug(f"Extracted calibration features: {features}")

                # Calibrate primary result
                if (
                    primary
                    and hasattr(primary, "confidence")
                    and primary.confidence is not None
                ):
                    track = (
                        "modal"
                        if primary.type == AnalysisType.MODAL
                        else "functional"
                    )
                    original_confidence = primary.confidence
                    calibrated_confidence = (
                        self.calibration_service.calibrate_confidence(
                            primary.confidence, track, features
                        )
                    )
                    primary.confidence = calibrated_confidence
                    calibration_count += 1

                    logger.info(
                        f"Calibrated {track} confidence: {original_confidence:.3f} →"
                        f" {calibrated_confidence:.3f} "
                        f"(delta: {calibrated_confidence - original_confidence:+.3f})"
                    )

                # Calibrate alternatives
                for i, alt in enumerate(alternatives):
                    if (
                        alt
                        and hasattr(alt, "confidence")
                        and alt.confidence is not None
                    ):
                        alt_track = (
                            "modal"
                            if alt.type == AnalysisType.MODAL
                            else "functional"
                        )
                        original_alt_confidence = alt.confidence
                        calibrated_alt_confidence = (
                            self.calibration_service.calibrate_confidence(
                                alt.confidence, alt_track, features
                            )
                        )
                        alt.confidence = calibrated_alt_confidence
                        calibration_count += 1

                        logger.debug(
                            f"Calibrated alternative {i+1} ({alt_track}):"
                            f" {original_alt_confidence:.3f} →"
                            f" {calibrated_alt_confidence:.3f}"
                        )

                # Log calibration performance metrics
                calibration_duration = (time.time() - calibration_start) * 1000
                logger.info(
                    f"Confidence calibration completed: {calibration_count} scores "
                    f"calibrated in {calibration_duration:.1f}ms"
                )

            except Exception as e:
                # Graceful fallback - log error but continue with uncalibrated results
                logger.error(f"Confidence calibration failed: {str(e)}", exc_info=True)
                logger.warning("Continuing with uncalibrated confidence scores")

        envelope = AnalysisEnvelope(
            primary=primary,
            alternatives=alternatives,
            analysis_time_ms=(time.time() - t0) * 1000.0,
            chord_symbols=list(chord_symbols),
            evidence=[],
            schema_version="1.0",
        )
        return envelope

    # --- Thin sync facade (optional) ---
    def analyze_with_patterns(
        self,
        chord_symbols: List[str],
        profile: str = "classical",
        best_cover: bool = True,
        key_hint: Optional[str] = None,
        sections: Optional[List[SectionDTO]] = None,
    ) -> AnalysisEnvelope:
        """Synchronous wrapper. Prefer the async API in async applications.

        Safe in both contexts:
        - If no event loop is running in this thread, use asyncio.run().
        - If an event loop *is* running (e.g., pytest-asyncio), spin up a
          dedicated thread with its own loop and run the coroutine there.
        """
        try:
            # If this does not raise, we're currently inside a running event loop.
            asyncio.get_running_loop()

            # Run the coroutine in a separate thread with its own loop.
            import threading

            result_holder: Dict[str, AnalysisEnvelope] = {}
            error_holder: Dict[str, BaseException] = {}

            def _runner() -> None:
                loop = asyncio.new_event_loop()
                try:
                    asyncio.set_event_loop(loop)
                    coro = self.analyze_with_patterns_async(
                        chord_symbols=chord_symbols,
                        profile=profile,
                        best_cover=best_cover,
                        key_hint=key_hint,
                        sections=sections,
                    )
                    result_holder["res"] = loop.run_until_complete(coro)
                except (
                    BaseException
                ) as e:  # capture any exception to re-raise in caller thread
                    error_holder["err"] = e
                finally:
                    loop.close()

            t = threading.Thread(target=_runner, daemon=True)
            t.start()
            t.join()

            if "err" in error_holder:
                raise error_holder["err"]
            return result_holder["res"]

        except RuntimeError:
            # No running loop in this thread: safe to use asyncio.run
            return asyncio.run(
                self.analyze_with_patterns_async(
                    chord_symbols=chord_symbols,
                    profile=profile,
                    best_cover=best_cover,
                    key_hint=key_hint,
                    sections=sections,
                )
            )
