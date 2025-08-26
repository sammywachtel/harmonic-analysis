#!/usr/bin/env python3
"""
Comprehensive Multi-Layer Test Generator

Generates comprehensive test cases with multi-layer analysis expectations for the
harmonic analysis library. This script creates test cases that validate functional
harmony, modal analysis, and chromatic analysis simultaneously.

Key Features:
- Generates 427+ test cases across multiple categories
- Creates realistic expectations for all analysis types
- Includes proper Roman numeral generation (FIXED as of Aug 2025)
- Supports confidence scoring expectations
- Exports to JSON and CSV formats for comprehensive validation

Categories:
- modal_characteristic: 168 tests - Clear modal progressions
- modal_contextless: 168 tests - Modal progressions without parent key
- functional_clear: 60 tests - Unambiguous functional harmony
- chromatic_*: 7 tests - Secondary dominants and borrowed chords
- ambiguous: 9 tests - Theoretically unclear progressions
- edge_*: 10 tests - Edge cases (single chords, repetition, etc.)
- jazz_complex: 3 tests - Complex jazz harmony

Usage:
    python scripts/generate_comprehensive_multi_layer_tests.py

Output:
    tests/generated/comprehensive-multi-layer-tests.json
    tests/generated/comprehensive-multi-layer-tests.csv

Historical Note:
Originally had a critical bug in chord_to_roman_numeral() that returned "I"
for all major chords, causing widespread test failures. Fixed Aug 2025 to
properly calculate Roman numerals based on chord root and key center.

Author: Music Theory Analysis Team
Date: August 2025
"""

import csv
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

# === Mode Families derived from frontend allScaleData (intervals in semitones) ===
ALL_MODE_FAMILIES = [
    {
        "name": "Major Scale",
        "tableId": "major-scale-modes",
        "is_diatonic": True,
        "modes": [
            {
                "degree": "I",
                "name": "Ionian",
                "intervals": [0, 2, 4, 5, 7, 9, 11],
                "formula": "1, 2, 3, 4, 5, 6, 7",
            },
            {
                "degree": "II",
                "name": "Dorian",
                "intervals": [0, 2, 3, 5, 7, 9, 10],
                "formula": "1, 2, ♭3, 4, 5, 6, ♭7",
            },
            {
                "degree": "III",
                "name": "Phrygian",
                "intervals": [0, 1, 3, 5, 7, 8, 10],
                "formula": "1, ♭2, ♭3, 4, 5, ♭6, ♭7",
            },
            {
                "degree": "IV",
                "name": "Lydian",
                "intervals": [0, 2, 4, 6, 7, 9, 11],
                "formula": "1, 2, 3, ♯4, 5, 6, 7",
            },
            {
                "degree": "V",
                "name": "Mixolydian",
                "intervals": [0, 2, 4, 5, 7, 9, 10],
                "formula": "1, 2, 3, 4, 5, 6, ♭7",
            },
            {
                "degree": "VI",
                "name": "Aeolian",
                "intervals": [0, 2, 3, 5, 7, 8, 10],
                "formula": "1, 2, ♭3, 4, 5, ♭6, ♭7",
            },
            {
                "degree": "VII",
                "name": "Locrian",
                "intervals": [0, 1, 3, 5, 6, 8, 10],
                "formula": "1, ♭2, ♭3, 4, ♭5, ♭6, ♭7",
            },
        ],
    },
    {
        "name": "Melodic Minor",
        "tableId": "melodic-minor-modes",
        "is_diatonic": True,
        "modes": [
            {
                "degree": "I",
                "name": "Melodic Minor",
                "intervals": [0, 2, 3, 5, 7, 9, 11],
                "formula": "1, 2, ♭3, 4, 5, 6, 7",
            },
            {
                "degree": "II",
                "name": "Dorian ♭2",
                "intervals": [0, 1, 3, 5, 7, 9, 10],
                "formula": "1, ♭2, ♭3, 4, 5, 6, ♭7",
            },
            {
                "degree": "III",
                "name": "Lydian Augmented",
                "intervals": [0, 2, 4, 6, 8, 9, 11],
                "formula": "1, 2, 3, ♯4, ♯5, 6, 7",
            },
            {
                "degree": "IV",
                "name": "Lydian Dominant",
                "intervals": [0, 2, 4, 6, 7, 9, 10],
                "formula": "1, 2, 3, ♯4, 5, 6, ♭7",
            },
            {
                "degree": "V",
                "name": "Mixolydian ♭6",
                "intervals": [0, 2, 4, 5, 7, 8, 10],
                "formula": "1, 2, 3, 4, 5, ♭6, ♭7",
            },
            {
                "degree": "VI",
                "name": "Locrian ♮2",
                "intervals": [0, 2, 3, 5, 6, 8, 10],
                "formula": "1, 2, ♭3, 4, ♭5, ♭6, ♭7",
            },
            {
                "degree": "VII",
                "name": "Altered",
                "intervals": [0, 1, 3, 4, 6, 8, 10],
                "formula": "1, ♭2, ♭3, ♭4, ♭5, ♭6, ♭7",
            },
        ],
    },
    {
        "name": "Harmonic Minor",
        "tableId": "harmonic-minor-modes",
        "is_diatonic": True,
        "modes": [
            {
                "degree": "I",
                "name": "Harmonic Minor",
                "intervals": [0, 2, 3, 5, 7, 8, 11],
                "formula": "1, 2, ♭3, 4, 5, ♭6, 7",
            },
            {
                "degree": "II",
                "name": "Locrian ♮6",
                "intervals": [0, 1, 3, 5, 6, 8, 10],
                "formula": "1, ♭2, ♭3, 4, ♭5, 6, ♭7",
            },
            {
                "degree": "III",
                "name": "Ionian ♯5",
                "intervals": [0, 2, 4, 5, 8, 9, 11],
                "formula": "1, 2, 3, 4, ♯5, 6, 7",
            },
            {
                "degree": "IV",
                "name": "Dorian ♯4",
                "intervals": [0, 2, 3, 6, 7, 9, 10],
                "formula": "1, 2, ♭3, ♯4, 5, 6, ♭7",
            },
            {
                "degree": "V",
                "name": "Phrygian Dominant",
                "intervals": [0, 1, 4, 5, 7, 8, 10],
                "formula": "1, ♭2, 3, 4, 5, ♭6, ♭7",
            },
            {
                "degree": "VI",
                "name": "Lydian ♯2",
                "intervals": [0, 3, 4, 6, 8, 10, 11],
                "formula": "1, ♯2, 3, ♯4, 5, 6, 7",
            },
            {
                "degree": "VII",
                "name": "Super-Locrian",
                "intervals": [0, 1, 3, 4, 6, 7, 9],
                "formula": "1, ♭2, ♭3, ♭4, ♭5, ♭6, ♭7",
            },
        ],
    },
    {
        "name": "Harmonic Major",
        "tableId": "harmonic-major-modes",
        "is_diatonic": True,
        "modes": [
            {
                "degree": "I",
                "name": "Harmonic Major",
                "intervals": [0, 2, 4, 5, 7, 8, 11],
                "formula": "1, 2, 3, 4, 5, ♭6, 7",
            },
            {
                "degree": "II",
                "name": "Dorian ♭5",
                "intervals": [0, 2, 3, 5, 6, 9, 10],
                "formula": "1, 2, ♭3, 4, ♭5, 6, ♭7",
            },
            {
                "degree": "III",
                "name": "Phrygian ♭4",
                "intervals": [0, 1, 3, 4, 7, 8, 10],
                "formula": "1, ♭2, ♭3, ♭4, 5, ♭6, ♭7",
            },
            {
                "degree": "IV",
                "name": "Lydian ♭3",
                "intervals": [0, 2, 3, 6, 7, 9, 11],
                "formula": "1, 2, ♭3, ♯4, 5, 6, 7",
            },
            {
                "degree": "V",
                "name": "Mixolydian ♭2",
                "intervals": [0, 1, 4, 5, 7, 9, 10],
                "formula": "1, ♭2, 3, 4, 5, 6, ♭7",
            },
            {
                "degree": "VI",
                "name": "Lydian Aug ♯2",
                "intervals": [0, 3, 4, 6, 8, 10, 11],
                "formula": "1, ♯2, 3, ♯4, ♯5, 6, 7",
            },
            {
                "degree": "VII",
                "name": "Locrian ♭7♭5",
                "intervals": [0, 1, 3, 5, 6, 8, 9],
                "formula": "1, ♭2, ♭3, 4, ♭5, ♭6, ♭♭7",
            },
        ],
    },
    {
        "name": "Double Harmonic Major",
        "tableId": "double-harmonic-major-modes",
        "is_diatonic": True,
        "modes": [
            {
                "degree": "I",
                "name": "Double Harmonic",
                "intervals": [0, 1, 4, 5, 7, 8, 11],
                "formula": "1, ♭2, 3, 4, 5, ♭6, 7",
            },
            {
                "degree": "II",
                "name": "Lydian ♯2 ♯6",
                "intervals": [0, 3, 4, 6, 7, 10, 11],
                "formula": "1, ♯2, 3, ♯4, 5, ♯6, 7",
            },
            {
                "degree": "III",
                "name": "Ultraphrygian",
                "intervals": [0, 1, 3, 4, 7, 9, 10],
                "formula": "1, ♭2, ♭3, ♭4, 5, 6, ♭7",
            },
            {
                "degree": "IV",
                "name": "Hungarian Minor",
                "intervals": [0, 2, 3, 6, 7, 8, 10],
                "formula": "1, 2, ♭3, ♯4, 5, ♭6, ♭7",
            },
            {
                "degree": "V",
                "name": "Oriental",
                "intervals": [0, 1, 4, 5, 6, 9, 10],
                "formula": "1, ♭2, 3, 4, ♭5, 6, ♭7",
            },
            {
                "degree": "VI",
                "name": "Ionian Aug ♯2",
                "intervals": [0, 3, 4, 5, 8, 9, 11],
                "formula": "1, ♯2, 3, 4, ♯5, 6, 7",
            },
            {
                "degree": "VII",
                "name": "Ultra-Locrian",
                "intervals": [0, 1, 2, 4, 5, 7, 8],
                "formula": "1, ♭2, ♭♭3, ♭4, ♭5, ♭6, ♭♭7",
            },
        ],
    },
    {
        "name": "Major Pentatonic",
        "tableId": "major-pentatonic-modes",
        "is_diatonic": False,
        "modes": [
            {
                "degree": "I",
                "name": "Mode I",
                "intervals": [0, 2, 4, 7, 9],
                "formula": "1, 2, 3, 5, 6",
            },
            {
                "degree": "II",
                "name": "Mode II",
                "intervals": [0, 2, 5, 7, 10],
                "formula": "1, 2, 4, 5, ♭7",
            },
            {
                "degree": "III",
                "name": "Mode III",
                "intervals": [0, 3, 5, 8, 10],
                "formula": "1, ♭3, 4, ♭6, ♭7",
            },
            {
                "degree": "IV",
                "name": "Mode IV",
                "intervals": [0, 2, 5, 7, 9],
                "formula": "1, 2, 4, 5, 6",
            },
            {
                "degree": "V",
                "name": "Mode V",
                "intervals": [0, 3, 5, 7, 10],
                "formula": "1, ♭3, 4, 5, ♭7",
            },
        ],
    },
    {
        "name": "Blues Scale",
        "tableId": "blues-scale-modes",
        "is_diatonic": False,
        "modes": [
            {
                "degree": "I",
                "name": "Mode I",
                "intervals": [0, 3, 5, 6, 7, 10],
                "formula": "1, ♭3, 4, ♭5, 5, ♭7",
            },
            {
                "degree": "II",
                "name": "Mode II",
                "intervals": [0, 2, 3, 4, 7, 9],
                "formula": "1, 2, ♭3, 3, 5, 6",
            },
            {
                "degree": "III",
                "name": "Mode III",
                "intervals": [0, 1, 2, 5, 7, 10],
                "formula": "1, ♭2, 2, 4, 5, ♭7",
            },
            {
                "degree": "IV",
                "name": "Mode IV",
                "intervals": [0, 1, 4, 6, 9, 11],
                "formula": "1, ♭2, 3, ♯4, 6, 7",
            },
            {
                "degree": "V",
                "name": "Mode V",
                "intervals": [0, 3, 5, 8, 10, 11],
                "formula": "1, ♭3, 4, ♭6, ♭7, 7",
            },
            {
                "degree": "VI",
                "name": "Mode VI",
                "intervals": [0, 2, 3, 7, 8, 9],
                "formula": "1, 2, ♭3, 5, ♭6, 6",
            },
        ],
    },
]


