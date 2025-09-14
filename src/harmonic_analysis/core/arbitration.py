"""
Modal vs Functional Arbitration - Single Source of Truth

This module implements the centralized arbitration logic for choosing between
functional and modal analyses, as specified in music-alg-2g.md.
"""

from dataclasses import dataclass


@dataclass
class ArbitrationResult:
    """Result of modal vs functional arbitration."""

    chosen: str  # "functional" | "modal"
    functional_confidence: float
    modal_confidence: float
    reasoning: str


class ModalFunctionalArbitrator:
    """Centralized arbitrator for modal vs functional analysis selection."""

    def decide(
        self,
        functional_conf: float,
        modal_conf: float,
        *,
        margin: float = 0.10,
        min_primary: float = 0.35,
    ) -> ArbitrationResult:
        """
        Decide between functional and modal analyses based on confidence scores.

        Args:
            functional_conf: Functional analysis confidence (0.0-1.0)
            modal_conf: Modal analysis confidence (0.0-1.0)
            margin: Minimum difference required for clear winner (default 0.10)
            min_primary: Minimum confidence required for primary analysis (default 0.35)

        Returns:
            ArbitrationResult with chosen analysis and reasoning
        """
        # Step 1: Clamp confidence values to valid range
        f = max(0.0, min(1.0, functional_conf or 0.0))
        m = max(0.0, min(1.0, modal_conf or 0.0))

        # Step 2: Apply margin-based tie-breaking with minimum threshold
        if f >= m + margin and f >= min_primary:
            return ArbitrationResult(
                "functional", f, m, "Functional exceeds modal by margin."
            )

        if m >= f + margin and m >= min_primary:
            return ArbitrationResult(
                "modal", f, m, "Modal exceeds functional by margin."
            )

        # Step 3: Fallback - pick higher confidence with low-certainty note
        chosen = "functional" if f >= m else "modal"
        return ArbitrationResult(
            chosen, f, m, "Within margin; selected higher with low-certainty note."
        )
