# Contributing to Music Theory Analysis

We welcome contributions to the Music Theory Analysis library! This document provides guidelines for contributing to the
project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Process](#contributing-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to
uphold this code. Please report unacceptable behavior to the owner.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of music theory concepts

### Areas for Contribution

We welcome contributions in the following areas:

1. **Algorithm Improvements**: Enhance existing analysis algorithms
2. **New Features**: Add support for additional music theory concepts
3. **Performance Optimization**: Improve speed and memory usage
4. **Documentation**: Improve examples, tutorials, and API documentation
5. **Testing**: Add test cases and improve coverage
6. **Bug Fixes**: Fix issues and edge cases

## Development Setup

### Automated Setup (Recommended) 🚀

1. **Fork the repository** on GitHub

2. **Clone your fork** and setup environment:
   ```bash
   git clone https://github.com/yourusername/harmonic-analysis-py.git
   cd harmonic-analysis-py

   # One-command comprehensive setup
   python scripts/setup_dev_env.py
   ```

This automated setup script will:

- 📎 Create and activate virtual environment
- 📦 Install all development dependencies
- ⚙️ Configure pre-commit hooks with quality automation
- 📊 Setup IDE integration (PyCharm/VS Code)
- 🛡️ Install security scanning tools (Bandit)
- ✅ Verify installation with comprehensive test run

### Manual Setup (Alternative)

If you prefer manual setup:

3. **Set up the development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev,test]"
   pip install bandit  # Security scanner
   ```

4. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

5. **Verify the setup**:
   ```bash
   # Quick verification
   python scripts/quality_check.py

   # Or manual verification
   pytest
   mypy src/ --ignore-missing-imports
   black --check src/ tests/ scripts/
   flake8 src/ tests/ scripts/
   bandit -r src/ -f json
   ```

### Quality Automation Features 🎯

Our development environment includes comprehensive quality automation:

#### Pre-commit Hooks (Automatic)

Every commit automatically runs:

- **⚫ Black**: Auto-formats code to consistent style
- **📦 isort**: Organizes and sorts import statements
- **🛡️ Bandit**: Scans for security vulnerabilities
- **📊 MyPy**: Validates type annotations
- **🧹 File hygiene**: Removes trailing whitespace, fixes line endings

#### Interactive Quality Commands

```bash
# Comprehensive quality check with auto-fix
python scripts/quality_check.py --fix

# Quick quality check (faster feedback)
python scripts/quality_check.py --quick-tests

# Quality check without auto-fix (validation only)
python scripts/quality_check.py
```

#### Warning-Based Edge Case Testing ⚠️

Our testing system uses warnings instead of failures for edge cases:

- **🟠 Warning icons** highlight issues without blocking development
- **Behavioral validation** ensures appropriate graceful degradation
- **Educational feedback** explains edge case behavior
- **CI/CD friendly** - warnings don't break builds

#### IDE Integration 💻

The setup configures your IDE for optimal development:

**PyCharm Integration:**

- Auto-format on save with Black
- Import optimization with isort
- Real-time linting with flake8
- Type checking integration with MyPy
- Test runner configuration

**VS Code Integration:**

- Python extension configuration
- Linting and formatting settings
- Debugging configuration
- Test discovery and execution

## Contributing Process

### Streamlined Development Workflow 🚦

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with automatic quality assistance:
    - Pre-commit hooks auto-format and validate code on each commit
    - IDE integration provides real-time feedback
    - Quality scripts provide comprehensive validation

3. **Write or update tests** for your changes:
   ```bash
   # Add tests following our warning-based approach for edge cases
   # See tests/test_edge_case_behavior.py for examples
   ```

4. **Update documentation** if necessary

5. **Run comprehensive quality validation**:
   ```bash
   # Comprehensive check with auto-fix and colorful reporting
   python scripts/quality_check.py --fix

   # Quick validation for faster feedback
   python scripts/quality_check.py --quick-tests

   # Traditional approach (also works)
   pytest && pre-commit run --all-files
   ```

6. **Commit your changes** with descriptive messages:
   ```bash
   git add .
   # Pre-commit hooks run automatically here ✨
   git commit -m "feat: add support for augmented sixth chords"
   ```

7. **Push to your fork** and **create a pull request**:
   ```bash
   git push origin feature/your-feature-name
   ```

### Automated CI/CD Pipeline 🚀

Our GitHub Actions pipeline automatically:

- **✅ Validates** code quality, security, and tests
- **📝 Checks** CHANGELOG.md updates for releases
- **🛡️ Scans** for security vulnerabilities
- **📚 Creates releases** when version is incremented
- **📦 Publishes** to PyPI on successful validation

### Quality Validation Workflow

```bash
# Before committing (automatic with pre-commit)
python scripts/quality_check.py --fix

