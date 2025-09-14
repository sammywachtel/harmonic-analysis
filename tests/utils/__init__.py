"""
Test utilities package.

Provides debugging, testing, and development utilities for the
harmonic analysis library.
"""

from .debug_helpers import (
    COMMON_DEBUG_CASES,
    DebugCase,
    PatternDebugger,
    create_test_from_case,
    get_case_by_name,
    list_available_cases,
    run_debug_case,
)
from .test_debug_utils import (
    DebugContext,
    DebugTestRunner,
    TestFailureDebugger,
    debug_chord_progression,
    debug_failing_test,
)
from .unified_debug import (
    DebugConfig,
    UnifiedDebugger,
    debug_always,
    debug_on_failure,
    debug_progression,
    debug_test_failure,
    get_unified_debugger,
)

__all__ = [
    # Debug helpers
    "DebugCase",
    "PatternDebugger",
    "run_debug_case",
    "create_test_from_case",
    "COMMON_DEBUG_CASES",
    "get_case_by_name",
    "list_available_cases",
    # Test debug utils
    "TestFailureDebugger",
    "DebugTestRunner",
    "DebugContext",
    "debug_failing_test",
    "debug_chord_progression",
    # Unified debug system
    "debug_on_failure",
    "debug_always",
    "UnifiedDebugger",
    "DebugConfig",
    "get_unified_debugger",
    "debug_progression",
    "debug_test_failure",
]
