"""
Educational service for enriching harmonic analysis results.

Transforms technical analysis output into educational learning experiences
by providing context, examples, and practice suggestions.
"""

from typing import Any, Dict, List, Optional

from ..core.pattern_engine.glossary_service import GlossaryService
from .knowledge_base import KnowledgeBase
from .types import (
    EducationalCard,
    EducationalContext,
    FullExplanation,
    LearningLevel,
    PatternSummary,
    ProgressionExample,
    RelatedConcept,
)


class EducationalService:
    """
    Enriches harmonic analysis results with educational context.

    Provides learning-level-appropriate explanations, musical examples,
    and practice suggestions based on the knowledge base.
    """

    def __init__(self, knowledge_base: Optional[KnowledgeBase] = None):
        """
        Initialize educational service.

        Args:
            knowledge_base: KnowledgeBase instance. If None, creates default.
        """
        # Opening move: set up our knowledge sources
        self.kb = knowledge_base if knowledge_base else KnowledgeBase()
        self.glossary = GlossaryService()

    def explain_pattern(
        self, pattern_id: str, level: LearningLevel = LearningLevel.BEGINNER
    ) -> Optional[EducationalContext]:
        """
        Get comprehensive educational explanation for a pattern.

        Args:
            pattern_id: Pattern identifier (e.g., "cadence.authentic.perfect")
            level: Learning level for explanation

        Returns:
            EducationalContext with level-appropriate content
        """
        return self.kb.get_concept(pattern_id, level)

    def explain_pattern_full(self, pattern_id: str) -> Optional[FullExplanation]:
        """
        Get complete Bernstein-style explanation with progressive disclosure.

        Opening move: Delegate to knowledge base for full explanation.
        Victory lap: Return complete explanation with Layer 1 and optional Layer 2.

        Args:
            pattern_id: Pattern identifier (e.g., "cadence.authentic.perfect")

        Returns:
            FullExplanation if found, None otherwise
        """
        return self.kb.get_full_explanation(pattern_id)

    def get_related_learning(
        self, pattern_id: str, relationship_type: str = "all"
    ) -> List[RelatedConcept]:
        """
        Get related concepts for further learning.

        Args:
            pattern_id: Current pattern
            relationship_type: Type of relationship to explore

        Returns:
            List of related concepts with descriptions
        """
        return self.kb.get_related_concepts(pattern_id, relationship_type)

    def get_musical_examples(self, pattern_id: str) -> List[ProgressionExample]:
        """
        Get playable musical examples for a pattern.

        Args:
            pattern_id: Pattern to get examples for

        Returns:
            List of progression examples
        """
        return self.kb.get_progression_examples(pattern_id)

    def explain_function(self, function_abbr: str) -> Optional[Dict[str, str]]:
        """
        Get musician-friendly explanation of harmonic function.

        Args:
            function_abbr: Function abbreviation (T, D, PD, etc.)

        Returns:
            Dictionary with function explanation
        """
        return self.kb.get_function_explanation(function_abbr)

    def generate_practice_suggestions(
        self, pattern_ids: List[str], level: LearningLevel = LearningLevel.BEGINNER
    ) -> List[str]:
        """
        Generate practice exercises based on detected patterns.

        Args:
            pattern_ids: List of patterns found in analysis
            level: Learning level for suggestions

        Returns:
            List of practice suggestions
        """
        # Opening move: collect all practice suggestions
        suggestions = []

        for pattern_id in pattern_ids:
            context = self.kb.get_concept(pattern_id, level)
            if context and context.practice_suggestions:
                suggestions.extend(context.practice_suggestions)

        # Victory lap: deduplicate and return
        return list(dict.fromkeys(suggestions))  # Preserves order while removing dupes

    def create_learning_path(
        self, start_pattern: str, target_pattern: Optional[str] = None
    ) -> List[str]:
        """
        Create a learning path from one concept to another.

        Args:
            start_pattern: Starting concept
            target_pattern: Target concept (or None for basic progression)

        Returns:
            Ordered list of concepts to learn
        """
        # Opening move: build path from prerequisites
        path: List[str] = []
        current = start_pattern

        # Add prerequisites first
        related = self.kb.get_related_concepts(current, "builds_from")
        for concept in related:
            if concept.concept_id not in path:
                path.insert(0, concept.concept_id)

        # Add current concept
        path.append(current)

        # Add next steps
        related = self.kb.get_related_concepts(current, "leads_to")
        for concept in related:
            if concept.concept_id not in path:
                path.append(concept.concept_id)

        # Victory lap: return the learning sequence
        return path

    def get_comparison(
        self,
        pattern_a: str,
        pattern_b: str,
        level: LearningLevel = LearningLevel.INTERMEDIATE,
    ) -> Dict[str, Any]:
        """
        Compare two patterns for educational purposes.

        Args:
            pattern_a: First pattern ID
            pattern_b: Second pattern ID
            level: Learning level for comparison

        Returns:
            Dictionary with comparison information
        """
        # Opening move: get both concepts
        context_a = self.kb.get_concept(pattern_a, level)
        context_b = self.kb.get_concept(pattern_b, level)

        if not context_a or not context_b:
            return {}

        # Main play: build comparison
        similarities: List[str] = []
        differences: List[str] = []
        comparison: Dict[str, Any] = {
            "pattern_a": {
                "id": pattern_a,
                "summary": context_a.summary,
                "key_points": context_a.key_points,
            },
            "pattern_b": {
                "id": pattern_b,
                "summary": context_b.summary,
                "key_points": context_b.key_points,
            },
            "similarities": similarities,
            "differences": differences,
            "when_to_use_each": {},
        }

        # Check if they're listed as contrasts in the knowledge base
        for related in context_a.related_concepts:
            if (
                related.concept_id == pattern_b
                and related.relationship == "contrasts_with"
            ):
                differences.append(f"{pattern_a} contrasts with {pattern_b}")

        # Victory lap: return comparison analysis
        return comparison

    def list_available_concepts(self) -> List[str]:
        """Get list of all concepts in knowledge base."""
        return self.kb.list_all_concepts()

    def get_pattern_family_overview(self, family: str) -> Optional[Dict]:
        """Get educational overview of a pattern family."""
        return self.kb.get_pattern_family_info(family)

    def get_summary(
        self, pattern_id: str, level: LearningLevel = LearningLevel.BEGINNER
    ) -> Optional[PatternSummary]:
        """
        Get lightweight pattern summary for card display.

        Opening move: Delegate to knowledge base with fallback logic.

        Args:
            pattern_id: Pattern identifier (e.g., "cadence.authentic.perfect")
            level: Learning level for summary

        Returns:
            PatternSummary if found, None otherwise
        """
        return self.kb.get_summary(pattern_id, level)

    def enrich_analysis(
        self,
        detected_patterns: List[Any],
        level: LearningLevel = LearningLevel.BEGINNER,
    ) -> List[EducationalCard]:
        """
        Map detected pattern IDs to educational cards.

        Opening move: Extract pattern IDs from analysis results.
        Main play: Look up summaries with normalization and logging.
        Victory lap: Return list of educational cards.

        Args:
            detected_patterns: List of pattern match objects or dicts with 'pattern_id'
            level: Learning level for summaries

        Returns:
            List of EducationalCard objects for matched patterns
        """
        # Opening move: extract pattern IDs and positions from various input formats
        pattern_data = []
        for pattern in detected_patterns:
            pattern_id = None
            pattern_start = 0  # Default to 0 if no position info

            if isinstance(pattern, dict):
                pattern_id = pattern.get("pattern_id") or pattern.get("id")
                pattern_start = pattern.get("start", 0)
            elif hasattr(pattern, "pattern_id"):
                pattern_id = pattern.pattern_id
                pattern_start = getattr(pattern, "start", 0)
            elif hasattr(pattern, "id"):
                pattern_id = pattern.id
                pattern_start = getattr(pattern, "start", 0)
            else:
                # Time to tackle the tricky bit - try str conversion
                pattern_id = str(pattern)

            if pattern_id:
                pattern_data.append({"id": pattern_id, "start": pattern_start})

        # Main play: look up summaries for each pattern
        cards = []
        for pdata in pattern_data:
            pattern_id = pdata["id"]
            pattern_start = pdata["start"]

            summary = self.get_summary(pattern_id, level)
            if summary:
                # Big play: Get visualization hints from first progression example
                visualization = None
                progression_examples = self.kb.get_progression_examples(pattern_id)
                if progression_examples and progression_examples[0].visualization:
                    raw_viz = progression_examples[0].visualization

                    # Critical: Adjust bracket range based on pattern position
                    # Knowledge base uses indices relative to the example progression,
                    # but we need indices relative to the user's full chord progression
                    from harmonic_analysis.educational.types import VisualizationHints

                    # Adjust bracket indices by pattern start position
                    if raw_viz.bracket_range:
                        # bracket_range is a dict with 'start' and 'end' keys
                        original_range = raw_viz.bracket_range
                        adjusted_range = {
                            "start": original_range["start"] + pattern_start,
                            "end": original_range["end"] + pattern_start,
                        }
                        # Create new VisualizationHints with adjusted bracket
                        visualization = VisualizationHints(
                            chord_colors=raw_viz.chord_colors,
                            bracket_range=adjusted_range,
                        )
                    else:
                        visualization = raw_viz

                cards.append(
                    EducationalCard(
                        pattern_id=summary.pattern_id,
                        title=summary.title,
                        summary=summary.summary,
                        category=summary.category,
                        difficulty=summary.difficulty,
                        visualization=visualization,
                    )
                )
            else:
                # Here's where we log unmatched IDs for observability
                # (This looks odd, but it saves us from silent failures)
                import logging

                logging.debug(f"No educational content found for pattern: {pattern_id}")

        # Final whistle: apply pattern merging and prioritization before returning
        from . import pattern_merger

        cards = pattern_merger.merge_and_prioritize(cards)

        # Victory lap: return the educational cards
        return cards
