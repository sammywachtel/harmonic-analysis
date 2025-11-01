"""
Unit tests for StyleConfidenceCalculator.

Tests cover:
- Basic confidence calculation
- Pattern typicality weighting
- Evidence diversity bonus
- Multi-style confidence calculation
- Confidence normalization
- Dominant style selection
"""

import pytest

from harmonic_analysis.core.pattern_engine.profile_manager import Profile
from harmonic_analysis.core.pattern_engine.style_confidence import (
    StyleConfidenceCalculator,
)
from harmonic_analysis.dto import PatternMatchDTO


class TestStyleConfidenceCalculator:
    """Test basic confidence calculation."""

    def test_empty_patterns_returns_zero(self):
        """Empty pattern list returns 0.0 confidence."""
        calculator = StyleConfidenceCalculator()
        profile = Profile(name="test", display_name="Test")

        confidence = calculator.calculate_confidence([], profile)

        assert confidence == 0.0

    def test_single_pattern_neutral_typicality(self):
        """Single pattern with neutral typicality (0.5) returns normalized score."""
        calculator = StyleConfidenceCalculator()
        profile = Profile(name="test", display_name="Test")

        patterns = [
            PatternMatchDTO(
                start=0,
                end=2,
                pattern_id="unknown.pattern",
                name="Unknown",
                family="unknown",
                score=0.8,
            )
        ]

        # Pattern has default typicality 0.5, no diversity bonus (1 family)
        # Weighted = 0.8 * 0.5 = 0.4
        # Normalized = 0.4 / 0.8 = 0.5
        confidence = calculator.calculate_confidence(patterns, profile)

        assert confidence == pytest.approx(0.5, abs=0.01)

    def test_high_typicality_increases_confidence(self):
        """High typicality weight increases confidence."""
        calculator = StyleConfidenceCalculator()
        profile = Profile(
            name="jazz",
            display_name="Jazz",
            typicality_weights={"jazz.pattern": 0.95},
        )

        patterns = [
            PatternMatchDTO(
                start=0,
                end=2,
                pattern_id="jazz.pattern",
                name="Jazz Pattern",
                family="functional",
                score=0.8,
            )
        ]

        # Weighted = 0.8 * 0.95 = 0.76
        # Normalized = 0.76 / 0.8 = 0.95
        confidence = calculator.calculate_confidence(patterns, profile)

        assert confidence == pytest.approx(0.95, abs=0.01)

    def test_low_typicality_decreases_confidence(self):
        """Low typicality weight decreases confidence."""
        calculator = StyleConfidenceCalculator()
        profile = Profile(
            name="classical",
            display_name="Classical",
            typicality_weights={"jazz.pattern": 0.20},
        )

        patterns = [
            PatternMatchDTO(
                start=0,
                end=2,
                pattern_id="jazz.pattern",
                name="Jazz Pattern",
                family="functional",
                score=0.8,
            )
        ]

        # Weighted = 0.8 * 0.20 = 0.16
        # Normalized = 0.16 / 0.8 = 0.20
        confidence = calculator.calculate_confidence(patterns, profile)

        assert confidence == pytest.approx(0.20, abs=0.01)

    def test_diversity_bonus_multiple_families(self):
        """Multiple pattern families provide diversity bonus."""
        calculator = StyleConfidenceCalculator(diversity_bonus_rate=0.1)
        profile = Profile(
            name="test",
            display_name="Test",
            typicality_weights={
                "cadence.auth": 0.9,
                "functional.progression": 0.9,
            },
        )

        patterns = [
            PatternMatchDTO(
                start=0,
                end=2,
                pattern_id="cadence.auth",
                name="Cadence",
                family="cadence",  # Family 1
                score=0.8,
            ),
            PatternMatchDTO(
                start=2,
                end=4,
                pattern_id="functional.progression",
                name="Progression",
                family="functional",  # Family 2
                score=0.7,
            ),
        ]

        # Base weighted = (0.8*0.9 + 0.7*0.9) / (0.8+0.7) = 1.35/1.5 = 0.9
        # Diversity multiplier = 1 + (2-1)*0.1 = 1.1
        # Final = 0.9 * 1.1 = 0.99
        confidence = calculator.calculate_confidence(patterns, profile)

        assert confidence == pytest.approx(0.99, abs=0.01)

    def test_diversity_bonus_same_family_no_bonus(self):
        """Multiple patterns from same family get no diversity bonus."""
        calculator = StyleConfidenceCalculator(diversity_bonus_rate=0.1)
        profile = Profile(
            name="test",
            display_name="Test",
            typicality_weights={"cadence.*": 0.9},
        )

        patterns = [
            PatternMatchDTO(
                start=0,
                end=2,
                pattern_id="cadence.auth",
                name="Cadence 1",
                family="cadence",  # Same family
                score=0.8,
            ),
            PatternMatchDTO(
                start=2,
                end=4,
                pattern_id="cadence.plagal",
                name="Cadence 2",
                family="cadence",  # Same family
                score=0.7,
            ),
        ]

        # Diversity multiplier = 1 + (1-1)*0.1 = 1.0 (no bonus)
        # Base weighted = (0.8*0.9 + 0.7*0.9) / (0.8+0.7) = 1.35/1.5 = 0.9
        confidence = calculator.calculate_confidence(patterns, profile)

        assert confidence == pytest.approx(0.9, abs=0.01)

    def test_confidence_capped_at_one(self):
        """Confidence is capped at 1.0 even with high scores and bonuses."""
        calculator = StyleConfidenceCalculator(diversity_bonus_rate=0.3)
        profile = Profile(
            name="test",
            display_name="Test",
            typicality_weights={
                "pattern1": 1.0,
                "pattern2": 1.0,
                "pattern3": 1.0,
            },
        )

        patterns = [
            PatternMatchDTO(
                start=0,
                end=1,
                pattern_id="pattern1",
                name="P1",
                family="family1",
                score=1.0,
            ),
            PatternMatchDTO(
                start=1,
                end=2,
                pattern_id="pattern2",
                name="P2",
                family="family2",
                score=1.0,
            ),
            PatternMatchDTO(
                start=2,
                end=3,
                pattern_id="pattern3",
                name="P3",
                family="family3",
                score=1.0,
            ),
        ]

        # This would exceed 1.0 without capping
        confidence = calculator.calculate_confidence(patterns, profile)

        assert confidence == 1.0

    def test_wildcard_typicality_matching(self):
        """Wildcard pattern matching works in confidence calculation."""
        calculator = StyleConfidenceCalculator()
        profile = Profile(
            name="modal",
            display_name="Modal",
            typicality_weights={"modal.*": 0.95},
        )

        patterns = [
            PatternMatchDTO(
                start=0,
                end=2,
                pattern_id="modal.dorian_vamp",
                name="Dorian Vamp",
                family="modal",
                score=0.8,
            )
        ]

        # Should match wildcard and get 0.95 weight
        confidence = calculator.calculate_confidence(patterns, profile)

        assert confidence == pytest.approx(0.95, abs=0.01)


