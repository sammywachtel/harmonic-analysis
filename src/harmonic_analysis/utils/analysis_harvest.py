"""
Token harvesting utilities for educational tags integration.

Extracts normalized harmonic terms from analysis results to power
glossary features, UI hovers, and educational context.
"""

from typing import List, Dict, Any, Tuple


# Accidental normalization mapping
ACC = str.maketrans({"♭": "b", "♯": "#"})


def harvest_harmonic_terms(tokens: List[Dict[str, Any]], patterns: List[Dict[str, Any]]) -> Tuple[List[str], str]:
    """
    Extract normalized harmonic terms and roman text from analysis results.

    Args:
        tokens: List of harmonic analysis tokens with roman numerals, roles, etc.
        patterns: List of pattern matches with families and educational context

    Returns:
        Tuple of (harmonic_terms, romans_text) where:
        - harmonic_terms: Normalized list of harmonic terms for glossary/UI
        - romans_text: Space-separated string of roman numerals
    """
    romans: List[str] = []
    roles: set[str] = set()
    qualities: set[str] = set()
    families: set[str] = set()

    def norm_roman(s: str) -> str:
        """Normalize roman numeral: lowercase, strip secondary targets."""
        if not s:
            return ""
        s = s.translate(ACC)  # Normalize accidentals
        s = s.split("/")[0]   # Drop secondary target (V/ii → V)
        return s.lower()

    # Extract terms from tokens
    for t in tokens:
        r = norm_roman(t.get("roman", ""))
        if r:
            romans.append(r)

        # Map functional roles T/PD/D → tonic/predominant/dominant
        role = (t.get("role") or "").upper()
        if role == "T":
            roles.add("tonic")
        elif role == "PD":
            roles.add("predominant")
        elif role == "D":
            roles.add("dominant")

        # Detect seventh chords for quality tagging
        chord_txt = (t.get("roman") or "") + " " + (t.get("flags_text") or "")
        chord_txt = chord_txt.lower()
        if any(x in chord_txt for x in ["7", "maj7", "∆", "Δ"]):
            qualities.add("seventh")

    # Extract terms from pattern matches
    for m in patterns or []:
        fam = (m.get("family") or "").lower()
        if fam:
            families.add(fam)

        # Add specific pattern family terms
        if fam == "cadence":
            families.add("cadence")
        elif fam in ["sequence", "schema", "jazz_pop"]:
            families.add(fam)

    # Clean up romans and create romans_text
    romans = [r for r in romans if r]
    romans_text = " ".join(romans)

    # Combine terms: romans first (preserve order), then other terms sorted
    # Use dict.fromkeys to preserve order while removing duplicates
    terms = list(dict.fromkeys(romans)) + sorted(roles | qualities | families)

    return terms, romans_text


def extract_chord_qualities(tokens: List[Dict[str, Any]]) -> set[str]:
    """
    Extract chord quality terms from harmonic analysis tokens.

    Args:
        tokens: List of harmonic analysis tokens

    Returns:
        Set of quality terms like 'seventh', 'triad', etc.
    """
    qualities = set()

    for token in tokens:
        roman = token.get("roman", "")
        flags = token.get("flags_text", "") or " ".join(token.get("flags", []))
        chord_text = f"{roman} {flags}".lower()

        # Detect seventh chords
        if any(indicator in chord_text for indicator in ["7", "maj7", "∆", "Δ"]):
            qualities.add("seventh")

        # Could extend with other qualities: ninth, eleventh, augmented, etc.

    return qualities


def normalize_roman_numeral(roman: str) -> str:
    """
    Normalize a single roman numeral for consistent term extraction.

    Args:
        roman: Raw roman numeral string (e.g., "♭VI", "V7/ii")

    Returns:
        Normalized lowercase roman with accidentals standardized
    """
    if not roman:
        return ""

    # Normalize accidentals
    normalized = roman.translate(ACC)

    # Strip secondary targets (V/ii → V)
    normalized = normalized.split("/")[0]

    # Strip inversion figures for base roman (vi6 → vi)
    # Keep common inversions but remove complex extensions
    for suffix in ["65", "43", "42", "64"]:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)]
            break
    if normalized.endswith("6") and not normalized.endswith("64"):
        normalized = normalized[:-1]

    return normalized.lower()
