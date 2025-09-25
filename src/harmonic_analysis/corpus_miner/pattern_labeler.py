"""
Pattern Labeler - Unified target construction with adjudication heuristics.
"""

import logging
from dataclasses import asdict
from typing import Dict, List, Optional, Tuple

from ..core.pattern_engine import AnalysisContext, PatternEngine
from .types import (
    AdjudicationRules,
    DifficultyStratum,
    LabeledSample,
    LabelSource,
    PatternMatch,
)


class PatternLabeler:
    """Unified pattern labeling with adjudication heuristics."""

    def __init__(self, adjudication_rules: AdjudicationRules = None):
        self.rules = adjudication_rules or AdjudicationRules()
        self.logger = logging.getLogger(__name__)
        self.pattern_engine = None  # Lazy initialization

    def label_corpus_samples(self, samples: List[Dict[str, any]]) -> List[LabeledSample]:
        """
        Generate unified reliability labels for corpus samples.

        Args:
            samples: List of musical contexts from corpus extractor

        Returns:
            List of labeled samples with p(correct | evidence) targets
        """
        labeled_samples = []

        for sample in samples:
            try:
                labeled_sample = self._label_single_sample(sample)
                if labeled_sample:
                    labeled_samples.append(labeled_sample)
            except Exception as e:
                self.logger.warning(f"Failed to label sample: {e}")
                continue

        self.logger.info(f"Generated {len(labeled_samples)} labeled samples")
        return labeled_samples

    def _label_single_sample(self, sample: Dict[str, any]) -> Optional[LabeledSample]:
        """Generate unified label for a single sample."""
        # For production, use simplified heuristic labeling
        # Real implementation would use pattern engine analysis

        # Extract basic features
        chords = sample.get("chords", [])
        romans = sample.get("roman_numerals", [])

        # Simple pattern detection
        pattern_matches = []
        if len(chords) >= 2:
            # Check for cadence patterns
            if romans[-2:] == ["V", "I"] or chords[-2:] == ["G", "C"]:
                pattern_matches.append(
                    PatternMatch(
                        pattern_id="cadence.authentic.perfect",
                        span=(len(chords) - 2, len(chords)),
                        raw_score=0.85,
                        evidence_features={"cadence_type": "authentic"}
                    )
                )

        # Apply adjudication heuristics
        reliability, label_source, breakdown = self._adjudicate_reliability(
            pattern_matches, sample
        )

        # Determine difficulty
        difficulty = self._classify_difficulty(sample, pattern_matches)

        return LabeledSample(
            context=sample,
            matches=pattern_matches,
            label=reliability,
            label_source=label_source,
            difficulty_stratum=difficulty,
            confidence_breakdown=breakdown
        )

    def _adjudicate_reliability(
        self,
        pattern_matches: List[PatternMatch],
        sample: Dict[str, any]
    ) -> Tuple[float, LabelSource, Dict[str, float]]:
        """Apply adjudication heuristics to determine reliability."""

        # Strong evidence patterns
        strong_patterns = [
            m for m in pattern_matches
            if m.pattern_id in self.rules.consensus_patterns
            and m.raw_score >= self.rules.strong_evidence_threshold
        ]

        if strong_patterns:
            reliability = 0.9
            return reliability, LabelSource.ADJUDICATION_HEURISTIC, {
                "strong_patterns": len(strong_patterns),
                "rule": "strong_evidence"
            }

        # Pattern consensus
        if len(pattern_matches) >= 2:
            avg_score = sum(m.raw_score for m in pattern_matches) / len(pattern_matches)
            if avg_score >= 0.7:
                reliability = 0.85
                return reliability, LabelSource.ADJUDICATION_HEURISTIC, {
                    "pattern_count": len(pattern_matches),
                    "avg_score": avg_score,
                    "rule": "pattern_consensus"
                }

        # Default soft label
        base_confidence = 0.5
        if pattern_matches:
            base_confidence = max(m.raw_score for m in pattern_matches) * 0.8

        return base_confidence, LabelSource.WEAK_SUPERVISION, {
            "base_confidence": base_confidence,
            "rule": "default_heuristic"
        }

    def _classify_difficulty(
        self,
        sample: Dict[str, any],
        pattern_matches: List[PatternMatch]
    ) -> DifficultyStratum:
        """Classify sample difficulty."""

        # Check metadata hints
        metadata = sample.get("metadata", {})
        if "difficulty" in metadata:
            difficulty_map = {
                "simple": DifficultyStratum.DIATONIC_SIMPLE,
                "modal": DifficultyStratum.MODAL_COMPLEX,
                "chromatic": DifficultyStratum.CHROMATIC_MODERATE,
                "jazz": DifficultyStratum.CHROMATIC_MODERATE,
            }
            return difficulty_map.get(
                metadata["difficulty"],
                DifficultyStratum.DIATONIC_SIMPLE
            )

        # Default based on patterns
        if any("modal" in m.pattern_id for m in pattern_matches):
            return DifficultyStratum.MODAL_COMPLEX
        elif any("chromatic" in m.pattern_id for m in pattern_matches):
            return DifficultyStratum.CHROMATIC_MODERATE
        else:
            return DifficultyStratum.DIATONIC_SIMPLE