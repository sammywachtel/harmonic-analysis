"""
Unified Debug System with Test Integration

Provides decorator-based debugging that can be enabled/disabled for specific tests,
plus consolidated debug capabilities from all specialized debug tools.
"""

import asyncio
import functools
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest

# Import existing debug helpers
from .debug_helpers import DebugCase, PatternDebugger, run_debug_case

# Add src to path for harmonic analysis imports
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from harmonic_analysis.core.functional_harmony import (  # noqa: E402
    FunctionalHarmonyAnalyzer,
)
from harmonic_analysis.core.pattern_engine.low_level_events import (  # noqa: E402
    LowLevelEventExtractor,
)
from harmonic_analysis.core.pattern_engine.token_converter import (  # noqa: E402
    TokenConverter,
)
from harmonic_analysis.services.pattern_analysis_service import (  # noqa: E402
    PatternAnalysisService,
)


@dataclass
class DebugConfig:
    """Configuration for debug behavior."""

    enabled: bool = False
    auto_on_failure: bool = True
    trace_patterns: bool = False
    analyze_tokens: bool = True
    analyze_intervals: bool = False
    analyze_stage_b_events: bool = False
    analyze_backdoor: bool = False
    output_file: Optional[str] = None
    verbose: bool = True


class UnifiedDebugger:
    """Consolidated debugger combining all specialized debug tools."""

    def __init__(self, config: Optional[DebugConfig] = None):
        self.config = config or DebugConfig()
        self.pattern_debugger = PatternDebugger()
        self.functional_analyzer = FunctionalHarmonyAnalyzer()
        self.token_converter = TokenConverter()
        self.event_extractor = LowLevelEventExtractor()
        self.pattern_service = PatternAnalysisService()

        # Track debug sessions
        self.debug_sessions = []

    def analyze_comprehensive(
        self,
        chords: List[str],
        profile: str = "classical",
        key_hint: Optional[str] = None,
        test_name: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis combining all debug tools.

        Returns unified debug information from all specialized analyzers.
        """
        debug_info = {
            "test_name": test_name,
            "chords": chords,
            "profile": profile,
            "key_hint": key_hint,
            "analyses": {},
        }

        try:
            # 1. Pattern Analysis (core pattern debugging functionality)
            if self.config.enabled:
                # Filter out parameters that conflict with DebugCase constructor
                filtered_kwargs = {
                    k: v
                    for k, v in kwargs.items()
                    if k not in ["trace", "trace_patterns", "analyze_all"]
                }
                case = DebugCase(
                    name=test_name or f"unified_debug_{len(chords)}_chords",
                    chords=chords,
                    profile=profile,
                    key_hint=key_hint,
                    trace=self.config.trace_patterns,
                    **filtered_kwargs,
                )
                pattern_result = run_debug_case(case, verbose=False)
                debug_info["analyses"]["patterns"] = pattern_result

            # 2. Functional Harmony Analysis (detailed)
            if self.config.analyze_tokens:
                functional_result = asyncio.run(
                    self._analyze_functional_harmony(chords, key_hint)
                )
                debug_info["analyses"]["functional"] = functional_result

            # 3. Stage B Events Analysis
            if self.config.analyze_stage_b_events:
                stage_b_result = self._analyze_stage_b_events(chords, key_hint)
                debug_info["analyses"]["stage_b"] = stage_b_result

            # 4. Backdoor Analysis (if relevant)
            if self.config.analyze_backdoor or self._is_backdoor_progression(chords):
                backdoor_result = asyncio.run(self._analyze_backdoor(chords, key_hint))
                debug_info["analyses"]["backdoor"] = backdoor_result

            # 5. Interval Analysis
            if self.config.analyze_intervals:
                interval_result = self._analyze_intervals(chords)
                debug_info["analyses"]["intervals"] = interval_result

        except Exception as e:
            debug_info["error"] = {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc(),
            }

        # Store session
        if self.config.enabled:
            self.debug_sessions.append(debug_info)

        return debug_info

    async def _analyze_functional_harmony(
        self, chords: List[str], key_hint: Optional[str]
    ) -> Dict[str, Any]:
        """Detailed functional harmony analysis with Stage B support."""
        try:
            # Use FunctionalHarmonyAnalyzer directly for detailed analysis
            result = await self.functional_analyzer.analyze_functionally(
                chords, key_hint=key_hint
            )

            # Convert to tokens for detailed inspection
            tokens = self.token_converter.convert_analysis_to_tokens(result, chords)

            # Handle both dict and DTO result types
            if hasattr(result, "key_center"):
                # DTO format (FunctionalAnalysisResult)
                key_center = result.key_center
                confidence = result.confidence
                reasoning = (
                    result.explanation
                )  # Note: it's 'explanation' not 'reasoning'
            else:
                # Dict format
                key_center = result.get("key_center")
                confidence = result.get("confidence", 0)
                reasoning = result.get("reasoning", "")

            return {
                "analysis_result": str(
                    result
                ),  # Convert to string to avoid iteration issues
                "tokens": [
                    {
                        "roman": t.roman,
                        "role": t.role,
                        "flags": list(getattr(t, "flags", [])),
                        "mode": getattr(t, "mode", None),
                        "secondary_of": getattr(t, "secondary_of", None),
                    }
                    for t in tokens
                ],
                "key_center": key_center,
                "confidence": confidence,
                "reasoning": reasoning,
            }
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}

    def _analyze_stage_b_events(
        self, chords: List[str], key_hint: Optional[str]
    ) -> Dict[str, Any]:
        """Stage B event analysis with Neapolitan and cadential 6/4 detection."""
        try:
            # Extract bass pitch classes for Stage B analysis
            bass_pcs = self.event_extractor._extract_bass_pitch_classes(chords)

            # Detect pedal points
            pedal_flags = self.event_extractor._detect_pedal_points(bass_pcs)

            # Create mock events structure for circle of fifths analysis
            class MockEvents:
                def __init__(self, chords):
                    self.root_motion = self._calculate_root_motion(chords)

                def _calculate_root_motion(self, chords):
                    # Simplified root motion calculation
                    # In real implementation, this would use the chord analysis
                    motion = []
                    for i in range(1, len(chords)):
                        # Placeholder - would calculate actual interval
                        motion.append("-5")  # Assume fifth motion for demo
                    return motion

            events = MockEvents(chords)
            circle_chains = self.event_extractor._detect_circle_of_fifths_chains(
                events, min_length=2
            )

            return {
                "bass_pitch_classes": bass_pcs,
                "pedal_points": pedal_flags,
                "circle_of_fifths_chains": circle_chains,
                "has_neapolitan_characteristics": self._check_neapolitan(
                    chords, key_hint
                ),
                "has_cadential_64_characteristics": self._check_cadential_64(chords),
            }
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}

    async def _analyze_backdoor(
        self, chords: List[str], key_hint: Optional[str]
    ) -> Dict[str, Any]:
        """Backdoor progression analysis for ♭iv7-♭VII7-I patterns."""
        try:
            # Specific analysis for backdoor progressions (♭iv7-♭VII7-I)
            is_backdoor = self._is_backdoor_progression(chords)

            if is_backdoor:
                # Detailed backdoor analysis
                result = await self.functional_analyzer.analyze_functionally(
                    chords, key_hint=key_hint
                )
                tokens = self.token_converter.convert_analysis_to_tokens(result, chords)

                return {
                    "is_backdoor": True,
                    "progression_type": "backdoor_ii_V",
                    "expected_progression": "♭iv7-♭VII7-I",
                    "analysis": result,
                    "tokens": [{"roman": t.roman, "role": t.role} for t in tokens],
                    "backdoor_quality": self._assess_backdoor_quality(chords, tokens),
                }
            else:
                return {
                    "is_backdoor": False,
                    "reason": "Progression does not match backdoor pattern",
                }
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}

    def _analyze_intervals(self, chords: List[str]) -> Dict[str, Any]:
        """Interval analysis for voice-leading and chord progression patterns."""
        try:
            # Simplified interval analysis
            root_intervals = []

            for i in range(1, len(chords)):
                # Extract roots and calculate intervals
                # This would be more sophisticated in practice
                prev_chord = chords[i - 1].split("/")[0]  # Remove slash chord info
                curr_chord = chords[i].split("/")[0]

                # Placeholder interval calculation
                interval = self._calculate_interval(prev_chord, curr_chord)
                root_intervals.append(interval)

            return {
                "root_intervals": root_intervals,
                "has_stepwise_motion": any(
                    "step" in interval for interval in root_intervals
                ),
                "has_leap_motion": any(
                    "leap" in interval for interval in root_intervals
                ),
                "predominant_motion": (
                    "fifth"
                    if root_intervals.count("fifth") > len(root_intervals) / 2
                    else "mixed"
                ),
            }
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}

    def _is_backdoor_progression(self, chords: List[str]) -> bool:
        """Check if progression matches backdoor pattern."""
        if len(chords) < 3:
            return False

        # Look for ♭iv7-♭VII7-I pattern (simplified detection)
        return (
            any("m7" in chord for chord in chords[:2])  # Has minor 7th chords
            and len(chords) >= 3
            and not any(
                "#" in chord or "b" in chord for chord in chords[-1:]
            )  # Ends on major
        )

    def _check_neapolitan(self, chords: List[str], key_hint: Optional[str]) -> bool:
        """Check for Neapolitan characteristics."""
        # Look for ♭II chord (simplified)
        return any("b" in chord or "Db" in chord or "Eb" in chord for chord in chords)

    def _check_cadential_64(self, chords: List[str]) -> bool:
        """Check for cadential 6/4 characteristics."""
        # Look for slash chords indicating inversions
        return any("/" in chord for chord in chords)

    def _calculate_interval(self, chord1: str, chord2: str) -> str:
        """Calculate interval between chord roots (simplified)."""
        # This would be more sophisticated in practice
        if chord1 == chord2:
            return "unison"
        elif abs(ord(chord1[0]) - ord(chord2[0])) == 1:
            return "step"
        elif abs(ord(chord1[0]) - ord(chord2[0])) > 3:
            return "fifth"
        else:
            return "leap"

    def _assess_backdoor_quality(self, chords: List[str], tokens: List[Any]) -> str:
        """Assess quality of backdoor progression."""
        if len(tokens) >= 3:
            roles = [getattr(t, "role", "") for t in tokens[-3:]]
            if "PD" in roles and "D" in roles and "T" in roles:
                return "strong_backdoor"
        return "weak_backdoor"

    def print_debug_summary(self, debug_info: Dict[str, Any]) -> None:
        """Print comprehensive debug summary."""
        if not self.config.verbose:
            return

        print(f"\n🔍 UNIFIED DEBUG: {debug_info['test_name'] or 'Unknown Test'}")
        print("=" * 60)
        print(f"Chords: {debug_info['chords']}")
        print(f"Profile: {debug_info['profile']}")
        if debug_info["key_hint"]:
            print(f"Key Hint: {debug_info['key_hint']}")

        for analysis_type, analysis_data in debug_info["analyses"].items():
            print(f"\n📊 {analysis_type.upper()} ANALYSIS:")
            print("-" * 30)

            if "error" in analysis_data:
                print(f"❌ Error: {analysis_data['error']}")
                continue

            if analysis_type == "patterns":
                pattern_names = analysis_data.get("pattern_names", [])
                print(f"Found patterns: {pattern_names}")

            elif analysis_type == "functional":
                tokens = analysis_data.get("tokens", [])
                print(f"Tokens: {[t['roman'] for t in tokens]}")
                print(f"Key: {analysis_data.get('key_center', 'Unknown')}")

            elif analysis_type == "stage_b":
                bass_pcs = analysis_data.get("bass_pitch_classes", [])
                pedal_points = analysis_data.get("pedal_points", [])
                print(f"Bass PCs: {bass_pcs}")
                print(f"Pedal points: {pedal_points}")

            elif analysis_type == "backdoor":
                is_backdoor = analysis_data.get("is_backdoor", False)
                print(f"Is backdoor: {is_backdoor}")
                if is_backdoor:
                    quality = analysis_data.get("backdoor_quality", "unknown")
                    print(f"Quality: {quality}")

            elif analysis_type == "intervals":
                intervals = analysis_data.get("root_intervals", [])
                print(f"Root intervals: {intervals}")

        if "error" in debug_info:
            print(f"\n❌ DEBUG ERROR: {debug_info['error']['message']}")


# Global debug instance
_unified_debugger = None


def get_unified_debugger() -> UnifiedDebugger:
    """Get or create global unified debugger instance."""
    global _unified_debugger
    if _unified_debugger is None:
        _unified_debugger = UnifiedDebugger()
    return _unified_debugger


# Decorator for enabling debug on specific tests
def debug_on_failure(
    trace_patterns: bool = False,
    analyze_tokens: bool = True,
    analyze_intervals: bool = False,
    analyze_stage_b: bool = False,
    analyze_backdoor: bool = False,
    verbose: bool = True,
    auto_extract_chords: bool = True,
):
    """
    Decorator to enable debugging when a test fails.

    Args:
        trace_patterns: Enable detailed pattern tracing
        analyze_tokens: Analyze token stream
        analyze_intervals: Include interval analysis
        analyze_stage_b: Include Stage B event analysis
        analyze_backdoor: Include backdoor progression analysis
        verbose: Print debug output
        auto_extract_chords: Try to extract chord progressions from test

    Usage:
        @debug_on_failure(trace_patterns=True, analyze_stage_b=True)
        def test_my_progression():
            result = analyze_progression(["Am", "F", "C", "G"])
            assert len(result.patterns) > 0
    """

    def decorator(test_func: Callable) -> Callable:
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            debugger = get_unified_debugger()
            original_config = debugger.config

            # Configure debug settings
            debugger.config = DebugConfig(
                enabled=False,  # Only enable on failure
                auto_on_failure=True,
                trace_patterns=trace_patterns,
                analyze_tokens=analyze_tokens,
                analyze_intervals=analyze_intervals,
                analyze_stage_b_events=analyze_stage_b,
                analyze_backdoor=analyze_backdoor,
                verbose=verbose,
            )

            try:
                # Run the test
                result = test_func(*args, **kwargs)
                return result

            except Exception as e:
                # Test failed - run debug analysis
                if auto_extract_chords:
                    chords = _extract_chords_from_test(test_func, args, kwargs, e)
                    if chords:
                        print(
                            f"\n🔍 TEST FAILED - Running debug analysis for {test_func.__name__}"
                        )

                        debugger.config.enabled = True
                        debug_info = debugger.analyze_comprehensive(
                            chords=chords,
                            test_name=test_func.__name__,
                            profile=kwargs.get("profile", "classical"),
                            key_hint=kwargs.get("key_hint"),
                        )
                        debugger.print_debug_summary(debug_info)

                        # Save debug info for potential inspection
                        wrapper._last_debug_info = debug_info

                # Re-raise the original exception
                raise e

            finally:
                # Restore original config
                debugger.config = original_config

        return wrapper

    return decorator


def debug_always(
    trace_patterns: bool = False,
    analyze_tokens: bool = True,
    analyze_intervals: bool = False,
    analyze_stage_b: bool = False,
    analyze_backdoor: bool = False,
    verbose: bool = True,
):
    """
    Decorator to always enable debugging for a test.

    Usage:
        @debug_always(trace_patterns=True, analyze_stage_b=True)
        def test_my_progression():
            result = analyze_progression(["Am", "F", "C", "G"])
            return result  # Debug info available in result._debug_info
    """

    def decorator(test_func: Callable) -> Callable:
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            debugger = get_unified_debugger()
            original_config = debugger.config

            # Configure debug settings
            debugger.config = DebugConfig(
                enabled=True,
                trace_patterns=trace_patterns,
                analyze_tokens=analyze_tokens,
                analyze_intervals=analyze_intervals,
                analyze_stage_b_events=analyze_stage_b,
                analyze_backdoor=analyze_backdoor,
                verbose=verbose,
            )

            try:
                # Extract chords and run debug analysis
                chords = _extract_chords_from_test(test_func, args, kwargs)
                if chords:
                    debug_info = debugger.analyze_comprehensive(
                        chords=chords,
                        test_name=test_func.__name__,
                        profile=kwargs.get("profile", "classical"),
                        key_hint=kwargs.get("key_hint"),
                    )
                    debugger.print_debug_summary(debug_info)

                    # Attach debug info to test context
                    wrapper._debug_info = debug_info

                # Run the test
                result = test_func(*args, **kwargs)
                return result

            finally:
                # Restore original config
                debugger.config = original_config

        return wrapper

    return decorator


def _extract_chords_from_test(
    test_func: Callable,
    args: tuple,
    kwargs: dict,
    exception: Optional[Exception] = None,
) -> Optional[List[str]]:
    """Extract chord progressions from test function parameters or docstring."""

    # 1. Look in kwargs
    for key in ["chords", "chord_symbols", "progression", "chord_progression"]:
        if key in kwargs and isinstance(kwargs[key], list):
            return kwargs[key]

    # 2. Look in args (if test follows common pattern)
    for arg in args:
        if isinstance(arg, list) and len(arg) > 0:
            # Check if it looks like chord symbols
            if all(isinstance(item, str) and len(item) <= 10 for item in arg):
                if any(char in "".join(arg) for char in "ABCDEFG#bm7/"):
                    return arg

    # 3. Look in function name (basic extraction)
    func_name = test_func.__name__

    # Extract from patterns like "test_Am_F_C_G_progression"
    import re

    chord_pattern = r"([A-G][#b]?m?\d*(?:/[A-G][#b]?)?)"
    name_chords = re.findall(chord_pattern, func_name)
    if len(name_chords) >= 2:
        return name_chords

    # 4. Look in docstring
    if test_func.__doc__:
        doc_chords = re.findall(chord_pattern, test_func.__doc__)
        if len(doc_chords) >= 2:
            return doc_chords

    # 5. Look in exception message (if provided)
    if exception and hasattr(exception, "args"):
        for arg in exception.args:
            if isinstance(arg, str):
                exc_chords = re.findall(chord_pattern, arg)
                if len(exc_chords) >= 2:
                    return exc_chords

    return None


# Pytest fixtures for unified debugging
@pytest.fixture
def unified_debugger():
    """Pytest fixture providing unified debugger instance."""
    return get_unified_debugger()


@pytest.fixture
def debug_chord_progression():
    """Pytest fixture for debugging chord progressions."""

    def _debug_progression(chords: List[str], **kwargs) -> Dict[str, Any]:
        debugger = get_unified_debugger()
        debugger.config.enabled = True

        debug_info = debugger.analyze_comprehensive(
            chords=chords, test_name="fixture_debug", **kwargs
        )
        debugger.print_debug_summary(debug_info)
        return debug_info

    return _debug_progression


# Convenience functions for manual debugging
def debug_progression(
    chords: List[str],
    profile: str = "classical",
    key_hint: Optional[str] = None,
    trace_patterns: bool = False,
    analyze_all: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """
    Quick debug function for any chord progression.

    Usage:
        debug_progression(["Am", "F", "C", "G"], trace_patterns=True, analyze_all=True)
    """
    debugger = get_unified_debugger()
    debugger.config = DebugConfig(
        enabled=True,
        trace_patterns=trace_patterns,
        analyze_tokens=True,
        analyze_intervals=analyze_all,
        analyze_stage_b_events=analyze_all,
        analyze_backdoor=analyze_all,
        verbose=True,
    )

    debug_info = debugger.analyze_comprehensive(
        chords=chords,
        profile=profile,
        key_hint=key_hint,
        test_name="manual_debug",
        **kwargs,
    )
    debugger.print_debug_summary(debug_info)
    return debug_info


def debug_test_failure(test_name: str, chords: List[str], **kwargs) -> Dict[str, Any]:
    """
    Debug a specific test failure.

    Usage:
        debug_test_failure("test_vi_IV_I_V", ["Am", "F", "C", "G"], profile="pop")
    """
    return debug_progression(
        chords=chords, test_name=test_name, analyze_all=True, **kwargs
    )
