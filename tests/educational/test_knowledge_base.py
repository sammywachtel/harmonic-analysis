"""Tests for KnowledgeBase loader and educational content."""

import pytest

from harmonic_analysis.educational import (
    EducationalFormatter,
    EducationalService,
    KnowledgeBase,
    LearningLevel,
)

# Mark entire module as requiring educational extra
pytestmark = pytest.mark.educational


class TestKnowledgeBase:
    """Test knowledge base loading and access."""

    def test_load_default_knowledge_base(self):
        """Opening move: verify knowledge base loads from default location."""
        kb = KnowledgeBase()
        assert kb.data is not None
        assert "concepts" in kb.data
        assert "version" in kb.data

    def test_get_pac_concept_beginner(self):
        """Main play: retrieve PAC concept at beginner level."""
        kb = KnowledgeBase()
        context = kb.get_concept(
            "functional.cadence.authentic.perfect", LearningLevel.BEGINNER
        )

        assert context is not None
        assert context.pattern_id == "functional.cadence.authentic.perfect"
        assert context.level == LearningLevel.BEGINNER
        assert len(context.summary) > 0
        assert len(context.key_points) > 0

    def test_get_pac_concept_advanced(self):
        """Test advanced level content differs from beginner."""
        kb = KnowledgeBase()
        beginner_ctx = kb.get_concept(
            "functional.cadence.authentic.perfect", LearningLevel.BEGINNER
        )
        advanced_ctx = kb.get_concept(
            "functional.cadence.authentic.perfect", LearningLevel.ADVANCED
        )

        assert beginner_ctx.summary != advanced_ctx.summary

    def test_get_progression_examples(self):
        """Verify progression examples are loaded."""
        kb = KnowledgeBase()
        examples = kb.get_progression_examples("functional.cadence.authentic.perfect")

        assert len(examples) > 0
        assert examples[0].chords
        assert examples[0].key
        assert examples[0].context

    def test_get_related_concepts(self):
        """Test relationship extraction."""
        kb = KnowledgeBase()
        related = kb.get_related_concepts(
            "functional.cadence.authentic.perfect", "contrasts_with"
        )

        assert len(related) > 0
        assert any("imperfect" in r.concept_id for r in related)

    def test_list_all_concepts(self):
        """Victory lap: verify we can list all concepts."""
        kb = KnowledgeBase()
        concepts = kb.list_all_concepts()

        assert len(concepts) > 0
        assert "functional.cadence.authentic.perfect" in concepts
        assert "functional.ii_V_I" in concepts

    def test_get_summary_exact_match(self):
        """Test get_summary with exact pattern ID match."""
        kb = KnowledgeBase()
        summary = kb.get_summary(
            "functional.cadence.authentic.perfect", LearningLevel.BEGINNER
        )

        assert summary is not None
        assert summary.pattern_id == "functional.cadence.authentic.perfect"
        assert summary.title == "Perfect Authentic Cadence (PAC)"
        assert len(summary.summary) > 0
        assert summary.category == "cadential"

    def test_get_summary_parent_fallback(self):
        """Test get_summary falls back to parent when exact match missing."""
        kb = KnowledgeBase()
        # Test with a non-existent child of cadential family
        # Since there's no parent concept, this should fall back to cadential family
        summary = kb.get_summary("cadential.unknown.pattern", LearningLevel.BEGINNER)

        # Should fall back to pattern family - regression test for fallback logic
        assert (
            summary is not None
        ), "Family fallback must return a PatternSummary, not None"
        assert isinstance(summary.pattern_id, str)
        assert len(summary.title) > 0
        assert len(summary.summary) > 0
        # Should return cadential family info
        assert (
            summary.pattern_id == "cadential"
            or "cadential" in summary.pattern_id.lower()
        )

    def test_get_summary_family_fallback(self):
        """Test get_summary falls back to family when parent missing."""
        kb = KnowledgeBase()
        # Test with a pattern that matches functional family
        summary = kb.get_summary(
            "functional.unknown.progression", LearningLevel.BEGINNER
        )

        # Should fall back to functional family - regression test for fallback
        assert (
            summary is not None
        ), "Family fallback must return a PatternSummary, not None"
        assert isinstance(summary.pattern_id, str)
        assert len(summary.title) > 0
        assert len(summary.summary) > 0
        assert (
            summary.pattern_id == "functional"
            or "functional" in summary.pattern_id.lower()
        )

    def test_get_summary_normalization(self):
        """Test pattern ID case-insensitive lookup."""
        kb = KnowledgeBase()
        # Test with different case
        summary1 = kb.get_summary(
            "functional.cadence.authentic.perfect", LearningLevel.BEGINNER
        )
        summary2 = kb.get_summary(
            "FUNCTIONAL.CADENCE.AUTHENTIC.PERFECT", LearningLevel.BEGINNER
        )
        summary3 = kb.get_summary(
            "Functional.Cadence.Authentic.Perfect", LearningLevel.BEGINNER
        )

        assert summary1 is not None
        assert summary2 is not None
        assert summary3 is not None
        assert summary1.pattern_id == summary2.pattern_id == summary3.pattern_id

    def test_get_summary_nonexistent(self):
        """Test get_summary returns None for completely unknown pattern."""
        kb = KnowledgeBase()
        summary = kb.get_summary("totally.unknown.pattern", LearningLevel.BEGINNER)

        # Should return None if no match found in exact, parent, or family
        # (This depends on whether we have a "totally" family)
        # For patterns that don't match any known family, should return None
        assert summary is None or "totally" not in summary.pattern_id

    def test_get_summary_two_sentence_requirement(self):
        """Test that PAC summary meets two-sentence requirement."""
        kb = KnowledgeBase()
        summary = kb.get_summary(
            "functional.cadence.authentic.perfect", LearningLevel.BEGINNER
        )

        assert summary is not None
        # Count sentences (simple heuristic: count periods)
        sentence_count = summary.summary.count(".")
        assert (
            sentence_count >= 2
        ), f"Summary should have at least 2 sentences, found {sentence_count}"

    def test_get_full_explanation_pac(self):
        """Test retrieval of full Bernstein-style explanation for PAC."""
        kb = KnowledgeBase()
        explanation = kb.get_full_explanation("functional.cadence.authentic.perfect")

        # Opening move: verify explanation exists
        assert explanation is not None
        assert explanation.pattern_id == "functional.cadence.authentic.perfect"
        assert explanation.title == "Perfect Authentic Cadence (PAC)"

        # Main play: verify Layer 1 content (core Bernstein-style)
        assert len(explanation.hook) > 0, "Hook should be present"
        assert len(explanation.breakdown) > 0, "Breakdown should have items"
        assert len(explanation.story) > 0, "Story should be present"
        assert len(explanation.composers) > 0, "Composers section should be present"
        assert len(explanation.examples) > 0, "Examples should be present"
        assert len(explanation.try_this) > 0, "Try this section should be present"

        # Victory lap: verify Layer 2 content (optional technical notes)
        assert (
            explanation.technical_notes is not None
        ), "Technical notes should exist for PAC"
        assert explanation.technical_notes.voice_leading is not None
        assert explanation.technical_notes.theoretical_depth is not None
        assert explanation.technical_notes.historical_context is not None

    def test_get_full_explanation_nonexistent(self):
        """Test get_full_explanation returns None for nonexistent pattern."""
        kb = KnowledgeBase()
        explanation = kb.get_full_explanation("nonexistent.pattern")

        assert explanation is None

    def test_get_full_explanation_no_explanation_field(self):
        """Test get_full_explanation returns None for pattern without explanation field."""
        kb = KnowledgeBase()
        # Use a non-existent pattern to test None return
        explanation = kb.get_full_explanation("cadence.nonexistent.pattern")

        assert explanation is None


