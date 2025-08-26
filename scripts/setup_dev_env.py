#!/usr/bin/env python3
"""
🚀 Development Environment Setup Script

Automatically configures the development environment with all necessary tools,
pre-commit hooks, and IDE integration for optimal code quality workflow.
"""

import os
import subprocess
from pathlib import Path


def run_command(cmd, description, check=True):
    """Run a command with nice output"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(
            cmd, shell=True, check=check, text=True, capture_output=True
        )
        if result.returncode == 0:
            print(f"   ✅ {description} completed")
            return True
        else:
            print(f"   ❌ {description} failed: {result.stderr}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"   ❌ {description} failed: {e}")
        return False


def setup_development_environment():
    """Setup complete development environment"""
    print("🚀 HARMONIC ANALYSIS - DEVELOPMENT ENVIRONMENT SETUP")
    print("=" * 60)

    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    success_count = 0
    total_steps = 10

    # Step 1: Install package in development mode
    if run_command("pip install -e .", "Installing package in development mode"):
        success_count += 1

    # Step 2: Install development dependencies
    if run_command("pip install -e .[dev,test]", "Installing development dependencies"):
        success_count += 1

    # Step 3: Install additional quality tools
    extra_tools = [
        "bandit",
        "safety",
        "pre-commit-hooks",
        "pytest-xdist",
        "coverage[toml]",
    ]

    if run_command(
        f"pip install {' '.join(extra_tools)}", "Installing additional quality tools"
    ):
        success_count += 1

    # Step 4: Install pre-commit hooks
    if run_command("pre-commit install", "Installing pre-commit hooks"):
        success_count += 1

    # Step 5: Update pre-commit hook versions
    if run_command("pre-commit autoupdate", "Updating pre-commit hook versions"):
        success_count += 1

    # Step 6: Run initial pre-commit on all files
    print("🧪 Running initial pre-commit check on all files...")
    subprocess.run("pre-commit run --all-files", shell=True)
    success_count += 1

    # Step 7: Create IDE configuration hints
    if create_ide_config():
        success_count += 1

    # Step 8: Setup git hooks for quality reminders
    if setup_git_hooks():
        success_count += 1

    # Step 9: Create quality check shortcuts
    if create_quality_shortcuts():
        success_count += 1

    # Step 10: Verify setup
    if verify_setup():
        success_count += 1

    # Summary
    print("\n📊 SETUP SUMMARY:")
    print(f"✅ Completed: {success_count}/{total_steps} steps")

    if success_count == total_steps:
        print("\n🎉 DEVELOPMENT ENVIRONMENT SETUP COMPLETE!")
        print_next_steps()
    else:
        print(f"\n⚠️  Setup partially completed ({success_count}/{total_steps})")
        print("🔧 Review errors above and run again if needed")


def create_ide_config():
    """Create IDE configuration hints"""
    print("🔧 Creating IDE configuration hints...")

    # PyCharm/IntelliJ configuration
    idea_dir = Path(".idea")
    if idea_dir.exists() or Path("*.iml").glob():
        # Suggested PyCharm inspection profile snippet (for reference):
        # <!-- Add to .idea/inspectionProfiles/profiles_settings.xml -->
        # <profile version="1.0">
        #   <option name="myName" value="Harmonic Analysis Quality" />
        #   <inspection_tool class="PyPep8Inspection" enabled="true"
        #                    level="WARNING" enabled_by_default="true">
        #     <option name="ignoreErrors">
        #       <list>
        #         <option value="E203" />
        #         <option value="W503" />
        #       </list>
        #     </option>
        #   </inspection_tool>
        # </profile>

        print("   💡 PyCharm detected - configure real-time inspection:")
        print("      📋 STEP-BY-STEP PYCHARM SETUP:")
        print("      1️⃣ File → Settings → Editor → Inspections")
        print("         ✅ Enable 'Python' → 'PEP 8 coding style violation'")
        print("         ✅ Enable 'Python' → 'Type checker compatibility'")
        print("")
        print("      2️⃣ File → Settings → Tools → External Tools → Add:")
        print("         🔧 Name: 'Quality Check Fix'")
        print("         🔧 Program: python")
        print("         🔧 Arguments: scripts/quality_check.py --fix")
        print("         🔧 Working Directory: $ProjectFileDir$")
        print("")
        print(
            "      💡 SHORTCUT: Use keyboard shortcut ⌘, (Ctrl+Alt+S on Windows/Linux)"
        )
        print("          to quickly open Settings dialog")
        print("")
        print("      3️⃣ File → Settings → Tools → File Watchers (Optional):")
        print("         👁️ Add Black formatter for auto-format on save")
        print("         👁️ Add isort for auto-import organization")
        print("")
        print("      4️⃣ Enable real-time highlighting:")
        print("         ⚙️ Settings → Editor → General → Code Completion")
        print("         ✅ 'Show suggestions as you type'")
        print("         ✅ 'Add unambiguous imports on the fly'")
        print("")
        print("      🎯 Result: Real-time red/yellow underlines for issues!")
        print("      📖 Full details in scripts/README.md")

    # VS Code configuration`
    vscode_dir = Path(".vscode")
    if vscode_dir.exists():
        vscode_config = {
            "python.formatting.provider": "black",
            "python.linting.enabled": True,
            "python.linting.flake8Enabled": True,
            "python.linting.mypyEnabled": True,
            "editor.formatOnSave": True,
            "editor.codeActionsOnSave": {"source.organizeImports": True},
        }

        settings_file = vscode_dir / "settings.json"
        if not settings_file.exists():
            import json

            with open(settings_file, "w") as f:
                json.dump(vscode_config, f, indent=2)
            print("   ✅ VS Code settings.json created")
        else:
            print(
                "   💡 VS Code detected - verify settings.json includes "
                "formatting config"
            )

    return True


def setup_git_hooks():
    """Setup additional git hooks for quality reminders"""
    print("🔧 Setting up git quality reminders...")

    hooks_dir = Path(".git/hooks")

    # Pre-push hook for extra validation
    pre_push_hook = hooks_dir / "pre-push"
    pre_push_content = """#!/bin/sh
