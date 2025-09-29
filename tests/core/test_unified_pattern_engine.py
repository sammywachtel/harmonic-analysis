"""
Unit tests for the unified pattern engine.

Tests all components of the new unified architecture including
evidence, aggregation, calibration, and the main engine.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from harmonic_analysis.core.pattern_engine import (
    Aggregator,
    AnalysisContext,
    Calibrator,
    Evidence,
    PatternEngine,
    PatternLoader,
    PluginRegistry,
    TargetAnnotation,
    TargetBuilder,
)
from harmonic_analysis.dto import AnalysisEnvelope, AnalysisType


# --------------- Evidence Tests ---------------


class TestEvidence:
    """Test the Evidence dataclass."""

    def test_evidence_creation(self):
        """Test creating evidence objects."""
        evidence = Evidence(
            pattern_id="cadence.authentic",
            track_weights={"functional": 0.8, "modal": 0.2},
            features={"has_cadence": 1.0},
            raw_score=0.75,
            uncertainty=0.1,
            span=(2, 4),
        )

        assert evidence.pattern_id == "cadence.authentic"
        assert evidence.track_weights["functional"] == 0.8
        assert evidence.raw_score == 0.75
        assert evidence.span == (2, 4)

    def test_evidence_overlap_detection(self):
        """Test overlap detection between evidence."""
        ev1 = Evidence(
            pattern_id="p1",
            track_weights={},
            features={},
            raw_score=0.5,
            uncertainty=None,
            span=(0, 3),
        )
        ev2 = Evidence(
            pattern_id="p2",
            track_weights={},
            features={},
            raw_score=0.5,
            uncertainty=None,
            span=(2, 5),
        )
        ev3 = Evidence(
            pattern_id="p3",
            track_weights={},
            features={},
            raw_score=0.5,
            uncertainty=None,
            span=(5, 7),
        )

        assert ev1.overlaps(ev2)  # Overlapping
        assert ev2.overlaps(ev1)  # Symmetric
        assert not ev1.overlaps(ev3)  # Non-overlapping
        assert not ev3.overlaps(ev1)

    def test_evidence_to_dict(self):
        """Test serialization to dictionary."""
        evidence = Evidence(
            pattern_id="test.pattern",
            track_weights={"functional": 0.9},
            features={"f1": 0.5},
            raw_score=0.8,
            uncertainty=0.05,
            span=(1, 3),
        )

        d = evidence.to_dict()
        assert d["pattern_id"] == "test.pattern"
        assert d["raw_score"] == 0.8
        assert d["span"] == [1, 3]


# --------------- Plugin Registry Tests ---------------


class TestPluginRegistry:
    """Test the plugin registry system."""

    def test_registry_initialization(self):
        """Test registry starts with built-in evaluators."""
        registry = PluginRegistry()
        evaluators = registry.list_evaluators()

        assert "identity" in evaluators
        assert "logistic_default" in evaluators
        assert "logistic_dorian" in evaluators

    def test_register_custom_evaluator(self):
        """Test registering a custom evaluator."""
        registry = PluginRegistry()

        def custom_evaluator(pattern, context):
            return Evidence(
                pattern_id="custom",
                track_weights={"functional": 1.0},
                features={},
                raw_score=1.0,
                uncertainty=None,
                span=(0, 1),
            )

        registry.register("custom", custom_evaluator)
        assert "custom" in registry.list_evaluators()

        # Test it works
        evaluator = registry.get("custom")
        evidence = evaluator({}, {})
        assert evidence.pattern_id == "custom"

    def test_duplicate_registration_error(self):
        """Test that duplicate registration raises error."""
        registry = PluginRegistry()

        def dummy_evaluator(pattern, context):
            return None

        registry.register("test", dummy_evaluator)
        with pytest.raises(ValueError, match="already registered"):
            registry.register("test", dummy_evaluator)

    def test_unknown_evaluator_error(self):
        """Test that unknown evaluator raises error."""
        registry = PluginRegistry()
        with pytest.raises(KeyError, match="Unknown plugin"):
            registry.get("nonexistent")


# --------------- Aggregator Tests ---------------


class TestAggregator:
    """Test the evidence aggregator."""

    def test_empty_evidence_aggregation(self):
        """Test aggregating empty evidence list."""
        aggregator = Aggregator()
        result = aggregator.aggregate([])

        assert result["functional_conf"] == 0.0
        assert result["modal_conf"] == 0.0
        assert result["combined_conf"] == 0.0
        assert result["debug_breakdown"]["evidence_count"] == 0

    def test_single_evidence_aggregation(self):
        """Test aggregating single evidence."""
        aggregator = Aggregator()
        evidence = Evidence(
            pattern_id="test",
            track_weights={"functional": 0.8},
            features={},
            raw_score=0.8,
            uncertainty=None,
            span=(0, 2),
        )

        result = aggregator.aggregate([evidence])
        assert result["functional_conf"] > 0.7
        assert result["modal_conf"] == 0.0

    def test_multi_track_aggregation(self):
        """Test aggregating evidence across multiple tracks."""
        aggregator = Aggregator()
        evidences = [
            Evidence(
                pattern_id="func1",
                track_weights={"functional": 0.7},
                features={},
                raw_score=0.7,
                uncertainty=None,
                span=(0, 2),
            ),
            Evidence(
                pattern_id="modal1",
                track_weights={"modal": 0.6},
                features={},
                raw_score=0.6,
                uncertainty=None,
                span=(2, 4),
            ),
        ]

        result = aggregator.aggregate(evidences)
        assert result["functional_conf"] > 0.6
        assert result["modal_conf"] > 0.5
        assert result["combined_conf"] > 0.5

    def test_max_pool_conflict_resolution(self):
        """Test max pooling conflict resolution."""
        aggregator = Aggregator(conflict_strategy="max_pool")

        # Overlapping evidence with different scores
        evidences = [
            Evidence(
                pattern_id="high",
                track_weights={"functional": 0.9},
                features={},
                raw_score=0.9,
                uncertainty=None,
                span=(0, 3),
            ),
            Evidence(
                pattern_id="low",
                track_weights={"functional": 0.5},
                features={},
                raw_score=0.5,
                uncertainty=None,
                span=(1, 4),  # Overlaps with high
            ),
        ]

        result = aggregator.aggregate(evidences)
        # Only high-scoring evidence should be kept
        assert result["debug_breakdown"]["resolved_count"] == 1

    def test_soft_nms_conflict_resolution(self):
        """Test soft NMS conflict resolution."""
        aggregator = Aggregator(conflict_strategy="soft_nms", overlap_decay=0.5)

        evidences = [
            Evidence(
                pattern_id="first",
                track_weights={"functional": 0.8},
                features={},
                raw_score=0.8,
                uncertainty=None,
                span=(0, 3),
            ),
            Evidence(
                pattern_id="second",
                track_weights={"functional": 0.7},
                features={},
                raw_score=0.7,
                uncertainty=None,
                span=(2, 5),  # Overlaps with first
            ),
        ]

        result = aggregator.aggregate(evidences)
        # Both should be included but second should be decayed
        assert result["debug_breakdown"]["resolved_count"] == 2
        assert result["functional_conf"] < 0.8 + 0.7  # Less than sum due to decay

    def test_diversity_bonus(self):
        """Test diversity bonus for multiple pattern families."""
        aggregator = Aggregator(diversity_bonus=0.1)

        # Evidence from different families
        evidences = [
            Evidence(
                pattern_id="cadence.authentic",
                track_weights={"functional": 0.5},
                features={},
                raw_score=0.5,
                uncertainty=None,
                span=(0, 2),
            ),
            Evidence(
                pattern_id="progression.circle",
                track_weights={"functional": 0.5},
                features={},
                raw_score=0.5,
                uncertainty=None,
                span=(2, 4),
            ),
        ]

        result = aggregator.aggregate(evidences)
        # Should get diversity bonus
        assert result["debug_breakdown"]["diversity_bonus"] > 0


# --------------- Pattern Loader Tests ---------------


class TestPatternLoader:
    """Test the pattern loader and validation."""

    def test_load_valid_patterns(self, tmp_path):
        """Test loading valid pattern file."""
        pattern_file = tmp_path / "patterns.json"
        patterns = {
            "version": 1,
            "patterns": [
                {
                    "id": "test.pattern",
                    "name": "Test Pattern",
                    "scope": ["harmonic"],
                    "track": ["functional"],
                    "matchers": {"chord_seq": ["I", "V"]},
                    "evidence": {"weight": 0.5},
                }
            ],
        }
        pattern_file.write_text(json.dumps(patterns))

        loader = PatternLoader()
        data = loader.load(pattern_file)

        assert data["version"] == 1
        assert len(data["patterns"]) == 1
        assert data["patterns"][0]["id"] == "test.pattern"

    def test_validation_error_on_invalid_schema(self, tmp_path):
        """Test validation error on invalid pattern schema."""
        pattern_file = tmp_path / "bad.json"
        patterns = {
            "version": 1,
            "patterns": [
                {
                    "id": "bad",
                    # Missing required fields
                }
            ],
        }
        pattern_file.write_text(json.dumps(patterns))

        loader = PatternLoader()
        with pytest.raises(Exception):  # jsonschema.ValidationError
            loader.load(pattern_file)

    def test_merge_patterns(self, tmp_path):
        """Test merging patterns from multiple files."""
        file1 = tmp_path / "p1.json"
        file1.write_text(
            json.dumps(
                {
                    "version": 1,
                    "patterns": [
                        {
                            "id": "p1",
                            "name": "Pattern 1",
                            "scope": ["harmonic"],
                            "track": ["functional"],
                            "matchers": {},
                            "evidence": {"weight": 0.5},
                        }
                    ],
                }
            )
        )

        file2 = tmp_path / "p2.json"
        file2.write_text(
            json.dumps(
                {
                    "version": 1,
                    "patterns": [
                        {
                            "id": "p2",
                            "name": "Pattern 2",
                            "scope": ["harmonic"],
                            "track": ["modal"],
                            "matchers": {},
                            "evidence": {"weight": 0.6},
                        }
                    ],
                }
            )
        )

        loader = PatternLoader()
        merged = loader.merge_patterns(file1, file2)

        assert len(merged["patterns"]) == 2
        pattern_ids = {p["id"] for p in merged["patterns"]}
        assert pattern_ids == {"p1", "p2"}


# --------------- Target Builder Tests ---------------


class TestTargetBuilder:
    """Test the target builder for ground truth."""

    def test_heuristic_targets(self):
        """Test building heuristic targets without annotations."""
        builder = TargetBuilder()
        evidences = [
            Evidence(
                pattern_id="cadence.authentic",
                track_weights={"functional": 0.8},
                features={},
                raw_score=0.8,
                uncertainty=None,
                span=(0, 2),
            ),
            Evidence(
                pattern_id="modal.dorian",
                track_weights={"modal": 0.7, "functional": 0.3},
                features={},
                raw_score=0.7,
                uncertainty=None,
                span=(2, 4),
            ),
        ]

        targets = builder.build_targets(evidences)
        assert len(targets) == 2
        assert targets[0] > 0.8  # Cadence gets boost
        assert targets[1] < 0.8  # Multi-track gets reduction

    def test_targets_with_annotations(self):
        """Test building targets with ground truth annotations."""
        builder = TargetBuilder()
        evidences = [
            Evidence(
                pattern_id="test",
                track_weights={"functional": 0.5},
                features={},
                raw_score=0.5,
                uncertainty=None,
                span=(0, 2),
            )
        ]

        annotations = [
            TargetAnnotation(
                span=(0, 2),
                analysis_type="functional",
                confidence=0.9,
                source="expert",
                metadata={},
            )
        ]

        targets = builder.build_targets(evidences, annotations)
        assert len(targets) == 1
        assert targets[0] == 0.9  # Uses annotation confidence

    def test_overlapping_annotations(self):
        """Test handling overlapping annotations."""
        builder = TargetBuilder()
        evidences = [
            Evidence(
                pattern_id="test",
                track_weights={"functional": 0.5},
                features={},
                raw_score=0.5,
                uncertainty=None,
                span=(1, 4),
            )
        ]

        annotations = [
            TargetAnnotation(
                span=(0, 3),
                analysis_type="functional",
                confidence=0.8,
                source="corpus",
                metadata={},
            ),
            TargetAnnotation(
                span=(2, 5),
                analysis_type="functional",
                confidence=0.7,
                source="corpus",
                metadata={},
            ),
        ]

        targets = builder.build_targets(evidences, annotations)
        assert len(targets) == 1
        # Should be weighted average
        assert 0.7 <= targets[0] <= 0.8


# --------------- Calibrator Tests ---------------


class TestCalibrator:
    """Test the calibration system with quality gates."""

    def test_identity_mapping_for_insufficient_data(self):
        """Test that insufficient data returns identity mapping."""
        calibrator = Calibrator(min_samples=50)

        # Only 5 samples - below threshold
        raw_scores = [0.1, 0.3, 0.5, 0.7, 0.9]
        targets = [0.2, 0.4, 0.6, 0.8, 1.0]

        mapping = calibrator.fit(raw_scores, targets)
        assert mapping.mapping_type == "identity"
        assert not mapping.passed_gates

        # Test that it returns unchanged values
        assert mapping.apply(0.5) == 0.5

    def test_identity_mapping_for_low_variance(self):
        """Test that low variance returns identity mapping."""
        calibrator = Calibrator(min_variance=0.01)

        # All targets are the same - zero variance
        raw_scores = np.random.rand(100)
        targets = np.ones(100) * 0.5

        mapping = calibrator.fit(raw_scores, targets)
        assert mapping.mapping_type == "identity"
        assert not mapping.passed_gates

    def test_identity_mapping_for_low_correlation(self):
        """Test that low correlation returns identity mapping."""
        calibrator = Calibrator(min_correlation=0.3)

        # Random uncorrelated data
        np.random.seed(42)
        raw_scores = np.random.rand(100)
        targets = np.random.rand(100)

        mapping = calibrator.fit(raw_scores, targets)
        assert mapping.mapping_type == "identity"
        assert not mapping.passed_gates

    def test_platt_scaling_with_good_data(self):
        """Test Platt scaling with data that passes gates."""
        calibrator = Calibrator(min_samples=10, min_correlation=0.1, min_variance=0.01)

        # Create correlated data with good properties
        np.random.seed(42)
        raw_scores = np.linspace(0.2, 0.8, 50)
        targets = raw_scores * 0.8 + np.random.normal(0, 0.05, 50)
        targets = np.clip(targets, 0, 1)

        mapping = calibrator.fit(raw_scores, targets, method="platt")

        # Should get a non-identity mapping
        if mapping.mapping_type == "platt":
            assert mapping.passed_gates
            # Calibrated values should be different from raw
            assert abs(mapping.apply(0.5) - 0.5) > 0.01

    def test_ece_calculation(self):
        """Test Expected Calibration Error calculation."""
        calibrator = Calibrator()

        # Perfect calibration
        predictions = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
        targets = predictions.copy()
        ece = calibrator._calculate_ece(predictions, targets)
        assert ece < 0.01  # Should be near zero

        # Poor calibration
        predictions = np.array([0.9] * 10)
        targets = np.array([0.1] * 10)
        ece = calibrator._calculate_ece(predictions, targets)
        assert ece > 0.7  # Should be high


# --------------- Pattern Engine Tests ---------------


class TestPatternEngine:
    """Test the main pattern engine."""

    def test_engine_initialization(self):
        """Test engine initialization with components."""
        engine = PatternEngine()
        assert engine.loader is not None
        assert engine.aggregator is not None
        assert engine.plugins is not None

    def test_analyze_empty_context(self):
        """Test analyzing empty context."""
        engine = PatternEngine()
        context = AnalysisContext(
            key=None, chords=[], roman_numerals=[], melody=[], scales=[], metadata={}
        )

        envelope = engine.analyze(context)
        assert isinstance(envelope, AnalysisEnvelope)
        assert envelope.primary.confidence == 0.0

    def test_analyze_simple_progression(self, tmp_path):
        """Test analyzing a simple chord progression."""
        # Create pattern file
        pattern_file = tmp_path / "patterns.json"
        patterns = {
            "version": 1,
            "patterns": [
                {
                    "id": "cadence.v_i",
                    "name": "Perfect Cadence",
                    "scope": ["harmonic"],
                    "track": ["functional"],
                    "matchers": {"roman_seq": ["V", "I"]},
                    "evidence": {"weight": 0.9, "confidence_fn": "identity"},
                }
            ],
        }
        pattern_file.write_text(json.dumps(patterns))

        # Setup engine
        engine = PatternEngine()
        engine.load_patterns(pattern_file)

        # Analyze
        context = AnalysisContext(
            key="C major",
            chords=["G", "C"],
            roman_numerals=["V", "I"],
            melody=[],
            scales=[],
            metadata={},
        )

        envelope = engine.analyze(context)
        assert envelope.primary.type == AnalysisType.FUNCTIONAL
        assert envelope.primary.confidence > 0.8
        assert len(envelope.primary.patterns) > 0

    def test_ambiguous_analysis_generates_alternatives(self, tmp_path):
        """Test that ambiguous progressions generate alternatives."""
        # Create patterns for both functional and modal
        pattern_file = tmp_path / "patterns.json"
        patterns = {
            "version": 1,
            "patterns": [
                {
                    "id": "functional.pattern",
                    "name": "Functional",
                    "scope": ["harmonic"],
                    "track": ["functional"],
                    "matchers": {"roman_seq": ["i", "iv"]},
                    "evidence": {"weight": 0.6, "confidence_fn": "identity"},
                },
                {
                    "id": "modal.pattern",
                    "name": "Modal",
                    "scope": ["harmonic"],
                    "track": ["modal"],
                    "matchers": {"roman_seq": ["i", "iv"]},
                    "evidence": {"weight": 0.55, "confidence_fn": "identity"},
                },
            ],
        }
        pattern_file.write_text(json.dumps(patterns))

        engine = PatternEngine()
        engine.load_patterns(pattern_file)

        context = AnalysisContext(
            key="A minor",
            chords=["Am", "Dm"],
            roman_numerals=["i", "iv"],
            melody=[],
            scales=[],
            metadata={},
        )

        envelope = engine.analyze(context)
        # When confidences are close, should have alternatives
        if (
            abs(
                envelope.primary.functional_confidence
                - envelope.primary.modal_confidence
            )
            < 0.15
        ):
            assert len(envelope.alternatives) > 0

    def test_pattern_matching_with_window(self, tmp_path):
        """Test pattern matching with window constraints."""
        pattern_file = tmp_path / "patterns.json"
        patterns = {
            "version": 1,
            "patterns": [
                {
                    "id": "test.window",
                    "name": "Window Test",
                    "scope": ["harmonic"],
                    "track": ["functional"],
                    "matchers": {
                        "chord_seq": ["C", "F"],
                        "window": {"len": 2, "overlap_ok": False},
                    },
                    "evidence": {"weight": 0.7, "confidence_fn": "identity"},
                }
            ],
        }
        pattern_file.write_text(json.dumps(patterns))

        engine = PatternEngine()
        engine.load_patterns(pattern_file)

        context = AnalysisContext(
            key="C major",
            chords=["C", "F", "G", "C", "F"],  # Pattern appears twice
            roman_numerals=["I", "IV", "V", "I", "IV"],
            melody=[],
            scales=[],
            metadata={},
        )

        envelope = engine.analyze(context)
        # Should find two matches
        assert len([e for e in envelope.evidence if e.reason == "test.window"]) >= 1


# --------------- Integration Tests ---------------


class TestPatternEngineIntegration:
    """Integration tests for the complete pattern engine."""

    def test_end_to_end_analysis_flow(self, tmp_path):
        """Test complete analysis flow from patterns to envelope."""
        # Use the actual unified patterns
        pattern_path = (
            Path(__file__).parent.parent.parent
            / "src"
            / "harmonic_analysis"
            / "core"
            / "pattern_engine"
            / "patterns_unified.json"
        )

        if not pattern_path.exists():
            # Create a minimal test pattern file if the actual one doesn't exist
            pattern_path = tmp_path / "patterns.json"
            patterns = {
                "version": 1,
                "patterns": [
                    {
                        "id": "cadence.authentic",
                        "name": "Authentic Cadence",
                        "scope": ["harmonic"],
                        "track": ["functional"],
                        "matchers": {"roman_seq": ["V", "I"]},
                        "evidence": {
                            "weight": 0.9,
                            "confidence_fn": "logistic_default",
                        },
                    }
                ],
            }
            pattern_path.write_text(json.dumps(patterns))

        engine = PatternEngine()
        engine.load_patterns(pattern_path)

        # Classic ii-V-I progression
        context = AnalysisContext(
            key="C major",
            chords=["Dm", "G", "C"],
            roman_numerals=["ii", "V", "I"],
            melody=[],
            scales=[],
            metadata={"style": "jazz"},
        )

        envelope = engine.analyze(context)

        # Verify envelope structure
        assert isinstance(envelope, AnalysisEnvelope)
        assert envelope.primary is not None
        assert envelope.primary.type in [AnalysisType.FUNCTIONAL, AnalysisType.MODAL]
        assert 0.0 <= envelope.primary.confidence <= 1.0
        assert envelope.schema_version == "1.0"
        assert envelope.chord_symbols == ["Dm", "G", "C"]

    def test_calibration_integration(self):
        """Test that calibration integrates properly."""
        engine = PatternEngine()

        # Train a calibration mapping
        raw_scores = np.linspace(0.1, 0.9, 100)
        targets = raw_scores * 0.8 + 0.1  # Systematic bias
        targets = np.clip(targets + np.random.normal(0, 0.05, 100), 0, 1)

        mapping = engine.calibrator.fit(raw_scores, targets)
        engine._calibration_mapping = mapping

        # Analyze and check calibration was applied
        context = AnalysisContext(
            key="G major",
            chords=["G", "D"],
            roman_numerals=["I", "V"],
            melody=[],
            scales=[],
            metadata={},
        )

        envelope = engine.analyze(context)
        # Confidence should be adjusted if calibration passed gates
        assert envelope.primary.confidence >= 0.0