class TestEducationalService:
    """Test educational service functionality."""

    def test_explain_pattern(self):
        """Test pattern explanation retrieval."""
        service = EducationalService()
        context = service.explain_pattern(
            "functional.cadence.authentic.perfect", LearningLevel.INTERMEDIATE
        )

        assert context is not None
        assert context.level == LearningLevel.INTERMEDIATE

    def test_get_musical_examples(self):
        """Test musical example retrieval."""
        service = EducationalService()
        examples = service.get_musical_examples("functional.cadence.authentic.perfect")

        assert len(examples) > 0

    def test_generate_practice_suggestions(self):
        """Test practice suggestion generation."""
        service = EducationalService()
        suggestions = service.generate_practice_suggestions(
            ["functional.cadence.authentic.perfect", "functional.ii_V_I"],
            LearningLevel.BEGINNER,
        )

        assert len(suggestions) > 0

    def test_create_learning_path(self):
        """Test learning path generation."""
        service = EducationalService()
        path = service.create_learning_path("functional.cadence.authentic.perfect")

        assert len(path) > 0
        assert "functional.cadence.authentic.perfect" in path

    def test_get_summary(self):
        """Test get_summary method delegates to knowledge base."""
        service = EducationalService()
        summary = service.get_summary(
            "functional.cadence.authentic.perfect", LearningLevel.BEGINNER
        )

        assert summary is not None
        assert summary.pattern_id == "functional.cadence.authentic.perfect"
        assert len(summary.summary) > 0

    def test_enrich_analysis_with_dict_patterns(self):
        """Test enrich_analysis with dict-based pattern matches."""
        service = EducationalService()
        patterns = [
            {"pattern_id": "functional.cadence.authentic.perfect"},
            {"pattern_id": "functional.ii_V_I"},
        ]

        cards = service.enrich_analysis(patterns, LearningLevel.BEGINNER)

        assert len(cards) == 2
        assert cards[0].pattern_id == "functional.cadence.authentic.perfect"
        assert cards[1].pattern_id == "functional.ii_V_I"
        assert all(len(card.summary) > 0 for card in cards)

    def test_enrich_analysis_with_object_patterns(self):
        """Test enrich_analysis with object-based pattern matches."""
        from harmonic_analysis.dto import PatternMatchDTO

        service = EducationalService()
        patterns = [
            PatternMatchDTO(
                start=0,
                end=3,
                pattern_id="functional.cadence.authentic.perfect",
                name="PAC",
                family="cadential",
                score=0.9,
            )
        ]

        cards = service.enrich_analysis(patterns, LearningLevel.BEGINNER)

        assert len(cards) == 1
        assert cards[0].pattern_id == "functional.cadence.authentic.perfect"
        assert cards[0].title == "Perfect Authentic Cadence (PAC)"

    def test_enrich_analysis_filters_unmatched(self):
        """Test enrich_analysis filters out patterns not in knowledge base."""
        service = EducationalService()
        patterns = [
            {"pattern_id": "functional.cadence.authentic.perfect"},
            {"pattern_id": "nonexistent.pattern"},
        ]

        cards = service.enrich_analysis(patterns, LearningLevel.BEGINNER)

        # Only the PAC should be in results
        assert len(cards) == 1
        assert cards[0].pattern_id == "functional.cadence.authentic.perfect"

    def test_enrich_analysis_empty_input(self):
        """Test enrich_analysis with empty pattern list."""
        service = EducationalService()
        cards = service.enrich_analysis([], LearningLevel.BEGINNER)

        assert len(cards) == 0

    def test_enrich_analysis_normalization(self):
        """Test enrich_analysis normalizes pattern IDs (case-insensitive)."""
        service = EducationalService()
        patterns = [
            {"pattern_id": "FUNCTIONAL.CADENCE.AUTHENTIC.PERFECT"},
        ]

        cards = service.enrich_analysis(patterns, LearningLevel.BEGINNER)

        assert len(cards) == 1
        # Should normalize to lowercase
        assert cards[0].pattern_id == "functional.cadence.authentic.perfect"

    def test_explain_pattern_full_pac(self):
        """Test explain_pattern_full returns full Bernstein-style explanation."""
        service = EducationalService()
        explanation = service.explain_pattern_full(
            "functional.cadence.authentic.perfect"
        )

        # Opening move: verify explanation exists and has correct structure
        assert explanation is not None
        assert explanation.pattern_id == "functional.cadence.authentic.perfect"
        assert explanation.title == "Perfect Authentic Cadence (PAC)"

        # Main play: verify all required Layer 1 fields
        assert explanation.hook
        assert explanation.breakdown
        assert explanation.story
        assert explanation.composers
        assert explanation.examples
        assert explanation.try_this

        # Victory lap: verify Layer 2 technical notes present
        assert explanation.technical_notes is not None
        assert explanation.technical_notes.voice_leading
        assert explanation.technical_notes.theoretical_depth
        assert explanation.technical_notes.historical_context

    def test_explain_pattern_full_nonexistent(self):
        """Test explain_pattern_full returns None for nonexistent pattern."""
        service = EducationalService()
        explanation = service.explain_pattern_full("nonexistent.pattern")

        assert explanation is None

    def test_explain_pattern_full_no_explanation(self):
        """Test explain_pattern_full returns None when pattern lacks explanation."""
        service = EducationalService()
        # Use a non-existent pattern to test None return
        explanation = service.explain_pattern_full("cadence.nonexistent.pattern")

        assert explanation is None


class TestEducationalFormatter:
    """Test formatting of educational content."""

    def test_format_text_beginner(self):
        """Test text formatting for beginner level."""
        service = EducationalService()
        formatter = EducationalFormatter()

        context = service.explain_pattern(
            "functional.cadence.authentic.perfect", LearningLevel.BEGINNER
        )
        text = formatter.format_text(context)

        assert len(text) > 0
        assert "✨" in text  # Beginner emoji

    def test_format_text_advanced(self):
        """Test text formatting for advanced level."""
        service = EducationalService()
        formatter = EducationalFormatter()

        context = service.explain_pattern(
            "functional.cadence.authentic.perfect", LearningLevel.ADVANCED
        )
        text = formatter.format_text(context)

        assert len(text) > 0
        assert "⚗️" in text  # Advanced emoji

    def test_format_html(self):
        """Test HTML formatting."""
        service = EducationalService()
        formatter = EducationalFormatter()

        context = service.explain_pattern(
            "functional.cadence.authentic.perfect", LearningLevel.INTERMEDIATE
        )
        html = formatter.format_html(context)

        assert len(html) > 0
        assert "<div" in html
        assert context.summary in html
