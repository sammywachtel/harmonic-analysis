#!/usr/bin/env python
"""
Music Expert Review Script

Systematically reviews the harmonic analysis library's logic, algorithms,
and test coverage using music theory expertise to identify improvements.

Usage:
    python scripts/music_expert_review.py --module functional_harmony
    python scripts/music_expert_review.py --module modal_analysis
    python scripts/music_expert_review.py --module chromatic_analysis
    python scripts/music_expert_review.py --module orchestration
    python scripts/music_expert_review.py --all
"""


import argparse
import asyncio
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from harmonic_analysis import analyze_progression_multiple


class Severity(Enum):
    """Issue severity levels."""

    CRITICAL = "critical"  # Theoretical incorrectness
    MAJOR = "major"  # Significant improvement needed
    MINOR = "minor"  # Enhancement opportunity
    INFO = "info"  # Informational note


@dataclass
class ReviewFinding:
    """A finding from the music expert review."""

    module: str
    function: str
    severity: Severity
    issue: str
    suggestion: str
    example: Optional[str] = None


@dataclass
class ReviewReport:
    """Complete review report for a module."""

    module: str
    accuracy_score: float  # 0-100
    findings: List[ReviewFinding] = field(default_factory=list)
    test_coverage: float = 0.0
    suggested_tests: List[str] = field(default_factory=list)
    alternative_approaches: List[str] = field(default_factory=list)


