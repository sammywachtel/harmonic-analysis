"""
Enhanced modal analysis engine with evidence-based confidence scoring.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..utils.chord_logic import ChordMatch, find_chord_matches
from ..utils.scales import NOTE_TO_PITCH_CLASS, get_parent_key


@dataclass
class ModalEvidence:
    """Evidence supporting modal interpretation."""

    type: str  # 'structural', 'cadential', 'intervallic', 'contextual'
    description: str
    strength: float  # 0.0 to 1.0


@dataclass
class ModalAnalysisResult:
    """Result of enhanced modal analysis."""

    detected_tonic_center: str
    parent_key_signature: str
    mode_name: str
    roman_numerals: List[str]
    confidence: float
    evidence: List[ModalEvidence]
    characteristics: List[str]


@dataclass
class ModalPattern:
    """Definition of a modal characteristic pattern."""

    pattern: str
    modes: List[str]
    strength: float
    context: str  # 'structural' or 'cadential'


class EnhancedModalAnalyzer:
    """Enhanced modal analyzer with pattern recognition and evidence scoring."""

    def __init__(self) -> None:
        # Functional patterns that should NOT be detected as modal
        self.functional_patterns = [
            {"pattern": "I-V-I", "strength": 0.95, "type": "authentic_cadence"},
            {"pattern": "I-IV-V-I", "strength": 0.95, "type": "functional_progression"},
            {"pattern": "I-vi-IV-V", "strength": 0.90, "type": "pop_progression"},
            {"pattern": "vi-IV-I-V", "strength": 0.90, "type": "pop_progression"},
            {"pattern": "ii-V-I", "strength": 0.85, "type": "jazz_cadence"},
            {"pattern": "IV-V-I", "strength": 0.90, "type": "plagal_cadence"},
            {"pattern": "V-I", "strength": 0.85, "type": "dominant_resolution"},
        ]

        # Known modal characteristic patterns
        self.modal_patterns = [
            # Ionian patterns
            ModalPattern("I-IV-I", ["Ionian"], 0.80, "structural"),
            ModalPattern("I-vi-IV-V", ["Ionian"], 0.75, "structural"),
            # Mixolydian patterns (major tonic with bVII)
            ModalPattern("I-bVII-IV-I", ["Mixolydian"], 0.95, "structural"),
            ModalPattern("I-bVII-I", ["Mixolydian"], 0.90, "structural"),
            ModalPattern("bVII-I", ["Mixolydian"], 0.85, "cadential"),
            ModalPattern("I-IV-bVII-I", ["Mixolydian"], 0.88, "structural"),
            # Dorian patterns (minor tonic with major IV)
            ModalPattern("i-IV-i", ["Dorian"], 0.90, "structural"),
            ModalPattern("i-IV-bVII-i", ["Dorian"], 0.95, "structural"),
            ModalPattern("i-bVII-IV-i", ["Dorian"], 0.95, "structural"),
            ModalPattern("IV-i", ["Dorian"], 0.80, "cadential"),
            # Phrygian patterns (minor tonic with bII)
            ModalPattern("i-bII-i", ["Phrygian"], 0.95, "structural"),
            ModalPattern("bII-i", ["Phrygian"], 0.90, "cadential"),
            ModalPattern("i-bII-bVII-i", ["Phrygian"], 0.95, "structural"),
            # Lydian patterns (major tonic with II or #IV)
            ModalPattern("I-II-I", ["Lydian"], 0.90, "structural"),
            ModalPattern("I-#IV-I", ["Lydian"], 0.95, "structural"),
            ModalPattern("I-II-V-I", ["Lydian"], 0.92, "structural"),
            # Aeolian patterns (natural minor)
            ModalPattern("i-bVII-bVI-bVII", ["Aeolian"], 0.85, "structural"),
            ModalPattern("i-bVI-bVII-i", ["Aeolian"], 0.88, "structural"),
            # Locrian patterns (rare but distinctive)
            ModalPattern("i-bII-bV", ["Locrian"], 0.90, "structural"),
        ]

    def analyze_modal_characteristics(
        self, chord_symbols: List[str], parent_key: Optional[str] = None
    ) -> Optional[ModalAnalysisResult]:
        """
        Analyze chord progression for modal characteristics.

        Args:
            chord_symbols: List of chord symbols to analyze
            parent_key: Optional parent key context

        Returns:
            ModalAnalysisResult if modal characteristics detected, None otherwise
        """
        if not chord_symbols:
            return None

        # Parse chords
        chord_matches = find_chord_matches(chord_symbols)

        # Try different potential tonic centers
        potential_tonics = self._identify_potential_tonics(chord_matches)

        best_analysis = None
        best_confidence = 0.0

        for tonic_candidate in potential_tonics:
            analysis = self._analyze_for_tonic(
                chord_matches, tonic_candidate, parent_key
            )
            if analysis and analysis.confidence > best_confidence:
                best_analysis = analysis
                best_confidence = analysis.confidence

        # Only return if confidence meets threshold
        if best_analysis and best_analysis.confidence >= 0.6:
            return best_analysis

        return None

    def _identify_potential_tonics(self, chord_matches: List[ChordMatch]) -> List[str]:
        """Identify potential tonic centers from chord progression."""
        candidates = []

        # First chord is often tonic
        if chord_matches:
            candidates.append(chord_matches[0].root)

        # Last chord is often tonic
        if len(chord_matches) > 1:
            last_root = chord_matches[-1].root
            if last_root not in candidates:
                candidates.append(last_root)

        # Most frequent chord root
        root_counts: Dict[str, int] = {}
        for chord in chord_matches:
            root_counts[chord.root] = root_counts.get(chord.root, 0) + 1

        most_frequent = max(root_counts.items(), key=lambda x: x[1])[0]
        if most_frequent not in candidates:
            candidates.append(most_frequent)

        return candidates

    def _analyze_for_tonic(
        self,
        chord_matches: List[ChordMatch],
        tonic_candidate: str,
        parent_key: Optional[str],
    ) -> Optional[ModalAnalysisResult]:
        """Analyze progression assuming a specific tonic center."""

        # Generate Roman numerals relative to candidate tonic
        roman_numerals = self._generate_roman_numerals(chord_matches, tonic_candidate)

        # Check for modal patterns
        pattern_matches = self._find_pattern_matches(roman_numerals)

        if not pattern_matches:
            return None

        # Determine most likely mode
        mode_scores: Dict[str, float] = {}
        evidence: List[ModalEvidence] = []

        for pattern_match in pattern_matches:
            for mode in pattern_match["pattern"].modes:
                mode_scores[mode] = (
                    mode_scores.get(mode, 0) + pattern_match["pattern"].strength
                )

                evidence.append(
                    ModalEvidence(
                        type=pattern_match["pattern"].context,
                        description=(
                            f"{pattern_match['pattern'].pattern} pattern supports "
                            f"{mode}"
                        ),
                        strength=pattern_match["pattern"].strength,
                    )
                )

        if not mode_scores:
            return None

        # Select mode with highest score
        best_mode = max(mode_scores.items(), key=lambda x: x[1])[0]

        # Calculate parent key signature
        try:
            parent_key_sig = get_parent_key(tonic_candidate, best_mode)
        except ValueError:
            parent_key_sig = f"{tonic_candidate} major"  # fallback

        # Calculate overall confidence
        confidence = self._calculate_modal_confidence(
            pattern_matches, chord_matches, tonic_candidate, evidence
        )

        # Generate characteristics
        characteristics = self._generate_characteristics(pattern_matches, best_mode)

        return ModalAnalysisResult(
            detected_tonic_center=tonic_candidate,
            parent_key_signature=parent_key_sig,
            mode_name=best_mode,
            roman_numerals=roman_numerals,
            confidence=confidence,
            evidence=evidence,
            characteristics=characteristics,
        )

    def _generate_roman_numerals(
        self, chord_matches: List[ChordMatch], tonic: str
    ) -> List[str]:
        """Generate Roman numerals relative to a tonic center."""
        if tonic not in NOTE_TO_PITCH_CLASS:
            return [chord.chord_symbol for chord in chord_matches]

        tonic_pitch = NOTE_TO_PITCH_CLASS[tonic]
        romans = []

        for chord in chord_matches:
            interval = (chord.root_pitch - tonic_pitch) % 12

            # Basic interval to Roman numeral mapping
            interval_to_roman = {
                0: "I",  # Unison
                1: "bII",  # Minor second
                2: "II",  # Major second
                3: "bIII",  # Minor third
                4: "III",  # Major third
                5: "IV",  # Perfect fourth
                6: "bV",  # Tritone
                7: "V",  # Perfect fifth
                8: "bVI",  # Minor sixth
                9: "VI",  # Major sixth
                10: "bVII",  # Minor seventh
                11: "VII",  # Major seventh
            }

            base_roman = interval_to_roman.get(interval, "X")

            # Adjust case based on chord quality
            if chord.quality == "minor":
                base_roman = base_roman.lower()
            elif chord.quality == "diminished":
                base_roman = base_roman.lower() + "°"
            elif chord.quality == "augmented":
                base_roman = base_roman + "+"

            romans.append(base_roman)

        return romans

    def _find_pattern_matches(self, roman_numerals: List[str]) -> List[Dict[str, Any]]:
        """Find matching modal patterns in Roman numeral sequence."""
        pattern_matches = []
        roman_string = "-".join(roman_numerals)

        for pattern in self.modal_patterns:
            if pattern.pattern in roman_string:
                pattern_matches.append(
                    {"pattern": pattern, "position": roman_string.find(pattern.pattern)}
                )

        return pattern_matches

    def _calculate_modal_confidence(
        self,
        pattern_matches: List[Dict[str, Any]],
        chord_matches: List[ChordMatch],
        tonic: str,
        evidence: List[ModalEvidence],
    ) -> float:
        """Calculate confidence score for modal analysis."""
        if not pattern_matches:
            return 0.0

        # Base confidence from pattern strength
        strengths: List[float] = [
            float(pm["pattern"].strength) for pm in pattern_matches
        ]
        pattern_confidence: float = sum(strengths) / len(strengths)

        # Boost for structural emphasis on tonic
        tonic_emphasis = self._calculate_tonic_emphasis(chord_matches, tonic)

        # Boost for multiple evidence types
        evidence_types = set(e.type for e in evidence)
        evidence_bonus = len(evidence_types) * 0.1

        # Combine factors
        total_confidence = min(
            pattern_confidence + tonic_emphasis * 0.2 + evidence_bonus, 1.0
        )

        return total_confidence

    def _calculate_tonic_emphasis(
        self, chord_matches: List[ChordMatch], tonic: str
    ) -> float:
        """Calculate how much emphasis the tonic receives in the progression."""
        if not chord_matches:
            return 0.0

        tonic_count = sum(1 for chord in chord_matches if chord.root == tonic)
        tonic_ratio = tonic_count / len(chord_matches)

        # Bonus for tonic in structural positions (first/last)
        structural_bonus = 0.0
        if chord_matches[0].root == tonic:
            structural_bonus += 0.3
        if len(chord_matches) > 1 and chord_matches[-1].root == tonic:
            structural_bonus += 0.3

        return min(tonic_ratio + structural_bonus, 1.0)

    def _generate_characteristics(
        self, pattern_matches: List[Dict[str, Any]], mode: str
    ) -> List[str]:
        """Generate list of modal characteristics found."""
        characteristics = []

        for pm in pattern_matches:
            pattern = pm["pattern"]
            if pattern.context == "cadential":
                characteristics.append(
                    f"{pattern.pattern} cadence ({mode} characteristic)"
                )
            else:
                characteristics.append(
                    f"{pattern.pattern} progression ({mode} pattern)"
                )

        return characteristics
