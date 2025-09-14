"""
Debug utilities for pattern analysis testing and development.

Provides shared utilities for the unified debug system and test files,
enabling consistent debugging workflows and test case management.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from harmonic_analysis.core.pattern_engine.matcher import Matcher, Token
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService


@dataclass
class DebugCase:
    """Structured test case for pattern debugging."""

    name: str
    chords: List[str]
    profile: str = "classical"
    pattern_ids: Optional[List[str]] = None
    key_hint: Optional[str] = None
    best_cover: bool = False
    expected_patterns: Optional[List[str]] = None
    should_fail: bool = False
    description: str = ""
    trace: bool = False

    def __post_init__(self):
        if self.pattern_ids is None:
            self.pattern_ids = []
        if self.expected_patterns is None:
            self.expected_patterns = []


class PatternDebugger:
    """Enhanced pattern debugging with test integration."""

    def __init__(self):
        self.service = PatternAnalysisService()
        self.last_result = None
        self.last_tokens = None

    def dump_tokens(self, tokens: List[Token]) -> List[Dict[str, Any]]:
        """Extract token information for debugging display."""
        rows = []
        for i, t in enumerate(tokens):
            rows.append(
                {
                    "i": i,
                    "roman": t.roman,
                    "role": t.role,
                    "flags": list(getattr(t, "flags", []) or []),
                    "mode": getattr(t, "mode", None),
                    "sop": getattr(t, "soprano_degree", None),
                    "bassΔ": getattr(t, "bass_motion_from_prev", None),
                    "sec": getattr(t, "secondary_of", None),
                }
            )
        return rows

    def analyze_case(self, case: DebugCase, verbose: bool = True) -> Dict[str, Any]:
        """
        Analyze a debug case and return structured results.

        Returns:
            Dictionary with analysis results, tokens, patterns, and debug info
        """
        result = self.service.analyze_with_patterns(
            case.chords,
            profile=case.profile,
            key_hint=case.key_hint,
            best_cover=case.best_cover,
        )

        self.last_result = result

        # Extract patterns using DTO structure
        patterns = []
        pattern_names = []
        if hasattr(result, "primary") and hasattr(result.primary, "patterns"):
            patterns = result.primary.patterns or []
            pattern_names = [p.name for p in patterns if hasattr(p, "name")]

        # Try to access matcher and tokens
        matcher = None
        tokens = None
        try:
            matcher = self.service.get_pattern_matcher()
        except AttributeError:
            matcher = getattr(self.service, "_pattern_matcher", None)

        # Get tokens from service if available
        tokens = getattr(self.service, "_last_tokens", None)
        if tokens is None and hasattr(self.service, "get_last_tokens"):
            tokens = self.service.get_last_tokens()

        self.last_tokens = tokens

        debug_info = {
            "case": case,
            "result": result,
            "patterns": patterns,
            "pattern_names": pattern_names,
            "tokens": tokens,
            "matcher": matcher,
            "token_dump": self.dump_tokens(tokens) if tokens else [],
        }

        if verbose:
            self._print_analysis(debug_info)

        # Run focused traces if requested
        if case.trace and case.pattern_ids and matcher and tokens:
            trace_results = self._run_pattern_traces(case.pattern_ids, matcher, tokens)
            debug_info["trace_results"] = trace_results
            if verbose:
                self._print_traces(trace_results)

        return debug_info

    def _print_analysis(self, debug_info: Dict[str, Any]) -> None:
        """Print formatted analysis results."""
        case = debug_info["case"]
        pattern_names = debug_info["pattern_names"]
        tokens = debug_info["tokens"]

        print(f"\n=== {case.name} | {case.chords} | profile={case.profile} ===")
        if case.description:
            print(f"Description: {case.description}")

        # Show library info if available
        matcher = debug_info["matcher"]
        if matcher and hasattr(matcher, "library"):
            lib = matcher.library
            if lib:
                print(
                    f"Loaded patterns (last 10): {[p.id for p in lib.patterns[-10:]]}"
                )

        # Show tokens
        if tokens:
            print("\nTOKENS:")
            for row in debug_info["token_dump"]:
                print(f"  {row}")
        else:
            print("[note] Tokens not available from service")

        # Show found patterns
        print(f"Found patterns: {pattern_names}")

        # Show expectations
        if case.expected_patterns:
            missing = set(case.expected_patterns) - set(pattern_names)
            unexpected = set(pattern_names) - set(case.expected_patterns)
            if missing:
                print(f"⚠️  Missing expected patterns: {list(missing)}")
            if unexpected:
                print(f"ℹ️  Unexpected patterns found: {list(unexpected)}")
            if not missing and not unexpected:
                print("✅ All expected patterns found")

    def _run_pattern_traces(
        self, pattern_ids: List[str], matcher: Matcher, tokens: List[Token]
    ) -> Dict[str, Any]:
        """Run detailed traces for specific patterns."""
        trace_results = {}
        lib = getattr(matcher, "library", None)

        if not lib:
            return {"error": "No library available for tracing"}

        for pid in pattern_ids:
            pat = lib.get_pattern_by_id(pid)
            if not pat:
                trace_results[pid] = {"error": f"Pattern {pid} not found in library"}
                continue

            matches = []
            min_len = pat.window.get("min", 1)
            max_len = pat.window.get("max", 8)

            for start in range(len(tokens)):
                for end in range(
                    start + min_len, min(len(tokens), start + max_len) + 1
                ):
                    window_tokens = tokens[start:end]
                    try:
                        mr = matcher._try_match_pattern(pat, window_tokens)
                        if mr.success:
                            matches.append(
                                {
                                    "window": (start, end),
                                    "score": mr.score,
                                    "evidence": mr.evidence,
                                    "tokens": [t.roman for t in window_tokens],
                                }
                            )
                        elif start == 0:  # Show first failure for debugging
                            matches.append(
                                {
                                    "window": (start, end),
                                    "failed": True,
                                    "reason": mr.failure_reason,
                                    "debug_info": mr.debug_info,
                                    "tokens": [t.roman for t in window_tokens],
                                }
                            )
                    except Exception as e:
                        matches.append(
                            {
                                "window": (start, end),
                                "error": str(e),
                                "tokens": [t.roman for t in window_tokens],
                            }
                        )

            trace_results[pid] = {
                "pattern": pat,
                "matches": matches,
                "success_count": len([m for m in matches if m.get("score", 0) > 0]),
            }

        return trace_results

    def _print_traces(self, trace_results: Dict[str, Any]) -> None:
        """Print formatted trace results."""
        for pid, trace in trace_results.items():
            print(f"\n-- Trace {pid} --")
            if "error" in trace:
                print(f"  Error: {trace['error']}")
                continue

            matches = trace["matches"]
            success_count = trace["success_count"]

            if success_count == 0:
                print("  (no matches)")
                # Show first failure for debugging
                failed = [m for m in matches if m.get("failed")]
                if failed:
                    f = failed[0]
                    print(
                        f"  x {f['window']} failed: {f.get('reason', 'unknown')} | tokens: {f['tokens']}"
                    )
            else:
                for match in matches:
                    if match.get("score", 0) > 0:
                        print(
                            f"  ✓ match @ {match['window']}: score={match['score']} | tokens: {match['tokens']}"
                        )


def run_debug_case(case: DebugCase, verbose: bool = True) -> Dict[str, Any]:
    """Convenience function to run a single debug case."""
    debugger = PatternDebugger()
    return debugger.analyze_case(case, verbose=verbose)


def create_test_from_case(case: DebugCase):
    """
    Create a pytest test function from a DebugCase.
    Usage: test_func = create_test_from_case(my_case)
    """

    def test_func():
        debug_info = run_debug_case(case, verbose=False)
        pattern_names = debug_info["pattern_names"]

        if case.should_fail:
            assert (
                len(pattern_names) == 0
            ), f"Expected no patterns but found: {pattern_names}"
        elif case.expected_patterns:
            missing = set(case.expected_patterns) - set(pattern_names)
            assert (
                not missing
            ), f"Missing expected patterns: {missing}. Found: {pattern_names}"

        # Ensure analysis completed successfully
        assert debug_info["result"] is not None
        if hasattr(debug_info["result"], "primary"):
            assert debug_info["result"].primary.confidence > 0

    test_func.__name__ = f"test_{case.name.replace(' ', '_').replace('-', '_').lower()}"
    return test_func


# Common debug cases for reuse across tests
COMMON_DEBUG_CASES = [
    DebugCase(
        name="pop_vi_IV_I_V",
        chords=["Am", "F", "C", "G"],
        profile="pop",
        pattern_ids=["vi_IV_I_V"],
        expected_patterns=["vi–IV–I–V"],
        description="Common pop progression vi-IV-I-V",
    ),
    DebugCase(
        name="jazz_ii_V_I",
        chords=["Dm7", "G7", "Cmaj7"],
        profile="jazz",
        pattern_ids=["ii_V_I"],
        expected_patterns=["ii–V–I"],
        description="Classic jazz ii-V-I progression",
    ),
    DebugCase(
        name="phrygian_cadence",
        chords=["Am", "Dm/F", "E"],
        profile="classical",
        pattern_ids=["cadence_phrygian_relaxed"],
        description="Phrygian half cadence in A minor",
    ),
    DebugCase(
        name="pachelbel_canon",
        chords=["D", "A", "Bm", "F#m", "G", "D", "G", "A"],
        profile="pop",
        pattern_ids=["pachelbel_canon_core_roots"],
        description="Pachelbel Canon progression in D major",
    ),
    DebugCase(
        name="andalusian_cadence",
        chords=["Am", "G", "F", "E"],
        profile="classical",
        pattern_ids=["cadence_andalusian_minor", "cadence_andalusian_relaxed"],
        description="Andalusian cadence vi-bVII-bVI-V",
    ),
    DebugCase(
        name="backdoor_progression",
        chords=["Fm7", "Bb7", "Cmaj7"],
        profile="jazz",
        pattern_ids=["cadence_backdoor"],
        key_hint="C major",
        description="Backdoor ii-V progression biv-bVII-I",
    ),
    DebugCase(
        name="cadential_64",
        chords=["C/G", "G7", "C"],
        profile="classical",
        key_hint="C major",
        pattern_ids=["cadential_64"],
        trace=True,
        description="Cadential 6/4 pattern I64-V-I",
    ),
]


def get_case_by_name(name: str) -> Optional[DebugCase]:
    """Get a common debug case by name."""
    for case in COMMON_DEBUG_CASES:
        if case.name == name:
            return case
    return None


def list_available_cases() -> List[str]:
    """List all available common debug cases."""
    return [case.name for case in COMMON_DEBUG_CASES]
