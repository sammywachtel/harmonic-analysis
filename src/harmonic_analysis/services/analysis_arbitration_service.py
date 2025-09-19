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
from typing import Any, List, Optional, Tuple

from harmonic_analysis.analysis_types import EvidenceType
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

    # Evidence-based modal arbitration (feature flag for new logic)
    enable_evidence_based_modal_arbitration: bool = (
        False  # Set to True to enable new logic
    )


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

    def _score_modal_evidence(self, items: List[Any]) -> Tuple[bool, float, List[str]]:
        """Score typed modal evidence into (has_evidence, score∈[0,1], labels).

        Favor CADENTIAL/STRUCTURAL, then INTERVALLIC, then CONTEXTUAL.

        Args:
            items: List of ModalEvidence objects

        Returns:
            Tuple of (has_evidence, score, labels)
        """
        if not items:
            return False, 0.0, []

        score = 0.0
        labels: List[str] = []

        for e in items:
            et = getattr(e, "type", None)
            desc = getattr(e, "description", "")
            s = float(getattr(e, "strength", 0.0))

            if et == EvidenceType.CADENTIAL:
                score += max(0.25, 0.7 * s)
            elif et == EvidenceType.STRUCTURAL:
                score += max(0.15, 0.5 * s)
            elif et == EvidenceType.INTERVALLIC:
                score += max(0.10, 0.4 * s)
            elif et == EvidenceType.CONTEXTUAL:
                score += max(0.05, 0.3 * s)

            if desc:
                labels.append(desc)

        score = max(0.0, min(1.0, score))
        return (score > 0.20), score, labels[:6]

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

    def _has_authentic_cadence(self, patterns: Any) -> bool:
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

    def _has_modal_characteristics(
        self, summary: AnalysisSummary
    ) -> Tuple[bool, List[str]]:
        """
        Check if analysis contains strong modal characteristics.

        Returns:
            Tuple of (has_modal_chars, list_of_characteristics)
        """
        if not summary or not summary.roman_numerals:
            return False, []

        modal_indicators = []
        romans = summary.roman_numerals

        # Check for diagnostic modal roman numerals
        modal_romans = {
            "bVII": "Mixolydian ♭VII",
            "♭VII": "Mixolydian ♭VII",
            "bII": "Phrygian ♭II",
            "♭II": "Phrygian ♭II",
            "bVI": "Aeolian ♭VI",
            "♭VI": "Aeolian ♭VI",
            "#IV": "Lydian #IV",
            "♯IV": "Lydian #IV",
        }

        for roman in romans:
            if roman in modal_romans:
                modal_indicators.append(modal_romans[roman])

        # Check for modal progressions
        roman_sequence = " → ".join(romans)

        # Mixolydian patterns (most common modal indicators)
        if any(
            pattern in roman_sequence
            for pattern in ["I → bVII", "bVII → I", "I → bVII → IV"]
        ):
            modal_indicators.append("Mixolydian cadential pattern")

        # Dorian patterns
        if any(pattern in roman_sequence for pattern in ["i → IV", "iv → I"]):
            modal_indicators.append("Dorian iv-I pattern")

        # Phrygian patterns
        if any(pattern in roman_sequence for pattern in ["i → bII", "bII → i"]):
            modal_indicators.append("Phrygian bII pattern")

        return len(modal_indicators) > 0, modal_indicators

    def _calculate_modal_characteristic_score(self, modal_chars: List[str]) -> float:
        """
        Calculate a numeric score for modal characteristics strength.

        Returns:
            Float score from 0.0 to 1.0 based on modal evidence strength
        """
        if not modal_chars:
            return 0.0

        # Weight different types of modal evidence
        characteristic_weights = {
            "Mixolydian ♭VII": 0.8,  # Strong modal indicator
            "Mixolydian cadential pattern": 0.6,  # Strong pattern evidence
            "Phrygian ♭II": 0.7,  # Strong modal indicator
            "Phrygian bII pattern": 0.5,  # Pattern evidence
            "Dorian iv-I pattern": 0.4,  # Moderate pattern evidence
            "Lydian #IV": 0.7,  # Strong modal indicator
            "Aeolian ♭VI": 0.6,  # Moderate modal indicator
        }

        total_score = 0.0
        for char in modal_chars:
            # Find matching characteristic (partial match for flexibility)
            for key, weight in characteristic_weights.items():
                if key in char or char in key:
                    total_score += weight
                    break
            else:
                # Unknown characteristic gets default weight
                total_score += 0.3

        # Normalize to [0, 1] range with diminishing returns
        return min(1.0, total_score)

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

        # Get additional signals for arbitration
        outside_key_ratio = self._get_outside_key_ratio(modal_summary)
        has_auth_cadence = self._has_authentic_cadence(functional_summary.patterns)

        # Check for modal characteristics in functional analysis (shows we detected modal elements)
        has_modal_chars, modal_chars = self._has_modal_characteristics(
            functional_summary
        )
        modal_char_score = self._calculate_modal_characteristic_score(modal_chars)

        # NEW: Evidence-based modal analysis (when feature flag enabled)
        modal_evidence_items = []
        modal_evidence_labels: List[str] = []
        has_evidence_markers = False
        evidence_score = 0.0

        if self.policy.enable_evidence_based_modal_arbitration:
            # Materialize modal evidence (prefer what modal_summary already carries)
            modal_evidence_items = getattr(modal_summary, "modal_evidence", None) or []

            if not modal_evidence_items:
                # Fallback: try to get evidence from the analyzer directly
                try:
                    from harmonic_analysis.services.modal_analysis_service import (
                        ModalAnalysisService,
                    )

                    _modal_svc = ModalAnalysisService()
                    _modal = _modal_svc._analyzer.analyze_modal_characteristics(
                        chord_symbols=chord_symbols,
                        parent_key=getattr(functional_summary, "key_signature", None),
                    )
                    if _modal and hasattr(_modal, "evidence"):
                        modal_evidence_items = _modal.evidence
                except Exception:
                    # Arbitration must not crash on evidence lookup
                    modal_evidence_items = []

            # Score the evidence
            has_evidence_markers, evidence_score, modal_evidence_labels = (
                self._score_modal_evidence(modal_evidence_items)
            )

        # Utility-based arbitration per music-alg-5a-mod-v-func.md
        # Tunable weights
        w1, w2, w3, w4 = 1.0, 0.6, 0.4, 0.2  # Modal utility weights
        v1, v2, v3 = 1.0, 0.2, 0.4  # Functional utility weights
        tau_okr = 0.20  # Outside key ratio threshold
        delta_guardband = 0.10  # Guardband for confidence protection

        # Calculate outside key ratio term (only positive contribution)
        okr_term = max(0.0, outside_key_ratio - tau_okr)

        # Calculate utilities
        # Use evidence score when feature flag is enabled, otherwise use char score
        modal_score_for_utility = (
            evidence_score
            if self.policy.enable_evidence_based_modal_arbitration
            else modal_char_score
        )

        utility_modal = (
            w1 * modal_conf
            + w2 * modal_score_for_utility
            + w3 * okr_term
            - w4 * (1.0 if has_auth_cadence else 0.0)
        )

        utility_functional = (
            v1 * func_conf + v2 * (1.0 if has_auth_cadence else 0.0) - v3 * okr_term
        )

        # Initial decision by utility
        winner = "modal" if utility_modal > utility_functional else "functional"
        rationale = (
            f"Decision by utility_v1 (modal={utility_modal:.3f}, "
            f"functional={utility_functional:.3f})"
        )

        # Apply guardbands when modal wins
        if winner == "modal":
            if self.policy.enable_evidence_based_modal_arbitration:
                # NEW: Evidence-based guardband logic
                # Guardband 1: Modal confidence must be within delta_guardband of functional
                confidence_gap = func_conf - modal_conf

                if confidence_gap > delta_guardband:
                    winner = "functional"
                    rationale += (
                        f"; guardband kept functional (gap {confidence_gap:.2f} > "
                        f"delta {delta_guardband:.2f})"
                    )
                # Guardband 2: Must have actual modal evidence markers present
                elif not has_evidence_markers:
                    winner = "functional"
                    rationale += "; no modal evidence markers present"
                else:
                    # Modal wins with evidence and within guardband
                    rationale += (
                        f"; modal wins with evidence: {modal_evidence_labels[:3]}, "
                        f"score={evidence_score:.2f}, guardband OK"
                    )
            else:
                # EXISTING: Original guardband logic
                # Guardband 1: Modal confidence must not be much lower than functional
                # BUT allow override for very strong modal characteristics (high modal_char_score)
                confidence_gap = func_conf - modal_conf
                max_allowed_gap = delta_guardband + (
                    modal_char_score * 0.15
                )  # Extra allowance for strong modal chars

                if confidence_gap > max_allowed_gap:
                    winner = "functional"
                    rationale += (
                        f"; guardband kept functional (gap {confidence_gap:.2f} > "
                        f"max_allowed {max_allowed_gap:.2f})"
                    )
                # Guardband 2: Must have actual modal markers present
                elif not has_modal_chars:
                    winner = "functional"
                    rationale += "; no modal markers present"

        # Add utility breakdown for transparency
        if has_modal_chars:
            rationale += f" [modal_chars: {', '.join(modal_chars[:2])}]"

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

        # Add debug information to warnings for observability
        warnings = []
        if self.policy.enable_evidence_based_modal_arbitration:
            warnings.append(
                f"arb_v2: func={func_conf:.3f}, modal={modal_conf:.3f}, "
                f"okr={outside_key_ratio:.2f}, auth_cadence={has_auth_cadence}, "
                f"evidence_markers={modal_evidence_labels[:3] if has_evidence_markers else []}, "
                f"evidence_score={evidence_score:.3f}"
            )
        else:
            warnings.append(
                f"arb_v1: func={func_conf:.3f}, modal={modal_conf:.3f}, "
                f"okr={outside_key_ratio:.2f}, auth_cadence={has_auth_cadence}, "
                f"modal_chars={modal_chars[:3] if has_modal_chars else []}"
            )

        return ArbitrationResult(
            primary=primary,
            alternatives=alternatives,
            confidence_gap=confidence_gap,
            progression_type=progression_type,
            rationale=rationale,
            warnings=warnings,
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
