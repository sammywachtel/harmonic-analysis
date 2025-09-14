"""
Glossary Service - Educational context for pattern analysis terms.

Provides definitions, examples, and educational context for music theory
terms used in pattern analysis results.
"""

import json
from typing import Any, Dict, List, Optional

try:
    from ...resources import load_glossary
except ImportError:
    # Fallback for testing or when resources aren't available
    from pathlib import Path


class GlossaryService:
    """Service for providing educational context about music theory terms."""

    def __init__(self, glossary_path: Optional[str] = None):
        """Initialize glossary service.

        Args:
            glossary_path: Path to glossary JSON file. If None, uses resource loader.
        """
        if glossary_path is None:
            try:
                self.glossary: Dict[str, Any] = load_glossary()
            except (ImportError, NameError):
                # Fallback to old path-based loading
                glossary_path_obj = Path(__file__).parent / "glossary.json"
                try:
                    with open(glossary_path_obj, "r") as f:
                        self.glossary = json.load(f)
                except FileNotFoundError:
                    print(f"Warning: Glossary file not found at {glossary_path_obj}")
                    self.glossary = {}
        else:
            try:
                with open(glossary_path, "r") as f:
                    self.glossary = json.load(f)
            except FileNotFoundError:
                print(f"Warning: Glossary file not found at {glossary_path}")
                self.glossary = {}

    def get_cadence_explanation(self, pattern_name: str) -> Optional[Dict[str, Any]]:
        """Get explanation for cadence pattern.

        Args:
            pattern_name: Name of the pattern (e.g., "PAC with soprano on 1")

        Returns:
            Dictionary with definition, example, and educational context
        """
        # Extract cadence type from pattern name
        cadence_type = self._extract_cadence_type(pattern_name)

        if cadence_type and cadence_type in self.glossary.get("cadences", {}):
            cadence_info = self.glossary["cadences"][cadence_type].copy()

            # Add soprano information if present
            if "soprano on" in pattern_name.lower():
                soprano_degree = self._extract_soprano_degree(pattern_name)
                if soprano_degree:
                    cadence_info["soprano_context"] = self._get_soprano_context(
                        soprano_degree
                    )

            return dict(cadence_info) if cadence_info else None

        return None

    def get_term_definition(self, term: str) -> Optional[str]:
        """Get definition of a music theory term.

        Args:
            term: Term to look up (e.g., "scale_degree", "tonic")

        Returns:
            Definition string or None if not found
        """
        # Check in different sections
        sections = [
            "terms",
            "functions",
            "voices",
            "chord_positions",
            "figured_bass_notation",
            "non_cadential_progressions",
            "patterns",
            "pattern_families",
            "analysis_terms",
        ]

        term_lower = term.lower().replace(" ", "_")
        term_original = term.replace(" ", "_")

        for section in sections:
            if section in self.glossary:
                # Try lowercase first (standard case)
                if term_lower in self.glossary[section]:
                    return str(self.glossary[section][term_lower])
                # Try original case (for abbreviations like T, D, PD)
                elif term_original in self.glossary[section]:
                    return str(self.glossary[section][term_original])

        return None

    def get_scale_degree_info(
        self, degree: int, key: str = "C major"
    ) -> Dict[str, Any]:
        """Get information about a scale degree.

        Args:
            degree: Scale degree (1-7)
            key: Key context (e.g., "C major")

        Returns:
            Dictionary with degree name, function, and note in key
        """
        if str(degree) not in self.glossary.get("scale_degrees", {}):
            return {}

        degree_info = {
            "degree": degree,
            "name": self._get_degree_name(degree),
            "description": self.glossary["scale_degrees"][str(degree)],
            "key_context": key,
        }

        # Add actual note name in the given key
        if key.endswith("major"):
            key_root = key.split()[0]
            degree_info["note_in_key"] = self._calculate_note_in_key(key_root, degree)

        return degree_info

    def explain_pattern_result(self, pattern_match: Dict[str, Any]) -> Dict[str, Any]:
        """Provide comprehensive explanation for a pattern match result.

        Args:
            pattern_match: Pattern match dictionary from matcher

        Returns:
            Enhanced result with educational explanations
        """
        explanation = {
            "pattern_name": pattern_match.get("name", "Unknown"),
            "family": pattern_match.get("family", "unknown"),
            "score": pattern_match.get("score", 0),
            "educational_context": {},
        }

        pattern_name = pattern_match.get("name", "")

        # Add cadence explanation if it's a cadence
        if pattern_match.get("family") == "cadence":
            cadence_explanation = self.get_cadence_explanation(pattern_name)
            if cadence_explanation:
                explanation["educational_context"]["cadence_info"] = cadence_explanation

        # Add Roman numeral explanations from evidence
        if "evidence" in pattern_match and isinstance(pattern_match["evidence"], list):
            roman_explanations = []
            for evidence_item in pattern_match["evidence"]:
                # Handle both old tuple format and new StepEvidence format
                if isinstance(evidence_item, dict):
                    # New StepEvidence format: {'step_index': int, 'roman': str,
                    # 'role': str, 'flags': List[str]}
                    roman = evidence_item.get("roman")
                    role = evidence_item.get("role")
                elif (
                    isinstance(evidence_item, (tuple, list)) and len(evidence_item) >= 3
                ):
                    # Old tuple format: (index, roman, role, flags)
                    roman = evidence_item[1]
                    role = evidence_item[2]
                else:
                    # Skip invalid evidence items
                    continue

                if roman and role:
                    roman_explanation = {
                        "roman": roman,
                        "role": role,
                        "role_definition": self.get_term_definition(role.lower()),
                    }
                    roman_explanations.append(roman_explanation)

            if roman_explanations:
                explanation["educational_context"][
                    "chord_functions"
                ] = roman_explanations

        # Add progression type explanations
        family = pattern_match.get("family", "")
        if family:
            family_explanation = self._get_family_explanation(family)
            if family_explanation:
                explanation["educational_context"][
                    "pattern_family"
                ] = family_explanation

        return explanation

    def get_pattern_teaching_points(
        self, pattern_matches: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate teaching points based on found patterns.

        Args:
            pattern_matches: List of pattern match results

        Returns:
            List of educational teaching points
        """
        teaching_points = []

        for match in pattern_matches:
            pattern_name = match.get("name", "").lower()
            family = match.get("family", "").lower()

            # Cadence teaching points
            if family == "cadence":
                if "pac" in pattern_name:
                    teaching_points.append(
                        "Perfect Authentic Cadence (PAC) provides the strongest sense "
                        "of closure because both chords are in root position and the "
                        "soprano resolves to the tonic."
                    )
                elif "iac" in pattern_name:
                    teaching_points.append(
                        "Imperfect Authentic Cadence (IAC) is weaker than PAC because "
                        "either a chord is inverted or the soprano doesn't end on "
                        "the tonic."
                    )
                elif "half" in pattern_name:
                    teaching_points.append(
                        "Half Cadence creates expectation by ending on the "
                        "dominant (V), "
                        "leaving the phrase feeling incomplete and needing "
                        "continuation."
                    )
                elif "plagal" in pattern_name:
                    teaching_points.append(
                        "Plagal Cadence (IV-I) has a distinctive sound often "
                        "associated with "
                        "hymns and provides gentler closure than authentic "
                        "cadences."
                    )

            # Sequence teaching points
            elif family == "sequence":
                if "circle of fifths" in pattern_name:
                    teaching_points.append(
                        "Circle of fifths progressions create strong forward "
                        "momentum through "
                        "root motion by descending fifths (or ascending "
                        "fourths)."
                    )

        return teaching_points

    def _extract_cadence_type(self, pattern_name: str) -> Optional[str]:
        """Extract cadence type abbreviation from pattern name."""
        name_lower = pattern_name.lower()

        if "perfect authentic" in name_lower or "pac" in name_lower:
            return "PAC"
        elif "imperfect authentic" in name_lower or "iac" in name_lower:
            return "IAC"
        elif "half cadence" in name_lower or "half" in name_lower:
            return "HC"
        elif "plagal" in name_lower:
            return "PC"
        elif "deceptive" in name_lower:
            return "DC"
        elif "phrygian" in name_lower:
            return "Phrygian_HC"
        elif "evaded" in name_lower:
            return "Evaded"
        elif "cadential" in name_lower and "6" in name_lower:
            return "Cadential_6_4"

        return None

    def _extract_soprano_degree(self, pattern_name: str) -> Optional[int]:
        """Extract soprano scale degree from pattern name."""
        import re

        match = re.search(r"soprano on (\d+)", pattern_name.lower())
        if match:
            return int(match.group(1))
        return None

    def _get_soprano_context(self, degree: int) -> str:
        """Get context about soprano scale degree in cadences."""
        if degree == 1:
            return (
                "Soprano ending on scale degree 1 (tonic) provides the "
                "strongest closure."
            )
        elif degree == 3:
            return (
                "Soprano ending on scale degree 3 (mediant) creates weaker "
                "closure than tonic."
            )
        elif degree == 5:
            return (
                "Soprano ending on scale degree 5 (dominant) provides less "
                "stable closure."
            )
        else:
            return f"Soprano ending on scale degree {degree}."

    def _get_degree_name(self, degree: int) -> str:
        """Get the name of a scale degree."""
        names = {
            1: "Tonic",
            2: "Supertonic",
            3: "Mediant",
            4: "Subdominant",
            5: "Dominant",
            6: "Submediant",
            7: "Leading tone",
        }
        return names.get(degree, f"Degree {degree}")

    def _calculate_note_in_key(self, key_root: str, degree: int) -> str:
        """Calculate the note name for a scale degree in a given key."""
        # Simple chromatic mapping (would be enhanced for all keys)
        if key_root == "C":
            notes = ["C", "D", "E", "F", "G", "A", "B"]
            return notes[(degree - 1) % 7] if 1 <= degree <= 7 else f"Degree {degree}"

        # For other keys, would need more sophisticated calculation
        return f"Degree {degree} in {key_root}"

    def _get_family_explanation(self, family: str) -> Optional[str]:
        """Get explanation for pattern family."""
        family_explanations = {
            "cadence": (
                "Cadences are harmonic progressions that provide closure "
                "or punctuation in musical phrases."
            ),
            "sequence": (
                "Sequences are patterns where a melodic or harmonic idea "
                "is repeated at different pitch levels."
            ),
            "prolongation": (
                "Prolongational patterns extend or elaborate a single harmony "
                "over time."
            ),
            "chromatic_pd": (
                "Chromatic predominants use altered chords to enhance motion "
                "toward the dominant."
            ),
            "mixture_modal": (
                "Modal mixture borrows chords from the parallel mode "
                "(major/minor) for color."
            ),
        }

        return family_explanations.get(family.lower())
