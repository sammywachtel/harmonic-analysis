"""
Data structures for educational content system.

Defines types for representing educational context, learning levels,
and supporting educational materials for harmonic analysis.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class LearningLevel(Enum):
    """Learning level for educational content presentation."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class ProgressionExample:
    """Musical progression example with educational context."""

    chords: str  # "Dm G7 C"
    key: str  # "C major"
    roman_numerals: str  # "ii V7 I"
    context: str  # "Classic jazz turnaround"
    audio_file: Optional[str] = None  # Future: actual audio


@dataclass
class RepertoireExample:
    """Real-world musical example from repertoire."""

    composer: str
    piece: str
    location: str  # "m. 21-24"
    note: str  # What to listen for
    difficulty: str = "intermediate"  # For practice suggestions


@dataclass
class Misconception:
    """Common misconception about a music theory concept."""

    myth: str  # The incorrect belief
    reality: str  # The correct understanding
    clarification: str  # Extended explanation


@dataclass
class RelatedConcept:
    """Link to related musical concept for further learning."""

    concept_id: str
    relationship: str  # "builds_from", "contrasts_with", "leads_to"
    description: str


@dataclass
class EducationalContext:
    """
    Educational enrichment for analysis results.

    Provides learning-level-appropriate explanations, examples, and
    guidance for understanding harmonic analysis patterns.
    """

    pattern_id: str
    level: LearningLevel

    # Core explanations
    summary: str  # Level-appropriate summary
    key_points: List[str]  # Main learning points
    why_it_matters: str  # Musical significance

    # Examples and practice
    musical_examples: List[ProgressionExample] = field(default_factory=list)
    repertoire_examples: List[RepertoireExample] = field(default_factory=list)
    practice_suggestions: List[str] = field(default_factory=list)

    # Learning navigation
    related_concepts: List[RelatedConcept] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)

    # Clarifications
    common_misconceptions: List[Misconception] = field(default_factory=list)
    comparison_with: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "pattern_id": self.pattern_id,
            "level": self.level.value,
            "summary": self.summary,
            "key_points": self.key_points,
            "why_it_matters": self.why_it_matters,
            "musical_examples": [
                {
                    "chords": ex.chords,
                    "key": ex.key,
                    "roman_numerals": ex.roman_numerals,
                    "context": ex.context,
                    "audio_file": ex.audio_file,
                }
                for ex in self.musical_examples
            ],
            "repertoire_examples": [
                {
                    "composer": ex.composer,
                    "piece": ex.piece,
                    "location": ex.location,
                    "note": ex.note,
                    "difficulty": ex.difficulty,
                }
                for ex in self.repertoire_examples
            ],
            "practice_suggestions": self.practice_suggestions,
            "related_concepts": [
                {
                    "concept_id": rc.concept_id,
                    "relationship": rc.relationship,
                    "description": rc.description,
                }
                for rc in self.related_concepts
            ],
            "prerequisites": self.prerequisites,
            "next_steps": self.next_steps,
            "common_misconceptions": [
                {
                    "myth": m.myth,
                    "reality": m.reality,
                    "clarification": m.clarification,
                }
                for m in self.common_misconceptions
            ],
            "comparison_with": self.comparison_with,
        }