class TestMultiStyleConfidence:
    """Test multi-style confidence calculation."""

    def test_calculate_multi_style_confidence(self):
        """Calculates confidence for multiple profiles."""
        calculator = StyleConfidenceCalculator()

        jazz = Profile(
            name="jazz",
            display_name="Jazz",
            typicality_weights={"jazz.pattern": 0.95, "classical.pattern": 0.30},
        )
        classical = Profile(
            name="classical",
            display_name="Classical",
            typicality_weights={"jazz.pattern": 0.30, "classical.pattern": 0.95},
        )

        patterns = [
            PatternMatchDTO(
                start=0,
                end=2,
                pattern_id="jazz.pattern",
                name="Jazz Pattern",
                family="functional",
                score=0.8,
            )
        ]

        scores = calculator.calculate_multi_style_confidence(
            patterns, [jazz, classical]
        )

        assert "jazz" in scores
        assert "classical" in scores
        # Jazz should have higher confidence for jazz pattern
        assert scores["jazz"] > scores["classical"]

    def test_multi_style_empty_patterns(self):
        """Multi-style with empty patterns returns all zeros."""
        calculator = StyleConfidenceCalculator()

        profiles = [
            Profile(name="jazz", display_name="Jazz"),
            Profile(name="classical", display_name="Classical"),
        ]

        scores = calculator.calculate_multi_style_confidence([], profiles)

        assert scores["jazz"] == 0.0
        assert scores["classical"] == 0.0


