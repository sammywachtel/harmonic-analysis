# Scripts Directory

This directory contains essential maintenance scripts and quality automation tools for the harmonic analysis library.

## 🚀 Quality Automation Scripts (New in v0.1.0b4)

### 🛠️ `setup_dev_env.py`
**Purpose**: One-command comprehensive development environment setup

**Key Features**:
- 📦 Installs all development dependencies and security tools
- ⚙️ Configures pre-commit hooks with quality automation
- 💻 Sets up IDE integration for PyCharm and VS Code
- 🧪 Runs initial quality checks to verify setup
- ✨ Creates quality check shortcuts and git hooks

**Usage**:
```bash
# Complete development setup in one command
python scripts/setup_dev_env.py
```

**What it sets up**:
1. Package installation in development mode
2. Development dependencies (Black, isort, flake8, MyPy, Bandit, pytest)
3. Pre-commit hooks with comprehensive quality checks
4. IDE configuration (PyCharm External Tools, VS Code settings)
5. Git hooks for quality reminders
6. Quality check shortcuts and verification

### 📊 `quality_check.py`
**Purpose**: Interactive comprehensive quality validation with auto-fix capabilities

**Key Features**:
- 🎨 Auto-formatting with Black and isort
- 🔍 Comprehensive linting with flake8
- 📊 Type checking with MyPy
- 🛡️ Security scanning with Bandit
- 🧪 Quick test execution option
- 🌈 Colorful reporting with actionable recommendations

**Usage**:
```bash
# Comprehensive quality check with auto-fix
python scripts/quality_check.py --fix

# Quick quality check for faster feedback
python scripts/quality_check.py --quick-tests

# Validation only (no auto-fix)
python scripts/quality_check.py
```

**Quality Gates Checked**:
- ⚫ **Black**: Code formatting (88-char lines, consistent style)
- 📦 **isort**: Import organization and sorting
- 🔍 **flake8**: Code linting and style validation
- 📊 **MyPy**: Static type checking
- 🛡️ **Bandit**: Security vulnerability scanning
- 🧪 **pytest**: Test execution (optional quick tests)

**Output Example**:
```
🚀 HARMONIC ANALYSIS - COMPREHENSIVE QUALITY CHECK
========================================================
⚫ Code Formatting (Black).................. ✅ PASS
📦 Import Organization (isort)............. ✅ PASS
🔍 Code Linting (flake8)................... ⚠️  3 issues (auto-fixed)
📊 Type Checking (MyPy).................... ❌ 5 errors
🛡️ Security Scan (Bandit).................. ✅ PASS
🧪 Quick Tests (pytest).................... ✅ PASS (107/115)
```

## 🔧 Analysis & Maintenance Scripts

### 🎯 `confidence_calibration_analysis.py`
**Purpose**: Production confidence scoring analysis and calibration tool

**Key Features**:
- Analyzes confidence patterns between expected vs actual scores
- Uses proper parent_key context from comprehensive test cases
- Provides detailed confidence difference reporting for debugging
- Essential for maintaining system accuracy and calibration

**Usage**:
```bash
python scripts/confidence_calibration_analysis.py
```

**When to Use**:
- After making changes to confidence scoring algorithms
- When comprehensive tests show confidence mismatches
- During confidence calibration development cycles
- For debugging systematic confidence scoring issues

**Historical Significance**: Critical for identifying the parent key parsing bug that improved functional harmony success rate from 0% to 72%.

### 🏭 `generate_comprehensive_multi_layer_tests.py`
**Purpose**: Comprehensive test case generation system

**Key Features**:
- Generates 427+ multi-layer test cases with complete analysis expectations
- Covers functional harmony, modal analysis, and chromatic analysis
- Exports to JSON and CSV formats for validation and analysis
- **FIXED** Roman numeral generation bug (Aug 2025)

**Usage**:
```bash
python scripts/generate_comprehensive_multi_layer_tests.py
```

**Output Files**:
- `tests/generated/comprehensive-multi-layer-tests.json` - Complete test data
- `tests/generated/comprehensive-multi-layer-tests.csv` - Analysis-friendly format

**When to Use**:
- After fixing bugs in test expectation generation
- Before major releases to refresh test expectations
- When updating test coverage or adding new categories

**Critical Fix**: The original version had a broken `chord_to_roman_numeral()` method that returned `"I"` for all major chords and `"ii"` for all minor chords, causing systematic test failures. This has been fixed to properly calculate Roman numerals based on chord root and key center relationships.

## 🚀 Quality Automation Workflows

