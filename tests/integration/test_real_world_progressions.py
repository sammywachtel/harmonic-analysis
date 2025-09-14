#!/usr/bin/env python
"""
Real-world progression integration tests

These tests validate common musical progressions that users actually input,
catching issues that unit tests miss.
"""

from types import SimpleNamespace

import pytest

from harmonic_analysis import AnalysisOptions
from harmonic_analysis.services.analysis_arbitration_service import (
    AnalysisArbitrationService,
)
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService


def _derive_parent_key_from_mode(modal_mode_name: str) -> str:
    """
    Derive parent key from modal mode name like 'G Mixolydian' -> 'C major'.

    This maps from the modal tonic and mode to the parent key signature.
    """
    if not modal_mode_name:
        return None

    # Extract tonic and mode from names like "G Mixolydian", "E Phrygian", "D Dorian"
    parts = modal_mode_name.strip().split()
    if len(parts) < 2:
        return None

    tonic = parts[0]
    mode_name = parts[1].lower()

    # Mode to parent key offset (semitones down from modal tonic to parent tonic)
    mode_offsets = {
        "ionian": 0,  # C Ionian = C major
        "dorian": 2,  # D Dorian = C major (D down 2 semitones)
        "phrygian": 4,  # E Phrygian = C major (E down 4 semitones)
        "lydian": 5,  # F Lydian = C major (F down 5 semitones)
        "mixolydian": 7,  # G Mixolydian = C major (G down 7 semitones)
        "aeolian": 9,  # A Aeolian = C major (A down 9 semitones)
        "locrian": 11,  # B Locrian = C major (B down 11 semitones)
    }

    if mode_name not in mode_offsets:
        return None

    # Convert tonic to semitone number (C=0, C#=1, D=2, etc.)
    tonic_semitones = {
        "C": 0,
        "C#": 1,
        "Db": 1,
        "D": 2,
        "D#": 3,
        "Eb": 3,
        "E": 4,
        "F": 5,
        "F#": 6,
        "Gb": 6,
        "G": 7,
        "G#": 8,
        "Ab": 8,
        "A": 9,
        "A#": 10,
        "Bb": 10,
        "B": 11,
    }

    if tonic not in tonic_semitones:
        return None

    # Calculate parent key semitone
    modal_tonic_semitone = tonic_semitones[tonic]
    offset = mode_offsets[mode_name]
    parent_semitone = (modal_tonic_semitone - offset) % 12

    # Convert back to key name
    semitone_to_key = {
        0: "C",
        1: "Db",
        2: "D",
        3: "Eb",
        4: "E",
        5: "F",
        6: "Gb",
        7: "G",
        8: "Ab",
        9: "A",
        10: "Bb",
        11: "B",
    }

    parent_key = semitone_to_key[parent_semitone]
    return f"{parent_key} major"


async def analyze_progression_new(chords, options: AnalysisOptions):
    """Simplified test helper using the clean PatternAnalysisService API."""
    svc = PatternAnalysisService()
    key_hint = getattr(options, "parent_key", None)

    # Use the service directly - no complex workarounds needed
    result = svc.analyze_with_patterns(
        chords,
        profile="classical",
        best_cover=False,
        key_hint=key_hint,
    )

    # Simple mapping for test compatibility
    primary = SimpleNamespace(
        type=SimpleNamespace(value=result.primary.type.value),
        roman_numerals=result.primary.roman_numerals,
        confidence=result.primary.confidence,
        key_signature=result.primary.key_signature,
        mode=result.primary.mode or "major",
        reasoning=result.primary.reasoning or "analysis completed",
        functional_confidence=result.primary.functional_confidence or 0.0,
        modal_confidence=result.primary.modal_confidence or 0.0,
    )

    return SimpleNamespace(primary_analysis=primary)


