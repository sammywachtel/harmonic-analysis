# Development Tools

This directory contains debugging and development utilities for the harmonic analysis library.

## 🔧 **Primary Tool: Unified Debug System**

### `debug_unified.py` - **Main Debug Tool**
Comprehensive debugging interface that consolidates all debug capabilities into a single, powerful tool.

**Usage:**

#### General Commands
```bash
# List all available capabilities and cases
python tools/debug_unified.py --list-capabilities

# Interactive debugging session
python tools/debug_unified.py --interactive
```

#### Analyze Chord Progressions
```bash
# Analyze any chord progression with all analysis types
python tools/debug_unified.py --progression "Am F C G" --all

# Specific analysis types
python tools/debug_unified.py --progression "Am F C G" --patterns --stage-b --backdoor
```

#### Use Predefined Test Cases
```bash
# Use predefined test cases with specific flags
python tools/debug_unified.py --case pop_vi_IV_I_V --patterns --trace

# Test failure analysis
python tools/debug_unified.py --test-failure "test_name" "Am F C G" --all
```

**🔍 Analysis Capabilities:**
- **Patterns**: Pattern detection and matching
- **Tokens**: Token stream analysis
- **Stage B**: Stage B event detection (Neapolitan, cadential 6/4)
- **Backdoor**: Backdoor progression analysis (♭iv7-♭VII7-I)
- **Intervals**: Interval and voice-leading analysis
- **Trace**: Detailed pattern matching traces

**🎵 Predefined Cases:**
- `pop_vi_IV_I_V` - Common pop progression vi-IV-I-V
- `jazz_ii_V_I` - Classic jazz ii-V-I progression
- `phrygian_cadence` - Phrygian half cadence
- `pachelbel_canon` - Pachelbel Canon progression
- `andalusian_cadence` - Andalusian cadence vi-bVII-bVI-V
- `backdoor_progression` - Backdoor ii-V progression
- `cadential_64` - Cadential 6/4 pattern

## 🎯 **Streamlined Debug Architecture**

The debug system has been fully consolidated into a single, unified interface. All legacy debug scripts have been removed to eliminate confusion and ensure consistent behavior:

**✅ Single Entry Point**: `debug_unified.py` provides all debugging capabilities
**✅ Consistent Output**: Unified analysis format across all debug types
**✅ Integrated Workflow**: Seamless integration with pytest decorators
**✅ Clean Architecture**: No overlapping tools or conflicting implementations

## 🧪 **Test Integration & Decorators**

The debug system provides seamless pytest integration through decorators and utilities:

### **Debug Decorators**
```python
from tests.utils import debug_on_failure, debug_always

@debug_on_failure(trace_patterns=True, analyze_tokens=True)
def test_complex_progression(self):
    # Automatically gets debug output only when test fails
    result = analyze_progression(["Am", "F", "C", "G"])
    assert result.confidence > 0.8

@debug_always(analyze_stage_b=True, analyze_backdoor=True)
def test_with_full_debug(self):
    # Always shows comprehensive debug analysis
    result = analyze_progression(["Fm7", "Bb7", "Cmaj7"])
```

**Note**: Many example test files have been cleaned up. The debug decorators are available in `tests/utils/__init__.py`.

### **Manual Debug Cases**
```python
from tests.utils import DebugCase, run_debug_case, get_case_by_name

# Use predefined cases
case = get_case_by_name("pop_vi_IV_I_V")
debug_info = run_debug_case(case, verbose=True)

# Create custom cases
case = DebugCase(
    name="my_test",
    chords=["C", "F", "G", "C"],
    expected_patterns=["vi–IV–I–V"],
    trace=True
)
debug_info = run_debug_case(case)
```

### **Regression Testing**
```python
from tests.utils import create_test_from_case

# Convert debug cases to pytest tests
case = get_case_by_name("jazz_ii_V_I")
test_func = create_test_from_case(case)
test_func()  # Validates expected patterns are detected
```

## 📋 **Best Practices**

