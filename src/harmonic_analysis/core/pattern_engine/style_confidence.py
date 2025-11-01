"""
Style-specific confidence calculation for multi-profile harmonic analysis.

This module calculates confidence scores for how well an analysis fits a
particular musical style (jazz, classical, pop, modal) based on pattern
typicality and evidence diversity.
"""

from __future__ import annotations

from typing import List, Set

from harmonic_analysis.core.pattern_engine.profile_manager import Profile
from harmonic_analysis.dto import PatternMatchDTO


class StyleConfidenceCalculator:
    """
    Calculates style-specific confidence scores for harmonic analysis results.

    The confidence calculation combines:
    1. Pattern typicality weighting (how typical is each pattern for this style?)
    2. Evidence diversity bonus (do we have multiple types of evidence?)
    3. Normalization to [0.0, 1.0] range

    This produces a confidence score indicating how well the analysis fits the style.
    """

    def __init__(self, diversity_bonus_rate: float = 0.1):
        """
        Initialize the StyleConfidenceCalculator.

        Args:
            diversity_bonus_rate: Bonus multiplier per additional pattern family.
                                 Default 0.1 means 10% boost per family.
        """
        self.diversity_bonus_rate = diversity_bonus_rate

    def calculate_confidence(
        self,
        patterns: List[PatternMatchDTO],
        profile: Profile,
    ) -> float:
        """
        Calculate confidence score for how well patterns fit a style profile.

        Algorithm:
        1. Weight each pattern's score by its typicality in this style
        2. Sum weighted scores to get base confidence
        3. Apply diversity bonus based on number of distinct pattern families
        4. Normalize to [0.0, 1.0] range

        Args:
            patterns: List of detected patterns from analysis
            profile: Style profile to calculate confidence for

        Returns:
            Confidence score from 0.0 to 1.0
        """
        if not patterns:
            return 0.0

        # Step 1: Calculate weighted score from pattern typicality
        weighted_score = self._calculate_weighted_score(patterns, profile)

        # Step 2: Calculate diversity bonus
        diversity_multiplier = self._calculate_diversity_multiplier(patterns)

        # Step 3: Combine and normalize
        raw_confidence = weighted_score * diversity_multiplier

        # Normalize to [0.0, 1.0] range
        # Using min(1.0, ...) caps the score at 1.0
        # The diversity bonus can push us above 1.0, which we clamp
        normalized_confidence = min(1.0, raw_confidence)

        return normalized_confidence

    def _calculate_weighted_score(
        self,
        patterns: List[PatternMatchDTO],
        profile: Profile,
    ) -> float:
        """
        Calculate base weighted score from pattern typicality.

        Each pattern's score is weighted by how typical it is for this style.
        Jazz patterns get high weights in jazz profile, low in classical, etc.

        Args:
            patterns: List of detected patterns
            profile: Style profile with typicality weights

        Returns:
            Weighted score (unbounded, typically 0.0-1.0 range but can exceed)
        """
        if not patterns:
            return 0.0

        total_weighted = 0.0
        total_base_score = 0.0

        for pattern in patterns:
            # Get how typical this pattern is for the profile
            typicality = profile.get_typicality_weight(pattern.pattern_id)

            # Weight the pattern's score by typicality
            weighted = pattern.score * typicality

            total_weighted += weighted
            total_base_score += pattern.score

        # Normalize by total base score to keep in reasonable range
        # This prevents having more patterns from automatically giving higher confidence
        if total_base_score > 0:
            return total_weighted / total_base_score
        else:
            return 0.0

    def _calculate_diversity_multiplier(
        self,
        patterns: List[PatternMatchDTO],
    ) -> float:
        """
        Calculate diversity bonus multiplier.

        Multiple types of evidence (cadences, schemas, chromatic patterns, etc.)
        increase confidence in the analysis. Each additional pattern family
        adds a bonus.

        Formula: 1.0 + (num_families - 1) * diversity_bonus_rate

        Examples (with default 0.1 rate):
        - 1 family: 1.0 (no bonus)
        - 2 families: 1.1 (10% boost)
        - 3 families: 1.2 (20% boost)
        - 4 families: 1.3 (30% boost)

        Args:
            patterns: List of detected patterns

        Returns:
            Diversity multiplier (>= 1.0)
        """
        if not patterns:
            return 1.0

        # Extract unique pattern families
        families: Set[str] = {pattern.family for pattern in patterns}

        # Calculate bonus: starts at 1.0, adds rate per additional family
        # (num_families - 1) because we don't give bonus for just one family
        num_families = len(families)
        multiplier = 1.0 + (num_families - 1) * self.diversity_bonus_rate

        return multiplier

    def calculate_multi_style_confidence(
        self,
        patterns: List[PatternMatchDTO],
        profiles: List[Profile],
    ) -> dict[str, float]:
        """
        Calculate confidence scores for multiple style profiles.

        This is a convenience method that calculates confidence for each profile
        and returns a dictionary mapping profile names to confidence scores.

        The scores are NOT normalized relative to each other - each is
        independently calculated. Use normalize_confidence_scores() if you
        want relative normalization.

        Args:
            patterns: List of detected patterns from analysis
            profiles: List of style profiles to calculate confidence for

        Returns:
            Dictionary mapping profile name to confidence score (0.0-1.0)
        """
        confidence_scores = {}

        for profile in profiles:
            score = self.calculate_confidence(patterns, profile)
            confidence_scores[profile.name] = score

        return confidence_scores

    def normalize_confidence_scores(
        self,
        scores: dict[str, float],
    ) -> dict[str, float]:
        """
        Normalize confidence scores to sum to 1.0 (probability distribution).

        This converts absolute confidence scores into relative probabilities.
        Useful when you want to show "this analysis is 60% jazz,
        30% classical, 10% pop".

        Args:
            scores: Dictionary of profile name to confidence score

        Returns:
            Dictionary of profile name to normalized score (sum = 1.0)
        """
        if not scores:
            return {}

        total = sum(scores.values())

        if total == 0:
            # If all scores are 0, distribute equally
            equal_share = 1.0 / len(scores)
            return {name: equal_share for name in scores}

        # Normalize so sum = 1.0
        return {name: score / total for name, score in scores.items()}

    def select_dominant_style(
        self,
        scores: dict[str, float],
        profile_focus: str | None = None,
        focus_weight: float = 1.2,
    ) -> str:
        """
        Select the dominant style based on confidence scores.

        If profile_focus is specified, that profile gets a weight boost
        before selection.

        Args:
            scores: Dictionary of profile name to confidence score
            profile_focus: Optional profile to weight higher (e.g., "jazz")
            focus_weight: Multiplier for focused profile (default 1.2 = 20% boost)

        Returns:
            Name of the profile with highest (weighted) confidence

        Raises:
            ValueError: If scores is empty
        """
        if not scores:
            raise ValueError("Cannot select dominant style from empty scores")

        # Apply focus weight if specified
        weighted_scores = dict(scores)
        if profile_focus and profile_focus in weighted_scores:
            weighted_scores[profile_focus] *= focus_weight

        # Select highest score
        dominant = max(weighted_scores, key=weighted_scores.get)  # type: ignore
        return dominant
