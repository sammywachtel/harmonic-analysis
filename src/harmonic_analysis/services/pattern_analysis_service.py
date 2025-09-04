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

from ..core.pattern_engine import Token, Matcher, load_library, TokenConverter, GlossaryService
from ..core.functional_harmony import FunctionalHarmonyAnalyzer
from ..services.multiple_interpretation_service import MultipleInterpretationService
from ..api.analysis import analyze_chord_progression


class PatternAnalysisService:
    """Service for pattern-based harmonic analysis with A/B testing capabilities."""

    def __init__(self):
        self.token_converter = TokenConverter()
        self.functional_analyzer = FunctionalHarmonyAnalyzer()
        self.interpretation_service = MultipleInterpretationService()
        self.glossary_service = GlossaryService()

        # Load pattern library
        patterns_path = Path(__file__).parent.parent / 'core' / 'pattern_engine' / 'patterns.json'
        try:
            self.pattern_lib = load_library(str(patterns_path))
            self.matcher = Matcher(self.pattern_lib, profile="classical")
        except FileNotFoundError:
            print(f"Warning: Pattern library not found at {patterns_path}")
            self.pattern_lib = None
            self.matcher = None

        # ---- DEBUG EXPOSURE (safe to remove later) ----
        # Expose matcher so debug_patterns.py can introspect the engine internals.
        # Remove these lines once validation is complete.
        self._pattern_matcher = self.matcher
        # Will be populated per-call in analyze_with_patterns
        self._last_tokens = None
        # ---- END DEBUG EXPOSURE ----

    # ---- DEBUG GETTERS (safe to remove later) ----
    def get_pattern_matcher(self):
        """[DEBUG] Expose the PatternMatcher instance. Safe to remove later."""
        return getattr(self, "_pattern_matcher", None)

    def get_last_tokens(self):
        """[DEBUG] Return the last token sequence used for matching. Safe to remove later."""
        return getattr(self, "_last_tokens", None)
    # ---- END DEBUG GETTERS ----

    def analyze_with_patterns(
        self,
        chord_symbols: List[str],
        profile: str = "classical",
        best_cover: bool = True,
        key_hint: str | None = None,   # ← add this
    ) -> Dict[str, Any]:
        """
        Analyze chord progression using pattern engine.

        Args:
            chord_symbols: List of chord symbols (e.g., ['Am', 'F', 'C', 'G'])
            profile: Analysis profile ('classical', 'jazz', 'pop')
            best_cover: If True, return best non-overlapping cover; if False, return all candidates.

        Returns:
            Dictionary containing pattern analysis results
        """
        if not self.matcher:
            return {"error": "Pattern engine not available"}

        start_time = time.time()

        # First, get functional analysis with key hint
        functional_result = asyncio.run(
            self.functional_analyzer.analyze_functionally(
                chord_symbols, key_hint=key_hint, lock_key=True
            )
        )

        # Convert to tokens (no key_hint - use analysis result key)
        tokens = self.token_converter.convert_analysis_to_tokens(
            chord_symbols=chord_symbols,
            analysis_result=functional_result,
        )
        # ---- DEBUG EXPOSURE (safe to remove later) ----
        self._last_tokens = tokens
        # ---- END DEBUG EXPOSURE ----

        # Update matcher profile if needed
        if profile != "classical":
            self.matcher = Matcher(self.pattern_lib, profile=profile)
            # ---- DEBUG EXPOSURE (safe to remove later) ----
            self._pattern_matcher = self.matcher
            # ---- END DEBUG EXPOSURE ----

        # Find pattern matches
        pattern_matches = self.matcher.match(tokens, best_cover=best_cover)

        analysis_time = time.time() - start_time

        return {
            "chord_symbols": chord_symbols,
            "tokens": [self._token_to_dict(token) for token in tokens],
            "pattern_matches": pattern_matches,
            "analysis_time_ms": round(analysis_time * 1000, 2),
            "profile": profile,
            "functional_analysis": self._functional_result_to_dict(functional_result)
        }

    def analyze_with_educational_context(
        self,
        chord_symbols: List[str],
        profile: str = "classical"
    ) -> Dict[str, Any]:
        """
        Analyze chord progression with educational explanations and glossary context.

        Args:
            chord_symbols: List of chord symbols
            profile: Analysis profile

        Returns:
            Analysis results enhanced with educational context
        """
        # Get standard pattern analysis
        basic_analysis = self.analyze_with_patterns(chord_symbols, profile)

        # Enhance with educational context
        enhanced_matches = []
        for match in basic_analysis.get("pattern_matches", []):
            enhanced_match = self.glossary_service.explain_pattern_result(match)
            enhanced_matches.append(enhanced_match)

        # Generate teaching points
        teaching_points = self.glossary_service.get_pattern_teaching_points(
            basic_analysis.get("pattern_matches", [])
        )

        # Add glossary explanations for key terms found
        key_terms = self._extract_key_terms(basic_analysis)
        term_definitions = {}
        for term in key_terms:
            definition = self.glossary_service.get_term_definition(term)
            if definition:
                term_definitions[term] = definition

        return {
            **basic_analysis,
            "enhanced_pattern_matches": enhanced_matches,
            "teaching_points": teaching_points,
            "term_definitions": term_definitions,
            "educational_analysis": True
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
                "expected_patterns": ["vi-IV-I-V"],
                "profile": "pop"
            },
            {
                "name": "ii-V-I Jazz Progression",
                "chords": ["Dm7", "G7", "Cmaj7"],
                "expected_key": "C major",
                "expected_patterns": ["ii-V-I"],
                "profile": "jazz"
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
            },
            {
                "name": "Phrygian Cadence (minor)",
                "chords": ["Am", "Dm/F", "E"],
                "expected_key": "A minor",
                "expected_patterns": ["phrygian"],
                "profile": "classical"
            },
            {
                "name": "Pachelbel Canon Core (D)",
                "chords": ["D", "A", "Bm", "F#m", "G", "D", "G", "A"],
                "expected_key": "D major",
                "expected_patterns": ["pachelbel"],
                "profile": "pop"
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
                analysis = self.analyze_with_patterns(
                    test_case["chords"],
                    profile=test_case.get("profile", "classical"),
                    best_cover=False,
                )

                # Check if expected patterns were found
                pattern_matches = analysis.get("pattern_matches", [])
                found_patterns = [match.get("name", "").lower() for match in pattern_matches]
                found_families = [match.get("family", "").lower() for match in pattern_matches]

                # More flexible pattern validation (aliases, families, descriptors)
                pattern_found = False

                # helpers
                def name_has(s: str) -> bool:
                    s = s.lower()
                    return any(s in p for p in found_patterns)

                def fam_has(s: str) -> bool:
                    s = s.lower()
                    return any(s in f for f in found_families)

                # alias map
                ALIASES = {
                    "vi-iv-i-v": ["vi–iv–i–v", "i–v–vi–iv", "i–vi–iv–v", "pop loop", "jazz_pop"],
                    "ii-v-i": ["ii–v–i", "ii–v–i (macro)", "jazz ii–v–i"],
                    "pac": ["perfect authentic cadence", "authentic cadence"],
                    "iac": ["imperfect authentic cadence"],
                    "half_cadence": ["half cadence"],
                    "phrygian": ["phrygian"],
                    "pachelbel": ["pachelbel", "pachelbel canon core"]
                }

                for expected in test_case["expected_patterns"]:
                    e = expected.lower()

                    # direct name or alias
                    if name_has(e) or any(name_has(a) for a in ALIASES.get(e, [])):
                        pattern_found = True
                        break

                    # family-based acceptance
                    if e in ("vi-iv-i-v", "ii-v-i"):
                        if fam_has("jazz_pop") or fam_has("sequence"):
                            pattern_found = True
                            break
                    if e in ("pac", "iac", "half_cadence", "phrygian"):
                        if fam_has("cadence"):
                            pattern_found = True
                            break
                    if e == "pachelbel" and fam_has("schema"):
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
        """Analyze using current library approach (public API)."""
        try:
            # Use the public API - what users actually call
            result = asyncio.run(analyze_chord_progression(chord_symbols))

            # Extract information from MultipleInterpretationResult
            primary_analysis = getattr(result, 'primary_analysis', None)
            alternative_analyses = getattr(result, 'alternative_analyses', [])

            # Build best interpretation from primary analysis
            best_interpretation = {}
            if primary_analysis:
                best_interpretation = {
                    'key': getattr(primary_analysis, 'key', 'unknown'),
                    'confidence': getattr(primary_analysis, 'confidence', 0.0),
                    'analysis': getattr(primary_analysis, 'analysis', ''),
                    'interpretation_type': getattr(primary_analysis, 'interpretation_type', 'unknown')
                }

            # Build interpretations list
            interpretations = [best_interpretation] if best_interpretation else []
            for alt in alternative_analyses:
                interpretations.append({
                    'key': getattr(alt, 'key', 'unknown'),
                    'confidence': getattr(alt, 'confidence', 0.0),
                    'analysis': getattr(alt, 'analysis', ''),
                    'interpretation_type': getattr(alt, 'interpretation_type', 'unknown')
                })

            return {
                "interpretations": interpretations,
                "best_interpretation": best_interpretation,
                "approach": "public_api",
                "result_type": str(type(result).__name__)
            }
        except Exception as e:
            return {"error": str(e), "approach": "public_api"}

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

    def _extract_key_terms(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract key musical terms from analysis for glossary lookup."""
        key_terms = set()

        # Extract terms from pattern matches
        for match in analysis.get("pattern_matches", []):
            family = match.get("family", "").lower()
            if family:
                key_terms.add(family)

            # Extract role terms from evidence
            if isinstance(match.get("evidence"), list):
                for evidence_item in match["evidence"]:
                    if len(evidence_item) >= 3:
                        role = evidence_item[2].lower()
                        if role in ['t', 'tonic']:
                            key_terms.add('tonic')
                        elif role in ['pd', 'predominant']:
                            key_terms.add('predominant')
                        elif role in ['d', 'dominant']:
                            key_terms.add('dominant')

        # Extract terms from tokens
        for token in analysis.get("tokens", []):
            role = token.get("role", "").lower()
            if role in ['t', 'tonic']:
                key_terms.add('tonic')
            elif role in ['pd', 'predominant']:
                key_terms.add('predominant')
            elif role in ['d', 'dominant']:
                key_terms.add('dominant')

        # Add common terms
        key_terms.add('scale_degree')

        return list(key_terms)
