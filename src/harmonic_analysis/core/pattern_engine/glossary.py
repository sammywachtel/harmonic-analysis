"""
Glossary helper functions for feature term enrichment.

This module provides pure helper functions that work with the existing GlossaryProvider
to enrich backend feature names with human-readable labels, tooltips, and definitions
for UI presentation. No UI dependencies - pure data transformation.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .glossary_provider import GlossaryProvider


def load_glossary(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load glossary data using the existing GlossaryProvider.

    Args:
        path: Optional path to glossary.json file. If None, uses default.

    Returns:
        Dictionary containing glossary data with categories and terms

    Raises:
        FileNotFoundError: If glossary file doesn't exist
    """
    if path:
        service = GlossaryProvider(str(path))
    else:
        service = GlossaryProvider()

    return service.glossary


def explain_feature(glossary: Dict[str, Any], key: str) -> Tuple[str, str]:
    """
    Get human-readable label and tooltip for a feature key using GlossaryProvider logic.

    Args:
        glossary: Loaded glossary data (from GlossaryProvider)
        key: Feature key to explain (e.g., "lt_suppression", "raised6_ratio")

    Returns:
        Tuple of (label, tooltip) strings. If key not found, returns (key, key)
        to provide graceful fallback without exceptions.
    """
    # Create a temporary service instance to use existing lookup logic
    service = GlossaryProvider()
    service.glossary = glossary

    # Use existing get_term_definition method
    definition = service.get_term_definition(key)
    if definition:
        label = key.replace("_", " ").title()
        return label, definition

    # Map common feature keys to human-readable labels with custom logic
    feature_mappings = {
        # Cadence features
        "has_auth_cadence": (
            "Authentic Cadence",
            "Perfect or Imperfect Authentic Cadence detected",
        ),
        "has_plagal_cadence": (
            "Plagal Cadence",
            "IV-I progression, often at hymn endings",
        ),
        "has_half_cadence": (
            "Half Cadence",
            "Cadence ending on V, creating expectation",
        ),
        "has_deceptive_cadence": (
            "Deceptive Cadence",
            "V-vi avoiding resolution to tonic",
        ),
        # Modal features
        "modal_char_score": (
            "Modal Character",
            "Strength of modal vs functional characteristics",
        ),
        "dorian_character": (
            "Dorian Character",
            "Dorian mode characteristics (raised 6th)",
        ),
        "phrygian_character": (
            "Phrygian Character",
            "Phrygian mode characteristics (lowered 2nd)",
        ),
        "mixolydian_character": (
            "Mixolydian Character",
            "Mixolydian mode characteristics (lowered 7th)",
        ),
        # Functional features
        "tonal_clarity": (
            "Tonal Clarity",
            "Strength of functional harmonic progression",
        ),
        "predominant_function": (
            "Predominant Function",
            "Pre-dominant harmony (ii, IV, vi)",
        ),
        "dominant_function": ("Dominant Function", "Dominant harmony creating tension"),
        # Chromatic features
        "outside_key_ratio": (
            "Chromatic Content",
            "Proportion of notes outside the diatonic scale",
        ),
        "chromatic_density": ("Chromatic Density", "Amount of chromatic alteration"),
        "secondary_dominants": (
            "Secondary Dominants",
            "V/x chords tonicizing other degrees",
        ),
        # Voice leading features
        "voice_leading_smoothness": (
            "Voice Leading",
            "Quality of melodic motion between chords",
        ),
        "soprano_degree": ("Soprano Degree", "Scale degree of the soprano voice"),
        # Rhythmic features
        "harmonic_rhythm": ("Harmonic Rhythm", "Rate of chord change"),
        # Legacy support for common features
        "lt_suppression": (
            "Leading Tone Suppression",
            "Avoidance of leading tone resolution",
        ),
        "raised6_ratio": ("Raised Sixth", "Proportion of raised 6th scale degrees"),
        "flat7_ratio": ("Lowered Seventh", "Proportion of lowered 7th scale degrees"),
        # Pattern weight features
        "pattern_weight": ("Pattern Weight", "Base confidence weight for this pattern"),
    }

    if key in feature_mappings:
        return feature_mappings[key]

    # Try to extract from glossary using existing paths
    cadences = glossary.get("cadences", {})
    if key.lower() in [k.lower() for k in cadences.keys()]:
        for cadence_key, cadence_data in cadences.items():
            if key.lower() == cadence_key.lower():
                if isinstance(cadence_data, dict) and "definition" in cadence_data:
                    label = cadence_key.replace("_", " ")
                    return label, cadence_data["definition"]

    # Check analysis_terms directly
    analysis_terms = glossary.get("analysis_terms", {})
    if key in analysis_terms:
        label = key.replace("_", " ").title()
        return label, analysis_terms[key]

    # Fallback: return key as both label and tooltip
    return key, key


def enrich_features(
    glossary: Dict[str, Any], features: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enrich feature dictionary with UI labels and tooltips.

    Args:
        glossary: Loaded glossary data
        features: Dictionary of feature keys to values

    Returns:
        Enhanced features dictionary with added 'features_ui' section containing
        labels and tooltips for known features. Original features preserved.
    """
    enriched = features.copy()
    ui_enrichment = {}

    for feature_key, feature_value in features.items():
        label, tooltip = explain_feature(glossary, feature_key)

        # Only add UI enrichment if we have meaningful enhancement
        if label != feature_key or tooltip != feature_key:
            ui_enrichment[feature_key] = {
                "label": label,
                "tooltip": tooltip,
                "value": feature_value,
            }

    # Add UI enrichment if we found any
    if ui_enrichment:
        enriched["features_ui"] = ui_enrichment

    return enriched


def get_summary_terms(
    glossary: Dict[str, Any], feature_keys: list[str]
) -> Dict[str, Dict[str, str]]:
    """
    Generate summary terms mapping for AnalysisSummary.terms field.

    Args:
        glossary: Loaded glossary data
        feature_keys: List of feature keys to generate terms for

    Returns:
        Dictionary mapping feature keys to {label, tooltip} dicts
    """
    terms = {}

    for key in feature_keys:
        label, tooltip = explain_feature(glossary, key)

        # Only include if we have meaningful enhancement
        if label != key or tooltip != key:
            terms[key] = {"label": label, "tooltip": tooltip}

    return terms


def describe_feature(glossary: Dict[str, Any], key: str) -> Dict[str, Any]:
    """
    Get comprehensive description of a feature for documentation/debugging.

    Args:
        glossary: Loaded glossary data
        key: Feature key to describe

    Returns:
        Dictionary with human_name, definition, computation info, ui data, examples
    """
    label, tooltip = explain_feature(glossary, key)

    description = {
        "key": key,
        "human_name": label,
        "definition": tooltip,
        "computation": "Computed during pattern matching",
        "ui": {"label": label, "tooltip": tooltip},
        "examples": [],
    }

    # Add examples if available in glossary
    # This could be extended to include more detailed examples
    if "cadence" in key.lower():
        description["examples"] = ["V-I progression", "Authentic resolution"]
    elif "modal" in key.lower():
        description["examples"] = [
            "Dorian progression",
            "Mode-specific characteristics",
        ]
    elif "chromatic" in key.lower():
        description["examples"] = ["Secondary dominants", "Non-diatonic chords"]

    return description


def load_default_glossary() -> Dict[str, Any]:
    """
    Load glossary from default location using GlossaryProvider.

    Returns:
        Loaded glossary data

    Raises:
        FileNotFoundError: If default glossary doesn't exist
    """
    return load_glossary()
