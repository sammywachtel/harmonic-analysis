#!/usr/bin/env python3
"""
API Serialization Validation Tests

Validates that all DTO types serialize correctly through the API layer:
- StyleAnalysisDetail dataclass serialization
- Dict[str, StyleAnalysisDetail] nested serialization
- AnalysisSummary with multi-profile fields
- AnalysisEnvelope complete serialization
- JSON roundtrip consistency

Tests the serialization infrastructure without requiring HTTP layer.
"""

import json

import pytest

from harmonic_analysis.dto import (
    AnalysisEnvelope,
    AnalysisSummary,
    AnalysisType,
    PatternMatchDTO,
    StyleAnalysisDetail,
    serialize_dataclass,
)

# -----------------------------
# StyleAnalysisDetail Serialization Tests (AC-3, AC-6)
# -----------------------------


def test_style_analysis_detail_serialization():
    """
    Opening move: Verify StyleAnalysisDetail serializes to valid JSON.

    AC-6: Serialization test validates all new DTO types serialize correctly
    """
    detail = StyleAnalysisDetail(
        style_name="jazz",
        confidence=0.85,
        patterns=[
            PatternMatchDTO(
                start=0,
                end=2,
                pattern_id="ii-V-I",
                name="ii-V-I Jazz Cadence",
                family="cadence",
                score=0.9,
                style_tags=["jazz"],
                detected_via_profile="jazz",
            )
        ],
        roman_numerals=["ii7", "V7", "Imaj7"],
        key_signature="C major",
        reasoning="Strong jazz ii-V-I resolution with extended chords",
    )

    # Serialize using centralized serializer
    result = serialize_dataclass(detail)

    # Validate structure
    assert isinstance(result, dict), "Serialization should produce a dictionary"
    assert result["style_name"] == "jazz"
    assert result["confidence"] == 0.85
    assert isinstance(result["patterns"], list)
    assert len(result["patterns"]) == 1
    assert isinstance(result["roman_numerals"], list)
    assert result["key_signature"] == "C major"

    # Validate nested pattern serialization
    pattern = result["patterns"][0]
    assert pattern["pattern_id"] == "ii-V-I"
    assert pattern["score"] == 0.9
    assert isinstance(pattern["style_tags"], list)

    # Ensure JSON-serializable
    try:
        json_str = json.dumps(result)
        assert len(json_str) > 0
    except Exception as e:
        pytest.fail(f"StyleAnalysisDetail not JSON-serializable: {e}")


def test_style_analysis_detail_to_dict_method():
    """
    Main play: Verify StyleAnalysisDetail.to_dict() works correctly.

    AC-6: Serialization test validates all new DTO types serialize correctly
    """
    detail = StyleAnalysisDetail(
        style_name="classical",
        confidence=0.75,
        patterns=[],
        roman_numerals=["I", "IV", "V", "I"],
        key_signature="C major",
        reasoning="Traditional functional progression",
    )

    result = detail.to_dict()

    assert isinstance(result, dict)
    assert result["style_name"] == "classical"
    assert result["confidence"] == 0.75
    assert result["patterns"] == []
    assert result["roman_numerals"] == ["I", "IV", "V", "I"]


# -----------------------------
# Dict[str, StyleAnalysisDetail] Serialization Tests (AC-3, AC-6)
# -----------------------------


def test_dict_style_analysis_serialization():
    """
    Big play: Verify Dict[str, StyleAnalysisDetail] serializes correctly.

    AC-3: Dict[str, StyleAnalysisDetail] serializes correctly to nested JSON
    AC-6: Serialization test validates all new DTO types serialize correctly
    """
    style_analysis = {
        "jazz": StyleAnalysisDetail(
            style_name="jazz",
            confidence=0.92,
            patterns=[
                PatternMatchDTO(
                    start=0,
                    end=3,
                    pattern_id="ii-V-I",
                    name="ii-V-I",
                    family="cadence",
                    score=0.9,
                )
            ],
            roman_numerals=["ii7", "V7", "Imaj7"],
            key_signature="C major",
        ),
        "classical": StyleAnalysisDetail(
            style_name="classical",
            confidence=0.78,
            patterns=[],
            roman_numerals=["ii", "V", "I"],
            key_signature="C major",
        ),
        "pop": StyleAnalysisDetail(
            style_name="pop",
            confidence=0.65,
            patterns=[],
            roman_numerals=["ii", "V", "I"],
            key_signature="C major",
        ),
    }

    # Serialize the dict using centralized serializer
    # (simulating what happens in AnalysisSummary.to_dict())
    from harmonic_analysis.dto import _serialize_value

    result = _serialize_value(style_analysis)

    # Validate structure
    assert isinstance(result, dict), "Should be a dictionary"
    assert len(result) == 3, "Should have 3 profiles"
    assert "jazz" in result
    assert "classical" in result
    assert "pop" in result

    # Validate each nested StyleAnalysisDetail
    jazz_detail = result["jazz"]
    assert isinstance(jazz_detail, dict), "Nested detail should be dict"
    assert jazz_detail["style_name"] == "jazz"
    assert jazz_detail["confidence"] == 0.92
    assert isinstance(jazz_detail["patterns"], list)
    assert len(jazz_detail["patterns"]) == 1

    classical_detail = result["classical"]
    assert classical_detail["style_name"] == "classical"
    assert classical_detail["confidence"] == 0.78

    # Ensure JSON-serializable
    try:
        json_str = json.dumps(result)
        assert len(json_str) > 0
    except Exception as e:
        pytest.fail(f"Dict[str, StyleAnalysisDetail] not JSON-serializable: {e}")


