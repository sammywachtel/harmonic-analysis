#!/usr/bin/env python3
"""
🎯 Code Quality Check and Automation Script

Provides comprehensive code quality checks, auto-fixes, and reminders for
development best practices. Integrates with IDE and pre-commit workflows.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class CodeQualityChecker:
    """Comprehensive code quality checker with auto-fixes and reporting"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_paths = ["src/", "tests/", "scripts/"]

    def run_command(self, cmd: List[str], description: str) -> Tuple[bool, str]:
        """Run a command and return success status and output"""
        try:
            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True, timeout=120
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, f"Command timed out: {' '.join(cmd)}"
        except Exception as e:
            return False, f"Command failed: {e}"

    def print_header(self, title: str, icon: str = "🎯"):
        """Print a colorful section header"""
        print(f"\n{icon} {title}")
        print("=" * (len(title) + 4))

    def print_result(self, success: bool, message: str, details: str = ""):
        """Print a colorful result with optional details"""
        icon = "✅" if success else "❌"
        print(f"{icon} {message}")
        if details and not success:
            print(f"   Details: {details}")

    def run_black_format(self, fix: bool = False) -> bool:
        """Run Black code formatting"""
        self.print_header("Black Code Formatting", "⚫")

        cmd = ["black"] + self.src_paths
        if not fix:
            cmd.append("--check")

        success, output = self.run_command(cmd, "Black formatting")

        if fix:
            self.print_result(
                success, "Code formatted with Black", output if not success else ""
            )
        else:
            self.print_result(
                success, "Black formatting check", output if not success else ""
            )

        return success

    def run_isort_imports(self, fix: bool = False) -> bool:
        """Run isort import sorting"""
        self.print_header("Import Sorting with isort", "🔤")

        cmd = ["isort"] + self.src_paths
        if not fix:
            cmd.append("--check-only")

        success, output = self.run_command(cmd, "Import sorting")

        if fix:
            self.print_result(
                success, "Imports sorted with isort", output if not success else ""
            )
        else:
            self.print_result(
                success, "Import sorting check", output if not success else ""
            )

        return success

    def run_flake8_linting(self) -> bool:
        """Run flake8 linting"""
        self.print_header("Linting with flake8", "🔍")

        cmd = ["flake8"] + self.src_paths
        success, output = self.run_command(cmd, "Flake8 linting")

        self.print_result(
            success, "Flake8 linting check", output if not success else ""
        )
        return success

    def run_mypy_typing(self) -> bool:
        """Run MyPy type checking"""
        self.print_header("Type Checking with MyPy", "🎯")

        cmd = ["mypy", "src/", "--ignore-missing-imports"]
        success, output = self.run_command(cmd, "MyPy type checking")

        self.print_result(success, "MyPy type checking", output if not success else "")
        return success

    def run_security_scan(self) -> bool:
        """Run Bandit security scanning"""
        self.print_header("Security Scanning with Bandit", "🔒")

        cmd = ["bandit", "-r", "src/", "-f", "txt"]  # Fixed: "text" -> "txt"
        success, output = self.run_command(cmd, "Security scanning")

        # Bandit returns non-zero for findings, so we check output content
        has_issues = "No issues identified" not in output

        self.print_result(not has_issues, "Security scan", output if has_issues else "")
        return not has_issues

    def run_tests(self, quick: bool = False) -> bool:
        """Run test suite with discovery-based approach"""
        self.print_header("Running Tests", "🧪")

        if quick:
            # Quick mode: Run functional and unit tests (skip slow integration tests)
            cmd = ["pytest", "tests/", "-m", "unit or functional", "-v", "--tb=short"]
            description = "Quick functionality tests (unit + functional)"
        else:
            # Full mode: Run all tests
            cmd = ["pytest", "tests/", "--tb=short"]
            description = "Full test suite"

        success, output = self.run_command(cmd, description)

        self.print_result(success, description, output if not success else "")
        return success

    def check_pre_commit_setup(self) -> bool:
        """Check if pre-commit is installed and configured"""
        self.print_header("Pre-commit Setup Check", "🔧")

        # Check if pre-commit is installed
        success, _ = self.run_command(
            ["pre-commit", "--version"], "Pre-commit version check"
        )
        if not success:
            self.print_result(
                False, "Pre-commit not installed", "Run: pip install pre-commit"
            )
            return False

        # Check if hooks are installed
        hooks_file = self.project_root / ".git" / "hooks" / "pre-commit"
        if not hooks_file.exists():
            self.print_result(
                False, "Pre-commit hooks not installed", "Run: pre-commit install"
            )
            return False

        self.print_result(True, "Pre-commit setup verified")
        return True

    def print_quality_summary(self, results: dict):
        """Print a comprehensive quality summary with recommendations"""
        self.print_header("Quality Check Summary", "📊")

        total_checks = len(results)
        passed_checks = sum(1 for r in results.values() if r)
        success_rate = (passed_checks / total_checks) * 100 if total_checks > 0 else 0

        print(f"📈 Success Rate: {success_rate:.1f}% ({passed_checks}/{total_checks})")
        print(f"✅ Passed: {passed_checks}")
        print(f"❌ Failed: {total_checks - passed_checks}")

        if success_rate == 100:
            print("\n🎉 ALL QUALITY CHECKS PASSED!")
            print("🚀 Code is ready for commit")
        else:
            print("\n⚠️  QUALITY ISSUES DETECTED")
            print("🔧 Run with --fix to auto-fix formatting and imports")
            print("💡 Review failed checks above for details")

        print("\n📋 Next Steps:")
        if not results.get("pre_commit", True):
            print("  1. 🔧 Install pre-commit: pip install pre-commit")
            print("     and then run: pre-commit install")
        if not results.get("formatting", True):
            print("  2. ⚫ Fix formatting: python scripts/quality_check.py --fix")
        if not results.get("imports", True):
            print("  3. 🔤 Fix imports: python scripts/quality_check.py --fix")
        if not results.get("linting", True):
            print("  4. 🔍 Fix linting issues manually")
        if not results.get("typing", True):
            print("  5. 🎯 Fix type annotations")
        if not results.get("security", True):
            print("  6. 🔒 Review security findings")

    def run_comprehensive_check(self, fix: bool = False, quick_tests: bool = False):
        """Run all quality checks and provide comprehensive report"""
        print("🎯 COMPREHENSIVE CODE QUALITY CHECK")
        print("=" * 40)
        print("🚀 Ensuring code meets professional standards")

        results = {}

        # Pre-commit setup check
        results["pre_commit"] = self.check_pre_commit_setup()

        # Code formatting and style
        results["formatting"] = self.run_black_format(fix)
        results["imports"] = self.run_isort_imports(fix)
        results["linting"] = self.run_flake8_linting()
        results["typing"] = self.run_mypy_typing()

        # Security and testing
        results["security"] = self.run_security_scan()
        results["tests"] = self.run_tests(quick_tests)

        # Summary and recommendations
        self.print_quality_summary(results)

        return all(results.values())


