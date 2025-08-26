#!/usr/bin/env python3
"""
Confidence Calibration Analysis Tool

This script analyzes confidence scoring patterns to help calibrate the music theory
analysis system. It compares expected vs. actual confidence scores from test cases
to identify systematic patterns and calibration needs.

Key Features:
- Analyzes functional harmony confidence patterns
- Analyzes modal characteristic confidence patterns
- Uses proper parent_key context from test cases
- Provides detailed confidence difference reporting

Usage:
    python scripts/confidence_calibration_analysis.py

This tool was essential for identifying and fixing the parent key parsing bug
where "C major" was incorrectly parsed as "C minor", leading to a major improvement
in functional harmony analysis from 0% to 72% success rate.

Author: Claude Code
Date: August 2024
Purpose: Production confidence calibration and debugging
"""

import asyncio
import json
import os
import sys

from harmonic_analysis.multiple_interpretation_service import (
    analyze_progression_multiple,
)
from harmonic_analysis.types import AnalysisOptions

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


async def analyze_test_cases():
    with open("tests/generated/comprehensive-multi-layer-tests.json", "r") as f:
        data = json.load(f)

    test_cases = data["test_cases"]
    functional_cases = [
        tc for tc in test_cases if tc["category"] == "functional_clear"
    ][:10]
    modal_cases = [tc for tc in test_cases if tc["category"] == "modal_characteristic"][
        :5
    ]

    print("CONFIDENCE ANALYSIS:")
    print("=" * 50)
    print("\nFUNCTIONAL HARMONY CASES:")
    print("-" * 30)

    for case in functional_cases:
        chords = case["chords"]
        expected_conf = case["expected_functional"]["confidence"]
        parent_key = case.get("parent_key")

        # Use parent_key context if available
        options = AnalysisOptions(parent_key=parent_key) if parent_key else None
        result = await analyze_progression_multiple(chords, options)
        actual_conf = result.primary_analysis.confidence

        print(f"Chords: {chords}")
        print(f"Parent Key: {parent_key}")
        print(f"Expected: {expected_conf:.3f}")
        print(f"Actual:   {actual_conf:.3f}")
        print(f"Diff:     {abs(expected_conf - actual_conf):.3f}")
        print(f"Type:     {result.primary_analysis.type}")
        print(f"Evidence: {len(result.primary_analysis.evidence)} pieces")
        print("-" * 15)

    print("\nMODAL CHARACTERISTIC CASES:")
    print("-" * 30)

    for case in modal_cases:
        chords = case["chords"]
        expected_conf = case["expected_modal"]["confidence"]
        parent_key = case.get("parent_key")

        # Use parent_key context if available
        options = AnalysisOptions(parent_key=parent_key) if parent_key else None
        result = await analyze_progression_multiple(chords, options)
        actual_conf = result.primary_analysis.confidence

        print(f"Chords: {chords}")
        print(f"Parent Key: {parent_key}")
        print(f"Expected: {expected_conf:.3f}")
        print(f"Actual:   {actual_conf:.3f}")
        print(f"Diff:     {abs(expected_conf - actual_conf):.3f}")
        print(f"Type:     {result.primary_analysis.type}")
        print(f"Evidence: {len(result.primary_analysis.evidence)} pieces")
        print("-" * 15)


if __name__ == "__main__":
    asyncio.run(analyze_test_cases())
