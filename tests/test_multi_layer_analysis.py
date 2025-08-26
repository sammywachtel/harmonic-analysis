#!/usr/bin/env python3
"""
Unit tests for multi-layer analysis expectations.

These tests validate the comprehensive analysis framework that should provide:
- Functional harmony analysis with Roman numerals and cadences
- Modal analysis with characteristics and evidence
- Chromatic analysis with secondary dominants and borrowed chords
- UI behavior with primary/alternative interpretations
- Contextual classification (diatonic vs modal borrowing)

These tests are designed to FAIL initially to drive TDD development.
"""

import json
import os
from typing import List

import pytest

from harmonic_analysis.scale_melody_analysis import analyze_scale_melody

# Import the harmonic analysis library
from harmonic_analysis.services.multiple_interpretation_service import (
    analyze_progression_multiple,
)
from harmonic_analysis.types import AnalysisOptions


class TestMultiLayerAnalysis:
    """Test the new multi-layer analysis framework"""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Load test data"""
        test_data_path = os.path.join(
            os.path.dirname(__file__),
            "generated",
            "comprehensive-multi-layer-tests.json",
        )

        with open(test_data_path, "r") as f:
            self.test_data = json.load(f)

        self.test_cases = self.test_data["test_cases"]
        self.thresholds = self.test_data["metadata"]["thresholds"]

    @pytest.mark.asyncio
    async def test_functional_analysis_expectations(self):
        """Test that functional analysis meets new expectations"""
        # Get a functional test case
        functional_case = next(
            tc for tc in self.test_cases if tc["category"] == "functional_clear"
        )

        # Run analysis
        options = AnalysisOptions(
            parent_key=functional_case["parent_key"],
            confidence_threshold=0.3,
            max_alternatives=3,
        )

        result = await analyze_progression_multiple(functional_case["chords"], options)
        expected = functional_case["expected_functional"]

        # Test functional analysis structure
        assert hasattr(
            result.primary_analysis, "roman_numerals"
        ), "Analysis should include Roman numerals"
        assert hasattr(
            result.primary_analysis, "cadences"
        ), "Analysis should include cadence detection"
        assert hasattr(
            result.primary_analysis, "chord_functions"
        ), "Analysis should include chord functions"

        # Test confidence expectations
        functional_confidence = self._get_functional_confidence(result)
        assert (
            functional_confidence >= expected["confidence"] - 0.15
        ), f"Functional confidence {functional_confidence} below expected {expected['confidence']}"

        # Test Roman numeral accuracy
        if expected["detected"] and expected["roman_numerals"]:
            actual_romans = getattr(result.primary_analysis, "roman_numerals", [])
            assert len(actual_romans) == len(
                expected["roman_numerals"]
            ), "Roman numeral count mismatch"

    @pytest.mark.asyncio
    async def test_modal_analysis_expectations(self):
        """Test that modal analysis meets new expectations"""
        # Get a modal test case
        modal_case = next(
            tc
            for tc in self.test_cases
            if tc["category"] == "modal_characteristic"
            and tc["expected_modal"]["detected"]
        )

        # Run analysis
        options = AnalysisOptions(
            parent_key=modal_case["parent_key"],
            confidence_threshold=0.3,
            max_alternatives=3,
        )

        result = await analyze_progression_multiple(modal_case["chords"], options)
        expected = modal_case["expected_modal"]

        # Test modal analysis structure
        assert hasattr(
            result.primary_analysis, "modal_characteristics"
        ), "Analysis should include modal characteristics"
        assert hasattr(
            result.primary_analysis, "evidence"
        ), "Analysis should include modal evidence"
        assert hasattr(
            result.primary_analysis, "parent_key_relationship"
        ), "Analysis should include parent key relationship"

        # Test confidence expectations
        modal_confidence = self._get_modal_confidence(result)
        if expected["detected"]:
            assert (
                modal_confidence >= self.thresholds["modal"]
            ), f"Modal confidence {modal_confidence} below threshold {self.thresholds['modal']}"

        # Test modal characteristics detection
        if expected["modal_characteristics"]:
            actual_characteristics = getattr(
                result.primary_analysis, "modal_characteristics", []
            )
            assert (
                len(actual_characteristics) > 0
            ), "Should detect modal characteristics"

    @pytest.mark.asyncio
    async def test_chromatic_analysis_expectations(self):
        """Test that chromatic analysis meets new expectations"""
        # Get a chromatic test case
        chromatic_case = next(
            tc for tc in self.test_cases if tc["category"] == "chromatic_secondary"
        )

        # Run analysis
        options = AnalysisOptions(
            parent_key=chromatic_case["parent_key"],
            confidence_threshold=0.3,
            max_alternatives=3,
        )

        result = await analyze_progression_multiple(chromatic_case["chords"], options)
        expected = chromatic_case["expected_chromatic"]

        # Test chromatic analysis structure
        assert hasattr(
            result.primary_analysis, "secondary_dominants"
        ), "Analysis should include secondary dominants"
        assert hasattr(
            result.primary_analysis, "borrowed_chords"
        ), "Analysis should include borrowed chords"
        assert hasattr(
            result.primary_analysis, "chromatic_mediants"
        ), "Analysis should include chromatic mediants"

        # Test secondary dominant detection
        if expected["secondary_dominants"]:
            actual_secondaries = getattr(
                result.primary_analysis, "secondary_dominants", []
            )
            assert len(actual_secondaries) > 0, "Should detect secondary dominants"

            # Check structure of secondary dominants
            if actual_secondaries:
                secondary = actual_secondaries[0]
                assert (
                    "chord" in secondary
                ), "Secondary dominant should have chord field"
                assert (
                    "target" in secondary
                ), "Secondary dominant should have target field"
                assert (
                    "roman_numeral" in secondary
                ), "Secondary dominant should have Roman numeral"

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Framework not yet implemented")
    async def test_contextual_classification(self):
        """Test contextual classification (diatonic vs modal borrowing)"""
        # Test diatonic case
        diatonic_case = next(
            tc
            for tc in self.test_cases
            if tc["parent_key"] is not None and tc["category"] == "functional_clear"
        )

        options = AnalysisOptions(parent_key=diatonic_case["parent_key"])
        result = await analyze_progression_multiple(diatonic_case["chords"], options)

        # Should classify as diatonic when chords fit the key
        assert hasattr(
            result.primary_analysis, "contextual_classification"
        ), "Analysis should include contextual classification"

        classification = getattr(
            result.primary_analysis, "contextual_classification", None
        )
        assert classification in [
            "diatonic",
            "modal_borrowing",
            "modal_candidate",
        ], f"Invalid classification: {classification}"

        # Test modal borrowing case - find a case where expected context differs from key
        borrowing_case = next(
            (
                tc
                for tc in self.test_cases
                if tc["parent_key"] is not None
                and tc["category"] == "modal_characteristic"
                and tc["expected_modal"]["parent_key_relationship"] == "conflicts"
            ),
            None,
        )

        if borrowing_case:
            options = AnalysisOptions(parent_key=borrowing_case["parent_key"])
            result = await analyze_progression_multiple(
                borrowing_case["chords"], options
            )

            classification = getattr(
                result.primary_analysis, "contextual_classification", None
            )
            # Should detect this as modal borrowing since it conflicts with the given key
            assert (
                classification == "modal_borrowing"
            ), f"Expected modal_borrowing, got {classification}"

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Framework not yet implemented")
    async def test_ui_behavior_expectations(self):
        """Test UI behavior matches expectations"""
        # Get a test case with multiple analyses expected
        multi_analysis_case = next(
            tc
            for tc in self.test_cases
            if len(tc["expected_ui"]["displayed_analyses"]) >= 2
        )

        options = AnalysisOptions(
            parent_key=multi_analysis_case["parent_key"],
            confidence_threshold=0.3,
            max_alternatives=3,
        )

        result = await analyze_progression_multiple(
            multi_analysis_case["chords"], options
        )
        expected_ui = multi_analysis_case["expected_ui"]

        # Test that we can determine which analyses should be displayed
        displayed_analyses = self._get_displayed_analyses(result)
        expected_displayed = set(expected_ui["displayed_analyses"])

        assert len(displayed_analyses) >= len(
            expected_displayed
        ), f"Expected at least {len(expected_displayed)} displayed analyses, got {len(displayed_analyses)}"

        # Test primary interpretation logic
        primary = self._get_primary_interpretation(result)
        allowed_primaries = (
            expected_ui["allowed_primary_interpretations"]
            if "allowed_primary_interpretations" in expected_ui
            else expected_ui["alternative_interpretations"]
            + [expected_ui["primary_interpretation"]]
        )

        assert (
            primary in allowed_primaries
        ), f"Primary interpretation '{primary}' not in allowed list {allowed_primaries}"

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Framework not yet implemented")
    async def test_confidence_calibration(self):
        """Test that confidence scores are properly calibrated"""
        # Test across different categories
        for category in [
            "functional_clear",
            "modal_characteristic",
            "chromatic_secondary",
        ]:
            cases = [tc for tc in self.test_cases if tc["category"] == category][
                :3
            ]  # Test 3 per category

            for case in cases:
                options = AnalysisOptions(
                    parent_key=case["parent_key"],
                    confidence_threshold=0.3,
                    max_alternatives=3,
                )

                result = await analyze_progression_multiple(case["chords"], options)

                # Check functional confidence
                functional_conf = self._get_functional_confidence(result)
                expected_functional = case["expected_functional"]["confidence"]
                variance = abs(functional_conf - expected_functional)

                assert (
                    variance <= 0.25
                ), f"Functional confidence variance {variance} too high for {case['id']}"

                # Check modal confidence
                modal_conf = self._get_modal_confidence(result)
                expected_modal = case["expected_modal"]["confidence"]
                variance = abs(modal_conf - expected_modal)

                assert (
                    variance <= 0.25
                ), f"Modal confidence variance {variance} too high for {case['id']}"

    @pytest.mark.asyncio
    async def test_scale_melody_expectations(self):
        """Test scale and melody analysis expectations from generated test data"""
        # Get scale/melody test cases from generated test data
        scale_melody_cases = [
            tc
            for tc in self.test_cases
            if tc["category"] == "scale_melody" and tc.get("expected_scale_melody")
        ]

        assert len(scale_melody_cases) > 0, "Should have scale/melody test cases"

        for case in scale_melody_cases[:3]:  # Test first 3 cases
            scale_expectations = case["expected_scale_melody"]

            # Test that framework provides the expected fields
            result = self._analyze_scale_with_enhanced_expectations(
                scale_expectations["notes"], scale_expectations.get("key")
            )

            # Test parent scale detection
            assert hasattr(result, "parent_scales"), "Should detect parent scales"
            expected_parents = set(scale_expectations["parent_scales"])
            actual_parents = set(result.parent_scales)
            assert expected_parents.issubset(
                actual_parents
            ), f"Missing parent scales: expected {expected_parents}, got {actual_parents}"

            # Test diatonic classification
            assert hasattr(result, "diatonic_in_key"), "Should test diatonic fitness"
            expected_diatonic = scale_expectations["diatonic_in_key"]
            assert (
                result.diatonic_in_key == expected_diatonic
            ), f"Diatonic classification mismatch: expected {expected_diatonic}, got {result.diatonic_in_key}"

            # Test contextual classification
            assert hasattr(result, "classification"), "Should classify usage context"
            expected_classification = scale_expectations["classification"]
            assert (
                result.classification == expected_classification
            ), f"Classification mismatch: expected {expected_classification}, got {result.classification}"

            # Test modal labels
            assert hasattr(result, "modal_labels"), "Should provide modal labels"
            expected_modal_labels = scale_expectations["modal_labels"]
            # Check that at least some expected modal labels are present
            for tonic, expected_label in expected_modal_labels.items():
                if tonic in result.modal_labels:
                    # Allow flexible matching - just check the mode name is present
                    mode_name = expected_label.split()[
                        -1
                    ]  # e.g., "Dorian" from "A Dorian"
                    assert (
                        mode_name in result.modal_labels[tonic]
                    ), f"Modal label mismatch for {tonic}: expected {expected_label}, got {result.modal_labels[tonic]}"

            # Test rationale is provided
            assert hasattr(result, "rationale"), "Should provide analysis rationale"
            assert len(result.rationale) > 0, "Rationale should not be empty"

            # Test melody-specific expectations
            if scale_expectations.get("melody"):
                assert hasattr(
                    result, "suggested_tonic"
                ), "Should suggest tonic for melodies"
                assert hasattr(
                    result, "confidence"
                ), "Should provide confidence for melodies"
                if scale_expectations.get("suggested_tonic"):
                    assert (
                        result.suggested_tonic == scale_expectations["suggested_tonic"]
                    ), f"Suggested tonic mismatch: expected {scale_expectations['suggested_tonic']}, got {result.suggested_tonic}"

    # Helper methods

    def _get_functional_confidence(self, result) -> float:
        """Extract functional confidence from analysis result"""
        if hasattr(result.primary_analysis, "functional_confidence"):
            return result.primary_analysis.functional_confidence
        elif result.primary_analysis.type.value == "functional":
            return result.primary_analysis.confidence
        else:
            return 0.0

    def _get_modal_confidence(self, result) -> float:
        """Extract modal confidence from analysis result"""
        if hasattr(result.primary_analysis, "modal_confidence"):
            return result.primary_analysis.modal_confidence
        elif result.primary_analysis.type.value == "modal":
            return result.primary_analysis.confidence
        else:
            return 0.0

    def _get_displayed_analyses(self, result) -> List[str]:
        """Determine which analyses should be displayed based on thresholds"""
        displayed = []

        functional_conf = self._get_functional_confidence(result)
        if functional_conf >= self.thresholds["functional"]:
            displayed.append("functional")

        modal_conf = self._get_modal_confidence(result)
        if modal_conf >= self.thresholds["modal"]:
            displayed.append("modal")

        # Add chromatic if above threshold
        if hasattr(result.primary_analysis, "chromatic_confidence"):
            chromatic_conf = result.primary_analysis.chromatic_confidence
            if chromatic_conf >= self.thresholds["chromatic"]:
                displayed.append("chromatic")

        return displayed

    def _get_primary_interpretation(self, result) -> str:
        """Get primary interpretation based on highest confidence above threshold"""
        confidences = {
            "functional": self._get_functional_confidence(result),
            "modal": self._get_modal_confidence(result),
            "chromatic": getattr(result.primary_analysis, "chromatic_confidence", 0.0),
        }

        # Filter to above threshold
        valid = {k: v for k, v in confidences.items() if v >= self.thresholds[k]}

        if not valid:
            return "undetermined"

        return max(valid.keys(), key=lambda k: valid[k])

    def _analyze_scale_with_enhanced_expectations(
        self, notes: List[str], key: str = None
    ):
        """Real scale analysis using the implemented framework"""
        # Use the real scale/melody analysis framework
        return analyze_scale_melody(notes=notes, key=key, melody=False)

    def _analyze_scale_with_context(self, notes: List[str], key: str = None):
        """Backward compatibility method"""
        return self._analyze_scale_with_enhanced_expectations(notes, key)


# Specific test classes for different analysis types


class TestFunctionalHarmonyFramework:
    """Test functional harmony analysis framework"""

    @pytest.mark.asyncio
    async def test_roman_numeral_generation(self):
        """Test accurate Roman numeral generation"""
        test_cases = [
            {
                "chords": ["C", "F", "G", "C"],
                "key": "C major",
                "expected_romans": ["I", "IV", "V", "I"],
            },
            {
                "chords": ["Am", "Dm", "G", "C"],
                "key": "C major",
                "expected_romans": ["vi", "ii", "V", "I"],
            },
            {
                "chords": ["Dm", "G", "C"],
                "key": "C major",
                "expected_romans": ["ii", "V", "I"],
            },
        ]

        for case in test_cases:
            options = AnalysisOptions(parent_key=case["key"])
            result = await analyze_progression_multiple(case["chords"], options)

            # Roman numerals should be available and accurate
            assert hasattr(
                result.primary_analysis, "roman_numerals"
            ), "Analysis should include Roman numerals"

            romans = getattr(result.primary_analysis, "roman_numerals", [])
            expected = case["expected_romans"]

            assert len(romans) == len(
                expected
            ), f"Roman numeral count mismatch: expected {len(expected)}, got {len(romans)}"

            # Allow some flexibility in Roman numeral representation
            for i, (actual, expected_roman) in enumerate(zip(romans, expected)):
                assert (
                    actual.replace("°", "o").lower()
                    == expected_roman.replace("°", "o").lower()
                ), f"Roman numeral mismatch at position {i}: expected {expected_roman}, got {actual}"


class TestModalAnalysisFramework:
    """Test modal analysis framework"""

    @pytest.mark.asyncio
    async def test_modal_characteristic_detection(self):
        """Test detection of modal characteristics"""
        # Mixolydian progression with bVII
        options = AnalysisOptions(parent_key="C major")
        result = await analyze_progression_multiple(["C", "Bb", "F", "C"], options)

        # Should detect modal characteristics
        assert hasattr(
            result.primary_analysis, "modal_characteristics"
        ), "Should detect modal characteristics"

        characteristics = getattr(result.primary_analysis, "modal_characteristics", [])
        assert (
            len(characteristics) > 0
        ), "Should identify specific modal characteristics"

        # Should include evidence for modal interpretation
        assert hasattr(
            result.primary_analysis, "evidence"
        ), "Should provide evidence for modal interpretation"

        evidence = getattr(result.primary_analysis, "evidence", [])
        modal_evidence = [
            e
            for e in evidence
            if "modal" in str(e).lower() or "mixolydian" in str(e).lower()
        ]
        assert len(modal_evidence) > 0, "Should have specific modal evidence"


class TestChromaticAnalysisFramework:
    """Test chromatic analysis framework"""

    @pytest.mark.asyncio
    async def test_secondary_dominant_detection(self):
        """Test detection of secondary dominants"""
        # Classic ii-V with secondary dominant: C - A7 - Dm - G - C
        options = AnalysisOptions(parent_key="C major")
        result = await analyze_progression_multiple(
            ["C", "A7", "Dm", "G", "C"], options
        )

        # Should detect secondary dominants
        assert hasattr(
            result.primary_analysis, "secondary_dominants"
        ), "Should detect secondary dominants"

        secondaries = getattr(result.primary_analysis, "secondary_dominants", [])
        assert len(secondaries) > 0, "Should identify A7 as V7/ii"

        # Check structure of detected secondary
        if secondaries:
            secondary = secondaries[0]
            assert "chord" in secondary, "Secondary should identify the chord"
            assert "target" in secondary, "Secondary should identify the target"
            assert (
                "roman_numeral" in secondary
            ), "Secondary should have Roman numeral like V7/ii"

            # A7 should target Dm
            assert secondary["chord"] == "A7", f"Expected A7, got {secondary['chord']}"
            assert (
                secondary["target"] == "Dm"
            ), f"Expected Dm target, got {secondary['target']}"


# Mark most tests as expected to fail initially (except scale_melody_expectations which passes)
# pytestmark = pytest.mark.xfail(
#     reason="These tests define the new framework - should fail until implementation"
# )
