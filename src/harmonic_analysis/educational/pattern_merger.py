"""
Pattern prioritization module for educational content.

Handles prioritizing patterns for optimal educational presentation.
Maintains 1:1 correspondence with backend-detected patterns (no merging).
"""

from typing import List

from .types import EducationalCard

# Priority scoring: Higher numbers = higher priority
CATEGORY_PRIORITIES = {
    "cadential": 3,  # Cadences are most important (structural endings)
    "progression": 2,  # Progressions are secondary (harmonic motion)
    "functional": 1,  # Functions are lowest priority (most general)
}


def prioritize_patterns(cards: List[EducationalCard]) -> List[EducationalCard]:
    """
    Assign priority scores and sort by priority.

    Opening move: Score each card based on category.
    Main play: Sort by priority (descending), then title for stability.
    Victory lap: Return sorted list.

    Priority scoring:
    - cadences (category="cadential") = 3 points
    - progressions (category="progression") = 2 points
    - functions (category="functional") = 1 point

    Sort: priority DESC, then alphabetical by title for deterministic ordering

    Args:
        cards: List of EducationalCard objects

    Returns:
        Sorted list with highest priority cards first
    """
    if not cards:
        return cards

    # Opening move: assign priority scores based on category
    def get_priority(card: EducationalCard) -> int:
        return CATEGORY_PRIORITIES.get(card.category or "", 0)

    # Main play: sort by priority (descending), secondary sort by title for stability
    sorted_cards = sorted(
        cards,
        key=lambda card: (
            -get_priority(
                card
            ),  # Negative for descending order (higher priority first)
            card.title,  # Alphabetical tiebreaker for deterministic ordering
        ),
    )

    # Victory lap: return the prioritized list
    return sorted_cards


def merge_and_prioritize(cards: List[EducationalCard]) -> List[EducationalCard]:
    """
    Main entry point: prioritize patterns for display.

    Maintains 1:1 correspondence with backend-detected patterns.
    No merging - preserves backend fidelity for two-way conversion.
    No limiting - displays all detected patterns.

    Pipeline: prioritize only

    Args:
        cards: List of EducationalCard objects

    Returns:
        Prioritized card list (sorted by category priority)
    """
    # Main play: prioritize by category
    return prioritize_patterns(cards)
