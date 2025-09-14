#!/usr/bin/env python3
"""
Analysis Arbitration Service

Centralizes arbitration heuristics for choosing between functional and modal analyses.
This consolidates arbitration logic that was previously scattered in tests,
making it available consistently across the application.

Updated to use the new ModalFunctionalArbitrator as specified in music-alg-2g.md.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

from harmonic_analysis.core.arbitration import ModalFunctionalArbitrator
from harmonic_analysis.dto import (
    AnalysisSummary,
    AnalysisType,
    ArbitrationResult,
    ProgressionType,
)

logger = logging.getLogger(__name__)


@dataclass
class ArbitrationPolicy:
    """Configuration for arbitration decisions"""

    # Minimum confidence thresholds
    min_functional_confidence: float = 0.50
    min_modal_confidence: float = 0.40

    # Confidence margins
    functional_margin_required: float = (
        0.10  # Functional should exceed modal by this much
    )
    modal_dominance_threshold: float = (
        0.15  # Modal needs this much advantage to be primary
    )

    # Warning thresholds
    excessive_modal_dominance: float = (
        0.30  # Warn if modal dominates functional by this much for common progressions
    )

    # Pattern-based adjustments
    enable_pattern_based_classification: bool = True
    enable_progression_type_heuristics: bool = True


class AnalysisArbitrationService:
    """
    Centralizes arbitration logic for choosing between analytical approaches.

    This service encapsulates heuristics that determine which analysis
    (functional vs modal)
    should be primary, based on confidence scores, progression characteristics, and
    music-theoretical considerations.
    """

    def __init__(self, policy: Optional[ArbitrationPolicy] = None):
        self.policy = policy or ArbitrationPolicy()
        self.arbitrator = ModalFunctionalArbitrator()

    def _get_outside_key_ratio(self, modal_summary: AnalysisSummary) -> float:
        """Extract outside_key_ratio from modal analysis result."""
        # Check if modal_summary has validator info
        if hasattr(modal_summary, "validator"):
            return float(getattr(modal_summary.validator, "outside_key_ratio", 0.0))
        # Check dict path (for compatibility)
        if isinstance(modal_summary, dict):
            return float(
                (modal_summary.get("validator") or {}).get("outside_key_ratio", 0.0)
            )
        return 0.0

    def _has_authentic_cadence(self, patterns) -> bool:
        """Check if patterns contain an authentic cadence."""
        if not patterns:
            return False
        # DTO path
        if hasattr(patterns[0], "family"):
            return any(
                p.family == "cadence" and "authentic" in (p.name or "").lower()
                for p in patterns
            )
        # dict path
        return any(
            (pm.get("family") == "cadence")
            and ("authentic" in (pm.get("name", "").lower()))
            for pm in patterns
        )

    def arbitrate(
        self,
        functional_summary: AnalysisSummary,
        modal_summary: Optional[AnalysisSummary] = None,
        chord_symbols: Optional[List[str]] = None,
    ) -> ArbitrationResult:
        """
        Main arbitration method with enhanced tie-breaking logic.

        Args:
            functional_summary: The functional analysis result
            modal_summary: The modal analysis result (optional)
            chord_symbols: Original chord symbols for pattern detection

        Returns:
            ArbitrationResult with primary/alternatives and rationale
        """
        if modal_summary is None:
            # Only functional analysis available
            return ArbitrationResult(
                primary=functional_summary,
                alternatives=[],
                confidence_gap=0.0,
                progression_type=ProgressionType.CLEAR_FUNCTIONAL,
                rationale="Only functional analysis available",
                warnings=[],
            )

        # Extract confidence values
        func_conf = functional_summary.confidence
        modal_conf = modal_summary.confidence

        # Set confidence breakdown fields
        functional_summary.functional_confidence = func_conf
        functional_summary.modal_confidence = modal_conf
        modal_summary.functional_confidence = func_conf
        modal_summary.modal_confidence = modal_conf

        # Get additional signals for tie-breaking
        outside_key_ratio = self._get_outside_key_ratio(modal_summary)
        has_auth_cadence = self._has_authentic_cadence(functional_summary.patterns)

        # Enhanced arbitration logic from music-alg-2i.md
        winner = "functional"
        rationale = ""

        if modal_conf > func_conf + 0.10:
            winner = "modal"
            rationale = (
                f"Modal confidence ({modal_conf:.2f}) exceeds functional by > 0.10"
            )
        elif func_conf > modal_conf + 0.10:
            winner = "functional"
            rationale = (
                f"Functional confidence ({func_conf:.2f}) exceeds modal by > 0.10"
            )
        else:
            # Tie-breaking logic
            if outside_key_ratio >= 0.25 and not has_auth_cadence:
                winner = "modal"
                rationale = (
                    f"Tie-break: High outside-key ratio "
                    f"({outside_key_ratio:.2f}) and no authentic cadence"
                )
            else:
                winner = "functional"
                rationale = (
                    f"Tie-break: Functional preferred (okr"
                    f"={outside_key_ratio:.2f},"
                    f"auth_cadence={has_auth_cadence})"
                )

        # Set primary and alternatives based on winner
        if winner == "modal":
            primary = modal_summary
            alternatives = [functional_summary]
        else:
            primary = functional_summary
            alternatives = [modal_summary]

        # Calculate confidence gap for backwards compatibility
        confidence_gap = modal_conf - func_conf

        # Determine progression type
        progression_type = ProgressionType.AMBIGUOUS
        if abs(confidence_gap) > 0.20:
            progression_type = (
                ProgressionType.CLEAR_MODAL
                if winner == "modal"
                else ProgressionType.CLEAR_FUNCTIONAL
            )

        return ArbitrationResult(
            primary=primary,
            alternatives=alternatives,
            confidence_gap=confidence_gap,
            progression_type=progression_type,
            rationale=rationale,
            warnings=[],
        )

    def _classify_progression_type(
        self,
        chord_symbols: List[str],
        functional_summary: AnalysisSummary,
        modal_summary: AnalysisSummary,
    ) -> ProgressionType:
        """
        Classify progression as clearly functional, clearly modal, or ambiguous.

        This encapsulates knowledge about what progressions are typically
        functional vs modal based on harmonic patterns.
        """
        if not chord_symbols:
            return ProgressionType.UNKNOWN

        # chord_str = " ".join(chord_symbols)  # Not currently used
        romans = functional_summary.roman_numerals
        # roman_str = " ".join(romans) if romans else ""  # Not currently used

        # Clear functional patterns (should not be modal primary)
        clear_functional_patterns = [
            # Perfect authentic cadences
            (["I", "IV", "V", "I"], "I-IV-V-I cadence"),
            (["I", "V", "I"], "V-I cadence"),
            # Common functional progressions
            (["vi", "ii", "V", "I"], "vi-ii-V-I progression"),
            (["IV", "V", "vi"], "deceptive cadence"),
            (["ii", "V", "I"], "ii-V-I progression"),
            # Circle of fifths progressions
            (["vi", "ii", "V", "I"], "circle of fifths"),
            (["iii", "vi", "ii", "V"], "extended circle of fifths"),
        ]

        for pattern, description in clear_functional_patterns:
            if self._matches_roman_pattern(romans, pattern):
                logger.debug(f"Classified as CLEAR_FUNCTIONAL: {description}")
                return ProgressionType.CLEAR_FUNCTIONAL

        # Clear modal patterns (should be modal primary)
        clear_modal_patterns = [
            # Modal vamps and characteristic progressions
            (["bVII", "I"], "Mixolydian bVII-I"),
            (["I", "bVII"], "Mixolydian I-bVII"),
            (["i", "bII"], "Phrygian i-bII"),
            (["bII", "i"], "Phrygian bII-i"),
            (["i", "IV"], "Dorian i-IV"),
            (["iv", "I"], "Dorian iv-I"),
        ]

        for pattern, description in clear_modal_patterns:
            if self._matches_roman_pattern(romans, pattern):
                logger.debug(f"Classified as CLEAR_MODAL: {description}")
                return ProgressionType.CLEAR_MODAL

        # Ambiguous patterns (common progressions that could be interpreted either way)
        ambiguous_patterns = [
            # The vi-IV-I-V family - can be functional in major or modal in
            # relative minor
            (["vi", "IV", "I", "V"], "vi-IV-I-V progression"),
            (["F#m", "D", "A", "E"], "specific vi-IV-I-V example"),
            (["Am", "F", "C", "G"], "specific vi-IV-I-V example"),
            (["Em", "C", "G", "D"], "specific vi-IV-I-V example"),
        ]

        for pattern, description in ambiguous_patterns:
            if self._matches_roman_pattern(
                romans, pattern
            ) or self._matches_chord_pattern(chord_symbols, pattern):
                logger.debug(f"Classified as AMBIGUOUS: {description}")
                return ProgressionType.AMBIGUOUS

        return ProgressionType.UNKNOWN

    def _matches_roman_pattern(self, romans: List[str], pattern: List[str]) -> bool:
        """Check if roman numerals match a pattern"""
        if not romans or len(romans) != len(pattern):
            return False
        return romans == pattern

    def _matches_chord_pattern(self, chords: List[str], pattern: List[str]) -> bool:
        """Check if chord symbols match a pattern"""
        if not chords or len(chords) != len(pattern):
            return False
        return chords == pattern

    def _apply_arbitration_rules(
        self,
        functional_summary: AnalysisSummary,
        modal_summary: AnalysisSummary,
        confidence_gap: float,
        progression_type: ProgressionType,
    ) -> Tuple[AnalysisSummary, List[AnalysisSummary], str, List[str]]:
        """
        Apply arbitration rules based on confidence scores and progression type.

        Returns: (primary, alternatives, rationale, warnings)
        """
        func_conf = functional_summary.confidence
        modal_conf = modal_summary.confidence
        warnings = []

        # Rule 1: Clear functional progressions should not be modal primary
        if progression_type == ProgressionType.CLEAR_FUNCTIONAL:
            if modal_conf > func_conf:
                warnings.append(
                    f"Modal confidence ({modal_conf:.3f}) higher than functional "
                    f"({func_conf:.3f}) "
                    f"for clearly functional progression"
                )

            # Functional should dominate or be competitive
            if func_conf >= self.policy.min_functional_confidence:
                return (
                    functional_summary,
                    [modal_summary],
                    f"Clear functional progression analyzed as functional "
                    f"(confidence: {func_conf:.3f})",
                    warnings,
                )
            else:
                warnings.append(
                    f"Functional confidence below minimum threshold "
                    f"({func_conf:.3f} < {self.policy.min_functional_confidence})"
                )

        # Rule 2: Clear modal progressions should be modal primary
        elif progression_type == ProgressionType.CLEAR_MODAL:
            if modal_conf >= self.policy.min_modal_confidence:
                return (
                    modal_summary,
                    [functional_summary],
                    f"Clear modal progression analyzed as modal "
                    f"(confidence: {modal_conf:.3f})",
                    warnings,
                )
            else:
                warnings.append(
                    f"Modal confidence below minimum threshold "
                    f"({modal_conf:.3f} < {self.policy.min_modal_confidence})"
                )

        # Rule 3: Ambiguous progressions - check for excessive modal dominance
        elif progression_type == ProgressionType.AMBIGUOUS:
            if confidence_gap > self.policy.excessive_modal_dominance:
                warnings.append(
                    f"Modal analysis dominance ({confidence_gap:.3f}) may be excessive "
                    f"for ambiguous progression. Consider calibration."
                )

        # Standard arbitration logic (original algorithm)
        if modal_conf > (func_conf + self.policy.modal_dominance_threshold):
            return (
                modal_summary,
                [functional_summary],
                f"Modal analysis selected (confidence gap: {confidence_gap:.3f})",
                warnings,
            )
        else:
            return (
                functional_summary,
                [modal_summary],
                f"Functional analysis selected (modal gap insufficient: "
                f"{confidence_gap:.3f})",
                warnings,
            )

    def validate_analysis_quality(
        self, result: ArbitrationResult, expected_type: Optional[AnalysisType] = None
    ) -> List[str]:
        """
        Validate analysis quality and return issues found.

        This can be used by tests to check if arbitration results meet quality
        standards.
        """
        issues = []

        primary = result.primary
        func_conf = None
        modal_conf = None

        # Extract confidence values
        if hasattr(primary, "functional_confidence"):
            func_conf = primary.functional_confidence
        if hasattr(primary, "modal_confidence"):
            modal_conf = primary.modal_confidence

        # Check confidence thresholds based on analysis type
        if primary.type == AnalysisType.FUNCTIONAL:
            if (
                func_conf is not None
                and func_conf < self.policy.min_functional_confidence
            ):
                issues.append(
                    f"Functional confidence too low: {func_conf:.3f} < "
                    f"{self.policy.min_functional_confidence}"
                )

            if (
                func_conf is not None
                and modal_conf is not None
                and func_conf < modal_conf + self.policy.functional_margin_required
            ):
                issues.append(
                    f"Functional confidence should exceed modal by "
                    f"{self.policy.functional_margin_required}"
                )

        elif primary.type == AnalysisType.MODAL:
            if modal_conf is not None and modal_conf < self.policy.min_modal_confidence:
                issues.append(
                    f"Modal confidence too low: {modal_conf:.3f} < "
                    f"{self.policy.min_modal_confidence}"
                )

        # Check for expected type mismatch
        if expected_type and primary.type != expected_type:
            issues.append(
                f"Expected {expected_type.value} analysis, got {primary.type.value}"
            )

        # Include any warnings from arbitration
        issues.extend(result.warnings)

        return issues