def main():
    """Main entry point for code quality checking"""
    parser = argparse.ArgumentParser(
        description="🎯 Comprehensive code quality checker with auto-fixes"
    )
    parser.add_argument(
        "--fix", action="store_true", help="🔧 Auto-fix formatting and import issues"
    )
    parser.add_argument(
        "--quick-tests",
        action="store_true",
        help="🧪 Run only quick functionality tests",
    )
    parser.add_argument(
        "--pre-commit", action="store_true", help="🚀 Run pre-commit hooks on all files"
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    checker = CodeQualityChecker(project_root)

    if args.pre_commit:
        # Run pre-commit hooks
        success, output = checker.run_command(
            ["pre-commit", "run", "--all-files"], "Pre-commit hooks"
        )
        print(output)
        sys.exit(0 if success else 1)

    # Run comprehensive check
    success = checker.run_comprehensive_check(
        fix=args.fix, quick_tests=args.quick_tests
    )

    if success:
        print("\n🎉 QUALITY CHECK COMPLETE - ALL CHECKS PASSED!")
        print("💡 Remember to run quality checks before every commit")
        print("🔧 Pre-commit hooks will run automatically on git commit")
    else:
        print("\n⚠️  QUALITY ISSUES DETECTED")
        print("🔧 Use --fix to auto-resolve formatting and import issues")
        print("📖 Review output above for manual fixes needed")

    if not args.fix:
        print("\n⚠️  Quality issues detected - consider fixing before push")
        print("🔧 Run: python scripts/quality_check.py --fix")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