# Quality reminder before push
echo "🎯 QUALITY REMINDER: Running quick checks before push..."
python scripts/quality_check.py --quick-tests
if [ $? -ne 0 ]; then
    echo "⚠️  Quality issues detected - consider fixing before push"
    echo "🔧 Run: python scripts/quality_check.py --fix"
fi
"""

    try:
        with open(pre_push_hook, "w") as f:
            f.write(pre_push_content)
        pre_push_hook.chmod(0o755)
        print("   ✅ Pre-push quality reminder installed")
        return True
    except Exception as e:
        print(f"   ⚠️  Could not setup pre-push hook: {e}")
        return False


def create_quality_shortcuts():
    """Create convenient quality check shortcuts"""
    print("🔧 Creating quality check shortcuts...")

    # Create Makefile for common commands
    makefile_content = """# Harmonic Analysis Development Commands

.PHONY: help format lint test quality setup clean

help:  ## Show this help
\t@echo "🎯 Harmonic Analysis Development Commands:"
\t@echo "make setup     - Setup development environment"
\t@echo "make format    - Auto-fix code formatting and imports"
\t@echo "make lint      - Run all quality checks"
\t@echo "make test      - Run test suite"
\t@echo "make quality   - Run comprehensive quality check"
\t@echo "make clean     - Clean build artifacts"

setup:  ## Setup development environment
\tpython scripts/setup_dev_env.py

format:  ## Auto-fix formatting and imports
\tpython scripts/quality_check.py --fix

lint:  ## Run linting checks
\tpython scripts/quality_check.py

test:  ## Run test suite
\tpytest tests/ -v

quality:  ## Run comprehensive quality check
\tpython scripts/quality_check.py

clean:  ## Clean build artifacts
\trm -rf build/ dist/ *.egg-info/
\tfind . -type d -name __pycache__ -delete
\tfind . -type f -name "*.pyc" -delete
"""

    try:
        with open("Makefile", "w") as f:
            f.write(makefile_content)
        print("   ✅ Makefile created with quality shortcuts")
        return True
    except Exception as e:
        print(f"   ⚠️  Could not create Makefile: {e}")
        return False


def verify_setup():
    """Verify the development setup is working"""
    print("🔍 Verifying development setup...")

    checks = [
        ("pre-commit --version", "Pre-commit installed"),
        ("black --version", "Black formatter installed"),
        ("flake8 --version", "Flake8 linter installed"),
        ("mypy --version", "MyPy type checker installed"),
        ("pytest --version", "Pytest test runner installed"),
        ("bandit --version", "Bandit security scanner installed"),
    ]

    success = True
    for cmd, description in checks:
        if not run_command(cmd, description, check=False):
            success = False

    return success


def print_next_steps():
    """Print next steps and usage instructions"""
    print(
        """
🎯 NEXT STEPS FOR QUALITY-DRIVEN DEVELOPMENT:

📝 Daily Development Workflow:
  1. 🔧 make format          - Auto-fix formatting before coding
  2. 💻 [Write your code]    - Implement features/fixes
  3. 🧪 make test           - Run tests to verify functionality
  4. 🔍 make quality        - Comprehensive quality check
  5. 📝 git add/commit       - Pre-commit hooks run automatically
  6. 🚀 git push            - Pre-push reminder runs quality checks

🛠️  Available Commands:
  • python scripts/quality_check.py --fix    - Auto-fix formatting
  • python scripts/quality_check.py          - Full quality check
  • python scripts/quality_check.py --quick-tests - Quick test run
  • pre-commit run --all-files               - Run all pre-commit hooks
  • make help                                - Show all available commands

🔧 IDE Integration:
  • PyCharm: Configure External Tools for quality scripts
  • VS Code: Auto-formatting and linting should work automatically
  • Any editor: Run scripts/quality_check.py before commits

⚡ Automated Quality Gates:
  • Pre-commit: Runs on every git commit (formatting, linting, typing)
  • Pre-push: Quality reminder before pushing to remote
  • GitHub Actions: Full validation on PRs with automated releases

💡 Pro Tips:
  • Run 'make format' frequently while coding
  • Use 'make quality' before creating PRs
  • The pre-commit hooks will fix most issues automatically
  • All quality checks use colorful icons for easy identification

🎉 Happy coding with automated quality assurance!
"""
    )


if __name__ == "__main__":
    setup_development_environment()
