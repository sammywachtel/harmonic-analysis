"""
Unified Target Builder - Replaces legacy per-track target construction.

Implements the Iteration 3 unified target construction system that replaces
split functional/modal targets with single reliability targets p(correct | evidence).

This is integrated with the corpus mining pipeline and provides a drop-in
replacement for the legacy TargetBuilder.
"""

from typing import Any, Dict, Iterable, List, Optional, Tuple
from dataclasses import dataclass

import numpy as np

from .evidence import Evidence


@dataclass
class TargetAnnotation:
    """Annotation for target construction - migrated from legacy target builder."""
    span: Tuple[int, int]
    analysis_type: str
    confidence: float
    source: str
    metadata: Dict[str, Any]

# Import the production corpus miner
try:
    from ...corpus_miner import (
        UnifiedTargetBuilder as CorpusTargetBuilder,
        LabeledSample,
        LabelSource,
        DifficultyStratum,
        PatternMatch
    )
    CORPUS_MINER_AVAILABLE = True
except ImportError:
    CORPUS_MINER_AVAILABLE = False
    # Mock classes for when corpus miner is not available
    class LabeledSample:
        def __init__(self, context, matches, label, label_source, difficulty_stratum, confidence_breakdown):
            self.context = context
            self.matches = matches
            self.label = label
            self.label_source = label_source
            self.difficulty_stratum = difficulty_stratum
            self.confidence_breakdown = confidence_breakdown

    class LabelSource:
        ADJUDICATION_HEURISTIC = "adjudication_heuristic"
        WEAK_SUPERVISION = "weak_supervision"

    class DifficultyStratum:
        DIATONIC_SIMPLE = "diatonic_simple"
        CHROMATIC_MODERATE = "chromatic_moderate"
        MODAL_COMPLEX = "modal_complex"

    class PatternMatch:
        def __init__(self, pattern_id, span, raw_score, evidence_features):
            self.pattern_id = pattern_id
            self.span = span
            self.raw_score = raw_score
            self.evidence_features = evidence_features