@dataclass
class FunctionalExpectation:
    detected: bool
    key_center: Optional[str]
    mode: str
    roman_numerals: List[str]
    confidence: float
    threshold: float
    cadences: List[Dict[str, Any]]
    progression_type: str
    chord_functions: List[Dict[str, Any]]


@dataclass
class ModalExpectation:
    detected: bool
    mode: Optional[str]
    confidence: float
    threshold: float
    evidence: List[str]
    parent_key_relationship: Optional[str]
    tonic_center: Optional[str]
    modal_characteristics: List[str]


@dataclass
class ChromaticExpectation:
    detected: bool
    confidence: float
    threshold: float
    secondary_dominants: List[Dict[str, Any]]
    borrowed_chords: List[Dict[str, Any]]
    chromatic_mediants: List[Dict[str, Any]]
    alterations: List[Dict[str, Any]]


@dataclass
class UIExpectation:
    primary_interpretation: str
    alternative_interpretations: List[str]
    displayed_analyses: List[str]
    confidence_display: Dict[str, str]
    recommended_pedagogical_level: str


@dataclass
class ScaleMelodyExpectation:
    notes: List[str]
    key: Optional[str]
    melody: bool
    parent_scales: List[str]
    diatonic_in_key: Optional[bool]
    non_diatonic_pitches: List[str]
    modal_labels: Dict[str, str]
    classification: str
    suggested_tonic: Optional[str] = None
    confidence: Optional[float] = None
    rationale: Optional[str] = None


@dataclass
class ValidationCriteria:
    acceptable_confidence_variance: float
    requires_all_analyses: bool
    minimum_displayed_analyses: int
    allowed_primary_interpretations: List[str]
    critical_thresholds: Dict[str, float]


@dataclass
class MultiLayerTestCase:
    id: str
    description: str
    chords: List[str]
    parent_key: Optional[str]
    category: str
    theoretical_basis: str
    expected_functional: FunctionalExpectation
    expected_modal: ModalExpectation
    expected_chromatic: ChromaticExpectation
    expected_ui: UIExpectation
    validation: ValidationCriteria
    expected_scale_melody: Optional[ScaleMelodyExpectation] = None


