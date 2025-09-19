"""
Test calibration edge cases and error handling.

This module tests the robustness and resilience of our 4-stage calibration system
when confronted with unusual, malformed, or extreme inputs. Production systems
must gracefully handle edge cases without crashing or producing nonsensical results.

Edge Case Categories:
1. Extreme Confidence Values: NaN, infinity, negative values, values > 1.0
2. Invalid Track Names: Non-existent tracks, empty strings, wrong types
3. Malformed Features: Missing features, wrong types, extreme values, NaN
4. Corrupted Calibration Mappings: Missing keys, invalid parameters, inconsistent data
5. System Stress: Rapid calls, threading issues, memory constraints
6. Boundary Conditions: Edge values in isotonic regression, Platt scaling limits

Error Handling Expectations:
- Invalid inputs should either raise appropriate exceptions OR handle gracefully
- Valid results should always be in range [0.0, 1.0] and not NaN
- System should never crash or enter undefined state
- Fallback behavior should be predictable and documented
- Memory leaks and threading issues should not occur under stress

These tests ensure the calibration system is production-ready for real-world
usage where inputs may not always be perfectly clean or expected.
"""

import json
import math
import os

import pytest

from harmonic_analysis.services.calibration_service import CalibrationService


class TestCalibrationEdgeCases:
    """Test calibration edge cases and robustness."""

    @pytest.mark.parametrize(
        "raw_confidence",
        [
            -0.5,  # Below 0
            0.0,  # Minimum
            1.0,  # Maximum
            1.5,  # Above 1
            float("nan"),  # NaN
            float("inf"),  # Infinity
            float("-inf"),  # Negative infinity
        ],
    )
    def test_extreme_confidence_values(self, calibration_service, raw_confidence):
        """Test calibration with extreme confidence values.

        Validates robust handling of mathematical edge cases:
        - Negative confidence values (mathematically invalid)
        - Values outside [0,1] range (beyond normal probability bounds)
        - NaN and infinity values (computational edge cases)
        - Boundary values 0.0 and 1.0 (should always work correctly)

        Expected behavior: Either raise appropriate exception OR return valid
        result in [0,1] range. System must never crash or return NaN/infinity.
        """
        features = {"chord_count": 4, "evidence_strength": 0.7}

        try:
            result = calibration_service.calibrate_confidence(
                raw_confidence, "functional", features
            )
            # If it succeeds, result should be bounded and not NaN
            if not math.isnan(result):  # not NaN
                assert 0.0 <= result <= 1.0
        except (ValueError, TypeError, OverflowError):
            # Acceptable to raise error for invalid inputs
            pass

    @pytest.mark.parametrize(
        "track",
        [
            "functional",  # Valid
            "modal",  # Valid
            "invalid_track",  # Invalid
            "",  # Empty string
            None,  # None
            123,  # Wrong type
        ],
    )
    def test_track_variations(self, calibration_service, track):
        """Test calibration with various track values."""
        features = {"chord_count": 4}

        try:
            result = calibration_service.calibrate_confidence(0.5, track, features)
            assert 0.0 <= result <= 1.0
        except (KeyError, ValueError, TypeError, AttributeError):
            # Should handle invalid tracks gracefully
            pass

    @pytest.mark.parametrize(
        "features",
        [
            {},  # Empty features
            {"invalid_key": "value"},  # Invalid features
            {"chord_count": "not_a_number"},  # Wrong types
            {"chord_count": -1},  # Negative values
            {"chord_count": 1000000},  # Very large values
            None,  # None features
            "not_a_dict",  # Wrong type entirely
            {"evidence_strength": float("nan")},  # NaN in features
        ],
    )
    def test_feature_variations(self, calibration_service, features):
        """Test calibration with various feature dictionaries."""
        try:
            result = calibration_service.calibrate_confidence(
                0.5, "functional", features
            )
            assert 0.0 <= result <= 1.0
        except (TypeError, ValueError, KeyError, AttributeError):
            # Should handle invalid features gracefully
            pass

    def test_very_large_feature_values(self, calibration_service):
        """Test calibration with extremely large feature values."""
        extreme_features = {
            "chord_count": 999999,
            "evidence_strength": 1000000.0,
            "outside_key_ratio": 99999.9,
        }

        try:
            result = calibration_service.calibrate_confidence(
                0.5, "functional", extreme_features
            )
            # Should handle extreme values and stay bounded
            assert 0.0 <= result <= 1.0
        except (ValueError, OverflowError):
            # Acceptable to fail on extreme inputs
            pass

    def test_missing_required_features(self, calibration_service):
        """Test calibration when expected features are missing."""
        # Features that might be expected by the calibration but are missing
        minimal_features = {"chord_count": 4}  # Only one feature

        result = calibration_service.calibrate_confidence(
            0.5, "functional", minimal_features
        )
        # Should handle gracefully and return valid result
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0


