"""
Unit tests for the glossary integration in the unified pattern engine.

Tests the glossary helper functions and their integration with the pattern engine
to ensure feature enrichment works correctly.
"""

import pytest
from unittest.mock import patch, MagicMock

from harmonic_analysis.core.pattern_engine import (
    PatternEngine,
    AnalysisContext,
    Evidence,
)
from harmonic_analysis.core.pattern_engine.glossary import (
    explain_feature,
    enrich_features,
    get_summary_terms,
    load_glossary,
    load_default_glossary,
)


class TestGlossaryHelpers:
    """Test the glossary helper functions."""

    def test_explain_feature_with_known_features(self):
        """Test explaining known features with mock glossary."""
        glossary = {
            "analysis_terms": {
                "functional_harmony": "System of chord functions guiding progression",
                "chromaticism": "Use of notes outside the diatonic scale",
            },
            "cadences": {
                "PAC": {
                    "definition": "Perfect Authentic Cadence. V–I with soprano on tonic."
                }
            },
        }

        # Test feature mapping
        label, tooltip = explain_feature(glossary, "has_auth_cadence")
        assert label == "Authentic Cadence"
        assert "Authentic Cadence detected" in tooltip

        # Test direct analysis_terms lookup
        label, tooltip = explain_feature(glossary, "functional_harmony")
        assert label == "Functional Harmony"
        assert tooltip == "System of chord functions guiding progression"

    def test_explain_feature_with_unknown_features(self):
        """Test explaining unknown features returns fallback."""
        glossary = {}

        label, tooltip = explain_feature(glossary, "unknown_feature")
        assert label == "unknown_feature"
        assert tooltip == "unknown_feature"

    def test_explain_feature_with_legacy_features(self):
        """Test explaining legacy features like lt_suppression."""
        glossary = {"scale_degrees": {"7": "Leading tone — B in C major."}}

        label, tooltip = explain_feature(glossary, "lt_suppression")
        assert label == "Leading Tone Suppression"
        assert "leading tone resolution" in tooltip.lower()

    def test_enrich_features_with_known_features(self):
        """Test enriching features dictionary."""
        glossary = {"analysis_terms": {"modal_char_score": "Modal character strength"}}

        features = {
            "modal_char_score": 0.8,
            "pattern_weight": 0.7,
            "unknown_feature": 0.5,
        }

        enriched = enrich_features(glossary, features)

        # Original features preserved
        assert enriched["modal_char_score"] == 0.8
        assert enriched["pattern_weight"] == 0.7
        assert enriched["unknown_feature"] == 0.5

        # UI enrichment added
        assert "features_ui" in enriched
        ui_features = enriched["features_ui"]

        # Check known features have UI info
        assert "modal_char_score" in ui_features
        assert ui_features["modal_char_score"]["label"] == "Modal Char Score"
        assert ui_features["modal_char_score"]["value"] == 0.8

        assert "pattern_weight" in ui_features
        assert ui_features["pattern_weight"]["label"] == "Pattern Weight"

    def test_enrich_features_with_no_known_features(self):
        """Test enriching features when no features are known."""
        glossary = {}
        features = {"unknown1": 0.5, "unknown2": 0.8}

        enriched = enrich_features(glossary, features)

        # Original features preserved
        assert enriched["unknown1"] == 0.5
        assert enriched["unknown2"] == 0.8

        # No UI enrichment added since no features were enhanced
        assert "features_ui" not in enriched

    def test_get_summary_terms(self):
        """Test getting summary terms for AnalysisSummary."""
        glossary = {
            "analysis_terms": {
                "tonal_clarity": "Strength of functional harmonic progression"
            }
        }

        feature_keys = ["tonal_clarity", "has_auth_cadence", "unknown_feature"]
        terms = get_summary_terms(glossary, feature_keys)

        # Known features should be included
        assert "tonal_clarity" in terms
        assert terms["tonal_clarity"]["label"] == "Tonal Clarity"
        assert (
            terms["tonal_clarity"]["tooltip"]
            == "Strength of functional harmonic progression"
        )

        assert "has_auth_cadence" in terms
        assert terms["has_auth_cadence"]["label"] == "Authentic Cadence"

        # Unknown features should not be included
        assert "unknown_feature" not in terms

    def test_load_glossary_uses_glossary_service(self):
        """Test that load_glossary uses the existing GlossaryService."""
        with patch(
            "harmonic_analysis.core.pattern_engine.glossary.GlossaryService"
        ) as mock_service:
            mock_instance = MagicMock()
            mock_instance.glossary = {"test": "data"}
            mock_service.return_value = mock_instance

            result = load_glossary()

            assert result == {"test": "data"}
            mock_service.assert_called_once_with()

    def test_load_default_glossary(self):
        """Test loading default glossary."""
        with patch(
            "harmonic_analysis.core.pattern_engine.glossary.load_glossary"
        ) as mock_load:
            mock_load.return_value = {"default": "glossary"}

            result = load_default_glossary()

            assert result == {"default": "glossary"}
            mock_load.assert_called_once_with()