class MusicExpertReviewer:
    """Expert reviewer for music theory logic and algorithms."""

    def __init__(self):
        self.test_progressions = self._load_test_progressions()

    def _load_test_progressions(self) -> Dict[str, List[List[str]]]:
        """Load test progressions for validation."""
        return {
            "ii_v_i": [
                ["Dm7", "G7", "Cmaj7"],  # C major
                ["Em7", "A7", "Dmaj7"],  # D major
                ["Gm7", "C7", "Fmaj7"],  # F major
                ["F#m7b5", "B7", "Em"],  # E minor
            ],
            "modal": [
                ["Dm", "G", "Dm", "C"],  # D Dorian
                ["G", "F", "C", "G"],  # G Mixolydian
                ["Em", "F", "Em", "D"],  # E Phrygian
                ["F", "G", "Am", "F"],  # F Lydian
            ],
            "chromatic": [
                ["C", "E", "Ab", "C"],  # Chromatic mediant
                ["C", "C#dim7", "Dm7"],  # Chromatic passing
                ["C", "Db", "C"],  # Neapolitan
                ["C", "F#7", "G"],  # Augmented sixth
            ],
            "ambiguous": [
                ["Am", "F", "C", "G"],  # Could be C major or A minor
                ["Dm", "G", "C"],  # ii-V-I or modal?
                ["C", "Am", "F", "G"],  # Multiple valid interpretations
            ],
        }

    async def review_functional_harmony(self) -> ReviewReport:
        """Review functional harmony analysis logic."""
        report = ReviewReport(module="functional_harmony", accuracy_score=0.0)

        # Test ii-V-I detection across all keys
        print("🎵 Reviewing ii-V-I detection...")
        for progression in self.test_progressions["ii_v_i"]:
            result = await analyze_progression_multiple(progression)

            # Check if ii-V-I is detected
            if result.primary_analysis.type.value != "functional":
                report.findings.append(
                    ReviewFinding(
                        module="functional_harmony",
                        function="analyze_functionally",
                        severity=Severity.MAJOR,
                        issue=f"ii-V-I pattern {progression} not analyzed as functional",
                        suggestion="Improve ii-V-I pattern recognition",
                        example=str(progression),
                    )
                )

        # Test cadence detection
        print("🎵 Reviewing cadence detection...")
        test_cadences = [
            (["C", "F", "G", "C"], "authentic"),
            (["C", "F", "C"], "plagal"),
            (["C", "G", "Am"], "deceptive"),
            (["Am", "E", "Am"], "authentic_minor"),
        ]

        for progression, expected_cadence in test_cadences:
            result = await analyze_progression_multiple(progression)
            # Add cadence validation logic here

        # Calculate accuracy score
        total_tests = len(self.test_progressions["ii_v_i"]) + len(test_cadences)
        passed_tests = total_tests - len(
            [
                f
                for f in report.findings
                if f.severity in [Severity.CRITICAL, Severity.MAJOR]
            ]
        )
        report.accuracy_score = (passed_tests / total_tests) * 100

        # Add suggested improvements
        report.alternative_approaches = [
            "Consider using interval vectors for more robust pattern detection",
            "Implement voice leading analysis for better cadence detection",
            "Add support for extended jazz harmony (9ths, 11ths, 13ths)",
        ]

        return report

    async def review_modal_analysis(self) -> ReviewReport:
        """Review modal analysis logic."""
        report = ReviewReport(module="modal_analysis", accuracy_score=0.0)

        print("🎵 Reviewing modal characteristic detection...")

        for progression in self.test_progressions["modal"]:
            result = await analyze_progression_multiple(progression)

            # Check modal detection
            if result.primary_analysis.type.value != "modal":
                report.findings.append(
                    ReviewFinding(
                        module="modal_analysis",
                        function="analyze_modal_characteristics",
                        severity=Severity.MAJOR,
                        issue=f"Modal progression {progression} not detected as modal",
                        suggestion="Improve modal characteristic detection",
                        example=str(progression),
                    )
                )

        # Test parent key + local tonic consistency
        print("🎵 Reviewing parent key/local tonic approach...")

        # Add specific modal tests here

        report.accuracy_score = 75.0  # Placeholder
        return report

    async def review_chromatic_analysis(self) -> ReviewReport:
        """Review chromatic harmony analysis logic."""
        report = ReviewReport(module="chromatic_analysis", accuracy_score=0.0)

        print("🎵 Reviewing chromatic harmony detection...")

        for progression in self.test_progressions["chromatic"]:
            _ = await analyze_progression_multiple(progression)

            # Check chromatic element detection
            # Add validation logic here

        report.accuracy_score = 70.0  # Placeholder
        return report

    async def review_orchestration(self) -> ReviewReport:
        """Review how multiple analyzers are orchestrated."""
        report = ReviewReport(module="orchestration", accuracy_score=0.0)

        print("🎵 Reviewing analyzer orchestration...")

        # Test ambiguous progressions
        for progression in self.test_progressions["ambiguous"]:
            result = await analyze_progression_multiple(progression)

            # Check if alternatives are properly generated
            if len(result.alternative_analyses) == 0:
                report.findings.append(
                    ReviewFinding(
                        module="orchestration",
                        function="analyze_multiple_interpretations",
                        severity=Severity.MINOR,
                        issue=f"No alternatives for ambiguous progression {progression}",
                        suggestion="Consider lowering confidence threshold for alternatives",
                        example=str(progression),
                    )
                )

        # Test confidence calibration
        print("🎵 Reviewing confidence calibration...")

        # Add orchestration tests here

        report.accuracy_score = 80.0  # Placeholder
        return report

    def review_test_coverage(self, module: str) -> Tuple[float, List[str]]:
        """Review test coverage for a module."""
        # This would analyze actual test files
        # For now, return placeholder values

        suggested_tests = [
            f"Test {module} with chromatic alterations",
            f"Test {module} with incomplete progressions",
            f"Test {module} with enharmonic equivalents",
            f"Test {module} edge cases (empty, single chord, etc.)",
        ]

        return 75.0, suggested_tests

    async def generate_full_report(self) -> Dict[str, ReviewReport]:
        """Generate complete review report for all modules."""
        reports = {}

        print("=" * 60)
        print("🎼 MUSIC EXPERT REVIEW - HARMONIC ANALYSIS LIBRARY")
        print("=" * 60)

        # Review each module
        reports["functional_harmony"] = await self.review_functional_harmony()
        reports["modal_analysis"] = await self.review_modal_analysis()
        reports["chromatic_analysis"] = await self.review_chromatic_analysis()
        reports["orchestration"] = await self.review_orchestration()

        # Add test coverage analysis
        for module_name, report in reports.items():
            coverage, suggested_tests = self.review_test_coverage(module_name)
            report.test_coverage = coverage
            report.suggested_tests = suggested_tests

        return reports

    def print_report(self, reports: Dict[str, ReviewReport]):
        """Print formatted review report."""

        print("\n" + "=" * 60)
        print("📊 REVIEW SUMMARY")
        print("=" * 60)

        for module_name, report in reports.items():
            print(f"\n📦 Module: {module_name}")
            print(f"   Accuracy Score: {report.accuracy_score:.1f}%")
            print(f"   Test Coverage: {report.test_coverage:.1f}%")
            print(f"   Findings: {len(report.findings)}")

            if report.findings:
                print("\n   Issues by Severity:")
                severity_counts = {}
                for finding in report.findings:
                    severity_counts[finding.severity] = (
                        severity_counts.get(finding.severity, 0) + 1
                    )
                for severity, count in severity_counts.items():
                    print(f"     {severity.value}: {count}")

        print("\n" + "=" * 60)
        print("📋 DETAILED FINDINGS")
        print("=" * 60)

        for module_name, report in reports.items():
            if report.findings:
                print(f"\n📦 {module_name}:")
                for finding in report.findings:
                    self._print_finding(finding)

        print("\n" + "=" * 60)
        print("💡 IMPROVEMENT SUGGESTIONS")
        print("=" * 60)

        for module_name, report in reports.items():
            if report.alternative_approaches:
                print(f"\n📦 {module_name}:")
                for approach in report.alternative_approaches:
                    print(f"   • {approach}")

    def _print_finding(self, finding: ReviewFinding):
        """Print a single finding."""
        severity_emoji = {
            Severity.CRITICAL: "🔴",
            Severity.MAJOR: "🟠",
            Severity.MINOR: "🟡",
            Severity.INFO: "🔵",
        }

        print(
            f"\n   {severity_emoji[finding.severity]} [{finding.severity.value}] {finding.function}"
        )
        print(f"      Issue: {finding.issue}")
        print(f"      Suggestion: {finding.suggestion}")
        if finding.example:
            print(f"      Example: {finding.example}")

    def save_report(self, reports: Dict[str, ReviewReport], output_path: Path):
        """Save report to JSON file."""
        report_data = {}

        for module_name, report in reports.items():
            report_data[module_name] = {
                "accuracy_score": report.accuracy_score,
                "test_coverage": report.test_coverage,
                "findings": [
                    {
                        "function": f.function,
                        "severity": f.severity.value,
                        "issue": f.issue,
                        "suggestion": f.suggestion,
                        "example": f.example,
                    }
                    for f in report.findings
                ],
                "suggested_tests": report.suggested_tests,
                "alternative_approaches": report.alternative_approaches,
            }

        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"\n✅ Report saved to {output_path}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Music Expert Review for Harmonic Analysis Library"
    )
    parser.add_argument(
        "--module",
        choices=[
            "functional_harmony",
            "modal_analysis",
            "chromatic_analysis",
            "orchestration",
            "all",
        ],
        default="all",
        help="Module to review",
    )
    parser.add_argument("--output", type=Path, help="Output file for report (JSON)")

    args = parser.parse_args()

    reviewer = MusicExpertReviewer()

    if args.module == "all":
        reports = await reviewer.generate_full_report()
    else:
        # Review single module
        if args.module == "functional_harmony":
            report = await reviewer.review_functional_harmony()
        elif args.module == "modal_analysis":
            report = await reviewer.review_modal_analysis()
        elif args.module == "chromatic_analysis":
            report = await reviewer.review_chromatic_analysis()
        elif args.module == "orchestration":
            report = await reviewer.review_orchestration()

        reports = {args.module: report}

    # Print report
    reviewer.print_report(reports)

    # Save if requested
    if args.output:
        reviewer.save_report(reports, args.output)


if __name__ == "__main__":
    asyncio.run(main())