def test_empty_style_analysis_dict_serialization():
    """
    Edge case: Verify empty style_analysis dict serializes correctly.

    AC-3: Dict[str, StyleAnalysisDetail] serializes correctly to nested JSON
    """
    from harmonic_analysis.dto import _serialize_value

    empty_dict = {}
    result = _serialize_value(empty_dict)

    assert isinstance(result, dict)
    assert len(result) == 0

    # Should be JSON-serializable
    json_str = json.dumps(result)
    assert json_str == "{}"


# -----------------------------
# AnalysisSummary Multi-Profile Serialization Tests (AC-2, AC-6)
# -----------------------------


def test_analysis_summary_with_style_fields_serialization():
    """
    Victory lap: Verify AnalysisSummary with multi-profile fields serializes.

    AC-2: Response includes style-aware fields (dominant_style, style_confidence, style_analysis)
    AC-6: Serialization test validates all new DTO types serialize correctly
    """
    summary = AnalysisSummary(
        type=AnalysisType.FUNCTIONAL,
        roman_numerals=["ii7", "V7", "Imaj7"],
        confidence=0.88,
        key_signature="C major",
        reasoning="Jazz progression with ii-V-I",
        # Multi-profile fields
        dominant_style="jazz",
        style_confidence={"jazz": 0.92, "classical": 0.75, "pop": 0.68},
        style_analysis={
            "jazz": StyleAnalysisDetail(
                style_name="jazz",
                confidence=0.92,
                patterns=[],
                roman_numerals=["ii7", "V7", "Imaj7"],
                key_signature="C major",
            ),
            "classical": StyleAnalysisDetail(
                style_name="classical",
                confidence=0.75,
                patterns=[],
                roman_numerals=["ii", "V", "I"],
                key_signature="C major",
            ),
        },
    )

    # Serialize using to_dict()
    result = summary.to_dict()

    # Validate core fields
    assert result["type"] == "functional"
    assert result["confidence"] == 0.88
    assert result["roman_numerals"] == ["ii7", "V7", "Imaj7"]

    # Validate multi-profile fields
    assert result["dominant_style"] == "jazz"
    assert isinstance(result["style_confidence"], dict)
    assert result["style_confidence"]["jazz"] == 0.92
    assert result["style_confidence"]["classical"] == 0.75

    # Validate style_analysis nested structure
    assert isinstance(result["style_analysis"], dict)
    assert "jazz" in result["style_analysis"]
    assert "classical" in result["style_analysis"]

    jazz_detail = result["style_analysis"]["jazz"]
    assert isinstance(jazz_detail, dict)
    assert jazz_detail["style_name"] == "jazz"
    assert jazz_detail["confidence"] == 0.92

    # Ensure JSON-serializable
    try:
        json_str = json.dumps(result)
        assert len(json_str) > 0
    except Exception as e:
        pytest.fail(f"AnalysisSummary with style fields not JSON-serializable: {e}")


def test_analysis_summary_without_style_fields_serialization():
    """
    Backward compatibility: Verify AnalysisSummary without style fields serializes.

    AC-7: Backward compatibility test verifies old API requests work unchanged
    """
    summary = AnalysisSummary(
        type=AnalysisType.FUNCTIONAL,
        roman_numerals=["I", "IV", "V", "I"],
        confidence=0.85,
        key_signature="C major",
        reasoning="Traditional functional progression",
        # No multi-profile fields (None/null)
        dominant_style=None,
        style_confidence=None,
        style_analysis=None,
    )

    result = summary.to_dict()

    # Core fields should be present
    assert result["type"] == "functional"
    assert result["confidence"] == 0.85

    # Style fields should be None
    assert result["dominant_style"] is None
    assert result["style_confidence"] is None
    assert result["style_analysis"] is None

    # Should still be JSON-serializable
    json_str = json.dumps(result)
    assert len(json_str) > 0


# -----------------------------
# AnalysisEnvelope Serialization Tests (AC-6)
# -----------------------------


