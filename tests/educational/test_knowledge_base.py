"""Tests for KnowledgeBase loader and educational content."""

from harmonic_analysis.educational import (
    EducationalFormatter,
    EducationalService,
    KnowledgeBase,
    LearningLevel,
)


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
        context = kb.get_concept("cadence.authentic.perfect", LearningLevel.BEGINNER)

        assert context is not None
        assert context.pattern_id == "cadence.authentic.perfect"
        assert context.level == LearningLevel.BEGINNER
        assert len(context.summary) > 0
        assert len(context.key_points) > 0

    def test_get_pac_concept_advanced(self):
        """Test advanced level content differs from beginner."""
        kb = KnowledgeBase()
        beginner_ctx = kb.get_concept(
            "cadence.authentic.perfect", LearningLevel.BEGINNER
        )
        advanced_ctx = kb.get_concept(
            "cadence.authentic.perfect", LearningLevel.ADVANCED
        )

        assert beginner_ctx.summary != advanced_ctx.summary

    def test_get_progression_examples(self):
        """Verify progression examples are loaded."""
        kb = KnowledgeBase()
        examples = kb.get_progression_examples("cadence.authentic.perfect")

        assert len(examples) > 0
        assert examples[0].chords
        assert examples[0].key
        assert examples[0].context

    def test_get_related_concepts(self):
        """Test relationship extraction."""
        kb = KnowledgeBase()
        related = kb.get_related_concepts("cadence.authentic.perfect", "contrasts_with")

        assert len(related) > 0
        assert any("imperfect" in r.concept_id for r in related)

    def test_list_all_concepts(self):
        """Victory lap: verify we can list all concepts."""
        kb = KnowledgeBase()
        concepts = kb.list_all_concepts()

        assert len(concepts) > 0
        assert "cadence.authentic.perfect" in concepts
        assert "functional.ii_V_I" in concepts


class TestEducationalService:
    """Test educational service functionality."""

    def test_explain_pattern(self):
        """Test pattern explanation retrieval."""
        service = EducationalService()
        context = service.explain_pattern(
            "cadence.authentic.perfect", LearningLevel.INTERMEDIATE
        )

        assert context is not None
        assert context.level == LearningLevel.INTERMEDIATE

    def test_get_musical_examples(self):
        """Test musical example retrieval."""
        service = EducationalService()
        examples = service.get_musical_examples("cadence.authentic.perfect")

        assert len(examples) > 0

    def test_generate_practice_suggestions(self):
        """Test practice suggestion generation."""
        service = EducationalService()
        suggestions = service.generate_practice_suggestions(
            ["cadence.authentic.perfect", "functional.ii_V_I"], LearningLevel.BEGINNER
        )

        assert len(suggestions) > 0

    def test_create_learning_path(self):
        """Test learning path generation."""
        service = EducationalService()
        path = service.create_learning_path("cadence.authentic.perfect")

        assert len(path) > 0
        assert "cadence.authentic.perfect" in path


class TestEducationalFormatter:
    """Test formatting of educational content."""

    def test_format_text_beginner(self):
        """Test text formatting for beginner level."""
        service = EducationalService()
        formatter = EducationalFormatter()

        context = service.explain_pattern(
            "cadence.authentic.perfect", LearningLevel.BEGINNER
        )
        text = formatter.format_text(context)

        assert len(text) > 0
        assert "✨" in text  # Beginner emoji

    def test_format_text_advanced(self):
        """Test text formatting for advanced level."""
        service = EducationalService()
        formatter = EducationalFormatter()

        context = service.explain_pattern(
            "cadence.authentic.perfect", LearningLevel.ADVANCED
        )
        text = formatter.format_text(context)

        assert len(text) > 0
        assert "⚗️" in text  # Advanced emoji

    def test_format_html(self):
        """Test HTML formatting."""
        service = EducationalService()
        formatter = EducationalFormatter()

        context = service.explain_pattern(
            "cadence.authentic.perfect", LearningLevel.INTERMEDIATE
        )
        html = formatter.format_html(context)

        assert len(html) > 0
        assert "<div" in html
        assert context.summary in html
