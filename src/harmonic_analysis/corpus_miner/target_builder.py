"""
Unified Target Builder for corpus-based ground truth.
"""

import logging
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np

from .types import CalibrationBucket, DifficultyStratum, LabeledSample, TargetStatistics


class UnifiedTargetBuilder:
    """
    Unified target construction system.

    Builds single reliability targets p(correct | evidence) from
    labeled corpus samples with stratified calibration support.
    """

    def __init__(self, min_bucket_size: int = 10, max_buckets: int = 50):
        self.min_bucket_size = min_bucket_size
        self.max_buckets = max_buckets
        self.logger = logging.getLogger(__name__)

    def build_unified_targets(
        self, labeled_samples: List[LabeledSample]
    ) -> Tuple[np.ndarray, np.ndarray, TargetStatistics]:
        """
        Build unified reliability targets from labeled corpus samples.

        Args:
            labeled_samples: Samples with adjudicated reliability labels

        Returns:
            Tuple of (raw_scores, reliability_targets, statistics)
        """
        if not labeled_samples:
            raise ValueError("No labeled samples provided")

        # Extract raw scores and reliability labels
        raw_scores: List[float] = []
        reliability_targets: List[float] = []

        for sample in labeled_samples:
            # Extract primary pattern score as raw score
            if sample.matches:
                primary_score = max(match.raw_score for match in sample.matches)
            else:
                primary_score = 0.5  # Neutral score for no matches

            raw_scores.append(primary_score)
            reliability_targets.append(sample.label)

        raw_scores_array = np.array(raw_scores)
        reliability_targets_array = np.array(reliability_targets)

        # Compute statistics
        stats = self._compute_target_statistics(
            labeled_samples, raw_scores_array, reliability_targets_array
        )

        self.logger.info(
            f"Built targets: {len(raw_scores_array)} samples, "
            f"reliability range [{stats.reliability_range[0]:.3f}, "
            f"{stats.reliability_range[1]:.3f}]"
        )

        return raw_scores_array, reliability_targets_array, stats

    def build_stratified_targets(
        self, labeled_samples: List[LabeledSample]
    ) -> Dict[str, CalibrationBucket]:
        """
        Build stratified calibration buckets for difficulty-aware calibration.

        Args:
            labeled_samples: Samples with difficulty stratification

        Returns:
            Dictionary mapping bucket_id -> CalibrationBucket
        """
        # Group samples by difficulty stratum and pattern family
        buckets = defaultdict(list)

        for sample in labeled_samples:
            stratum = sample.difficulty_stratum

            # Determine primary pattern family
            if sample.matches:
                primary_pattern = sample.matches[0].pattern_id
                family = self._extract_pattern_family(primary_pattern)
            else:
                family = "no_patterns"

            bucket_key = f"{stratum.value}_{family}"
            buckets[bucket_key].append(sample)

        # Create calibration buckets with statistics
        calibration_buckets = {}

        for bucket_key, samples in buckets.items():
            if len(samples) >= self.min_bucket_size:
                bucket = self._create_calibration_bucket(bucket_key, samples)
                calibration_buckets[bucket_key] = bucket

        self.logger.info(f"Created {len(calibration_buckets)} stratified buckets")
        return calibration_buckets

    def _extract_pattern_family(self, pattern_id: str) -> str:
        """Extract pattern family from pattern ID."""
        if pattern_id.startswith("cadence"):
            return "cadence"
        elif pattern_id.startswith("modal"):
            return "modal"
        elif pattern_id.startswith("chromatic"):
            return "chromatic"
        else:
            return "functional"

    def _create_calibration_bucket(
        self, bucket_key: str, samples: List[LabeledSample]
    ) -> CalibrationBucket:
        """Create calibration bucket with computed statistics."""
        parts = bucket_key.split("_", 1)
        stratum_name = parts[0]
        family = parts[1] if len(parts) > 1 else "unknown"

        try:
            stratum = DifficultyStratum(stratum_name)
        except ValueError:
            stratum = DifficultyStratum.DIATONIC_SIMPLE

        # Compute statistics
        labels = [sample.label for sample in samples]
        raw_scores = []

        for sample in samples:
            if sample.matches:
                raw_scores.append(max(match.raw_score for match in sample.matches))
            else:
                raw_scores.append(0.5)

        empirical_reliability = float(np.mean(labels))
        label_variance = float(np.var(labels))
        score_range = (min(raw_scores), max(raw_scores)) if raw_scores else (0.0, 1.0)

        return CalibrationBucket(
            stratum=stratum,
            pattern_family=family,
            min_score=score_range[0],
            max_score=score_range[1],
            samples=samples,
            empirical_reliability=empirical_reliability,
            sample_count=len(samples),
            label_variance=label_variance,
        )

    def _compute_target_statistics(
        self,
        labeled_samples: List[LabeledSample],
        raw_scores: np.ndarray,
        reliability_targets: np.ndarray,
    ) -> TargetStatistics:
        """Compute comprehensive statistics for target quality assessment."""

        # Label source distribution
        label_dist: Dict[str, int] = defaultdict(int)
        for sample in labeled_samples:
            label_dist[sample.label_source.value] += 1

        # Difficulty distribution
        difficulty_dist: Dict[str, int] = defaultdict(int)
        for sample in labeled_samples:
            difficulty_dist[sample.difficulty_stratum.value] += 1

        # Pattern family distribution
        family_dist: Dict[str, int] = defaultdict(int)
        for sample in labeled_samples:
            if sample.matches:
                family = self._extract_pattern_family(sample.matches[0].pattern_id)
                family_dist[family] += 1
            else:
                family_dist["no_patterns"] += 1

        # Correlation statistics
        correlation_stats = {}
        try:
            if (
                len(raw_scores) > 1
                and np.std(raw_scores) > 0
                and np.std(reliability_targets) > 0
            ):
                correlation_stats["raw_reliability_corr"] = float(
                    np.corrcoef(raw_scores, reliability_targets)[0, 1]
                )
            else:
                correlation_stats["raw_reliability_corr"] = 0.0

            correlation_stats["raw_score_variance"] = float(np.var(raw_scores))
            correlation_stats["reliability_variance"] = float(
                np.var(reliability_targets)
            )
        except Exception:
            correlation_stats = {
                "raw_reliability_corr": 0.0,
                "raw_score_variance": 0.0,
                "reliability_variance": 0.0,
            }

        return TargetStatistics(
            total_samples=len(labeled_samples),
            label_distribution=dict(label_dist),
            difficulty_distribution=dict(difficulty_dist),
            pattern_family_distribution=dict(family_dist),
            reliability_range=(
                float(np.min(reliability_targets)),
                float(np.max(reliability_targets)),
            ),
            correlation_stats=correlation_stats,
        )
