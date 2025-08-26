"""
Comprehensive analysis engine coordinating functional, modal, and chromatic analysis.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

from ..core.functional_harmony import (
    FunctionalAnalysisResult,
    FunctionalHarmonyAnalyzer,
)
from ..core.modal_analysis import EnhancedModalAnalyzer, ModalAnalysisResult
from ..types import AnalysisOptions, MultipleInterpretationResult, UserInputContext
from ..utils.chord_logic import parse_chord_progression


@dataclass
class ModalEnhancementResult:
    """Modal analysis enhancement to functional analysis."""

    applicable_analysis: Optional[Any]  # Legacy compatibility
    enhanced_analysis: Optional[ModalAnalysisResult]
    modal_characteristics: List[str]
    comparison_to_functional: str
    when_to_use_modal: str


@dataclass
class ChromaticAnalysisResult:
    """Chromatic harmony analysis result."""

    secondary_dominants: List[dict]
    borrowed_chords: List[dict]
    chromatic_mediants: List[dict]
    resolution_patterns: List[dict]


@dataclass
class ComprehensiveAnalysisResult:
    """Complete comprehensive analysis result."""

    # Primary analysis (always present)
    functional: FunctionalAnalysisResult

    # Secondary analyses (conditional)
    modal: Optional[ModalEnhancementResult]
    chromatic: Optional[ChromaticAnalysisResult]

    # Analysis metadata
    primary_approach: Literal["functional", "modal", "chromatic"]
    confidence: float
    explanation: str
    pedagogical_value: str

    # User input context
    user_input: UserInputContext


class ComprehensiveAnalysisEngine:
    """Main comprehensive analysis engine."""

    def __init__(self) -> None:
        self.functional_analyzer = FunctionalHarmonyAnalyzer()
        self.modal_analyzer = EnhancedModalAnalyzer()

    async def analyze_comprehensively(
        self, progression_input: str, parent_key: Optional[str] = None
    ) -> ComprehensiveAnalysisResult:
        """
        Analyze chord progression with comprehensive approach.

        Args:
            progression_input: Chord symbols (e.g., "G F C G")
            parent_key: Optional parent key signature (e.g., "C major")

        Returns:
            Comprehensive analysis with multiple perspectives
        """
        if not progression_input.strip():
            raise ValueError("Empty chord progression")

        chord_symbols = self._parse_chord_progression(progression_input)

        # Step 1: Primary functional analysis
        functional_analysis = await self.functional_analyzer.analyze_functionally(
            chord_symbols, parent_key
        )

        # Step 2: Determine if modal analysis adds value
        modal_enhancement = await self._evaluate_modal_enhancement(
            progression_input, functional_analysis, parent_key
        )

        # Step 3: Analyze chromatic elements in detail
        chromatic_analysis = self._analyze_chromatic_elements(functional_analysis)

        # Step 4: Determine primary analytical approach
        primary_approach = self._determine_primary_approach(
            functional_analysis, modal_enhancement, chromatic_analysis
        )

        # Step 5: Calculate overall confidence and create explanation
        confidence = self._calculate_overall_confidence(
            functional_analysis, modal_enhancement
        )

        explanation = self._create_comprehensive_explanation(
            functional_analysis, modal_enhancement, chromatic_analysis, primary_approach
        )

        pedagogical_value = self._create_pedagogical_explanation(
            primary_approach, functional_analysis
        )

        return ComprehensiveAnalysisResult(
            functional=functional_analysis,
            modal=modal_enhancement,
            chromatic=chromatic_analysis,
            primary_approach=primary_approach,
            confidence=confidence,
            explanation=explanation,
            pedagogical_value=pedagogical_value,
            user_input=UserInputContext(
                chord_progression=progression_input,
                parent_key=parent_key,
                analysis_type="chord_progression",
            ),
        )

    async def analyze_with_multiple_interpretations(
        self, progression_input: str, options: Optional[AnalysisOptions] = None
    ) -> MultipleInterpretationResult:
        """
        Analyze with multiple interpretation approach.

        Args:
            progression_input: Chord symbols
            options: Analysis options

        Returns:
            Multiple interpretation analysis result
        """
        if options is None:
            options = AnalysisOptions()

        try:
            # For now, fall back to comprehensive analysis
            # TODO: Implement true multiple interpretation logic
            comprehensive_result = await self.analyze_comprehensively(
                progression_input, options.parent_key
            )

            return self._convert_to_multiple_interpretation_format(
                comprehensive_result, progression_input, options
            )

        except Exception as error:
            raise ValueError(f"Multiple interpretation analysis failed: {error}")

    def _convert_to_multiple_interpretation_format(
        self,
        comprehensive_result: ComprehensiveAnalysisResult,
        progression_input: str,
        options: AnalysisOptions,
    ) -> MultipleInterpretationResult:
        """Convert comprehensive result to multiple interpretation format."""
        from ..types import Evidence, Interpretation

        chord_symbols = self._parse_chord_progression(progression_input)

        # Create primary interpretation
        primary_interpretation = Interpretation(
            type=comprehensive_result.primary_approach,
            confidence=comprehensive_result.confidence,
            analysis=comprehensive_result.explanation,
            roman_numerals=[
                chord.roman_numeral for chord in comprehensive_result.functional.chords
            ],
            key_signature=comprehensive_result.functional.key_signature,
            mode=(
                comprehensive_result.modal.enhanced_analysis.mode_name
                if comprehensive_result.modal
                and comprehensive_result.modal.enhanced_analysis
                else None
            ),
            evidence=[
                Evidence(
                    type="contextual",
                    strength=comprehensive_result.confidence,
                    description="Comprehensive analysis",
                    supported_interpretations=[comprehensive_result.primary_approach],
                    musical_basis=comprehensive_result.pedagogical_value,
                )
            ],
            reasoning=comprehensive_result.explanation,
            theoretical_basis=(
                f"{comprehensive_result.primary_approach} analysis approach"
            ),
        )

        return MultipleInterpretationResult(
            primary_analysis=primary_interpretation,
            alternative_analyses=[],
            metadata={
                "total_interpretations_considered": 1,
                "confidence_threshold": options.confidence_threshold,
                "show_alternatives": False,
                "pedagogical_level": options.pedagogical_level,
                "analysis_time_ms": 0,
            },
            input={
                "chords": chord_symbols,
                "parent_key": options.parent_key,
                "options": options.__dict__,
            },
        )

    async def _evaluate_modal_enhancement(
        self,
        progression_input: str,
        functional_analysis: FunctionalAnalysisResult,
        parent_key: Optional[str],
    ) -> Optional[ModalEnhancementResult]:
        """Evaluate whether modal analysis adds pedagogical value."""

        chord_symbols = self._parse_chord_progression(progression_input)

        # Try enhanced modal analysis
        enhanced_modal_analysis = self.modal_analyzer.analyze_modal_characteristics(
            chord_symbols, parent_key
        )

        # If enhanced analysis has high confidence, use it
        if enhanced_modal_analysis and enhanced_modal_analysis.confidence >= 0.7:
            comparison_to_functional = self._compare_enhanced_analytical_approaches(
                functional_analysis, enhanced_modal_analysis
            )

            return ModalEnhancementResult(
                applicable_analysis=None,  # Legacy field
                enhanced_analysis=enhanced_modal_analysis,
                modal_characteristics=enhanced_modal_analysis.characteristics,
                comparison_to_functional=comparison_to_functional,
                when_to_use_modal=self._explain_when_to_use_enhanced_modal(
                    enhanced_modal_analysis
                ),
            )

        # Fallback to original modal detection
        has_modal_characteristics = self._detect_modal_characteristics(
            functional_analysis
        )

        if not has_modal_characteristics:
            return None

        # Create basic modal enhancement
        modal_characteristics = self._identify_modal_characteristics(
            functional_analysis
        )
        comparison_to_functional = self._compare_analytical_approaches(
            functional_analysis
        )

        return ModalEnhancementResult(
            applicable_analysis=None,
            enhanced_analysis=enhanced_modal_analysis,
            modal_characteristics=modal_characteristics,
            comparison_to_functional=comparison_to_functional,
            when_to_use_modal=self._explain_when_to_use_modal(functional_analysis),
        )

    def _detect_modal_characteristics(
        self, functional_analysis: FunctionalAnalysisResult
    ) -> bool:
        """Detect if progression has modal characteristics."""
        if not functional_analysis.chords:
            return False

        roman_numerals = " ".join(
            chord.roman_numeral for chord in functional_analysis.chords
        )

        # Check for characteristic modal movements
        modal_indicators = ["bVII", "bII", "#IV", "bVI", "bIII"]
        return any(indicator in roman_numerals for indicator in modal_indicators)

    def _identify_modal_characteristics(
        self, functional_analysis: FunctionalAnalysisResult
    ) -> List[str]:
        """Identify specific modal characteristics."""
        characteristics = []
        chords = functional_analysis.chords

        for i in range(len(chords) - 1):
            current = chords[i].roman_numeral
            next_chord = chords[i + 1].roman_numeral

            if current == "bVII" and next_chord == "I":
                characteristics.append("bVII-I cadence (Mixolydian characteristic)")
            elif current == "bII" and next_chord == "I":
                characteristics.append("bII-I cadence (Phrygian characteristic)")
            elif "#IV" in current:
                characteristics.append("#IV chord (Lydian characteristic)")
            elif current == "bVI":
                characteristics.append("bVI chord (modal interchange or natural minor)")

        return characteristics

    def _compare_enhanced_analytical_approaches(
        self,
        functional_analysis: FunctionalAnalysisResult,
        enhanced_modal_analysis: ModalAnalysisResult,
    ) -> str:
        """Compare functional and enhanced modal approaches."""
        functional_romans = " - ".join(
            chord.roman_numeral for chord in functional_analysis.chords
        )
        modal_romans = " - ".join(enhanced_modal_analysis.roman_numerals)

        return (
            (
                f"Functional perspective (in {functional_analysis.key_center}): "
                f"{functional_romans}. "
            )
            + (
                f"Modal perspective ({enhanced_modal_analysis.mode_name}): "
                f"{modal_romans}. "
            )
            + "The modal analysis better explains the structural emphasis on "
            + (
                f"{enhanced_modal_analysis.detected_tonic_center} and "
                "characteristic modal relationships."
            )
        )

    def _compare_analytical_approaches(
        self, functional_analysis: FunctionalAnalysisResult
    ) -> str:
        """Compare functional and basic modal approaches."""
        functional_romans = " - ".join(
            chord.roman_numeral for chord in functional_analysis.chords
        )
        return (
            f"Functional analysis shows: {functional_romans}. Modal analysis "
            "provides alternative perspective on scale relationships."
        )

    def _explain_when_to_use_enhanced_modal(
        self, enhanced_modal_analysis: ModalAnalysisResult
    ) -> str:
        """Explain when enhanced modal analysis is valuable."""
        has_strong_structural = any(
            e.type == "structural" and e.strength >= 0.7
            for e in enhanced_modal_analysis.evidence
        )
        has_cadential = any(
            e.type == "cadential" and e.strength >= 0.8
            for e in enhanced_modal_analysis.evidence
        )

        if has_strong_structural and has_cadential:
            return (
                "Modal analysis is highly recommended - the progression shows "
                f"strong structural emphasis on "
                f"{enhanced_modal_analysis.detected_tonic_center} with "
                "characteristic modal cadences"
            )
        elif has_strong_structural:
            return (
                f"Modal analysis adds value - the structural pattern suggests "
                f"{enhanced_modal_analysis.detected_tonic_center} as the tonal center"
            )
        else:
            return "Modal analysis provides insight into scale-based relationships"

    def _explain_when_to_use_modal(
        self, functional_analysis: FunctionalAnalysisResult
    ) -> str:
        """Explain when modal analysis is valuable."""
        has_strong_functional = len(functional_analysis.cadences) > 0
        has_modal_chords = any(
            chord.is_chromatic for chord in functional_analysis.chords
        )

        if has_strong_functional and not has_modal_chords:
            return (
                "Modal analysis is less applicable - this progression works "
                "primarily through functional harmony"
            )
        elif has_modal_chords:
            return (
                "Modal analysis helps explain the chromatic chords and their "
                "relationship to the underlying scale"
            )
        else:
            return (
                "Modal analysis provides alternative perspective focusing on "
                "scale relationships"
            )

    def _analyze_chromatic_elements(
        self, functional_analysis: FunctionalAnalysisResult
    ) -> Optional[ChromaticAnalysisResult]:
        """Analyze chromatic elements in detail."""
        if not functional_analysis.chromatic_elements:
            return None

        secondary_dominants: List[Dict[str, Any]] = []
        borrowed_chords: List[Dict[str, Any]] = []
        chromatic_mediants: List[Dict[str, Any]] = []
        resolution_patterns: List[Dict[str, Any]] = []

        for element in functional_analysis.chromatic_elements:
            if element.type.value == "secondary_dominant":
                secondary_dominants.append(
                    {
                        "chord": element.chord.chord_symbol,
                        "roman_numeral": element.chord.roman_numeral,
                        "target": (
                            element.resolution.roman_numeral
                            if element.resolution
                            else "unresolved"
                        ),
                        "explanation": element.explanation,
                    }
                )

                if element.resolution:
                    resolution_patterns.append(
                        {
                            "from": element.chord.roman_numeral,
                            "to": element.resolution.roman_numeral,
                            "type": "strong",
                            "explanation": (
                                f"Secondary dominant resolution: "
                                f"{element.chord.roman_numeral} → "
                                f"{element.resolution.roman_numeral}"
                            ),
                        }
                    )

            elif element.type.value == "borrowed_chord":
                borrowed_chords.append(
                    {
                        "chord": element.chord.chord_symbol,
                        "roman_numeral": element.chord.roman_numeral,
                        "borrowed_from": (
                            "parallel minor"
                            if functional_analysis.mode == "major"
                            else "parallel major"
                        ),
                        "explanation": element.explanation,
                    }
                )

        return ChromaticAnalysisResult(
            secondary_dominants=secondary_dominants,
            borrowed_chords=borrowed_chords,
            chromatic_mediants=chromatic_mediants,
            resolution_patterns=resolution_patterns,
        )

    def _determine_primary_approach(
        self,
        functional_analysis: FunctionalAnalysisResult,
        modal_enhancement: Optional[ModalEnhancementResult],
        chromatic_analysis: Optional[ChromaticAnalysisResult],
    ) -> Literal["functional", "modal", "chromatic"]:
        """Determine the primary analytical approach."""

        # If significant chromatic content, lead with chromatic analysis
        if chromatic_analysis and chromatic_analysis.secondary_dominants:
            return "chromatic"

        # If strong modal characteristics without functional cadences, lead with modal
        if (
            modal_enhancement
            and modal_enhancement.modal_characteristics
            and len(functional_analysis.cadences) == 0
        ):
            return "modal"

        # Default to functional approach (most common)
        return "functional"

    def _calculate_overall_confidence(
        self,
        functional_analysis: FunctionalAnalysisResult,
        modal_enhancement: Optional[ModalEnhancementResult],
    ) -> float:
        """Calculate overall analysis confidence."""
        confidence = functional_analysis.confidence

        # If modal and functional analyses agree, increase confidence
        if modal_enhancement and modal_enhancement.enhanced_analysis:
            modal_confidence = modal_enhancement.enhanced_analysis.confidence
            confidence = (confidence + modal_confidence) / 2

        return min(confidence, 1.0)

    def _create_comprehensive_explanation(
        self,
        functional_analysis: FunctionalAnalysisResult,
        modal_enhancement: Optional[ModalEnhancementResult],
        chromatic_analysis: Optional[ChromaticAnalysisResult],
        primary_approach: Literal["functional", "modal", "chromatic"],
    ) -> str:
        """Create comprehensive explanation combining all analyses."""

        if primary_approach == "functional":
            explanation = f"Primary analysis: {functional_analysis.explanation}"

            if modal_enhancement:
                explanation += (
                    f". Modal perspective: {modal_enhancement.comparison_to_functional}"
                )

            if chromatic_analysis and chromatic_analysis.secondary_dominants:
                explanation += (
                    f". Contains {len(chromatic_analysis.secondary_dominants)} "
                    "secondary dominant(s)"
                )

        elif primary_approach == "modal":
            characteristics = (
                ", ".join(modal_enhancement.modal_characteristics)
                if modal_enhancement
                else ""
            )
            explanation = f"Primary analysis: Modal progression with {characteristics}"
            explanation += f". Functional context: {functional_analysis.explanation}"

        elif primary_approach == "chromatic":
            sec_dom_count = (
                len(chromatic_analysis.secondary_dominants) if chromatic_analysis else 0
            )
            explanation = (
                f"Primary analysis: Chromatic harmony with {sec_dom_count} "
                "secondary dominant(s)"
            )
            explanation += f". Functional foundation: {functional_analysis.explanation}"

        return explanation

    def _create_pedagogical_explanation(
        self,
        primary_approach: Literal["functional", "modal", "chromatic"],
        functional_analysis: FunctionalAnalysisResult,
    ) -> str:
        """Create pedagogical explanation of analytical approach."""

        if primary_approach == "functional":
            return (
                "This progression is best understood through functional harmony - "
                "how chords relate through tonic, predominant, and dominant functions."
            )
        elif primary_approach == "modal":
            return (
                "This progression emphasizes modal characteristics that are "
                "better understood through scale relationships than traditional "
                "functional harmony."
            )
        elif primary_approach == "chromatic":
            return (
                "This progression uses chromatic harmony (non-diatonic chords) "
                "that requires understanding secondary dominants and borrowed chords."
            )

    def _parse_chord_progression(self, input_str: str) -> List[str]:
        """Parse chord progression string into individual chord symbols."""
        return parse_chord_progression(input_str)
