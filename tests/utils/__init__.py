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
    # Unified debug system
    "debug_on_failure",
    "debug_always",
    "UnifiedDebugger",
    "DebugConfig",
    "get_unified_debugger",
    "debug_progression",
    "debug_test_failure",
]
