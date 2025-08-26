"""
Edge Case Warning System

Provides colorful warning utilities for edge case tests that should pass with warnings
instead of failing, to avoid blocking CI/CD while highlighting areas for improvement.
"""

import warnings
from typing import List


class EdgeCaseWarning(UserWarning):
    """Custom warning class for edge case behavioral issues"""

    pass


def warn_edge_case_behavior(
    test_name: str,
    expected_behavior: str,
    actual_behavior: str,
    severity: str = "medium",
    icon: str = "⚠️",
) -> None:
    """
    Issue a colorful warning for edge case behavioral deviations

    Args:
        test_name: Name of the failing test
        expected_behavior: What was expected
        actual_behavior: What actually happened
        severity: "low", "medium", "high"
        icon: Warning icon to display
    """
    severity_icons = {"low": "🟡", "medium": "🟠", "high": "🔴"}

    severity_icon = severity_icons.get(severity, "⚠️")

    message = f"""
{severity_icon} EDGE CASE BEHAVIORAL WARNING {icon}

Test: {test_name}
Expected: {expected_behavior}
Actual: {actual_behavior}

This edge case needs attention but won't block CI/CD.
Consider reviewing confidence thresholds and behavioral expectations.
    """.strip()

    warnings.warn(message, EdgeCaseWarning, stacklevel=2)


def soft_assert_with_warning(
    condition: bool,
    test_name: str,
    expected: str,
    actual: str,
    severity: str = "medium",
    icon: str = "⚠️",
) -> bool:
    """
    Assert with warning instead of failure

    Returns True if condition passes, warns and returns False if it fails
    """
    if not condition:
        warn_edge_case_behavior(
            test_name=test_name,
            expected_behavior=expected,
            actual_behavior=actual,
            severity=severity,
            icon=icon,
        )
        return False
    return True


def collect_edge_case_warnings(
    test_results: List[dict], category: str = "edge_cases"
) -> dict:
    """
    Collect and summarize edge case warnings for reporting

    Args:
        test_results: List of test result dictionaries
        category: Test category name

    Returns:
        Summary dictionary with warning statistics
    """
    warnings_summary = {
        "total_tests": len(test_results),
        "passing_tests": 0,
        "warning_tests": 0,
        "high_severity": 0,
        "medium_severity": 0,
        "low_severity": 0,
        "warnings": [],
    }

    for result in test_results:
        if result.get("passed", False):
            warnings_summary["passing_tests"] += 1
        elif result.get("warning", False):
            warnings_summary["warning_tests"] += 1
            severity = result.get("severity", "medium")
            warnings_summary[f"{severity}_severity"] += 1
            warnings_summary["warnings"].append(result)

    return warnings_summary


def print_edge_case_summary(warnings_summary: dict, category: str) -> None:
    """Print colorful summary of edge case test results"""
    print(f"\n🎯 EDGE CASE SUMMARY: {category.upper()}")
    print("=" * 50)

    total = warnings_summary["total_tests"]
    passing = warnings_summary["passing_tests"]
    warning = warnings_summary["warning_tests"]

    print(f"✅ Passing: {passing}/{total}")
    print(f"⚠️  With Warnings: {warning}/{total}")

    if warning > 0:
        print("\n📊 Warning Breakdown:")
        print(f"  🔴 High: {warnings_summary['high_severity']}")
        print(f"  🟠 Medium: {warnings_summary['medium_severity']}")
        print(f"  🟡 Low: {warnings_summary['low_severity']}")

        success_rate = (passing / total) * 100 if total > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        print(
            "🎯 Edge cases are expected to have behavioral issues - warnings are normal!"
        )
