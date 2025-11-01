"""
Tests for EducationalService integration with pattern merger.

Validates that enrich_analysis returns merged and prioritized results.
"""

import pytest

from harmonic_analysis.educational import EducationalService, LearningLevel

# Mark entire module as requiring educational extra
pytestmark = pytest.mark.educational


class TestEducationalServiceMerger:
    """Test EducationalService integration with pattern merger."""

    def test_enrich_analysis_preserves_pac_and_iac(self):
        """
        When both PAC and IAC detected, both cards are returned (no merging).
        """
        service = EducationalService()

        # Setup: mock detected patterns for PAC + IAC
        detected_patterns = [
            {"pattern_id": "functional.cadence.authentic.perfect", "start": 0},
            {"pattern_id": "functional.cadence.authentic.imperfect", "start": 0},
        ]

        # Execute: enrich analysis
        result = service.enrich_analysis(detected_patterns, LearningLevel.BEGINNER)

        # Verify: should return 2 cards (PAC + IAC, no merging)
        assert len(result) == 2
        pattern_ids = [card.pattern_id for card in result]
        assert "functional.cadence.authentic.perfect" in pattern_ids
        assert "functional.cadence.authentic.imperfect" in pattern_ids
        # Both should be cadential category
        assert all(card.category == "cadential" for card in result)
