"""
Enhanced Modal Analyzer

Implements robust modal detection with confidence-based analysis

Key Improvements:
- Structural pattern recognition (I-bVII-IV-I, etc.)
- Tonal center weighting (first/last chord emphasis)
- Modal characteristic detection (bVII-I, bII-I cadences)
- Evidence-based confidence scoring
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from ..analysis_types import EvidenceType
from ..utils.chord_inversions import analyze_chord_inversion
from ..utils.scales import KEY_SIGNATURES

# EvidenceType moved to types.py for shared usage


class PatternContext(Enum):
    STRUCTURAL = "structural"
    CADENTIAL = "cadential"


@dataclass
class ModalEvidence:
    """Evidence supporting modal interpretation"""

    type: EvidenceType
    description: str
    strength: float  # 0.0 to 1.0


@dataclass
class ModalPattern:
    """Known modal characteristic patterns"""

    pattern: str
    modes: List[str]
    strength: float
    context: PatternContext


@dataclass
class ChordAnalysis:
    """Analyzed chord with components"""

    symbol: str
    root: str
    quality: str
    pitch_class: int
    bass_pitch_class: Optional[int] = None  # For inversions


@dataclass
class ModalAnalysisResult:
    """Result of modal analysis"""

    detected_tonic_center: str
    parent_key_signature: str
    mode_name: str
    roman_numerals: List[str]
    confidence: float
    evidence: List[ModalEvidence]
    characteristics: List[str]


class EnhancedModalAnalyzer:
    """Enhanced Modal Analyzer with sophisticated pattern recognition"""

    # Note to pitch class mapping (C=0, C#=1, D=2, etc.)
    NOTE_TO_PITCH_CLASS = {
        "C": 0,
        "C#": 1,
        "Db": 1,
        "D": 2,
        "D#": 3,
        "Eb": 3,
        "E": 4,
        "F": 5,
        "F#": 6,
        "Gb": 6,
        "G": 7,
        "G#": 8,
        "Ab": 8,
        "A": 9,
        "A#": 10,
        "Bb": 10,
        "B": 11,
    }

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
            {"pattern": "vi-V-I", "strength": 0.85, "type": "deceptive_resolution"},
            {"pattern": "I-vi-ii-V", "strength": 0.88, "type": "circle_progression"},
            {"pattern": "I-ii-V-I", "strength": 0.90, "type": "extended_functional"},
            {"pattern": "IV-I-V-I", "strength": 0.85, "type": "plagal_functional"},
        ]

        # Known modal characteristic patterns
        self.modal_patterns = [
            # Ionian patterns
            ModalPattern("I-IV-I", ["Ionian"], 0.80, PatternContext.STRUCTURAL),
            ModalPattern("I-IV", ["Ionian"], 0.75, PatternContext.STRUCTURAL),
            ModalPattern("I-vi-IV-V", ["Ionian"], 0.75, PatternContext.STRUCTURAL),
            # Dorian patterns
            ModalPattern("i-IV", ["Dorian"], 0.80, PatternContext.STRUCTURAL),
            ModalPattern("i-IV-i", ["Dorian"], 0.90, PatternContext.STRUCTURAL),
            ModalPattern("i-IV-bVII-i", ["Dorian"], 0.95, PatternContext.STRUCTURAL),
            ModalPattern("i-bVII-IV-i", ["Dorian"], 0.95, PatternContext.STRUCTURAL),
            ModalPattern("i-IV-bVII", ["Dorian"], 0.85, PatternContext.STRUCTURAL),
            ModalPattern("IV-i", ["Dorian"], 0.80, PatternContext.CADENTIAL),
            # Mixolydian patterns
            ModalPattern(
                "I-bVII-IV-I", ["Mixolydian"], 0.95, PatternContext.STRUCTURAL
            ),
            ModalPattern("I-bVII-I", ["Mixolydian"], 0.90, PatternContext.STRUCTURAL),
            ModalPattern("bVII-I", ["Mixolydian"], 0.85, PatternContext.CADENTIAL),
            ModalPattern(
                "I-IV-bVII-I", ["Mixolydian"], 0.88, PatternContext.STRUCTURAL
            ),
            ModalPattern("I-bVII-IV", ["Mixolydian"], 0.82, PatternContext.STRUCTURAL),
            # Phrygian patterns
            ModalPattern("i-bII-i", ["Phrygian"], 0.95, PatternContext.STRUCTURAL),
            ModalPattern("bII-i", ["Phrygian"], 0.90, PatternContext.CADENTIAL),
            ModalPattern("i-bII-bVII-i", ["Phrygian"], 0.95, PatternContext.STRUCTURAL),
            ModalPattern("i-bII-bVII", ["Phrygian"], 0.88, PatternContext.STRUCTURAL),
            # Lydian patterns
            ModalPattern("I-II-I", ["Lydian"], 0.90, PatternContext.STRUCTURAL),
            ModalPattern("I-#IV-I", ["Lydian"], 0.95, PatternContext.STRUCTURAL),
            ModalPattern("I-II-V-I", ["Lydian"], 0.92, PatternContext.STRUCTURAL),
            ModalPattern("I-II-I-II", ["Lydian"], 0.88, PatternContext.STRUCTURAL),
            # Aeolian patterns
            ModalPattern("i-bVI-bVII-i", ["Aeolian"], 0.90, PatternContext.STRUCTURAL),
            ModalPattern("i-bVII-iv-i", ["Aeolian"], 0.95, PatternContext.STRUCTURAL),
            ModalPattern("i-bVII-bVI-i", ["Aeolian"], 0.88, PatternContext.STRUCTURAL),
            ModalPattern("i-iv-bVII-i", ["Aeolian"], 0.92, PatternContext.STRUCTURAL),
            ModalPattern("i-bVI-iv-i", ["Aeolian"], 0.85, PatternContext.STRUCTURAL),
            ModalPattern("bVII-i", ["Aeolian"], 0.80, PatternContext.CADENTIAL),
            # Locrian patterns
            ModalPattern("i°-bII-i°", ["Locrian"], 0.95, PatternContext.STRUCTURAL),
            ModalPattern("i°-bII-v-i°", ["Locrian"], 0.95, PatternContext.STRUCTURAL),
            ModalPattern("bII-i°", ["Locrian"], 0.90, PatternContext.CADENTIAL),
        ]

    def analyze_modal_characteristics(
        self, chord_symbols: List[str], parent_key: Optional[str] = None
    ) -> Optional[ModalAnalysisResult]:
        """
        Analyze chord progression for modal characteristics

        Args:
            chord_symbols: List of chord symbols (e.g., ['Am', 'F', 'C', 'G'])
            parent_key: Optional parent key context (e.g., 'C major')

        Returns:
            ModalAnalysisResult if modal characteristics detected, None otherwise
        """
        # Handle edge cases
        if not chord_symbols:
            return None

        # FUNCTIONAL HARMONY PRE-SCREENING
        # This is here to prevent returning a modal analysis if the functional
        # analysis is very strong. CONSIDER... letting it do modal analysis anyway?
        if parent_key:
            functional_roman_numerals = self._generate_functional_roman_numerals(
                chord_symbols, parent_key
            )
            if functional_roman_numerals:
                functional_strength = self._detect_functional_patterns(
                    functional_roman_numerals
                )
                if functional_strength > 0.8:
                    return (
                        None  # Block modal analysis for clear functional progressions
                    )

        if len(chord_symbols) == 1:
            return None  # Single chord - not enough for modal analysis

        if all(chord == chord_symbols[0] for chord in chord_symbols):
            return None  # All same chord - static harmony, not modal

        # Parse chords with error handling
        chord_analyses = []
        for symbol in chord_symbols:
            try:
                analysis = self._parse_chord(symbol)
                chord_analyses.append(analysis)
            except Exception as e:
                print(f"Warning: Failed to parse chord symbol: {symbol} - {e}")
                continue

        # Check if we have enough valid chords after parsing
        if len(chord_analyses) < 2:
            return None

        # PARENT KEY VALIDATION
        validation_result = None
        if parent_key:
            validation_result = self._validate_chords_against_parent_key(
                chord_analyses, parent_key
            )

            # If too many chords are outside the key, reject analysis
            if validation_result["outside_key_ratio"] > 0.7:
                # More than 70% of chords are outside the key - invalid parent key
                return None

        # Detect potential tonal centers
        tonic_candidates = self._detect_tonic_candidates(chord_analyses, parent_key)

        # Analyze each tonic candidate
        results = []
        for candidate in tonic_candidates:
            result = self._analyze_with_tonic(
                chord_analyses,
                candidate["tonic"],
                candidate["parent_key"],
                parent_key is not None,
                validation_result,
            )
            if result:
                results.append(result)

        if not results:
            return None

        # CRITICAL FIX: Check for foil patterns across ALL candidates before selection
        foil_results = [
            result
            for result in results
            if self._detect_foil_patterns(result.roman_numerals)
        ]

        # If ANY candidate is detected as foil, override with low confidence result
        if foil_results:
            foil_result = foil_results[0]
            foil_result.confidence = 0.3  # Force low confidence for foil patterns
            return foil_result if foil_result.confidence >= 0.4 else None

        # Select best result based on confidence
        best_result = max(results, key=lambda r: r.confidence)

        # Lower threshold for vamp patterns to handle valid two-chord progressions
        confidence_threshold = 0.25 if len(chord_analyses) == 2 else 0.4
        return best_result if best_result.confidence >= confidence_threshold else None

    def _detect_tonic_candidates(
        self, chord_analyses: List[ChordAnalysis], parent_key: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Detect potential tonal centers based on structural analysis"""
        candidates: Dict[str, float] = {}

        # Heavily weight first and last chords (structural importance)
        first_chord = chord_analyses[0]
        last_chord = chord_analyses[-1]

        candidates[first_chord.root] = candidates.get(first_chord.root, 0) + 3.0
        candidates[last_chord.root] = candidates.get(last_chord.root, 0) + 3.0

        # If first and last are the same, give massive weight
        if first_chord.root == last_chord.root:
            candidates[first_chord.root] = candidates.get(first_chord.root, 0) + 5.0

        # Weight other chords less
        for chord in chord_analyses:
            candidates[chord.root] = candidates.get(chord.root, 0) + 0.5

        # Sort candidates by weight
        sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)

        # Build result array with appropriate parent keys
        results = []

        # Add top candidate with provided parent key or inferred
        top_candidate = sorted_candidates[0][0]
        results.append(
            {
                "tonic": top_candidate,
                "parent_key": parent_key or self._infer_parent_key(top_candidate),
            }
        )

        # If parent key provided and different from top candidate, add it as alternative
        if parent_key:
            parent_key_root = self._extract_key_root(parent_key)
            if parent_key_root != top_candidate:
                results.append({"tonic": parent_key_root, "parent_key": parent_key})

        return results[:2]  # Top 2 candidates

    def _analyze_with_tonic(
        self,
        chord_analyses: List[ChordAnalysis],
        tonic: str,
        parent_key: str,
        was_parent_key_provided: bool = True,
        validation_result: Optional[Dict[str, Any]] = None,
    ) -> Optional[ModalAnalysisResult]:
        """Analyze progression with specific tonic center"""
        tonic_pitch_class = self.NOTE_TO_PITCH_CLASS.get(tonic)
        if tonic_pitch_class is None:
            raise ValueError(f"Invalid tonic: {tonic}")

        # Generate Roman numerals relative to tonic
        roman_numerals = [
            self._generate_modal_roman_numeral(chord, tonic_pitch_class)
            for chord in chord_analyses
        ]

        # Detect modal patterns
        pattern_results = self._detect_modal_patterns(roman_numerals)

        # Collect evidence
        evidence = self._collect_evidence(
            chord_analyses, roman_numerals, tonic, parent_key
        )

        # Calculate confidence
        confidence = self._calculate_confidence(
            evidence, pattern_results, roman_numerals, chord_analyses, parent_key
        )

        # Determine mode name
        mode_name = self._determine_mode_name(
            pattern_results, evidence, tonic, parent_key, roman_numerals, chord_analyses
        )

        # Identify characteristics
        characteristics = self._identify_modal_characteristics(roman_numerals)

        # Apply foil detection to reduce confidence for functional patterns
        # masquerading as modal
        final_confidence = confidence
        is_detected_as_foil = self._detect_foil_patterns(roman_numerals)

        if is_detected_as_foil:
            final_confidence = min(
                confidence, 0.3
            )  # Reduce confidence well below threshold for foil patterns
        elif "-".join(roman_numerals) == "I-IV-I":
            # Special boost for clear Ionian pattern that isn't functional
            final_confidence = max(confidence, 0.75)

        # CRITICAL FIX: Reduce confidence for ambiguous patterns without
        # parent key context
        if not was_parent_key_provided:
            # Without explicit parent key, modal identification lacks harmonic context
            final_confidence = min(
                final_confidence, 0.65
            )  # Cap confidence for ambiguous cases

        # PARENT KEY VALIDATION PENALTIES
        if validation_result is not None:
            outside_key_ratio = validation_result["outside_key_ratio"]
            print(
                f"🔍 MODAL VALIDATOR: outside_key_ratio={outside_key_ratio:.3f}, "
                f"confidence before penalty={final_confidence:.3f}"
            )

            # Apply confidence penalties based on how many chords are outside the key
            if outside_key_ratio > 0.5:
                final_confidence *= 0.3  # Heavy penalty for >50% outside key
                print(
                    f"🔍 MODAL VALIDATOR: Applied heavy penalty (0.3), "
                    f"new confidence={final_confidence:.3f}"
                )
            elif outside_key_ratio > 0.3:
                final_confidence *= 0.5  # Moderate penalty for >30% outside key
                print(
                    f"🔍 MODAL VALIDATOR: Applied moderate penalty (0.5), "
                    f"new confidence={final_confidence:.3f}"
                )
            elif outside_key_ratio > 0.1:
                final_confidence *= 0.7  # Light penalty for >10% outside key
                print(
                    f"🔍 MODAL VALIDATOR: Applied light penalty (0.7), "
                    f"new confidence={final_confidence:.3f}"
                )

            # Add contextual evidence about key validation
            if outside_key_ratio > 0.1:
                key_evidence = ModalEvidence(
                    type=EvidenceType.CONTEXTUAL,
                    description=f"{int(outside_key_ratio * 100)}% of chords fall "
                    f"outside {parent_key}",
                    strength=0.3
                    + (outside_key_ratio * 0.4),  # Strength increases with violations
                )
                evidence.append(key_evidence)

        # FIX: Correct parent key based on determined mode
        corrected_parent_key = self._get_correct_parent_key(
            mode_name, tonic, parent_key
        )

        return ModalAnalysisResult(
            detected_tonic_center=tonic,
            parent_key_signature=corrected_parent_key,
            mode_name=mode_name,
            roman_numerals=roman_numerals,
            confidence=min(final_confidence, 0.95),  # Cap at 0.95 to show uncertainty
            evidence=evidence,
            characteristics=characteristics,
        )

    def _generate_modal_roman_numeral(
        self, chord: ChordAnalysis, tonic_pitch_class: int
    ) -> str:
        """Generate Roman numeral relative to tonic center"""
        interval = (chord.pitch_class - tonic_pitch_class + 12) % 12

        # Determine base Roman numeral based on interval and chord quality
        base_roman_numerals = {
            0: {"major": "I", "minor": "i", "diminished": "i°"},
            1: {"major": "bII", "minor": "bii", "diminished": "bii°"},
            2: {"major": "II", "minor": "ii", "diminished": "ii°"},
            3: {"major": "bIII", "minor": "biii", "diminished": "biii°"},
            4: {"major": "III", "minor": "iii", "diminished": "iii°"},
            5: {"major": "IV", "minor": "iv", "diminished": "iv°"},
            6: {"major": "#IV", "minor": "#iv", "diminished": "#iv°"},
            7: {"major": "V", "minor": "v", "diminished": "v°"},
            8: {"major": "bVI", "minor": "bvi", "diminished": "bvi°"},
            9: {"major": "VI", "minor": "vi", "diminished": "vi°"},
            10: {"major": "bVII", "minor": "bvii", "diminished": "bvii°"},
            11: {"major": "VII", "minor": "vii", "diminished": "vii°"},
        }

        roman_options = base_roman_numerals.get(interval)
        if not roman_options:
            return f"?{interval}"

        # Choose appropriate Roman numeral based on chord quality
        base_roman = ""
        if chord.quality in ["major", "major7", "dominant7"]:
            base_roman = roman_options["major"]
        elif chord.quality in ["minor", "minor7"]:
            base_roman = roman_options["minor"]
        elif chord.quality in ["diminished", "half_diminished"]:
            base_roman = roman_options["diminished"]
        elif chord.quality == "augmented":
            base_roman = roman_options["major"] + "+"
        elif chord.quality == "suspended":
            base_roman = roman_options["major"] + "sus"
        else:
            # Default to major/minor based on interval position
            base_roman = (
                roman_options["major"] if interval == 0 else roman_options["minor"]
            )

        # Add inversion notation if present
        if chord.bass_pitch_class is not None:
            inversion_info = analyze_chord_inversion(
                chord.pitch_class,
                chord.bass_pitch_class,
                chord.symbol,  # Pass original symbol for 7th chord detection
            )
            figured_bass = inversion_info["figured_bass"]
            if isinstance(figured_bass, str):
                base_roman += figured_bass

        return base_roman

    def _detect_modal_patterns(self, roman_numerals: List[str]) -> List[Dict[str, Any]]:
        """Detect known modal patterns in Roman numeral sequence"""
        roman_string = "-".join(roman_numerals)
        results: List[Dict[str, Any]] = []

        for pattern in self.modal_patterns:
            if pattern.pattern in roman_string:
                results.append({"pattern": pattern, "matches": 1})

            # Check for partial matches
            pattern_parts = pattern.pattern.split("-")
            partial_matches = 0

            for i in range(len(roman_numerals) - len(pattern_parts) + 1):
                segment = "-".join(roman_numerals[i : i + len(pattern_parts)])
                if segment == pattern.pattern:
                    partial_matches += 1

            if partial_matches > 0 and not any(
                r["pattern"].pattern == pattern.pattern for r in results
            ):
                results.append({"pattern": pattern, "matches": partial_matches})

        return sorted(
            results, key=lambda x: x["pattern"].strength * x["matches"], reverse=True
        )

    def _collect_evidence(
        self,
        chord_analyses: List[ChordAnalysis],
        roman_numerals: List[str],
        tonic: str,
        parent_key: str,
    ) -> List[ModalEvidence]:
        """Collect evidence for modal analysis"""
        evidence = []

        # Structural evidence: starts and ends on same chord
        if chord_analyses[0].root == chord_analyses[-1].root:
            evidence.append(
                ModalEvidence(
                    type=EvidenceType.STRUCTURAL,
                    description=(
                        f"Progression starts and ends on {chord_analyses[0].root}, "
                        f"suggesting {chord_analyses[0].root} as tonal center"
                    ),
                    strength=0.8,
                )
            )

        # Cadential evidence: modal cadences
        for i in range(len(roman_numerals) - 1):
            current = roman_numerals[i]
            next_chord = roman_numerals[i + 1]

            if current == "bVII" and next_chord in ["I", "i"]:
                evidence.append(
                    ModalEvidence(
                        type=EvidenceType.CADENTIAL,
                        description=(
                            "bVII-I cadence (characteristic of Mixolydian mode)"
                        ),
                        strength=0.9,
                    )
                )

            if current == "bII" and next_chord in ["I", "i"]:
                evidence.append(
                    ModalEvidence(
                        type=EvidenceType.CADENTIAL,
                        description="bII-I cadence (characteristic of Phrygian mode)",
                        strength=0.9,
                    )
                )

        # Intervallic evidence: characteristic modal intervals
        if "bVII" in roman_numerals:
            evidence.append(
                ModalEvidence(
                    type=EvidenceType.INTERVALLIC,
                    description="Contains bVII chord (modal characteristic)",
                    strength=0.7,
                )
            )

        if "bII" in roman_numerals:
            evidence.append(
                ModalEvidence(
                    type=EvidenceType.INTERVALLIC,
                    description="Contains bII chord (modal characteristic)",
                    strength=0.7,
                )
            )

        # FIX: Add weak evidence for basic tonic relationships that could be modal
        # This ensures progressions like I-iii get at least minimal modal alternatives
        roman_string = "-".join(roman_numerals)
        if "I-iii" in roman_string or "i-III" in roman_string:
            evidence.append(
                ModalEvidence(
                    type=EvidenceType.INTERVALLIC,
                    description="Contains tonic-mediant relationship (weak modal"
                    "character)",
                    strength=0.25,  # Low strength - enough to generate an alternative
                )
            )
        if "I-vi" in roman_string or "i-VI" in roman_string:
            evidence.append(
                ModalEvidence(
                    type=EvidenceType.INTERVALLIC,
                    description="Contains tonic-submediant relationship (weak modal"
                    "character)",
                    strength=0.25,
                )
            )

        # Contextual evidence: parent key relationship
        if parent_key and tonic != self._extract_key_root(parent_key):
            evidence.append(
                ModalEvidence(
                    type=EvidenceType.CONTEXTUAL,
                    description=(
                        f"Tonal center ({tonic}) differs from parent key "
                        f"({parent_key}), "
                        "suggesting modal interpretation"
                    ),
                    strength=0.6,
                )
            )

        # Vamp pattern evidence
        roman_string = "-".join(roman_numerals)
        if len(chord_analyses) == 2:
            vamp_patterns = {
                "I-IV": (
                    "I-IV vamp pattern (characteristic of Ionian modal color)",
                    0.7,
                ),
                "i-IV": (
                    "i-IV vamp pattern (characteristic of Dorian modal color)",
                    0.8,
                ),
                "I-bVII": (
                    "I-bVII vamp pattern (characteristic of Mixolydian modal color)",
                    0.85,
                ),
                "i-bII": (
                    "i-bII vamp pattern (characteristic of Phrygian modal color)",
                    0.85,
                ),
                "I-II": (
                    "I-II vamp pattern (characteristic of Lydian modal color)",
                    0.8,
                ),
            }

            if roman_string in vamp_patterns:
                description, strength = vamp_patterns[roman_string]
                evidence.append(
                    ModalEvidence(
                        type=EvidenceType.STRUCTURAL,
                        description=description,
                        strength=strength,
                    )
                )

        return evidence

    def _generate_functional_roman_numerals(
        self, chord_symbols: List[str], parent_key: str
    ) -> Optional[List[str]]:
        """Generate Roman numerals relative to parent key (for functional analysis)"""
        try:
            # Extract parent key root (e.g., "C" from "C major")
            parent_key_root = parent_key.split(" ")[0]
            parent_key_pitch_class = self.NOTE_TO_PITCH_CLASS.get(parent_key_root)
            if parent_key_pitch_class is None:
                return None

            is_minor_key = "minor" in parent_key

            # Generate Roman numerals with proper functional harmony chord qualities
            result = []
            for chord_symbol in chord_symbols:
                try:
                    chord = self._parse_chord(chord_symbol)
                    roman = self._generate_functional_roman_numeral(
                        chord, parent_key_pitch_class, is_minor_key
                    )
                    result.append(roman)
                except Exception:
                    result.append("?")

            return result
        except Exception:
            return None

    def _generate_functional_roman_numeral(
        self, chord: ChordAnalysis, tonic_pitch_class: int, is_minor_key: bool = False
    ) -> str:
        """Generate Roman numeral with proper functional harmony chord qualities"""
        interval = (chord.pitch_class - tonic_pitch_class + 12) % 12

        # Define diatonic chord qualities for major and minor keys
        major_key_qualities = [
            "major",
            "minor",
            "minor",
            "major",
            "major",
            "minor",
            "diminished",
        ]
        minor_key_qualities = [
            "minor",
            "diminished",
            "major",
            "minor",
            "minor",
            "major",
            "major",
        ]

        expected_qualities = (
            minor_key_qualities if is_minor_key else major_key_qualities
        )

        # Map intervals to scale degrees
        scale_degree_mappings = [
            (0, 0),
            (2, 1),
            (4, 2),
            (5, 3),
            (7, 4),
            (9, 5),
            (11, 6),
        ]

        # Find the scale degree for this interval
        mapping = next(
            (mapping for mapping in scale_degree_mappings if mapping[0] == interval),
            None,
        )

        if not mapping:
            # Chromatic chord - use modal approach
            return self._generate_modal_roman_numeral(chord, tonic_pitch_class)

        scale_degree = mapping[1]
        expected_quality = expected_qualities[scale_degree]

        # Roman numeral symbols
        roman_numerals = ["I", "II", "III", "IV", "V", "VI", "VII"]
        roman_numeral = roman_numerals[scale_degree]

        # Adjust case based on expected quality
        if expected_quality in ["minor", "diminished"]:
            roman_numeral = roman_numeral.lower()

        # Add diminished symbol
        if expected_quality == "diminished":
            roman_numeral += "°"

        # Add inversion notation if present
        if chord.bass_pitch_class is not None:
            inversion_info = analyze_chord_inversion(
                chord.pitch_class,
                chord.bass_pitch_class,
                chord.symbol,  # Pass original symbol for 7th chord detection
            )
            figured_bass = inversion_info["figured_bass"]
            if isinstance(figured_bass, str):
                roman_numeral += figured_bass

        return roman_numeral

    def _detect_functional_patterns(self, roman_numerals: List[str]) -> float:
        """Detect functional patterns in Roman numeral sequence"""
        progression = "-".join(roman_numerals)

        # Only detect PURE functional patterns without modal characteristics
        pure_functional_patterns: List[Dict[str, Any]] = [
            {"pattern": "I-V-I", "strength": 0.95},
            {"pattern": "I-IV-V-I", "strength": 0.95},
            {"pattern": "ii-V-I", "strength": 0.85},
            {"pattern": "vi-IV-I-V", "strength": 0.90},
        ]

        # Check if progression contains modal characteristics
        has_modal_characteristics = any(
            "bVII" in rn
            or "bII" in rn
            or "II" in rn
            or "#IV" in rn
            or "bVI" in rn
            or "bIII" in rn
            for rn in roman_numerals
        )

        if has_modal_characteristics:
            return 0  # Modal characteristics present - not purely functional

        # Only flag exact matches of pure functional progressions
        for pattern in pure_functional_patterns:
            if progression == pattern["pattern"]:
                return float(pattern["strength"])

        return 0  # No pure functional patterns detected

    def _detect_foil_patterns(self, roman_numerals: List[str]) -> bool:
        """Detect foil patterns that should have reduced modal confidence"""
        progression = "-".join(roman_numerals)

        # Normalize roman numerals by removing chord extensions
        normalized_roman_numerals = [
            re.sub(r"7|maj7|m7|ø7|°7|sus|add|dim", "", rn) for rn in roman_numerals
        ]
        normalized_progression = "-".join(normalized_roman_numerals)

        # Modal foil patterns
        modal_foil_patterns = [
            "I-V-I",  # Pure functional - any mode
            "I-IV-V-I",  # Pure functional progression
            "ii-V-I",  # Jazz ii-V-I - purely functional
            "vi-IV-I-V",  # Pop progression - functional
            "i-iv-i",  # Dorian foil: minor iv suggests Aeolian, not Dorian
            "i-II-i",  # Phrygian foil: natural II undermines characteristic bII
            "i-V-i",  # Minor authentic cadence - functional, not modal
            "i-v-i",  # Natural minor (Aeolian) - not other minor modes
            "i°-V-i°",  # Locrian foil: functional V resolution in diminished contexts
        ]

        return any(
            pattern in [progression, normalized_progression]
            for pattern in modal_foil_patterns
        )

    def _calculate_confidence(
        self,
        evidence: List[ModalEvidence],
        pattern_results: List[Dict],
        roman_numerals: Optional[List[str]] = None,
        chord_analyses: Optional[List[ChordAnalysis]] = None,
        parent_key: Optional[str] = None,
    ) -> float:
        """Calculate overall confidence based on evidence"""
        if not evidence:
            return 0.0

        # Check for functional patterns first
        functional_strength = 0.0
        if roman_numerals:
            functional_strength = self._detect_functional_patterns(roman_numerals)

        # Base confidence from evidence
        evidence_strength = sum(e.strength for e in evidence) / len(evidence)

        # Pattern matching bonus
        pattern_bonus = 0
        if pattern_results:
            best_pattern = pattern_results[0]
            pattern_bonus = (
                best_pattern["pattern"].strength * best_pattern["matches"] * 0.3
            )

        # Structural bonus for strong evidence
        structural_evidence = [e for e in evidence if e.type == EvidenceType.STRUCTURAL]
        structural_bonus = 0.1 if structural_evidence else 0

        # Consistency bonus for multiple types of evidence
        evidence_types = set(e.type for e in evidence)
        consistency_bonus = 0.1 if len(evidence_types) > 1 else 0

        base_confidence = (
            evidence_strength + pattern_bonus + structural_bonus + consistency_bonus
        )

        # Boost confidence for clear modal patterns
        if pattern_results:
            best_pattern = pattern_results[0]
            if best_pattern["pattern"].strength >= 0.85:
                base_confidence = max(base_confidence, 0.75)

        # Boost confidence for multiple strong evidence types
        if len(evidence_types) >= 2 and evidence_strength > 0.7:
            base_confidence = max(base_confidence, 0.72)

        # Block modal analysis if clear functional patterns detected
        if functional_strength > 0.8:
            return 0  # Don't analyze clear functional progressions as modal

        # Special handling for vamp patterns (two-chord progressions)
        if chord_analyses and len(chord_analyses) == 2:
            if pattern_results:
                vamp_pattern = pattern_results[0]
                if vamp_pattern["pattern"].pattern in ["I-IV", "i-IV"]:
                    base_confidence = max(base_confidence, 0.72)
            elif roman_numerals and "-".join(roman_numerals) in ["I-IV", "i-IV"]:
                base_confidence = max(base_confidence, 0.70)

        # Boost confidence for clear modal patterns
        if roman_numerals:
            roman_string = "-".join(roman_numerals)
            if roman_string == "I-IV-I":
                base_confidence = max(base_confidence, 0.78)
            elif roman_string in ["i-IV-i", "I-bVII-I"]:
                base_confidence = max(base_confidence, 0.75)

        return min(base_confidence, 0.95)

    def _determine_mode_name(
        self,
        pattern_results: List[Dict],
        evidence: List[ModalEvidence],
        tonic: str,
        parent_key: str,
        roman_numerals: List[str],
        chord_analyses: List[ChordAnalysis],
    ) -> str:
        """Determine mode name based on analysis"""

        # PRIORITY 1: Pattern-based mode detection (most reliable)
        if pattern_results:
            best_pattern = pattern_results[0]

            # Check if this is an ambiguous pattern that could be multiple modes
            if best_pattern["pattern"].pattern == "I-IV" and parent_key:
                parent_root = self._extract_key_root(parent_key)
                interval = (
                    self.NOTE_TO_PITCH_CLASS[tonic]
                    - self.NOTE_TO_PITCH_CLASS[parent_root]
                    + 12
                ) % 12

                # If tonic is 5th degree of parent key (interval = 7), it's Mixolydian
                if interval == 7:
                    return f"{tonic} Mixolydian"
                # If tonic is same as parent key (interval = 0), it's Ionian
                if interval == 0:
                    return f"{tonic} Ionian"

            # Check 7th chord qualities before returning pattern-based mode
            tonic_pitch_class = self.NOTE_TO_PITCH_CLASS[tonic]
            tonic_chords = [
                chord
                for chord in chord_analyses
                if chord.pitch_class == tonic_pitch_class
            ]
            has_dominant7_tonic = any(
                chord.quality == "dominant7" for chord in tonic_chords
            )
            has_half_diminished7_tonic = any(
                chord.quality == "half_diminished" for chord in tonic_chords
            )
            has_major_iv = "IV" in roman_numerals

            # 7th chord qualities provide more specific mode identification
            if has_half_diminished7_tonic:
                return f"{tonic} Locrian"

            if has_dominant7_tonic and has_major_iv:
                return f"{tonic} Mixolydian"

            mode_name = best_pattern["pattern"].modes[0]
            return f"{tonic} {mode_name}"

        # PRIORITY 2: Evidence-based mode detection with chord quality discrimination
        has_sharp4 = any("#IV" in e.description for e in evidence)

        # Check Roman numerals for chord quality clues
        roman_string = "-".join(roman_numerals)
        has_minor_tonic = any(rn in ["i", "i7", "im7"] for rn in roman_numerals)
        has_major_tonic = any(rn in ["I", "I7", "Imaj7"] for rn in roman_numerals)
        has_major_iv = "IV" in roman_numerals
        has_minor_iv = "iv" in roman_numerals
        has_diminished_tonic = "i°" in roman_string

        # Check actual chord qualities
        tonic_pitch_class = self.NOTE_TO_PITCH_CLASS[tonic]
        tonic_chords = [
            chord for chord in chord_analyses if chord.pitch_class == tonic_pitch_class
        ]
        has_dominant7_tonic = any(
            chord.quality == "dominant7" for chord in tonic_chords
        )
        has_half_diminished7_tonic = any(
            chord.quality == "half_diminished" for chord in tonic_chords
        )

        has_flat7_chord = "bVII" in roman_numerals
        has_flat2_chord = "bII" in roman_numerals
        has_natural2_chord = "II" in roman_numerals
        has_flat6_chord = "bVI" in roman_numerals

        # PRIORITY 1: 7th chord quality discrimination
        if has_half_diminished7_tonic:
            return f"{tonic} Locrian"

        if has_dominant7_tonic and has_major_iv:
            return f"{tonic} Mixolydian"

        # PRIORITY 2: Distinctive modal characteristics
        if has_diminished_tonic and has_flat2_chord:
            return f"{tonic} Locrian"

        if has_flat2_chord and has_minor_tonic:
            return f"{tonic} Phrygian"

        if (has_natural2_chord or has_sharp4) and has_major_tonic:
            return f"{tonic} Lydian"

        # Minor mode discrimination
        if has_minor_tonic:
            # Dorian: minor tonic + major IV + flat VII
            if has_major_iv and has_flat7_chord:
                return f"{tonic} Dorian"

            # Aeolian: minor tonic + minor iv + flat VII + flat VI
            if has_minor_iv and has_flat7_chord and has_flat6_chord:
                return f"{tonic} Aeolian"

            # If has major IV but no clear flat VII, likely Dorian
            if has_major_iv and not has_flat6_chord:
                return f"{tonic} Dorian"

            # If has minor iv and flat VI, likely Aeolian
            if has_minor_iv and has_flat6_chord:
                return f"{tonic} Aeolian"

            # Default for minor tonic
            return f"{tonic} Aeolian"

        # PRIORITY 3: Parent key relationship calculation
        if parent_key:
            parent_root = self._extract_key_root(parent_key)
            interval = (
                self.NOTE_TO_PITCH_CLASS[tonic]
                - self.NOTE_TO_PITCH_CLASS[parent_root]
                + 12
            ) % 12

            mode_map = {
                0: "Ionian",
                2: "Dorian",
                4: "Phrygian",
                5: "Lydian",
                7: "Mixolydian",
                9: "Aeolian",
                11: "Locrian",
            }

            mode_name = mode_map.get(interval)
            if mode_name:
                # For ambiguous cases, prioritize parent key context
                # Default to that mode with parent key context and
                # a resolvable interval
                return f"{tonic} {mode_name}"

        # PRIORITY 4: Major mode discrimination (fallback)
        if has_major_tonic:
            if has_flat7_chord:
                return f"{tonic} Mixolydian"
            return f"{tonic} Ionian"

        # FALLBACK
        return f"{tonic} Ionian"

    def _identify_modal_characteristics(self, roman_numerals: List[str]) -> List[str]:
        """Identify specific modal characteristics"""
        characteristics = []

        if "bVII" in roman_numerals:
            characteristics.append("Contains bVII chord (flat seventh scale degree)")

        if "bII" in roman_numerals:
            characteristics.append("Contains bII chord (flat second scale degree)")

        # Check for cadential patterns
        roman_string = "-".join(roman_numerals)
        if "bVII-I" in roman_string:
            characteristics.append("bVII-I cadence (Mixolydian characteristic)")

        if "bII-I" in roman_string:
            characteristics.append("bII-I cadence (Phrygian characteristic)")

        return characteristics

    def _parse_chord(self, symbol: str) -> ChordAnalysis:
        """Parse chord symbol into components"""
        clean_symbol = symbol.strip()
        if not clean_symbol:
            raise ValueError("Empty chord symbol")

        # Check for slash chord notation
        bass_pitch_class = None
        if "/" in clean_symbol:
            chord_part, bass_part = clean_symbol.split("/", 1)
            bass_part = bass_part.strip()
            bass_pitch_class = self.NOTE_TO_PITCH_CLASS.get(bass_part)
            # Continue parsing with just the chord part
            clean_symbol = chord_part.strip()

        # Extract root note (handles sharps and flats)
        root_match = re.match(r"^([A-G][#b]?)", clean_symbol)
        if not root_match:
            raise ValueError(f"Cannot parse chord: {symbol} - invalid root note")

        root = root_match.group(1)
        remainder = clean_symbol[len(root) :]

        # Determine chord quality
        quality = "major"  # default

        # Check chord qualities (most specific to least specific)
        if any(pattern in remainder for pattern in ["m7b5", "ø7", "m7♭5"]):
            quality = "half_diminished"
        elif "dim" in remainder:
            quality = "diminished"
        elif "aug" in remainder:
            quality = "augmented"
        elif "maj7" in remainder or "M7" in remainder:
            quality = "major7"
        elif "m7" in remainder:
            quality = "minor7"
        elif "7" in remainder:
            quality = "dominant7"
        elif re.match(r"^m(?!aj)", remainder):
            quality = "minor"
        elif "sus2" in remainder or "sus4" in remainder:
            quality = "suspended"

        pitch_class = self.NOTE_TO_PITCH_CLASS.get(root)
        if pitch_class is None:
            raise ValueError(f"Unknown root note: {root}")

        return ChordAnalysis(
            symbol=symbol,  # Keep original symbol
            root=root,
            quality=quality,
            pitch_class=pitch_class,
            bass_pitch_class=bass_pitch_class,
        )

    def _validate_chords_against_parent_key(
        self, chord_analyses: List[ChordAnalysis], parent_key: str
    ) -> Dict[str, Any]:
        """
        Validate how well chords fit within the specified parent key.

        Returns:
            Dict with validation metrics including outside_key_ratio
        """
        if parent_key not in KEY_SIGNATURES:
            # Unknown key signature - assume valid
            return {
                "outside_key_ratio": 0.0,
                "outside_key_chords": [],
                "key_signature_notes": [],
            }

        key_signature_accidentals = KEY_SIGNATURES[parent_key]

        # Build the complete set of notes in this key
        natural_notes = ["C", "D", "E", "F", "G", "A", "B"]
        key_notes = set()

        for note in natural_notes:
            # Start with natural note
            final_note = note

            # Apply accidentals from key signature
            sharp_note = note + "#"
            flat_note = note + "b"

            if sharp_note in key_signature_accidentals:
                final_note = sharp_note
            elif flat_note in key_signature_accidentals:
                final_note = flat_note

            key_notes.add(final_note)

        # Also add enharmonic equivalents for edge cases
        enharmonic_map = {
            "E#": "F",
            "B#": "C",
            "Cb": "B",
            "Fb": "E",
            "F#": "Gb",
            "C#": "Db",
            "G#": "Ab",
            "D#": "Eb",
            "A#": "Bb",
        }

        expanded_key_notes = set(key_notes)
        for note in key_notes:
            if note in enharmonic_map:
                expanded_key_notes.add(enharmonic_map[note])
            # Add reverse mappings
            for enharmonic, equivalent in enharmonic_map.items():
                if note == equivalent:
                    expanded_key_notes.add(enharmonic)

        # Check each chord's root against the key
        outside_key_chords = []
        total_chords = len(chord_analyses)

        for chord in chord_analyses:
            chord_root = chord.root

            # Check if chord root is in the key
            if chord_root not in expanded_key_notes:
                outside_key_chords.append(chord.symbol)

        outside_key_ratio = (
            len(outside_key_chords) / total_chords if total_chords > 0 else 0
        )

        return {
            "outside_key_ratio": outside_key_ratio,
            "outside_key_chords": outside_key_chords,
            "key_signature_notes": list(expanded_key_notes),
            "total_chords": total_chords,
        }

    def _infer_parent_key(self, tonic: str) -> str:
        """Infer parent key from tonic"""
        # Simple heuristic: assume major key for parent
        return f"{tonic} major"

    def _get_correct_parent_key(
        self, mode_name: str, tonic: str, current_parent_key: str
    ) -> str:
        """Get correct parent key based on detected mode"""
        # Extract mode type from mode name
        if "Ionian" in mode_name:
            # Ionian: tonic IS the parent key
            return f"{tonic} major"
        elif "Dorian" in mode_name:
            # Dorian: tonic is 2nd degree, parent is whole step down
            parent_root = self._transpose_note(tonic, -2)
            return f"{parent_root} major"
        elif "Phrygian" in mode_name:
            # Phrygian: tonic is 3rd degree, parent is major 3rd down
            parent_root = self._transpose_note(tonic, -4)
            return f"{parent_root} major"
        elif "Lydian" in mode_name:
            # Lydian: tonic is 4th degree, parent is perfect 4th down
            parent_root = self._transpose_note(tonic, -5)
            return f"{parent_root} major"
        elif "Mixolydian" in mode_name:
            # Mixolydian: tonic is 5th degree, parent is perfect 4th up
            parent_root = self._transpose_note(tonic, 5)
            return f"{parent_root} major"
        elif "Aeolian" in mode_name:
            # Aeolian: tonic is 6th degree, parent is minor 3rd up
            parent_root = self._transpose_note(tonic, 3)
            return f"{parent_root} major"
        elif "Locrian" in mode_name:
            # Locrian: tonic is 7th degree, parent is semitone up
            parent_root = self._transpose_note(tonic, 1)
            return f"{parent_root} major"
        else:
            # Unknown mode, return current parent key
            return current_parent_key

    def _transpose_note(self, note: str, semitones: int) -> str:
        """Transpose a note by given number of semitones"""
        # Circle of fifths for clean enharmonic spelling
        notes_sharp = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        notes_flat = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

        # Use sharp notation for F# and related keys, flat for others
        use_sharps = "#" in note or note in ["F#", "C#", "G#", "D#", "A#"]
        note_list = notes_sharp if use_sharps else notes_flat

        # Find current note index
        try:
            current_index = note_list.index(note)
        except ValueError:
            # Try the other notation
            note_list = notes_flat if use_sharps else notes_sharp
            current_index = note_list.index(note)

        # Calculate new index
        new_index = (current_index + semitones) % 12
        return note_list[new_index]

    def _extract_key_root(self, key_signature: str) -> str:
        """Extract root note from key signature string"""
        match = re.match(r"^([A-G][#b]?)", key_signature)
        return match.group(1) if match else "C"


# Convenience function export to match dynamic import expectations
async def analyze_modal_progression(
    chords: List[str], parent_key: Optional[str] = None
) -> Optional[ModalAnalysisResult]:
    """
    Analyze chord progression for modal characteristics

    Args:
        chords: List of chord symbols
        parent_key: Optional parent key context

    Returns:
        ModalAnalysisResult if modal characteristics detected, None otherwise
    """
    analyzer = EnhancedModalAnalyzer()
    return analyzer.analyze_modal_characteristics(chords, parent_key)
