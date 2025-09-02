#!/usr/bin/env python3
"""
Export comprehensive test failures with detailed expected vs actual results.
Creates both human-readable and machine-readable output for analysis.
"""

import asyncio
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from harmonic_analysis import analyze_progression_multiple
from harmonic_analysis.services.multiple_interpretation_service import (
    InterpretationType,
)
from harmonic_analysis.analysis_types import AnalysisOptions


class TestFailureExporter:
    def __init__(self):
        self.failures = []
        self.test_data = None

    def load_test_data(self) -> List[Dict]:
        """Load comprehensive test data"""
        test_file = (
            Path(__file__).parent.parent
            / "tests"
            / "generated"
            / "comprehensive-multi-layer-tests.json"
        )

        if not test_file.exists():
            print("❌ Test data file not found. Generating fresh test data...")
            import subprocess

            subprocess.run(
                [
                    sys.executable,
                    str(
                        Path(__file__).parent
                        / "generate_comprehensive_multi_layer_tests.py"
                    ),
                ]
            )

        with open(test_file, "r") as f:
            data = json.load(f)
            return data["test_cases"]

    async def analyze_test_case(self, test_case: Dict) -> Dict:
        """Run analysis on a single test case and capture results"""
        chords = test_case["chords"]
        test_id = test_case["id"]

        # Create options with parent key if provided
        options = AnalysisOptions()
        if "parent_key" in test_case and test_case["parent_key"]:
            options.parent_key = test_case["parent_key"]

        try:
            result = await analyze_progression_multiple(chords, options)

            return {
                "test_id": test_id,
                "chords": chords,
                "category": test_case.get("category", "unknown"),
                "description": test_case.get("description", ""),
                "parent_key": test_case.get("parent_key"),
                "result": {
                    "primary_type": str(result.primary_analysis.type),
                    "primary_confidence": result.primary_analysis.confidence,
                    "primary_analysis": result.primary_analysis.analysis,
                    "primary_key": result.primary_analysis.key_signature,
                    "primary_roman": result.primary_analysis.roman_numerals,
                    "alternatives": [
                        {
                            "type": str(alt.type),
                            "confidence": alt.confidence,
                            "analysis": alt.analysis,
                            "key": alt.key_signature,
                            "roman": alt.roman_numerals,
                        }
                        for alt in result.alternative_analyses
                    ],
                },
                "expected": {
                    "functional": test_case.get("expected_functional", {}),
                    "modal": test_case.get("expected_modal", {}),
                    "chromatic": test_case.get("expected_chromatic", {}),
                },
            }
        except Exception as e:
            return {
                "test_id": test_id,
                "chords": chords,
                "category": test_case.get("category", "unknown"),
                "error": str(e),
                "expected": {
                    "functional": test_case.get("expected_functional", {}),
                    "modal": test_case.get("expected_modal", {}),
                    "chromatic": test_case.get("expected_chromatic", {}),
                },
            }

    def validate_test_case(self, analysis_result: Dict) -> Dict:
        """Validate a test case analysis and return failure details if any"""
        test_id = analysis_result["test_id"]
        expected = analysis_result["expected"]
        actual = analysis_result.get("result")

        if not actual:
            return {
                "test_id": test_id,
                "failure_type": "ANALYSIS_ERROR",
                "error": analysis_result.get("error", "Unknown analysis error"),
                "chords": analysis_result["chords"],
                "category": analysis_result["category"],
            }

        failures = []

        # Check functional expectations
        if expected.get("functional", {}).get("detected", False):
            func_expected = expected["functional"]

            # Check if functional analysis is primary or alternative
            is_functional_primary = actual["primary_type"] == str(
                InterpretationType.FUNCTIONAL
            )
            functional_result = None

            if is_functional_primary:
                functional_result = {
                    "confidence": actual["primary_confidence"],
                    "key_center": actual["primary_key"],
                    "roman_numerals": actual["primary_roman"],
                }
            else:
                # Look for functional in alternatives
                for alt in actual["alternatives"]:
                    if alt["type"] == str(InterpretationType.FUNCTIONAL):
                        functional_result = {
                            "confidence": alt["confidence"],
                            "key_center": alt["key"],
                            "roman_numerals": alt["roman"],
                        }
                        break

            if functional_result:
                # Check confidence
                expected_conf = func_expected.get("confidence", 0.5)
                actual_conf = functional_result["confidence"]
                if abs(expected_conf - actual_conf) > 0.15:
                    failures.append(
                        {
                            "type": "FUNCTIONAL_CONFIDENCE",
                            "expected": expected_conf,
                            "actual": actual_conf,
                            "diff": abs(expected_conf - actual_conf),
                        }
                    )

                # Check key center
                expected_key = func_expected.get("key_center")
                actual_key = functional_result["key_center"]
                if expected_key and expected_key != actual_key:
                    failures.append(
                        {
                            "type": "FUNCTIONAL_KEY",
                            "expected": expected_key,
                            "actual": actual_key,
                        }
                    )

                # Check Roman numerals
                expected_roman = func_expected.get("roman_numerals", [])
                actual_roman = functional_result["roman_numerals"]
                if expected_roman and expected_roman != actual_roman:
                    failures.append(
                        {
                            "type": "FUNCTIONAL_ROMAN",
                            "expected": expected_roman,
                            "actual": actual_roman,
                        }
                    )

        # Check modal expectations
        if expected.get("modal", {}).get("detected", False):
            modal_expected = expected["modal"]

            # Check if modal analysis is primary or alternative
            is_modal_primary = actual["primary_type"] == str(InterpretationType.MODAL)
            modal_result = None

            if is_modal_primary:
                modal_result = {
                    "confidence": actual["primary_confidence"],
                    "mode": actual["primary_analysis"],  # Mode info is in analysis text
                    "key": actual["primary_key"],
                }
            else:
                # Look for modal in alternatives
                for alt in actual["alternatives"]:
                    if alt["type"] == str(InterpretationType.MODAL):
                        modal_result = {
                            "confidence": alt["confidence"],
                            "mode": alt["analysis"],
                            "key": alt["key"],
                        }
                        break

            if modal_result:
                # Check confidence
                expected_conf = modal_expected.get("confidence", 0.6)
                actual_conf = modal_result["confidence"]
                if abs(expected_conf - actual_conf) > 0.15:
                    failures.append(
                        {
                            "type": "MODAL_CONFIDENCE",
                            "expected": expected_conf,
                            "actual": actual_conf,
                            "diff": abs(expected_conf - actual_conf),
                        }
                    )

                # Check mode name
                expected_mode = modal_expected.get("mode_name")
                if expected_mode and expected_mode not in modal_result["mode"]:
                    failures.append(
                        {
                            "type": "MODAL_MODE",
                            "expected": expected_mode,
                            "actual": modal_result["mode"],
                        }
                    )

        # Check chromatic expectations
        if expected.get("chromatic", {}).get("detected", False):
            chromatic_expected = expected["chromatic"]

            # Look for chromatic analysis (usually alternative)
            is_chromatic_primary = actual["primary_type"] == str(
                InterpretationType.CHROMATIC
            )
            chromatic_result = None

            if is_chromatic_primary:
                chromatic_result = {"confidence": actual["primary_confidence"]}
            else:
                for alt in actual["alternatives"]:
                    if alt["type"] == str(InterpretationType.CHROMATIC):
                        chromatic_result = {"confidence": alt["confidence"]}
                        break

            if chromatic_result:
                expected_conf = chromatic_expected.get("confidence", 0.5)
                actual_conf = chromatic_result["confidence"]
                if abs(expected_conf - actual_conf) > 0.15:
                    failures.append(
                        {
                            "type": "CHROMATIC_CONFIDENCE",
                            "expected": expected_conf,
                            "actual": actual_conf,
                            "diff": abs(expected_conf - actual_conf),
                        }
                    )

        if failures:
            return {
                "test_id": test_id,
                "failure_type": "VALIDATION_FAILURE",
                "chords": analysis_result["chords"],
                "category": analysis_result["category"],
                "description": analysis_result["description"],
                "failures": failures,
                "full_expected": expected,
                "full_actual": actual,
            }

        return None

    async def run_comprehensive_analysis(self) -> None:
        """Run comprehensive analysis on all test cases"""
        print("🔍 Loading test data...")
        test_cases = self.load_test_data()

        print(f"📊 Analyzing {len(test_cases)} test cases...")

        all_results = []
        failed_results = []

        # Process in batches to avoid overwhelming the system
        batch_size = 50
        for i in range(0, len(test_cases), batch_size):
            batch = test_cases[i : i + batch_size]
            print(
                f"  Processing batch {i // batch_size + 1}/{(len(test_cases) + batch_size - 1) // batch_size}"
            )

            # Analyze batch
            batch_results = await asyncio.gather(
                *[self.analyze_test_case(test_case) for test_case in batch]
            )

            # Validate results
            for result in batch_results:
                all_results.append(result)
                failure = self.validate_test_case(result)
                if failure:
                    failed_results.append(failure)

        print("\n📊 ANALYSIS COMPLETE:")
        print(f"  Total tests: {len(all_results)}")
        print(f"  Failed tests: {len(failed_results)}")
        print(
            f"  Success rate: {(len(all_results) - len(failed_results)) / len(all_results) * 100:.1f}%"
        )

        # Export results
        await self.export_results(all_results, failed_results)

    async def export_results(
        self, all_results: List[Dict], failed_results: List[Dict]
    ) -> None:
        """Export results in multiple formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Export detailed failures as JSON
        failures_json = (
            Path(__file__).parent.parent / f"test_failures_detailed_{timestamp}.json"
        )
        with open(failures_json, "w") as f:
            json.dump(
                {
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "total_tests": len(all_results),
                        "failed_tests": len(failed_results),
                        "success_rate": (len(all_results) - len(failed_results))
                        / len(all_results)
                        * 100,
                    },
                    "failures": failed_results,
                },
                f,
                indent=2,
                default=str,
            )

        # Export summary as CSV
        failures_csv = (
            Path(__file__).parent.parent / f"test_failures_summary_{timestamp}.csv"
        )
        with open(failures_csv, "w", newline="") as f:
            if failed_results:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "test_id",
                        "category",
                        "chords",
                        "failure_type",
                        "specific_failures",
                        "description",
                    ],
                )
                writer.writeheader()

                for failure in failed_results:
                    writer.writerow(
                        {
                            "test_id": failure["test_id"],
                            "category": failure["category"],
                            "chords": " -> ".join(failure["chords"]),
                            "failure_type": failure["failure_type"],
                            "specific_failures": "; ".join(
                                [
                                    f"{f['type']}: expected={f.get('expected', 'N/A')} actual={f.get('actual', 'N/A')}"
                                    for f in failure.get("failures", [])
                                ]
                            ),
                            "description": failure.get("description", ""),
                        }
                    )

        # Export human-readable summary
        summary_txt = (
            Path(__file__).parent.parent / f"test_failures_readable_{timestamp}.txt"
        )
        with open(summary_txt, "w") as f:
            f.write("COMPREHENSIVE TEST FAILURE ANALYSIS\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Total Tests: {len(all_results)}\n")
            f.write(f"Failed Tests: {len(failed_results)}\n")
            f.write(
                f"Success Rate: {(len(all_results) - len(failed_results)) / len(all_results) * 100:.1f}%\n\n"
            )

            # Group failures by category
            by_category = {}
            for failure in failed_results:
                category = failure["category"]
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(failure)

            for category, failures in by_category.items():
                f.write(f"\n{category.upper()} FAILURES ({len(failures)} cases)\n")
                f.write("-" * 40 + "\n")

                for failure in failures[:10]:  # Show first 10 of each category
                    f.write(f"\nTest ID: {failure['test_id']}\n")
                    f.write(f"Chords: {' -> '.join(failure['chords'])}\n")
                    f.write(f"Description: {failure.get('description', 'N/A')}\n")

                    if "failures" in failure:
                        for specific in failure["failures"]:
                            f.write(
                                f"  - {specific['type']}: Expected={specific.get('expected', 'N/A')}, Actual={specific.get('actual', 'N/A')}\n"
                            )

                    f.write("\n")

                if len(failures) > 10:
                    f.write(f"... and {len(failures) - 10} more {category} failures\n")

        print("\n📁 RESULTS EXPORTED:")
        print(f"  📄 Detailed JSON: {failures_json}")
        print(f"  📊 Summary CSV: {failures_csv}")
        print(f"  📖 Human-readable: {summary_txt}")


async def main():
    """Main execution function"""
    exporter = TestFailureExporter()
    await exporter.run_comprehensive_analysis()


if __name__ == "__main__":
    asyncio.run(main())