def test_analysis_envelope_with_multi_profile_serialization():
    """
    Complete flow: Verify full AnalysisEnvelope with multi-profile data serializes.

    AC-6: Serialization test validates all new DTO types serialize correctly
    """
    primary = AnalysisSummary(
        type=AnalysisType.FUNCTIONAL,
        roman_numerals=["ii7", "V7", "Imaj7"],
        confidence=0.88,
        key_signature="C major",
        dominant_style="jazz",
        style_confidence={"jazz": 0.92, "classical": 0.75},
        style_analysis={
            "jazz": StyleAnalysisDetail(
                style_name="jazz",
                confidence=0.92,
                patterns=[],
                roman_numerals=["ii7", "V7", "Imaj7"],
                key_signature="C major",
            ),
        },
    )

    envelope = AnalysisEnvelope(
        primary=primary,
        alternatives=[],
        chord_symbols=["Dm7", "G7", "Cmaj7"],
        analysis_time_ms=45.2,
    )

    # Serialize envelope
    result = envelope.to_dict()

    # Validate envelope structure
    assert "primary" in result
    assert "alternatives" in result
    assert "chord_symbols" in result
    assert "analysis_time_ms" in result

    # Validate primary summary
    primary_dict = result["primary"]
    assert primary_dict["dominant_style"] == "jazz"
    assert isinstance(primary_dict["style_confidence"], dict)
    assert isinstance(primary_dict["style_analysis"], dict)

    # Ensure JSON-serializable
    try:
        json_str = json.dumps(result)
        assert len(json_str) > 0
    except Exception as e:
        pytest.fail(f"AnalysisEnvelope not JSON-serializable: {e}")


# -----------------------------
# JSON Roundtrip Tests (AC-6)
# -----------------------------


def test_style_analysis_detail_json_roundtrip():
    """
    Roundtrip validation: Verify StyleAnalysisDetail survives JSON roundtrip.

    AC-6: Serialization test validates all new DTO types serialize correctly
    """
    original = StyleAnalysisDetail(
        style_name="jazz",
        confidence=0.85,
        patterns=[],
        roman_numerals=["ii7", "V7", "Imaj7"],
        key_signature="C major",
        reasoning="Jazz cadence",
    )

    # Serialize to dict, then JSON, then back to dict
    dict1 = original.to_dict()
    json_str = json.dumps(dict1)
    dict2 = json.loads(json_str)

    # Verify fields match after roundtrip
    assert dict1 == dict2
    assert dict2["style_name"] == "jazz"
    assert dict2["confidence"] == 0.85
    assert dict2["roman_numerals"] == ["ii7", "V7", "Imaj7"]


def test_analysis_summary_json_roundtrip():
    """
    Roundtrip validation: Verify AnalysisSummary survives JSON roundtrip.

    AC-6: Serialization test validates all new DTO types serialize correctly
    """
    original = AnalysisSummary(
        type=AnalysisType.FUNCTIONAL,
        roman_numerals=["I", "IV", "V", "I"],
        confidence=0.85,
        key_signature="C major",
        dominant_style="classical",
        style_confidence={"classical": 0.90, "jazz": 0.60},
        style_analysis={
            "classical": StyleAnalysisDetail(
                style_name="classical",
                confidence=0.90,
                patterns=[],
                roman_numerals=["I", "IV", "V", "I"],
                key_signature="C major",
            ),
        },
    )

    # Serialize using to_json() and deserialize using from_json()
    json_str = original.to_json()
    restored = AnalysisSummary.from_json(json_str)

    # Verify core fields match
    assert restored.type == original.type
    assert restored.confidence == original.confidence
    assert restored.roman_numerals == original.roman_numerals
    assert restored.dominant_style == original.dominant_style

    # Verify style_confidence dict
    assert restored.style_confidence == original.style_confidence

    # Verify style_analysis nested structure
    assert restored.style_analysis is not None
    assert "classical" in restored.style_analysis
    assert restored.style_analysis["classical"].style_name == "classical"
    assert restored.style_analysis["classical"].confidence == 0.90


def test_analysis_envelope_json_roundtrip():
    """
    Full roundtrip: Verify complete AnalysisEnvelope survives JSON roundtrip.

    AC-6: Serialization test validates all new DTO types serialize correctly
    """
    original = AnalysisEnvelope(
        primary=AnalysisSummary(
            type=AnalysisType.FUNCTIONAL,
            roman_numerals=["ii7", "V7", "Imaj7"],
            confidence=0.88,
            dominant_style="jazz",
            style_confidence={"jazz": 0.92},
            style_analysis={
                "jazz": StyleAnalysisDetail(
                    style_name="jazz",
                    confidence=0.92,
                    patterns=[],
                    roman_numerals=["ii7", "V7", "Imaj7"],
                    key_signature="C major",
                ),
            },
        ),
        alternatives=[],
        chord_symbols=["Dm7", "G7", "Cmaj7"],
    )

    # Roundtrip through JSON
    json_str = original.to_json()
    restored = AnalysisEnvelope.from_json(json_str)

    # Verify structure preserved
    assert restored.primary.dominant_style == "jazz"
    assert restored.primary.style_confidence == {"jazz": 0.92}
    assert restored.primary.style_analysis is not None
    assert "jazz" in restored.primary.style_analysis
    assert restored.chord_symbols == ["Dm7", "G7", "Cmaj7"]


