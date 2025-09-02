"""
Algorithmic Suggestion Engine

Provides parent key suggestions using proper music theory algorithms
instead of hardcoded pattern matching.

Key Design Principles:
1. Leverage existing analyzers (functional, modal, chromatic)
2. Use systematic multi-key analysis and comparison
3. Detect improvement opportunities algorithmically
4. No hardcoded chord names or key-specific patterns
"""

import logging
from dataclasses import dataclass
from typing import Any, List, Optional

from ..core.chromatic_analysis import ChromaticAnalyzer
from ..core.enhanced_modal_analyzer import EnhancedModalAnalyzer
from ..core.functional_harmony import FunctionalHarmonyAnalyzer
from ..analysis_types import KeySuggestion


@dataclass
class KeyAnalysisResult:
    """Result of analyzing a progression in a specific key."""

    key: str
    confidence: float
    has_roman_numerals: bool
    roman_numerals: List[str]
    analysis_type: str  # 'functional', 'modal', 'chromatic'
    pattern_matches: List[str]  # Detected patterns (ii-V-I, vi-IV-I-V, etc.)
    improvement_score: float  # How much better this is than no key


class AlgorithmicSuggestionEngine:
    """
    Algorithmic engine for generating parent key suggestions.

    Uses existing music theory analyzers to systematically test keys
    and identify improvements, rather than hardcoded pattern matching.
    """

    # Common keys to test for suggestions
    COMMON_KEYS = [
        # Major keys (circle of fifths)
        "C major",
        "G major",
        "D major",
        "A major",
        "E major",
        "B major",
        "F# major",
        "Db major",
        "Ab major",
        "Eb major",
        "Bb major",
        "F major",
        # Natural minor keys
        "A minor",
        "E minor",
        "B minor",
        "F# minor",
        "C# minor",
        "G# minor",
        "D# minor",
        "Bb minor",
        "F minor",
        "C minor",
        "G minor",
        "D minor",
    ]

    def __init__(self) -> None:
        self.functional_analyzer = FunctionalHarmonyAnalyzer()
        self.modal_analyzer = EnhancedModalAnalyzer()
        self.chromatic_analyzer = ChromaticAnalyzer()

    async def generate_suggestions(
        self,
        chords: List[str],
        current_analysis_confidence: float,
        current_roman_numerals: List[str],
    ) -> List[KeySuggestion]:
        """
        Generate parent key suggestions algorithmically.

        Strategy:
        1. Test progression in multiple common keys
        2. Compare analysis quality (confidence, Roman numerals, patterns)
        3. Suggest keys that provide significant improvement
        4. Rank by improvement potential and theoretical strength
        """

        # Don't suggest if we already have good analysis with Roman numerals
        if current_analysis_confidence > 0.8 and current_roman_numerals:
            return []

        # Don't suggest for very poor analysis (likely invalid input)
        if current_analysis_confidence < 0.35:
            return []

        # Don't suggest for minimal progressions
        if len(chords) < 2:
            return []

        # Analyze progression in multiple keys
        key_results = await self._analyze_in_multiple_keys(chords)

        # Find keys that offer significant improvement
        suggestions = self._identify_improvements(
            key_results, current_analysis_confidence, current_roman_numerals
        )

        # Sort by improvement potential
        suggestions.sort(key=lambda s: s.confidence, reverse=True)

        return suggestions[:3]  # Return top 3 suggestions

    async def _analyze_in_multiple_keys(
        self, chords: List[str]
    ) -> List[KeyAnalysisResult]:
        """Analyze progression systematically across multiple keys."""
        results = []

        for key in self.COMMON_KEYS:
            try:
                result = await self._analyze_in_key(chords, key)
                if result:
                    results.append(result)
            except (ValueError, TypeError, KeyError) as e:
                # Skip keys that cause expected analysis errors
                #   (invalid chords, parsing issues)
                logging.debug(f"Analysis failed for key {key}: {e}")
                continue
            except Exception as e:
                # Log unexpected errors but continue with other keys  # nosec B112
                logging.warning(f"Unexpected error analyzing key {key}: {e}")
                continue

        return results

    async def _analyze_in_key(
        self, chords: List[str], key: str
    ) -> Optional[KeyAnalysisResult]:
        """Analyze progression in a specific key using existing analyzers."""

        # Parse key to determine if major/minor (currently unused)
        # is_minor = "minor" in key.lower()
        # key_root = key.replace(" major", "").replace(" minor", "")

        try:
            # Try functional analysis first (most common)
            functional_result = await self.functional_analyzer.analyze_functionally(
                chords, key
            )

            if functional_result and functional_result.confidence > 0.4:
                # Extract roman numerals from chord analyses
                roman_numerals = [
                    chord.roman_numeral for chord in functional_result.chords
                ]
                patterns = self._detect_functional_patterns(roman_numerals)
                return KeyAnalysisResult(
                    key=key,
                    confidence=functional_result.confidence,
                    has_roman_numerals=len(roman_numerals) > 0,
                    roman_numerals=roman_numerals,
                    analysis_type="functional",
                    pattern_matches=patterns,
                    improvement_score=self._calculate_improvement_score(
                        functional_result
                    ),
                )

            # Try modal analysis
            modal_result = self.modal_analyzer.analyze_modal_characteristics(
                chords, key
            )

            if modal_result and modal_result.confidence > 0.5:
                patterns = self._detect_modal_patterns(modal_result.roman_numerals)
                return KeyAnalysisResult(
                    key=key,
                    confidence=modal_result.confidence,
                    has_roman_numerals=len(modal_result.roman_numerals) > 0,
                    roman_numerals=modal_result.roman_numerals,
                    analysis_type="modal",
                    pattern_matches=patterns,
                    improvement_score=self._calculate_improvement_score(modal_result),
                )

        except Exception as e:
            # Analysis failed in this key - for debugging
            print(f"Analysis failed for {key}: {e}")
            pass

        return None

    def _detect_functional_patterns(self, roman_numerals: List[str]) -> List[str]:
        """Detect common functional patterns algorithmically."""
        if len(roman_numerals) < 2:
            return []

        patterns = []

        # ii-V-I patterns (any key)
        if len(roman_numerals) >= 3:
            for i in range(len(roman_numerals) - 2):
                window = roman_numerals[i : i + 3]
                if self._is_ii_v_i_pattern(window):
                    patterns.append("ii-V-I progression")

        # vi-IV-I-V patterns (pop progressions)
        if len(roman_numerals) >= 4:
            for i in range(len(roman_numerals) - 3):
                window = roman_numerals[i : i + 4]
                if self._is_vi_iv_i_v_pattern(window):
                    patterns.append("vi-IV-I-V progression")

        # Authentic cadence patterns
        for i in range(len(roman_numerals) - 1):
            if self._is_authentic_cadence(roman_numerals[i], roman_numerals[i + 1]):
                patterns.append("authentic cadence")

        return patterns

    def _is_ii_v_i_pattern(self, window: List[str]) -> bool:
        """Detect ii-V-I pattern algorithmically using Roman numeral analysis."""
        if len(window) != 3:
            return False

        # Check for ii-V-I pattern (works in any key)
        # ii: some form of 'ii' (minor second degree)
        # V: some form of 'V' (major fifth degree)
        # I: some form of 'I' (tonic)

        chord1_is_ii = "ii" in window[0].lower() or window[0].lower().startswith("ii")
        chord2_is_v = "v" in window[1].lower() and window[1].upper().startswith(
            "V"
        )  # Major V
        chord3_is_i = window[2].lower().startswith("i") or window[2].upper().startswith(
            "I"
        )

        return chord1_is_ii and chord2_is_v and chord3_is_i

    def _is_vi_iv_i_v_pattern(self, window: List[str]) -> bool:
        """Detect vi-IV-I-V pattern algorithmically."""
        if len(window) != 4:
            return False

        # vi-IV-I-V pattern (pop progression)
        chord1_is_vi = window[0].lower().startswith("vi")
        chord2_is_iv = window[1].upper().startswith("IV")
        chord3_is_i = window[2].lower().startswith("i") or window[2].upper().startswith(
            "I"
        )
        chord4_is_v = window[3].upper().startswith("V")

        return chord1_is_vi and chord2_is_iv and chord3_is_i and chord4_is_v

    def _is_authentic_cadence(self, chord1: str, chord2: str) -> bool:
        """Detect V-I authentic cadence."""
        return chord1.upper().startswith("V") and (
            chord2.upper().startswith("I") or chord2.lower().startswith("i")
        )

    def _detect_modal_patterns(self, roman_numerals: List[str]) -> List[str]:
        """Detect modal patterns using existing modal analysis."""
        patterns = []

        # Look for modal-specific characteristics
        rn_str = "-".join(roman_numerals).lower()

        # Mixolydian: bVII chord
        if "bvii" in rn_str:
            patterns.append("Mixolydian characteristic (bVII)")

        # Dorian: Natural VI in minor context
        if any("iv" in rn and "biv" not in rn for rn in roman_numerals):
            patterns.append("Dorian characteristic (natural IV)")

        # Phrygian: bII chord
        if "bii" in rn_str:
            patterns.append("Phrygian characteristic (bII)")

        return patterns

    def _calculate_improvement_score(self, analysis_result: Any) -> float:
        """Calculate how much this key analysis improves upon no-key analysis."""
        score: float = 0.0

        # Base confidence contribution
        confidence = float(getattr(analysis_result, "confidence", 0.0))
        score += confidence * 0.6

        # Roman numerals provide structural clarity
        romans = getattr(analysis_result, "roman_numerals", [])
        if isinstance(romans, list) and romans:
            score += 0.3

        # More roman numerals = better structural understanding
        if isinstance(romans, list):
            score += min(len(romans) * 0.05, 0.2)

        return float(min(score, 1.0))

    def _identify_improvements(
        self,
        key_results: List[KeyAnalysisResult],
        current_confidence: float,
        current_roman_numerals: List[str],
    ) -> List[KeySuggestion]:
        """Identify keys that offer significant improvement."""

        suggestions = []
        current_has_romans = len(current_roman_numerals) > 0

        for result in key_results:
            improvement_threshold = 0.15  # Must improve by at least 15%

            # Calculate improvement over current analysis
            confidence_improvement = result.confidence - current_confidence
            structural_improvement = (
                result.has_roman_numerals and not current_has_romans
            )

            # Suggest if significant improvement
            if (
                confidence_improvement > improvement_threshold
                or structural_improvement
                or (result.confidence > 0.75 and current_confidence < 0.6)
            ):

                # Generate human-readable reason
                reason = self._generate_suggestion_reason(
                    result, current_confidence, current_has_romans
                )

                # Boost confidence for pattern matches
                pattern_bonus = 0.15 if result.pattern_matches else 0.1
                final_confidence = min(result.confidence + pattern_bonus, 1.0)

                suggestions.append(
                    KeySuggestion(
                        suggested_key=result.key,
                        confidence=final_confidence,
                        reason=reason,
                        detected_pattern=(
                            ", ".join(result.pattern_matches)
                            if result.pattern_matches
                            else f"{result.analysis_type} analysis"
                        ),
                        potential_improvement=(
                            "Provides Roman numeral analysis and clear harmonic "
                            "function"
                            if structural_improvement
                            else (
                                "Improves analysis confidence from "
                                f"{current_confidence:.1f} to {result.confidence:.1f}"
                            )
                        ),
                    )
                )

        return suggestions

    def _generate_suggestion_reason(
        self,
        result: KeyAnalysisResult,
        current_confidence: float,
        current_has_romans: bool,
    ) -> str:
        """Generate human-readable reason for suggestion."""

        if result.pattern_matches:
            # Pattern-based reason
            primary_pattern = result.pattern_matches[0]
            return f"Contains {primary_pattern}"

        elif result.has_roman_numerals and not current_has_romans:
            # Structural improvement reason
            return "Provides clear harmonic structure with Roman numeral analysis"

        elif result.confidence > current_confidence + 0.2:
            # Confidence improvement reason
            return f"Significantly improves {result.analysis_type} analysis confidence"

        else:
            # General improvement reason
            return f"Alternative {result.analysis_type} interpretation in {result.key}"
