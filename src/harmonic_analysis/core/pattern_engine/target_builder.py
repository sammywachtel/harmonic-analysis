"""
Target builder for corpus-based ground truth.

This module constructs unified reliability targets for calibration
based on corpus annotations and heuristic adjudication.
"""

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np

from .evidence import Evidence


@dataclass
class TargetAnnotation:
    """Annotation for a musical segment from corpus or rules."""

    span: Tuple[int, int]  # Chord indices [start, end)
    analysis_type: str  # "functional", "modal", or "hybrid"
    confidence: float  # Ground truth confidence (0.0-1.0)
    source: str  # "corpus", "rule", "expert", etc.
    metadata: Dict[str, Any]  # Additional info (key, mode, etc.)


class TargetBuilder:
    """
    Constructs unified training targets for calibration.

    Combines corpus annotations, rule-based adjudication, and
    evidence strength to produce reliability targets.
    """

    def __init__(
        self,
        agreement_threshold: float = 0.8,
        ambiguous_range: Tuple[float, float] = (0.3, 0.7),
    ):
        """
        Initialize target builder.

        Args:
            agreement_threshold: Min agreement for high confidence labels
            ambiguous_range: Confidence range for ambiguous cases
        """
        self.agreement_threshold = agreement_threshold
        self.ambiguous_range = ambiguous_range

    def build_targets(
        self,
        evidences: Iterable[Evidence],
        annotations: Optional[List[TargetAnnotation]] = None,
    ) -> List[float]:
        """
        Build reliability targets from evidence and annotations.

        Args:
            evidences: Pattern match evidence
            annotations: Optional ground truth annotations

        Returns:
            List of target values (0.0-1.0) aligned with evidences
        """
        evidences = list(evidences)

        if not evidences:
            return []

        # If no annotations, use heuristic targets
        if not annotations:
            return self._build_heuristic_targets(evidences)

        # Build targets using annotations
        targets = []
        for evidence in evidences:
            target = self._compute_target_for_evidence(evidence, annotations)
            targets.append(target)

        return targets

    def _build_heuristic_targets(self, evidences: List[Evidence]) -> List[float]:
        """
        Build targets using heuristic rules when no annotations available.

        Uses evidence strength, track agreement, and pattern reliability.

        Args:
            evidences: List of evidence

        Returns:
            Heuristic target values
        """
        targets = []

        for evidence in evidences:
            # Base target on raw score
            base_target = evidence.raw_score

            # Adjust based on track agreement
            tracks = list(evidence.track_weights.keys())
            if len(tracks) > 1:
                # Multi-track evidence - check agreement
                weights = list(evidence.track_weights.values())
                if max(weights) / (sum(weights) + 1e-6) > 0.7:
                    # Strong agreement on primary track
                    base_target *= 1.1
                else:
                    # Disagreement - reduce confidence
                    base_target *= 0.9

            # Adjust based on pattern type (from pattern_id)
            if "cadence" in evidence.pattern_id:
                # Cadences are typically reliable
                base_target *= 1.05
            elif "chromatic" in evidence.pattern_id:
                # Chromatic patterns need context
                base_target *= 0.95

            # Clamp to valid range
            target = np.clip(base_target, 0.0, 1.0)
            targets.append(target)

        return targets

    def _compute_target_for_evidence(
        self, evidence: Evidence, annotations: List[TargetAnnotation]
    ) -> float:
        """
        Compute target for single evidence using annotations.

        Args:
            evidence: Evidence to compute target for
            annotations: Ground truth annotations

        Returns:
            Target value (0.0-1.0)
        """
        # Find annotations that overlap with evidence span
        overlapping = [
            ann
            for ann in annotations
            if self._spans_overlap(evidence.span, ann.span)
        ]

        if not overlapping:
            # No annotations - use raw score as fallback
            return evidence.raw_score

        # Aggregate overlapping annotations
        if len(overlapping) == 1:
            # Single annotation - use its confidence
            ann = overlapping[0]
            return self._adjust_target_for_match(evidence, ann)
        else:
            # Multiple annotations - weighted average by overlap
            weighted_sum = 0.0
            total_weight = 0.0

            for ann in overlapping:
                overlap_ratio = self._compute_overlap_ratio(evidence.span, ann.span)
                adjusted_target = self._adjust_target_for_match(evidence, ann)
                weighted_sum += adjusted_target * overlap_ratio
                total_weight += overlap_ratio

            if total_weight > 0:
                return weighted_sum / total_weight
            else:
                return evidence.raw_score

    def _adjust_target_for_match(
        self, evidence: Evidence, annotation: TargetAnnotation
    ) -> float:
        """
        Adjust annotation confidence based on evidence match quality.

        Args:
            evidence: Evidence being evaluated
            annotation: Ground truth annotation

        Returns:
            Adjusted target value
        """
        base_confidence = annotation.confidence

        # Check if evidence type matches annotation
        evidence_types = set(evidence.track_weights.keys())
        if annotation.analysis_type in evidence_types:
            # Type matches - use full confidence
            return base_confidence
        elif annotation.analysis_type == "hybrid" and evidence_types:
            # Hybrid annotation with any evidence type
            return base_confidence * 0.9
        else:
            # Type mismatch - reduce confidence
            return base_confidence * 0.7

    def _spans_overlap(self, span1: Tuple[int, int], span2: Tuple[int, int]) -> bool:
        """Check if two spans overlap."""
        return not (span1[1] <= span2[0] or span2[1] <= span1[0])

    def _compute_overlap_ratio(
        self, span1: Tuple[int, int], span2: Tuple[int, int]
    ) -> float:
        """
        Compute overlap ratio between two spans.

        Args:
            span1: First span [start, end)
            span2: Second span [start, end)

        Returns:
            Overlap ratio (0.0-1.0)
        """
        if not self._spans_overlap(span1, span2):
            return 0.0

        overlap_start = max(span1[0], span2[0])
        overlap_end = min(span1[1], span2[1])
        overlap_size = overlap_end - overlap_start

        span1_size = span1[1] - span1[0]
        if span1_size > 0:
            return overlap_size / span1_size
        else:
            return 0.0

    def build_corpus_annotations(
        self, corpus_data: Dict[str, Any]
    ) -> List[TargetAnnotation]:
        """
        Convert corpus data to target annotations.

        This is a placeholder for corpus integration.
        In production, this would parse music21 or other corpus formats.

        Args:
            corpus_data: Raw corpus data

        Returns:
            List of target annotations
        """
        annotations = []

        # Example corpus data structure
        # This would be replaced with actual corpus parsing
        for segment in corpus_data.get("segments", []):
            ann = TargetAnnotation(
                span=(segment["start"], segment["end"]),
                analysis_type=segment.get("type", "functional"),
                confidence=segment.get("confidence", 0.8),
                source=segment.get("source", "corpus"),
                metadata=segment.get("metadata", {}),
            )
            annotations.append(ann)

        return annotations