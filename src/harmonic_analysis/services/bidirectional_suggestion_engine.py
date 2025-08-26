"""
Bidirectional Suggestion Engine

Intelligently detects when parent keys should be added OR removed from analysis.
Uses algorithmic music theory approaches - no hardcoded patterns.

Key Features:
1. "Add Key" suggestions when key context would significantly improve analysis
2. "Remove Key" suggestions when provided key doesn't help or adds confusion
3. Key relevance scoring based on measurable improvement metrics
4. Bidirectional feedback for optimal user experience
"""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional

from ..core.enhanced_modal_analyzer import EnhancedModalAnalyzer
from ..core.functional_harmony import FunctionalHarmonyAnalyzer
from ..types import AnalysisOptions, AnalysisSuggestions

if TYPE_CHECKING:
    pass

from .algorithmic_suggestion_engine import AlgorithmicSuggestionEngine


class SuggestionType(Enum):
    """Types of suggestions the system can make."""

    ADD_KEY = "add_key"  # Suggest adding a parent key
    REMOVE_KEY = "remove_key"  # Suggest removing provided key
    CHANGE_KEY = "change_key"  # Suggest different key than provided


@dataclass
class KeyRelevanceScore:
    """Detailed scoring of how relevant a key is for a progression."""

    total_score: float  # Overall relevance (0.0 - 1.0)

    # Component scores (0.0 - 1.0 each)
    roman_numeral_improvement: float
    confidence_improvement: float
    analysis_type_improvement: float
    pattern_clarity_improvement: float

    # Analysis details
    without_key_confidence: float
    with_key_confidence: float
    without_key_romans: List[str]
    with_key_romans: List[str]
    detected_patterns: List[str]


@dataclass
class BidirectionalSuggestion:
    """Enhanced suggestion with bidirectional capability."""

    suggestion_type: SuggestionType
    suggested_key: Optional[str]  # None for "remove key" suggestions
    current_key: Optional[str]  # Key currently provided (if any)

    confidence: float
    relevance_score: KeyRelevanceScore
    reason: str
    potential_improvement: str

    # Enhanced details
    improvement_summary: List[str]  # What specifically improves
    trade_offs: List[str]  # What might be lost (if any)
    detected_pattern: str = "algorithmic analysis"  # Default value