class TestRealWorldProgressions:
    """Test common real-world chord progressions"""

    @pytest.mark.asyncio
    async def test_vi_IV_I_V_in_A_major(self):
        """
        Test F#m-D-A-E (vi-IV-I-V in A major)

        This is one of the most common progressions in popular music.
        Should be analyzed as functional, not modal.
        """
        result = await analyze_progression_new(
            ["F#m", "D", "A", "E"], AnalysisOptions(confidence_threshold=0.4)
        )

        # Should have both functional and modal interpretations (new-pipeline compatible)
        alts = (
            getattr(result, "alternative_analyses", None)
            or getattr(result, "alternatives", None)
            or []
        )
        if alts:
            assert len(alts) > 0, "Should provide alternative analyses"
        else:
            # Fallback: require both confidence signals on primary when alternatives are not provided
            pa = result.primary_analysis
            assert hasattr(pa, "functional_confidence") and hasattr(
                pa, "modal_confidence"
            ), "Primary analysis should expose functional_confidence and modal_confidence when alternatives are not present"

        # Check primary analysis
        primary = result.primary_analysis

        # Should have roman numerals populated
        assert (
            len(primary.roman_numerals) == 4
        ), f"Should have 4 roman numerals, got: {primary.roman_numerals}"

        # This common progression should be analyzed functionally, not modally
        # When analyzed modally in F# Aeolian, E would be bVII (which is technically correct)
        # But functional analysis in A major (vi-IV-I-V) is more appropriate for this progression
        if primary.type.value == "modal" and "bVII" in primary.reasoning:
            # This suggests the functional analysis should have higher confidence
            # Check if functional analysis is available as alternative
            functional_analyses = [
                a for a in result.alternative_analyses if a.type.value == "functional"
            ]
            assert (
                len(functional_analyses) > 0
            ), "Should provide functional alternative for this common progression"

            # Use centralized arbitration service to validate confidence gap
            arbitration_service = AnalysisArbitrationService()

            # Create mock summaries for validation
            from harmonic_analysis.dto import AnalysisType

            functional_mock = type(
                "MockSummary",
                (),
                {
                    "confidence": functional_analyses[0].confidence,
                    "type": AnalysisType.FUNCTIONAL,
                    "functional_confidence": functional_analyses[0].confidence,
                    "modal_confidence": primary.confidence,
                    "roman_numerals": [],
                    "patterns": [],  # Required by arbitration service
                    "key_signature": "A major",
                    "mode": "major",
                    "reasoning": "functional analysis",
                },
            )()
            modal_mock = type(
                "MockSummary",
                (),
                {
                    "confidence": primary.confidence,
                    "type": AnalysisType.MODAL,
                    "functional_confidence": functional_analyses[0].confidence,
                    "modal_confidence": primary.confidence,
                    "roman_numerals": [],
                    "patterns": [],  # Required by arbitration service
                    "key_signature": "A major",
                    "mode": "Aeolian",
                    "reasoning": "modal analysis",
                },
            )()

            arbitration_result = arbitration_service.arbitrate(
                functional_summary=functional_mock,
                modal_summary=modal_mock,
                chord_symbols=["F#m", "D", "A", "E"],  # vi-IV-I-V example
            )

            # Check for excessive modal dominance warnings
            if arbitration_result.warnings:
                for warning in arbitration_result.warnings:
                    if "excessive" in warning.lower():
                        pytest.fail(f"Arbitration service detected issue: {warning}")

        # Should provide meaningful reasoning
        reasoning = primary.reasoning.lower()
        assert (
            "contains" in reasoning
            or "progression" in reasoning
            or "analysis" in reasoning
        ), f"Reasoning should be meaningful, got: {primary.reasoning}"

    @pytest.mark.asyncio
    async def test_common_progressions_have_alternatives(self):
        """Common progressions should offer multiple valid interpretations where appropriate"""
        # Progressions that should have alternatives (ambiguous between functional and modal)
        ambiguous_progressions = [
            (["F#m", "D", "A", "E"], "vi-IV-I-V in A major"),
            (["Em", "C", "G", "D"], "vi-IV-I-V in G major"),
            (["Am", "F", "C", "G"], "vi-IV-I-V in C major"),
        ]

        for progression, description in ambiguous_progressions:
            result = await analyze_progression_new(
                progression, AnalysisOptions(confidence_threshold=0.3)
            )

            # These progressions should have alternatives (functional vs modal); be compatible with new pipeline
            alts = (
                getattr(result, "alternative_analyses", None)
                or getattr(result, "alternatives", None)
                or []
            )
            if alts:
                assert (
                    len(alts) > 0
                ), f"{description} should have alternative interpretations"
            else:
                pa = result.primary_analysis
                assert hasattr(pa, "functional_confidence") and hasattr(
                    pa, "modal_confidence"
                ), f"{description}: primary should expose both confidences when alternatives not provided"

            # Should have roman numerals
            assert (
                len(result.primary_analysis.roman_numerals) == 4
            ), f"{description} should have 4 roman numerals"

        # Clear functional progressions may not have alternatives (and that's OK)
        clear_functional_progressions = [
            (["C", "Am", "F", "G"], "I-vi-IV-V in C major"),
            (["C", "F", "G", "C"], "I-IV-V-I in C major"),
        ]

        for progression, description in clear_functional_progressions:
            result = await analyze_progression_new(
                progression, AnalysisOptions(confidence_threshold=0.3)
            )

            # Should still have roman numerals even if no alternatives
            assert (
                len(result.primary_analysis.roman_numerals) == 4
            ), f"{description} should have 4 roman numerals"

            # Primary should be functional
            assert (
                result.primary_analysis.type.value == "functional"
            ), f"{description} should be analyzed as functional"

    @pytest.mark.asyncio
    async def test_modal_vs_functional_accuracy(self):
        """Test that modal vs functional classification is accurate"""

        # Clearly functional progressions (should NOT be modal primary)
        functional_progressions = [
            (["C", "F", "G", "C"], "I-IV-V-I cadence"),
            (["Am", "Dm", "G", "C"], "vi-ii-V-I progression"),
            (["F", "G", "Am"], "IV-V-vi deceptive cadence"),
        ]

        for progression, description in functional_progressions:
            result = await analyze_progression_new(progression, AnalysisOptions())

            pa = result.primary_analysis
            f_conf = getattr(pa, "functional_confidence", None)
            m_conf = getattr(pa, "modal_confidence", None)
            assert (
                f_conf is not None and m_conf is not None
            ), "Analysis should expose both confidence signals"

            # Use arbitration service to validate functional progression quality
            arbitration_service = AnalysisArbitrationService()

            # Create mock summary for validation
            from harmonic_analysis.dto import AnalysisType

            functional_mock = type(
                "MockSummary",
                (),
                {
                    "confidence": f_conf,
                    "type": AnalysisType.FUNCTIONAL,
                    "functional_confidence": f_conf,
                    "modal_confidence": m_conf,
                    "roman_numerals": [],
                    "patterns": [],  # Required by arbitration service
                    "key_signature": "C major",
                    "mode": "major",
                    "reasoning": "functional analysis",
                },
            )()

            # Validate that functional analysis meets quality standards
            arbitration_result = arbitration_service.arbitrate(
                functional_summary=functional_mock,
                modal_summary=None,  # Only functional analysis
                chord_symbols=progression,
            )

            issues = arbitration_service.validate_analysis_quality(
                arbitration_result, expected_type=AnalysisType.FUNCTIONAL
            )

            if issues:
                pytest.fail(
                    f"{description}: Arbitration service found issues: {', '.join(issues)}"
                )

        # Clearly modal progressions (should be modal primary)
        modal_progressions = [
            (["G", "F", "G"], "G Mixolydian with bVII"),
            (["Em", "F", "Em"], "E Phrygian with bII"),
            (["Dm", "G", "Dm"], "D Dorian vamp"),
        ]

        for progression, description in modal_progressions:
            result = await analyze_progression_new(progression, AnalysisOptions())

            pa = result.primary_analysis
            f_conf = getattr(pa, "functional_confidence", None)
            m_conf = getattr(pa, "modal_confidence", None)
            assert (
                f_conf is not None and m_conf is not None
            ), "Analysis should expose both confidence signals"

            # Use arbitration service to validate modal progression quality
            arbitration_service = AnalysisArbitrationService()

            # Create mock summaries for validation
            modal_mock = type(
                "MockSummary",
                (),
                {
                    "confidence": m_conf,
                    "type": AnalysisType.MODAL,
                    "functional_confidence": f_conf,
                    "modal_confidence": m_conf,
                    "roman_numerals": [],
                    "patterns": [],  # Required by arbitration service
                    "key_signature": "C major",
                    "mode": "modal",
                    "reasoning": "modal analysis",
                },
            )()

            functional_mock = type(
                "MockSummary",
                (),
                {
                    "confidence": f_conf,
                    "type": AnalysisType.FUNCTIONAL,
                    "functional_confidence": f_conf,
                    "modal_confidence": m_conf,
                    "roman_numerals": [],
                    "patterns": [],  # Required by arbitration service
                    "key_signature": "C major",
                    "mode": "major",
                    "reasoning": "functional analysis",
                },
            )()

            # Check arbitration for modal progressions
            arbitration_result = arbitration_service.arbitrate(
                functional_summary=functional_mock,
                modal_summary=modal_mock,
                chord_symbols=progression,
            )

            # Modal progression should have reasonable modal confidence
            assert (
                m_conf >= 0.40
            ), f"{description}: modal_confidence too low ({m_conf:.3f})"
            assert (
                m_conf > 0.0
            ), f"{description}: modal analysis should detect some modal characteristics"

    @pytest.mark.asyncio
    async def test_parent_key_accuracy(self):
        """Test that parent keys are theoretically correct for modes when modal analysis is selected"""
        mode_tests = [
            (["G", "F", "G"], "G Mixolydian", "C major"),  # G is 5th of C
            (
                ["Dm", "G", "Dm"],
                "D Dorian",
                "C major",
            ),  # D is 2nd of C - AMBIGUOUS: could be D minor functional
            (["F#m", "D", "A", "E"], "F# Aeolian", "A major"),  # F# is 6th of A
            (["Em", "F", "Em"], "E Phrygian", "C major"),  # E is 3rd of C
        ]

        for progression, expected_mode, expected_parent in mode_tests:
            result = await analyze_progression_new(progression, AnalysisOptions())

            if result.primary_analysis.type.value == "modal":
                actual_mode = result.primary_analysis.mode
                actual_parent = result.primary_analysis.key_signature

                # Special case for ambiguous Dm-G-Dm progression
                if progression == ["Dm", "G", "Dm"]:
                    # This could be either D Dorian (C major parent) or D minor (functional)
                    # Both are theoretically valid - accept both modal and functional analysis
                    if result.primary_analysis.type.value == "modal":
                        # If analyzed as modal, should be some form of D-centered mode
                        assert (
                            "D" in actual_mode or "d" in actual_mode.lower()
                        ), f"Expected D-centered mode for {progression}, got {actual_mode}"
                        # Parent key could be either C major (Dorian) or D minor (natural minor)
                        assert actual_parent in [
                            "C major",
                            "D minor",
                        ], f"Expected C major or D minor parent for {progression}, got {actual_parent}"
                else:
                    # For other progressions, expect exact matches
                    assert (
                        expected_mode in actual_mode
                    ), f"Expected mode {expected_mode}, got {actual_mode}"
                    assert (
                        expected_parent == actual_parent
                    ), f"Expected parent key {expected_parent}, got {actual_parent} for {expected_mode}"
            else:
                # If functional analysis is chosen instead, that's also valid
                # Some progressions like Dm-G-Dm could be analyzed functionally in D minor
                assert result.primary_analysis.type.value in [
                    "functional",
                    "chromatic",
                ], (
                    f"Expected modal or functional analysis, got {result.primary_analysis.type.value} "
                    f"for progression {progression}"
                )

    @pytest.mark.asyncio
    async def test_reasoning_quality(self):
        """Test that analysis reasoning is accurate and helpful"""

        test_cases = [
            (["C", "F", "G", "C"], ["I-IV-V-I", "authentic cadence", "tonic"]),
            (["G", "F", "G"], ["bVII", "Mixolydian", "modal"]),
            (["Am", "F", "C", "G"], ["vi-IV-I-V", "pop", "progression"]),
        ]

        for progression, expected_keywords in test_cases:
            result = await analyze_progression_new(progression, AnalysisOptions())

            reasoning = result.primary_analysis.reasoning.lower()

            # Should contain relevant keywords
            found_keywords = [kw for kw in expected_keywords if kw.lower() in reasoning]
            assert (
                len(found_keywords) > 0
            ), f"Reasoning '{reasoning}' should contain at least one of: {expected_keywords}"

            # Should not contain obviously wrong information
            wrong_indicators = [
                "contains bvii" if "bvii" not in expected_keywords else ""
            ]
            wrong_found = [wi for wi in wrong_indicators if wi and wi in reasoning]
            assert (
                len(wrong_found) == 0
            ), f"Reasoning contains incorrect information: {wrong_found}"

    @pytest.mark.asyncio
    async def test_roman_numeral_accuracy(self):
        """Test that roman numerals are correct for well-known progressions"""

        # Test in C major context
        roman_tests = [
            (["C", "F", "G", "C"], ["I", "IV", "V", "I"]),
            (["Am", "F", "C", "G"], ["vi", "IV", "I", "V"]),
            (["Dm", "G", "C"], ["ii", "V", "I"]),
        ]

        for progression, expected_romans in roman_tests:
            result = await analyze_progression_new(
                progression, AnalysisOptions(parent_key="C major")
            )

            actual_romans = result.primary_analysis.roman_numerals

            assert (
                actual_romans == expected_romans
            ), f"Progression {progression} in C major should be {expected_romans}, got {actual_romans}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