class TestPatternEngineGlossaryIntegration:
    """Test glossary integration in the pattern engine."""

    def test_pattern_engine_loads_glossary_on_init(self):
        """Test that pattern engine loads glossary on initialization."""
        with patch(
            "harmonic_analysis.core.pattern_engine.pattern_engine.GlossaryService"
        ) as mock_service:
            instance = mock_service.return_value
            instance.glossary = {"test": "glossary"}
            engine = PatternEngine()
            assert engine._glossary == {"test": "glossary"}
            mock_service.assert_called_once()

    def test_pattern_engine_handles_missing_glossary(self):
        """Test that pattern engine handles missing glossary gracefully."""
        with patch(
            "harmonic_analysis.core.pattern_engine.pattern_engine.GlossaryService"
        ) as mock_service:
            with patch(
                "harmonic_analysis.core.pattern_engine.pattern_engine.load_default_glossary"
            ) as mock_load:
                mock_service.side_effect = Exception("service unavailable")
                mock_load.side_effect = FileNotFoundError("Glossary not found")

                engine = PatternEngine()

                assert engine._glossary == {}

    def test_evidence_conversion_enriches_features(self):
        """Test that evidence conversion enriches features with glossary."""
        # Create engine with mock glossary
        engine = PatternEngine()
        engine._glossary = {
            "analysis_terms": {
                "tonal_clarity": "Strength of functional harmonic progression"
            }
        }

        # Create evidence with features
        evidences = [
            Evidence(
                pattern_id="test.pattern",
                track_weights={"functional": 0.8},
                features={"tonal_clarity": 0.9, "unknown_feature": 0.5},
                raw_score=0.8,
                uncertainty=None,
                span=(0, 2),
            )
        ]

        # Convert evidence
        evidence_dtos = engine._convert_evidence(evidences)

        assert len(evidence_dtos) == 1
        dto = evidence_dtos[0]

        # Check that features were enriched
        features = dto.details["features"]
        assert "tonal_clarity" in features
        assert "unknown_feature" in features

        # Check for UI enrichment
        assert "features_ui" in features
        ui_features = features["features_ui"]
        assert "tonal_clarity" in ui_features
        assert ui_features["tonal_clarity"]["label"] == "Tonal Clarity"
        assert (
            ui_features["tonal_clarity"]["tooltip"]
            == "Strength of functional harmonic progression"
        )

    def test_analysis_summary_includes_terms(self, tmp_path):
        """Test that analysis summary includes terms from glossary."""
        # Create minimal pattern file
        pattern_file = tmp_path / "test_patterns.json"
        pattern_file.write_text('{"version": 1, "patterns": []}')

        # Create engine with mock glossary
        engine = PatternEngine()
        engine._glossary = {
            "analysis_terms": {"pattern_weight": "Base confidence weight for patterns"}
        }
        engine.load_patterns(pattern_file)

        # Mock evidences with features
        evidences = [
            Evidence(
                pattern_id="test.pattern",
                track_weights={"functional": 0.8},
                features={"pattern_weight": 0.7},
                raw_score=0.8,
                uncertainty=None,
                span=(0, 2),
            )
        ]

        # Build analysis summary
        context = AnalysisContext(
            key="C major",
            chords=["C", "F"],
            roman_numerals=["I", "IV"],
            melody=[],
            scales=[],
            metadata={},
        )

        summary = engine._build_analysis_summary(context, evidences, 0.8, 0.2, 0.8, {})

        # Check that terms were populated
        assert "terms" in summary.__dict__
        terms = summary.terms
        assert "analysis_method" in terms
        assert isinstance(terms["analysis_method"], dict)
        assert terms["analysis_method"]["label"] == "Unified Pattern Engine"
        assert "tooltip" in terms["analysis_method"]

        assert "pattern_weight" in terms
        assert terms["pattern_weight"]["label"] == "Pattern Weight"
        assert terms["pattern_weight"].get("tooltip")

    def test_end_to_end_glossary_integration(self, tmp_path):
        """Test complete end-to-end glossary integration."""
        # Create pattern file with a simple pattern
        pattern_file = tmp_path / "test_patterns.json"
        patterns = {
            "version": 1,
            "patterns": [
                {
                    "id": "cadence.test",
                    "name": "Test Cadence",
                    "scope": ["harmonic"],
                    "track": ["functional"],
                    "matchers": {"roman_seq": ["V", "I"]},
                    "evidence": {"weight": 0.9, "confidence_fn": "identity"},
                }
            ],
        }
        import json

        pattern_file.write_text(json.dumps(patterns))

        # Create engine with mock glossary
        engine = PatternEngine()
        engine._glossary = {
            "analysis_terms": {
                "identity": "Identity function",
                "pattern_weight": "Base pattern weight",
            }
        }
        engine._glossary_service = type(
            "StubGlossary",
            (),
            {
                "get_cadence_explanation": staticmethod(
                    lambda name: {"definition": "Test cadence definition"}
                ),
                "get_term_definition": staticmethod(lambda term: None),
            },
        )()
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

        # Check that terms are populated in primary analysis
        terms = envelope.primary.terms
        assert "analysis_method" in terms
        assert isinstance(terms["analysis_method"], dict)

        # Check evidence enrichment
        if envelope.evidence:
            evidence = envelope.evidence[0]
            features = evidence.details["features"]
            # Should have features_ui if any known features were found
            if any(
                key in engine._glossary.get("analysis_terms", {})
                for key in features.keys()
            ):
                assert "features_ui" in features

        # Cadence glossary should be attached to pattern match
        patterns = envelope.primary.patterns
        if patterns:
            assert patterns[0].glossary
            assert patterns[0].glossary.get("definition") == "Test cadence definition"


