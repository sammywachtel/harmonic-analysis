"""
Chromatic Harmony Analysis

Processes chromatic elements detected by functional harmony analysis,
organizing them into secondary dominants, borrowed chords, and chromatic mediants.

The main chromatic detection logic resides in the FunctionalHarmonyAnalyzer.
This module processes and categorizes the detected chromatic elements.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from .functional_harmony import FunctionalAnalysisResult


class ResolutionType(Enum):
    """Types of chromatic resolutions"""

    STRONG = "strong"
    WEAK = "weak"
    DECEPTIVE = "deceptive"


@dataclass
class SecondaryDominant:
    """Secondary dominant chord analysis"""

    chord: str
    roman_numeral: str
    target: str
    explanation: str


@dataclass
class BorrowedChord:
    """Borrowed chord analysis"""

    chord: str
    roman_numeral: str
    borrowed_from: str
    explanation: str


@dataclass
class ChromaticMediant:
    """Chromatic mediant relationship"""

    chord: str
    relationship: str
    explanation: str


@dataclass
class ResolutionPattern:
    """Pattern of harmonic resolution"""

    from_chord: str
    to_chord: str
    type: ResolutionType
    explanation: str


@dataclass
class ChromaticAnalysisResult:
    """Result of chromatic harmony analysis"""

    secondary_dominants: List[SecondaryDominant]
    borrowed_chords: List[BorrowedChord]
    chromatic_mediants: List[ChromaticMediant]
    resolution_patterns: List[ResolutionPattern]


class ChromaticAnalyzer:
    """
    Chromatic Harmony Analyzer

    Processes chromatic elements from functional harmony analysis and
    organizes them into secondary dominants, borrowed chords, and
    chromatic mediants with resolution patterns.
    """

    def analyze_chromatic_elements(
        self, functional_analysis: FunctionalAnalysisResult
    ) -> Optional[ChromaticAnalysisResult]:
        """
        Analyze chromatic elements from functional harmony analysis

        Args:
            functional_analysis: Results from functional harmony analysis

        Returns:
            ChromaticAnalysisResult if chromatic elements found, None otherwise
        """
        chromatic_elements = functional_analysis.chromatic_elements or []

        if not chromatic_elements:
            return None

        secondary_dominants = []
        borrowed_chords = []
        chromatic_mediants = []
        resolution_patterns = []

        # Process each chromatic element
        for element in chromatic_elements:
            if element.type.value == "secondary_dominant":
                secondary_dominants.append(
                    SecondaryDominant(
                        chord=element.chord.chord_symbol,
                        roman_numeral=element.chord.roman_numeral,
                        target=(
                            element.resolution.roman_numeral
                            if element.resolution
                            else "unresolved"
                        ),
                        explanation=element.explanation,
                    )
                )

                # Add resolution pattern if resolved
                if element.resolution:
                    resolution_patterns.append(
                        ResolutionPattern(
                            from_chord=element.chord.roman_numeral,
                            to_chord=element.resolution.roman_numeral,
                            type=ResolutionType.STRONG,
                            explanation=(
                                f"Secondary dominant resolution: "
                                f"{element.chord.roman_numeral} → "
                                f"{element.resolution.roman_numeral}"
                            ),
                        )
                    )

            elif element.type.value == "borrowed_chord":
                borrowed_from = (
                    "parallel minor"
                    if functional_analysis.mode == "major"
                    else "parallel major"
                )
                borrowed_chords.append(
                    BorrowedChord(
                        chord=element.chord.chord_symbol,
                        roman_numeral=element.chord.roman_numeral,
                        borrowed_from=borrowed_from,
                        explanation=element.explanation,
                    )
                )

            elif element.type.value == "chromatic_mediant":
                chromatic_mediants.append(
                    ChromaticMediant(
                        chord=element.chord.chord_symbol,
                        relationship="chromatic mediant",
                        explanation=element.explanation,
                    )
                )

        return ChromaticAnalysisResult(
            secondary_dominants=secondary_dominants,
            borrowed_chords=borrowed_chords,
            chromatic_mediants=chromatic_mediants,
            resolution_patterns=resolution_patterns,
        )

    def analyze_secondary_dominant_chains(
        self, secondary_dominants: List[SecondaryDominant]
    ) -> List[str]:
        """
        Analyze chains of secondary dominants (e.g., V/V/V)

        Args:
            secondary_dominants: List of detected secondary dominants

        Returns:
            List of chain descriptions
        """
        chains = []

        # Look for consecutive secondary dominants
        for i, dom in enumerate(secondary_dominants):
            if i < len(secondary_dominants) - 1:
                next_dom = secondary_dominants[i + 1]

                # Check if current target is the next secondary dominant
                if dom.target in next_dom.roman_numeral:
                    chains.append(
                        (
                            f"Secondary dominant chain: {dom.roman_numeral} → "
                            f"{next_dom.roman_numeral}"
                        )
                    )

        return chains

    def analyze_borrowed_chord_patterns(
        self, borrowed_chords: List[BorrowedChord]
    ) -> List[str]:
        """
        Analyze patterns in borrowed chords

        Args:
            borrowed_chords: List of detected borrowed chords

        Returns:
            List of pattern descriptions
        """
        patterns = []

        # Common borrowed chord patterns
        roman_numerals = [chord.roman_numeral for chord in borrowed_chords]

        # Neapolitan sixth chord pattern
        if any("bII" in rn for rn in roman_numerals):
            patterns.append(
                (
                    "Contains Neapolitan chord (bII⁶) - characteristic of "
                    "dramatic harmonic color"
                )
            )

        # Modal interchange patterns
        if any("bVII" in rn for rn in roman_numerals):
            patterns.append(
                "Contains bVII chord - borrowed from parallel minor (modal interchange)"
            )

        if any("bVI" in rn for rn in roman_numerals):
            patterns.append("Contains bVI chord - borrowed from parallel minor")

        if any("bIII" in rn for rn in roman_numerals):
            patterns.append("Contains bIII chord - borrowed from parallel minor")

        return patterns

    def get_chromatic_complexity_score(
        self, chromatic_analysis: ChromaticAnalysisResult
    ) -> float:
        """
        Calculate complexity score based on chromatic content

        Args:
            chromatic_analysis: Results of chromatic analysis

        Returns:
            Complexity score from 0.0 to 1.0
        """
        score = 0.0

        # Secondary dominants add complexity
        score += len(chromatic_analysis.secondary_dominants) * 0.2

        # Borrowed chords add moderate complexity
        score += len(chromatic_analysis.borrowed_chords) * 0.15

        # Chromatic mediants add significant complexity
        score += len(chromatic_analysis.chromatic_mediants) * 0.25

        # Resolution patterns add sophistication
        score += len(chromatic_analysis.resolution_patterns) * 0.1

        return min(score, 1.0)  # Cap at 1.0

    def should_lead_with_chromatic_analysis(
        self, chromatic_analysis: ChromaticAnalysisResult
    ) -> bool:
        """
        Determine if chromatic analysis should be the primary approach

        Args:
            chromatic_analysis: Results of chromatic analysis

        Returns:
            True if chromatic should be primary, False otherwise
        """
        # Lead with chromatic if significant secondary dominants
        if len(chromatic_analysis.secondary_dominants) > 0:
            return True

        # Lead with chromatic if multiple borrowed chords
        if len(chromatic_analysis.borrowed_chords) > 1:
            return True

        # Lead with chromatic if any chromatic mediants
        if len(chromatic_analysis.chromatic_mediants) > 0:
            return True

        return False

    def generate_chromatic_explanation(
        self, chromatic_analysis: ChromaticAnalysisResult
    ) -> str:
        """
        Generate educational explanation of chromatic elements

        Args:
            chromatic_analysis: Results of chromatic analysis

        Returns:
            Human-readable explanation of chromatic harmony
        """
        explanations = []

        # Secondary dominants explanation
        if chromatic_analysis.secondary_dominants:
            sec_dom_count = len(chromatic_analysis.secondary_dominants)
            explanations.append(
                (
                    f"This progression contains {sec_dom_count} secondary "
                    f"dominant{'s' if sec_dom_count > 1 else ''}, "
                )
                + "which temporarily tonicize other keys within the progression. "
                + (
                    "Secondary dominants create forward harmonic motion and "
                    "add chromatic color."
                )
            )

            # Mention specific secondary dominants
            for sec_dom in chromatic_analysis.secondary_dominants:
                explanations.append(f"• {sec_dom.explanation}")

        # Borrowed chords explanation
        if chromatic_analysis.borrowed_chords:
            borrowed_count = len(chromatic_analysis.borrowed_chords)
            explanations.append(
                (
                    f"The progression features {borrowed_count} borrowed "
                    f"chord{'s' if borrowed_count > 1 else ''} "
                    "through modal interchange, borrowing chords from the "
                    "parallel mode to add harmonic richness."
                )
            )

            for borrowed in chromatic_analysis.borrowed_chords:
                explanations.append(f"• {borrowed.explanation}")

        # Chromatic mediants explanation
        if chromatic_analysis.chromatic_mediants:
            explanations.append(
                "The progression includes chromatic mediant relationships, "
                + (
                    "which create dramatic harmonic shifts through "
                    "non-functional chord progressions."
                )
            )

            for mediant in chromatic_analysis.chromatic_mediants:
                explanations.append(f"• {mediant.explanation}")

        # Resolution patterns explanation
        if chromatic_analysis.resolution_patterns:
            explanations.append(
                "The chromatic elements demonstrate clear resolution patterns, "
                "showing sophisticated voice leading and harmonic logic."
            )

        return " ".join(explanations)


# Convenience function for direct analysis
def analyze_chromatic_harmony(
    functional_analysis: FunctionalAnalysisResult,
) -> Optional[ChromaticAnalysisResult]:
    """
    Analyze chromatic harmony elements from functional analysis

    Args:
        functional_analysis: Results from functional harmony analysis

    Returns:
        ChromaticAnalysisResult if chromatic elements found, None otherwise
    """
    analyzer = ChromaticAnalyzer()
    return analyzer.analyze_chromatic_elements(functional_analysis)