# Before pushing (comprehensive validation)
python scripts/quality_check.py
pytest tests/

# For releases (update version and CHANGELOG.md)
# Then create PR to main - automation handles the rest!
```

## Coding Standards

### Python Style

We follow PEP 8 with some modifications:

- **Line length**: 88 characters (Black default)
- **Imports**: Organized with isort, grouped by standard library, third-party, local
- **Type hints**: Required for all public functions and methods
- **Docstrings**: Google-style docstrings for all public APIs

### Code Quality Tools 🧰

We use a comprehensive suite of automated quality tools:

- **⚫ Black**: Consistent code formatting (88 char line length)
- **📦 isort**: Import statement organization and sorting
- **🔍 flake8**: Code linting and style checking
- **📊 mypy**: Static type checking and validation
- **🛡️ Bandit**: Security vulnerability scanning
- **⚙️ pre-commit**: Git hooks for automatic quality validation
- **📊 pytest**: Comprehensive testing with warning-based edge cases
- **🎨 Quality Scripts**: Interactive validation with auto-fix capabilities

#### Quality Automation Commands

```bash
# Interactive quality management
python scripts/quality_check.py --fix      # Auto-fix with colorful reporting
python scripts/quality_check.py            # Validation only
python scripts/quality_check.py --quick-tests  # Faster feedback

# Individual tool commands (also available)
black src/ tests/ scripts/                 # Format code
isort src/ tests/ scripts/                 # Sort imports
flake8 src/ tests/ scripts/                # Lint code
mypy src/ --ignore-missing-imports         # Type checking
bandit -r src/ -f json                     # Security scan
pre-commit run --all-files                 # Run all hooks
```

### Naming Conventions

- **Functions and variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`
- **Files and modules**: `snake_case`

### Example Code Style

```python
from typing import List, Optional, Tuple
from dataclasses import dataclass

from .types import ChordFunction


@dataclass
class FunctionalChordAnalysis:
    """Analysis result for a single chord in functional harmony context.

    Args:
        chord_symbol: The chord symbol (e.g., "Cm7")
        roman_numeral: Roman numeral analysis (e.g., "ii7")
        function: Harmonic function of the chord
        confidence: Analysis confidence (0.0 to 1.0)
    """
    chord_symbol: str
    roman_numeral: str
    function: ChordFunction
    confidence: float

    def is_high_confidence(self) -> bool:
        """Check if analysis confidence is above threshold.

        Returns:
            True if confidence >= 0.7, False otherwise
        """
        return self.confidence >= 0.7


def analyze_chord_function(
        chord_symbol: str,
        key_center: str,
        mode: str = "major"
) -> FunctionalChordAnalysis:
    """Analyze the harmonic function of a chord in context.

    Args:
        chord_symbol: Chord to analyze (e.g., "Dm7")
        key_center: Tonal center (e.g., "C")
        mode: Mode context ("major" or "minor")

    Returns:
        Functional analysis result with Roman numeral and function

    Raises:
        ValueError: If chord_symbol or key_center is invalid
    """
    if not chord_symbol.strip():
        raise ValueError("Chord symbol cannot be empty")

    # Implementation details...
    return FunctionalChordAnalysis(
        chord_symbol=chord_symbol,
        roman_numeral="ii7",
        function=ChordFunction.PREDOMINANT,
        confidence=0.85
    )
```

## Testing

### Test Structure

We organize tests by category and scope with **warning-based edge case handling**:

```
tests/
├── test_comprehensive_multi_layer_validation.py  # 427 comprehensive test cases
├── test_edge_case_behavior.py                    # Warning-based edge case tests ⚠️
├── test_enhanced_modal_analyzer.py               # Modal analysis unit tests
├── test_functional_harmony.py                    # Functional harmony tests
├── generated/                                     # Generated test cases from scripts
├── fixtures/                                      # Test data and fixtures
└── edge_case_warnings.py                         # Warning utilities for edge cases
```

### Warning-Based Testing Philosophy ⚠️

Our testing system uses **warnings instead of failures** for edge cases:

```python
# Traditional approach (blocks CI/CD)
assert result.confidence > 0.8  # Hard failure

# Our warning-based approach (CI/CD friendly)
if not soft_assert_with_warning(
        result.confidence > 0.8,
        "edge_case_confidence",
        "confidence > 0.8",
        f"confidence = {result.confidence:.3f}",
        severity="medium",
        icon="📊"
):
    warnings_issued += 1  # Log warning, don't fail
```

**Benefits:**