class TestConfidenceNormalization:
    """Test confidence score normalization."""

    def test_normalize_confidence_scores(self):
        """Normalization converts to probability distribution."""
        calculator = StyleConfidenceCalculator()

        scores = {
            "jazz": 0.8,
            "classical": 0.6,
            "pop": 0.4,
            "modal": 0.2,
        }

        normalized = calculator.normalize_confidence_scores(scores)

        # Should sum to 1.0
        total = sum(normalized.values())
        assert total == pytest.approx(1.0, abs=0.01)

        # Relative ordering preserved
        assert normalized["jazz"] > normalized["classical"]
        assert normalized["classical"] > normalized["pop"]
        assert normalized["pop"] > normalized["modal"]

    def test_normalize_all_zeros_distributes_equally(self):
        """All zero scores get equal distribution."""
        calculator = StyleConfidenceCalculator()

        scores = {
            "jazz": 0.0,
            "classical": 0.0,
            "pop": 0.0,
        }

        normalized = calculator.normalize_confidence_scores(scores)

        # Each should get 1/3
        assert normalized["jazz"] == pytest.approx(1.0 / 3, abs=0.01)
        assert normalized["classical"] == pytest.approx(1.0 / 3, abs=0.01)
        assert normalized["pop"] == pytest.approx(1.0 / 3, abs=0.01)

    def test_normalize_empty_dict_returns_empty(self):
        """Empty scores dict returns empty normalized dict."""
        calculator = StyleConfidenceCalculator()

        normalized = calculator.normalize_confidence_scores({})

        assert normalized == {}


class TestDominantStyleSelection:
    """Test dominant style selection."""

    def test_select_dominant_style_highest_score(self):
        """Selects style with highest confidence score."""
        calculator = StyleConfidenceCalculator()

        scores = {
            "jazz": 0.92,
            "classical": 0.85,
            "pop": 0.70,
            "modal": 0.60,
        }

        dominant = calculator.select_dominant_style(scores)

        assert dominant == "jazz"

    def test_select_dominant_style_with_focus(self):
        """profile_focus parameter weights that style higher."""
        calculator = StyleConfidenceCalculator()

        scores = {
            "jazz": 0.85,
            "classical": 0.80,  # Close to jazz
        }

        # Without focus, jazz wins
        dominant_no_focus = calculator.select_dominant_style(scores)
        assert dominant_no_focus == "jazz"

        # With classical focus (1.2x weight), classical wins
        # classical: 0.80 * 1.2 = 0.96 > jazz: 0.85
        dominant_with_focus = calculator.select_dominant_style(
            scores, profile_focus="classical", focus_weight=1.2
        )
        assert dominant_with_focus == "classical"

    def test_select_dominant_style_focus_nonexistent_ignored(self):
        """Focusing on nonexistent profile doesn't cause error."""
        calculator = StyleConfidenceCalculator()

        scores = {
            "jazz": 0.85,
            "classical": 0.80,
        }

        # Focus on nonexistent profile is ignored
        dominant = calculator.select_dominant_style(scores, profile_focus="nonexistent")

        assert dominant == "jazz"  # Original highest still wins

    def test_select_dominant_style_empty_raises_error(self):
        """Empty scores raises ValueError."""
        calculator = StyleConfidenceCalculator()

        with pytest.raises(ValueError, match="empty scores"):
            calculator.select_dominant_style({})


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_score_patterns_ignored(self):
        """Patterns with zero score don't break calculation."""
        calculator = StyleConfidenceCalculator()
        profile = Profile(
            name="test",
            display_name="Test",
            typicality_weights={"pattern": 0.9},
        )

        patterns = [
            PatternMatchDTO(
                start=0,
                end=1,
                pattern_id="pattern",
                name="P",
                family="f",
                score=0.0,  # Zero score
            )
        ]

        confidence = calculator.calculate_confidence(patterns, profile)

        # Should not crash, returns 0.0 (can't divide by zero base score)
        assert confidence >= 0.0

    def test_custom_diversity_bonus_rate(self):
        """Custom diversity bonus rate is applied correctly."""
        calculator = StyleConfidenceCalculator(diversity_bonus_rate=0.2)
        profile = Profile(
            name="test",
            display_name="Test",
            typicality_weights={"p1": 1.0, "p2": 1.0},
        )

        patterns = [
            PatternMatchDTO(
                start=0, end=1, pattern_id="p1", name="P1", family="family1", score=0.5
            ),
            PatternMatchDTO(
                start=1, end=2, pattern_id="p2", name="P2", family="family2", score=0.5
            ),
        ]

        # 2 families: multiplier = 1 + (2-1)*0.2 = 1.2
        confidence = calculator.calculate_confidence(patterns, profile)

        # Base = (0.5*1.0 + 0.5*1.0)/(0.5+0.5) = 1.0
        # With 0.2 bonus rate: 1.0 * 1.2 = 1.2, capped at 1.0
        assert confidence == 1.0

    def test_many_pattern_families_increases_confidence(self):
        """Many different pattern families provide larger bonus."""
        calculator = StyleConfidenceCalculator(diversity_bonus_rate=0.1)
        profile = Profile(
            name="test",
            display_name="Test",
            typicality_weights={f"p{i}": 0.8 for i in range(5)},
        )

        patterns = [
            PatternMatchDTO(
                start=i,
                end=i + 1,
                pattern_id=f"p{i}",
                name=f"P{i}",
                family=f"family{i}",
                score=0.6,
            )
            for i in range(5)
        ]

        # 5 families: multiplier = 1 + (5-1)*0.1 = 1.4
        confidence = calculator.calculate_confidence(patterns, profile)

        # Base weighted = (0.6*0.8*5)/(0.6*5) = 0.8
        # With diversity: 0.8 * 1.4 = 1.12, capped at 1.0
        assert confidence == 1.0


