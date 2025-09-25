"""
Evidence aggregator for unified pattern engine.

This module combines evidence from multiple pattern matches into unified
functional, modal, and combined confidence scores.
"""

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

import numpy as np

from .evidence import Evidence


class Aggregator:
    """
    Aggregates evidence from pattern matches into unified scores.

    Handles weighting, conflict resolution, and combination of evidence
    across functional and modal analysis tracks.
    """

    def __init__(
        self,
        conflict_strategy: str = "soft_nms",
        overlap_decay: float = 0.5,
        diversity_bonus: float = 0.1,
    ):
        """
        Initialize aggregator with configuration.

        Args:
            conflict_strategy: How to handle overlapping evidence ("soft_nms", "max_pool")
            overlap_decay: Decay factor for overlapping evidence (0.0-1.0)
            diversity_bonus: Bonus for diverse evidence sources (0.0-0.2)
        """
        self.conflict_strategy = conflict_strategy
        self.overlap_decay = overlap_decay
        self.diversity_bonus = diversity_bonus
        self.logger = logging.getLogger(__name__)

    def aggregate(self, evidences: List[Evidence]) -> Dict[str, Any]:
        """
        Combine evidence into functional/modal/combined confidences.

        Args:
            evidences: List of evidence from pattern matches

        Returns:
            Dictionary with aggregated scores and debug info:
            - functional_conf: Functional harmony confidence (0.0-1.0)
            - modal_conf: Modal analysis confidence (0.0-1.0)
            - chromatic_conf: Chromatic harmony confidence (0.0-1.0)
            - combined_conf: Combined confidence (0.0-1.0)
            - debug_breakdown: Detailed scoring breakdown
        """
        if not evidences:
            return {
                "functional_conf": 0.0,
                "modal_conf": 0.0,
                "chromatic_conf": 0.0,
                "combined_conf": 0.0,
                "debug_breakdown": {"evidence_count": 0, "message": "No evidence provided"},
            }

        # Apply conflict resolution
        resolved_evidences = self._resolve_conflicts(evidences)

        # Aggregate by track
        track_scores = self._aggregate_by_track(resolved_evidences)

        # Apply diversity bonus
        diversity_score = self._calculate_diversity(resolved_evidences)

        # Combine tracks into final scores
        functional_conf = min(1.0, track_scores.get("functional", 0.0) + diversity_score)
        modal_conf = min(1.0, track_scores.get("modal", 0.0) + diversity_score)
        chromatic_conf = min(1.0, track_scores.get("chromatic", 0.0) + diversity_score)

        # Combined confidence (weighted average biased toward higher score)
        all_confs = [functional_conf, modal_conf, chromatic_conf]
        active_confs = [c for c in all_confs if c > 0]
        if active_confs:
            # Weight slightly toward the highest confidence
            max_conf = max(active_confs)
            avg_conf = sum(active_confs) / len(active_confs)
            combined_conf = 0.7 * max_conf + 0.3 * avg_conf
        else:
            combined_conf = 0.0

        return {
            "functional_conf": functional_conf,
            "modal_conf": modal_conf,
            "chromatic_conf": chromatic_conf,
            "combined_conf": combined_conf,
            "debug_breakdown": {
                "evidence_count": len(evidences),
                "resolved_count": len(resolved_evidences),
                "track_scores": track_scores,
                "diversity_bonus": diversity_score,
                "patterns_detected": list({e.pattern_id for e in evidences}),
                "conflict_strategy": self.conflict_strategy,
            },
        }

    def _resolve_conflicts(self, evidences: List[Evidence]) -> List[Evidence]:
        """
        Resolve overlapping evidence using configured strategy.

        Args:
            evidences: Original evidence list

        Returns:
            Evidence list with conflicts resolved
        """
        if self.conflict_strategy == "max_pool":
            return self._max_pool_conflicts(evidences)
        elif self.conflict_strategy == "soft_nms":
            return self._soft_nms_conflicts(evidences)
        else:
            # No conflict resolution
            return evidences

    def _max_pool_conflicts(self, evidences: List[Evidence]) -> List[Evidence]:
        """
        Keep only highest-scoring evidence in overlapping regions.

        Args:
            evidences: Evidence to filter

        Returns:
            Filtered evidence list
        """
        if not evidences:
            return []

        # Sort by score descending
        sorted_evidence = sorted(evidences, key=lambda e: e.raw_score, reverse=True)
        kept = []

        for evidence in sorted_evidence:
            # Check if this overlaps with any kept evidence
            overlaps = False
            for kept_evidence in kept:
                if evidence.overlaps(kept_evidence):
                    overlaps = True
                    break

            if not overlaps:
                kept.append(evidence)

        return kept

    def _soft_nms_conflicts(self, evidences: List[Evidence]) -> List[Evidence]:
        """
        Apply soft non-maximum suppression to overlapping evidence.

        Overlapping evidence has scores decayed rather than removed entirely.

        Args:
            evidences: Evidence to process

        Returns:
            Evidence list with adjusted scores
        """
        if not evidences:
            return []

        # Work with mutable copies
        processed = []

        # Sort by score descending
        sorted_evidence = sorted(evidences, key=lambda e: e.raw_score, reverse=True)

        for i, evidence in enumerate(sorted_evidence):
            # Calculate decay from higher-scoring overlapping evidence
            decay_factor = 1.0

            for j in range(i):
                if sorted_evidence[j].overlaps(evidence):
                    # Apply exponential decay based on score difference
                    score_diff = sorted_evidence[j].raw_score - evidence.raw_score
                    decay_factor *= 1.0 - self.overlap_decay * np.exp(-score_diff)

            # Create adjusted evidence if decay is significant
            if decay_factor > 0.1:  # Keep if not too decayed
                adjusted_score = evidence.raw_score * decay_factor

                # Adjust track weights proportionally
                adjusted_weights = {
                    track: weight * decay_factor
                    for track, weight in evidence.track_weights.items()
                }

                processed.append(
                    Evidence(
                        pattern_id=evidence.pattern_id,
                        track_weights=adjusted_weights,
                        features=evidence.features,
                        raw_score=adjusted_score,
                        uncertainty=evidence.uncertainty,
                        span=evidence.span,
                    )
                )

        return processed

    def _aggregate_by_track(self, evidences: List[Evidence]) -> Dict[str, float]:
        """
        Sum evidence weights grouped by analysis track.

        Args:
            evidences: Processed evidence list

        Returns:
            Dictionary of track names to aggregated scores
        """
        track_scores = defaultdict(float)

        for evidence in evidences:
            for track, weight in evidence.track_weights.items():
                # Use a sublinear combination to avoid score inflation
                # This implements a soft-OR combination
                current = track_scores[track]
                track_scores[track] = current + weight * (1 - current)

        return dict(track_scores)

    def _calculate_diversity(self, evidences: List[Evidence]) -> float:
        """
        Calculate diversity bonus based on variety of evidence sources.

        Args:
            evidences: Evidence list

        Returns:
            Diversity bonus (0.0 to diversity_bonus parameter)
        """
        if len(evidences) <= 1:
            return 0.0

        # Count unique pattern families
        pattern_families = set()
        for evidence in evidences:
            # Extract family from pattern_id (e.g., "cadence.authentic" -> "cadence")
            family = evidence.pattern_id.split(".")[0] if "." in evidence.pattern_id else "general"
            pattern_families.add(family)

        # Diversity increases with more families, up to the configured bonus
        diversity_ratio = min(1.0, len(pattern_families) / 4.0)  # Max out at 4 families
        return self.diversity_bonus * diversity_ratio