- ✅ **CI/CD doesn't break** on edge cases during development
- ⚠️ **Colorful warnings** highlight issues for attention
- 📝 **Educational feedback** explains edge case behavior
- 📊 **Progress tracking** shows improvement over time

**Warning Categories:**

- 🟠 **Behavioral**: Edge cases behaving as expected but suboptimally
- ⚠️ **Confidence**: Low confidence scores needing attention
- 📊 **Performance**: Metrics below ideal thresholds
- 💭 **Analysis**: Analytical edge cases requiring context
- 🔍 **Validation**: Assertion mismatches worth noting

### Test Execution with Quality Automation

```bash
# Run tests with quality automation
python scripts/quality_check.py --quick-tests  # Fast test + quality check
pytest tests/                                  # Full test suite
pytest tests/test_edge_case_behavior.py -v     # Edge case warnings

# Specific test categories
pytest -m "modal" -v                           # Modal analysis tests
pytest -m "functional" -v                      # Functional harmony tests
pytest tests/test_comprehensive_multi_layer_validation.py -v  # Comprehensive
```

### Test Categories

Use pytest markers to categorize tests:

```python
import pytest


@pytest.mark.unit
def test_chord_parsing():
    """Unit test for chord parsing logic."""
    pass


@pytest.mark.modal
def test_modal_detection():
    """Test modal analysis specifically."""
    pass


@pytest.mark.slow
def test_comprehensive_analysis():
    """Long-running comprehensive test."""
    pass
```

### Writing Good Tests

1. **Descriptive names**: Test function names should describe what is being tested
2. **Arrange, Act, Assert**: Structure tests clearly
3. **Test edge cases**: Include boundary conditions and error cases
4. **Use fixtures**: Share test data and setup code
5. **Parameterize**: Use `pytest.mark.parametrize` for multiple similar test cases

### Example Test

```python
import pytest
from harmonic_analysis import ComprehensiveAnalysisEngine


class TestFunctionalAnalysis:

    @pytest.fixture
    def analyzer(self):
        """Fixture providing a configured analysis engine."""
        return ComprehensiveAnalysisEngine()

    @pytest.mark.parametrize("progression,expected_key", [
        ("C F G C", "C major"),
        ("Am Dm G Am", "A minor"),
        ("G C D G", "G major"),
    ])
    def test_key_detection(self, analyzer, progression, expected_key):
        """Test key center detection for common progressions."""
        result = analyzer.analyze_comprehensively(progression)
        assert result.functional.key_center == expected_key
        assert result.confidence > 0.7

    def test_invalid_progression_raises_error(self, analyzer):
        """Test that invalid input raises appropriate error."""
        with pytest.raises(ValueError, match="empty progression"):
            analyzer.analyze_comprehensively("")
```

## Documentation

### API Documentation

- Use Google-style docstrings for all public functions and classes
- Include examples in docstrings where helpful
- Document parameter types and return values
- Note any exceptions that may be raised

### Code Comments

- Use comments sparingly, prefer self-documenting code
- Explain **why** something is done, not **what** is done
- Comment complex algorithms or non-obvious business logic
- Keep comments up-to-date with code changes

### Examples and Tutorials

When adding new features, consider adding:

- Usage examples in docstrings
- Tutorial notebooks in `docs/examples/`
- Updates to the main README if it affects the public API

## Submitting Changes

### Pull Request Process with Automated Quality 🚀

1. **Update documentation** for any user-facing changes
2. **Add tests** that cover your changes (use warning-based approach for edge cases)
3. **Run comprehensive quality validation**:
   ```bash
   python scripts/quality_check.py --fix  # Auto-fix and validate
   ```
4. **Write a clear PR description** explaining:
    - What changes were made
    - Why they were made
    - Any breaking changes
    - How to test the changes

### Automated Release Process 📚

For releases, our GitHub Actions automatically handle:

1. **Version Detection**: Detects version increments in `src/harmonic_analysis/__init__.py`
2. **CHANGELOG Validation**: Ensures `CHANGELOG.md` is updated
3. **Comprehensive Testing**: Runs full test suite including security scans
4. **Release Creation**: Creates GitHub release with tags
5. **PyPI Publishing**: Automatically publishes to PyPI on successful validation

**To trigger a release:**

```bash
# 1. Update version in src/harmonic_analysis/__init__.py
__version__ = "0.1.0b5"  # Increment version

# 2. Update CHANGELOG.md with release notes
# 3. Create PR to main branch
# 4. Merge PR - automation handles release!
```

### Quality Gate Requirements ✅

All PRs must pass:

- **⚫ Code Formatting**: Black formatting validation
- **📦 Import Organization**: isort validation
- **🔍 Linting**: flake8 code quality checks
- **📊 Type Checking**: MyPy type validation
- **🛡️ Security Scanning**: Bandit vulnerability checks
- **📊 Test Suite**: All tests pass (warnings allowed for edge cases)
- **📝 Documentation**: Updates for user-facing changes

### Commit Message Format

We follow conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

**Examples:**

- `feat(modal): add Lydian mode detection`
- `fix(parsing): handle enharmonic chord symbols`
- `docs(api): update functional analysis examples`

### Review Process with Quality Automation

All submissions require review before merging:

1. **Automated Quality Gates** must pass:
    - ✅ CI/CD pipeline validation
    - 📊 Comprehensive test suite (warnings allowed for edge cases)
    - 🛡️ Security scanning with Bandit
    - ⚫ Code formatting with Black
    - 📦 Import organization with isort
    - 🔍 Linting with flake8
    - 📊 Type checking with MyPy

2. **Code review** by at least one maintainer

3. **Quality validation** using our interactive tools:
   ```bash
   # Reviewer can run comprehensive validation
   python scripts/quality_check.py
   ```

   **PyCharm Users**: Use keyboard shortcuts for faster development:
    - `Ctrl+Alt+F`: Auto-fix formatting and imports
    - `Ctrl+Alt+T`: Run quick functionality tests
    - `Ctrl+Alt+Q`: Comprehensive quality check before commit

4. **Discussion** of any design decisions or concerns

5. **Final approval** and merge by maintainer

### Automated Post-Merge Actions 🎆

After merge to main:

- **Version Detection**: Checks for version increments
- **Automated Release**: Creates releases for version changes
- **PyPI Publishing**: Automatically publishes new versions
- **Tag Creation**: Tags releases in git repository
- **Release Notes**: Generates from CHANGELOG.md

### After Your PR is Merged

1. **Delete your feature branch**
2. **Pull the latest main** to stay up-to-date
3. **Consider contributing** to related areas

## Quality Automation Troubleshooting 🔧

### Common Issues and Solutions

#### Pre-commit Hook Failures

```bash
# If pre-commit hooks fail, run manual fixes:
python scripts/quality_check.py --fix

# Then retry commit:
git add .
git commit -m "your message"
```

#### IDE Integration Issues

```bash
# Re-run setup if IDE integration isn't working:
python scripts/setup_dev_env.py

# Or manually configure IDE settings (check scripts/setup_dev_env.py for details)
```

#### Quality Check Script Issues

```bash
# If quality check script fails, install missing dependencies:
pip install bandit black isort flake8 mypy pytest

# Or reinstall development environment:
pip install -e ".[dev,test]"
```

#### Edge Case Test Warnings

Edge case tests are designed to show warnings, not failures:

- 🟠 **Orange warnings** are expected for edge cases
- ⚠️ **Warning icons** highlight areas for future improvement
- 📊 **Confidence warnings** show suboptimal but acceptable behavior
- These warnings **don't block CI/CD** - this is intentional!

### Quality Automation Commands Reference

```bash
# Complete development setup
python scripts/setup_dev_env.py

# Interactive quality management
python scripts/quality_check.py --fix         # Auto-fix with reporting
python scripts/quality_check.py               # Validation only
python scripts/quality_check.py --quick-tests # Fast feedback

# Manual quality commands (also available)
black src/ tests/ scripts/                    # Format code
isort src/ tests/ scripts/                    # Sort imports
flake8 src/ tests/ scripts/                   # Lint code
mypy src/ --ignore-missing-imports            # Type checking
bandit -r src/ -f json                        # Security scan
pre-commit run --all-files                    # Run pre-commit hooks

# Testing with quality automation
pytest                                         # Full test suite
pytest tests/test_edge_case_behavior.py -v    # Edge case warnings
python scripts/quality_check.py --quick-tests # Tests + quality
```

## Getting Help

If you need help with contributing:

1. **Check existing issues** and discussions
2. **Read the documentation** and examples
3. **Try the quality automation scripts** for common issues:
   ```bash
   python scripts/quality_check.py --fix
   python scripts/setup_dev_env.py
   ```
4. **Ask questions** in GitHub discussions
5. **Contact maintainers** at sammywachtel@gmail.com

## Quality Automation Benefits 🎆

Our comprehensive quality system provides:

- **⚡ Instant feedback** through pre-commit hooks
- **🎨 Auto-formatting** ensures consistent code style
- **🛡️ Security scanning** catches vulnerabilities early
- **⚠️ Warning-based testing** doesn't block development flow
- **🚀 Automated releases** reduce manual deployment work
- **💻 IDE integration** provides seamless development experience
- **📊 Comprehensive validation** ensures production-ready code

Thank you for contributing to Music Theory Analysis! 🎵
