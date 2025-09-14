"""
Test debugging utilities.

Provides utilities for debugging failing tests and creating debug cases
from test failures.
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

# Add debug helpers to path
sys.path.insert(0, str(Path(__file__).parent))
from debug_helpers import DebugCase, PatternDebugger, run_debug_case  # noqa: E402


class TestFailureDebugger:
    """Utilities for debugging test failures."""

    @staticmethod
    def create_case_from_failure(
        test_function_name: str,
        chords: List[str],
        profile: str = "classical",
        pattern_ids: Optional[List[str]] = None,
        **kwargs,
    ) -> DebugCase:
        """
        Create a debug case from a failing test.

        Args:
            test_function_name: Name of the failing test function
            chords: Chord progression that failed
            profile: Analysis profile
            pattern_ids: Pattern IDs to trace
            **kwargs: Additional DebugCase parameters
        """
        case_name = test_function_name.replace("test_", "debug_")

        return DebugCase(
            name=case_name,
            chords=chords,
            profile=profile,
            pattern_ids=pattern_ids or [],
            description=f"Debug case for failing test: {test_function_name}",
            trace=True,  # Enable tracing for debugging
            **kwargs,
        )

    @staticmethod
    def debug_test_case(
        test_function_name: str,
        chords: List[str],
        profile: str = "classical",
        pattern_ids: Optional[List[str]] = None,
        verbose: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Quick debug of a test case.

        Returns the debug_info dictionary for further analysis.
        """
        case = TestFailureDebugger.create_case_from_failure(
            test_function_name, chords, profile, pattern_ids, **kwargs
        )

        return run_debug_case(case, verbose=verbose)

    @staticmethod
    def extract_progression_from_test_name(test_name: str) -> Optional[List[str]]:
        """
        Try to extract chord progression from test name.

        Looks for patterns like:
        - test_vi_IV_I_V_in_A_major -> ["F#m", "D", "A", "E"] (if key context available)
        - test_Dm_G_C_progression -> ["Dm", "G", "C"]
        """
        # Look for Roman numeral patterns
        roman_pattern = r"([ivIV]+)_([ivIV]+)_([ivIV]+)(?:_([ivIV]+))?"
        match = re.search(roman_pattern, test_name)

        if match:
            romans = [g for g in match.groups() if g is not None]
            # Would need key context to convert to actual chords
            # For now, return as placeholder
            return [f"Chord{i+1}" for i in range(len(romans))]

        # Look for chord symbol patterns
        chord_pattern = r"([A-G][#b]?m?\d*(?:/[A-G][#b]?)?)"
        chords = re.findall(chord_pattern, test_name)

        if chords and len(chords) >= 2:
            return chords

        return None


