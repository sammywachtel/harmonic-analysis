"""
Functional harmony analysis engine.

Implements comprehensive functional harmony analysis with complete Roman numeral
generation, chromatic chord detection, and figured bass notation.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..analysis_types import ChordFunction, ChromaticType, ProgressionType
from .utils.chord_inversions import analyze_chord_inversion
from .utils.chord_logic import ChordMatch
from .utils.scales import NOTE_TO_PITCH_CLASS

# TODO(romanizer-unification):
#   Roman numeral generation exists here and in services/token_converter.py.
#   To ensure a single source of truth (and avoid drift like VII vs ♭VII in minor),
#   delegate romanization here to the token converter’s logic in a follow-up change.
#   For now, the subtonic in minor is aligned to ♭VII in both places.


# Enhanced Roman numeral templates with chromatic chord support
FUNCTIONAL_ROMAN_NUMERALS = {
    "major": {
        "diatonic": ["I", "ii", "iii", "IV", "V", "vi", "vii°"],
        "chromatic": {
            # Secondary dominants (used as fallback for non-dominant quality
            # chords at these intervals)
            2: "V/V",  # D7 - Dominant of V (very common)
            4: "V/vi",  # E7 - Dominant of vi
            9: "V/ii",  # A7 - Dominant of ii
            11: "V/iii",  # B7 - Dominant of iii
        },
    },
    "minor": {
        # In minor, the natural subtonic is conventionally notated as ♭VII
        # (major triad on lowered 7̂)
        "diatonic": ["i", "ii°", "III", "iv", "v", "VI", "bVII"],
        "chromatic": {
            # Secondary dominants
            2: "V/III",  # Dominant of III
            5: "V/iv",  # Dominant of iv
            7: "V/v",  # Dominant of v
            9: "V/VI",  # Dominant of VI
            11: "V/VII",  # Dominant of VII
            # Common chromatic chords in minor keys
            4: "#iv°",  # Raised 4th diminished
        },
    },
}

# Chord function mapping based on Roman numeral degree
CHORD_FUNCTIONS: Dict[int, Dict[str, ChordFunction]] = {
    # Major key functions
    0: {"major": ChordFunction.TONIC, "minor": ChordFunction.TONIC},  # I/i
    1: {
        "major": ChordFunction.CHROMATIC,
        "minor": ChordFunction.CHROMATIC,
    },  # Chromatic
    2: {
        "major": ChordFunction.PREDOMINANT,
        "minor": ChordFunction.PREDOMINANT,
    },  # ii/ii°
    4: {
        "major": ChordFunction.MEDIANT,
        "minor": ChordFunction.MEDIANT,
    },  # iii/III - mediant in major and minor
    5: {
        "major": ChordFunction.SUBDOMINANT,
        "minor": ChordFunction.SUBDOMINANT,
    },  # IV/iv
    6: {"major": ChordFunction.CHROMATIC, "minor": ChordFunction.CHROMATIC},  # Tritone
    7: {"major": ChordFunction.DOMINANT, "minor": ChordFunction.DOMINANT},  # V/v
    8: {
        "major": ChordFunction.CHROMATIC,
        "minor": ChordFunction.CHROMATIC,
    },  # Chromatic
    9: {
        "major": ChordFunction.SUBMEDIANT,
        "minor": ChordFunction.SUBDOMINANT,
    },  # vi/VI - submediant in major, subdominant in minor
    10: {
        "major": ChordFunction.CHROMATIC,
        "minor": ChordFunction.SUBDOMINANT,
    },  # bVII - modal in major, natural in minor
    11: {
        "major": ChordFunction.LEADING_TONE,
        "minor": ChordFunction.LEADING_TONE,
    },  # vii°/VII
}


@dataclass
class FunctionalChordAnalysis:
    """Analysis result for a single chord in functional harmony context."""

    chord_symbol: str
    root: int
    chord_name: str
    roman_numeral: str
    figured_bass: str
    inversion: int
    function: ChordFunction
    is_chromatic: bool
    chromatic_type: Optional[ChromaticType] = None
    bass_note: Optional[int] = None


@dataclass
class Cadence:
    """Cadence analysis result."""

    type: str  # 'authentic', 'plagal', 'deceptive', 'half'
    chords: List[FunctionalChordAnalysis]
    strength: float
    position: str  # 'phrase_ending' or 'mid_phrase'


@dataclass
class ChromaticElement:
    """Chromatic harmony element."""

    chord: FunctionalChordAnalysis
    type: ChromaticType
    resolution: Optional[FunctionalChordAnalysis]
    explanation: str


@dataclass
class FunctionalAnalysisResult:
    """Complete functional harmony analysis result."""

    key_center: str
    key_signature: str
    mode: str  # 'major', 'minor', 'modal'
    chords: List[FunctionalChordAnalysis]
    cadences: List[Cadence]
    progression_type: ProgressionType
    confidence: float
    explanation: str
    chromatic_elements: List[ChromaticElement]
    ambiguity_factors: Optional[List[str]] = None
    key_source: str = "detected"  # 'user' | 'detected'
    key_locked: bool = False


class FunctionalHarmonyAnalyzer:
    """Main functional harmony analyzer class with comprehensive Roman
    numeral generation."""

    def __init__(self) -> None:
        self.last_analysis_ambiguity: List[str] = []
        # Mapping of chromatic scale degrees to common secondary dominant labels
        # Used as a fallback in _calculate_roman_numeral when detecting
        # chromatic degrees
        self.secondary_dominants: Dict[int, str] = {}

    async def analyze_functionally(
        self,
        chord_symbols: List[str],
        parent_key: Optional[str] = None,
        *,
        key_hint: str | None = None,
        lock_key: bool = True,
    ) -> FunctionalAnalysisResult:
        """
        Analyze chord progression with functional harmony as primary framework.

        Args:
            chord_symbols: List of chord symbols to analyze
            parent_key: Optional parent key signature (e.g., "C major")
                        - for backward compatibility
            key_hint: Optional key hint for analysis (new parameter)
            lock_key: If True, force the provided key hint;
                     else use for detection guidance

        Returns:
            Complete functional analysis result
        """
        if not chord_symbols:
            raise ValueError("Empty chord progression")

        # Step 1: Determine key center - key_hint takes precedence over parent_key
        effective_key_hint = key_hint or parent_key
        key_analysis = self._determine_key_center(
            chord_symbols, effective_key_hint, lock_key
        )

        # Step 2: Analyze each chord functionally
        functional_chords = self._analyze_chords_in_key(chord_symbols, key_analysis)

        # Step 3: Identify cadences and progressions
        cadences = self._identify_cadences(functional_chords)
        progression_type = self._classify_progression(functional_chords, cadences)

        # Step 4: Detect chromatic elements
        chromatic_elements = self._detect_chromatic_elements(
            functional_chords, key_analysis
        )

        # Step 5: Calculate confidence and create explanation
        confidence = self._calculate_confidence(
            functional_chords, cadences, chromatic_elements
        )
        explanation = self._create_explanation(
            functional_chords, progression_type, chromatic_elements
        )

        result = FunctionalAnalysisResult(
            key_center=key_analysis["key_center"],
            key_signature=key_analysis["key_signature"],
            mode=key_analysis["mode"],
            chords=functional_chords,
            cadences=cadences,
            progression_type=progression_type,
            confidence=confidence,
            explanation=explanation,
            chromatic_elements=chromatic_elements,
            ambiguity_factors=(
                self.last_analysis_ambiguity if self.last_analysis_ambiguity else None
            ),
            key_source=key_analysis["key_source"],
            key_locked=key_analysis["key_locked"],
        )

        # Debug: print analyzer key decision
        # TODO: implement a unified debugging approach for the library

        # print(
        #     f"[analyzer] key={key_analysis['key_center']} "
        #     f"(source={key_analysis['key_source']}, "
        #     f"locked={key_analysis['key_locked']})"
        # )

        return result

    def _determine_key_center(
        self,
        chord_symbols: List[str],
        effective_key_hint: Optional[str],
        lock_key: bool = True,
    ) -> Dict[str, Any]:
        """
        Determine the key center using multiple methods.

        Returns:
            Dictionary with key_center, key_signature, mode, root_pitch,
            is_minor, key_source, key_locked
        """
        if effective_key_hint:
            # Use provided key hint
            parsed = self._parse_key(effective_key_hint)
            if parsed:
                return {
                    "key_center": (
                        f"{parsed['tonic']} "
                        f"{'minor' if parsed['is_minor'] else 'major'}"
                    ),
                    "key_signature": self._get_key_signature(
                        parsed["tonic"], parsed["is_minor"]
                    ),
                    "mode": "minor" if parsed["is_minor"] else "major",
                    "root_pitch": NOTE_TO_PITCH_CLASS.get(parsed["tonic"], 0),
                    "is_minor": parsed["is_minor"],
                    "key_source": "user",
                    "key_locked": lock_key,
                }

        # SMART KEY DETECTION: Check for common functional patterns first
        detected_key = self._detect_functional_patterns(chord_symbols)
        if detected_key:
            suggested_root = NOTE_TO_PITCH_CLASS.get(detected_key["tonic"], 0)
            is_minor = detected_key["is_minor"]
        else:
            # Fallback: Analyze first chord for tonal center
            first_chord = self._parse_chord_symbol(chord_symbols[0])

            # Assume first/last chord suggests key (simple heuristic)
            suggested_root = first_chord["root"] if first_chord else 0
            is_minor = bool(
                first_chord
                and (
                    "m" in first_chord["chord_name"]
                    and "M" not in first_chord["chord_name"]
                )
            )
        root_name = next(
            (
                name
                for name, pitch in NOTE_TO_PITCH_CLASS.items()
                if pitch == suggested_root
            ),
            "C",
        )

        return {
            "key_center": f"{root_name} {'minor' if is_minor else 'major'}",
            "key_signature": self._get_key_signature(root_name, is_minor),
            "mode": "minor" if is_minor else "major",
            "root_pitch": suggested_root,
            "is_minor": is_minor,
            "key_source": "detected",
            "key_locked": False,
        }

    def _parse_key(self, key_str: str) -> Optional[Dict[str, Any]]:
        """Parse key string like 'C major' or 'A minor'."""
        parts = key_str.split()
        if len(parts) >= 2:
            tonic = parts[0]
            mode = parts[1].lower()
            if tonic in NOTE_TO_PITCH_CLASS:
                return {
                    "tonic": tonic,
                    "is_minor": mode == "minor" or mode == "m",
                }
        return None

    def _get_key_signature(self, tonic: str, is_minor: bool) -> str:
        """Get key signature for display."""
        return f"{tonic} {'minor' if is_minor else 'major'}"

    def _parse_chord_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Parse chord symbol into components."""
        try:
            from .utils.chord_logic import ChordParser

            parser = ChordParser()
            chord_match = parser.parse_chord(symbol)
            return {
                "root": chord_match.root_pitch,
                "chord_name": symbol,
                "bass_note": chord_match.bass_pitch,
            }
        except Exception:
            # Fallback parsing
            if symbol and symbol[0] in NOTE_TO_PITCH_CLASS:
                return {
                    "root": NOTE_TO_PITCH_CLASS[symbol[0]],
                    "chord_name": symbol,
                    "bass_note": None,
                }
            return None

    def _analyze_chords_in_key(
        self, chord_symbols: List[str], key_analysis: Dict[str, Any]
    ) -> List[FunctionalChordAnalysis]:
        """
        Analyze each chord within the established key with figured bass notation.
        """
        analyzed_chords = []

        for symbol in chord_symbols:
            chord_info = self._parse_chord_symbol(symbol)
            if not chord_info:
                analyzed_chords.append(self._create_empty_chord_analysis(symbol))
                continue

            # Calculate interval from key center
            interval_from_key = (
                chord_info["root"] - key_analysis["root_pitch"] + 12
            ) % 12

            # Determine if chord is diatonic or chromatic
            is_diatonic = self._is_chord_diatonic(
                interval_from_key, key_analysis["is_minor"], chord_info["chord_name"]
            )

            # Get Roman numeral and function
            roman_numeral = self._get_roman_numeral(
                interval_from_key,
                key_analysis["is_minor"],
                chord_info["chord_name"],
                not is_diatonic,
            )

            chord_function = self._get_chord_function(
                interval_from_key, key_analysis["is_minor"], not is_diatonic
            )

            # Analyze inversion and figured bass
            inversion_analysis = self._analyze_inversion_and_figured_bass(
                chord_info, roman_numeral
            )

            # Determine chromatic type if applicable
            chromatic_type = None
            if not is_diatonic:
                chromatic_type = self._determine_chromatic_type(
                    interval_from_key,
                    key_analysis["is_minor"],
                    chord_info["chord_name"],
                )

            analyzed_chords.append(
                FunctionalChordAnalysis(
                    chord_symbol=symbol,
                    root=chord_info["root"],
                    chord_name=chord_info["chord_name"],
                    roman_numeral=roman_numeral + inversion_analysis["figured_bass"],
                    figured_bass=inversion_analysis["figured_bass"],
                    inversion=inversion_analysis["inversion"],
                    function=chord_function,
                    is_chromatic=not is_diatonic,
                    chromatic_type=chromatic_type,
                    bass_note=chord_info["bass_note"],
                )
            )

        return analyzed_chords

    def _create_empty_chord_analysis(self, symbol: str) -> FunctionalChordAnalysis:
        """Create empty analysis for unparseable chords."""
        return FunctionalChordAnalysis(
            chord_symbol=symbol,
            root=0,
            chord_name=symbol,
            roman_numeral="?",
            figured_bass="",
            inversion=0,
            function=ChordFunction.CHROMATIC,
            is_chromatic=True,
            bass_note=None,
        )

    def _is_chord_diatonic(
        self, interval_from_key: int, is_minor: bool, chord_name: str
    ) -> bool:
        """Check if chord is diatonic to the key."""
        # Diatonic intervals for each mode
        diatonic_intervals = (
            [0, 2, 3, 5, 7, 8, 10] if is_minor else [0, 2, 4, 5, 7, 9, 11]
        )

        # If the interval itself is not diatonic, it's definitely chromatic
        if interval_from_key not in diatonic_intervals:
            return False

        # Check if chord quality matches expected diatonic chord quality
        expected_qualities = self._get_expected_diatonic_qualities(
            interval_from_key, is_minor
        )
        actual_quality = self._parse_chord_quality(chord_name)

        # Check if the actual quality matches any expected diatonic quality
        return any(
            self._qualities_match(actual_quality, expected)
            for expected in expected_qualities
        )

    def _get_expected_diatonic_qualities(
        self, interval_from_key: int, is_minor: bool
    ) -> List[str]:
        """Get expected diatonic chord qualities for a scale degree."""
        if is_minor:
            # Natural minor chord qualities
            minor_qualities = {
                0: ["minor"],  # i
                2: ["diminished"],  # ii°
                3: ["major"],  # III
                5: ["minor"],  # iv
                7: ["minor", "major", "dominant"],  # v (or V, or V7)
                8: ["major"],  # VI
                10: ["major"],  # bVII (subtonic)
            }
            return minor_qualities.get(interval_from_key, [])
        else:
            # Major chord qualities
            major_qualities = {
                0: ["major"],  # I
                2: ["minor"],  # ii
                4: ["minor"],  # iii
                5: ["major"],  # IV
                7: ["major", "dominant"],  # V (can be V or V7)
                9: ["minor"],  # vi
                11: ["diminished"],  # vii°
            }
            return major_qualities.get(interval_from_key, [])

    def _parse_chord_quality(self, chord_name: str) -> str:
        """Parse chord quality from chord name."""
        chord_lower = chord_name.lower()

        if "maj7" in chord_lower or "M7" in chord_name:
            return "major7"
        elif "dom7" in chord_lower:
            return "dominant7"
        elif "m7" in chord_lower or "min7" in chord_lower:
            return "minor7"
        elif "7" in chord_lower and "maj" not in chord_lower and "m" not in chord_lower:
            return "dominant7"
        elif "dim" in chord_lower or "°" in chord_name:
            return "diminished"
        elif "aug" in chord_lower or "+" in chord_name:
            return "augmented"
        elif "sus4" in chord_lower:
            return "suspended"
        elif "sus2" in chord_lower:
            return "suspended"
        elif "m" in chord_lower and "maj" not in chord_lower:
            return "minor"
        else:
            return "major"

    def _qualities_match(self, actual: str, expected: str) -> bool:
        """Check if chord qualities match (accounting for extensions)."""
        # Exact match
        if actual == expected:
            return True

        # Major chord can be major or major7
        if expected == "major" and actual in ["major", "major7"]:
            return True

        # Minor chord can be minor or minor7
        if expected == "minor" and actual in ["minor", "minor7"]:
            return True

        # Suspended chords are diatonic variants
        if actual == "suspended" and expected in ["major", "minor"]:
            return True

        # PRECEDENCE RULE: V7 in home key is diatonic functional, not chromatic
        # Dominant 7th matches expected dominant (V chord can be V or V7)
        if actual == "dominant7" and expected == "dominant":
            return True

        # Pure dominant7 chord only matches if explicitly expected
        if actual == "dominant7":
            return expected == "dominant7"

        return False

    def _get_roman_numeral(
        self,
        interval_from_key: int,
        is_minor: bool,
        chord_name: str,
        is_chromatic: bool,
    ) -> str:
        """
        Get Roman numeral with chromatic chord support - comprehensive implementation.
        """
        templates: Dict[str, Any] = FUNCTIONAL_ROMAN_NUMERALS[
            "minor" if is_minor else "major"
        ]

        if not is_chromatic:
            # Use diatonic Roman numerals
            diatonic_intervals = (
                [0, 2, 3, 5, 7, 8, 10] if is_minor else [0, 2, 4, 5, 7, 9, 11]
            )
            try:
                scale_index = diatonic_intervals.index(interval_from_key)
                numeral: str = str(templates["diatonic"][scale_index])

                # Add chord extensions and modifications
                if "maj7" in chord_name.lower() or "M7" in chord_name:
                    numeral += "maj7"
                elif "7" in chord_name:
                    numeral += "7"
                if "+" in chord_name or "aug" in chord_name:
                    numeral += "+"
                if "9" in chord_name:
                    numeral += "9"
                if "sus4" in chord_name:
                    numeral += "sus4"
                if "sus2" in chord_name:
                    numeral += "sus2"

                return numeral
            except ValueError:
                pass  # Fall through to chromatic analysis

        # Handle chromatic chords with comprehensive analysis
        if is_chromatic:
            # Check if this is actually a dominant quality chord
            # (for secondary dominants)
            actual_quality = self._parse_chord_quality(chord_name)
            is_dominant_quality = actual_quality in ["dominant7", "major"]

            # First check for common borrowed chords from parallel minor/major
            is_common_borrowed_chord = self._is_common_borrowed_chord(
                interval_from_key, is_minor
            )

            if not is_common_borrowed_chord and not is_minor and is_dominant_quality:
                # Comprehensive secondary dominant detection for major keys
                if self._is_likely_secondary_dominant(
                    interval_from_key, actual_quality
                ):
                    major_secondary_notation = {
                        0: "V/IV",  # Root as dominant of IV
                        1: "V/bv",  # C# -> unusual, treat as chromatic mediant
                        2: "V/V",  # D in C major -> tonicizes G (V)
                        3: "V/bVI",  # Eb -> borrowed/chromatic
                        4: "V/vi",  # E in C major -> tonicizes Am (vi)
                        6: "V/bII",  # F# -> Neapolitan area
                        8: "V/bVI",  # Ab -> borrowed chord area
                        9: "V/ii",  # A in C major -> tonicizes Dm (ii)
                        10: "V/bVII",  # Bb -> borrowed from minor
                        11: "V/iii",  # B in C major -> tonicizes Em (iii)
                    }

                    # Specific fixes for common intervals
                    if interval_from_key in [7, 9]:
                        notation = "V7/ii" if actual_quality == "dominant7" else "V/ii"
                        return notation

                    if interval_from_key in major_secondary_notation:
                        notation = major_secondary_notation[interval_from_key]
                        if actual_quality == "dominant7":
                            notation = notation.replace("V/", "V7/")
                        if "+" in chord_name:
                            notation += "+"
                        return notation

            # Secondary dominant detection for minor keys
            if is_minor and is_dominant_quality:
                minor_secondary_notation = {
                    0: "V/iv",  # Root chord as dominant of iv
                    1: "V/bV",  # Chromatic
                    2: "V/V",  # D in A minor -> tonicizes Em (v) or E (V)
                    3: "V/VI",  # Eb in A minor -> tonicizes F (VI)
                    4: "V/bVII",  # E -> could tonicize G
                    5: "V/bII",  # F -> Neapolitan
                    7: "V/bIII",  # G -> tonicizes C (III)
                    8: "V/IV",  # Ab -> unusual
                    9: "V/VI",  # A -> tonicizes F (VI)
                    10: "V/bVII",  # Bb -> tonicizes Eb
                    11: "V/VII",  # B -> tonicizes G# (rare in natural minor)
                }

                if interval_from_key in minor_secondary_notation:
                    notation = minor_secondary_notation[interval_from_key]
                    if actual_quality == "dominant7":
                        notation = notation.replace("V/", "V7/")
                    if "+" in chord_name:
                        notation += "+"
                    return notation

            # For non-dominant chromatic chords, use borrowed chord notation
            chromatic_notation = (
                {
                    # Borrowed from parallel major in minor keys
                    2: "II",  # Major II (borrowed)
                    4: "IV",  # Major IV (borrowed)
                    6: "bVI",  # Flat VI
                    7: "V",  # Major V (borrowed)
                    9: "VI",  # Major VI (borrowed)
                    11: "vii°",  # Diminished vii (borrowed)
                }
                if is_minor
                else {
                    # Borrowed from parallel minor in major keys
                    1: "bii",  # Flat ii
                    3: "bIII",  # Flat III (borrowed)
                    5: "iv",  # iv (borrowed minor fourth)
                    6: "bvi",  # Flat vi
                    8: "bVI",  # Flat VI (borrowed)
                    10: "bVII",  # Flat VII (borrowed)
                }
            )

            if interval_from_key in chromatic_notation:
                result = chromatic_notation[interval_from_key]
                # Add chord quality indicators
                if "7" in chord_name:
                    result += "7"
                if "+" in chord_name:
                    result += "+"
                if "°" in chord_name:
                    result += "°"
                return result

            # Last resort - use interval-based Roman numeral
            interval_to_roman_base = {
                0: "I",
                1: "bII",
                2: "II",
                3: "bIII",
                4: "III",
                5: "IV",
                6: "bV",
                7: "V",
                8: "bVI",
                9: "VI",
                10: "bVII",
                11: "VII",
            }

            result = interval_to_roman_base.get(interval_from_key, "I")

            # Apply chord quality
            if actual_quality == "minor":
                result = result.lower()
            elif actual_quality == "diminished":
                result = result.lower() + "°"

            # Add extensions
            if "7" in chord_name:
                result += "7"
            if "+" in chord_name:
                result += "+"

            return result

        # Enhanced fallback: compute nearest diatonic degree with accidentals
        return self._fallback_diatonic_degree(interval_from_key, is_minor)

    def _fallback_diatonic_degree(self, interval_from_key: int, is_minor: bool) -> str:
        """Compute a fallback roman numeral using nearest diatonic degree with
        accidentals."""
        # Define diatonic intervals for major and minor
        if is_minor:
            diatonic_intervals = [0, 2, 3, 5, 7, 8, 10]  # Natural minor: W-H-W-W-H-W-W
            scale_degrees = ["i", "ii°", "III", "iv", "v", "VI", "VII"]
        else:
            diatonic_intervals = [0, 2, 4, 5, 7, 9, 11]  # Major: W-W-H-W-W-W-H
            scale_degrees = ["I", "ii", "iii", "IV", "V", "vi", "vii°"]

        # Normalize interval to 0-11 range
        interval_from_key = interval_from_key % 12

        # If it's already diatonic, use it directly
        if interval_from_key in diatonic_intervals:
            idx = diatonic_intervals.index(interval_from_key)
            return scale_degrees[idx]

        # Find closest diatonic degree and add accidental
        closest_below = max(
            [d for d in diatonic_intervals if d < interval_from_key], default=None
        )
        closest_above = min(
            [d for d in diatonic_intervals if d > interval_from_key], default=None
        )

        # Handle wraparound at octave boundary
        if closest_below is None:
            closest_below = diatonic_intervals[-1] - 12
        if closest_above is None:
            closest_above = diatonic_intervals[0] + 12

        # Choose the closer one
        if abs(interval_from_key - closest_below) <= abs(
            interval_from_key - closest_above
        ):
            base_interval = closest_below % 12
            semitone_diff = interval_from_key - closest_below
        else:
            base_interval = closest_above % 12
            semitone_diff = interval_from_key - closest_above

        # Get base degree
        idx = diatonic_intervals.index(base_interval)
        base_degree = scale_degrees[idx]

        # Add accidentals
        if semitone_diff > 0:
            accidental = "#" * semitone_diff
        elif semitone_diff < 0:
            accidental = "b" * abs(semitone_diff)
        else:
            accidental = ""

        return f"{accidental}{base_degree}"

    def _is_common_borrowed_chord(self, interval_from_key: int, is_minor: bool) -> bool:
        """Check if this is a common borrowed chord that should not be
        analyzed as secondary dominant."""
        if is_minor:
            # Common borrowed chords from parallel major in minor keys
            return interval_from_key in [2, 4, 7, 9, 11]  # II, IV, V, VI, vii°
        else:
            # Common borrowed chords from parallel minor in major keys
            return interval_from_key in [
                1,
                3,
                5,
                6,
                8,
                10,
            ]  # bii, bIII, bVII, bvi, bVI, bVII

    def _is_likely_secondary_dominant(
        self, interval_from_key: int, actual_quality: str
    ) -> bool:
        """Determine if this chord is likely a secondary dominant."""
        # Secondary dominants are typically dominant 7th or major triads
        if actual_quality not in ["dominant7", "major"]:
            return False

        # Common secondary dominant intervals
        secondary_intervals = [
            2,
            4,
            6,
            8,
            9,
            11,
        ]  # Avoid 0, 5, 7, 10 which are often borrowed chords
        return interval_from_key in secondary_intervals

    def _get_chord_function(
        self, interval_from_key: int, is_minor: bool, is_chromatic: bool
    ) -> ChordFunction:
        """Determine chord function."""
        if is_chromatic:
            return ChordFunction.CHROMATIC

        mode_key = "minor" if is_minor else "major"
        return CHORD_FUNCTIONS.get(interval_from_key, {}).get(
            mode_key, ChordFunction.CHROMATIC
        )

    def _analyze_inversion_and_figured_bass(
        self, chord_info: Dict[str, Any], roman_numeral: str
    ) -> Dict[str, Any]:
        """Analyze chord inversion and generate precise figured bass notation."""
        bass_note = chord_info.get("bass_note")
        root_note = chord_info.get("root")
        chord_name = chord_info.get("chord_name", "")

        # Use the shared utility function
        return analyze_chord_inversion(root_note, bass_note, chord_name)

    def _determine_chromatic_type(
        self, interval_from_key: int, is_minor: bool, chord_name: str
    ) -> Optional[ChromaticType]:
        """Determine chromatic type if applicable."""
        actual_quality = self._parse_chord_quality(chord_name)

        # Secondary dominants
        if actual_quality in ["dominant7", "major"]:
            if self._is_likely_secondary_dominant(interval_from_key, actual_quality):
                return ChromaticType.SECONDARY_DOMINANT

        # Borrowed chords
        if self._is_common_borrowed_chord(interval_from_key, is_minor):
            return ChromaticType.BORROWED_CHORD

        # Augmented sixth chords (simplified detection)
        if "aug" in chord_name or "+" in chord_name:
            return ChromaticType.AUGMENTED_SIXTH

        # Neapolitan (simplified detection)
        if interval_from_key == 1:  # bII
            return ChromaticType.NEAPOLITAN

        # Default to chromatic mediant for other chromatic chords
        return ChromaticType.CHROMATIC_MEDIANT

    def _identify_cadences(
        self, chords: List[FunctionalChordAnalysis]
    ) -> List[Cadence]:
        """Detect cadential patterns in progression."""
        cadences = []

        for i in range(len(chords) - 1):
            current = chords[i]
            next_chord = chords[i + 1]

            # V-I authentic cadence
            if (
                current.function == ChordFunction.DOMINANT
                and next_chord.function == ChordFunction.TONIC
            ):
                cadences.append(
                    Cadence(
                        type="authentic",
                        chords=[current, next_chord],
                        strength=0.9,
                        position=(
                            "phrase_ending" if i == len(chords) - 2 else "mid_phrase"
                        ),
                    )
                )

            # IV-I plagal cadence
            elif (
                current.function == ChordFunction.SUBDOMINANT
                and next_chord.function == ChordFunction.TONIC
            ):
                cadences.append(
                    Cadence(
                        type="plagal",
                        chords=[current, next_chord],
                        strength=0.7,
                        position=(
                            "phrase_ending" if i == len(chords) - 2 else "mid_phrase"
                        ),
                    )
                )

            # V-vi deceptive cadence
            elif (
                current.function == ChordFunction.DOMINANT
                and "vi" in next_chord.roman_numeral.lower()
            ):
                cadences.append(
                    Cadence(
                        type="deceptive",
                        chords=[current, next_chord],
                        strength=0.8,
                        position=(
                            "phrase_ending" if i == len(chords) - 2 else "mid_phrase"
                        ),
                    )
                )

        return cadences

    def _classify_progression(
        self, chords: List[FunctionalChordAnalysis], cadences: List[Cadence]
    ) -> ProgressionType:
        """Determine the overall progression type."""
        # Check for specific cadence types
        if any(c.type == "authentic" for c in cadences):
            return ProgressionType.AUTHENTIC_CADENCE
        elif any(c.type == "plagal" for c in cadences):
            return ProgressionType.PLAGAL_CADENCE
        elif any(c.type == "deceptive" for c in cadences):
            return ProgressionType.DECEPTIVE_CADENCE

        # Check for modal characteristics
        roman_string = " ".join(chord.roman_numeral for chord in chords)
        if "bVII" in roman_string or "bII" in roman_string:
            return ProgressionType.MODAL_PROGRESSION

        # Check for circle of fifths
        if len(chords) >= 3:
            functions = [chord.function for chord in chords]
            if (
                ChordFunction.TONIC in functions
                and ChordFunction.PREDOMINANT in functions
                and ChordFunction.DOMINANT in functions
            ):
                return ProgressionType.CIRCLE_OF_FIFTHS

        return ProgressionType.OTHER

    def _detect_chromatic_elements(
        self, chords: List[FunctionalChordAnalysis], key_analysis: Dict[str, Any]
    ) -> List[ChromaticElement]:
        """Detect chromatic elements in detail."""
        chromatic_elements = []

        for i, chord in enumerate(chords):
            if chord.is_chromatic and chord.chromatic_type:
                resolution = chords[i + 1] if i + 1 < len(chords) else None

                explanation = self._get_chromatic_explanation(chord, resolution)

                chromatic_elements.append(
                    ChromaticElement(
                        chord=chord,
                        type=chord.chromatic_type,
                        resolution=resolution,
                        explanation=explanation,
                    )
                )

        return chromatic_elements

    def _get_chromatic_explanation(
        self,
        chord: FunctionalChordAnalysis,
        resolution: Optional[FunctionalChordAnalysis],
    ) -> str:
        """Generate explanation for chromatic element."""
        if chord.chromatic_type == ChromaticType.SECONDARY_DOMINANT:
            if resolution:
                return (
                    f"Secondary dominant {chord.roman_numeral} resolves to "
                    f"{resolution.roman_numeral}."
                )
            else:
                return f"Secondary dominant {chord.roman_numeral} (unresolved)."
        elif chord.chromatic_type == ChromaticType.BORROWED_CHORD:
            return f"Borrowed chord {chord.roman_numeral} from parallel mode."
        else:
            return f"Chromatic chord {chord.roman_numeral}."

    def _calculate_confidence(
        self,
        chords: List[FunctionalChordAnalysis],
        cadences: List[Cadence],
        chromatic_elements: List[ChromaticElement],
    ) -> float:
        """Calculate analysis confidence score."""
        base_confidence = 0.5

        # Boost for strong cadences
        if cadences:
            cadence_boost = sum(c.strength for c in cadences) / len(cadences) * 0.3
            base_confidence += cadence_boost

        # Boost for mostly diatonic chords
        if chords:
            diatonic_ratio = sum(1 for c in chords if not c.is_chromatic) / len(chords)
            base_confidence += diatonic_ratio * 0.2

        # Slight penalty for many unresolved chromatic elements
        unresolved_chromatic = sum(1 for ce in chromatic_elements if not ce.resolution)
        if unresolved_chromatic > 0 and chords:
            penalty = (unresolved_chromatic / len(chords)) * 0.1
            base_confidence -= penalty

        return min(base_confidence, 1.0)

    def _create_explanation(
        self,
        chords: List[FunctionalChordAnalysis],
        progression_type: ProgressionType,
        chromatic_elements: List[ChromaticElement],
    ) -> str:
        """Generate human-readable explanation of analysis."""
        romans = " - ".join(c.roman_numeral for c in chords)

        explanation = f"Functional progression: {romans}."

        if progression_type != ProgressionType.OTHER:
            explanation += f" ({progression_type.value.replace('_', ' ')})"

        if chromatic_elements:
            chromatic_count = len(chromatic_elements)
            explanation += f". Contains {chromatic_count} chromatic element(s)."

        return explanation

    def _calculate_roman_numeral(
        self, chord_match: ChordMatch, key_center: str, mode: str
    ) -> str:
        """Calculate Roman numeral for chord in key context."""
        key_pitch = NOTE_TO_PITCH_CLASS.get(key_center, 0)
        chord_pitch = chord_match.root_pitch

        scale_degree = (chord_pitch - key_pitch) % 12

        # Get basic Roman numeral
        if mode == "major":
            roman_map = {
                0: "I",
                2: "ii",
                4: "iii",
                5: "IV",
                7: "V",
                9: "vi",
                11: "vii°",
            }
        else:
            roman_map = {
                0: "i",
                2: "ii°",
                3: "III",
                5: "iv",
                7: "V",
                8: "VI",
                10: "bVII",  # subtonic in minor is conventionally ♭VII
            }

        roman = roman_map.get(scale_degree, "X")  # X for unknown/chromatic

        # Adjust for chord quality if it doesn't match expected
        if roman == "X":
            # Check for secondary dominants
            if scale_degree in self.secondary_dominants:
                roman = self.secondary_dominants[scale_degree]
            else:
                # Generic chromatic notation
                accidental = self._get_accidental_for_degree(
                    scale_degree, key_center, mode
                )
                degree_roman = ["I", "II", "III", "IV", "V", "VI", "VII"][
                    scale_degree // 2
                ]
                roman = f"{accidental}{degree_roman}"

        return roman

    def _get_accidental_for_degree(
        self, scale_degree: int, key_center: str, mode: str
    ) -> str:
        """Get accidental symbol for chromatic scale degree."""
        # Simplified - could be more sophisticated
        chromatic_degrees = {1: "b", 3: "b", 6: "b", 8: "b", 10: "b"}
        return chromatic_degrees.get(scale_degree, "")

    def _generate_figured_bass(self, chord_match: ChordMatch) -> str:
        """Generate figured bass notation for chord."""
        if chord_match.inversion == 0:
            return ""  # Root position
        elif chord_match.inversion == 1:
            return "⁶"  # First inversion
        elif chord_match.inversion == 2:
            return "⁶₄"  # Second inversion
        else:
            return "⁷"  # Assume seventh chord

    def _detect_cadences(self, chords: List[FunctionalChordAnalysis]) -> List[Cadence]:
        """Detect cadential patterns in progression."""
        cadences = []

        for i in range(len(chords) - 1):
            current = chords[i]
            next_chord = chords[i + 1]

            # V-I authentic cadence
            if (
                current.function == ChordFunction.DOMINANT
                and next_chord.function == ChordFunction.TONIC
            ):
                cadences.append(
                    Cadence(
                        type="authentic",
                        chords=[current, next_chord],
                        strength=0.9,
                        position=(
                            "phrase_ending" if i == len(chords) - 2 else "mid_phrase"
                        ),
                    )
                )

            # IV-I plagal cadence
            elif (
                current.function == ChordFunction.SUBDOMINANT
                and next_chord.function == ChordFunction.TONIC
            ):
                cadences.append(
                    Cadence(
                        type="plagal",
                        chords=[current, next_chord],
                        strength=0.7,
                        position=(
                            "phrase_ending" if i == len(chords) - 2 else "mid_phrase"
                        ),
                    )
                )

        return cadences

    def _identify_chromatic_elements(
        self, chords: List[FunctionalChordAnalysis], key_center: str, mode: str
    ) -> List[ChromaticElement]:
        """Identify chromatic harmony elements."""
        chromatic_elements = []

        for i, chord in enumerate(chords):
            if chord.is_chromatic:
                # Simple secondary dominant detection
                if "V/" in chord.roman_numeral:
                    resolution = chords[i + 1] if i + 1 < len(chords) else None
                    chromatic_elements.append(
                        ChromaticElement(
                            chord=chord,
                            type=ChromaticType.SECONDARY_DOMINANT,
                            resolution=resolution,
                            explanation=f"Secondary dominant {chord.roman_numeral}",
                        )
                    )

        return chromatic_elements

    def _determine_progression_type(
        self, chords: List[FunctionalChordAnalysis], cadences: List[Cadence]
    ) -> ProgressionType:
        """Determine the overall progression type."""
        # Simple heuristics
        if any(c.type == "authentic" for c in cadences):
            return ProgressionType.AUTHENTIC_CADENCE
        elif any(c.type == "plagal" for c in cadences):
            return ProgressionType.PLAGAL_CADENCE
        else:
            return ProgressionType.OTHER

    def _generate_explanation(
        self, chords: List[FunctionalChordAnalysis], key_center: str, mode: str
    ) -> str:
        """Generate human-readable explanation of analysis."""
        romans = " - ".join(c.roman_numeral for c in chords)
        return f"Functional progression in {key_center} {mode}: {romans}"

    def _detect_functional_patterns(
        self, chord_symbols: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect common functional patterns and infer the correct key center.

        This fixes the critical issue where ii-V-I progressions are analyzed in
        the wrong key because the first chord is assumed to be tonic.

        Returns:
            Dictionary with tonic and is_minor if pattern detected, None otherwise
        """
        if len(chord_symbols) < 3:
            return None

        # ii-V-I PATTERN DETECTION (most critical)
        # Check if progression has intervallic pattern of ii-V-I
        try:
            # Extract chord roots
            roots = []
            qualities = []

            for chord_symbol in chord_symbols[-3:]:  # Last 3 chords
                # Parse chord root
                root = chord_symbol[0]
                if len(chord_symbol) > 1 and chord_symbol[1] in ["#", "b"]:
                    root = chord_symbol[:2]
                roots.append(root)

                # Parse chord quality
                chord_lower = chord_symbol.lower()
                if "m7b5" in chord_lower or "ø" in chord_symbol:
                    qualities.append("half_dim")
                elif "m7" in chord_lower or (
                    chord_lower.endswith("m") and "7" not in chord_lower
                ):
                    qualities.append("minor")
                elif (
                    "7" in chord_lower
                    and "maj7" not in chord_lower
                    and "M7" not in chord_symbol
                ):
                    qualities.append("dominant")
                elif "maj7" in chord_lower or "M7" in chord_symbol:
                    qualities.append("major7")
                elif "m" in chord_lower and "M" not in chord_symbol:
                    qualities.append("minor")
                else:
                    qualities.append("major")

            # Convert to semitones for interval analysis
            root_to_semitone = {
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

            if len(roots) >= 3:
                root1_st = root_to_semitone.get(roots[-3], 0)  # ii
                root2_st = root_to_semitone.get(roots[-2], 0)  # V
                root3_st = root_to_semitone.get(roots[-1], 0)  # I

                # ii-V-I intervals: ii->V (up 5 semitones), V->I (up 5 semitones)
                interval_ii_to_v = (root2_st - root1_st) % 12
                interval_v_to_i = (root3_st - root2_st) % 12

                if interval_ii_to_v == 5 and interval_v_to_i == 5:  # Perfect 4ths up
                    # This is a ii-V-I pattern!
                    tonic_root = roots[-1]  # Last chord is tonic

                    # Determine major/minor from V chord quality and final chord
                    is_minor = False
                    if qualities[-1] == "minor":  # Final chord is minor = minor key
                        is_minor = True
                    elif qualities[-2] == "dominant" and qualities[-1] in [
                        "major",
                        "major7",
                    ]:
                        is_minor = False  # V7->I = major key

                    return {
                        "tonic": tonic_root,
                        "is_minor": is_minor,
                        "pattern": "ii-V-I",
                        "confidence": 0.9,
                    }

        except (KeyError, IndexError):
            pass

        # AUTHENTIC CADENCE DETECTION (V-I, V7-I)
        if len(chord_symbols) >= 2:
            try:
                last_two = chord_symbols[-2:]

                # Parse last two chord roots
                roots = []
                qualities = []
                for chord_symbol in last_two:
                    root = chord_symbol[0]
                    if len(chord_symbol) > 1 and chord_symbol[1] in ["#", "b"]:
                        root = chord_symbol[:2]
                    roots.append(root)

                    chord_lower = chord_symbol.lower()
                    if "7" in chord_lower and "maj7" not in chord_lower:
                        qualities.append("dominant")
                    elif "m" in chord_lower:
                        qualities.append("minor")
                    else:
                        qualities.append("major")

                # Check for V-I relationship (up 5 semitones)
                root1_st = root_to_semitone.get(roots[0], 0)
                root2_st = root_to_semitone.get(roots[1], 0)
                interval = (root2_st - root1_st) % 12

                if interval == 5 and qualities[0] == "dominant":  # V or V7 to I
                    return {
                        "tonic": roots[1],
                        "is_minor": qualities[1] == "minor",
                        "pattern": "V-I",
                        "confidence": 0.8,
                    }

            except (KeyError, IndexError):
                pass

        # vi-IV-I-V PATTERN DETECTION (very common pop progression)
        if len(chord_symbols) == 4:
            try:
                # Extract all four chord roots
                roots = []
                qualities = []

                for chord_symbol in chord_symbols:
                    root = chord_symbol[0]
                    if len(chord_symbol) > 1 and chord_symbol[1] in ["#", "b"]:
                        root = chord_symbol[:2]
                    roots.append(root)

                    chord_lower = chord_symbol.lower()
                    if "m" in chord_lower and "M" not in chord_symbol:
                        qualities.append("minor")
                    else:
                        qualities.append("major")

                # Convert to semitones
                semitones = [root_to_semitone.get(root, 0) for root in roots]

                # Check for vi-IV-I-V intervallic pattern in a major key
                # If we assume the 3rd chord (index 2) is the tonic (I):
                if len(semitones) == 4:
                    tonic_st = semitones[2]  # Third chord as potential tonic

                    # Calculate expected positions relative to this tonic
                    expected_vi = (tonic_st + 9) % 12  # vi is 9 semitones above I
                    expected_iv = (tonic_st + 5) % 12  # IV is 5 semitones above I
                    expected_v = (tonic_st + 7) % 12  # V is 7 semitones above I

                    # Check if progression matches vi-IV-I-V pattern
                    if (
                        semitones[0] == expected_vi  # First chord is vi
                        and semitones[1] == expected_iv  # Second chord is IV
                        and semitones[2] == tonic_st  # Third chord is I
                        and semitones[3] == expected_v  # Fourth chord is V
                        and qualities[0] == "minor"  # vi should be minor
                        and qualities[1] == "major"  # IV should be major
                        and qualities[2] == "major"  # I should be major
                        and qualities[3] == "major"
                    ):  # V should be major

                        return {
                            "tonic": roots[2],  # Third chord is tonic
                            "is_minor": False,  # This is a major key pattern
                            "pattern": "vi-IV-I-V",
                            "confidence": 0.85,
                        }

            except (KeyError, IndexError):
                pass

        return None
