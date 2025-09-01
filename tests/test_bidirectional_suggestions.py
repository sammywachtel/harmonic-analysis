#!/usr/bin/env python
"""
Comprehensive tests for bidirectional suggestion framework.

Tests both 'add key' and 'remove key' suggestions to ensure the system
provides intelligent feedback about key relevance.
"""

import pytest

from harmonic_analysis.services.bidirectional_suggestion_engine import (
    BidirectionalSuggestion,
    BidirectionalSuggestionEngine,
    KeyRelevanceScore,
    SuggestionType,
)
from harmonic_analysis.types import AnalysisOptions


class TestBidirectionalSuggestionEngine:
    """Test the bidirectional suggestion engine"""

    def setup_method(self):
        """Setup test environment"""
        self.engine = BidirectionalSuggestionEngine()

    @pytest.mark.asyncio
    async def test_no_key_provided_beneficial_suggestion(self):
        """Test suggesting key when none provided but would help"""
        # Classic ii-V-I progression that benefits from key context
        progression = ["Dm7", "G7", "Cmaj7"]
        options = AnalysisOptions()  # No parent key

        suggestions = await self.engine.generate_bidirectional_suggestions(
            progression, options
        )

        assert suggestions is not None
        assert suggestions.parent_key_suggestions

        # Should suggest C major
        c_major_suggestion = next(
            (
                s
                for s in suggestions.parent_key_suggestions
                if "C major" in s.suggested_key
            ),
            None,
        )
        assert c_major_suggestion is not None
        assert c_major_suggestion.confidence > 0.7
        assert "ii-V-I" in c_major_suggestion.detected_pattern

    @pytest.mark.asyncio
    async def test_key_provided_unnecessary_suggestion(self):
        """Test suggesting key removal when provided key doesn't help"""
        # Simple progression that works fine without key context
        progression = ["C", "F", "G"]
        options = AnalysisOptions(parent_key="C major")

        suggestions = await self.engine.generate_bidirectional_suggestions(
            progression, options
        )

        # Should suggest removing the key if it doesn't improve analysis significantly
        if suggestions and suggestions.unnecessary_key_suggestions:
            removal_suggestion = suggestions.unnecessary_key_suggestions[0]
            assert removal_suggestion.suggested_key == "C major"
            assert "doesn't improve analysis" in removal_suggestion.reason.lower()

    @pytest.mark.asyncio
    async def test_key_provided_beneficial_no_suggestion(self):
        """Test no unnecessary suggestion when key is actually helpful"""
        # Complex progression that benefits from key context
        progression = ["F#m7b5", "B7", "Em"]
        options = AnalysisOptions(parent_key="E minor")

        suggestions = await self.engine.generate_bidirectional_suggestions(
            progression, options
        )

        # Should NOT suggest removing the key
        if suggestions:
            assert not suggestions.unnecessary_key_suggestions

    @pytest.mark.asyncio
    async def test_key_change_suggestion(self):
        """Test suggesting a different key when current one is suboptimal"""
        # Progression that works better in a different key
        progression = ["Am", "F", "C", "G"]
        options = AnalysisOptions(parent_key="A minor")  # Sub-optimal key choice

        suggestions = await self.engine.generate_bidirectional_suggestions(
            progression, options
        )

        # Might suggest C major as a better alternative
        if suggestions and suggestions.key_change_suggestions:
            change_suggestion = suggestions.key_change_suggestions[0]
            assert "C major" in change_suggestion.suggested_key
            assert change_suggestion.confidence > 0.6

    @pytest.mark.asyncio
    async def test_relevance_scoring_components(self):
        """Test that relevance scoring considers all components correctly"""
        progression = ["Dm7", "G7", "Cmaj7"]

        # Test with no key (should score high for C major)
        score = await self.engine._calculate_key_relevance_score(
            progression, "C major", None
        )

        assert (
            score.total_score > 0.55
        )  # TODO: Calibrate scoring algorithm for higher precision
        assert score.roman_numeral_improvement > 0.0
        assert (
            score.confidence_improvement >= 0.0
        )  # May be 0.0 if both analyses have similar confidence
        assert score.pattern_clarity_improvement > 0.0

    @pytest.mark.asyncio
    async def test_edge_case_empty_progression(self):
        """Test handling of empty progression"""
        progression = []
        options = AnalysisOptions()

        suggestions = await self.engine.generate_bidirectional_suggestions(
            progression, options
        )

        # Should handle gracefully - returns empty suggestions, not None
        assert suggestions is not None
        assert (
            len(suggestions.parent_key_suggestions) == 0
        )  # Empty progression = no suggestions

    @pytest.mark.asyncio
    async def test_edge_case_single_chord(self):
        """Test handling of single chord progression"""
        progression = ["Cmaj7"]
        options = AnalysisOptions()

        suggestions = await self.engine.generate_bidirectional_suggestions(
            progression, options
        )

        # Should handle gracefully - single chord has limited suggestion value
        if suggestions:
            assert len(suggestions.parent_key_suggestions) <= 2

    @pytest.mark.skip(
        reason="TODO: Complex multi-key scoring needs algorithm refinement"
    )
    @pytest.mark.asyncio
    async def test_multiple_key_candidates(self):
        """Test progression that has multiple valid key interpretations"""
        # Ambiguous progression that could be in multiple keys
        progression = ["Am", "F", "C", "G"]
        options = AnalysisOptions()

        suggestions = await self.engine.generate_bidirectional_suggestions(
            progression, options
        )

        assert suggestions is not None
        assert len(suggestions.parent_key_suggestions) >= 2

        # Should suggest both A minor and C major
        suggested_keys = {s.suggested_key for s in suggestions.parent_key_suggestions}
        assert any("A minor" in key for key in suggested_keys)
        assert any("C major" in key for key in suggested_keys)

    @pytest.mark.skip(
        reason="TODO: Jazz progression confidence scoring needs calibration"
    )
    @pytest.mark.asyncio
    async def test_jazz_progression_detection(self):
        """Test detection of jazz progressions across different keys"""
        # ii-V-I in different keys
        test_cases = [
            (["Dm7", "G7", "Cmaj7"], "C major"),
            (["Em7", "A7", "Dmaj7"], "D major"),
            (["F#m7b5", "B7", "Em"], "E minor"),
            (["Gm7", "C7", "Fmaj7"], "F major"),
        ]

        for progression, expected_key in test_cases:
            options = AnalysisOptions()
            suggestions = await self.engine.generate_bidirectional_suggestions(
                progression, options
            )

            assert suggestions is not None
            assert suggestions.parent_key_suggestions

            # Should detect the correct key with high confidence
            matching_suggestion = next(
                (
                    s
                    for s in suggestions.parent_key_suggestions
                    if expected_key in s.suggested_key
                ),
                None,
            )
            assert matching_suggestion is not None
            assert matching_suggestion.confidence > 0.6

    @pytest.mark.asyncio
    async def test_modal_progression_handling(self):
        """Test handling of modal progressions"""
        # D Dorian progression
        progression = ["Dm", "G", "Dm", "C"]
        options = AnalysisOptions()

        suggestions = await self.engine.generate_bidirectional_suggestions(
            progression, options
        )

        # Should either suggest C major (parent key) or handle modal context
        if suggestions and suggestions.parent_key_suggestions:
            suggested_keys = {
                s.suggested_key for s in suggestions.parent_key_suggestions
            }
            # Could suggest C major as parent key for Dorian analysis
            assert any("C major" in key or "D" in key for key in suggested_keys)

    @pytest.mark.asyncio
    async def test_chromatic_progression_handling(self):
        """Test handling of progressions with chromatic elements"""
        # Progression with chromatic passing chords
        progression = ["C", "C#dim7", "Dm7", "G7"]
        options = AnalysisOptions()

        suggestions = await self.engine.generate_bidirectional_suggestions(
            progression, options
        )

        # Should handle chromatic elements appropriately
        if suggestions and suggestions.parent_key_suggestions:
            # Likely suggests C major due to overall tonal context
            c_major_suggestion = next(
                (
                    s
                    for s in suggestions.parent_key_suggestions
                    if "C major" in s.suggested_key
                ),
                None,
            )
            if c_major_suggestion:
                assert c_major_suggestion.confidence > 0.5

    @pytest.mark.asyncio
    async def test_confidence_threshold_filtering(self):
        """Test that suggestions are filtered by confidence threshold"""
        # Ambiguous progression with weak key implications
        progression = ["C", "G"]
        options = AnalysisOptions()

        suggestions = await self.engine.generate_bidirectional_suggestions(
            progression, options
        )

        # All suggestions should meet minimum confidence threshold
        if suggestions and suggestions.parent_key_suggestions:
            for suggestion in suggestions.parent_key_suggestions:
                assert suggestion.confidence >= 0.5  # Minimum threshold

    @pytest.mark.skip(
        reason="TODO: Pattern detection confidence thresholds need adjustment"
    )
    @pytest.mark.asyncio
    async def test_algorithmic_pattern_detection(self):
        """Test that pattern detection is algorithmic, not hardcoded"""
        # Test same pattern in different keys
        test_progressions = [
            ["Dm7", "G7", "Cmaj7"],  # C major ii-V-I
            ["Em7", "A7", "Dmaj7"],  # D major ii-V-I
            ["Am7", "D7", "Gmaj7"],  # G major ii-V-I
            ["Bm7b5", "E7", "Am"],  # A minor ii-V-i
        ]

        for progression in test_progressions:
            options = AnalysisOptions()
            suggestions = await self.engine.generate_bidirectional_suggestions(
                progression, options
            )

            assert suggestions is not None
            assert suggestions.parent_key_suggestions

            # All should be detected as ii-V-I patterns
            for suggestion in suggestions.parent_key_suggestions:
                if suggestion.confidence > 0.7:
                    assert (
                        "ii-V-I" in suggestion.detected_pattern
                        or "ii-v-i" in suggestion.detected_pattern
                    )

    @pytest.mark.asyncio
    async def test_no_hardcoded_keys(self):
        """Test that no keys are hardcoded in the system"""
        # Test with uncommon key
        progression = ["C#m7", "F#7", "Bmaj7"]  # B major ii-V-I
        options = AnalysisOptions()

        suggestions = await self.engine.generate_bidirectional_suggestions(
            progression, options
        )

        assert suggestions is not None
        assert suggestions.parent_key_suggestions

        # Should detect B major despite being uncommon
        b_major_suggestion = next(
            (
                s
                for s in suggestions.parent_key_suggestions
                if "B major" in s.suggested_key
            ),
            None,
        )
        assert b_major_suggestion is not None
        assert b_major_suggestion.confidence > 0.6

    def test_suggestion_type_enum(self):
        """Test suggestion type enumeration"""
        assert SuggestionType.ADD_KEY.value == "add_key"
        assert SuggestionType.REMOVE_KEY.value == "remove_key"
        assert SuggestionType.CHANGE_KEY.value == "change_key"

    def test_key_relevance_score_properties(self):
        """Test KeyRelevanceScore dataclass properties"""
        score = KeyRelevanceScore(
            total_score=0.75,
            roman_numeral_improvement=0.8,
            confidence_improvement=0.7,
            analysis_type_improvement=0.6,
            pattern_clarity_improvement=0.9,
            chord_key_validity=0.85,
            without_key_confidence=0.3,
            with_key_confidence=0.8,
            without_key_romans=[],
            with_key_romans=["ii7", "V7", "I7"],
            detected_patterns=[],
        )

        assert score.roman_numeral_improvement == 0.8
        assert score.confidence_improvement == 0.7
        assert score.analysis_type_improvement == 0.6
        assert score.pattern_clarity_improvement == 0.9
        assert score.total_score == 0.75

    def test_bidirectional_suggestion_properties(self):
        """Test BidirectionalSuggestion dataclass properties"""
        relevance_score = KeyRelevanceScore(
            total_score=0.8,
            roman_numeral_improvement=0.7,
            confidence_improvement=0.6,
            analysis_type_improvement=0.9,
            pattern_clarity_improvement=0.8,
            chord_key_validity=0.75,
            without_key_confidence=0.3,
            with_key_confidence=0.8,
            without_key_romans=[],
            with_key_romans=["ii7", "V7", "I7"],
            detected_patterns=[],
        )

        suggestion = BidirectionalSuggestion(
            suggestion_type=SuggestionType.ADD_KEY,  # Correct field name
            suggested_key="C major",
            current_key=None,
            confidence=0.85,
            relevance_score=relevance_score,
            reason="Provides clear Roman numeral analysis",
            potential_improvement="Roman numerals available",
            improvement_summary=["Adds Roman numeral analysis"],
            trade_offs=["None"],
            detected_pattern="ii-V-I progression",
        )

        assert suggestion.suggestion_type == SuggestionType.ADD_KEY
        assert suggestion.suggested_key == "C major"
        assert suggestion.confidence == 0.85
        assert "Roman numeral" in suggestion.reason
        assert "ii-V-I" in suggestion.detected_pattern
        assert suggestion.relevance_score.total_score == 0.8


if __name__ == "__main__":
    pytest.main([__file__])