class BidirectionalSuggestionEngine:
    """
    Intelligent bidirectional suggestion engine.

    Determines when keys should be added, removed, or changed based on
    algorithmic analysis of musical improvement potential.
    """

    def __init__(self) -> None:
        self.add_key_engine = AlgorithmicSuggestionEngine()
        self.functional_analyzer = FunctionalHarmonyAnalyzer()
        self.modal_analyzer = EnhancedModalAnalyzer()

    async def generate_bidirectional_suggestions(
        self,
        chords: List[str],
        options: AnalysisOptions,
        current_analysis_confidence: float = 0.4,
        current_roman_numerals: Optional[List[str]] = None,
    ) -> AnalysisSuggestions:
        """
        Generate intelligent bidirectional suggestions.

        Args:
            chords: The chord progression to analyze
            options: Analysis options including parent key
            current_analysis_confidence: Current analysis confidence
            current_roman_numerals: Current roman numerals (if any)

        Returns:
            List of bidirectional suggestions (add, remove, or change key)
        """
        suggestions = []
        current_roman_numerals = current_roman_numerals or []
        current_key = options.parent_key

        if current_key:
            # Key is provided - check if it's beneficial or should be removed/changed
            suggestions.extend(
                await self._evaluate_provided_key(
                    chords,
                    current_key,
                    current_analysis_confidence,
                    current_roman_numerals,
                )
            )
        else:
            # No key provided - check if adding one would help
            suggestions.extend(
                await self._evaluate_missing_key(
                    chords, current_analysis_confidence, current_roman_numerals
                )
            )

        # Sort by relevance score
        suggestions.sort(key=lambda s: s.relevance_score.total_score, reverse=True)

        # Convert BidirectionalSuggestion list to AnalysisSuggestions format
        # For now, we'll put all suggestions in parent_key_suggestions
        # TODO: Implement proper categorization based on suggestion type
        from ..types import KeySuggestion

        parent_key_suggestions = []
        for bidirectional_suggestion in suggestions[:3]:
            # Only create KeySuggestion for suggestions that have a suggested_key
            if bidirectional_suggestion.suggested_key is not None:
                key_suggestion = KeySuggestion(
                    suggested_key=bidirectional_suggestion.suggested_key,
                    confidence=bidirectional_suggestion.confidence,
                    reason=bidirectional_suggestion.reason,
                    detected_pattern=bidirectional_suggestion.detected_pattern,
                    potential_improvement=(
                        bidirectional_suggestion.potential_improvement
                    ),
                )
                parent_key_suggestions.append(key_suggestion)

        return AnalysisSuggestions(
            parent_key_suggestions=parent_key_suggestions, general_suggestions=[]
        )

    async def _evaluate_provided_key(
        self,
        chords: List[str],
        provided_key: str,
        current_confidence: float,
        current_romans: List[str],
    ) -> List[BidirectionalSuggestion]:
        """Evaluate whether a provided key is beneficial."""
        suggestions = []

        # Get analysis WITH provided key
        with_key_result = await self._analyze_with_key(chords, provided_key)

        # Get analysis WITHOUT key
        without_key_result = await self._analyze_with_key(chords, None)

        # Calculate relevance score
        relevance = self._calculate_key_relevance(
            without_key_result, with_key_result, chords
        )

        # Determine suggestion type based on relevance
        if relevance.total_score < 0.15:
            # Key provides minimal benefit - suggest removal
            suggestions.append(
                BidirectionalSuggestion(
                    suggestion_type=SuggestionType.REMOVE_KEY,
                    suggested_key=None,
                    current_key=provided_key,
                    confidence=1.0
                    - relevance.total_score,  # High confidence in removal
                    relevance_score=relevance,
                    reason=self._generate_remove_key_reason(relevance),
                    potential_improvement=(
                        "Simplifies analysis without losing information"
                    ),
                    improvement_summary=self._generate_remove_improvements(relevance),
                    trade_offs=self._generate_remove_tradeoffs(relevance),
                )
            )

        elif relevance.total_score < 0.4:
            # Key provides some benefit but check for better alternatives
            alternative_suggestions = await self._find_better_keys(chords, provided_key)
            for alt_suggestion in alternative_suggestions:
                if (
                    alt_suggestion.relevance_score.total_score
                    > relevance.total_score + 0.2
                ):
                    suggestions.append(
                        BidirectionalSuggestion(
                            suggestion_type=SuggestionType.CHANGE_KEY,
                            suggested_key=alt_suggestion.suggested_key,
                            current_key=provided_key,
                            confidence=alt_suggestion.confidence,
                            relevance_score=alt_suggestion.relevance_score,
                            reason=(
                                "Alternative key provides better analysis than "
                                f"{provided_key}"
                            ),
                            potential_improvement=alt_suggestion.potential_improvement,
                            improvement_summary=alt_suggestion.improvement_summary,
                            trade_offs=[
                                f"Changes interpretation from {provided_key} context"
                            ],
                        )
                    )

        # If relevance.total_score >= 0.4, key is beneficial - no suggestion needed

        return suggestions

    async def _evaluate_missing_key(
        self, chords: List[str], current_confidence: float, current_romans: List[str]
    ) -> List[BidirectionalSuggestion]:
        """Evaluate whether adding a key would be beneficial."""
        suggestions = []

        # Use existing "add key" logic from AlgorithmicSuggestionEngine
        add_key_suggestions = await self.add_key_engine.generate_suggestions(
            chords, current_confidence, current_romans
        )

        # Convert to bidirectional suggestions with enhanced scoring
        for suggestion in add_key_suggestions:
            # Get detailed relevance analysis
            without_key_result = await self._analyze_with_key(chords, None)
            with_key_result = await self._analyze_with_key(
                chords, suggestion.suggested_key
            )

            relevance = self._calculate_key_relevance(
                without_key_result, with_key_result, chords
            )

            # Only suggest if relevance is meaningful
            if relevance.total_score > 0.4:
                suggestions.append(
                    BidirectionalSuggestion(
                        suggestion_type=SuggestionType.ADD_KEY,
                        suggested_key=suggestion.suggested_key,
                        current_key=None,
                        confidence=suggestion.confidence,
                        relevance_score=relevance,
                        reason=suggestion.reason,
                        potential_improvement=suggestion.potential_improvement,
                        detected_pattern=suggestion.detected_pattern,
                        improvement_summary=self._generate_add_improvements(relevance),
                        trade_offs=self._generate_add_tradeoffs(relevance),
                    )
                )

        return suggestions

    async def _analyze_with_key(self, chords: List[str], key: Optional[str]) -> Dict:
        """Analyze progression with or without a key context."""
        # Use the direct analyzers to avoid circular import
        # Options object not needed here for direct analyzer calls

        # Run both functional and modal analysis
        functional_result = await self.functional_analyzer.analyze_functionally(
            chords, key
        )
        modal_result = self.modal_analyzer.analyze_modal_characteristics(chords, key)

        # Determine primary analysis type and confidence
        functional_confidence = (
            functional_result.confidence if functional_result else 0.0
        )
        modal_confidence = modal_result.confidence if modal_result else 0.0

        if functional_confidence >= modal_confidence:
            result = {
                "confidence": functional_confidence,
                "roman_numerals": (
                    [chord.roman_numeral for chord in functional_result.chords]
                    if functional_result
                    else []
                ),
                "analysis_type": "functional",
                "analysis": (
                    functional_result.explanation
                    if functional_result
                    else "Basic progression"
                ),
                "key_signature": (
                    functional_result.key_center if functional_result else key
                ),
                "alternatives_count": 1 if modal_confidence > 0.4 else 0,
            }
        else:
            result = {
                "confidence": modal_confidence,
                "roman_numerals": [],  # Modal analysis typically doesn't provide Romans
                "analysis_type": "modal",
                "analysis": (
                    f"{modal_result.mode_name} modal progression"
                    if modal_result
                    else "Modal progression"
                ),
                "key_signature": (
                    modal_result.parent_key_signature if modal_result else key
                ),
                "alternatives_count": 1 if functional_confidence > 0.4 else 0,
            }

        return result

    async def _calculate_key_relevance_score(
        self, chords: List[str], key: str, current_key: Optional[str]
    ) -> KeyRelevanceScore:
        """Calculate key relevance score for test purposes."""
        without_key_result = await self._analyze_with_key(chords, current_key)
        with_key_result = await self._analyze_with_key(chords, key)

        return self._calculate_key_relevance(
            without_key_result, with_key_result, chords
        )

    def _calculate_key_relevance(
        self, without_key: Dict, with_key: Dict, chords: List[str]
    ) -> KeyRelevanceScore:
        """Calculate how relevant/beneficial a key is algorithmically."""

        # Component 1: Roman numeral improvement (0.3 weight)
        without_romans = without_key.get("roman_numerals", [])
        with_romans = with_key.get("roman_numerals", [])

        roman_score = 0.0
        if not without_romans and with_romans:
            roman_score = 1.0  # Provides romans where none existed
        elif len(with_romans) > len(without_romans):
            roman_score = 0.7  # Improves roman numeral coverage
        elif with_romans and without_romans:
            # Compare quality of romans (more complex analysis needed)
            roman_score = 0.3

        # Component 2: Confidence improvement (0.2 weight)
        confidence_delta = with_key["confidence"] - without_key["confidence"]
        confidence_score = min(max(confidence_delta * 2, 0.0), 1.0)  # Scale to 0-1

        # Component 3: Analysis type improvement (0.2 weight)
        type_score = 0.0
        without_type = without_key.get("analysis_type", "modal")
        with_type = with_key.get("analysis_type", "modal")

        if without_type == "modal" and with_type == "functional":
            type_score = 0.8  # Modal to functional often beneficial
        elif without_type == "functional" and with_type == "functional":
            type_score = 0.4  # Functional to functional - some benefit
        elif without_type == with_type:
            type_score = 0.2  # Same type - minimal type benefit

        # Component 4: Pattern clarity improvement (0.3 weight)
        pattern_score = self._calculate_pattern_clarity_score(
            chords, without_key, with_key
        )

        # Weighted total score
        total_score = (
            roman_score * 0.3
            + confidence_score * 0.2
            + type_score * 0.2
            + pattern_score * 0.3
        )

        return KeyRelevanceScore(
            total_score=min(total_score, 1.0),
            roman_numeral_improvement=roman_score,
            confidence_improvement=confidence_score,
            analysis_type_improvement=type_score,
            pattern_clarity_improvement=pattern_score,
            without_key_confidence=without_key["confidence"],
            with_key_confidence=with_key["confidence"],
            without_key_romans=without_romans,
            with_key_romans=with_romans,
            detected_patterns=self._detect_patterns_in_analysis(with_key),
        )

    def _calculate_pattern_clarity_score(
        self, chords: List[str], without_key: Dict, with_key: Dict
    ) -> float:
        """Calculate how much clearer musical patterns become with key context."""
        score = 0.0

        # Check for common patterns that become clearer

        # ii-V-I patterns
        if self._contains_ii_v_i_pattern(with_key.get("roman_numerals", [])):
            score += 0.4

        # Authentic cadences
        if "authentic" in with_key.get("analysis", "").lower():
            score += 0.3

        # Circle of fifths movement
        if self._contains_circle_of_fifths(chords):
            score += 0.2

        # Modal characteristics
        if (
            "modal" in with_key.get("analysis", "").lower()
            and len(with_key.get("roman_numerals", [])) > 0
        ):
            score += 0.3

        return min(score, 1.0)

    def _contains_ii_v_i_pattern(self, romans: List[str]) -> bool:
        """Check if roman numerals contain ii-V-I pattern."""
        if len(romans) < 3:
            return False

        romans_str = "-".join(romans).lower()
        patterns = ["ii-v-i", "ii7-v7-i", "iim7-v7-i", "ii-v7-i"]
        return any(pattern in romans_str for pattern in patterns)

    def _contains_circle_of_fifths(self, chords: List[str]) -> bool:
        """Detect circle of fifths movement algorithmically."""
        if len(chords) < 3:
            return False

        # Check for descending fifths pattern
        # This is simplified - could be enhanced with pitch class analysis
        fifth_progressions = [
            ["C", "F", "Bb"],
            ["G", "C", "F"],
            ["D", "G", "C"],
            ["A", "D", "G"],
            ["E", "A", "D"],
            ["B", "E", "A"],
        ]

        for i in range(len(chords) - 2):
            chord_slice = [
                c.split("/")[0].replace("m", "").replace("7", "")
                for c in chords[i : i + 3]
            ]
            if chord_slice in fifth_progressions:
                return True

        return False

    def _detect_patterns_in_analysis(self, analysis_result: Dict) -> List[str]:
        """Extract detected patterns from analysis result."""
        patterns = []
        analysis = analysis_result.get("analysis", "").lower()

        if "ii-v-i" in analysis:
            patterns.append("ii-V-I progression")
        if "authentic" in analysis:
            patterns.append("authentic cadence")
        if "plagal" in analysis:
            patterns.append("plagal cadence")
        if "deceptive" in analysis:
            patterns.append("deceptive cadence")
        if "circle" in analysis:
            patterns.append("circle of fifths")

        return patterns

    async def _find_better_keys(
        self, chords: List[str], current_key: str
    ) -> List[BidirectionalSuggestion]:
        """Find alternative keys that might work better than current key."""

        # Test related keys
        test_keys = self._get_related_keys(current_key)
        alternatives = []

        for test_key in test_keys:
            test_result = await self._analyze_with_key(chords, test_key)
            current_result = await self._analyze_with_key(chords, current_key)

            relevance = self._calculate_key_relevance(
                current_result, test_result, chords
            )

            if relevance.total_score > 0.5:  # Significantly better
                alternatives.append(
                    BidirectionalSuggestion(
                        suggestion_type=SuggestionType.CHANGE_KEY,
                        suggested_key=test_key,
                        current_key=current_key,
                        confidence=0.7 + relevance.total_score * 0.3,
                        relevance_score=relevance,
                        reason=(
                            f"{test_key} provides clearer analysis than {current_key}"
                        ),
                        potential_improvement=(
                            "Improved pattern recognition and harmonic clarity"
                        ),
                        improvement_summary=self._generate_change_improvements(
                            relevance
                        ),
                        trade_offs=[
                            f"Different harmonic interpretation than {current_key}"
                        ],
                    )
                )

        return alternatives

    def _get_related_keys(self, key: str) -> List[str]:
        """Get musically related keys to test as alternatives."""
        # This is simplified - could be enhanced with circle of fifths logic
        key_relationships = {
            "C major": ["A minor", "F major", "G major", "D minor", "E minor"],
            "A minor": ["C major", "F major", "D minor", "G major", "E minor"],
            "G major": ["C major", "D major", "E minor", "A minor", "B minor"],
            "F major": ["C major", "Bb major", "D minor", "A minor", "G minor"],
            "D major": ["G major", "A major", "B minor", "F# minor", "E minor"],
            "E minor": ["G major", "C major", "A minor", "D major", "B minor"],
        }

        return key_relationships.get(key, ["C major", "A minor", "G major"])

    def _generate_remove_key_reason(self, relevance: KeyRelevanceScore) -> str:
        """Generate human-readable reason for removing key."""
        if relevance.confidence_improvement < 0.05:
            return "Parent key doesn't improve analysis confidence"
        elif not relevance.with_key_romans and not relevance.without_key_romans:
            return "Parent key doesn't provide additional harmonic information"
        elif relevance.analysis_type_improvement < 0.1:
            return "Analysis type remains the same with or without parent key"
        else:
            return "Parent key provides minimal analytical benefit"

    def _generate_add_improvements(self, relevance: KeyRelevanceScore) -> List[str]:
        """Generate list of improvements from adding key."""
        improvements = []

        if relevance.roman_numeral_improvement > 0.5:
            improvements.append("Provides Roman numeral analysis")
        if relevance.confidence_improvement > 0.15:
            improvements.append(
                f"Increases confidence by {relevance.confidence_improvement:.0%}"
            )
        if relevance.analysis_type_improvement > 0.5:
            improvements.append("Enables functional harmonic analysis")
        if relevance.pattern_clarity_improvement > 0.5:
            improvements.append("Clarifies common chord progression patterns")

        return improvements

    def _generate_remove_improvements(self, relevance: KeyRelevanceScore) -> List[str]:
        """Generate list of improvements from removing key."""
        return [
            "Simplifies analysis without losing information",
            "Reduces analytical complexity",
            "Maintains current analysis quality",
        ]

    def _generate_change_improvements(self, relevance: KeyRelevanceScore) -> List[str]:
        """Generate list of improvements from changing key."""
        improvements = []

        if relevance.confidence_improvement > 0.2:
            improvements.append("Significantly improves analysis confidence")
        if relevance.roman_numeral_improvement > 0.3:
            improvements.append("Provides better Roman numeral analysis")
        if relevance.pattern_clarity_improvement > 0.4:
            improvements.append("Reveals clearer harmonic patterns")

        return improvements

    def _generate_add_tradeoffs(self, relevance: KeyRelevanceScore) -> List[str]:
        """Generate potential tradeoffs of adding key."""
        tradeoffs = []

        if relevance.analysis_type_improvement > 0.5:
            tradeoffs.append("May shift from modal to functional interpretation")
        if relevance.confidence_improvement < 0.1:
            tradeoffs.append("Only modest improvement in analysis certainty")

        return tradeoffs or ["No significant tradeoffs"]

    def _generate_remove_tradeoffs(self, relevance: KeyRelevanceScore) -> List[str]:
        """Generate potential tradeoffs of removing key."""
        tradeoffs = []

        if relevance.with_key_romans and not relevance.without_key_romans:
            tradeoffs.append("Loses Roman numeral analysis")
        if relevance.confidence_improvement > 0.1:
            tradeoffs.append("Slightly reduces analysis confidence")

        return tradeoffs or ["No significant tradeoffs"]