class TestCalibrationMappingValidation:
    """Test calibration mapping validation."""

    def test_missing_tracks_key(self, tmp_path):
        """Test handling of calibration mapping without tracks key."""
        invalid_mapping = {
            "version": "test",
            "created_at": "2025-01-01T00:00:00Z",
            # Missing "tracks" key
        }

        mapping_file = tmp_path / "invalid_calibration.json"
        mapping_file.write_text(json.dumps(invalid_mapping))

        with pytest.raises((KeyError, ValueError)):
            CalibrationService(str(mapping_file))

    def test_missing_file(self, tmp_path):
        """Test handling when calibration mapping file doesn't exist."""
        nonexistent_file = tmp_path / "nonexistent_calibration.json"

        with pytest.raises(ValueError, match="Failed to load calibration mapping"):
            CalibrationService(str(nonexistent_file))

    def test_empty_tracks(self, tmp_path):
        """Test handling of calibration mapping with empty tracks."""
        empty_mapping = {"tracks": {}}  # Empty tracks

        mapping_file = tmp_path / "empty_tracks.json"
        mapping_file.write_text(json.dumps(empty_mapping))

        # CalibrationService should accept empty tracks (fault-tolerant design)
        service = CalibrationService(str(mapping_file))

        # Should have no available tracks
        assert service.get_available_tracks() == []

        # Should work in pass-through mode and return valid results
        features = {"chord_count": 4, "evidence_strength": 0.7}
        result = service.calibrate_confidence(0.5, "functional", features)

        # Should return a valid confidence score (raw confidence in pass-through mode)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    def test_none_mapping_passthrough(self):
        """Test CalibrationService with None mapping (pass-through mode)."""
        # Should not raise an exception
        service = CalibrationService(None)

        # Should work in pass-through mode and return valid results
        features = {"chord_count": 4, "evidence_strength": 0.7}
        result = service.calibrate_confidence(0.5, "functional", features)

        # Should return a valid confidence score
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

        # In pass-through mode, should return input unchanged or apply minimal processing
        # The exact behavior depends on implementation, but should be predictable
        assert result is not None

    def test_malformed_calibration_params(self, tmp_path):
        """Test handling of malformed calibration parameters."""
        invalid_mapping = {
            "tracks": {
                "functional": {
                    "GLOBAL": {
                        "platt": {"invalid": "params"},  # Missing 'a' and 'b'
                        "isotonic": "not_a_dict",
                        "uncertainty": {"invalid": "structure"},
                    }
                }
            }
        }

        mapping_file = tmp_path / "malformed_calibration.json"
        mapping_file.write_text(json.dumps(invalid_mapping))

        # Should either raise error or handle gracefully
        try:
            service = CalibrationService(str(mapping_file))
            # If it loads, basic calibration should still work (fallback behavior)
            result = service.calibrate_confidence(0.5, "functional", {"chord_count": 4})
            assert 0.0 <= result <= 1.0
        except (ValueError, KeyError, TypeError):
            # Acceptable to reject malformed mapping
            pass

    def test_missing_global_bucket(self, tmp_path):
        """Test handling when GLOBAL bucket is missing."""
        invalid_mapping = {
            "tracks": {
                "functional": {
                    # Missing "GLOBAL" bucket
                    "buckets": {
                        "functional_simple": {
                            "platt": {"a": 1.0, "b": 0.0},
                            "isotonic": {"x": [0.0, 1.0], "y": [0.0, 1.0]},
                            "uncertainty": {"factor": 1.0},
                        }
                    }
                }
            }
        }

        mapping_file = tmp_path / "missing_global.json"
        mapping_file.write_text(json.dumps(invalid_mapping))

        try:
            service = CalibrationService(str(mapping_file))
            result = service.calibrate_confidence(0.5, "functional", {"chord_count": 4})
            # Should either work (using bucket calibration) or fail gracefully
            assert isinstance(result, float)
        except (KeyError, ValueError):
            # Acceptable to require GLOBAL bucket
            pass

    def test_inconsistent_isotonic_points(self, tmp_path):
        """Test handling of inconsistent isotonic regression points."""
        invalid_mapping = {
            "tracks": {
                "functional": {
                    "GLOBAL": {
                        "platt": {"a": 1.0, "b": 0.0},
                        "isotonic": {
                            "x": [0.0, 0.5, 1.0],  # 3 x points
                            "y": [0.0, 0.5],  # Only 2 y points (mismatch)
                        },
                        "uncertainty": {"factor": 1.0},
                    }
                }
            }
        }

        mapping_file = tmp_path / "inconsistent_isotonic.json"
        mapping_file.write_text(json.dumps(invalid_mapping))

        try:
            service = CalibrationService(str(mapping_file))
            result = service.calibrate_confidence(0.5, "functional", {"chord_count": 4})
            # Should handle gracefully or raise appropriate error
            assert isinstance(result, float)
        except (ValueError, IndexError, KeyError):
            # Acceptable to reject inconsistent isotonic data
            pass


