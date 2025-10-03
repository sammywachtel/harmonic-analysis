#!/usr/bin/env python3
"""
Smoke tests for Iteration 15 - Scale/Melody Evidence Enhancement

Tests the CLI, API, and core analysis functionality with the new scale/melody summaries.
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List

# Add src to path before imports
REPO_ROOT = Path(__file__).parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from harmonic_analysis.services.unified_pattern_service import (  # noqa: E402
    UnifiedPatternService,
)


class SmokeTestRunner:
    """Comprehensive smoke test suite for iteration 15."""

    def __init__(self):
        self.results: List[Dict] = []
        self.service = UnifiedPatternService()

    def log_result(
        self, test_name: str, passed: bool, details: str = "", error: str = ""
    ):
        """Log test result."""
        result = {
            "test": test_name,
            "passed": passed,
            "details": details,
            "error": error,
            "timestamp": time.time(),
        }
        self.results.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        if error:
            print(f"    Error: {error}")

    def test_demo_cli_basic(self) -> bool:
        """Test basic CLI functionality."""
        try:
            cmd = [
                sys.executable,
                "demo/full_library_demo.py",
                "--chords",
                "C Am F G",
                "--key",
                "C major",
                "--profile",
                "classical",
            ]

            result = subprocess.run(
                cmd,
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
                env={"PYTHONPATH": str(SRC_ROOT)},
            )

            if result.returncode != 0:
                self.log_result(
                    "CLI Basic",
                    False,
                    error=f"Exit code {result.returncode}: {result.stderr}",
                )
                return False

            output = result.stdout
            # Check for expected output structure
            checks = [
                "Primary Interpretation" in output,
                "Type" in output,
                "Confidence" in output,
                "Roman Numerals" in output,
            ]

            if all(checks):
                self.log_result(
                    "CLI Basic", True, "All expected output sections present"
                )
                return True
            else:
                self.log_result(
                    "CLI Basic", False, f"Missing output sections: {checks}"
                )
                return False

        except Exception as e:
            self.log_result("CLI Basic", False, error=str(e))
            return False

    def test_demo_cli_with_melody(self) -> bool:
        """Test CLI with melody analysis."""
        try:
            cmd = [
                sys.executable,
                "demo/full_library_demo.py",
                "--chords",
                "C Am F G",
                "--melody",
                "C4 E4 F4 G4",
                "--key",
                "C major",
                "--profile",
                "classical",
            ]

            result = subprocess.run(
                cmd,
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
                env={"PYTHONPATH": str(SRC_ROOT)},
            )

            if result.returncode != 0:
                self.log_result(
                    "CLI Melody",
                    False,
                    error=f"Exit code {result.returncode}: {result.stderr}",
                )
                return False

            output = result.stdout
            # Check for melody-related output
            has_melody_info = (
                "melodic line" in output.lower()
                or "melody analysis" in output.lower()
                or "melody" in output.lower()
            )

            if has_melody_info:
                self.log_result(
                    "CLI Melody", True, "Melody information present in output"
                )
                return True
            else:
                self.log_result("CLI Melody", False, "No melody information in output")
                return False

        except Exception as e:
            self.log_result("CLI Melody", False, error=str(e))
            return False

    def test_demo_cli_with_scale(self) -> bool:
        """Test CLI with scale analysis."""
        try:
            cmd = [
                sys.executable,
                "demo/full_library_demo.py",
                "--scale",
                "C D Eb F G A Bb",
                "--key",
                "C dorian",
                "--profile",
                "classical",
            ]

            result = subprocess.run(
                cmd,
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
                env={"PYTHONPATH": str(SRC_ROOT)},
            )

            if result.returncode != 0:
                self.log_result(
                    "CLI Scale",
                    False,
                    error=f"Exit code {result.returncode}: {result.stderr}",
                )
                return False

            output = result.stdout
            # Check for scale-related output
            has_scale_info = "scale" in output.lower() and (
                "7 notes" in output or "analyzed scale" in output.lower()
            )

            if has_scale_info:
                self.log_result(
                    "CLI Scale", True, "Scale information present in output"
                )
                return True
            else:
                self.log_result("CLI Scale", False, "No scale information in output")
                return False

        except Exception as e:
            self.log_result("CLI Scale", False, error=str(e))
            return False

    async def test_unified_service_scale_summary(self) -> bool:
        """Test UnifiedPatternService generates scale summaries."""
        try:
            # Test scale analysis
            result = await self.service.analyze_with_patterns_async(
                notes=["C", "D", "Eb", "F", "G", "A", "Bb"], key_hint="C dorian"
            )

            if not result.primary:
                self.log_result(
                    "Service Scale Summary", False, "No primary analysis returned"
                )
                return False

            # Check if scale_summary is populated
            has_scale_summary = (
                hasattr(result.primary, "scale_summary")
                and result.primary.scale_summary is not None
            )

            if has_scale_summary:
                scale_summary = result.primary.scale_summary
                details = (
                    f"Mode: {scale_summary.detected_mode}, "
                    f"Notes: {len(scale_summary.notes or [])}"
                )
                self.log_result("Service Scale Summary", True, details)
                return True
            else:
                self.log_result(
                    "Service Scale Summary", False, "scale_summary is None or missing"
                )
                return False

        except Exception as e:
            self.log_result("Service Scale Summary", False, error=str(e))
            return False

    async def test_unified_service_melody_summary(self) -> bool:
        """Test UnifiedPatternService generates melody summaries."""
        try:
            # Test melody analysis
            result = await self.service.analyze_with_patterns_async(
                melody=["C4", "E4", "G4", "C5"], key_hint="C major"
            )

            if not result.primary:
                self.log_result(
                    "Service Melody Summary", False, "No primary analysis returned"
                )
                return False

            # Check if melody_summary is populated
            has_melody_summary = (
                hasattr(result.primary, "melody_summary")
                and result.primary.melody_summary is not None
            )

            if has_melody_summary:
                melody_summary = result.primary.melody_summary
                details = (
                    f"Contour: {melody_summary.contour}, "
                    f"Range: {melody_summary.range_semitones}"
                )
                self.log_result("Service Melody Summary", True, details)
                return True
            else:
                self.log_result(
                    "Service Melody Summary", False, "melody_summary is None or missing"
                )
                return False

        except Exception as e:
            self.log_result("Service Melody Summary", False, error=str(e))
            return False

    async def test_comprehensive_analysis(self) -> bool:
        """Test comprehensive analysis with chord analysis and reasoning."""
        try:
            # Test chord analysis with enhanced reasoning
            result = await self.service.analyze_with_patterns_async(
                chords=["C", "Am", "F", "G"], key_hint="C major", profile="classical"
            )

            if not result.primary:
                self.log_result(
                    "Comprehensive Analysis", False, "No primary analysis returned"
                )
                return False

            # Check various aspects
            checks = {
                "has_confidence": result.primary.confidence > 0,
                "has_reasoning": bool(result.primary.reasoning),
                "has_roman_numerals": bool(result.primary.roman_numerals),
                "analysis_type_set": result.primary.type is not None,
            }

            passed_checks = sum(checks.values())
            total_checks = len(checks)

            if passed_checks >= 3:  # At least 3 out of 4 checks should pass
                details = f"Passed {passed_checks}/{total_checks} checks: {checks}"
                self.log_result("Comprehensive Analysis", True, details)
                return True
            else:
                details = f"Only passed {passed_checks}/{total_checks} checks: {checks}"
                self.log_result("Comprehensive Analysis", False, details)
                return False

        except Exception as e:
            self.log_result("Comprehensive Analysis", False, error=str(e))
            return False

    def test_gradio_server_startup(self) -> bool:
        """Test that Gradio demo can start up."""
        try:
            # Prepare environment with proper PATH
            env = os.environ.copy()
            env["PYTHONPATH"] = str(SRC_ROOT)

            # Start Gradio server in background
            process = subprocess.Popen(
                [sys.executable, "demo/full_library_demo.py", "--gradio"],
                cwd=REPO_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )

            # Wait for startup (up to 10 seconds)
            time.sleep(5)

            # Check if process is running
            if process.poll() is None:
                # Process is still running, try to terminate gracefully
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

                self.log_result("Gradio Startup", True, "Server started successfully")
                return True
            else:
                # Process exited, check for errors
                _, stderr = process.communicate()
                self.log_result(
                    "Gradio Startup", False, error=f"Process exited: {stderr.decode()}"
                )
                return False

        except Exception as e:
            self.log_result("Gradio Startup", False, error=str(e))
            return False

    async def run_all_tests(self) -> Dict:
        """Run all smoke tests and return summary."""
        print("🔥 Running Iteration 15 Smoke Tests...")
        print("=" * 50)

        # CLI Tests
        print("\n📱 CLI Tests")
        self.test_demo_cli_basic()
        self.test_demo_cli_with_melody()
        self.test_demo_cli_with_scale()

        # Service Tests
        print("\n🔧 Service Tests")
        await self.test_unified_service_scale_summary()
        await self.test_unified_service_melody_summary()
        await self.test_comprehensive_analysis()

        # Server Tests
        print("\n🌐 Server Tests")
        self.test_gradio_server_startup()

        # Summary
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["passed"])

        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("🎉 All smoke tests passed!")
        else:
            print("⚠️  Some tests failed - see details above")

        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": total_tests - passed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "results": self.results,
        }


async def main():
    """Main entry point."""
    runner = SmokeTestRunner()
    summary = await runner.run_all_tests()

    # Save results to file
    output_file = REPO_ROOT / ".local_docs" / "smoke_test_iteration_15.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n💾 Results saved to {output_file}")

    # Exit with error code if tests failed
    if summary["success_rate"] < 1.0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