### Development Workflow with Quality Automation
```bash
# 1. Setup development environment (one-time)
python scripts/setup_dev_env.py

# 2. Before coding - ensure environment is ready
python scripts/quality_check.py --quick-tests

# 3. During development - pre-commit hooks run automatically
git add .
git commit -m "feat: your changes"  # Auto-fixes applied

# 4. Before push - comprehensive validation
python scripts/quality_check.py --fix

# 5. Push with confidence
git push origin your-branch
```

### IDE Integration Workflow (PyCharm)

#### Setting up Real-Time Code Inspection in PyCharm 💡

**Step 1: Access Settings**
- Go to `File` → `Settings` (Windows/Linux) or `PyCharm` → `Preferences` (macOS)
- Or use keyboard shortcut: `Ctrl+Alt+S` (Windows/Linux) or `Cmd+,` (macOS)

**Step 2: Configure Code Inspections**
```
Settings → Editor → Inspections
  ├── Enable "Python"
  ├── ✅ Enable "PEP 8 coding style violation"
  ├── ✅ Enable "Type checker compatibility"
  └── ✅ Enable "Unreachable code"
```

**Step 3: Setup External Tools for Quality Commands**
```
Settings → Tools → External Tools → Add (+)

🔧 Tool 1: "Quality Check Fix"
  ├── Name: Quality Check (Auto-fix)
  ├── Program: python
  ├── Arguments: scripts/quality_check.py --fix
  ├── Working Directory: $ProjectFileDir$
  └── ✅ Show console

🔧 Tool 2: "Quality Check"
  ├── Name: Quality Check (Validate)
  ├── Program: python
  ├── Arguments: scripts/quality_check.py
  ├── Working Directory: $ProjectFileDir$
  └── ✅ Show console

🔧 Tool 3: "Quick Tests"
  ├── Name: Quick Tests
  ├── Program: python
  ├── Arguments: scripts/quality_check.py --quick-tests
  ├── Working Directory: $ProjectFileDir$
  └── ✅ Show console
```

**Step 4: Setup Keyboard Shortcuts (Optional)**
```
Settings → Keymap → External Tools
  ├── Quality Check (Auto-fix): Ctrl+Alt+F
  ├── Quality Check (Validate): Ctrl+Alt+Q
  └── Quick Tests: Ctrl+Alt+T
```

**Step 5: Configure File Watchers (Advanced)**
```
Settings → Tools → File Watchers → Add (+)

👀 Watcher 1: "Black Formatter"
  ├── File Type: Python
  ├── Program: black
  ├── Arguments: $FilePath$
  ├── Working Directory: $ProjectFileDir$
  └── ✅ Auto-save edited files

👀 Watcher 2: "isort Organizer"
  ├── File Type: Python
  ├── Program: isort
  ├── Arguments: $FilePath$
  ├── Working Directory: $ProjectFileDir$
  └── ✅ Auto-save edited files
```

**Step 6: Enable Real-Time Highlighting**
```
Settings → Editor → General → Code Completion
  ├── ✅ Show suggestions as you type
  ├── ✅ Insert selected suggestion by pressing space
  └── Case sensitivity: First letter only

Settings → Editor → General → Auto Import
  ├── ✅ Add unambiguous imports on the fly
  └── ✅ Optimize imports on the fly
```

**Result**: PyCharm will now provide:
- 🔴 **Red underlines** for syntax errors
- 🟡 **Yellow highlights** for PEP 8 violations
- 💡 **Light bulb suggestions** for improvements
- ⚡ **Auto-import** suggestions
- 🎯 **Real-time type checking** feedback

#### VS Code Integration Setup
```json
// .vscode/settings.json (auto-created by setup script)
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.linting.banditEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

## 🔧 Analysis & Maintenance Workflows

### Confidence Calibration Workflow
```bash
# 1. Run tests to identify confidence issues
python -m pytest tests/test_comprehensive_multi_layer_validation.py -v

# 2. Analyze confidence patterns
python scripts/confidence_calibration_analysis.py

# 3. Make algorithmic adjustments based on analysis

# 4. Validate improvements
python -m pytest tests/test_comprehensive_multi_layer_validation.py::TestComprehensiveMultiLayerValidation::test_functional_harmony_cases -v
```

### Test Regeneration Workflow (After Bug Fixes)
```bash
# 1. Generate fresh test data with fixed expectations
python scripts/generate_comprehensive_multi_layer_tests.py

# 2. Validate against regenerated test data
python -m pytest tests/test_comprehensive_multi_layer_validation.py -v

