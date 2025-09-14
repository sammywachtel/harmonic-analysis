"""
Test calibration performance and regression.

This module ensures our 4-stage calibration system maintains acceptable performance
characteristics and doesn't regress over time. Performance testing is critical
because calibration runs on every analysis request and must not become a bottleneck.

Performance Test Categories:
1. Load Time: CalibrationService initialization speed with mapping files
2. Single Calibration Speed: Individual calibrate_confidence() call performance
3. End-to-End Performance: Full analysis pipeline including calibration overhead
4. Memory Usage: Ensuring no memory leaks with repeated calibration calls
5. Regression Testing: Known-good calibration results remain stable over time
6. Scaling Tests: Performance with many simultaneous calibration requests

Performance Targets:
- CalibrationService load time: < 500ms (generous for CI environments)
- Single calibration call: < 2ms average (allows ~500 calibrations/second)
- End-to-end analysis with calibration: < 200ms average per progression
- Memory growth: < 100 objects after 1000+ calibration calls
- Regression tolerance: Results within expected ranges for known test cases

These tests help ensure calibration system remains production-ready as the
codebase evolves and calibration models become more sophisticated.
"""

import json
import os
import time

import pytest

from harmonic_analysis.services.calibration_service import CalibrationService
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService


class TestCalibrationPerformance:
    """Test calibration performance characteristics."""

    def test_calibration_service_load_time(self, sample_calibration_mapping):
        """Test CalibrationService loads within reasonable time.

        Validates initialization performance for production readiness:
        - Measures time from constructor call to ready service instance
        - Ensures mapping file parsing doesn't create startup delays
        - Target: < 500ms load time (generous for CI/container environments)
        - Validates loaded service has properly initialized mapping data

        This test catches performance regressions in mapping file parsing,
        JSON deserialization, or service initialization logic.
        """
        start_time = time.time()
        service = CalibrationService(sample_calibration_mapping)
        load_time = time.time() - start_time

        # Should load within 500ms (generous for CI environments)
        assert load_time < 0.5
        assert service.mapping is not None

    def test_single_calibration_performance(self, calibration_service):
        """Test individual calibration calls are fast.

        Measures calibration throughput for production load scenarios:
        - Runs 100 calibration calls to get statistically meaningful average
        - Includes warm-up call to avoid JIT/caching effects in timing
        - Target: < 2ms average per call (enables ~500 calibrations/second)
        - Tests with realistic feature sets and confidence values

        Critical test since every analysis request includes calibration call.
        Catches performance regressions in Platt scaling, isotonic regression,
        or uncertainty learning stages of the calibration pipeline.
        """
        features = {"chord_count": 4, "evidence_strength": 0.7}

        # Warm up
        calibration_service.calibrate_confidence(0.5, "functional", features)

        # Time multiple calibrations
        start_time = time.time()
        for _ in range(100):
            result = calibration_service.calibrate_confidence(
                0.5, "functional", features
            )
            assert isinstance(result, float)

        total_time = time.time() - start_time
        avg_time_ms = (total_time / 100) * 1000

        # Should average < 2ms per calibration (generous for CI)
        assert avg_time_ms < 2.0

    @pytest.mark.asyncio
    async def test_end_to_end_calibration_performance(self, sample_calibration_mapping):
        """Test end-to-end analysis with calibration performance."""
        calibration_service = CalibrationService(sample_calibration_mapping)
        service = PatternAnalysisService(
            calibration_service=calibration_service, auto_calibrate=True
        )

        # Time multiple analyses
        progressions = [
            ["C", "F", "G", "C"],
            ["Am", "F", "C", "G"],
            ["C", "Am", "F", "G"],
            ["C", "Bb", "F", "C"],  # Modal
            ["C", "F#dim", "G", "C"],  # Chromatic
        ]

        start_time = time.time()

        for progression in progressions:
            result = await service.analyze_with_patterns_async(progression)
            assert result.primary is not None

        total_time = time.time() - start_time
        avg_time_ms = (total_time / len(progressions)) * 1000

        # Should average < 200ms per progression including calibration (generous for CI)
        assert avg_time_ms < 200.0

    def test_calibration_memory_usage(self, calibration_service):
        """Test that calibration doesn't leak memory with repeated calls."""
        import gc

        features = {"chord_count": 4, "evidence_strength": 0.7}

        # Get baseline memory
        gc.collect()
        baseline_refs = len(gc.get_objects())

        # Make many calibration calls
        for _ in range(1000):
            result = calibration_service.calibrate_confidence(
                0.5, "functional", features
            )
            assert isinstance(result, float)

        # Check memory after operations
        gc.collect()
        final_refs = len(gc.get_objects())

        # Should not have significant memory growth (allow some variance)
        ref_growth = final_refs - baseline_refs
        assert ref_growth < 100  # Allow some object creation but not unbounded growth


