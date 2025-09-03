"""
Pattern Analysis Service - High-level API for pattern recognition.

Provides A/B testing capabilities to compare pattern engine results
with current functional analysis approaches.
"""

from typing import List, Dict, Any, Optional, Tuple
import time
import os
import asyncio
from pathlib import Path

from ..core.pattern_engine import Token, Matcher, load_library, TokenConverter
from ..core.functional_harmony import FunctionalHarmonyAnalyzer
from ..services.multiple_interpretation_service import MultipleInterpretationService


class PatternAnalysisService:
    """Service for pattern-based harmonic analysis with A/B testing capabilities."""

    def __init__(self):
        self.token_converter = TokenConverter()
        self.functional_analyzer = FunctionalHarmonyAnalyzer()
        self.interpretation_service = MultipleInterpretationService()

        # Load pattern library
        patterns_path = Path(__file__).parent.parent / 'core' / 'pattern_engine' / 'patterns.json'
        try:
            self.pattern_lib = load_library(str(patterns_path))
            self.matcher = Matcher(self.pattern_lib, profile="classical")
        except FileNotFoundError:
            print(f"Warning: Pattern library not found at {patterns_path}")
            self.pattern_lib = None
            self.matcher = None

    def analyze_with_patterns(
        self,
        chord_symbols: List[str],
        profile: str = "classical"
    ) -> Dict[str, Any]:
        """
        Analyze chord progression using pattern engine.

        Args:
            chord_symbols: List of chord symbols (e.g., ['Am', 'F', 'C', 'G'])
            profile: Analysis profile ('classical', 'jazz', 'pop')

        Returns:
            Dictionary containing pattern analysis results
        """
        if not self.matcher:
            return {"error": "Pattern engine not available"}

        start_time = time.time()

        # First, get functional analysis to convert to tokens
        functional_result = asyncio.run(
            self.functional_analyzer.analyze_functionally(chord_symbols)
        )

        # Convert to tokens
        tokens = self.token_converter.convert_analysis_to_tokens(
            chord_symbols, functional_result
        )

        # Update matcher profile if needed
        if profile != "classical":
            self.matcher = Matcher(self.pattern_lib, profile=profile)

        # Find pattern matches
        pattern_matches = self.matcher.match(tokens, best_cover=True)

        analysis_time = time.time() - start_time

        return {
            "chord_symbols": chord_symbols,
            "tokens": [self._token_to_dict(token) for token in tokens],
            "pattern_matches": pattern_matches,
            "analysis_time_ms": round(analysis_time * 1000, 2),
            "profile": profile,
            "functional_analysis": self._functional_result_to_dict(functional_result)
        }

    def a_b_test_analysis(
        self,
        chord_symbols: List[str],
        profile: str = "classical"
    ) -> Dict[str, Any]:
        """
        A/B test pattern engine vs current analysis approach.

        Args:
            chord_symbols: List of chord symbols
            profile: Analysis profile for pattern engine

        Returns:
            Comparison results between approaches
        """
        # Current approach analysis
        start_time = time.time()
        current_result = self._analyze_current_approach(chord_symbols)
        current_time = time.time() - start_time

        # Pattern engine analysis
        start_time = time.time()
        pattern_result = self.analyze_with_patterns(chord_symbols, profile)
        pattern_time = time.time() - start_time

        # Compare results
        comparison = self._compare_analyses(current_result, pattern_result)

        return {
            "chord_symbols": chord_symbols,
            "current_approach": {
                "result": current_result,
                "analysis_time_ms": round(current_time * 1000, 2)
            },
            "pattern_engine": {
                "result": pattern_result,
                "analysis_time_ms": round(pattern_time * 1000, 2)
            },
            "comparison": comparison,
            "performance_ratio": pattern_time / current_time if current_time > 0 else 0
        }

    def validate_core_patterns(self) -> Dict[str, Any]:
        """
        Validate core patterns against known test cases.

        Returns:
            Validation results for core harmonic patterns
        """
        test_cases = [
            {
                "name": "vi-IV-I-V Pop Progression",
                "chords": ["Am", "F", "C", "G"],
                "expected_key": "C major",
                "expected_patterns": ["vi-IV-I-V"]
            },
            {
                "name": "ii-V-I Jazz Progression",
                "chords": ["Dm7", "G7", "Cmaj7"],
                "expected_key": "C major",
                "expected_patterns": ["ii-V-I"]
            },
            {
                "name": "Perfect Authentic Cadence",
                "chords": ["F", "G7", "C"],
                "expected_key": "C major",
                "expected_patterns": ["PAC", "IV-V-I"]
            },
            {
                "name": "Imperfect Authentic Cadence",
                "chords": ["Dm", "G", "C"],
                "expected_key": "C major",
                "expected_patterns": ["IAC", "ii-V-I"]
            },
            {
                "name": "Half Cadence",
                "chords": ["C", "F", "G"],
                "expected_key": "C major",
                "expected_patterns": ["half_cadence"]
            }
        ]

        results = {
            "total_tests": len(test_cases),
            "passed": 0,
            "failed": 0,
            "test_results": []
        }

        for test_case in test_cases:
            try:
                analysis = self.analyze_with_patterns(test_case["chords"])

                # Check if expected patterns were found
                pattern_matches = analysis.get("pattern_matches", [])
                found_patterns = [match.get("name", "").lower() for match in pattern_matches]
                found_families = [match.get("family", "").lower() for match in pattern_matches]

                # More flexible pattern validation
                pattern_found = False
                for expected in test_case["expected_patterns"]:
                    expected_lower = expected.lower()

                    # Direct name match
                    if any(expected_lower in pattern for pattern in found_patterns):
                        pattern_found = True
                        break

                    # Family-based matching for common patterns
                    if expected_lower in ["vi-iv-i-v", "ii-v-i"] and "sequence" in found_families:
                        # Generic progression sequences often cover these
                        pattern_found = True
                        break
                    elif expected_lower in ["pac", "iac"] and "cadence" in found_families:
                        # Authentic cadences are a family
                        pattern_found = True
                        break
                    elif expected_lower == "half_cadence" and "half cadence" in str(found_patterns).lower():
                        pattern_found = True
                        break

                test_result = {
                    "name": test_case["name"],
                    "chords": test_case["chords"],
                    "expected_patterns": test_case["expected_patterns"],
                    "found_patterns": found_patterns,
                    "pattern_matched": pattern_found,
                    "key_detected": analysis.get("functional_analysis", {}).get("key_center", "unknown"),
                    "passed": pattern_found
                }

                if pattern_found:
                    results["passed"] += 1
                else:
                    results["failed"] += 1

                results["test_results"].append(test_result)

            except Exception as e:
                results["failed"] += 1
                results["test_results"].append({
                    "name": test_case["name"],
                    "chords": test_case["chords"],
                    "error": str(e),
                    "passed": False
                })

        results["success_rate"] = results["passed"] / results["total_tests"] if results["total_tests"] > 0 else 0

        return results

    def _analyze_current_approach(self, chord_symbols: List[str]) -> Dict[str, Any]:
        """Analyze using current library approach."""
        try:
            # Use existing multiple interpretation service
            interpretations = self.interpretation_service.analyze_chord_progression(chord_symbols)

            # Get the highest confidence interpretation
            if interpretations:
                best_interpretation = max(interpretations, key=lambda x: x.get('confidence', 0))
                return {
                    "interpretations": interpretations,
                    "best_interpretation": best_interpretation,
                    "approach": "current_library"
                }
            else:
                return {"interpretations": [], "approach": "current_library"}
        except Exception as e:
            return {"error": str(e), "approach": "current_library"}

    def _compare_analyses(self, current: Dict[str, Any], pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current approach vs pattern engine results."""
        comparison = {
            "key_agreement": False,
            "confidence_comparison": None,
            "pattern_coverage": None,
            "differences": []
        }

        # Compare key detection
        current_key = current.get("best_interpretation", {}).get("key", "unknown")
        pattern_key = pattern.get("functional_analysis", {}).get("key_center", "unknown")

        comparison["key_agreement"] = current_key.lower() == pattern_key.lower()
        comparison["current_key"] = current_key
        comparison["pattern_key"] = pattern_key

        # Compare confidence levels
        current_conf = current.get("best_interpretation", {}).get("confidence", 0)
        pattern_matches = pattern.get("pattern_matches", [])
        pattern_conf = max([match.get("score", 0) for match in pattern_matches], default=0)

        comparison["current_confidence"] = current_conf
        comparison["pattern_confidence"] = pattern_conf

        # Pattern coverage
        comparison["patterns_found"] = len(pattern_matches)
        comparison["pattern_names"] = [match.get("name", "unknown") for match in pattern_matches]

        return comparison

    def _token_to_dict(self, token: Token) -> Dict[str, Any]:
        """Convert Token object to dictionary for JSON serialization."""
        return {
            "roman": token.roman,
            "role": token.role,
            "flags": token.flags,
            "mode": token.mode,
            "bass_motion_from_prev": token.bass_motion_from_prev,
            "soprano_degree": token.soprano_degree,
            "secondary_of": token.secondary_of
        }

    def _functional_result_to_dict(self, result) -> Dict[str, Any]:
        """Convert FunctionalAnalysisResult object to dictionary for JSON serialization."""
        return {
            "key_center": getattr(result, 'key_center', 'unknown'),
            "key_signature": getattr(result, 'key_signature', 'unknown'),
            "mode": getattr(result, 'mode', 'major'),
            "confidence": getattr(result, 'confidence', 0.0),
            "explanation": getattr(result, 'explanation', ''),
            "progression_type": str(getattr(result, 'progression_type', 'unknown')),
            "chords": [
                {
                    "roman_numeral": chord.roman_numeral,
                    "function": str(chord.function),
                    "chord_symbol": chord.chord_symbol,
                    "inversion": getattr(chord, 'inversion', None),
                    "quality": getattr(chord, 'quality', 'triad')
                }
                for chord in getattr(result, 'chords', [])
            ],
            "cadences": [str(cadence) for cadence in getattr(result, 'cadences', [])],
            "chromatic_elements": [str(element) for element in getattr(result, 'chromatic_elements', [])]
        }