def debug_failing_test(
    test_name: str,
    chords: Optional[List[str]] = None,
    profile: str = "classical",
    pattern_ids: Optional[List[str]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Convenience function to debug a failing test.

    Args:
        test_name: Name of the failing test
        chords: Chord progression (will try to extract from test name if not provided)
        profile: Analysis profile
        pattern_ids: Pattern IDs to trace
        **kwargs: Additional debug parameters

    Returns:
        Debug info dictionary
    """
    if chords is None:
        chords = TestFailureDebugger.extract_progression_from_test_name(test_name)
        if chords is None:
            raise ValueError(
                f"Could not extract chord progression from test name '{test_name}'. Please provide chords manually."
            )

    return TestFailureDebugger.debug_test_case(
        test_name, chords, profile, pattern_ids, **kwargs
    )


class DebugTestRunner:
    """Test runner with enhanced debugging capabilities."""

    def __init__(self):
        self.failed_tests = []
        self.debug_cases = []

    def run_with_debug(
        self, test_module_or_function, auto_debug_failures: bool = False, **pytest_args
    ):
        """
        Run tests with automatic debug case generation for failures.

        Args:
            test_module_or_function: Test module, function, or path to run
            auto_debug_failures: If True, automatically create debug cases for failures
            **pytest_args: Additional arguments to pass to pytest
        """

        # Custom pytest plugin to capture failures
        class DebugCapturePlugin:
            def __init__(self, runner):
                self.runner = runner

            def pytest_runtest_logreport(self, report):
                if report.failed and hasattr(report, "longrepr"):
                    self.runner.failed_tests.append(
                        {
                            "nodeid": report.nodeid,
                            "longrepr": str(report.longrepr),
                            "outcome": report.outcome,
                        }
                    )

        plugin = DebugCapturePlugin(self)

        # Run pytest with our plugin
        pytest_args["plugins"] = pytest_args.get("plugins", []) + [plugin]
        exit_code = pytest.main(
            [test_module_or_function]
            + [
                f"--{k}={v}" if v is not True else f"--{k}"
                for k, v in pytest_args.items()
                if k != "plugins"
            ]
        )

        if auto_debug_failures and self.failed_tests:
            print(f"\\n🔍 Auto-debugging {len(self.failed_tests)} failed tests...")
            self._auto_debug_failures()

        return exit_code

    def _auto_debug_failures(self):
        """Automatically create debug cases for failed tests."""
        for failure in self.failed_tests:
            test_name = failure["nodeid"].split("::")[-1]

            try:
                # Try to extract progression from error message or test name
                chords = self._extract_chords_from_failure(failure)
                if chords:
                    print(f"\\n🔍 Debugging {test_name}...")
                    debug_info = debug_failing_test(test_name, chords)
                    self.debug_cases.append(debug_info)
                else:
                    print(f"⚠️  Could not extract chord progression for {test_name}")
            except Exception as e:
                print(f"❌ Error debugging {test_name}: {e}")

    def _extract_chords_from_failure(
        self, failure: Dict[str, Any]
    ) -> Optional[List[str]]:
        """Try to extract chord progression from test failure information."""
        longrepr = failure["longrepr"]
        test_name = failure["nodeid"]

        # Look for chord patterns in error messages
        chord_pattern = r'["\'][A-G][#b]?m?\d*(?:/[A-G][#b]?)?["\']'
        chords = re.findall(chord_pattern, longrepr)

        if chords:
            # Clean up quotes
            return [c.strip("'\"") for c in chords]

        # Try extracting from test name
        return TestFailureDebugger.extract_progression_from_test_name(test_name)


# Pytest fixtures for debug integration
@pytest.fixture
def debug_case_factory():
    """Factory fixture for creating debug cases in tests."""

    def _create_case(name: str, chords: List[str], **kwargs) -> DebugCase:
        return DebugCase(name=name, chords=chords, **kwargs)

    return _create_case


@pytest.fixture
def pattern_debugger():
    """Fixture providing a PatternDebugger instance."""
    return PatternDebugger()


@pytest.fixture
def debug_runner():
    """Fixture providing a test failure debugger."""

    def _debug_progression(
        chords: List[str],
        profile: str = "classical",
        pattern_ids: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        case = DebugCase(
            name=f"fixture_debug_{len(chords)}_chords",
            chords=chords,
            profile=profile,
            pattern_ids=pattern_ids or [],
            **kwargs,
        )
        return run_debug_case(case, verbose=False)

    return _debug_progression


# Context manager for debugging test sections
class DebugContext:
    """Context manager for debugging specific test sections."""

    def __init__(self, name: str, chords: List[str], **debug_kwargs):
        self.name = name
        self.chords = chords
        self.debug_kwargs = debug_kwargs
        self.debug_info = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # An exception occurred - run debug analysis
            print(f"\\n🔍 Exception in {self.name}, running debug analysis...")
            case = DebugCase(
                name=f"exception_debug_{self.name}",
                chords=self.chords,
                description=f"Debug case for exception in {self.name}: {exc_val}",
                **self.debug_kwargs,
            )
            self.debug_info = run_debug_case(case, verbose=True)

            # Re-raise the exception
            return False

    def debug_now(self) -> Dict[str, Any]:
        """Run debug analysis immediately (even without exception)."""
        case = DebugCase(
            name=f"manual_debug_{self.name}", chords=self.chords, **self.debug_kwargs
        )
        self.debug_info = run_debug_case(case, verbose=True)
        return self.debug_info


# Example usage functions
def debug_chord_progression(
    chords: List[str],
    profile: str = "classical",
    trace_patterns: Optional[List[str]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Quick debug function for any chord progression.

    Usage:
        debug_chord_progression(["Am", "F", "C", "G"], profile="pop")
    """
    case = DebugCase(
        name=f"quick_debug_{len(chords)}_chords",
        chords=chords,
        profile=profile,
        pattern_ids=trace_patterns or [],
        trace=bool(trace_patterns),
        **kwargs,
    )

    return run_debug_case(case, verbose=True)


if __name__ == "__main__":
    # Example usage
    print("🔍 Test Debug Utils Example")

    # Debug a simple progression
    result = debug_chord_progression(
        ["C", "Am", "F", "G"], profile="pop", trace_patterns=["pop_vi_IV_I_V"]
    )

    print(f"\\n✅ Debug completed. Found {len(result['pattern_names'])} patterns.")
