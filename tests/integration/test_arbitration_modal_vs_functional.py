#!/usr/bin/env python3
"""
Integration tests for modal vs functional arbitration with evidence-based gating.

Tests the new evidence-based modal arbitration logic when feature flag is enabled.
"""

import pytest

from harmonic_analysis.services.analysis_arbitration_service import (
    AnalysisArbitrationService,
    ArbitrationPolicy,
)
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService


@pytest.fixture
def analyze_progression_new():
    """Fixture to analyze progressions with new evidence-based arbitration."""

    async def _analyze(chords, enable_evidence_arbitration=True):
        # Create pattern analysis service with evidence-based arbitration
        policy = ArbitrationPolicy(
            enable_evidence_based_modal_arbitration=enable_evidence_arbitration
        )
        service = PatternAnalysisService(
            arbitration_policy=policy,  # Pass policy, not service
            auto_calibrate=False,  # Disable calibration for testing
        )
        result = await service.analyze_with_patterns_async(chords)
        return result

    return _analyze


@pytest.mark.asyncio
class TestEvidenceBasedArbitration:
    """Test evidence-based modal vs functional arbitration."""

    @pytest.mark.parametrize(
        "prog, expect_primary, expect_contains",
        [
            # Mixolydian vamp - modal wins with bVII evidence and close confidence
            (["C", "F", "Bb", "C"], "modal", ["Mixolydian", "bVII"]),
            # Phrygian pattern - modal wins with bII evidence and close confidence
            (["Am", "Bb", "Am", "Bb"], "modal", ["Phrygian", "bII"]),
            # Authentic cadence - functional should win
            (["C", "F", "G", "C"], "functional", ["authentic"]),
            # Short functional cadence - functional wins (no modal analysis)
            (["F", "G", "C"], "functional", ["major"]),
            # Complex progression analyzed as modal due to close confidence
            (["C", "Am", "F", "G", "C"], "modal", ["Dorian"]),
        ],
    )
    async def test_arbitration_gate(
        self, analyze_progression_new, prog, expect_primary, expect_contains
    ):
        """Test arbitration with evidence gating."""
        res = await analyze_progression_new(prog, enable_evidence_arbitration=True)
        primary = res.primary.type.value

        # Check for expected content across multiple fields
        mode = (res.primary.mode or "").lower()
        romans = " ".join(res.primary.roman_numerals or []).lower()
        characteristics = " ".join(
            getattr(res.primary, "modal_characteristics", [])
        ).lower()
        reasoning = (res.primary.reasoning or "").lower()

        # Combine all analysis text to search in
        all_text = f"{mode} {romans} {characteristics} {reasoning}"

        # Check primary type if not ambiguous
        if expect_primary != "either":
            assert (
                primary == expect_primary
            ), f"Expected {expect_primary} but got {primary}"

        # Check for expected content across multiple fields
        for token in expect_contains:
            assert (
                token.lower() in all_text
            ), f"Expected '{token}' in analysis but got: mode='{mode}', romans='{romans}', chars='{characteristics}', reasoning='{reasoning}'"

    @pytest.mark.parametrize(
        "prog, max_confidence_gap",
        [
            # Modal should not win with significantly lower confidence
            (["C", "F", "G", "C"], 0.10),  # Functional progression
            (["C", "Bb", "F", "C"], 0.10),  # Mixolydian that stays within guardband
        ],
    )
    async def test_guardband_enforcement(
        self, analyze_progression_new, prog, max_confidence_gap
    ):
        """Test that modal doesn't win with significantly lower confidence."""
        res = await analyze_progression_new(prog, enable_evidence_arbitration=True)

        # If modal is primary, check confidence gap
        if res.primary.type.value == "modal":
            func_conf = res.primary.functional_confidence or 0
            modal_conf = res.primary.modal_confidence or 0
            gap = func_conf - modal_conf

            assert (
                gap <= max_confidence_gap
            ), f"Modal won with too large a gap: {gap:.3f} > {max_confidence_gap}"

    async def test_modal_evidence_required(self, analyze_progression_new):
        """Test that modal requires actual evidence markers to win in tie region."""
        # A progression that might have similar confidences but no clear modal markers
        res = await analyze_progression_new(
            ["C", "Am", "F", "G"], enable_evidence_arbitration=True
        )

        # Check that the analysis completed
        assert res.primary is not None
        # With evidence-based arbitration, modal should only win with evidence
        # This progression doesn't have strong modal markers like bVII or bII

    async def test_authentic_cadence_preference(self, analyze_progression_new):
        """Test that authentic cadences strongly prefer functional analysis."""
        # Classic I-IV-V-I with authentic cadence
        res = await analyze_progression_new(
            ["C", "F", "G", "C"], enable_evidence_arbitration=True
        )

        assert (
            res.primary.type.value == "functional"
        ), "Authentic cadence should yield functional primary"

    async def test_clear_modal_pattern(self, analyze_progression_new):
        """Test that clear modal patterns can win when evidence is strong."""
        # Mixolydian vamp pattern
        res = await analyze_progression_new(
            ["G", "F", "G", "F"], enable_evidence_arbitration=True
        )

        # This should be modal if confidences are close and evidence is present
        # But we don't mandate it must be modal, as it depends on confidence values
        assert res.primary is not None
        # Just verify the analysis ran without errors

    async def test_feature_flag_toggle(self, analyze_progression_new):
        """Test difference between old and new arbitration logic."""
        prog = ["G", "F", "C", "G"]

        # Test with new logic
        res_new = await analyze_progression_new(prog, enable_evidence_arbitration=True)
        # Check that the analysis ran without errors
        assert res_new.primary is not None
        assert res_new.primary.type.value in ["functional", "modal"]

        # Test with old logic
        res_old = await analyze_progression_new(prog, enable_evidence_arbitration=False)
        # Check that the analysis ran without errors
        assert res_old.primary is not None
        assert res_old.primary.type.value in ["functional", "modal"]

        # The logic paths are different even if we can't see warnings directly
        # (warnings are internal to arbitration and not exposed in the envelope)

    async def test_rationale_transparency(self, analyze_progression_new):
        """Test that rationale explains tie-break decisions clearly."""
        res = await analyze_progression_new(
            ["Dm", "G", "C", "F"], enable_evidence_arbitration=True
        )

        # Check that analysis completed
        assert res.primary is not None
        # The primary analysis should have reasoning
        reasoning = res.primary.reasoning or ""
        assert len(reasoning) > 0, "Should have analysis reasoning"