# 3. Expected outcome: Much higher success rates due to correct expectations
```

## 📊 Integration Notes

**Script Dependencies**:
- Both scripts use `sys.path.append()` to access the main library
- Import library types like `AnalysisOptions` for consistency
- Generate data compatible with the test suite structure

**Configuration**:
- Scripts respect library configuration patterns
- Use the same confidence thresholds as the main analysis system
- Maintain compatibility with both development and production environments

## 🌈 Quality Automation Benefits

The new quality automation system provides:

### Immediate Developer Benefits
- **⚡ Instant Feedback**: Pre-commit hooks catch issues before push
- **🎨 Auto-Formatting**: Never worry about code style again
- **🛡️ Security**: Automatic vulnerability scanning
- **📊 Type Safety**: Real-time type checking prevents runtime errors
- **🧪 Test Integration**: Quick tests provide rapid validation

### Team Benefits
- **🤝 Consistent Code**: All team members follow same standards
- **🚫 No More "Style Wars"**: Automated formatting eliminates debates
- **🔄 CI/CD Reliability**: Pre-commit validation prevents pipeline failures
- **📈 Code Quality**: Systematic improvement through automation

### Project Benefits
- **🚀 Release Confidence**: Automated quality gates ensure production readiness
- **📚 Documentation**: Quality process is self-documenting
- **🔧 Maintainability**: Consistent code is easier to maintain
- **🎯 Focus**: Developers focus on logic, not style

## 🚨 Recent Changes & Migration

**August 2025 - Quality Automation System (v0.1.0b4)**:
- **Added** comprehensive quality automation with `setup_dev_env.py` and `quality_check.py`
- **Features**: Auto-formatting, security scanning, type checking, IDE integration
- **Benefits**: ⚡ Instant feedback, 🎨 consistent code style, 🛡️ security validation
- **IDE Support**: Detailed PyCharm and VS Code integration with real-time inspection
- **Impact**: Transforms development workflow with automated quality gates

**August 2025 - Critical Bug Fix**:
- **Fixed** `chord_to_roman_numeral()` in test generator
- **Before**: `C-F-G-C` generated expectations `["I", "I", "I", "I"]`
- **After**: `C-F-G-C` generates correct expectations `["I", "IV", "V", "I"]`
- **Impact**: Expected to improve test success rates from ~30% to 70%+

**Quality Automation Migration**:
- **Added** production-ready quality automation infrastructure
- **Integrated** comprehensive IDE setup with real-time code inspection
- **Automated** development workflow from setup to deployment
- **Enhanced** developer experience with colorful feedback and auto-fixes

**Cleanup**:
- **Removed** temporary debugging scripts:
  - `analyze_test_expectations.py`
  - `analyze_test_failures.py`
  - `comprehensive_failure_analysis.py`
  - `debug_key_detection.py`
  - `examine_specific_failures.py`
- **Kept** only essential production and infrastructure tools
- **Added** quality automation as core infrastructure

## 🎯 Quality Standards

All maintained scripts include:
- ✅ Comprehensive docstring with purpose and usage
- ✅ Historical context for significant changes
- ✅ Clear usage examples and expected outputs
- ✅ Integration notes with the main library
- ✅ Proper error handling and validation

## 📚 Script Documentation Standards

All scripts in this directory follow comprehensive documentation standards:

### Required Documentation Elements
- ✅ **Purpose Statement**: Clear description of script function
- ✅ **Usage Examples**: Command-line examples with expected output
- ✅ **Feature List**: Bullet-pointed capabilities
- ✅ **Integration Notes**: How script fits into overall workflow
- ✅ **Historical Context**: Significant changes and their impact

### Quality Automation Script Standards
- 🎨 **Colorful Output**: Use emojis and colors for visual feedback
- 📊 **Progress Reporting**: Show step-by-step progress with success/failure
- 🛠️ **Auto-Fix Capabilities**: Provide both validation and fix modes
- 🔧 **IDE Integration**: Support for external tool configuration
- ⚡ **Performance**: Quick execution for rapid feedback

### Maintenance Policy
Scripts in this directory are **essential infrastructure**. Any modifications must:
1. **Maintain backward compatibility** with existing workflows
2. **Include comprehensive testing** before deployment
3. **Update documentation** to reflect changes
4. **Preserve quality automation** functionality
5. **Follow the same quality standards** as the main codebase

**Breaking Change Policy**: Any changes that modify script interfaces or behavior must be announced and documented in `CHANGELOG.md`.

## 🎯 Future Enhancements

### Planned Quality Automation Features
- **🤖 AI-Powered Code Review**: Integration with code analysis tools
- **📈 Quality Metrics Dashboard**: Visual quality tracking over time
- **🔄 Automatic Dependency Updates**: Automated security patching
- **🧪 Advanced Testing**: Performance and load testing automation
- **📱 Mobile Notifications**: Quality gate status via mobile alerts

### Community Contributions
We welcome contributions to the quality automation system:
- **New IDE Integrations**: Support for additional IDEs
- **Enhanced Reporting**: Better visualization and metrics
- **Performance Improvements**: Faster execution and feedback
- **Additional Quality Gates**: New validation rules and checks