# -----------------------------
# Edge Cases and Error Handling
# -----------------------------


def test_none_style_analysis_serialization():
    """
    Edge case: Verify None style_analysis serializes correctly.

    AC-3: Dict[str, StyleAnalysisDetail] serializes correctly to nested JSON
    """
    summary = AnalysisSummary(
        type=AnalysisType.FUNCTIONAL,
        roman_numerals=["I", "IV", "V", "I"],
        confidence=0.85,
        style_analysis=None,  # Explicitly None
    )

    result = summary.to_dict()
    assert result["style_analysis"] is None

    # Should be JSON-serializable
    json_str = json.dumps(result)
    assert "style_analysis" in json_str


def test_nested_pattern_serialization_in_style_analysis():
    """
    Deep nesting: Verify patterns inside StyleAnalysisDetail serialize correctly.

    AC-3: Dict[str, StyleAnalysisDetail] serializes correctly to nested JSON
    AC-6: Serialization test validates all new DTO types serialize correctly
    """
    detail = StyleAnalysisDetail(
        style_name="jazz",
        confidence=0.90,
        patterns=[
            PatternMatchDTO(
                start=0,
                end=3,
                pattern_id="ii-V-I",
                name="ii-V-I Jazz Cadence",
                family="cadence",
                score=0.92,
                evidence=[{"type": "strong_resolution", "weight": 0.9}],
                style_tags=["jazz", "bebop"],
                detected_via_profile="jazz",
                style_typicality=0.95,
            ),
            PatternMatchDTO(
                start=3,
                end=5,
                pattern_id="turnaround",
                name="Jazz Turnaround",
                family="schema",
                score=0.85,
            ),
        ],
        roman_numerals=["ii7", "V7", "Imaj7", "vi7", "ii7"],
        key_signature="C major",
    )

    result = detail.to_dict()

    # Validate patterns list serialization
    assert isinstance(result["patterns"], list)
    assert len(result["patterns"]) == 2

    # Validate first pattern
    pattern1 = result["patterns"][0]
    assert pattern1["pattern_id"] == "ii-V-I"
    assert pattern1["score"] == 0.92
    assert isinstance(pattern1["evidence"], list)
    assert isinstance(pattern1["style_tags"], list)
    assert pattern1["style_tags"] == ["jazz", "bebop"]
    assert pattern1["detected_via_profile"] == "jazz"
    assert pattern1["style_typicality"] == 0.95

    # Ensure JSON-serializable
    json_str = json.dumps(result)
    assert len(json_str) > 0


def test_serialize_dataclass_with_mixed_types():
    """
    Stress test: Verify serializer handles mixed nested types correctly.

    AC-6: Serialization test validates all new DTO types serialize correctly
    """
    # Create a complex nested structure
    summary = AnalysisSummary(
        type=AnalysisType.FUNCTIONAL,
        roman_numerals=["I", "IV", "V", "I"],
        confidence=0.85,
        patterns=[
            PatternMatchDTO(
                start=0,
                end=4,
                pattern_id="authentic_cadence",
                name="Perfect Authentic Cadence",
                family="cadence",
                score=0.9,
            )
        ],
        style_analysis={
            "classical": StyleAnalysisDetail(
                style_name="classical",
                confidence=0.90,
                patterns=[],
                roman_numerals=["I", "IV", "V", "I"],
                key_signature="C major",
            ),
            "jazz": StyleAnalysisDetail(
                style_name="jazz",
                confidence=0.70,
                patterns=[],
                roman_numerals=["I", "IV", "V", "I"],
                key_signature="C major",
            ),
        },
    )

    # Serialize
    result = serialize_dataclass(summary)

    # Verify all nested types handled correctly
    assert result["type"] == "functional"  # Enum → string
    assert isinstance(result["patterns"], list)  # List[PatternMatchDTO] → list of dicts
    assert isinstance(
        result["style_analysis"], dict
    )  # Dict[str, StyleAnalysisDetail] → dict of dicts

    # Verify nested StyleAnalysisDetail
    assert isinstance(result["style_analysis"]["classical"], dict)
    assert result["style_analysis"]["classical"]["style_name"] == "classical"

    # Ensure JSON-serializable
    json_str = json.dumps(result)
    assert len(json_str) > 0