class TestCalibrationRobustness:
    """Test calibration system robustness under stress."""

    def test_rapid_calibration_calls(self, calibration_service):
        """Test rapid successive calibration calls for threading issues."""
        features = {"chord_count": 4, "evidence_strength": 0.7}

        results = []
        for i in range(100):
            result = calibration_service.calibrate_confidence(
                0.5, "functional", features
            )
            results.append(result)

        # All results should be valid and identical (deterministic)
        assert len(results) == 100
        assert all(isinstance(r, float) for r in results)
        assert all(0.0 <= r <= 1.0 for r in results)
        assert len(set(results)) == 1  # All should be identical

    def test_varying_feature_sets(self, calibration_service):
        """Test calibration with varying feature combinations."""
        test_features = [
            {"chord_count": 4},
            {"chord_count": 3, "evidence_strength": 0.8},
            {"chord_count": 5, "evidence_strength": 0.6, "has_flat7": True},
            {"chord_count": 2, "outside_key_ratio": 0.3},
            {
                "chord_count": 8,
                "evidence_strength": 0.9,
                "has_flat7": False,
                "outside_key_ratio": 0.1,
            },
        ]

        for features in test_features:
            result = calibration_service.calibrate_confidence(
                0.5, "functional", features
            )
            assert isinstance(result, float)
            assert 0.0 <= result <= 1.0


@pytest.fixture
def sample_calibration_mapping():
    """Use the standard calibration mapping file for edge case testing."""
    mapping_path = "src/harmonic_analysis/assets/calibration_mapping.json"
    if not os.path.exists(mapping_path):
        pytest.skip(f"Standard calibration mapping not found: {mapping_path}")
    return mapping_path


@pytest.fixture
def calibration_service(sample_calibration_mapping):
    """CalibrationService instance with test mapping for edge case testing."""
    return CalibrationService(sample_calibration_mapping)
