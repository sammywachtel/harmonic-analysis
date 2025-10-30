"""
Data structures for educational content system.

Defines types for representing educational context, learning levels,
and supporting educational materials for harmonic analysis.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class LearningLevel(Enum):
    """
    TODO -- remove this -- learning level is not going to be implemented
    Learning level for educational content presentation.
    """

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class VisualizationHints:
    """Visual representation hints for chord progressions."""

    chord_colors: List[str]  # ["PD", "D", "T"] for predominant, dominant, tonic
    bracket_range: Dict[str, int]  # {"start": 1, "end": 2} for pattern bracket


@dataclass
class ProgressionExample:
    """Musical progression example with educational context."""

    chords: str  # "Dm G7 C"
    key: str  # "C major"
    roman_numerals: str  # "ii V7 I"
    context: str  # "Classic jazz turnaround"
    audio_file: Optional[str] = None  # Future: actual audio
    visualization: Optional[VisualizationHints] = None  # Visual hints for frontend


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
class PatternSummary:
    """
    Lightweight summary for pattern cards (frontend MVP).

    Provides just the essential info for a card-sized educational display.
    Progressive disclosure model: Summary → Full explanation → Technical details
    (depth controlled by user interaction, not skill level assignments)
    """

    pattern_id: str
    title: str  # Display name (e.g., "Perfect Authentic Cadence (PAC)")
    summary: str  # Two-sentence Bernstein-style summary
    category: Optional[str] = None  # Pattern family (e.g., "cadential")


@dataclass
class TechnicalNotes:
    """
    Optional Layer 2 technical details for deep dives.

    Provides voice leading mechanics, theoretical context, and historical evolution.
    """

    voice_leading: Optional[str] = None  # Voice leading mechanics
    theoretical_depth: Optional[str] = None  # Advanced theoretical analysis
    historical_context: Optional[str] = None  # Historical evolution and context


@dataclass
class FullExplanation:
    """
    Complete Bernstein-style explanation with progressive disclosure.

    Opening move: Hook grabs attention, breakdown provides structure.
    Main play: Story gives context, composers show usage, examples prove it.
    Victory lap: Try-this makes it actionable, technical notes go deeper.
    """

    pattern_id: str
    title: str

    # Layer 1: Core Bernstein-style explanation (always visible)
    hook: str  # Opening 1-2 sentences that grab attention
    breakdown: List[str]  # Hierarchical bullet points explaining the pattern
    story: str  # Narrative 3-4 paragraphs with musical context
    composers: str  # Who uses this pattern and why
    examples: List[str]  # Specific pieces with measure numbers
    try_this: str  # Actionable suggestion for practicing/composing

    # Layer 2: Optional technical depth (progressive disclosure)
    technical_notes: Optional[TechnicalNotes] = None


@dataclass
class EducationalCard:
    """
    Frontend-ready card representation for educational content.

    Serializable format for REST API responses.
    Progressive disclosure model: Users explore depth through interaction,
    not skill level labels.
    """

    pattern_id: str
    title: str
    summary: str
    category: Optional[str] = None
    visualization: Optional[VisualizationHints] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: Dict[str, Any] = {
            "pattern_id": self.pattern_id,
            "title": self.title,
            "summary": self.summary,
            "category": self.category,
        }

        # Big play: Include visualization hints if present
        if self.visualization:
            result["visualization"] = {
                "chord_colors": self.visualization.chord_colors,
                "bracket_range": self.visualization.bracket_range,
            }

        return result


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