class UnifiedTargetBuilder:
    """
    Unified target builder that replaces legacy per-track construction.

    Implements the Section 5 design: single reliability target per sample/match
    using adjudication heuristics and corpus labels.
    """

    def __init__(
        self,
        agreement_threshold: float = 0.8,
        ambiguous_range: Tuple[float, float] = (0.3, 0.7),
        use_corpus_pipeline: bool = True
    ):
        """
        Initialize unified target builder.

        Args:
            agreement_threshold: Min agreement for high confidence labels (legacy compat)
            ambiguous_range: Confidence range for ambiguous cases (legacy compat)
            use_corpus_pipeline: Whether to use corpus mining pipeline (recommended)
        """
        self.agreement_threshold = agreement_threshold
        self.ambiguous_range = ambiguous_range
        self.use_corpus_pipeline = use_corpus_pipeline

        # Initialize corpus target builder if available
        if CORPUS_MINER_AVAILABLE and use_corpus_pipeline:
            self.corpus_builder = CorpusTargetBuilder()
        else:
            self.corpus_builder = None

    def build_targets(
        self,
        evidences: Iterable[Evidence],
        annotations: Optional[List[Any]] = None,  # Legacy parameter for backward compatibility
    ) -> List[float]:
        """
        Build unified reliability targets from evidence.

        This is the main entry point that replaces the legacy per-track approach
        with unified p(correct | evidence) targets.

        Args:
            evidences: Pattern match evidence
            annotations: Legacy annotations that override heuristics when provided

        Returns:
            List of unified reliability targets (0.0-1.0)
        """
        evidences = list(evidences)

        if not evidences:
            return []

        # Backward compatibility: if annotations provided, use them to override heuristics
        if annotations:
            return self._build_annotation_targets(evidences, annotations)

        # Convert evidence to labeled samples for unified processing
        labeled_samples = self._convert_evidence_to_labeled_samples(evidences)

        if self.corpus_builder and len(labeled_samples) > 0:
            try:
                # Use corpus mining unified target construction
                raw_scores, reliability_targets, _ = self.corpus_builder.build_unified_targets(labeled_samples)
                return reliability_targets.tolist()
            except Exception:
                # Fallback to heuristic approach
                pass

        # Fallback: use heuristic unified target construction
        return self._build_heuristic_unified_targets(evidences)

    def _convert_evidence_to_labeled_samples(self, evidences: List[Evidence]) -> List[LabeledSample]:
        """Convert legacy Evidence objects to unified LabeledSample format."""
        if not CORPUS_MINER_AVAILABLE:
            return []

        labeled_samples = []

        for evidence in evidences:
            try:
                # Create pattern match from evidence
                pattern_match = PatternMatch(
                    pattern_id=evidence.pattern_id,
                    span=evidence.span,
                    raw_score=evidence.raw_score,
                    evidence_features=evidence.features
                )

                # Apply unified adjudication heuristics
                reliability_score, label_source = self._adjudicate_evidence(evidence)

                # Classify difficulty based on evidence characteristics
                difficulty = self._classify_evidence_difficulty(evidence)

                # Create labeled sample
                labeled_sample = LabeledSample(
                    context={
                        "evidence_span": evidence.span,
                        "track_weights": evidence.track_weights,
                        "pattern_id": evidence.pattern_id
                    },
                    matches=[pattern_match],
                    label=reliability_score,
                    label_source=label_source,
                    difficulty_stratum=difficulty,
                    confidence_breakdown={"legacy_conversion": True}
                )

                labeled_samples.append(labeled_sample)

            except Exception:
                # Skip invalid evidence
                continue

        return labeled_samples

    def _adjudicate_evidence(self, evidence: Evidence) -> Tuple[float, LabelSource]:
        """Apply adjudication heuristics to determine reliability."""

        # Rule 1: Strong single-track evidence
        if len(evidence.track_weights) == 1:
            track_weight = list(evidence.track_weights.values())[0]
            if track_weight > 0.8 and evidence.raw_score > 0.8:
                return min(0.95, evidence.raw_score + 0.1), LabelSource.ADJUDICATION_HEURISTIC

        # Rule 2: Multi-track consensus
        if len(evidence.track_weights) > 1:
            max_weight = max(evidence.track_weights.values())
            total_weight = sum(evidence.track_weights.values())

            if max_weight / total_weight > 0.7:
                # Strong agreement on primary track
                return min(0.9, evidence.raw_score + 0.05), LabelSource.ADJUDICATION_HEURISTIC
            else:
                # Disagreement - soft label
                return 0.4 + (evidence.raw_score * 0.3), LabelSource.WEAK_SUPERVISION

        # Rule 3: High-confidence patterns
        if "cadence" in evidence.pattern_id and evidence.raw_score >= 0.8:
            return min(0.92, evidence.raw_score + 0.07), LabelSource.ADJUDICATION_HEURISTIC

        # Rule 4: Default reliability based on raw score
        reliability = np.clip(evidence.raw_score, 0.2, 0.85)
        return reliability, LabelSource.WEAK_SUPERVISION

    def _classify_evidence_difficulty(self, evidence: Evidence) -> DifficultyStratum:
        """Classify evidence difficulty for stratification."""

        # Check for complexity indicators
        if "chromatic" in evidence.pattern_id or "secondary" in evidence.pattern_id:
            return DifficultyStratum.CHROMATIC_MODERATE

        elif "modal" in evidence.pattern_id or "dorian" in evidence.pattern_id:
            return DifficultyStratum.MODAL_COMPLEX

        elif "cadence" in evidence.pattern_id and evidence.raw_score > 0.8:
            return DifficultyStratum.DIATONIC_SIMPLE

        else:
            return DifficultyStratum.CHROMATIC_MODERATE

    def _build_heuristic_unified_targets(self, evidences: List[Evidence]) -> List[float]:
        """
        Fallback heuristic target construction when corpus pipeline unavailable.

        This maintains the unified approach but without corpus mining integration.
        """
        targets = []

        for evidence in evidences:
            reliability_score, _ = self._adjudicate_evidence(evidence)
            targets.append(reliability_score)

        return targets

    def _build_annotation_targets(self, evidences: List[Evidence], annotations: List[Any]) -> List[float]:
        """
        Build targets using legacy annotations for backward compatibility.

        When annotations are provided, they override the unified heuristics,
        preserving the original behavior for existing test cases.

        Handles both 1:1 mapping and overlapping annotation scenarios.
        """
        targets = []

        for evidence in evidences:
            # Case 1: 1:1 mapping (same length lists)
            if len(annotations) == len(evidences):
                # Find corresponding annotation by index
                evidence_idx = evidences.index(evidence)
                annotation = annotations[evidence_idx] if evidence_idx < len(annotations) else None

                if annotation is not None:
                    target = self._compute_target_from_annotation(evidence, annotation)
                    targets.append(target)
                else:
                    reliability_score, _ = self._adjudicate_evidence(evidence)
                    targets.append(reliability_score)

            # Case 2: Find all overlapping annotations for this evidence
            else:
                overlapping_annotations = [
                    ann for ann in annotations
                    if ann is not None and hasattr(ann, 'span') and self._spans_overlap(evidence.span, ann.span)
                ]

                if overlapping_annotations:
                    if len(overlapping_annotations) == 1:
                        # Single overlapping annotation
                        target = self._compute_target_from_annotation(evidence, overlapping_annotations[0])
                        targets.append(target)
                    else:
                        # Multiple overlapping annotations - compute weighted average
                        target = self._compute_weighted_annotation_target(evidence, overlapping_annotations)
                        targets.append(target)
                else:
                    # No overlapping annotations - use heuristic
                    reliability_score, _ = self._adjudicate_evidence(evidence)
                    targets.append(reliability_score)

        return targets

    def _compute_target_from_annotation(self, evidence: Evidence, annotation: Any) -> float:
        """Extract confidence from annotation and apply type-based adjustments."""
        if not hasattr(annotation, 'confidence'):
            reliability_score, _ = self._adjudicate_evidence(evidence)
            return reliability_score

        base_confidence = annotation.confidence

        # Apply type matching logic from legacy implementation
        evidence_types = set(evidence.track_weights.keys())
        if hasattr(annotation, 'analysis_type'):
            if annotation.analysis_type in evidence_types:
                # Type matches - use full confidence
                return base_confidence
            elif annotation.analysis_type == "hybrid" and evidence_types:
                # Hybrid annotation with any evidence type
                return base_confidence * 0.9
            else:
                # Type mismatch - reduce confidence
                return base_confidence * 0.7
        else:
            # No analysis_type - use full confidence
            return base_confidence

    def _compute_weighted_annotation_target(self, evidence: Evidence, annotations: List[Any]) -> float:
        """Compute weighted average target from multiple overlapping annotations."""
        weighted_sum = 0.0
        total_weight = 0.0

        for annotation in annotations:
            # Compute overlap ratio as weight
            overlap_ratio = self._compute_overlap_ratio(evidence.span, annotation.span)
            adjusted_target = self._compute_target_from_annotation(evidence, annotation)
            weighted_sum += adjusted_target * overlap_ratio
            total_weight += overlap_ratio

        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            reliability_score, _ = self._adjudicate_evidence(evidence)
            return reliability_score

    def _spans_overlap(self, span1: Tuple[int, int], span2: Tuple[int, int]) -> bool:
        """Check if two spans overlap."""
        return span1[0] < span2[1] and span2[0] < span1[1]

    def _compute_overlap_ratio(self, span1: Tuple[int, int], span2: Tuple[int, int]) -> float:
        """Compute overlap ratio between two spans."""
        if not self._spans_overlap(span1, span2):
            return 0.0

        overlap_start = max(span1[0], span2[0])
        overlap_end = min(span1[1], span2[1])
        overlap_length = overlap_end - overlap_start

        span1_length = span1[1] - span1[0]
        return overlap_length / span1_length if span1_length > 0 else 0.0

    # Legacy compatibility methods (delegate to unified approach)

    def build_corpus_annotations(self, corpus_data: Dict[str, Any]) -> List[Any]:
        """Legacy method for compatibility - delegates to unified pipeline."""
        # In the unified approach, corpus processing is handled by the corpus mining pipeline
        # This method is kept for compatibility but returns empty list
        return []

    def _compute_target_for_evidence(self, evidence: Evidence, annotations: List[Any]) -> float:
        """Legacy method for compatibility."""
        reliability_score, _ = self._adjudicate_evidence(evidence)
        return reliability_score


# Legacy compatibility alias
TargetBuilder = UnifiedTargetBuilder