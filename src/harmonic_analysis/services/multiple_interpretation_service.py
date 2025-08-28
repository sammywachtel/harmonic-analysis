"""
Multiple Interpretation Analysis Service

Provides comprehensive harmonic analysis with multiple valid interpretations,
confidence scoring, and evidence-based reasoning. Transforms the binary
modal/functional approach into a nuanced system that reflects real music
theory practice.

Architecture:
- Orchestrates existing analyzers (functional, modal, chromatic)
- Applies confidence scoring based on harmonic evidence
- Returns multiple valid interpretations ranked by theoretical certainty
- Supports adaptive disclosure for different pedagogical levels
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, cast

from ..core.enhanced_modal_analyzer import EnhancedModalAnalyzer, ModalAnalysisResult
from ..core.functional_harmony import (
    FunctionalAnalysisResult,
    FunctionalHarmonyAnalyzer,
)
from ..types import (
    AnalysisOptions,
    AnalysisSuggestions,
    EvidenceType,
    InterpretationType,
    PedagogicalLevel,
)
from .algorithmic_suggestion_engine import AlgorithmicSuggestionEngine
from .bidirectional_suggestion_engine import BidirectionalSuggestionEngine

# Enums moved to types.py for shared usage


@dataclass
class AnalysisEvidence:
    """Evidence supporting an analytical interpretation"""

    type: EvidenceType
    strength: float  # 0.0 to 1.0
    description: str
    supported_interpretations: List[InterpretationType]
    musical_basis: str  # Theoretical explanation


@dataclass
class InterpretationAnalysis:
    """A single analytical interpretation with confidence"""

    type: InterpretationType
    confidence: float  # 0.0 to 1.0
    analysis: str
    roman_numerals: List[str] = field(default_factory=list)
    key_signature: Optional[str] = None
    mode: Optional[str] = None
    evidence: List[AnalysisEvidence] = field(default_factory=list)
    reasoning: str = ""
    theoretical_basis: str = ""

    # Modal analysis fields
    modal_characteristics: List[str] = field(default_factory=list)
    parent_key_relationship: Optional[str] = None

    # Chromatic analysis fields
    secondary_dominants: List[Dict[str, str]] = field(default_factory=list)
    borrowed_chords: List[Dict[str, str]] = field(default_factory=list)
    chromatic_mediants: List[Dict[str, str]] = field(default_factory=list)

    # Functional analysis fields
    cadences: List[Dict[str, str]] = field(default_factory=list)
    chord_functions: List[str] = field(default_factory=list)

    # Contextual classification
    contextual_classification: Optional[str] = None

    # Confidence breakdown for UI behavior
    functional_confidence: Optional[float] = None
    modal_confidence: Optional[float] = None
    chromatic_confidence: Optional[float] = None


@dataclass
class AlternativeAnalysis(InterpretationAnalysis):
    """Alternative analysis with relationship to primary"""

    relationship_to_primary: str = ""


@dataclass
class MultipleInterpretationMetadata:
    """Metadata about the interpretation analysis"""

    total_interpretations_considered: int
    confidence_threshold: float
    show_alternatives: bool
    pedagogical_level: PedagogicalLevel
    analysis_time_ms: float


@dataclass
class MultipleInterpretationResult:
    """Complete result of multiple interpretation analysis"""

    primary_analysis: InterpretationAnalysis
    alternative_analyses: List[AlternativeAnalysis]
    metadata: MultipleInterpretationMetadata
    input_chords: List[str]
    input_options: Optional[AnalysisOptions] = None
    suggestions: Optional[AnalysisSuggestions] = None


# Confidence framework based on music theory expert guidance
CONFIDENCE_LEVELS = {
    "definitive": {
        "min": 0.85,
        "max": 1.0,
        "description": "Unambiguous harmonic markers present",
    },
    "strong": {
        "min": 0.65,
        "max": 0.84,
        "description": "Clear evidence with minimal ambiguity",
    },
    "moderate": {
        "min": 0.45,
        "max": 0.64,
        "description": "Valid interpretation with competing possibilities",
    },
    "weak": {
        "min": 0.25,
        "max": 0.44,
        "description": "Theoretically possible but lacks context",
    },
    "insufficient": {
        "min": 0.0,
        "max": 0.24,
        "description": "Requires significant assumptions",
    },
}

# Evidence weighting based on theoretical importance
EVIDENCE_WEIGHTS = {
    EvidenceType.CADENTIAL: 0.4,  # bVII-I, V-I, bII-I patterns
    EvidenceType.STRUCTURAL: 0.25,  # First/last chord relationships
    EvidenceType.INTERVALLIC: 0.2,  # Distinctive scale degrees (bVII, bII, etc.)
    EvidenceType.HARMONIC: 0.15,  # Key signature, chord qualities
    EvidenceType.CONTEXTUAL: 0.15,  # Overall context
}


class AnalysisCache:
    """Simple cache for performance optimization"""

    def __init__(self, max_size: int = 100, ttl_minutes: int = 5):
        self.cache: Dict[str, MultipleInterpretationResult] = {}
        self.timestamps: Dict[str, datetime] = {}
        self.max_size = max_size
        self.ttl = timedelta(minutes=ttl_minutes)

    def get(self, key: str) -> Optional[MultipleInterpretationResult]:
        """Get cached result if still valid"""
        if key not in self.cache:
            return None

        # Check TTL
        if datetime.now() - self.timestamps[key] > self.ttl:
            del self.cache[key]
            del self.timestamps[key]
            return None

        return self.cache[key]

    def set(self, key: str, result: MultipleInterpretationResult) -> None:
        """Cache result with LRU eviction"""
        # Implement LRU by clearing oldest entries
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]

        self.cache[key] = result
        self.timestamps[key] = datetime.now()

    def get_cache_key(
        self, chords: List[str], options: Optional[AnalysisOptions] = None
    ) -> str:
        """Generate cache key from input"""
        options_str = json.dumps(options.__dict__ if options else {}, sort_keys=True)
        return f"{'_'.join(chords)}_{hash(options_str)}"


class MultipleInterpretationService:
    """Service for multiple interpretation analysis"""

    def __init__(self) -> None:
        self.cache = AnalysisCache()
        self.functional_analyzer = FunctionalHarmonyAnalyzer()
        self.modal_analyzer = EnhancedModalAnalyzer()
        self.suggestion_engine = AlgorithmicSuggestionEngine()
        self.bidirectional_engine = BidirectionalSuggestionEngine()

    async def analyze_progression(
        self, chords: List[str], options: Optional[AnalysisOptions] = None
    ) -> MultipleInterpretationResult:
        """
        Main entry point for multiple interpretation analysis

        Args:
            chords: List of chord symbols
            options: Analysis options

        Returns:
            Complete multiple interpretation analysis result
        """
        if not chords:
            raise ValueError("Empty chord progression provided")

        start_time = time.time()

        if options is None:
            options = AnalysisOptions()

        cache_key = self.cache.get_cache_key(chords, options)

        # Check cache first
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            # Set defaults
            pedagogical_level = (
                PedagogicalLevel(options.pedagogical_level)
                if options.pedagogical_level
                else PedagogicalLevel.INTERMEDIATE
            )
            confidence_threshold = (
                options.confidence_threshold
                if options.confidence_threshold is not None
                else 0.5
            )
            max_alternatives = (
                options.max_alternatives if options.max_alternatives is not None else 3
            )

            # Run parallel analysis
            functional_result, modal_result = await asyncio.gather(
                self._run_functional_analysis(chords, options),
                self._run_modal_analysis(chords, options),
                return_exceptions=True,
            )

            # Handle exceptions
            if isinstance(functional_result, Exception):
                functional_result = None
            if isinstance(modal_result, Exception):
                modal_result = None

            # Narrow types for MyPy
            functional_result = cast(
                Optional[FunctionalAnalysisResult], functional_result
            )
            modal_result = cast(Optional[ModalAnalysisResult], modal_result)

            # Calculate interpretations with confidence scoring
            interpretations = await self._calculate_interpretations(
                chords, functional_result, modal_result, options
            )

            # Rank and filter interpretations
            ranked_interpretations = self._rank_interpretations(interpretations)
            filtered_alternatives = self._filter_alternatives(
                ranked_interpretations, confidence_threshold, max_alternatives
            )

            # Generate suggestions for improving analysis
            suggestions = await self._generate_analysis_suggestions(
                chords, ranked_interpretations, functional_result, options
            )

            # Create result
            analysis_time_ms = (time.time() - start_time) * 1000

            result = MultipleInterpretationResult(
                primary_analysis=(
                    ranked_interpretations[0]
                    if ranked_interpretations
                    else self._create_fallback_interpretation(chords)
                ),
                alternative_analyses=filtered_alternatives,
                metadata=MultipleInterpretationMetadata(
                    total_interpretations_considered=len(interpretations),
                    confidence_threshold=confidence_threshold,
                    show_alternatives=self._should_show_alternatives(
                        ranked_interpretations,
                        pedagogical_level,
                        options.force_multiple_interpretations or False,
                    ),
                    pedagogical_level=pedagogical_level,
                    analysis_time_ms=analysis_time_ms,
                ),
                input_chords=chords,
                input_options=options,
                suggestions=suggestions,
            )

            # Cache result
            self.cache.set(cache_key, result)

            return result

        except Exception as error:
            raise Exception(f"Multiple interpretation analysis failed: {str(error)}")

    async def _run_functional_analysis(
        self, chords: List[str], options: AnalysisOptions
    ) -> Optional[FunctionalAnalysisResult]:
        """Run functional harmony analysis"""
        try:
            return await self.functional_analyzer.analyze_functionally(
                chords, options.parent_key
            )
        except Exception as e:
            print(f"Warning: Functional analysis failed: {e}")
            return None

    async def _run_modal_analysis(
        self, chords: List[str], options: AnalysisOptions
    ) -> Optional[ModalAnalysisResult]:
        """Run modal analysis"""
        try:
            return self.modal_analyzer.analyze_modal_characteristics(
                chords, options.parent_key
            )
        except Exception as e:
            print(f"Warning: Modal analysis failed: {e}")
            return None

    async def _calculate_interpretations(
        self,
        chords: List[str],
        functional_result: Optional[FunctionalAnalysisResult],
        modal_result: Optional[ModalAnalysisResult],
        options: AnalysisOptions,
    ) -> List[InterpretationAnalysis]:
        """Calculate all possible interpretations with confidence scores"""
        interpretations: List[InterpretationAnalysis] = []

        # Functional interpretation
        if functional_result:
            functional_interp = self._create_functional_interpretation(
                chords, functional_result, options
            )
            if functional_interp:
                interpretations.append(functional_interp)

        # Modal interpretation
        if modal_result:
            modal_interp = self._create_modal_interpretation(
                chords, modal_result, options
            )
            if modal_interp:
                interpretations.append(modal_interp)

        return interpretations

    def _create_functional_interpretation(
        self,
        chords: List[str],
        functional_result: FunctionalAnalysisResult,
        options: AnalysisOptions,
    ) -> Optional[InterpretationAnalysis]:
        """Create functional interpretation with confidence scoring"""
        try:
            evidence = self._collect_functional_evidence(
                chords, functional_result, options
            )
            confidence = self._calculate_confidence(evidence)

            # Extract cadences and chord functions from functional analysis
            cadences = self._extract_cadences(functional_result)
            chord_functions = self._extract_chord_functions(functional_result)

            # Detect chromatic elements
            chromatic_elements = self._detect_chromatic_elements(
                chords, options.parent_key
            )

            return InterpretationAnalysis(
                type=InterpretationType.FUNCTIONAL,
                confidence=confidence,
                analysis=functional_result.explanation or "Functional progression",
                roman_numerals=[
                    chord.roman_numeral for chord in functional_result.chords
                ],
                key_signature=functional_result.key_center or options.parent_key,
                evidence=evidence,
                reasoning=self._generate_functional_reasoning(
                    functional_result, evidence
                ),
                theoretical_basis=(
                    "Functional tonal harmony analysis based on Roman numeral "
                    "progressions"
                ),
                # New functional fields
                cadences=cadences,
                chord_functions=chord_functions,
                functional_confidence=confidence,
                contextual_classification=self._determine_contextual_classification(
                    chords, options.parent_key
                ),
                # Chromatic elements
                secondary_dominants=chromatic_elements["secondary_dominants"],
                borrowed_chords=chromatic_elements["borrowed_chords"],
                chromatic_mediants=chromatic_elements["chromatic_mediants"],
            )
        except Exception as e:
            print(f"Warning: Failed to create functional interpretation: {e}")
            return None

    def _create_modal_interpretation(
        self,
        chords: List[str],
        modal_result: ModalAnalysisResult,
        options: AnalysisOptions,
    ) -> Optional[InterpretationAnalysis]:
        """Create modal interpretation with confidence scoring"""
        try:
            evidence = self._collect_modal_evidence(chords, modal_result)
            confidence = self._calculate_confidence(evidence)

            # Extract modal characteristics and parent key relationship
            modal_characteristics = self._extract_modal_characteristics(modal_result)
            parent_key_relationship = self._determine_parent_key_relationship(
                modal_result, options.parent_key
            )

            # Detect chromatic elements
            chromatic_elements = self._detect_chromatic_elements(
                chords, options.parent_key
            )

            return InterpretationAnalysis(
                type=InterpretationType.MODAL,
                confidence=confidence,
                analysis=f"{modal_result.mode_name} modal progression",
                mode=modal_result.mode_name,
                key_signature=modal_result.parent_key_signature,
                evidence=evidence,
                reasoning=self._generate_modal_reasoning(modal_result, evidence),
                theoretical_basis=(
                    "Modal analysis based on characteristic scale degrees and "
                    "harmonic patterns"
                ),
                # New modal fields
                modal_characteristics=modal_characteristics,
                parent_key_relationship=parent_key_relationship,
                modal_confidence=confidence,
                contextual_classification=self._determine_contextual_classification(
                    chords, options.parent_key
                ),
                # Chromatic elements
                secondary_dominants=chromatic_elements["secondary_dominants"],
                borrowed_chords=chromatic_elements["borrowed_chords"],
                chromatic_mediants=chromatic_elements["chromatic_mediants"],
            )
        except Exception as e:
            print(f"Warning: Failed to create modal interpretation: {e}")
            return None

    def _collect_functional_evidence(
        self,
        chords: List[str],
        functional_result: FunctionalAnalysisResult,
        options: Optional[AnalysisOptions] = None,
    ) -> List[AnalysisEvidence]:
        """Collect evidence for functional analysis"""
        evidence: List[AnalysisEvidence] = []

        # Cadential evidence with cadence-specific strength calibration
        if functional_result.cadences:
            cadence = functional_result.cadences[0]
            cadence_name = getattr(
                cadence, "name", getattr(cadence, "type", "authentic")
            )

            # Cadence-specific strength values based on music theory analysis
            cadence_strengths = {
                "authentic": 0.90,  # V-I - strongest resolution
                "plagal": 0.65,  # IV-I - gentle, conclusive but weak
                "deceptive": 0.70,  # V-vi - surprising but clear
                "half": 0.50,  # ends on V - inconclusive
                "phrygian": 0.80,  # bII-I - strong modal cadence
                "modal": 0.75,  # bVII-I and other modal cadences
            }

            # Normalize cadence name and get appropriate strength
            cadence_key = cadence_name.lower().replace("_", "")
            cadence_strength = cadence_strengths.get(
                cadence_key, 0.60
            )  # default for unknown

            evidence.append(
                AnalysisEvidence(
                    type=EvidenceType.CADENTIAL,
                    strength=cadence_strength,
                    description=(
                        f"{cadence_name.title()} cadential progression identified"
                    ),
                    supported_interpretations=[InterpretationType.FUNCTIONAL],
                    musical_basis=(
                        f"{cadence_name} cadence provides "
                        f"{self._get_cadence_quality(cadence_key)} tonal resolution"
                    ),
                )
            )

        # Structural framing (reduced strength for realistic confidence)
        if len(chords) >= 3 and chords[0] == chords[-1]:
            evidence.append(
                AnalysisEvidence(
                    type=EvidenceType.STRUCTURAL,
                    strength=0.6,
                    description="Tonic framing present",
                    supported_interpretations=[
                        InterpretationType.FUNCTIONAL,
                        InterpretationType.MODAL,
                    ],
                    musical_basis="First and last chords establish tonic center",
                )
            )

        # Roman numeral clarity - cap and scale down excessive confidence
        if functional_result.confidence >= 0.5:
            # Scale down overly confident functional scores to be more realistic
            # For plagal cadences and weak progressions, use even lower strength
            harmonic_strength = min(0.60, functional_result.confidence * 0.65)
            evidence.append(
                AnalysisEvidence(
                    type=EvidenceType.HARMONIC,
                    strength=harmonic_strength,
                    description="Clear functional harmonic progression",
                    supported_interpretations=[InterpretationType.FUNCTIONAL],
                    musical_basis=(
                        "Roman numeral analysis shows clear tonal relationships"
                    ),
                )
            )

        # Roman numeral progression strength with pattern recognition
        if len(functional_result.chords) >= 3:
            roman_numerals = [chord.roman_numeral for chord in functional_result.chords]

            # Detect strong functional patterns that deserve high confidence
            strong_patterns = self._detect_strong_functional_patterns(roman_numerals)

            if strong_patterns:
                # High confidence for classic progressions like I-vi-IV-V, ii-V-I, etc.
                # Use STRUCTURAL type for higher weight (0.25 vs 0.15)
                # and boost strength
                evidence.append(
                    AnalysisEvidence(
                        type=EvidenceType.STRUCTURAL,
                        strength=0.95,
                        description=f"Classic functional pattern: {strong_patterns[0]}",
                        supported_interpretations=[InterpretationType.FUNCTIONAL],
                        musical_basis=(
                            f"{strong_patterns[0]} progression demonstrates strong "
                            "tonal logic"
                        ),
                    )
                )
            elif any(rn in ["I", "i"] for rn in roman_numerals):
                # Standard confidence for tonic-based progressions
                evidence.append(
                    AnalysisEvidence(
                        type=EvidenceType.HARMONIC,
                        strength=0.55,
                        description="Tonic-based harmonic progression",
                        supported_interpretations=[InterpretationType.FUNCTIONAL],
                        musical_basis=(
                            "Roman numeral progression shows tonic-centered "
                            "relationships"
                        ),
                    )
                )

        # FIXED: Add evidence for chromatic elements in functional analysis
        # This was missing and is crucial for secondary dominant detection
        if options and options.parent_key:
            chromatic_elements = self._detect_chromatic_elements(
                chords, options.parent_key
            )

            # Secondary dominants boost functional analysis confidence significantly
            if chromatic_elements["secondary_dominants"]:
                num_secondary = len(chromatic_elements["secondary_dominants"])
                evidence.append(
                    AnalysisEvidence(
                        type=EvidenceType.HARMONIC,
                        strength=0.85,  # High strength for secondary dominants
                        description=f"Contains {num_secondary} secondary dominant(s)",
                        supported_interpretations=[InterpretationType.FUNCTIONAL],
                        musical_basis=(
                            "Secondary dominants indicate sophisticated harmony"
                        ),
                    )
                )

            # Borrowed chords also support functional interpretation
            if chromatic_elements["borrowed_chords"]:
                num_borrowed = len(chromatic_elements["borrowed_chords"])
                evidence.append(
                    AnalysisEvidence(
                        type=EvidenceType.HARMONIC,
                        strength=0.75,
                        description=f"Contains {num_borrowed} borrowed chord(s)",
                        supported_interpretations=[InterpretationType.FUNCTIONAL],
                        musical_basis="Borrowed chords indicate functional awareness",
                    )
                )

        return evidence

    def _collect_modal_evidence(
        self, chords: List[str], modal_result: ModalAnalysisResult
    ) -> List[AnalysisEvidence]:
        """Collect evidence for modal analysis"""
        evidence: List[AnalysisEvidence] = []

        # Modal characteristics - preserve original evidence types and descriptions
        for modal_evidence in modal_result.evidence:
            # Use the original evidence type instead of forcing INTERVALLIC
            evidence_type = getattr(modal_evidence, "type", EvidenceType.INTERVALLIC)

            # Use the original description instead of stringifying
            description = getattr(modal_evidence, "description", str(modal_evidence))

            # FIXED: Use more conservative modal evidence scoring
            # Modal evidence should not default to such high values
            original_strength = getattr(modal_evidence, "strength", 0.70)
            # Cap modal evidence at reasonable levels to balance with functional
            strength = min(original_strength, 0.75)

            evidence.append(
                AnalysisEvidence(
                    type=evidence_type,
                    strength=strength,
                    description=description,
                    supported_interpretations=[InterpretationType.MODAL],
                    musical_basis=(
                        f"{description} is characteristic of "
                        f"{modal_result.mode_name} mode"
                    ),
                )
            )

        # FIXED: Reduce overall modal confidence contribution
        # Don't double-count the analyzer confidence at full strength
        contextual_strength = min(modal_result.confidence * 0.8, 0.75)
        evidence.append(
            AnalysisEvidence(
                type=EvidenceType.CONTEXTUAL,
                strength=contextual_strength,
                description="Overall modal characteristics present",
                supported_interpretations=[InterpretationType.MODAL],
                musical_basis="Combined modal features suggest modal interpretation",
            )
        )

        return evidence

    def _calculate_confidence(self, evidence: List[AnalysisEvidence]) -> float:
        """Calculate overall confidence based on evidence"""
        if not evidence:
            return 0.2

        # Weighted average based on evidence types
        total_weight = 0.0
        weighted_sum = 0.0

        for ev in evidence:
            weight = EVIDENCE_WEIGHTS.get(ev.type, 0.1)
            total_weight += weight
            weighted_sum += ev.strength * weight

        base_confidence = weighted_sum / total_weight if total_weight > 0 else 0.2

        # Bonus for multiple evidence types
        evidence_types = {ev.type for ev in evidence}
        diversity_bonus = 0.1 if len(evidence_types) > 1 else 0

        return min(1.0, base_confidence + diversity_bonus)

    def _generate_functional_reasoning(
        self,
        functional_result: FunctionalAnalysisResult,
        evidence: List[AnalysisEvidence],
    ) -> str:
        """Generate reasoning for functional interpretation"""
        reasons = []

        if functional_result.cadences:
            cadence = functional_result.cadences[0]
            cadence_name = getattr(
                cadence, "name", getattr(cadence, "type", "authentic")
            )
            reasons.append(
                f"Strong {cadence_name} cadence establishes functional tonality"
            )

        if functional_result.chords:
            reasons.append(
                "Clear Roman numeral progression supports functional analysis"
            )

        if any(
            e.type == EvidenceType.STRUCTURAL and e.strength > 0.6 for e in evidence
        ):
            reasons.append("Tonic framing reinforces key center")

        return (
            "; ".join(reasons)
            if reasons
            else "Functional harmonic progression with clear tonal relationships"
        )

    def _generate_modal_reasoning(
        self, modal_result: ModalAnalysisResult, evidence: List[AnalysisEvidence]
    ) -> str:
        """Generate reasoning for modal interpretation"""
        reasons = []

        if modal_result.evidence:
            first_evidence = modal_result.evidence[0]
            chord_info = getattr(
                first_evidence,
                "chord",
                getattr(first_evidence, "pattern", str(first_evidence)),
            )
            reasons.append(
                f"{chord_info} is characteristic of {modal_result.mode_name} mode"
            )

        if any(e.type == EvidenceType.INTERVALLIC for e in evidence):
            reasons.append("Distinctive modal scale degrees present")

        return (
            "; ".join(reasons)
            if reasons
            else (
                f"Modal characteristics suggest {modal_result.mode_name} "
                "interpretation"
            )
        )

    def _rank_interpretations(
        self, interpretations: List[InterpretationAnalysis]
    ) -> List[InterpretationAnalysis]:
        """Rank interpretations by confidence"""
        return sorted(
            [interp for interp in interpretations if interp.confidence > 0.2],
            key=lambda x: x.confidence,
            reverse=True,
        )

    def _filter_alternatives(
        self,
        ranked_interpretations: List[InterpretationAnalysis],
        confidence_threshold: float,
        max_alternatives: int,
    ) -> List[AlternativeAnalysis]:
        """Filter alternatives based on confidence and limits"""
        if len(ranked_interpretations) <= 1:
            return []

        primary = ranked_interpretations[0]
        alternatives = ranked_interpretations[1 : max_alternatives + 1]

        filtered_alternatives = []
        for alt in alternatives:
            if alt.confidence >= confidence_threshold:
                alt_analysis = AlternativeAnalysis(
                    type=alt.type,
                    confidence=alt.confidence,
                    analysis=alt.analysis,
                    roman_numerals=alt.roman_numerals,
                    key_signature=alt.key_signature,
                    mode=alt.mode,
                    evidence=alt.evidence,
                    reasoning=alt.reasoning,
                    theoretical_basis=alt.theoretical_basis,
                    relationship_to_primary=self._generate_relationship_description(
                        primary, alt
                    ),
                )
                filtered_alternatives.append(alt_analysis)

        return filtered_alternatives

    def _generate_relationship_description(
        self, primary: InterpretationAnalysis, alternative: InterpretationAnalysis
    ) -> str:
        """Generate description of relationship between interpretations"""
        if (
            primary.type == InterpretationType.FUNCTIONAL
            and alternative.type == InterpretationType.MODAL
        ):
            return (
                "Modal interpretation emphasizes scale degrees over functional "
                "harmonic relationships"
            )
        elif (
            primary.type == InterpretationType.MODAL
            and alternative.type == InterpretationType.FUNCTIONAL
        ):
            return (
                "Functional interpretation emphasizes tonal chord progressions "
                "over modal characteristics"
            )
        else:
            return "Alternative analytical perspective on the same harmonic content"

    def _should_show_alternatives(
        self,
        interpretations: List[InterpretationAnalysis],
        pedagogical_level: PedagogicalLevel,
        force_multiple: bool,
    ) -> bool:
        """Determine whether to show alternatives"""
        if force_multiple:
            return True
        if len(interpretations) <= 1:
            return False

        primary = interpretations[0]
        best_alternative = interpretations[1] if len(interpretations) > 1 else None

        # Always show for advanced users
        if pedagogical_level == PedagogicalLevel.ADVANCED:
            return True

        # For beginners, only show if primary isn't highly confident
        if pedagogical_level == PedagogicalLevel.BEGINNER:
            return primary.confidence < 0.8

        # For intermediate, show if alternative is reasonably strong
        if best_alternative:
            return (primary.confidence - best_alternative.confidence) < 0.3

        return False

    def _create_fallback_interpretation(
        self, chords: List[str]
    ) -> InterpretationAnalysis:
        """Create fallback interpretation when analysis fails"""
        return InterpretationAnalysis(
            type=InterpretationType.FUNCTIONAL,
            confidence=0.3,
            analysis=f"Basic chord progression: {' - '.join(chords)}",
            reasoning="Analysis completed with limited harmonic information",
            theoretical_basis="Basic chord progression analysis",
        )

    def _get_cadence_quality(self, cadence_key: str) -> str:
        """Get descriptive quality for different cadence types"""
        cadence_qualities = {
            "authentic": "strong",
            "plagal": "gentle",
            "deceptive": "surprising",
            "half": "inconclusive",
            "phrygian": "modal",
            "modal": "characteristic",
        }
        return cadence_qualities.get(cadence_key, "moderate")

    def _detect_strong_functional_patterns(
        self, roman_numerals: List[str]
    ) -> List[str]:
        """Detect classic functional patterns that deserve high confidence"""
        patterns = []
        rn_str = "-".join(roman_numerals)

        # Classic strong progressions (high theoretical strength)
        strong_patterns = {
            # Circle of fifths progressions
            "I-vi-IV-V": ["I-vi-IV-V", "i-VI-iv-V"],
            "vi-IV-I-V": ["vi-IV-I-V", "VI-iv-i-v"],
            "IV-I-V-vi": ["IV-I-V-vi", "iv-i-v-VI"],
            # Jazz standards
            "ii-V-I": ["ii-V-I", "IIo-V-I", "ii7-V7-I"],
            "I-vi-ii-V": ["I-vi-ii-V", "i-VI-iio-V"],
            # Common pop/rock patterns
            "I-V-vi-IV": ["I-V-vi-IV", "I-V-VI-IV"],
            "vi-IV-I-V-pop": ["vi-IV-I-V", "VI-IV-I-V"],
            # Authentic cadences
            "V-I": ["V-I", "V7-I", "v-i"],
            "ii-V-I-cadence": ["ii-V-I", "iio-V-I"],
            # Plagal variants (still functional but weaker - handled elsewhere)
        }

        # Check for exact matches and partial matches
        for pattern_name, variations in strong_patterns.items():
            for variation in variations:
                if rn_str == variation or rn_str.endswith(variation):
                    patterns.append(pattern_name)
                    break

        # Check for sequential patterns (like I-ii-iii-IV)
        if self._is_sequential_progression(roman_numerals):
            patterns.append("Sequential progression")

        return patterns

    def _is_sequential_progression(self, roman_numerals: List[str]) -> bool:
        """Check if progression follows sequential harmonic logic"""
        # Examples: I-ii-iii-IV, vi-vii-I-ii, etc.
        if len(roman_numerals) < 3:
            return False

        # Convert roman numerals to scale degrees for sequence detection
        degree_map = {
            "I": 1,
            "ii": 2,
            "iii": 3,
            "IV": 4,
            "V": 5,
            "vi": 6,
            "vii": 7,
            "i": 1,
            "II": 2,
            "III": 3,
            "iv": 4,
            "v": 5,
            "VI": 6,
            "VII": 7,
        }

        try:
            degrees = [degree_map.get(rn.rstrip("7o"), 0) for rn in roman_numerals]

            # Check for ascending or descending sequences
            if all(
                degrees[i] + 1 == degrees[i + 1] or degrees[i] - 6 == degrees[i + 1]
                for i in range(len(degrees) - 1)
            ):
                return True  # Ascending sequence
            if all(
                degrees[i] - 1 == degrees[i + 1] or degrees[i] + 6 == degrees[i + 1]
                for i in range(len(degrees) - 1)
            ):
                return True  # Descending sequence

        except (KeyError, IndexError):
            pass

        return False

    # Helper methods for new test framework fields

    def _extract_cadences(
        self, functional_result: FunctionalAnalysisResult
    ) -> List[Dict[str, str]]:
        """Extract cadence information from functional analysis"""
        cadences = []

        # Look for cadences in the progression
        if hasattr(functional_result, "cadences") and functional_result.cadences:
            for cadence in functional_result.cadences:
                # Handle cadence as dict or object
                if hasattr(cadence, "__dict__"):
                    cadence_chords = getattr(cadence, "chords", "")
                    # Convert chord objects to string representation
                    if isinstance(cadence_chords, list):
                        chord_names = []
                        for chord in cadence_chords:
                            if hasattr(chord, "roman_numeral"):
                                chord_names.append(chord.roman_numeral)
                            elif hasattr(chord, "chord_symbol"):
                                chord_names.append(chord.chord_symbol)
                            else:
                                chord_names.append(str(chord))
                        cadence_chords = "-".join(chord_names)

                    cadences.append(
                        {
                            "type": getattr(cadence, "type", "unknown"),
                            "chords": cadence_chords,
                            "strength": str(getattr(cadence, "strength", 0.5)),
                        }
                    )
                elif isinstance(cadence, dict):
                    cadences.append(
                        {
                            "type": cadence.get("type", "unknown"),
                            "chords": cadence.get("chords", ""),
                            "strength": str(cadence.get("strength", 0.5)),
                        }
                    )
        else:
            # Detect common cadences from roman numerals
            romans = [chord.roman_numeral for chord in functional_result.chords]
            if len(romans) >= 2:
                last_two = romans[-2:]
                if last_two == ["V", "I"] or last_two == ["V7", "I"]:
                    cadences.append(
                        {"type": "authentic", "chords": "V-I", "strength": "0.9"}
                    )
                elif last_two == ["IV", "I"]:
                    cadences.append(
                        {"type": "plagal", "chords": "IV-I", "strength": "0.7"}
                    )
                elif last_two == ["V", "vi"]:
                    cadences.append(
                        {"type": "deceptive", "chords": "V-vi", "strength": "0.8"}
                    )

        return cadences

    def _extract_chord_functions(
        self, functional_result: FunctionalAnalysisResult
    ) -> List[str]:
        """Extract chord function names from functional analysis"""
        functions = []

        for chord in functional_result.chords:
            roman = chord.roman_numeral

            # Map roman numerals to functions
            if roman in ["I", "i", "vi", "VI"]:
                functions.append("tonic")
            elif roman in ["ii", "IV", "iv", "ii7"]:
                functions.append("predominant")
            elif roman in ["V", "V7", "vii", "viio", "viio7"]:
                functions.append("dominant")
            else:
                functions.append("other")

        return functions

    def _extract_modal_characteristics(
        self, modal_result: ModalAnalysisResult
    ) -> List[str]:
        """Extract modal characteristics from modal analysis"""
        characteristics = []

        mode_name = modal_result.mode_name

        # Add characteristics based on mode
        if "Mixolydian" in mode_name:
            characteristics.append("bVII chord (modal characteristic)")
            characteristics.append("Lowered 7th scale degree")
        elif "Dorian" in mode_name:
            characteristics.append("Natural 6th in minor context")
            characteristics.append("Modal brightness")
        elif "Phrygian" in mode_name:
            characteristics.append("bII chord")
            characteristics.append("Lowered 2nd scale degree")
        elif "Lydian" in mode_name:
            characteristics.append("#IV chord")
            characteristics.append("Raised 4th scale degree")
        elif "Aeolian" in mode_name:
            characteristics.append("Natural minor scale")
        elif "Ionian" in mode_name:
            characteristics.append("Major scale characteristics")
        elif "Locrian" in mode_name:
            characteristics.append("Diminished tonic")
            characteristics.append("bII and b5")

        return characteristics

    def _determine_parent_key_relationship(
        self, modal_result: ModalAnalysisResult, given_key: Optional[str]
    ) -> str:
        """Determine relationship between modal analysis and given key"""
        if not given_key:
            return "no_context"

        modal_parent = modal_result.parent_key_signature

        # Normalize key strings for comparison
        given_normalized = given_key.replace(" major", "").replace(" minor", "")
        modal_normalized = (
            modal_parent.replace(" major", "").replace(" minor", "")
            if modal_parent
            else ""
        )

        if modal_normalized == given_normalized:
            return "matches"
        else:
            return "conflicts"

    def _determine_contextual_classification(
        self, chords: List[str], parent_key: Optional[str]
    ) -> str:
        """
        Determine contextual classification.

        (diatonic vs modal borrowing vs modal candidate)
        """
        if not parent_key:
            return "modal_candidate"

        # Use scale/melody analysis to determine classification
        from ..scale_melody_analysis import analyze_scale_melody

        # Extract unique notes from chords (simplified)
        notes = []
        for chord in chords:
            # Extract root note (simplified chord parsing)
            root = chord[0]
            if len(chord) > 1 and chord[1] in "b#":
                root = chord[:2]
            notes.append(root)

        if notes:
            result = analyze_scale_melody(notes, parent_key, melody=False)
            return result.classification

        return "modal_candidate"

    def _detect_chromatic_elements(
        self, chords: List[str], key: Optional[str] = None
    ) -> Dict[str, List[Dict[str, str]]]:
        """Detect chromatic elements like secondary dominants, borrowed chords, etc."""
        elements: Dict[str, List[Dict[str, str]]] = {
            "secondary_dominants": [],
            "borrowed_chords": [],
            "chromatic_mediants": [],
        }

        if not key:
            return elements

        # Simple secondary dominant detection
        for i, chord in enumerate(chords):
            # Look for dominant 7th chords that aren't V7 of the key
            if "7" in chord and i < len(chords) - 1:
                next_chord = chords[i + 1]

                # A7 -> Dm in key of C = V7/ii
                if chord == "A7" and next_chord == "Dm" and "C" in key:
                    elements["secondary_dominants"].append(
                        {"chord": chord, "target": next_chord, "roman_numeral": "V7/ii"}
                    )
                elif chord == "E7" and next_chord == "Am" and "C" in key:
                    elements["secondary_dominants"].append(
                        {"chord": chord, "target": next_chord, "roman_numeral": "V7/vi"}
                    )
                elif chord == "D7" and next_chord == "G" and "C" in key:
                    elements["secondary_dominants"].append(
                        {"chord": chord, "target": next_chord, "roman_numeral": "V7/V"}
                    )

        return elements

    async def _generate_analysis_suggestions(
        self,
        chords: List[str],
        interpretations: List[InterpretationAnalysis],
        functional_result: Optional[FunctionalAnalysisResult],
        options: AnalysisOptions,
    ) -> Optional[AnalysisSuggestions]:
        """Generate bidirectional suggestions for improving analysis quality."""

        try:
            # Extract current analysis metrics for bidirectional engine
            current_confidence = (
                interpretations[0].confidence if interpretations else 0.0
            )
            current_roman_numerals = (
                interpretations[0].roman_numerals if interpretations else []
            )

            # Use bidirectional suggestion engine for comprehensive suggestions
            bidirectional_suggestions = (
                await self.bidirectional_engine.generate_bidirectional_suggestions(
                    chords,
                    options,
                    current_confidence,
                    current_roman_numerals,
                )
            )

            if bidirectional_suggestions:
                # bidirectional_suggestions is already an AnalysisSuggestions object
                return bidirectional_suggestions

        except Exception as e:
            # If bidirectional engine fails, fall back to algorithmic engine
            print(f"Bidirectional suggestion engine error: {e}")

            # Fallback: Use old algorithmic engine for basic suggestions
            if not options.parent_key:
                try:
                    current_confidence = (
                        interpretations[0].confidence if interpretations else 0.0
                    )
                    current_roman_numerals = (
                        interpretations[0].roman_numerals if interpretations else []
                    )

                    key_suggestions = await self.suggestion_engine.generate_suggestions(
                        chords, current_confidence, current_roman_numerals
                    )

                    if key_suggestions:
                        return AnalysisSuggestions(
                            parent_key_suggestions=key_suggestions,
                            general_suggestions=[],
                        )

                except Exception as fallback_error:
                    print(f"Fallback suggestion engine error: {fallback_error}")

        return None


# Export singleton instance
multiple_interpretation_service = MultipleInterpretationService()


async def analyze_progression_multiple(
    chords: List[str], options: Optional[AnalysisOptions] = None
) -> MultipleInterpretationResult:
    """
    Convenience function for multiple interpretation analysis

    Args:
        chords: List of chord symbols
        options: Analysis options

    Returns:
        Complete multiple interpretation result
    """
    return await multiple_interpretation_service.analyze_progression(chords, options)
