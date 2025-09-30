"""
Tests for pattern loader validation against JSON schema.

Ensures pattern files conform to the unified DSL schema and provide
helpful error messages for common validation failures.
"""

import json

import pytest

from harmonic_analysis.core.pattern_engine.pattern_loader import PatternLoader


class TestPatternLoaderValidation:
    """Test pattern loader schema validation."""

    def test_valid_pattern_loads_successfully(self, tmp_path):
        """Test that valid pattern files load without errors."""
        valid_pattern = {
            "version": 1,
            "patterns": [
                {
                    "id": "cadence.authentic.simple",
                    "name": "Authentic Cadence (V-I)",
                    "scope": ["harmonic"],
                    "track": ["functional"],
                    "matchers": {
                        "roman_seq": ["V", "I"],
                        "transposition_invariant": True,
                    },
                    "evidence": {"weight": 0.9, "confidence_fn": "identity"},
                    "metadata": {"tags": ["cadence", "functional"], "priority": 80},
                }
            ],
        }

        pattern_file = tmp_path / "valid_patterns.json"
        pattern_file.write_text(json.dumps(valid_pattern))

        loader = PatternLoader()
        loaded = loader.load(pattern_file)

        assert loaded["version"] == 1
        assert len(loaded["patterns"]) == 1
        assert loaded["patterns"][0]["id"] == "cadence.authentic.simple"

    def test_missing_required_fields_raises_error(self, tmp_path):
        """Test that missing required fields cause validation failures."""
        invalid_pattern = {
            "version": 1,
            "patterns": [
                {
                    "id": "incomplete.pattern",
                    # Missing: name, scope, track, matchers, evidence
                }
            ],
        }

        pattern_file = tmp_path / "invalid_patterns.json"
        pattern_file.write_text(json.dumps(invalid_pattern))

        loader = PatternLoader()

        with pytest.raises(ValueError, match="Schema validation failed"):
            loader.load(pattern_file)

    def test_invalid_pattern_id_format_raises_error(self, tmp_path):
        """Test that invalid pattern ID format is rejected."""
        invalid_pattern = {
            "version": 1,
            "patterns": [
                {
                    "id": "invalid pattern id with spaces!",  # Invalid characters
                    "name": "Invalid Pattern",
                    "scope": ["harmonic"],
                    "track": ["functional"],
                    "matchers": {"roman_seq": ["I"]},
                    "evidence": {"weight": 0.5},
                }
            ],
        }

        pattern_file = tmp_path / "invalid_id.json"
        pattern_file.write_text(json.dumps(invalid_pattern))

        loader = PatternLoader()

        with pytest.raises(ValueError, match="Schema validation failed"):
            loader.load(pattern_file)

    def test_invalid_scope_enum_raises_error(self, tmp_path):
        """Test that invalid scope values are rejected."""
        invalid_pattern = {
            "version": 1,
            "patterns": [
                {
                    "id": "test.pattern",
                    "name": "Test Pattern",
                    "scope": ["invalid_scope"],  # Not in enum
                    "track": ["functional"],
                    "matchers": {"roman_seq": ["I"]},
                    "evidence": {"weight": 0.5},
                }
            ],
        }

        pattern_file = tmp_path / "invalid_scope.json"
        pattern_file.write_text(json.dumps(invalid_pattern))

        loader = PatternLoader()

        with pytest.raises(ValueError, match="Schema validation failed"):
            loader.load(pattern_file)

    def test_invalid_track_enum_raises_error(self, tmp_path):
        """Test that invalid track values are rejected."""
        invalid_pattern = {
            "version": 1,
            "patterns": [
                {
                    "id": "test.pattern",
                    "name": "Test Pattern",
                    "scope": ["harmonic"],
                    "track": ["invalid_track"],  # Not in enum
                    "matchers": {"roman_seq": ["I"]},
                    "evidence": {"weight": 0.5},
                }
            ],
        }

        pattern_file = tmp_path / "invalid_track.json"
        pattern_file.write_text(json.dumps(invalid_pattern))

        loader = PatternLoader()

        with pytest.raises(ValueError, match="Schema validation failed"):
            loader.load(pattern_file)

    def test_weight_out_of_range_raises_error(self, tmp_path):
        """Test that weight values outside [0,1] are rejected."""
        invalid_pattern = {
            "version": 1,
            "patterns": [
                {
                    "id": "test.pattern",
                    "name": "Test Pattern",
                    "scope": ["harmonic"],
                    "track": ["functional"],
                    "matchers": {"roman_seq": ["I"]},
                    "evidence": {"weight": 1.5},  # > 1.0
                }
            ],
        }

        pattern_file = tmp_path / "invalid_weight.json"
        pattern_file.write_text(json.dumps(invalid_pattern))

        loader = PatternLoader()

        with pytest.raises(ValueError, match="Schema validation failed"):
            loader.load(pattern_file)

    def test_multiple_patterns_load_correctly(self, tmp_path):
        """Test loading multiple valid patterns."""
        multi_pattern = {
            "version": 1,
            "patterns": [
                {
                    "id": "cadence.authentic",
                    "name": "Authentic Cadence",
                    "scope": ["harmonic"],
                    "track": ["functional"],
                    "matchers": {"roman_seq": ["V", "I"]},
                    "evidence": {"weight": 0.9},
                },
                {
                    "id": "modal.dorian.i_bVII",
                    "name": "Dorian i-♭VII",
                    "scope": ["harmonic"],
                    "track": ["modal"],
                    "matchers": {"roman_seq": ["i", "♭VII"]},
                    "evidence": {"weight": 0.7},
                },
            ],
        }

        pattern_file = tmp_path / "multi_patterns.json"
        pattern_file.write_text(json.dumps(multi_pattern))

        loader = PatternLoader()
        loaded = loader.load(pattern_file)

        assert len(loaded["patterns"]) == 2
        assert loaded["patterns"][0]["id"] == "cadence.authentic"
        assert loaded["patterns"][1]["id"] == "modal.dorian.i_bVII"

    def test_empty_patterns_array_is_valid(self, tmp_path):
        """Test that empty patterns array is valid."""
        empty_pattern = {"version": 1, "patterns": []}

        pattern_file = tmp_path / "empty_patterns.json"
        pattern_file.write_text(json.dumps(empty_pattern))

        loader = PatternLoader()
        loaded = loader.load(pattern_file)

        assert loaded["version"] == 1
        assert loaded["patterns"] == []

    def test_helpful_error_message_format(self, tmp_path):
        """Test that validation errors include helpful context."""
        invalid_pattern = {
            "version": "not_a_number",  # Should be integer
            "patterns": [],
        }

        pattern_file = tmp_path / "bad_version.json"
        pattern_file.write_text(json.dumps(invalid_pattern))

        loader = PatternLoader()

        with pytest.raises(ValueError) as exc_info:
            loader.load(pattern_file)

        error_message = str(exc_info.value)
        assert "Schema validation failed" in error_message
        # Note: We don't include filename in error message, just field path and helpful context

    def test_complex_pattern_with_all_fields(self, tmp_path):
        """Test loading a complex pattern with all optional fields."""
        complex_pattern = {
            "version": 1,
            "metadata": {"description": "Test patterns", "author": "Test Suite"},
            "patterns": [
                {
                    "id": "cadence.complex.test",
                    "name": "Complex Test Cadence",
                    "scope": ["harmonic", "melodic"],
                    "track": ["functional", "modal"],
                    "matchers": {
                        "roman_seq": ["ii", "V", "I"],
                        "chord_seq": ["Dm", "G", "C"],
                        "interval_seq": [2, -5],
                        "scale_degrees": [2, 5, 1],
                        "mode": "major",
                        "transposition_invariant": True,
                        "constraints": {
                            "soprano_degree": [1, 3, 5],
                            "bass_motion": "ascending",
                            "key_context": "diatonic",
                            "position": "end",
                        },
                        "window": {"len": 3, "overlap_ok": False, "min_gap": 1},
                    },
                    "evidence": {
                        "weight": 0.85,
                        "features": [
                            "outside_key_ratio",
                            "has_auth_cadence",
                            "voice_leading_smoothness",
                        ],
                        "confidence_fn": "logistic_default",
                        "uncertainty": 0.1,
                    },
                    "metadata": {
                        "tags": ["cadence", "complex", "test"],
                        "priority": 75,
                        "description": "A complex test pattern with all fields",
                        "examples": [
                            {
                                "chords": ["Dm", "G", "C"],
                                "key": "C major",
                                "description": "Basic ii-V-I in C major",
                            }
                        ],
                        "false_positives": ["Modal interchange cases"],
                        "references": ["Test Reference 2024"],
                    },
                }
            ],
        }

        pattern_file = tmp_path / "complex_pattern.json"
        pattern_file.write_text(json.dumps(complex_pattern))

        loader = PatternLoader()
        loaded = loader.load(pattern_file)

        assert loaded["version"] == 1
        assert len(loaded["patterns"]) == 1
        pattern = loaded["patterns"][0]
        assert pattern["id"] == "cadence.complex.test"
        assert len(pattern["scope"]) == 2
        assert len(pattern["track"]) == 2
        assert "constraints" in pattern["matchers"]
        assert "window" in pattern["matchers"]
        assert len(pattern["evidence"]["features"]) == 3
        assert "examples" in pattern["metadata"]