class TestIntegrationWithRealProfiles:
    """Integration tests with real profile data."""

    def test_jazz_turnaround_high_confidence_in_jazz(self):
        """Jazz turnaround pattern has high confidence in jazz profile."""
        from harmonic_analysis.core.pattern_engine.profile_manager import ProfileManager

        calculator = StyleConfidenceCalculator()
        manager = ProfileManager()
        jazz = manager.get_profile("jazz")

        patterns = [
            PatternMatchDTO(
                start=0,
                end=4,
                pattern_id="cadence.turnaround",
                name="Turnaround",
                family="cadence",
                score=0.85,
            )
        ]

        confidence = calculator.calculate_confidence(patterns, jazz)

        # Should be high in jazz profile
        assert confidence >= 0.80

    def test_perfect_authentic_cadence_high_in_classical(self):
        """Perfect authentic cadence has high confidence in classical."""
        from harmonic_analysis.core.pattern_engine.profile_manager import ProfileManager

        calculator = StyleConfidenceCalculator()
        manager = ProfileManager()
        classical = manager.get_profile("classical")

        patterns = [
            PatternMatchDTO(
                start=0,
                end=2,
                pattern_id="cadence.authentic.perfect",
                name="Perfect Authentic Cadence",
                family="cadence",
                score=0.9,
            )
        ]

        confidence = calculator.calculate_confidence(patterns, classical)

        # Should be high in classical profile
        assert confidence >= 0.85

    def test_modal_pattern_high_in_modal_profile(self):
        """Modal patterns have high confidence in modal profile."""
        from harmonic_analysis.core.pattern_engine.profile_manager import ProfileManager

        calculator = StyleConfidenceCalculator()
        manager = ProfileManager()
        modal = manager.get_profile("modal")

        patterns = [
            PatternMatchDTO(
                start=0,
                end=3,
                pattern_id="modal.dorian_vamp",
                name="Dorian Vamp",
                family="modal",
                score=0.85,
            )
        ]

        confidence = calculator.calculate_confidence(patterns, modal)

        # Should be very high in modal profile
        assert confidence >= 0.85