1. **Start with `debug_unified.py`**: It's the most comprehensive tool with all capabilities
2. **Use `--list-capabilities`**: See all available analysis types and predefined cases
3. **Test incrementally**: Start with `--patterns`, then add `--stage-b`, `--backdoor`, etc.
4. **Use predefined cases**: Leverage existing test cases like `pop_vi_IV_I_V` and `jazz_ii_V_I`
5. **Enable tracing selectively**: Use `--trace` only for patterns you're investigating, and exclusively within the unified tool
6. **Document expectations**: Create `DebugCase` objects with `expected_patterns`
7. **Use decorators in tests**: `@debug_on_failure` provides automatic debugging
8. **Convert to regression tests**: Turn working debug cases into permanent tests

## 🏛️ **Advanced Features**

### **Analysis Arbitration Service**
The system includes centralized arbitration logic for choosing between functional and modal analyses:

```python
from harmonic_analysis.services.analysis_arbitration_service import AnalysisArbitrationService

service = AnalysisArbitrationService()
result = service.arbitrate(functional_summary, modal_summary, chord_symbols)

# Validate analysis quality
issues = service.validate_analysis_quality(result, expected_type=AnalysisType.FUNCTIONAL)
```

### **PyCharm Integration**
All debug utilities now provide full IDE support:
- ✅ Autocompletion for decorator parameters
- ✅ Type hints and IntelliSense
- ✅ No more "unresolved reference" warnings
- ✅ Parameter hints for all debug functions

## 🚀 **Running from Root Directory**

All tools can be run from the project root:

```bash
# Unified debug tool (recommended)
python tools/debug_unified.py --progression "Am F C G" --all

# All debugging should use the unified tool
# Legacy debug_patterns.py and other scripts have been removed

# Set PYTHONPATH for imports (if needed)
PYTHONPATH=src python tools/debug_unified.py --case pop_vi_IV_I_V
```

## 📚 **See Also**

- **Primary Integration**: `tests/utils/__init__.py` - Main debug utilities package
- **Debug Helpers**: `tests/utils/debug_helpers.py` - Core debug case utilities
- **Unified System**: `tests/utils/unified_debug.py` - Comprehensive debug framework
- **Arbitration Service**: `src/harmonic_analysis/services/analysis_arbitration_service.py`
- **Test Utilities**: `tests/utils/test_debug_utils.py` - Debug utility tests

## 📈 **Recent Updates**

- ✅ **Unified Debug Tool**: All debug capabilities consolidated into single interface
- ✅ **PyCharm Integration**: Full IDE support with proper imports and autocompletion
- ✅ **Test Decorators**: `@debug_on_failure` and `@debug_always` for automatic debugging
- ✅ **Arbitration Service**: Centralized logic for functional vs modal analysis decisions
- ✅ **Pattern Name Updates**: Fixed test cases to use current pattern library names
- ✅ **Improved CLI**: Enhanced command-line interface with better error handling
- ✅ **Test Suite Cleanup**: Removed 8 redundant test files, streamlined to 5 essential files
- ✅ **Legacy Tool Removal**: All deprecated debug scripts removed for clean architecture

## 🎯 **Current Architecture**

- **Single Debug Interface**: `debug_unified.py` is the only debug tool, providing all debugging capabilities
- **Clean Test Suite**: Streamlined pattern engine tests with no redundancy
- **Focused Tools**: Each remaining test file serves a distinct, essential purpose
- **Consistent API**: Unified debug decorators and utilities in `tests/utils/`
- **Maintained Coverage**: 60% test coverage preserved despite 61% file reduction


## ✅ **Test Suite Cleanup Completed**

### Recently Cleaned Up
The test suite has been streamlined to remove redundant and obsolete files:

**Pattern Engine Tests Cleaned:**
- Removed 8 obsolete/redundant test files
- Kept 4 essential test files covering all functionality
- Reduced from 13 files to 5 files (61% reduction)
- All 52 remaining tests pass with 60% coverage maintained

**Current Essential Tests:**
- `test_low_level_events_comprehensive.py` - Comprehensive coverage tests
- `test_matcher.py` - Core pattern matcher with JSON test cases
- `test_glossary_service.py` - Educational features integration
- `test_voice_leading_events.py` - Stage C voice-leading inference

**Legacy Tools Removed:**
- All legacy debug scripts (`debug_patterns.py`, `debug_stage_b.py`, etc.) have been removed
- Only `debug_unified.py` remains as the single debug interface
- Test examples and redundant integration files cleaned up

This ensures a clean, focused codebase with no redundancy while preserving all essential functionality.