class ComprehensiveMultiLayerGenerator:
    """Comprehensive multi-layer test generator matching frontend behavior"""

    def __init__(self):
        self.test_cases: List[MultiLayerTestCase] = []
        self.test_id_counter = 1

        # Real UI thresholds from the application
        self.thresholds = {
            "functional": 0.4,  # Display functional analysis at 40%+
            "modal": 0.6,  # Display modal analysis at 60%+
            "chromatic": 0.5,  # Display chromatic analysis at 50%+
        }

        # Musical intervals in semitones
        self.intervals = {
            "unison": 0,
            "minor2": 1,
            "major2": 2,
            "minor3": 3,
            "major3": 4,
            "perfect4": 5,
            "tritone": 6,
            "perfect5": 7,
            "minor6": 8,
            "major6": 9,
            "minor7": 10,
            "major7": 11,
            "octave": 12,
        }

        # Note mappings for interval calculations
        self.note_map = {
            "C": 0,
            "Db": 1,
            "D": 2,
            "Eb": 3,
            "E": 4,
            "F": 5,
            "Gb": 6,
            "G": 7,
            "Ab": 8,
            "A": 9,
            "Bb": 10,
            "B": 11,
            "C#": 1,
            "D#": 3,
            "F#": 6,
            "G#": 8,
            "A#": 10,
        }

        # Modal parent key relationships
        self.modal_parent_keys = {
            "Ionian": {"offset": 0, "mode": "major"},
            "Dorian": {"offset": -2, "mode": "major"},
            "Phrygian": {"offset": -4, "mode": "major"},
            "Lydian": {"offset": 2, "mode": "major"},
            "Mixolydian": {"offset": -7, "mode": "major"},
            "Aeolian": {"offset": -9, "mode": "major"},
            "Locrian": {"offset": -11, "mode": "major"},
        }

        # Default tonics to exercise enharmonic coverage
        self.default_tonics = [
            "C",
            "G",
            "D",
            "A",
            "E",
            "B",
            "F#",
            "Db",
            "Ab",
            "Eb",
            "Bb",
            "F",
        ]

    def generate_all_tests(self) -> List[MultiLayerTestCase]:
        """🎵 GENERATE ALL THE TESTS!"""
        print("🚀 COMPREHENSIVE MULTI-LAYER TEST GENERATION REVOLUTION!")
        print("💪 Going HARD with sophisticated test expectations!\n")

        self.generate_modal_characteristic_tests()  # 300+ tests
        self.generate_functional_harmony_tests()  # 200+ tests
        self.generate_chromatic_analysis_tests()  # 150+ tests
        self.generate_ambiguous_context_tests()  # 200+ tests
        self.generate_edge_and_special_cases()  # 100+ tests
        self.generate_jazz_and_complex_harmony()  # 150+ tests
        self.generate_scale_and_melody_tests()  # enhanced scale & melody tests

        self.export_results()
        self.generate_statistics()

        return self.test_cases

    def generate_modal_characteristic_tests(self):
        """
        🎭 MODAL CHARACTERISTIC TESTS - Clear modal progressions with strong
        characteristics
        """
        print("  🎭 Generating modal characteristic tests...")

        modes = [
            "Ionian",
            "Dorian",
            "Phrygian",
            "Lydian",
            "Mixolydian",
            "Aeolian",
            "Locrian",
        ]
        roots = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

        for root in roots:
            for mode in modes:
                # Generate characteristic progressions for each mode
                progressions = self.get_modal_progressions(root, mode)

                for progression in progressions:
                    parent_key = self.get_parent_key(root, mode)

                    # Test with parent key context (high confidence)
                    self.test_cases.append(
                        self.create_multi_layer_test(
                            description=(
                                f'{root} {mode} - {", ".join(progression["chords"])} '
                                "(with context)"
                            ),
                            chords=progression["chords"],
                            parent_key=parent_key,
                            category="modal_characteristic",
                            theoretical_basis=progression["explanation"],
                            expected_strengths={
                                "functional": 0.5,  # Moderate functional strength
                                "modal": 0.9,  # Very strong modal characteristics
                                "chromatic": 0.1,  # Not chromatic
                            },
                        )
                    )

                    # Test without parent key (lower confidence but still detectable)
                    self.test_cases.append(
                        self.create_multi_layer_test(
                            description=(
                                f'{root} {mode} - {", ".join(progression["chords"])} '
                                "(no context)"
                            ),
                            chords=progression["chords"],
                            parent_key=None,
                            category="modal_contextless",
                            theoretical_basis=progression["explanation"]
                            + " (testing without parent key)",
                            expected_strengths={
                                "functional": 0.3,  # Lower without context
                                "modal": 0.7,  # Still strong modal characteristics
                                "chromatic": 0.1,  # Not chromatic
                            },
                        )
                    )

    def generate_functional_harmony_tests(self):
        """
        🎵 FUNCTIONAL HARMONY TESTS - Classical functional progressions with
        strong cadences
        """
        print("  🎵 Generating functional harmony tests...")

        keys = [
            "C major",
            "G major",
            "D major",
            "A major",
            "E major",
            "B major",
            "F# major",
            "Db major",
            "Ab major",
            "Eb major",
            "Bb major",
            "F major",
            "A minor",
            "E minor",
            "B minor",
            "F# minor",
            "C# minor",
            "G# minor",
            "Eb minor",
            "Bb minor",
            "F minor",
            "C minor",
            "G minor",
            "D minor",
        ]

        for key in keys:
            is_major = "major" in key
            root = key.replace(" major", "").replace(" minor", "")

            # Generate functional progressions
            progressions = self.get_functional_progressions(root, is_major)

            for progression in progressions:
                self.test_cases.append(
                    self.create_multi_layer_test(
                        description=f'{key} {progression["name"]}',
                        chords=progression["chords"],
                        parent_key=key,
                        category="functional_clear",
                        theoretical_basis=progression["explanation"],
                        expected_strengths={
                            "functional": 0.95,  # Very strong functional
                            "modal": 0.2,  # Weak modal (not characteristic)
                            "chromatic": 0.1,  # Not chromatic
                        },
                    )
                )

    def generate_chromatic_analysis_tests(self):
        """
        ⚡ CHROMATIC ANALYSIS TESTS - Secondary dominants, borrowed chords,
        chromatic mediants
        """
        print("  ⚡ Generating chromatic analysis tests...")

        # Secondary dominants
        secondary_dominants = [
            {
                "chords": ["C", "A7", "Dm", "G", "C"],
                "key": "C major",
                "target": "ii",
                "explanation": "V7/ii resolving to ii",
            },
            {
                "chords": ["C", "D7", "G", "C"],
                "key": "C major",
                "target": "V",
                "explanation": "V7/V resolving to V",
            },
            {
                "chords": ["C", "E7", "Am", "F", "C"],
                "key": "C major",
                "target": "vi",
                "explanation": "V7/vi resolving to vi",
            },
            {
                "chords": ["C", "B7", "Em", "Am", "F", "C"],
                "key": "C major",
                "target": "iii",
                "explanation": "V7/iii resolving to iii",
            },
        ]

        for prog in secondary_dominants:
            self.test_cases.append(
                self.create_multi_layer_test(
                    description=f'{prog["key"]} with {prog["explanation"]}',
                    chords=prog["chords"],
                    parent_key=prog["key"],
                    category="chromatic_secondary",
                    theoretical_basis=prog["explanation"],
                    expected_strengths={
                        "functional": 0.8,  # Strong functional foundation
                        "modal": 0.2,  # Not modal
                        "chromatic": 0.9,  # Very strong chromatic
                    },
                )
            )

        # Borrowed chords
        borrowed_chords = [
            {
                "chords": ["C", "Ab", "Bb", "C"],
                "key": "C major",
                "explanation": "bVI and bVII from parallel minor",
            },
            {
                "chords": ["Am", "F", "G", "Am"],
                "key": "A minor",
                "explanation": "Major IV from parallel major",
            },
            {
                "chords": ["C", "Fm", "C"],
                "key": "C major",
                "explanation": "iv from parallel minor",
            },
        ]

        for prog in borrowed_chords:
            self.test_cases.append(
                self.create_multi_layer_test(
                    description=f'{prog["key"]} with {prog["explanation"]}',
                    chords=prog["chords"],
                    parent_key=prog["key"],
                    category="chromatic_borrowed",
                    theoretical_basis=prog["explanation"],
                    expected_strengths={
                        "functional": 0.7,  # Good functional foundation
                        "modal": 0.4,  # Some modal characteristics
                        "chromatic": 0.8,  # Strong chromatic elements
                    },
                )
            )

    def generate_ambiguous_context_tests(self):
        """
        🤔 AMBIGUOUS CONTEXT TESTS - Progressions that could be interpreted
        multiple ways
        """
        print("  🤔 Generating ambiguous context tests...")

        ambiguous_progressions = [
            {
                "chords": ["Am", "F", "C", "G"],
                "contexts": [
                    {
                        "key": "C major",
                        "interpretation": "vi-IV-I-V functional",
                        "functional": 0.85,
                        "modal": 0.4,
                        "chromatic": 0.1,
                    },
                    {
                        "key": "A minor",
                        "interpretation": "i-bVI-bIII-bVII Aeolian",
                        "functional": 0.5,
                        "modal": 0.8,
                        "chromatic": 0.2,
                    },
                    {
                        "key": None,
                        "interpretation": "Ambiguous without context",
                        "functional": 0.4,
                        "modal": 0.6,
                        "chromatic": 0.1,
                    },
                ],
            },
            {
                "chords": ["C", "Bb", "F", "C"],
                "contexts": [
                    {
                        "key": "F major",
                        "interpretation": "V-IV-I-V Mixolydian",
                        "functional": 0.6,
                        "modal": 0.9,
                        "chromatic": 0.2,
                    },
                    {
                        "key": "C major",
                        "interpretation": "I-bVII-IV-I with borrowed bVII",
                        "functional": 0.7,
                        "modal": 0.5,
                        "chromatic": 0.8,
                    },
                    {
                        "key": None,
                        "interpretation": "Could be modal or chromatic",
                        "functional": 0.4,
                        "modal": 0.7,
                        "chromatic": 0.5,
                    },
                ],
            },
            {
                "chords": ["Dm", "G", "C", "F"],
                "contexts": [
                    {
                        "key": "C major",
                        "interpretation": "ii-V-I-IV functional",
                        "functional": 0.9,
                        "modal": 0.3,
                        "chromatic": 0.1,
                    },
                    {
                        "key": "F major",
                        "interpretation": "vi-II-V-I functional",
                        "functional": 0.85,
                        "modal": 0.2,
                        "chromatic": 0.1,
                    },
                    {
                        "key": None,
                        "interpretation": "Strong functional regardless of key",
                        "functional": 0.8,
                        "modal": 0.2,
                        "chromatic": 0.1,
                    },
                ],
            },
        ]

        for progression in ambiguous_progressions:
            for context in progression["contexts"]:
                self.test_cases.append(
                    self.create_multi_layer_test(
                        description=(
                            f'{"-".join(progression["chords"])} '
                            f'{context["interpretation"]}'
                        ),
                        chords=progression["chords"],
                        parent_key=context["key"],
                        category="ambiguous",
                        theoretical_basis=context["interpretation"],
                        expected_strengths={
                            "functional": context["functional"],
                            "modal": context["modal"],
                            "chromatic": context["chromatic"],
                        },
                    )
                )

    def generate_edge_and_special_cases(self):
        """🔬 EDGE CASES AND SPECIAL SITUATIONS"""
        print("  🔬 Generating edge cases and special situations...")

        # Single chords
        single_chords = ["C", "Dm", "G7", "Cmaj7", "Am7", "F#dim", "Bb"]
        for chord in single_chords:
            self.test_cases.append(
                self.create_multi_layer_test(
                    description=f"Single chord: {chord}",
                    chords=[chord],
                    parent_key=None,
                    category="edge_single",
                    theoretical_basis="Insufficient harmonic context for analysis",
                    expected_strengths={
                        "functional": 0.1,  # Almost no functional context
                        "modal": 0.1,  # Almost no modal context
                        "chromatic": 0.1,  # Almost no chromatic context
                    },
                )
            )

        # Special test cases
        special_cases = [
            {
                "description": "Repeated C major chord",
                "chords": ["C", "C", "C", "C"],
                "basis": "Static harmony with no progression",
                "strengths": {"functional": 0.2, "modal": 0.1, "chromatic": 0.0},
            },
            {
                "description": "Chromatic sequence C-C#-D-D#",
                "chords": ["C", "C#", "D", "D#"],
                "basis": "Chromatic motion without functional logic",
                "strengths": {"functional": 0.1, "modal": 0.3, "chromatic": 0.6},
            },
            {
                "description": "Enharmonic equivalents F#-Gb",
                "chords": ["F#", "Gb"],
                "basis": "Enharmonic equivalents - same pitch different spelling",
                "strengths": {"functional": 0.1, "modal": 0.1, "chromatic": 0.2},
            },
        ]

        for case in special_cases:
            self.test_cases.append(
                self.create_multi_layer_test(
                    description=case["description"],
                    chords=case["chords"],
                    parent_key=None,
                    category=f'edge_{case["description"].split()[0].lower()}',
                    theoretical_basis=case["basis"],
                    expected_strengths=case["strengths"],
                )
            )

    def generate_jazz_and_complex_harmony(self):
        """🎺 JAZZ AND COMPLEX HARMONY"""
        print("  🎺 Generating jazz and complex harmony tests...")

        # Jazz turnarounds
        jazz_progressions = [
            {
                "chords": ["Cmaj7", "A7", "Dm7", "G7"],
                "name": "I-V7/ii-ii7-V7",
                "explanation": "Classic jazz turnaround",
            },
            {
                "chords": ["Cmaj7", "C7", "Fmaj7", "F#dim7", "C/G", "G7", "C"],
                "name": "I-I7-IV-#ivdim7-I/5-V7-I",
                "explanation": "Jazz progression with chromatic passing chord",
            },
            {
                "chords": ["Am7", "D7", "Gmaj7", "Cmaj7"],
                "name": "ii7-V7-I-IV (in G)",
                "explanation": "ii-V-I with extension",
            },
        ]

        for prog in jazz_progressions:
            self.test_cases.append(
                self.create_multi_layer_test(
                    description=f'Jazz: {prog["name"]}',
                    chords=prog["chords"],
                    parent_key="C major",
                    category="jazz_complex",
                    theoretical_basis=prog["explanation"],
                    expected_strengths={
                        "functional": 0.9,  # Strong jazz functional harmony
                        "modal": 0.2,  # Not really modal
                        "chromatic": 0.7,  # Significant chromatic elements
                    },
                )
            )

        # Extended and altered chords
        extended_chords = [
            {
                "chords": ["Cmaj9", "Am11", "Dm9", "G13"],
                "explanation": "Extended chord progression",
            },
            {
                "chords": ["C7alt", "F7#11", "Bb7", "Ebmaj7#5"],
                "explanation": "Altered and modified chords",
            },
        ]

        for prog in extended_chords:
            self.test_cases.append(
                self.create_multi_layer_test(
                    description=f'Extended harmony: {"-".join(prog["chords"])}',
                    chords=prog["chords"],
                    parent_key="C major",
                    category="extended_harmony",
                    theoretical_basis=prog["explanation"],
                    expected_strengths={
                        "functional": 0.8,  # Strong functional foundation
                        "modal": 0.3,  # Some modal implications
                        "chromatic": 0.8,  # Strong chromatic content
                    },
                )
            )

    def create_multi_layer_test(
        self,
        description: str,
        chords: List[str],
        parent_key: Optional[str],
        category: str,
        theoretical_basis: str,
        expected_strengths: Dict[str, float],
    ) -> MultiLayerTestCase:
        """🏗️ CREATE MULTI-LAYER TEST WITH FULL ANALYSIS"""
        test_id = f"multi-{self.test_id_counter}"
        self.test_id_counter += 1

        # Analyze each layer
        functional = self.analyze_functional_layer(
            chords, parent_key, expected_strengths["functional"]
        )
        modal = self.analyze_modal_layer(
            chords, parent_key, expected_strengths["modal"]
        )
        chromatic = self.analyze_chromatic_layer(
            chords, parent_key, expected_strengths["chromatic"]
        )

        # Determine UI behavior
        ui = self.determine_ui_behavior(functional, modal, chromatic)

        # Create validation criteria
        validation = ValidationCriteria(
            acceptable_confidence_variance=0.15,  # Allow ±15% variance
            requires_all_analyses=True,
            minimum_displayed_analyses=(
                len(ui.displayed_analyses) if ui.displayed_analyses else 0
            ),
            allowed_primary_interpretations=ui.alternative_interpretations
            + [ui.primary_interpretation],
            critical_thresholds=self.thresholds.copy(),
        )

        return MultiLayerTestCase(
            id=test_id,
            description=description,
            chords=chords,
            parent_key=parent_key,
            category=category,
            theoretical_basis=theoretical_basis,
            expected_functional=functional,
            expected_modal=modal,
            expected_chromatic=chromatic,
            expected_ui=ui,
            validation=validation,
        )

    def analyze_functional_layer(
        self, chords: List[str], parent_key: Optional[str], strength_hint: float
    ) -> FunctionalExpectation:
        """🎵 ANALYZE FUNCTIONAL LAYER"""
        # Determine key center
        if parent_key:
            key_center = parent_key
            confidence = min(strength_hint * 1.2, 0.95)  # Boost with context
        else:
            key_center = self.infer_key_from_progression(chords)
            confidence = strength_hint * 0.8  # Reduce without context

        mode = "minor" if key_center and "minor" in key_center else "major"

        # Analyze cadences and functions
        cadences = self.detect_cadences(chords, key_center)
        progression_type = self.classify_progression_type(chords, key_center)
        roman_numerals = self.generate_roman_numerals(chords, key_center)
        chord_functions = self.analyze_chord_functions(chords, key_center)

        # Boost confidence for strong functional patterns
        if cadences:
            confidence = min(confidence * 1.3, 0.95)

        if progression_type == "ii-V-I":
            confidence = min(confidence * 1.4, 0.95)

        return FunctionalExpectation(
            detected=confidence >= self.thresholds["functional"],
            key_center=key_center,
            mode=mode,
            roman_numerals=roman_numerals,
            confidence=confidence,
            threshold=self.thresholds["functional"],
            cadences=cadences,
            progression_type=progression_type,
            chord_functions=chord_functions,
        )

    def analyze_modal_layer(
        self, chords: List[str], parent_key: Optional[str], strength_hint: float
    ) -> ModalExpectation:
        """🎭 ANALYZE MODAL LAYER"""
        # Detect modal characteristics
        modal_detection = self.detect_modal_characteristics(chords)

        if modal_detection["detected"]:
            mode = modal_detection["mode"]
            tonic_center = modal_detection["tonic"]
            characteristics = modal_detection["characteristics"]
            evidence = modal_detection["evidence"]
            confidence = strength_hint

            # Check parent key relationship
            parent_key_relationship = None
            if parent_key:
                expected_parent = self.get_parent_key_for_mode(mode)
                if expected_parent == parent_key:
                    parent_key_relationship = "confirms"
                    confidence = min(confidence * 1.2, 0.95)
                    evidence.append("Parent key confirms modal interpretation")
                else:
                    parent_key_relationship = "conflicts"
                    confidence *= 0.8
                    evidence.append("Parent key conflicts with expected modal parent")

            # Boost confidence for strong modal characteristics
            if len(characteristics) >= 2:
                confidence = min(confidence * 1.1, 0.95)
        else:
            mode = None
            tonic_center = None
            characteristics = []
            evidence = []
            confidence = strength_hint
            parent_key_relationship = None

        return ModalExpectation(
            detected=confidence >= self.thresholds["modal"],
            mode=mode,
            confidence=confidence,
            threshold=self.thresholds["modal"],
            evidence=evidence,
            parent_key_relationship=parent_key_relationship,
            tonic_center=tonic_center,
            modal_characteristics=characteristics,
        )

    def analyze_chromatic_layer(
        self, chords: List[str], parent_key: Optional[str], strength_hint: float
    ) -> ChromaticExpectation:
        """⚡ ANALYZE CHROMATIC LAYER"""
        # Detect secondary dominants
        secondary_dominants = self.detect_secondary_dominants(chords, parent_key)

        # Detect borrowed chords
        borrowed_chords = self.detect_borrowed_chords(chords, parent_key)

        # Detect chromatic mediants
        chromatic_mediants = self.detect_chromatic_mediants(chords)

        # Detect alterations
        alterations = self.detect_alterations(chords)

        # Calculate confidence based on chromatic elements found
        chromatic_elements = (
            len(secondary_dominants)
            + len(borrowed_chords)
            + len(chromatic_mediants)
            + len(alterations)
        )

        if chromatic_elements > 0:
            confidence = min(strength_hint + (chromatic_elements * 0.1), 0.95)
        else:
            confidence = strength_hint

        return ChromaticExpectation(
            detected=confidence >= self.thresholds["chromatic"],
            confidence=confidence,
            threshold=self.thresholds["chromatic"],
            secondary_dominants=secondary_dominants,
            borrowed_chords=borrowed_chords,
            chromatic_mediants=chromatic_mediants,
            alterations=alterations,
        )

    def determine_ui_behavior(
        self,
        functional: FunctionalExpectation,
        modal: ModalExpectation,
        chromatic: ChromaticExpectation,
    ) -> UIExpectation:
        """🖥️ DETERMINE UI BEHAVIOR"""
        analyses = [
            {
                "type": "functional",
                "confidence": functional.confidence,
                "threshold": self.thresholds["functional"],
            },
            {
                "type": "modal",
                "confidence": modal.confidence,
                "threshold": self.thresholds["modal"],
            },
            {
                "type": "chromatic",
                "confidence": chromatic.confidence,
                "threshold": self.thresholds["chromatic"],
            },
        ]

        # Filter to displayed analyses (above threshold)
        displayed = [a["type"] for a in analyses if a["confidence"] >= a["threshold"]]

        # Primary interpretation (highest confidence above threshold)
        valid_analyses = [a for a in analyses if a["confidence"] >= a["threshold"]]
        valid_analyses.sort(key=lambda a: a["confidence"], reverse=True)

        primary = valid_analyses[0]["type"] if valid_analyses else "undetermined"

        # Alternative interpretations (others above threshold)
        alternatives = [a["type"] for a in valid_analyses[1:]]

        # Confidence display (for UI)
        confidence_display = {}
        for analysis in displayed:
            conf = next(a["confidence"] for a in analyses if a["type"] == analysis)
            confidence_display[analysis] = f"{round(conf * 100)}%"

        # Pedagogical level recommendation
        pedagogical_level = "beginner"
        if len(displayed) >= 2:
            pedagogical_level = "intermediate"
        if len(displayed) >= 3 or chromatic.confidence >= 0.7:
            pedagogical_level = "advanced"

        return UIExpectation(
            primary_interpretation=primary,
            alternative_interpretations=alternatives,
            displayed_analyses=displayed,
            confidence_display=confidence_display,
            recommended_pedagogical_level=pedagogical_level,
        )

    # Helper methods for music theory analysis (simplified implementations)

    def get_scale_melody_fixtures(self) -> List[Dict[str, Any]]:
        """
        Deterministic, procedurally derived fixtures for scale/melody expectations.
        We only seed INPUTS; all EXPECTED fields are computed so nothing is hard-coded.
        """
        # Seed inputs (scales/melodies + optional key + melody flag)
        seeds = [
            {
                "id": "TC1-dorian-in-C",
                "notes": ["D", "E", "F", "G", "A", "B", "C"],
                "key": "C major",
                "melody": False,
            },
            {
                "id": "TC2-dorian-outside-Bb",
                "notes": ["D", "E", "F", "G", "A", "B", "C"],
                "key": "Bb major",
                "melody": False,
            },
            {
                "id": "TC3-ionian-C",
                "notes": ["C", "D", "E", "F", "G", "A", "B"],
                "key": "C major",
                "melody": False,
            },
            {
                "id": "TC4-aeolian-in-C",
                "notes": ["A", "B", "C", "D", "E", "F", "G"],
                "key": "C major",
                "melody": False,
            },
            {
                "id": "TC5-mixolydian-in-G",
                "notes": ["D", "E", "F#", "G", "A", "B", "C"],
                "key": "G major",
                "melody": False,
            },
            {
                "id": "TC6-c-mixolydian-borrowed",
                "notes": ["C", "D", "E", "F", "G", "A", "Bb"],
                "key": "C major",
                "melody": False,
            },
            {
                "id": "TC7-d-aeolian-in-F",
                "notes": ["D", "E", "F", "G", "A", "Bb", "C"],
                "key": "F major",
                "melody": False,
            },
            {
                "id": "TC8-e-phrygian-in-C",
                "notes": ["E", "F", "G", "A", "B", "C", "D"],
                "key": "C major",
                "melody": False,
            },
            {
                "id": "TC9-melody-tonic-guess-d-dorian",
                "notes": ["E", "F", "G", "A", "B", "C", "D", "A", "C", "D"],
                "key": None,
                "melody": True,
            },
            {
                "id": "TC10-c-lydian-borrowed",
                "notes": ["C", "D", "E", "F#", "G", "A", "B"],
                "key": "C major",
                "melody": False,
            },
        ]

        fixtures: List[Dict[str, Any]] = []
        for s in seeds:
            parents = self._parent_scales_of(s["notes"])
            diatonic = (
                None
                if not s.get("key")
                else self._is_diatonic_pitch_set(s["notes"], s["key"])
            )
            non_diatonic = (
                []
                if diatonic in (True, None)
                else self._non_diatonic_pitches(s["notes"], s["key"])
            )
            modal_labels = self._modal_labels_for(s["notes"])
            classification = self._classify_scale_usage(
                s["notes"], s.get("key"), diatonic
            )
            suggested_tonic, conf = (None, None)
            if s.get("melody"):
                suggested_tonic, conf = self._infer_tonic_from_melody(s["notes"])

            fixtures.append(
                {
                    "id": s["id"],
                    "input": {
                        "notes": s["notes"],
                        "key": s.get("key"),
                        "melody": bool(s.get("melody", False)),
                    },
                    "expected": {
                        "parent_scales": parents,
                        "diatonic_in_key": diatonic,
                        "non_diatonic_pitches": non_diatonic,
                        "modal_labels": modal_labels,
                        "classification": classification,
                        **(
                            {"suggested_tonic": suggested_tonic, "confidence": conf}
                            if s.get("melody")
                            else {}
                        ),
                        "rationale": self._scale_rationale(
                            s["notes"],
                            s.get("key"),
                            classification,
                            modal_labels,
                            parents,
                            non_diatonic,
                            suggested_tonic,
                        ),
                    },
                }
            )
        return fixtures

    def get_mode_family_scale_fixtures(self) -> List[Dict[str, Any]]:
        """
        Programmatically derive fixtures for every mode in each scale family from ALL_MODE_FAMILIES.
        For the Major family, include the parent major key context (e.g., D Dorian uses C major as context).
        For synthetic families (melodic minor, harmonic minor/major, double harmonic, pentatonic, blues),
        keep key=None to avoid mislabeling as diatonic-to-major/minor in our simplified checks.
        """
        fixtures: List[Dict[str, Any]] = []
        for family in ALL_MODE_FAMILIES:
            for tonic in self.default_tonics:
                for mode in family["modes"]:
                    intervals = mode["intervals"]
                    notes = self._build_scale_from_intervals(tonic, intervals)

                    key_ctx: Optional[str] = None
                    if family["name"] == "Major Scale":
                        # Parent is mode-tonic transposed DOWN by the major degree interval of that mode.
                        # Use the offsets you already expose in self.modal_parent_keys.
                        mode_root_name = mode["name"].split()[0]
                        if mode_root_name in self.modal_parent_keys:
                            offset = self.modal_parent_keys[mode_root_name]["offset"]
                        else:
                            offset = 0
                        parent_root = self.get_chord_at_interval(tonic, offset)
                        key_ctx = f"{parent_root} major"

                    fixtures.append(
                        {
                            "id": f"FAM:{family['tableId']}:{tonic}:{mode['degree']}:{mode['name']}",
                            "input": {"notes": notes, "key": key_ctx, "melody": False},
                            "expected": {},
                            "meta": {
                                "family": family["name"],
                                "mode": mode["name"],
                                "degree": mode["degree"],
                                "tonic": tonic,
                                "formula": mode.get("formula", ""),
                            },
                        }
                    )
        return fixtures

    def get_mode_family_melody_fixtures(self) -> List[Dict[str, Any]]:
        """Like get_mode_family_scale_fixtures, but generates short melodic phrases
        that start and end on the tonic and highlight each family's color tones.
        We set melody=True so tonic inference and contour description are exercised."""
        fixtures: List[Dict[str, Any]] = []
        for family in ALL_MODE_FAMILIES:
            for tonic in self.default_tonics:
                for mode in family["modes"]:
                    intervals = mode["intervals"]
                    notes = self._build_mode_phrase(
                        tonic, intervals, family["name"]
                    )  # melodic phrase

                    key_ctx: Optional[str] = None
                    if family["name"] == "Major Scale":
                        name = mode["name"].split()[0]
                        offset = self.modal_parent_keys.get(name, {}).get("offset", 0)
                        parent_root = self.get_chord_at_interval(tonic, offset)
                        key_ctx = f"{parent_root} major"

                    fixtures.append(
                        {
                            "id": f"FAM_MELODY:{family['tableId']}:{tonic}:{mode['degree']}:{mode['name']}",
                            "input": {
                                "notes": notes,
                                "key": key_ctx,
                                "melody": True,
                            },
                            "expected": {},
                            "meta": {
                                "family": family["name"],
                                "mode": mode["name"],
                                "degree": mode["degree"],
                                "tonic": tonic,
                                "formula": mode.get("formula", ""),
                            },
                        }
                    )
        return fixtures

    def create_scale_melody_test(self, fixture: Dict[str, Any]) -> MultiLayerTestCase:
        """Create a MultiLayerTestCase populated with scale/melody expectations only."""
        placeholders = self.minimal_expectations_for_nonharmonic()
        input_part = fixture["input"]
        expected_part = fixture["expected"]

        scale_exp = ScaleMelodyExpectation(
            notes=input_part["notes"],
            key=input_part.get("key"),
            melody=bool(input_part.get("melody", False)),
            parent_scales=expected_part["parent_scales"],
            diatonic_in_key=expected_part.get("diatonic_in_key"),
            non_diatonic_pitches=expected_part.get("non_diatonic_pitches", []),
            modal_labels=expected_part.get("modal_labels", {}),
            classification=expected_part["classification"],
            suggested_tonic=expected_part.get("suggested_tonic"),
            confidence=expected_part.get("confidence"),
            rationale=expected_part.get("rationale"),
        )

        return MultiLayerTestCase(
            id=fixture["id"],
            description=f'Scale/Melody: {fixture["id"]} - {" ".join(input_part["notes"])}',
            chords=[],  # No chord progression; scale/melody context only
            parent_key=input_part.get("key"),
            category="scale_melody",
            theoretical_basis="Scale/Melody enhanced expectations",
            expected_functional=placeholders["functional"],
            expected_modal=placeholders["modal"],
            expected_chromatic=placeholders["chromatic"],
            expected_ui=placeholders["ui"],
            validation=ValidationCriteria(
                acceptable_confidence_variance=0.15,
                requires_all_analyses=False,
                minimum_displayed_analyses=0,
                allowed_primary_interpretations=["undetermined"],
                critical_thresholds=self.thresholds.copy(),
            ),
            expected_scale_melody=scale_exp,
        )

    def generate_scale_and_melody_tests(self):
        """Generate enhanced tests for scales and melodies (pitch collections + tonic inference)."""
        print("  🎼 Generating scale & melody fixtures with enhanced expectations...")
        # 1) Existing procedural seeds (kept for regression coverage)
        for fixture in self.get_scale_melody_fixtures():
            self.test_cases.append(self.create_scale_melody_test(fixture))

        # 2) Comprehensive family/mode coverage for every mode in each type
        print("  🔬 Generating family/mode coverage for all modes in each type...")
        for raw in self.get_mode_family_scale_fixtures():
            input_part = raw["input"]
            parents = self._parent_scales_of(
                input_part["notes"]
            )  # major/minor parents only
            diatonic = (
                None
                if not input_part.get("key")
                else self._is_diatonic_pitch_set(input_part["notes"], input_part["key"])
            )
            non_diatonic = (
                []
                if diatonic in (True, None)
                else self._non_diatonic_pitches(input_part["notes"], input_part["key"])
            )
            modal_labels = self._modal_labels_for(input_part["notes"])
            classification = self._classify_scale_usage(
                input_part["notes"], input_part.get("key"), diatonic
            )

            raw["expected"] = {
                "parent_scales": parents,
                "diatonic_in_key": diatonic,
                "non_diatonic_pitches": non_diatonic,
                "modal_labels": modal_labels,
                "classification": classification,
                "rationale": self._scale_rationale(
                    input_part["notes"],
                    input_part.get("key"),
                    classification,
                    modal_labels,
                    parents,
                    non_diatonic,
                    None,
                ),
            }

            self.test_cases.append(self.create_scale_melody_test(raw))

        # 3) Melody variants for each family/mode (compact phrases)
        print("  🎵 Generating family/mode MELODY fixtures…")
        melody_fixtures = self.get_mode_family_melody_fixtures()
        for raw in melody_fixtures:
            input_part = raw["input"]
            parents = self._parent_scales_of(
                input_part["notes"]
            )  # major/minor parents only
            diatonic = (
                None
                if not input_part.get("key")
                else self._is_diatonic_pitch_set(input_part["notes"], input_part["key"])
            )
            non_diatonic = (
                []
                if diatonic in (True, None)
                else self._non_diatonic_pitches(input_part["notes"], input_part["key"])
            )
            modal_labels = self._modal_labels_for(
                input_part["notes"]
            )  # modal candidates over major parents
            classification = self._classify_scale_usage(
                input_part["notes"], input_part.get("key"), diatonic
            )

            raw["expected"] = {
                "parent_scales": parents,
                "diatonic_in_key": diatonic,
                "non_diatonic_pitches": non_diatonic,
                "modal_labels": modal_labels,
                "classification": classification,
                "rationale": self._scale_rationale(
                    input_part["notes"],
                    input_part.get("key"),
                    classification,
                    modal_labels,
                    parents,
                    non_diatonic,
                    None,
                ),
            }

            self.test_cases.append(self.create_scale_melody_test(raw))

    def _parent_scales_of(self, notes: List[str]) -> List[str]:
        """Return ALL parent scales that contain all given notes: major, natural minor, harmonic minor, melodic minor."""
        if not notes:
            return []

        # Convert notes to pitch classes for comparison
        note_pcs = set()
        for note in notes:
            pc = self._pc(note)
            if pc is None:
                return []  # Invalid note
            note_pcs.add(pc)

        result = []
        all_roots = ["C", "G", "D", "A", "E", "B", "F#", "Db", "Ab", "Eb", "Bb", "F"]

        for root in all_roots:
            root_pc = self._pc(root)
            if root_pc is None:
                continue

            # Test Major Scale (Ionian)
            major_intervals = [0, 2, 4, 5, 7, 9, 11]
            major_pcs = {(root_pc + iv) % 12 for iv in major_intervals}
            if note_pcs.issubset(major_pcs):
                result.append(f"{root} major")

            # Test Natural Minor (Aeolian) - same as relative major but different root
            natural_minor_intervals = [0, 2, 3, 5, 7, 8, 10]
            natural_minor_pcs = {(root_pc + iv) % 12 for iv in natural_minor_intervals}
            if note_pcs.issubset(natural_minor_pcs):
                result.append(f"{root} minor")

            # Test Harmonic Minor - THE KEY ADDITION!
            harmonic_minor_intervals = [0, 2, 3, 5, 7, 8, 11]
            harmonic_minor_pcs = {
                (root_pc + iv) % 12 for iv in harmonic_minor_intervals
            }
            if note_pcs.issubset(harmonic_minor_pcs):
                result.append(f"{root} harmonic minor")

            # Test Melodic Minor (ascending form)
            melodic_minor_intervals = [0, 2, 3, 5, 7, 9, 11]
            melodic_minor_pcs = {(root_pc + iv) % 12 for iv in melodic_minor_intervals}
            if note_pcs.issubset(melodic_minor_pcs):
                result.append(f"{root} melodic minor")

        return sorted(set(result))

    def _enh_norm(self, n: str) -> str:
        """Very small helper to normalize enharmonics to sharps/flats we know about."""
        r = self._extract_root(n)
        return r

    def _is_diatonic_pitch_set(self, notes: List[str], key: str) -> bool:
        """Check if all notes belong to the given key's major/minor pitch collection (simplified)."""
        if not key:
            return False
        root = key.split()[0]
        is_minor = "minor" in key
        if root not in self.note_map:
            return False
        pcs = {self.note_map[root]}
        if is_minor:
            # natural minor: 0,2,3,5,7,8,10
            for iv in [2, 3, 5, 7, 8, 10]:
                pcs.add((self.note_map[root] + iv) % 12)
        else:
            for iv in [2, 4, 5, 7, 9, 11]:
                pcs.add((self.note_map[root] + iv) % 12)
        for n in notes:
            pc = self.note_map.get(self._extract_root(n))
            if pc is None or pc not in pcs:
                return False
        return True

    def _non_diatonic_pitches(self, notes: List[str], key: str) -> List[str]:
        """Return list of notes that are not in the given key (simple pitch-class check)."""
        nd = []
        for n in notes:
            if not self._is_diatonic_pitch_set([n], key):
                nd.append(self._extract_root(n))
        # keep original spelling order as provided
        return [x for x in notes if self._extract_root(x) in nd]

    def _modal_labels_for(self, notes: List[str]) -> Dict[str, str]:
        """Return possible modal labels for candidate tonics within the parent major scales (Ionian/Aeolian/Dorian/Phrygian/Lydian/Mixolydian/Locrian)."""
        labels: Dict[str, str] = {}
        parents = self._parent_scales_of(notes)
        for p in parents:
            # Only process major scales for modal analysis
            if not p.endswith(" major"):
                continue
            p_root = p.split()[0]
            # build major scale degrees for parent
            degs = [(self.note_map[p_root] + iv) % 12 for iv in [0, 2, 4, 5, 7, 9, 11]]
            degree_roots = []
            for pc in degs:
                # choose a canonical spelling that exists in note_map keys (prefer naturals/flats)
                candidate = next(
                    (
                        k
                        for k, v in self.note_map.items()
                        if v == pc and len(k) <= 2 and not k.endswith("#")
                    ),
                    None,
                )
                if candidate is None:
                    candidate = next(
                        (k for k, v in self.note_map.items() if v == pc), None
                    )
                degree_roots.append(candidate)
            modes = [
                "Ionian",
                "Dorian",
                "Phrygian",
                "Lydian",
                "Mixolydian",
                "Aeolian",
                "Locrian",
            ]
            for idx, tonic in enumerate(degree_roots):
                if tonic is None:
                    continue
                labels.setdefault(tonic, f"{tonic} {modes[idx]}")
        # filter to labels whose tonic actually appears in the input notes
        input_roots = {self._extract_root(n) for n in notes}
        return {k: v for k, v in labels.items() if k in input_roots}

    def _classify_scale_usage(
        self, notes: List[str], key: Optional[str], diatonic: Optional[bool]
    ) -> str:
        """Decide diatonic/modal_borrowing/modal_candidate based on key and contents."""
        if key is None:
            return "modal_candidate"
        return "diatonic" if diatonic else "modal_borrowing"

    def _infer_tonic_from_melody(self, sequence: List[str]) -> (str, float):
        """Simple tonic guess: prefer final note; tie-break by frequency and A–C–D cadence hint for D Dorian case used in seeds."""
        if not sequence:
            return ("C", 0.5)
        last = self._extract_root(sequence[-1])
        counts: Dict[str, int] = {}
        for n in sequence:
            r = self._extract_root(n)
            counts[r] = counts.get(r, 0) + 1
        # heuristic bonus for the last note and presence of A–C–D
        conf = 0.6 + 0.02 * counts.get(last, 1)
        acd = {"A", "C", "D"}.issubset({self._extract_root(n) for n in sequence})
        if acd and last == "D":
            conf = max(conf, 0.78)
        return (last, min(conf, 0.95))

    def _scale_rationale(
        self,
        notes: List[str],
        key: Optional[str],
        classification: str,
        modal_labels: Dict[str, str],
        parents: List[str],
        non_diatonic: List[str],
        suggested: Optional[str],
    ) -> str:
        bits = []
        if parents:
            bits.append(f"Parents: {', '.join(parents)}")
        if key:
            bits.append(
                f"Key: {key} -> {'diatonic' if classification == 'diatonic' else 'non-diatonic'}"
            )
        if non_diatonic:
            bits.append(f"Non-diatonic: {', '.join(non_diatonic)}")
        if suggested:
            bits.append(f"Suggested tonic: {suggested}")
        if modal_labels:
            labs = ", ".join(sorted(modal_labels.values()))
            bits.append(f"Modal candidates: {labs}")
        return (
            "; ".join(bits)
            if bits
            else "Procedurally generated scale/melody expectation"
        )

    def _extract_root(self, n: str) -> str:
        """Extract the root note from a note string, e.g. F#3 -> F#."""
        if not n:
            return ""
        if len(n) > 1 and n[1] in "#b":
            return n[:2]
        return n[0]

    def get_modal_progressions(self, root: str, mode: str) -> List[Dict[str, Any]]:
        """Get characteristic progressions for a mode"""
        progressions = []

        if mode == "Mixolydian":
            progressions.extend(
                [
                    {
                        "chords": [
                            root,
                            self.get_chord_at_interval(root, 10),
                            self.get_chord_at_interval(root, 5),
                            root,
                        ],
                        "explanation": "I-bVII-IV-I Mixolydian",
                    },
                    {
                        "chords": [root, self.get_chord_at_interval(root, 10), root],
                        "explanation": "I-bVII-I Mixolydian cadence",
                    },
                ]
            )
        elif mode == "Dorian":
            progressions.extend(
                [
                    {
                        "chords": [
                            f"{root}m",
                            self.get_chord_at_interval(root, 5),
                            self.get_chord_at_interval(root, 10),
                            f"{root}m",
                        ],
                        "explanation": "i-IV-bVII-i Dorian",
                    },
                    {
                        "chords": [
                            f"{root}m",
                            self.get_chord_at_interval(root, 5),
                            f"{root}m",
                        ],
                        "explanation": "i-IV-i Dorian characteristic",
                    },
                ]
            )
        elif mode == "Phrygian":
            progressions.extend(
                [
                    {
                        "chords": [
                            f"{root}m",
                            self.get_chord_at_interval(root, 1),
                            f"{root}m",
                        ],
                        "explanation": "i-bII-i Phrygian cadence",
                    },
                    {
                        "chords": [
                            f"{root}m",
                            self.get_chord_at_interval(root, 1),
                            self.get_chord_at_interval(root, 10),
                            f"{root}m",
                        ],
                        "explanation": "i-bII-bVII-i Phrygian",
                    },
                ]
            )
        # Add more modes as needed
        else:
            # Default Ionian-style progressions
            progressions.extend(
                [
                    {
                        "chords": [root, self.get_chord_at_interval(root, 5), root],
                        "explanation": f"I-IV-I {mode}",
                    },
                    {
                        "chords": [root, self.get_chord_at_interval(root, 7), root],
                        "explanation": f"I-V-I {mode}",
                    },
                ]
            )

        return progressions

    def get_functional_progressions(
        self, root: str, is_major: bool
    ) -> List[Dict[str, Any]]:
        """Get functional progressions"""
        progressions = []

        if is_major:
            progressions.extend(
                [
                    {
                        "name": "I-IV-V-I",
                        "chords": [
                            root,
                            self.get_chord_at_interval(root, 5),
                            self.get_chord_at_interval(root, 7),
                            root,
                        ],
                        "explanation": "Classic I-IV-V-I cadence",
                    },
                    {
                        "name": "ii-V-I",
                        "chords": [
                            self.get_chord_at_interval(root, 2) + "m",
                            self.get_chord_at_interval(root, 7),
                            root,
                        ],
                        "explanation": "ii-V-I jazz cadence",
                    },
                    {
                        "name": "I-vi-IV-V",
                        "chords": [
                            root,
                            self.get_chord_at_interval(root, 9) + "m",
                            self.get_chord_at_interval(root, 5),
                            self.get_chord_at_interval(root, 7),
                        ],
                        "explanation": "I-vi-IV-V progression",
                    },
                ]
            )
        else:
            progressions.extend(
                [
                    {
                        "name": "i-iv-V-i",
                        "chords": [
                            root + "m",
                            self.get_chord_at_interval(root, 5) + "m",
                            self.get_chord_at_interval(root, 7),
                            root + "m",
                        ],
                        "explanation": "Minor i-iv-V-i",
                    },
                    {
                        "name": "i-VI-VII-i",
                        "chords": [
                            root + "m",
                            self.get_chord_at_interval(root, 8),
                            self.get_chord_at_interval(root, 10),
                            root + "m",
                        ],
                        "explanation": "Natural minor progression",
                    },
                ]
            )

        return progressions

    def get_chord_at_interval(self, root: str, semitones: int) -> str:
        """Get chord at specified interval from root"""
        root_value = self.note_map.get(root)
        if root_value is None:
            return root

        target_value = (root_value + semitones) % 12
        notes = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
        return notes[target_value]

    def get_parent_key(self, root: str, mode: str) -> str:
        """Get parent key for a given modal root and mode"""
        mode_info = self.modal_parent_keys.get(mode)
        if not mode_info:
            return f"{root} major"

        parent_root = self.get_chord_at_interval(root, mode_info["offset"])
        return f'{parent_root} {mode_info["mode"]}'

    def get_parent_key_for_mode(self, mode_name: str) -> str:
        """Get parent key for mode name like 'C Mixolydian'"""
        if not mode_name or " " not in mode_name:
            return "C major"

        root, mode = mode_name.split(" ", 1)
        return self.get_parent_key(root, mode)

    def _pc(self, name: str) -> Optional[int]:
        """Pitch-class from note name using self.note_map; returns None if unknown."""
        return self.note_map.get(self._extract_root(name))

    def _transpose_by_semitones(self, root: str, semitones: int) -> str:
        """Return note name transposed by semitones using a flat-friendly spelling set."""
        base = self._pc(root)
        if base is None:
            return root
        target = (base + semitones) % 12
        notes = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
        return notes[target]

    def _build_scale_from_intervals(
        self, tonic: str, intervals: List[int]
    ) -> List[str]:
        """Construct a pitch collection from semitone intervals relative to tonic."""
        if self._pc(tonic) is None:
            return [tonic]
        return [self._transpose_by_semitones(tonic, iv) for iv in intervals]

    def _characteristic_steps(
        self, family_name: str, intervals: List[int]
    ) -> List[int]:
        """Return offsets (in semitones) to emphasize a family's color tones.
        We use minimal heuristics: Lydian ♯4, Dorian ♮6, Phrygian ♭2, Mixolydian ♭7, etc.
        For non-heptatonic (pentatonic/blues), emphasize blue note / anhemitonic gaps.
        """
        # Map family highlights by detection of scale degrees present
        ivs = set(intervals)
        accents: List[int] = []
        if 6 in ivs:  # ♯4 in semitones relative to tonic
            accents.append(6)
        if 1 in ivs:  # ♭2
            accents.append(1)
        if 10 in ivs:  # ♭7
            accents.append(10)
        if 8 in ivs:  # ♭6
            accents.append(8)
        if 3 in ivs:  # ♭3 / ♯2 (contextual)
            accents.append(3)
        if family_name == "Blues Scale" and 6 in ivs:  # ♭5
            accents.append(6)
        # De-duplicate while preserving order
        seen = set()
        out: List[int] = []
        for a in accents:
            if a not in seen:
                out.append(a)
                seen.add(a)
        return out[:2]  # keep it short

    def _build_mode_phrase(
        self, tonic: str, intervals: List[int], family_name: str
    ) -> List[str]:
        """Create a short melodic phrase (~10 notes) in the given mode.
        Pattern: tonic → stepwise ascent → characteristic leap → descent → tonic.
        Notes are spelled with the same flat-friendly map as other helpers."""
        scale = self._build_scale_from_intervals(tonic, intervals)
        if not scale:
            return [tonic]

        # Stepwise ascent through the first 4–5 degrees (wrap if needed)
        ascent = []
        for i in range(min(5, len(scale))):
            ascent.append(scale[i % len(scale)])

        # Insert 1–2 characteristic tones by semitone transposition from tonic
        accents = self._characteristic_steps(family_name, intervals)
        accent_notes = [self._transpose_by_semitones(tonic, a) for a in accents]

        # Gentle descent touching scale degrees back to tonic
        descent = []
        for i in range(3, -1, -1):
            descent.append(scale[i % len(scale)])

        phrase = [tonic] + ascent + accent_notes + descent + [tonic]
        # Deduplicate immediate repeats, keep musical feel simple
        compact: List[str] = []
        for n in phrase:
            if not compact or compact[-1] != n:
                compact.append(n)
        return compact[:12]

    def infer_key_from_progression(self, chords: List[str]) -> Optional[str]:
        """Simple key inference - use first chord as basis"""
        if not chords:
            return None

        first_chord = chords[0]
        if "m" in first_chord and "maj" not in first_chord:
            return first_chord.replace("m", "").replace(r"[^A-G#b]", "") + " minor"
        return first_chord.split("m")[0].split("7")[0] + " major"

    def detect_cadences(
        self, chords: List[str], key_center: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Detect cadences in progression"""
        cadences = []

        for i in range(len(chords) - 1):
            current = chords[i]
            next_chord = chords[i + 1]

            # V-I authentic cadence (simplified)
            if "7" in current and "maj7" not in current:
                cadences.append(
                    {
                        "type": "authentic",
                        "chords": [current, next_chord],
                        "strength": "strong",
                    }
                )

        return cadences

    def classify_progression_type(
        self, chords: List[str], key_center: Optional[str]
    ) -> str:
        """Classify progression type"""
        progression = "-".join(chords)

        if "ii" in progression and "V" in progression and "I" in progression:
            return "ii-V-I"
        if "I" in progression and "V" in progression and "vi" in progression:
            return "circle-of-fifths"
        return "other"

    def generate_roman_numerals(
        self, chords: List[str], key_center: Optional[str]
    ) -> List[str]:
        """Generate Roman numerals for chords"""
        # Simplified Roman numeral generation
        return [self.chord_to_roman_numeral(chord, key_center) for chord in chords]

    def chord_to_roman_numeral(self, chord: str, key_center: Optional[str]) -> str:
        """
        Convert chord to Roman numeral based on actual chord root and key center.

        This is the fixed implementation that properly analyzes chord roots
        instead of the broken original that returned "I" for all major chords.
        """
        if not key_center:
            return "?"

        # Parse chord root (handle enharmonics)
        chord_root = chord[0]
        if len(chord) > 1 and chord[1] in ["#", "b"]:
            chord_root = chord[:2]

        # Parse key center root
        key_root = key_center.split()[0]
        if len(key_root) > 1 and key_root[1] in ["#", "b"]:
            key_root = key_root[:2]

        # Convert to pitch classes for interval calculation
        NOTE_TO_PITCH = {
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

        chord_pitch = NOTE_TO_PITCH.get(chord_root, 0)
        key_pitch = NOTE_TO_PITCH.get(key_root, 0)

        # Calculate scale degree (0-11)
        scale_degree = (chord_pitch - key_pitch) % 12

        # Determine if key is minor
        is_minor = "minor" in key_center.lower()

        # Generate Roman numeral based on scale degree and chord quality
        if is_minor:
            degree_map = {
                0: "i",
                2: "ii°",
                3: "bIII",
                5: "iv",
                7: "v",
                8: "bVI",
                10: "bVII",
            }
            base_numeral = degree_map.get(scale_degree, "?")

            # Handle major chords in minor keys (borrowed from parallel major)
            if "m" not in chord and base_numeral in ["i", "iv", "v"]:
                base_numeral = base_numeral.upper()

        else:
            degree_map = {
                0: "I",
                2: "ii",
                4: "iii",
                5: "IV",
                7: "V",
                9: "vi",
                11: "vii°",
            }
            base_numeral = degree_map.get(scale_degree, "?")

            # Handle minor chords in major keys
            if "m" in chord and base_numeral in ["I", "IV", "V"]:
                base_numeral = base_numeral.lower()

        # Add chord extensions
        if "7" in chord and "maj7" not in chord:
            if base_numeral == "V":
                return "V7"  # Dominant 7th
            else:
                return base_numeral + "7"
        elif "dim" in chord or "°" in chord:
            return base_numeral + "°" if "°" not in base_numeral else base_numeral

        return base_numeral

    def analyze_chord_functions(
        self, chords: List[str], key_center: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Analyze chord functions"""
        return [
            {
                "chord": chord,
                "function": self.get_chord_function(chord, key_center),
                "stability": self.get_chord_stability(chord, key_center),
            }
            for chord in chords
        ]

    def get_chord_function(self, chord: str, key_center: Optional[str]) -> str:
        """Get chord function (simplified)"""
        if "7" in chord and "maj7" not in chord:
            return "dominant"
        if "m" in chord:
            return "predominant"
        return "tonic"

    def get_chord_stability(self, chord: str, key_center: Optional[str]) -> str:
        """Get chord stability"""
        if "7" in chord and "maj7" not in chord:
            return "unstable"
        if "m" in chord:
            return "moderate"
        return "stable"

    def detect_modal_characteristics(self, chords: List[str]) -> Dict[str, Any]:
        """Detect modal characteristics"""
        result = {
            "detected": False,
            "mode": None,
            "tonic": None,
            "characteristics": [],
            "evidence": [],
        }

        # Check for modal patterns (simplified)
        # Mixolydian detection
        if self.contains_bVII_pattern(chords):
            result["detected"] = True
            result["mode"] = f"{self.infer_tonic(chords)} Mixolydian"
            result["tonic"] = self.infer_tonic(chords)
            result["characteristics"].append("bVII-I cadence")
            result["evidence"].append("Contains bVII chord (modal characteristic)")

        return result

    def contains_bVII_pattern(self, chords: List[str]) -> bool:
        """Check if progression contains bVII→I cadence (Mixolydian hallmark)"""
        if not chords:
            return False
        tonic = self._extract_root(self.infer_tonic(chords))
        tonic_pc = self.note_map.get(tonic)
        if tonic_pc is None:
            return False
        bvii_pc = (tonic_pc + 10) % 12  # b7 above tonic

        def root_pc(ch: str) -> Optional[int]:
            r = self._extract_root(ch)
            return self.note_map.get(r)

        # adjacent cadence
        for i in range(len(chords) - 1):
            a, b = root_pc(chords[i]), root_pc(chords[i + 1])
            if a is None or b is None:
                continue
            if a == bvii_pc and b == tonic_pc:
                return True
        # non-adjacent weak presence
        roots = {root_pc(c) for c in chords if root_pc(c) is not None}
        return (bvii_pc in roots) and (tonic_pc in roots)

    def infer_tonic(self, chords: List[str]) -> str:
        """Infer tonic from chord progression"""
        if not chords:
            return "C"
        return self._extract_root(chords[0])

    def minimal_expectations_for_nonharmonic(self) -> Dict[str, Any]:
        """Provide minimal placeholder expectations for functional/modal/chromatic layers when testing scales/melodies."""
        functional = FunctionalExpectation(
            detected=False,
            key_center=None,
            mode="major",
            roman_numerals=[],
            confidence=0.05,
            threshold=self.thresholds["functional"],
            cadences=[],
            progression_type="other",
            chord_functions=[],
        )
        modal = ModalExpectation(
            detected=False,
            mode=None,
            confidence=0.05,
            threshold=self.thresholds["modal"],
            evidence=[],
            parent_key_relationship=None,
            tonic_center=None,
            modal_characteristics=[],
        )
        chromatic = ChromaticExpectation(
            detected=False,
            confidence=0.05,
            threshold=self.thresholds["chromatic"],
            secondary_dominants=[],
            borrowed_chords=[],
            chromatic_mediants=[],
            alterations=[],
        )
        ui = self.determine_ui_behavior(functional, modal, chromatic)
        return {
            "functional": functional,
            "modal": modal,
            "chromatic": chromatic,
            "ui": ui,
        }

    def detect_secondary_dominants(
        self, chords: List[str], parent_key: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Detect secondary dominants"""
        secondaries = []

        for i in range(len(chords) - 1):
            if "7" in chords[i] and "maj7" not in chords[i]:
                secondaries.append(
                    {
                        "chord": chords[i],
                        "target": chords[i + 1],
                        "roman_numeral": (
                            "V7/"
                            + self.chord_to_roman_numeral(chords[i + 1], parent_key)
                        ),
                        "function": "tonicization",
                    }
                )

        return secondaries

    def detect_borrowed_chords(
        self, chords: List[str], parent_key: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Detect borrowed chords"""
        borrowed = []

        if parent_key and "major" in parent_key:
            for chord in chords:
                if "b" in chord or (
                    "m" in chord and not self.is_diatonic(chord, parent_key)
                ):
                    borrowed.append(
                        {
                            "chord": chord,
                            "source": "parallel minor",
                            "function": "modal interchange",
                            "roman_numeral": "bVII",  # Simplified
                        }
                    )

        return borrowed

    def detect_chromatic_mediants(self, chords: List[str]) -> List[Dict[str, Any]]:
        """Detect chromatic mediants"""
        mediants = []
        for i in range(len(chords) - 1):
            interval = self.get_interval_between(chords[i], chords[i + 1])
            if interval in [3, 4, 8, 9]:  # Third (±3/±4) or sixth (±8/±9) relationships
                if interval == 3:
                    rel = "minor third"
                elif interval == 4:
                    rel = "major third"
                elif interval == 8:
                    rel = "minor sixth"
                else:
                    rel = "major sixth"
                mediants.append(
                    {
                        "from": chords[i],
                        "to": chords[i + 1],
                        "relationship": rel,
                        "function": "chromatic mediant",
                    }
                )
        return mediants

    def detect_alterations(self, chords: List[str]) -> List[Dict[str, Any]]:
        """Detect alterations"""
        return [
            {
                "chord": chord,
                "alteration": "chromatic",
                "function": "chromatic alteration",
            }
            for chord in chords
            if "#" in chord or "b" in chord or "alt" in chord
        ]

    def is_diatonic(self, chord: str, key: Optional[str]) -> bool:
        """Check if chord is diatonic to key (simplified)"""
        return "#" not in chord and "b" not in chord

    def get_interval_between(self, chord1: str, chord2: str) -> int:
        """Get interval between chord roots in semitones"""
        a = self._extract_root(chord1)
        b = self._extract_root(chord2)
        if a not in self.note_map or b not in self.note_map:
            return 0
        return (self.note_map[b] - self.note_map[a]) % 12

    def export_results(self):
        """📊 EXPORT RESULTS"""
        print("\n🚀 EXPORTING REVOLUTIONARY MULTI-LAYER TESTS!")

        output_dir = os.path.join(os.path.dirname(__file__), "..", "tests", "generated")
        os.makedirs(output_dir, exist_ok=True)

        # JSON Export
        json_path = os.path.join(output_dir, "comprehensive-multi-layer-tests.json")
        json_content = {
            "metadata": {
                "generated": datetime.now().isoformat(),
                "total_cases": len(self.test_cases),
                "thresholds": self.thresholds,
                "version": "multi-layer-v2.0-python",
                "description": (
                    "Revolutionary multi-layer test cases with comprehensive "
                    "analysis expectations"
                ),
                "categories": self.get_category_breakdown(),
                "confidence_distribution": self.get_confidence_distribution(),
            },
            "test_cases": [asdict(test_case) for test_case in self.test_cases],
        }

        with open(json_path, "w") as f:
            json.dump(json_content, f, indent=2)

        # CSV Export
        self.export_to_csv(output_dir)

        print(
            f"✅ Generated {len(self.test_cases)} REVOLUTIONARY multi-layer test cases!"
        )
        print(f"💾 JSON: {json_path}")
        print(f"📊 CSV: {output_dir}/comprehensive-multi-layer-tests.csv")

    def export_to_csv(self, output_dir: str):
        """Export to CSV"""
        csv_path = os.path.join(output_dir, "comprehensive-multi-layer-tests.csv")

        headers = [
            "ID",
            "Description",
            "Chords",
            "Parent Key",
            "Category",
            "Func_Conf",
            "Func_Detected",
            "Func_Key",
            "Func_Romans",
            "Modal_Conf",
            "Modal_Detected",
            "Modal_Mode",
            "Modal_Evidence",
            "Chrom_Conf",
            "Chrom_Detected",
            "Chrom_Elements",
            "UI_Primary",
            "UI_Alternatives",
            "UI_Displayed",
            "Pedagogical_Level",
            "Theoretical_Basis",
            "SM_Notes",
            "SM_Key",
            "SM_Classification",
            "SM_Parents",
            "SM_DiatonicInKey",
            "SM_SuggestedTonic",
            "SM_Confidence",
            "SM_Family",
            "SM_Mode",
            "SM_Degree",
        ]

        with open(csv_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)

            for test in self.test_cases:
                writer.writerow(
                    [
                        test.id,
                        test.description,
                        " ".join(test.chords),
                        test.parent_key or "none",
                        test.category,
                        f"{test.expected_functional.confidence:.3f}",
                        test.expected_functional.detected,
                        test.expected_functional.key_center or "none",
                        "-".join(test.expected_functional.roman_numerals) or "none",
                        f"{test.expected_modal.confidence:.3f}",
                        test.expected_modal.detected,
                        test.expected_modal.mode or "none",
                        ";".join(test.expected_modal.evidence) or "none",
                        f"{test.expected_chromatic.confidence:.3f}",
                        test.expected_chromatic.detected,
                        len(test.expected_chromatic.secondary_dominants)
                        + len(test.expected_chromatic.borrowed_chords),
                        test.expected_ui.primary_interpretation,
                        ";".join(test.expected_ui.alternative_interpretations),
                        ";".join(test.expected_ui.displayed_analyses),
                        test.expected_ui.recommended_pedagogical_level,
                        test.theoretical_basis,
                        # Scale/melody fields
                        (
                            " ".join(test.expected_scale_melody.notes)
                            if test.expected_scale_melody
                            else "none"
                        ),
                        (
                            test.expected_scale_melody.key
                            if test.expected_scale_melody
                            else "none"
                        ),
                        (
                            test.expected_scale_melody.classification
                            if test.expected_scale_melody
                            else "none"
                        ),
                        (
                            ";".join(test.expected_scale_melody.parent_scales)
                            if test.expected_scale_melody
                            else "none"
                        ),
                        (
                            str(test.expected_scale_melody.diatonic_in_key)
                            if test.expected_scale_melody
                            else "none"
                        ),
                        (
                            test.expected_scale_melody.suggested_tonic
                            if test.expected_scale_melody
                            else "none"
                        ),
                        (
                            f"{test.expected_scale_melody.confidence:.3f}"
                            if test.expected_scale_melody
                            and test.expected_scale_melody.confidence
                            else "none"
                        ),
                        # SM_Family
                        (
                            test.id.split(":")[1]
                            if test.category == "scale_melody"
                            and test.id.startswith("FAM:")
                            and ":" in test.id
                            else "none"
                        ),
                        # SM_Mode
                        (
                            test.id.split(":")[4]
                            if test.category == "scale_melody"
                            and test.id.startswith("FAM:")
                            and len(test.id.split(":")) > 4
                            else "none"
                        ),
                        # SM_Degree
                        (
                            test.id.split(":")[3]
                            if test.category == "scale_melody"
                            and test.id.startswith("FAM:")
                            and len(test.id.split(":")) > 3
                            else "none"
                        ),
                    ]
                )

    def get_category_breakdown(self) -> Dict[str, int]:
        """Get category breakdown"""
        categories = {}
        for test in self.test_cases:
            categories[test.category] = categories.get(test.category, 0) + 1
        return categories

    def get_confidence_distribution(self) -> Dict[str, Dict[str, int]]:
        """Get confidence distribution"""
        distribution = {
            "functional": {"high": 0, "medium": 0, "low": 0},
            "modal": {"high": 0, "medium": 0, "low": 0},
            "chromatic": {"high": 0, "medium": 0, "low": 0},
        }

        for test in self.test_cases:
            for analysis_type in ["functional", "modal", "chromatic"]:
                confidence = getattr(test, f"expected_{analysis_type}").confidence
                if confidence >= 0.7:
                    distribution[analysis_type]["high"] += 1
                elif confidence >= 0.4:
                    distribution[analysis_type]["medium"] += 1
                else:
                    distribution[analysis_type]["low"] += 1

        return distribution

    def generate_statistics(self):
        """Generate statistics"""
        print("\n📊 REVOLUTIONARY TEST STATISTICS:")
        print(f"🎯 Total Tests: {len(self.test_cases)}")

        categories = self.get_category_breakdown()
        print("\n📋 By Category:")
        for cat, count in categories.items():
            print(f"  {cat}: {count} tests")

        distribution = self.get_confidence_distribution()
        print("\n🎚️ Confidence Distribution:")
        for analysis_type in ["functional", "modal", "chromatic"]:
            dist = distribution[analysis_type]
            print(
                (
                    f'  {analysis_type}: High({dist["high"]}) '
                    f'Medium({dist["medium"]}) Low({dist["low"]})'
                )
            )

        # Family/Mode coverage summary (scale/melody tests)
        fam_counts: Dict[str, int] = {}
        for t in self.test_cases:
            if t.category == "scale_melody" and t.id.startswith("FAM:"):
                family_key = t.id.split(":")[1]
                fam_counts[family_key] = fam_counts.get(family_key, 0) + 1
        if fam_counts:
            print("\n🧭 Family/Mode Coverage:")
            for fam, cnt in sorted(fam_counts.items()):
                print(f"  {fam}: {cnt} fixtures")

        # Melody family/mode coverage summary
        mel_counts: Dict[str, int] = {}
        for t in self.test_cases:
            if t.category == "scale_melody" and t.id.startswith("FAM_MELODY:"):
                family_key = t.id.split(":")[1]
                mel_counts[family_key] = mel_counts.get(family_key, 0) + 1
        if mel_counts:
            print("\n🎶 Melody Family/Mode Coverage:")
            for fam, cnt in sorted(mel_counts.items()):
                print(f"  {fam}: {cnt} fixtures")

        print("\n🎉 MULTI-LAYER TEST REVOLUTION COMPLETE!")
        print("💪 Ready to validate the sophisticated analysis system!")


def main():
    """🚀 LAUNCH THE REVOLUTION!"""
    generator = ComprehensiveMultiLayerGenerator()
    test_cases = generator.generate_all_tests()

    print("\n🎊 COMPREHENSIVE MULTI-LAYER TEST GENERATION COMPLETE!")
    print(f"📈 Generated {len(test_cases)} revolutionary test cases")
    print("🎯 All test cases include functional, modal, and chromatic expectations")
    print("🎚️ Confidence thresholds: functional(0.4), modal(0.6), chromatic(0.5)")
    print("🖥️ UI behavior expectations included for comprehensive validation")

    return test_cases


if __name__ == "__main__":
    main()
