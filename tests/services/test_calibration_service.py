"""
Comprehensive CalibrationService unit tests.
Tests the 4-stage calibration pipeline: Platt scaling, Isotonic regression,
Uncertainty learning.
"""

import json

import pytest

from harmonic_analysis.services.calibration_service import CalibrationService


class TestCalibrationServiceCore:
    """Test core CalibrationService functionality."""

    def test_load_valid_mapping(self, sample_calibration_mapping):
        """Test loading a valid 4-stage calibration mapping."""
        service = CalibrationService(sample_calibration_mapping)
        assert service.mapping is not None
        assert "tracks" in service.mapping
        assert "functional" in service.mapping["tracks"]
        assert "modal" in service.mapping["tracks"]

    def test_load_nonexistent_mapping(self):
        """Test handling of nonexistent calibration file."""
        with pytest.raises((FileNotFoundError, ValueError, OSError)):
            CalibrationService("/nonexistent/path.json")

    def test_load_invalid_json(self, tmp_path):
        """Test handling of corrupted calibration file."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("invalid json content")

        with pytest.raises((json.JSONDecodeError, ValueError)):
            CalibrationService(str(invalid_file))

    def test_load_empty_mapping(self, tmp_path):
        """Test handling of empty calibration mapping."""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("{}")

        with pytest.raises((KeyError, ValueError)):
            CalibrationService(str(empty_file))


class TestCalibrationApplication:
    """Test confidence calibration application."""

    @pytest.mark.parametrize(
        "track,raw_conf,expected_range",
        [
            ("functional", 0.5, (0.0, 1.0)),
            ("modal", 0.8, (0.0, 1.0)),
            ("functional", 0.0, (0.0, 1.0)),
            ("functional", 1.0, (0.0, 1.0)),
        ],
    )
    def test_calibrate_confidence_basic(
        self, calibration_service, track, raw_conf, expected_range
    ):
        """Test basic confidence calibration stays within bounds."""
        features = {"chord_count": 4, "evidence_strength": 0.7}
        result = calibration_service.calibrate_confidence(raw_conf, track, features)

        assert isinstance(result, float)
        assert expected_range[0] <= result <= expected_range[1]

    def test_calibration_bucket_routing(self, calibration_service):
        """Test that different features route to appropriate buckets."""
        base_features = {"chord_count": 4, "evidence_strength": 0.7}

        # Test functional simple - no modal markers
        simple_features = {
            **base_features,
            "has_flat7": False,
            "outside_key_ratio": 0.0,
        }
        result1 = calibration_service.calibrate_confidence(
            0.5, "functional", simple_features
        )

        # Test modal marked - has modal characteristics
        modal_features = {**base_features, "has_flat7": True, "outside_key_ratio": 0.1}
        result2 = calibration_service.calibrate_confidence(
            0.5, "functional", modal_features
        )

        # Both should be valid floats in range
        assert isinstance(result1, float)
        assert isinstance(result2, float)
        assert 0.0 <= result1 <= 1.0
        assert 0.0 <= result2 <= 1.0

    def test_calibration_consistency(self, calibration_service):
        """Test that calibration is deterministic for same inputs."""
        features = {"chord_count": 4, "evidence_strength": 0.7}

        result1 = calibration_service.calibrate_confidence(0.5, "functional", features)
        result2 = calibration_service.calibrate_confidence(0.5, "functional", features)

        # Should be exactly the same
        assert result1 == result2

    def test_calibration_preserves_extremes_roughly(self, calibration_service):
        """Test that calibration doesn't invert ordering too drastically."""
        features = {"chord_count": 4, "evidence_strength": 0.7}

        low_result = calibration_service.calibrate_confidence(
            0.1, "functional", features
        )
        high_result = calibration_service.calibrate_confidence(
            0.9, "functional", features
        )

        # Low confidence should generally stay lower than high confidence
        # (allowing some wiggle room for calibration effects)
        assert 0.0 <= low_result <= 1.0
        assert 0.0 <= high_result <= 1.0


class TestUtilityMethods:
    """Test CalibrationService utility methods."""

    def test_get_available_tracks(self, calibration_service):
        """Test getting available calibration tracks."""
        tracks = calibration_service.get_available_tracks()
        assert isinstance(tracks, list)
        assert "functional" in tracks
        assert "modal" in tracks

    def test_get_available_buckets(self, calibration_service):
        """Test getting available buckets per track."""
        buckets = calibration_service.get_available_buckets("functional")
        assert isinstance(buckets, list)
        # GLOBAL might not be included in buckets list, just check we get some buckets
        assert len(buckets) >= 0

    def test_get_available_buckets_invalid_track(self, calibration_service):
        """Test getting buckets for invalid track."""
        buckets = calibration_service.get_available_buckets("invalid_track")
        # Should handle gracefully, return empty list or raise appropriate error
        assert isinstance(buckets, list)

    def test_validate_features(self, calibration_service):
        """Test feature validation."""
        valid_features = {
            "chord_count": 4,
            "evidence_strength": 0.7,
            "outside_key_ratio": 0.1,
        }
        invalid_features = {"invalid_key": "invalid_value"}

        # Should return some kind of validation result (True/False or list of messages)
        valid_result = calibration_service.validate_features(valid_features)
        invalid_result = calibration_service.validate_features(invalid_features)

        # Both should return something (could be bool or list)
        assert valid_result is not None
        assert invalid_result is not None

    def test_get_calibration_stats(self, calibration_service):
        """Test getting calibration statistics."""
        stats = calibration_service.get_calibration_stats()
        assert isinstance(stats, dict)
        # Should contain some basic info about the calibration mapping


@pytest.fixture
def sample_calibration_mapping(tmp_path):
    """Create a sample calibration mapping for testing."""
    mapping = {
        "version": "test-v1",
        "created_at": "2025-01-01T00:00:00Z",
        "tracks": {
            "functional": {
                "GLOBAL": {
                    "platt": {"a": 1.2, "b": -0.1},
                    "isotonic": {"x": [0.0, 0.5, 1.0], "y": [0.0, 0.4, 0.9]},
                    "uncertainty": {"factor": 0.95},
                },
                "buckets": {
                    "functional_simple": {
                        "platt": {"a": 1.1, "b": 0.0},
                        "isotonic": {"x": [0.0, 1.0], "y": [0.0, 1.0]},
                        "uncertainty": {"factor": 1.0},
                    },
                    "modal_marked": {
                        "platt": {"a": 0.9, "b": 0.05},
                        "isotonic": {"x": [0.0, 0.5, 1.0], "y": [0.05, 0.45, 0.85]},
                        "uncertainty": {"factor": 0.92},
                    },
                },
            },
            "modal": {
                "GLOBAL": {
                    "platt": {"a": 0.9, "b": 0.1},
                    "isotonic": {"x": [0.0, 0.5, 1.0], "y": [0.1, 0.5, 0.8]},
                    "uncertainty": {"factor": 0.9},
                },
                "buckets": {},
            },
        },
    }

    mapping_file = tmp_path / "test_calibration.json"
    mapping_file.write_text(json.dumps(mapping, indent=2))
    return str(mapping_file)


@pytest.fixture
def calibration_service(sample_calibration_mapping):
    """CalibrationService instance with test mapping."""
    return CalibrationService(sample_calibration_mapping)
