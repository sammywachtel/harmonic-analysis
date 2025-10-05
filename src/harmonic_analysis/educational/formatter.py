"""
Formatting utilities for educational content.

Formats educational context into human-readable output for different
learning levels and output formats (CLI, HTML, etc.).
"""

from typing import Dict, Optional

from .types import EducationalContext, LearningLevel


class EducationalFormatter:
    """Formats educational content for display."""

    # Emoji mappings for different learning levels
    EMOJI_MAP = {
        LearningLevel.BEGINNER: {
            "summary": "✨",
            "learn": "🎵",
            "why": "🔑",
            "example": "🎼",
            "practice": "📚",
        },
        LearningLevel.INTERMEDIATE: {
            "theory": "🎓",
            "composition": "🎼",
            "technique": "🎹",
            "example": "🎵",
            "practice": "📚",
        },
        LearningLevel.ADVANCED: {
            "analysis": "⚗️",
            "theory": "🔬",
            "history": "🎼",
            "research": "📐",
            "practice": "🎯",
        },
    }

    def format_text(
        self,
        context: EducationalContext,
        include_examples: bool = True,
        include_practice: bool = True,
    ) -> str:
        """
        Format educational context as plain text.

        Args:
            context: Educational context to format
            include_examples: Include musical examples
            include_practice: Include practice suggestions

        Returns:
            Formatted text output
        """
        # Opening move: grab emoji set for this level
        emojis = self.EMOJI_MAP.get(
            context.level, self.EMOJI_MAP[LearningLevel.BEGINNER]
        )
        lines = []

        # Header based on learning level
        if context.level == LearningLevel.BEGINNER:
            lines.append(f"{emojis['summary']} What it is:")
        elif context.level == LearningLevel.INTERMEDIATE:
            lines.append(f"{emojis['theory']} Theory Overview:")
        else:
            lines.append(f"{emojis['analysis']} Advanced Analysis:")

        lines.append(f"   {context.summary}")
        lines.append("")

        # Key points
        if context.key_points:
            if context.level == LearningLevel.BEGINNER:
                lines.append(f"{emojis['learn']} Key Points:")
            else:
                lines.append(f"{emojis['theory']} Essential Concepts:")

            for point in context.key_points:
                lines.append(f"   • {point}")
            lines.append("")

        # Why it matters
        if context.why_it_matters:
            if context.level == LearningLevel.BEGINNER:
                lines.append(f"{emojis['why']} Why it matters:")
            else:
                lines.append(f"{emojis['theory']} Musical Significance:")

            lines.append(f"   {context.why_it_matters}")
            lines.append("")

        # Musical examples
        if include_examples and context.musical_examples:
            lines.append(f"{emojis.get('example', '🎵')} Musical Examples:")
            for ex in context.musical_examples[:3]:  # Limit to 3 examples
                lines.append(f"   • {ex.context}: {ex.chords} ({ex.key})")
            lines.append("")

        # Practice suggestions
        if include_practice and context.practice_suggestions:
            lines.append(f"{emojis.get('practice', '📚')} Practice Ideas:")
            for suggestion in context.practice_suggestions[:3]:  # Limit to 3
                lines.append(f"   • {suggestion}")
            lines.append("")

        # Related concepts
        if context.related_concepts and context.level != LearningLevel.BEGINNER:
            lines.append("📖 Related Concepts:")
            for related in context.related_concepts[:5]:  # Limit to 5
                arrow = (
                    "→"
                    if related.relationship == "leads_to"
                    else "←" if related.relationship == "builds_from" else "↔"
                )
                lines.append(f"   {arrow} {related.concept_id}")
            lines.append("")

        # Misconceptions (intermediate and advanced only)
        if context.common_misconceptions and context.level != LearningLevel.BEGINNER:
            lines.append("⚠️ Common Misconceptions:")
            for misc in context.common_misconceptions:
                lines.append(f"   ❌ Myth: {misc.myth}")
                lines.append(f"   ✅ Reality: {misc.reality}")
                lines.append("")

        # Victory lap: join and return
        return "\n".join(lines)

    def format_html(
        self,
        context: EducationalContext,
        include_examples: bool = True,
        include_practice: bool = True,
    ) -> str:
        """
        Format educational context as HTML.

        Args:
            context: Educational context to format
            include_examples: Include musical examples
            include_practice: Include practice suggestions

        Returns:
            Formatted HTML output
        """
        # Opening move: determine styling based on level
        if context.level == LearningLevel.BEGINNER:
            color = "#22c55e"  # Green - encouraging
            icon = "🌟"
        elif context.level == LearningLevel.INTERMEDIATE:
            color = "#f59e0b"  # Amber - building knowledge
            icon = "🎓"
        else:
            color = "#6366f1"  # Indigo - advanced
            icon = "⚗️"

        html = (
            f"<div style='background: linear-gradient(135deg, {color}15 0%, "
            f"{color}05 100%); border-left: 4px solid {color}; "
            f"padding: 1.5rem; border-radius: 12px; margin: 1rem 0; "
            f"font-family: -apple-system, system-ui, sans-serif;'>"
            f"<div style='display: flex; align-items: center; "
            f"margin-bottom: 1rem;'>"
            f"<span style='font-size: 1.5rem; margin-right: 0.5rem;'>{icon}</span>"
            f"<h3 style='margin: 0; color: {color}; font-size: 1.25rem;'>"
            f"{context.level.value.title()} Level</h3></div>"
            f"<div style='background: white; padding: 1rem; border-radius: 8px; "
            f"margin-bottom: 1rem;'>"
            f"<p style='margin: 0; font-size: 1.05rem; line-height: 1.6; "
            f"color: #374151;'>{context.summary}</p></div>"
        )

        # Key points
        if context.key_points:
            html += """
            <div style='margin-bottom: 1rem;'>
                <div style='font-weight: 600; color: #1f2937; margin-bottom: 0.5rem;'>
                    🎯 Key Points:
                </div>
                <ul style='margin: 0; padding-left: 1.5rem; color: #4b5563;'>
            """
            for point in context.key_points:
                html += f"<li style='margin: 0.25rem 0;'>{point}</li>"
            html += "</ul></div>"

        # Why it matters
        if context.why_it_matters:
            html += (
                f"<div style='background: {color}10; padding: 0.75rem; "
                f"border-radius: 6px; margin-bottom: 1rem; "
                f"border-left: 3px solid {color};'>"
                f"<div style='font-weight: 600; color: {color}; "
                f"margin-bottom: 0.25rem;'>💡 Why This Matters:</div>"
                f"<div style='color: #374151; font-style: italic;'>"
                f"{context.why_it_matters}</div></div>"
            )

        # Musical examples
        if include_examples and context.musical_examples:
            html += """
            <div style='margin-bottom: 1rem;'>
                <div style='font-weight: 600; color: #1f2937; margin-bottom: 0.5rem;'>
                    🎵 Try These Examples:
                </div>
            """
            for ex in context.musical_examples[:3]:
                html += (
                    f"<div style='background: #f3f4f6; padding: 0.5rem; "
                    f"border-radius: 4px; margin: 0.25rem 0; "
                    f"font-family: monospace; font-size: 0.9rem;'>"
                    f"<strong>{ex.context}:</strong> {ex.chords} in {ex.key}</div>"
                )
            html += "</div>"

        # Practice suggestions
        if include_practice and context.practice_suggestions:
            html += """
            <div style='margin-bottom: 1rem;'>
                <div style='font-weight: 600; color: #1f2937; margin-bottom: 0.5rem;'>
                    📚 Practice Suggestions:
                </div>
                <ul style='margin: 0; padding-left: 1.5rem; color: #4b5563;'>
            """
            for suggestion in context.practice_suggestions[:3]:
                html += f"<li style='margin: 0.25rem 0;'>{suggestion}</li>"
            html += "</ul></div>"

        # Related concepts (not for beginners)
        if context.related_concepts and context.level != LearningLevel.BEGINNER:
            html += (
                "<div style='margin-top: 1rem; padding-top: 1rem; "
                "border-top: 1px solid #e5e7eb;'>"
                "<div style='font-weight: 600; color: #1f2937; "
                "margin-bottom: 0.5rem;'>🔗 Related Concepts:</div>"
                "<div style='display: flex; flex-wrap: wrap; gap: 0.5rem;'>"
            )
            for related in context.related_concepts[:5]:
                html += (
                    f"<span style='background: {color}20; color: {color}; "
                    f"padding: 0.25rem 0.75rem; border-radius: 12px; "
                    f"font-size: 0.85rem;'>"
                    f"{related.concept_id.split('.')[-1]}</span>"
                )
            html += "</div></div>"

        # Victory lap: close container and return
        html += "</div>"
        return html

    def format_comparison(
        self, context_a: EducationalContext, context_b: EducationalContext
    ) -> str:
        """
        Format a comparison between two concepts.

        Args:
            context_a: First concept
            context_b: Second concept

        Returns:
            Formatted comparison text
        """
        lines = []
        lines.append("🔄 Concept Comparison")
        lines.append("=" * 50)
        lines.append("")

        lines.append(f"📘 {context_a.pattern_id}")
        lines.append(f"   {context_a.summary}")
        lines.append("")

        lines.append(f"📗 {context_b.pattern_id}")
        lines.append(f"   {context_b.summary}")
        lines.append("")

        # Check if they're related
        for related in context_a.related_concepts:
            if related.concept_id == context_b.pattern_id:
                lines.append(
                    f"↔️ Relationship: {related.relationship.replace('_', ' ').title()}"
                )
                lines.append(f"   {related.description}")
                lines.append("")

        return "\n".join(lines)

    def format_learning_path(
        self, concepts: list[str], descriptions: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Format a learning path through concepts.

        Args:
            concepts: Ordered list of concept IDs
            descriptions: Optional descriptions for each concept

        Returns:
            Formatted learning path
        """
        lines = []
        lines.append("🎯 Learning Path")
        lines.append("=" * 50)
        lines.append("")

        for i, concept in enumerate(concepts, 1):
            arrow = "→" if i < len(concepts) else "✓"
            desc = descriptions.get(concept, "") if descriptions else ""
            lines.append(f"{i}. {arrow} {concept}")
            if desc:
                lines.append(f"      {desc}")
            lines.append("")

        return "\n".join(lines)