# Integration test fixtures
@pytest.fixture
def mock_glossary():
    """Fixture providing a mock glossary for testing."""
    return {
        "cadences": {
            "PAC": {
                "definition": "Perfect Authentic Cadence. V–I with soprano on tonic."
            }
        },
        "analysis_terms": {
            "functional_harmony": "System of chord functions guiding progression",
            "modal_char_score": "Modal character strength",
            "tonal_clarity": "Strength of functional harmonic progression",
        },
        "terms": {"scale_degree": "Position of a note within the scale, numbered 1-7"},
    }


class TestGlossaryServiceCompatibility:
    """Test compatibility with existing GlossaryService."""

    def test_explain_feature_uses_existing_service_logic(self, mock_glossary):
        """Test that explain_feature properly leverages GlossaryService."""
        with patch(
            "harmonic_analysis.core.pattern_engine.glossary.GlossaryService"
        ) as mock_service_class:
            # Mock the service instance
            mock_service = MagicMock()
            mock_service.get_term_definition.return_value = "System of chord functions"
            mock_service_class.return_value = mock_service

            label, tooltip = explain_feature(mock_glossary, "functional_harmony")

            # Should have called the service method
            mock_service.get_term_definition.assert_called_once_with(
                "functional_harmony"
            )
            assert label == "Functional Harmony"
            assert tooltip == "System of chord functions"

    def test_fallback_when_service_returns_none(self, mock_glossary):
        """Test fallback behavior when GlossaryService returns None."""
        with patch(
            "harmonic_analysis.core.pattern_engine.glossary.GlossaryService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_term_definition.return_value = None
            mock_service_class.return_value = mock_service

            label, tooltip = explain_feature(mock_glossary, "has_auth_cadence")

            # Should fall back to custom mappings
            assert label == "Authentic Cadence"
            assert "Authentic Cadence detected" in tooltip
