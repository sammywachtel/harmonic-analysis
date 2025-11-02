"""
Regression tests for pattern matching fixes.

These tests ensure that the roman numeral normalization fixes
from Iteration 5 continue to work properly.
"""

from harmonic_analysis.core.pattern_engine.pattern_engine import (
    AnalysisContext,
    PatternEngine,
)


class TestPatternMatchingRegression:
    """Test specific pattern matching issues that were fixed."""

    def test_v7_matches_v_pattern_regression(self):
        """
        Regression test: V7 in context should match V pattern.

        This was broken before the roman numeral normalization fix,
        where V7 != V caused 0 evidence pieces to be found.
        """
        # Opening move: create test context with V7->I progression
        context = AnalysisContext(
            key="C major",
            chords=["G7", "C"],
            roman_numerals=["V7", "I"],
            melody=[],
            scales=[],
            metadata={"profile": "classical"},
        )

        # Main play: create engine and load patterns
        engine = PatternEngine()
        from pathlib import Path

        patterns_path = Path(
            "src/harmonic_analysis/resources/patterns/patterns_unified.json"
        )
        engine.load_patterns(patterns_path)

        # Victory lap: verify pattern matching finds evidence
        evidences = engine._match_patterns(context)

        # Should find evidence (not 0 as before the fix)
        assert len(evidences) > 0, "Should find pattern evidence for V7->I progression"

        # Should specifically find perfect authentic cadence
        pac_evidence = [
            e
            for e in evidences
            if e.pattern_id == "functional.cadence.authentic.perfect"
        ]
        assert len(pac_evidence) >= 1, "Should find perfect authentic cadence pattern"

        # Should have reasonable confidence
        pac = pac_evidence[0]
        assert (
            pac.raw_score > 0.5
        ), f"PAC should have high confidence, got {pac.raw_score}"

    def test_roman_numeral_normalization_cases(self):
        """Test the _normalize_roman_for_matching function with various inputs."""
        engine = PatternEngine()

        test_cases = [
            # Basic 7th chords
            ("V7", "V"),
            ("ii7", "ii"),
            ("vii°7", "vii°"),
            # Secondary dominants
            ("V/vi", "V"),
            ("V7/ii", "V"),
            ("vii°/V", "vii°"),
            # Inversions (if any)
            ("V64", "V"),
            ("IV6", "IV"),
            # Complex cases
            ("V7/vi", "V"),
            ("ii°7", "ii°"),
            # Should not change
            ("I", "I"),
            ("vi", "vi"),
            ("IV", "IV"),
        ]

        for input_roman, expected in test_cases:
            result = engine._normalize_roman_for_matching(input_roman)
            assert (
                result == expected
            ), f"Expected {input_roman} -> {expected}, got {result}"

    def test_pattern_engine_end_to_end_regression(self):
        """End-to-end test that full analysis works after pattern matching fix."""
        # Opening move: test the full analysis pipeline
        import asyncio

        from harmonic_analysis.services.pattern_analysis_service import (
            PatternAnalysisService,
        )

        async def run_test():
            service = PatternAnalysisService()

            # Test case that was failing before the fix
            result = await service.analyze_with_patterns_async(
                ["G7", "C"], key_hint="C major"
            )

            # Should now return functional analysis with high confidence
            from harmonic_analysis.dto import AnalysisType

            assert (
                result.primary.type == AnalysisType.FUNCTIONAL
            ), "Should classify as functional"
            assert (
                result.primary.confidence > 0.5
            ), f"Should have high confidence, got {result.primary.confidence}"
            assert result.primary.roman_numerals == [
                "V7",
                "I",
            ], "Should preserve roman numerals"

            return result

        # Victory lap: run the async test
        result = asyncio.run(run_test())
        assert result is not None, "Analysis should complete successfully"
