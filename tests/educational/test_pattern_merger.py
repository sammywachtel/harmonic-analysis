"""
Tests for pattern prioritization module.

Validates prioritization logic for educational pattern display.
No merging - maintains 1:1 backend-frontend correspondence.
"""

from harmonic_analysis.educational import pattern_merger
from harmonic_analysis.educational.types import EducationalCard


class TestPrioritizePatterns:
    """Test pattern prioritization logic."""

    def test_prioritize_cadential_over_progression(self):
        """Cadential patterns should be prioritized over progressions."""
        pac_card = EducationalCard(
            pattern_id="cadence.authentic.perfect",
            title="Perfect Authentic Cadence (PAC)",
            summary="Strongest cadence",
            category="cadential",
            difficulty="beginner",
        )
        ii_v_i_card = EducationalCard(
            pattern_id="functional.ii_V_I",
            title="ii-V-I Progression",
            summary="Jazz progression",
            category="functional",
            difficulty="beginner",
        )

        cards = [ii_v_i_card, pac_card]  # Reversed order

        # Execute: prioritize patterns
        result = pattern_merger.prioritize_patterns(cards)

        # Verify: PAC (cadential=3) should come before ii-V-I (functional=1)
        assert len(result) == 2
        assert result[0].pattern_id == "cadence.authentic.perfect"
        assert result[1].pattern_id == "functional.ii_V_I"

    def test_prioritize_progression_over_functional(self):
        """Progression patterns should be prioritized over functional."""
        ii_v_i_card = EducationalCard(
            pattern_id="functional.ii_V_I",
            title="ii-V-I Progression",
            summary="Jazz progression",
            category="functional",
            difficulty="beginner",
        )
        functional_card = EducationalCard(
            pattern_id="function_dominant",
            title="Dominant Function",
            summary="Resolves to tonic",
            category="functional",
            difficulty="beginner",
        )

        cards = [functional_card, ii_v_i_card]  # Reversed order

        # Execute: prioritize patterns
        result = pattern_merger.prioritize_patterns(cards)

        # Verify: Both functional, so alphabetical order
        assert len(result) == 2
        assert result[0].pattern_id == "function_dominant"
        assert result[1].pattern_id == "functional.ii_V_I"

    def test_prioritize_same_category_alphabetical_tiebreaker(self):
        """When priorities tie, sort alphabetically by title."""
        iac_card = EducationalCard(
            pattern_id="cadence.authentic.imperfect",
            title="Imperfect Authentic Cadence (IAC)",
            summary="Weaker cadence",
            category="cadential",
            difficulty="beginner",
        )
        pac_card = EducationalCard(
            pattern_id="cadence.authentic.perfect",
            title="Perfect Authentic Cadence (PAC)",
            summary="Strongest cadence",
            category="cadential",
            difficulty="beginner",
        )

        cards = [pac_card, iac_card]  # Both cadential, but reversed alphabetical

        # Execute: prioritize patterns
        result = pattern_merger.prioritize_patterns(cards)

        # Verify: Same priority (cadential=3), so alphabetical by title
        # "Imperfect" comes before "Perfect"
        assert len(result) == 2
        assert (
            result[0].pattern_id == "cadence.authentic.imperfect"
        )  # "Imperfect" < "Perfect"
        assert result[1].pattern_id == "cadence.authentic.perfect"

    def test_prioritize_empty_list(self):
        """Empty list returns empty list."""
        result = pattern_merger.prioritize_patterns([])
        assert result == []

    def test_prioritize_single_card(self):
        """Single card returns unchanged."""
        pac_card = EducationalCard(
            pattern_id="cadence.authentic.perfect",
            title="Perfect Authentic Cadence (PAC)",
            summary="Strongest cadence",
            category="cadential",
            difficulty="beginner",
        )

        result = pattern_merger.prioritize_patterns([pac_card])

        assert len(result) == 1
        assert result[0].pattern_id == "cadence.authentic.perfect"

    def test_prioritize_all_categories(self):
        """Test full priority ordering: cadential > functional."""
        cadential_card = EducationalCard(
            pattern_id="cadence.authentic.perfect",
            title="PAC",
            summary="Cadence",
            category="cadential",
            difficulty="beginner",
        )
        functional_card_1 = EducationalCard(
            pattern_id="functional.ii_V_I",
            title="ii-V-I",
            summary="Progression",
            category="functional",
            difficulty="beginner",
        )
        functional_card_2 = EducationalCard(
            pattern_id="function_dominant",
            title="Dominant",
            summary="Function",
            category="functional",
            difficulty="beginner",
        )

        # Input in reverse priority order
        cards = [functional_card_2, functional_card_1, cadential_card]

        # Execute: prioritize patterns
        result = pattern_merger.prioritize_patterns(cards)

        # Verify: correct priority order (cadential first, then functionals alphabetically)
        assert len(result) == 3
        assert result[0].pattern_id == "cadence.authentic.perfect"  # Priority 3
        assert (
            result[1].pattern_id == "function_dominant"
        )  # Priority 1, alphabetically "Dominant" < "ii-V-I"
        assert result[2].pattern_id == "functional.ii_V_I"  # Priority 1


class TestMergeAndPrioritize:
    """Test main entry point (now only prioritization, no merging/limiting)."""

    def test_merge_and_prioritize_maintains_all_patterns(self):
        """All patterns are returned (no limiting)."""
        pac_card = EducationalCard(
            pattern_id="cadence.authentic.perfect",
            title="PAC",
            summary="Cadence",
            category="cadential",
            difficulty="beginner",
        )
        iac_card = EducationalCard(
            pattern_id="cadence.authentic.imperfect",
            title="IAC",
            summary="Cadence",
            category="cadential",
            difficulty="beginner",
        )
        ii_v_i_card = EducationalCard(
            pattern_id="functional.ii_V_I",
            title="ii-V-I",
            summary="Progression",
            category="functional",
            difficulty="beginner",
        )

        cards = [ii_v_i_card, iac_card, pac_card]  # Reversed order

        # Execute: main entry point
        result = pattern_merger.merge_and_prioritize(cards)

        # Verify: all 3 cards returned (no limiting), sorted by priority
        assert len(result) == 3
        # Both PAC and IAC are cadential, so alphabetical: IAC < PAC
        assert result[0].pattern_id == "cadence.authentic.imperfect"
        assert result[1].pattern_id == "cadence.authentic.perfect"
        assert result[2].pattern_id == "functional.ii_V_I"

    def test_merge_and_prioritize_no_merging(self):
        """PAC and IAC remain separate (no merging)."""
        pac_card = EducationalCard(
            pattern_id="cadence.authentic.perfect",
            title="PAC",
            summary="Cadence",
            category="cadential",
            difficulty="beginner",
        )
        iac_card = EducationalCard(
            pattern_id="cadence.authentic.imperfect",
            title="IAC",
            summary="Cadence",
            category="cadential",
            difficulty="beginner",
        )

        cards = [pac_card, iac_card]

        # Execute: main entry point
        result = pattern_merger.merge_and_prioritize(cards)

        # Verify: both cards preserved (no merging)
        assert len(result) == 2
        pattern_ids = [card.pattern_id for card in result]
        assert "cadence.authentic.perfect" in pattern_ids
        assert "cadence.authentic.imperfect" in pattern_ids

    def test_merge_and_prioritize_empty_list(self):
        """Empty list returns empty list."""
        result = pattern_merger.merge_and_prioritize([])
        assert result == []
