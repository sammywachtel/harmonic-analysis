"""
Knowledge base loader for educational content.

Loads and provides access to educational content about musical concepts,
patterns, and harmonic analysis.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import jsonschema

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

from .types import LearningLevel  # TODO: remove LearningLevel -- not needed
from .types import (
    EducationalContext,
    FullExplanation,
    Misconception,
    PatternSummary,
    ProgressionExample,
    RelatedConcept,
    RepertoireExample,
    TechnicalNotes,
    VisualizationHints,
)


class KnowledgeBase:
    """
    Loads and provides access to educational knowledge base.

    The knowledge base contains educational content for musical concepts,
    organized by learning level (beginner, intermediate, advanced).
    """

    def __init__(
        self, kb_path: Optional[Path] = None, schema_path: Optional[Path] = None
    ):
        """
        Initialize knowledge base.

        Args:
            kb_path: Path to knowledge_base.json. If None, uses default.
            schema_path: Path to schema file. If None, uses default.
        """
        # Opening move: locate the knowledge base file
        if kb_path is None:
            kb_path = self._get_default_kb_path()

        if schema_path is None:
            schema_path = self._get_default_schema_path()

        # Main play: load the data with optional validation
        self.data: Dict[str, Any] = self._load_knowledge_base(kb_path)

        if HAS_JSONSCHEMA and schema_path and schema_path.exists():
            self._validate_against_schema(schema_path)

    def _get_default_kb_path(self) -> Path:
        """Get default path to knowledge base JSON."""
        # Check resources/educational first (new location)
        pkg_path = (
            Path(__file__).parent.parent
            / "resources"
            / "educational"
            / "knowledge_base.json"
        )
        if pkg_path.exists():
            return pkg_path

        # Fallback to package directory
        return Path(__file__).parent / "knowledge_base.json"

    def _get_default_schema_path(self) -> Path:
        """Get default path to schema JSON."""
        return (
            Path(__file__).parent.parent
            / "resources"
            / "educational"
            / "knowledge_base_schema.json"
        )

    def _load_knowledge_base(self, path: Path) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        if not path.exists():
            raise FileNotFoundError(f"Knowledge base not found at {path}")

        with open(path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
            return data

    def _validate_against_schema(self, schema_path: Path) -> None:
        """Validate loaded data against JSON schema."""
        if not HAS_JSONSCHEMA:
            return

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        try:
            jsonschema.validate(self.data, schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Knowledge base validation failed: {e.message}") from e

    def get_concept(
        self, pattern_id: str, level: LearningLevel = LearningLevel.BEGINNER
    ) -> Optional[EducationalContext]:
        """
        Get educational context for a concept at specified learning level.

        Args:
            pattern_id: Pattern ID (e.g., "cadence.authentic.perfect")
            level: Learning level to retrieve

        Returns:
            EducationalContext if found, None otherwise
        """
        # Opening move: check if concept exists
        concepts = self.data.get("concepts", {})
        if pattern_id not in concepts:
            return None

        concept = concepts[pattern_id]
        level_data = concept.get("learning_levels", {}).get(level.value)

        if not level_data:
            return None

        # Main play: build EducationalContext from the data
        summary = level_data.get("summary", "")
        key_points = level_data.get("key_points", [])

        # Extract "why it matters" from various possible fields
        why_it_matters = (
            level_data.get("listen_for", "")
            or level_data.get("theory_deep_dive", {}).get("why_strongest", [""])[0]
            or "This pattern is fundamental to understanding harmonic motion."
        )

        # Build progression examples
        musical_examples = []
        for prog in concept.get("musical_examples", {}).get("progressions", []):
            # Big play: Extract visualization hints if present
            visualization = None
            if "visualization" in prog:
                vis_data = prog["visualization"]
                visualization = VisualizationHints(
                    chord_colors=vis_data.get("chord_colors", []),
                    bracket_range=vis_data.get("bracket_range", {}),
                )

            musical_examples.append(
                ProgressionExample(
                    chords=prog["chords"],
                    key=prog["key"],
                    roman_numerals=prog.get("roman_numerals", ""),
                    context=prog["context"],
                    audio_file=None,
                    visualization=visualization,
                )
            )

        # Build repertoire examples
        repertoire_examples = []
        for rep in concept.get("musical_examples", {}).get("repertoire", []):
            repertoire_examples.append(
                RepertoireExample(
                    composer=rep.get("composer", "Unknown"),
                    piece=rep["piece"],
                    location=rep["location"],
                    note=rep.get("note", ""),
                    difficulty="intermediate",
                )
            )

        # Build related concepts
        related_concepts = []
        relationships = concept.get("relationships", {})
        for rel_type, concepts_list in relationships.items():
            for related_id in concepts_list:
                desc = f"{rel_type.replace('_', ' ').title()} {related_id}"
                related_concepts.append(
                    RelatedConcept(
                        concept_id=related_id,
                        relationship=rel_type,
                        description=desc,
                    )
                )

        # Build misconceptions
        misconceptions = []
        for misc in concept.get("misconceptions", []):
            misconceptions.append(
                Misconception(
                    myth=misc["myth"],
                    reality=misc["reality"],
                    clarification=misc.get("clarification", ""),
                )
            )

        # Practice suggestions
        practice_suggestions = concept.get("practice_exercises", [])

        # Prerequisites and next steps (from relationships)
        prerequisites = relationships.get("builds_from", [])
        next_steps = relationships.get("leads_to", [])

        # Victory lap: return the complete educational context
        return EducationalContext(
            pattern_id=pattern_id,
            level=level,
            summary=summary,
            key_points=key_points,
            why_it_matters=why_it_matters,
            musical_examples=musical_examples,
            repertoire_examples=repertoire_examples,
            practice_suggestions=practice_suggestions,
            related_concepts=related_concepts,
            prerequisites=prerequisites,
            next_steps=next_steps,
            common_misconceptions=misconceptions,
            comparison_with={},  # Could be built from contrasts_with
        )

    def get_progression_examples(self, pattern_id: str) -> List[ProgressionExample]:
        """Get playable progression examples for a pattern."""
        concepts = self.data.get("concepts", {})
        if pattern_id not in concepts:
            return []

        examples = []
        for prog in (
            concepts[pattern_id].get("musical_examples", {}).get("progressions", [])
        ):
            # Victory lap: Include visualization hints if present
            visualization = None
            if "visualization" in prog:
                vis_data = prog["visualization"]
                visualization = VisualizationHints(
                    chord_colors=vis_data.get("chord_colors", []),
                    bracket_range=vis_data.get("bracket_range", {}),
                )

            examples.append(
                ProgressionExample(
                    chords=prog["chords"],
                    key=prog["key"],
                    roman_numerals=prog.get("roman_numerals", ""),
                    context=prog["context"],
                    audio_file=None,
                    visualization=visualization,
                )
            )
        return examples

    def get_related_concepts(
        self, pattern_id: str, relationship_type: str = "all"
    ) -> List[RelatedConcept]:
        """
        Get related concepts for a pattern.

        Args:
            pattern_id: Pattern to find relations for
            relationship_type: Type of relationship
                ("all", "contrasts_with", "builds_from", "leads_to")
        """
        concepts = self.data.get("concepts", {})
        if pattern_id not in concepts:
            return []

        relationships = concepts[pattern_id].get("relationships", {})
        related = []

        if relationship_type == "all":
            for rel_type, concepts_list in relationships.items():
                for related_id in concepts_list:
                    desc = f"{rel_type.replace('_', ' ').title()}: {related_id}"
                    related.append(
                        RelatedConcept(
                            concept_id=related_id,
                            relationship=rel_type,
                            description=desc,
                        )
                    )
        elif relationship_type in relationships:
            for related_id in relationships[relationship_type]:
                desc = (
                    f"{relationship_type.replace('_', ' ').title()}: " f"{related_id}"
                )
                related.append(
                    RelatedConcept(
                        concept_id=related_id,
                        relationship=relationship_type,
                        description=desc,
                    )
                )

        return related

    def get_function_explanation(self, function_abbr: str) -> Optional[Dict[str, str]]:
        """
        Get explanation for harmonic function abbreviation.

        Args:
            function_abbr: Function abbreviation (T, D, PD, etc.)

        Returns:
            Dictionary with function explanation
        """
        functions = self.data.get("harmonic_functions", {})
        if function_abbr not in functions:
            return None

        result: Dict[str, str] = functions[function_abbr]
        return result

    def list_all_concepts(self) -> List[str]:
        """Get list of all available concept IDs."""
        return list(self.data.get("concepts", {}).keys())

    def get_pattern_family_info(self, family: str) -> Optional[Dict[str, Any]]:
        """Get information about a pattern family."""
        families = self.data.get("pattern_families", {})
        result: Optional[Dict[str, Any]] = families.get(family)
        return result

    def get_summary(
        self, pattern_id: str, level: LearningLevel = LearningLevel.BEGINNER
    ) -> Optional[PatternSummary]:
        """
        Get lightweight pattern summary with fallback hierarchy.

        Opening move: Try exact pattern match.
        Big play: Fall back to parent pattern (trim last segment).
        Final whistle: Fall back to pattern family metadata.

        Args:
            pattern_id: Pattern ID (e.g., "cadence.authentic.perfect")
            level: Learning level (default: BEGINNER)

        Returns:
            PatternSummary if found, None otherwise

        Fallback hierarchy:
            1. Exact match: "cadence.authentic.perfect"
            2. Parent match: "cadence.authentic"
            3. Family match: pattern_families["cadential"]
        """
        # Opening move: normalize pattern ID (handle delimiters)
        # Keep underscores and case as-is since they're used in actual pattern IDs
        normalized_id = pattern_id.replace(":", ".").replace("-", ".")

        # Main play: try exact match first (case-insensitive)
        concepts = self.data.get("concepts", {})
        # Build lowercase lookup map for case-insensitive matching
        concepts_lower = {k.lower(): k for k in concepts.keys()}
        normalized_lower = normalized_id.lower()

        if normalized_lower in concepts_lower:
            actual_id = concepts_lower[normalized_lower]
            concept = concepts[actual_id]
            level_data = concept.get("learning_levels", {}).get(level.value)
            if level_data:
                return PatternSummary(
                    pattern_id=actual_id,
                    title=concept.get("display_name", actual_id),
                    summary=level_data.get("summary", ""),
                    category=concept.get("category"),
                )

        # Big play: try parent pattern (trim last segment)
        if "." in normalized_id:
            parent_id = ".".join(normalized_id.split(".")[:-1])
            parent_lower = parent_id.lower()
            if parent_lower in concepts_lower:
                actual_parent_id = concepts_lower[parent_lower]
                concept = concepts[actual_parent_id]
                level_data = concept.get("learning_levels", {}).get(level.value)
                if level_data:
                    return PatternSummary(
                        pattern_id=actual_parent_id,
                        title=concept.get("display_name", actual_parent_id),
                        summary=level_data.get("summary", ""),
                        category=concept.get("category"),
                    )

        # Final whistle: try pattern family fallback
        # Extract family from pattern ID (first segment or category)
        family_candidates = []
        if "." in normalized_id:
            family_candidates.append(normalized_id.split(".")[0])

        # Also check if any concept has a category matching our pattern prefix
        for concept_id, concept_data in concepts.items():
            category = concept_data.get("category")
            if category and normalized_id.startswith(category):
                family_candidates.append(category)

        families = self.data.get("pattern_families", {})
        for family in family_candidates:
            if family in families:
                family_info = families[family]
                return PatternSummary(
                    pattern_id=family,
                    title=f"{family.title()} Patterns",
                    summary=family_info.get("overview", ""),
                    category=family,
                )

        # Victory lap: no match found
        return None

    def get_full_explanation(self, pattern_id: str) -> Optional[FullExplanation]:
        """
        Get complete Bernstein-style explanation for a pattern.

        Opening move: Check if explanation exists in knowledge base.
        Main play: Build FullExplanation with Layer 1 and optional Layer 2.
        Victory lap: Return complete explanation or None.

        Args:
            pattern_id: Pattern ID (e.g., "cadence.authentic.perfect")

        Returns:
            FullExplanation if found, None otherwise
        """
        # Opening move: locate the concept
        concepts = self.data.get("concepts", {})
        if pattern_id not in concepts:
            return None

        concept = concepts[pattern_id]
        explanation_data = concept.get("explanation")

        if not explanation_data:
            return None

        # Main play: extract Layer 1 (core explanation)
        hook = explanation_data.get("hook", "")
        breakdown = explanation_data.get("breakdown", [])
        story = explanation_data.get("story", "")
        composers = explanation_data.get("composers", "")
        examples = explanation_data.get("examples", [])
        try_this = explanation_data.get("try_this", "")
        title = concept.get("display_name", pattern_id)

        # Big play: extract Layer 2 (optional technical notes)
        technical_notes = None
        tech_data = explanation_data.get("technical_notes")
        if tech_data:
            technical_notes = TechnicalNotes(
                voice_leading=tech_data.get("voice_leading"),
                theoretical_depth=tech_data.get("theoretical_depth"),
                historical_context=tech_data.get("historical_context"),
            )

        # Victory lap: return the complete explanation
        return FullExplanation(
            pattern_id=pattern_id,
            title=title,
            hook=hook,
            breakdown=breakdown,
            story=story,
            composers=composers,
            examples=examples,
            try_this=try_this,
            technical_notes=technical_notes,
        )