class TestCalibrationRegression:
    """Test for calibration regressions."""

    # Known good calibrations - these serve as regression tests
    # Format: (raw_confidence, track, features, expected_min, expected_max)
    KNOWN_GOOD_CALIBRATIONS = [
        (0.5, "functional", {"chord_count": 4, "evidence_strength": 0.7}, 0.2, 0.8),
        (0.8, "functional", {"chord_count": 4, "evidence_strength": 0.9}, 0.4, 1.0),
        (0.2, "modal", {"chord_count": 4, "evidence_strength": 0.3}, 0.0, 0.6),
        (0.0, "functional", {"chord_count": 2, "evidence_strength": 0.1}, 0.0, 0.3),
        (1.0, "modal", {"chord_count": 6, "evidence_strength": 1.0}, 0.7, 1.0),
    ]

    @pytest.mark.parametrize(
        "raw_conf,track,features,min_expected,max_expected", KNOWN_GOOD_CALIBRATIONS
    )
    def test_calibration_regression(
        self, calibration_service, raw_conf, track, features, min_expected, max_expected
    ):
        """Test that calibration results stay within expected ranges."""
        result = calibration_service.calibrate_confidence(raw_conf, track, features)

        assert min_expected <= result <= max_expected, (
            f"Calibration regression detected: {raw_conf} -> {result} "
            f"(expected {min_expected}-{max_expected}) for {track} track with features {features}"
        )

    def test_calibration_stability_across_restarts(self, sample_calibration_mapping):
        """Test that calibration gives same results across service restarts."""
        features = {"chord_count": 4, "evidence_strength": 0.7}

        # First service instance
        service1 = CalibrationService(sample_calibration_mapping)
        result1 = service1.calibrate_confidence(0.5, "functional", features)

        # Second service instance (simulates restart)
        service2 = CalibrationService(sample_calibration_mapping)
        result2 = service2.calibrate_confidence(0.5, "functional", features)

        # Results should be identical
        assert result1 == result2

    def test_calibration_deterministic_across_calls(self, calibration_service):
        """Test that calibration is deterministic for repeated calls."""
        features = {"chord_count": 4, "evidence_strength": 0.7}

        results = []
        for _ in range(10):
            result = calibration_service.calibrate_confidence(
                0.5, "functional", features
            )
            results.append(result)

        # All results should be identical
        assert len(set(results)) == 1


class TestCalibrationScaling:
    """Test calibration system scaling characteristics."""

    def test_many_simultaneous_calibrations(self, calibration_service):
        """Test calibration with many different input combinations."""
        test_cases = []

        # Generate variety of test cases
        for conf in [0.1, 0.3, 0.5, 0.7, 0.9]:
            for track in ["functional", "modal"]:
                for chord_count in [2, 4, 6, 8]:
                    for evidence in [0.2, 0.5, 0.8]:
                        features = {
                            "chord_count": chord_count,
                            "evidence_strength": evidence,
                        }
                        test_cases.append((conf, track, features))

        # Time processing all cases
        start_time = time.time()

        for conf, track, features in test_cases:
            result = calibration_service.calibrate_confidence(conf, track, features)
            assert isinstance(result, float)
            assert 0.0 <= result <= 1.0

        total_time = time.time() - start_time
        avg_time_ms = (total_time / len(test_cases)) * 1000

        # Should process many cases quickly
        assert avg_time_ms < 1.0  # < 1ms average per case
        assert len(test_cases) > 50  # Ensure we actually tested many cases


@pytest.fixture
def sample_calibration_mapping():
    """Use the standard calibration mapping file for performance testing."""
    mapping_path = "src/harmonic_analysis/assets/calibration_mapping.json"
    if not os.path.exists(mapping_path):
        pytest.skip(f"Standard calibration mapping not found: {mapping_path}")
    return mapping_path


@pytest.fixture
def calibration_service(sample_calibration_mapping):
    """CalibrationService instance with test mapping for performance testing."""
    return CalibrationService(sample_calibration_mapping)
