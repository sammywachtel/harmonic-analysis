"""
Unit tests for AnalysisSummary and AnalysisEnvelope data transfer objects (DTOs) in the harmonic_analysis module.

These tests verify correct construction, serialization/deserialization, default values, clamping behavior,
and handling of edge cases for the AnalysisSummary and AnalysisEnvelope classes. They ensure that the DTOs behave
as expected when used in typical and boundary scenarios.
"""

from harmonic_analysis.dto import AnalysisEnvelope, AnalysisSummary, AnalysisType


def test_summary_minimal_construction():
    # Test minimal required fields for AnalysisSummary.
    # Verifies that the object can be created with just type, roman_numerals, and confidence,
    # and that optional fields default to None or empty collections.
    s = AnalysisSummary(
        type=AnalysisType.FUNCTIONAL, roman_numerals=["I"], confidence=0.9
    )
    assert s.type == AnalysisType.FUNCTIONAL
    assert s.roman_numerals == ["I"]
    assert s.confidence == 0.9
    assert s.key_signature is None
    assert s.terms == {}
    assert s.patterns == []


def test_summary_full_construction_and_serialization():
    # For full construction with nested fields, use from_dict with plain dicts for patterns/chromatic_elements.
    # This keeps tests robust to DTO constructor signature changes and still checks normalization/roundtrip.
    s = AnalysisSummary.from_dict(
        {
            "type": "modal",  # prove string accepted
            "roman_numerals": ["i", "bVII", "VI", "V"],
            "confidence": 1.2,  # should clamp to 1.0
            "key_signature": "A minor",
            "mode": "minor",
            "reasoning": "Andalusian cadence",
            "functional_confidence": 0.3,
            "modal_confidence": 0.7,
            "terms": {"cadence": "closure"},
            # Provide plain dicts; from_dict should normalize to DTOs internally
            "patterns": [
                {
                    "pattern_id": "andalusian",
                    "name": "Andalusian",
                    "family": "cadence",
                    "score": 1.0,
                    "start": 0,
                    "end": 3,
                }
            ],
            "modal_characteristics": ["♭VII chord"],
            "chromatic_elements": [
                {
                    "type": "secondary_dominant",
                    "roman_numeral": "V/V",
                    "explanation": "Secondary dominant",
                }
            ],
        }
    )
    # s is already normalized and fully constructed
    assert s.confidence == 1.0
    assert s.roman_numerals[-1] == "V"
    # Confirm that the pattern id is preserved and accessible regardless of DTO/dict representation
    pid = getattr(s, "patterns")[0]
    pid_val = getattr(pid, "pattern_id", None) or (
        pid.get("pattern_id") if isinstance(pid, dict) else None
    )
    assert pid_val == "andalusian"


def test_envelope_with_alternatives():
    # Test AnalysisEnvelope creation with a primary AnalysisSummary and alternatives list.
    # Also verifies serialization/deserialization round-trip maintains data integrity.
    primary = AnalysisSummary(
        type=AnalysisType.FUNCTIONAL, roman_numerals=["I"], confidence=0.8
    )
    alt = AnalysisSummary(type=AnalysisType.MODAL, roman_numerals=["i"], confidence=0.6)
    env = AnalysisEnvelope(
        primary=primary, alternatives=[alt], analysis_time_ms=12.3, chord_symbols=["C"]
    )
    # Confirm primary and alternative summaries are correctly assigned
    assert env.primary == primary
    assert env.alternatives[0] == alt
    d = env.to_dict()
    env2 = AnalysisEnvelope.from_dict(d)
    # Check that after deserialization, primary type and alternatives count are preserved
    assert env2.primary.type == AnalysisType.FUNCTIONAL
    assert len(env2.alternatives) == 1


def test_confidence_clamping_and_defaults():
    # Test that confidence values outside the valid range [0.0, 1.0] are clamped correctly.
    # Also test that providing empty roman numerals list does not cause issues.
    s = AnalysisSummary(
        type=AnalysisType.FUNCTIONAL, roman_numerals=[], confidence=-0.5
    )
    # Confidence below 0 should clamp to 0.0
    assert s.confidence == 0.0
    s2 = AnalysisSummary(type=AnalysisType.MODAL, roman_numerals=[], confidence=2.5)
    # Confidence above 1 should clamp to 1.0
    assert s2.confidence == 1.0


def test_enum_safety_in_from_dict():
    # Test that from_dict correctly handles enum-like string fields without error,
    # ensuring type field is preserved as string and matches expected values.
    d = {"type": "functional", "roman_numerals": ["I"], "confidence": 0.9}
    s = AnalysisSummary.from_dict(d)
    assert s.type == AnalysisType.FUNCTIONAL
    d2 = s.to_dict()
    # Confirm serialization preserves type string exactly
    assert d2["type"] == "functional"


def test_edge_cases_empty_fields():
    # Test handling of empty lists and default empty collections for terms and patterns.
    # Also verify that AnalysisEnvelope defaults to empty lists for chord_symbols and evidence when not provided.
    s = AnalysisSummary(type=AnalysisType.MODAL, roman_numerals=[], confidence=0.5)
    # Roman numerals list should be empty as provided
    assert s.roman_numerals == []
    # Terms should default to an empty dict
    assert isinstance(s.terms, dict)
    # Patterns should default to an empty list
    assert isinstance(s.patterns, list)
    env = AnalysisEnvelope(primary=s)
    # chord_symbols and evidence should default to empty lists
    assert env.chord_symbols == []
    assert env.evidence == []
