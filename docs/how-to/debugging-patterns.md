# Debug Integration Guide

This document explains how to use the integrated debugging system for pattern analysis development and testing.

## Overview

The debug system provides a unified approach to debugging pattern matching issues that works both as a standalone tool and integrates seamlessly with pytest. It consists of:

- **`tools/debug_patterns.py`**: Enhanced command-line debug tool with rich CLI features
- **`tests/utils/debug_helpers.py`**: Core debugging utilities and structured cases
- **`tests/utils/test_debug_utils.py`**: Pytest integration and test failure debugging
- **`tests/core/pattern_engine/test_debug_integration.py`**: Example integration tests

All debugging tools are organized in the `tools/` directory for easy discovery and maintenance.

## Quick Start

### Standalone Debugging

```bash
# List available debug cases
PYTHONPATH=src python tools/debug_patterns.py --list

# Run a specific case
PYTHONPATH=src python tools/debug_patterns.py --case pop_vi_IV_I_V

# Run with detailed tracing
PYTHONPATH=src python tools/debug_patterns.py --case cadential_64 --trace

# Create a custom case interactively
PYTHONPATH=src python tools/debug_patterns.py --interactive

# Run all common cases for regression testing
PYTHONPATH=src python tools/debug_patterns.py

# Run legacy examples
PYTHONPATH=src python tools/debug_patterns.py --legacy
```

### Pytest Integration

```python
# Import debug utilities in tests
from tests.utils import DebugCase, run_debug_case, debug_chord_progression

# Quick debug of a chord progression
debug_info = debug_chord_progression(
    ["Am", "F", "C", "G"],
    profile="pop",
    trace_patterns=["pop_vi_IV_I_V"]
)

# Create structured debug cases
case = DebugCase(
    name="my_test_case",
    chords=["C", "F", "G", "C"],
    profile="classical",
    expected_patterns=["I_IV_V_I"],
    description="Test I-IV-V-I progression"
)

result = run_debug_case(case)
```

### Debugging Test Failures

```python
# Debug a failing test case
from tests.utils import debug_failing_test

debug_info = debug_failing_test(
    "test_vi_IV_I_V_progression",
    chords=["Am", "F", "C", "G"],
    profile="pop"
)

# Use debug context for automatic debugging on exceptions
from tests.utils import DebugContext

def test_my_progression():
    chords = ["C", "Am", "F", "G"]

    with DebugContext("progression_test", chords, profile="pop") as ctx:
        # Test code that might fail
        result = analyze_progression(chords)
        assert len(result.patterns) > 0
        # If assertion fails, debug analysis runs automatically
```

## Core Components

### DebugCase Structure

```python
@dataclass
class DebugCase:
    name: str                              # Descriptive name
    chords: List[str]                      # Chord progression
    profile: str = "classical"             # Analysis profile
    pattern_ids: Optional[List[str]] = None # Patterns to trace
    key_hint: Optional[str] = None         # Key context
    best_cover: bool = False               # Use best cover algorithm
    expected_patterns: Optional[List[str]] = None  # For validation
    should_fail: bool = False              # Expect failure
    description: str = ""                  # Human description
    trace: bool = False                    # Enable detailed tracing
```

### PatternDebugger Features

The `PatternDebugger` class provides:

- **Token Analysis**: Displays the token stream used by the pattern matcher
- **Pattern Detection**: Shows which patterns were found and their scores
- **Detailed Tracing**: Step-by-step pattern matching for specific pattern IDs
- **Library Information**: Shows loaded patterns and matcher state
- **DTO Integration**: Works with the modern AnalysisEnvelope structure

### Common Debug Cases

Pre-defined cases for common patterns:

- `pop_vi_IV_I_V`: Am-F-C-G progression
- `jazz_ii_V_I`: Dm7-G7-Cmaj7 progression
- `phrygian_cadence`: Am-Dm/F-E progression
- `pachelbel_canon`: D-A-Bm-F#m-G-D-G-A progression
- `andalusian_cadence`: Am-G-F-E progression
- `backdoor_progression`: Fm7-Bb7-Cmaj7 progression
- `cadential_64`: C/G-G7-C progression

## Integration Patterns

### 1. Test Development Workflow

```python
# 1. Create debug case for your test scenario
case = DebugCase(
    name="new_feature_test",
    chords=["Dm", "G", "Em", "Am"],
    profile="classical",
    pattern_ids=["circle_of_fifths"],
    trace=True
)

# 2. Run debug analysis
debug_info = run_debug_case(case)

# 3. Examine results
print(f"Found patterns: {debug_info['pattern_names']}")
print(f"Tokens: {debug_info['token_dump']}")

# 4. Convert to pytest when ready
test_func = create_test_from_case(case)
```

### 2. Regression Testing

```python
# Generate tests from debug cases for regression protection
@pytest.mark.parametrize("case_name", [
    "pop_vi_IV_I_V", "jazz_ii_V_I", "cadential_64"
])
def test_common_patterns(case_name):
    case = get_case_by_name(case_name)
    test_func = create_test_from_case(case)
    test_func()  # Run the generated test
```

### 3. Issue Investigation

```python
# Quick analysis of problematic progressions
debug_chord_progression(
    ["F#m", "B", "E", "A"],
    profile="classical",
    trace_patterns=["circle_of_fifths"]
)

# Structured investigation with expectations
case = DebugCase(
    name="issue_investigation",
    chords=["F#m", "B", "E", "A"],
    profile="classical",
    expected_patterns=["ii_V_I_in_A"],
    description="Investigating why ii-V-I in A major isn't detected"
)
```

## Advanced Features

### Custom Debug Cases

```python
# Create reusable debug cases for your project
MY_DEBUG_CASES = [
    DebugCase(
        name="modal_vamp",
        chords=["G", "F", "G", "F"],
        profile="classical",
        pattern_ids=["modal_vamp", "mixolydian_vamp"],
        description="G Mixolydian vamp with bVII"
    ),
    # Add more cases...
]

# Run custom cases
for case in MY_DEBUG_CASES:
    run_debug_case(case)
```

### Pattern Tracing

When `trace=True` and `pattern_ids` are specified, the debugger shows detailed pattern matching attempts:

```
-- Trace cadential_64 --
  ✓ match @ (0,3): score=0.85 | tokens: ['I64', 'V7', 'I']
  x (0,2) failed: missing resolution | tokens: ['I64', 'V7']
```

### Token Analysis

The debugger shows the internal token representation:

```
TOKENS:
  {'i': 0, 'roman': 'I64', 'role': 'T', 'flags': ['inversion'], 'mode': None}
  {'i': 1, 'roman': 'V7', 'role': 'D', 'flags': ['seventh'], 'mode': None}
  {'i': 2, 'roman': 'I', 'role': 'T', 'flags': [], 'mode': None}
```

## Legacy Compatibility

The enhanced `debug_patterns.py` maintains backward compatibility with the original `try_case()` function:

```python
# Original interface still works
try_case(["Am", "F", "C", "G"], profile="pop", pattern_ids=["pop_vi_IV_I_V"])

# But new structured approach is preferred
case = DebugCase(name="pop_case", chords=["Am", "F", "C", "G"], profile="pop")
run_debug_case(case)
```

## Best Practices

1. **Use descriptive names**: Make debug case names clear and searchable
2. **Add descriptions**: Explain what you're testing and why
3. **Start with common cases**: Use existing debug cases as templates
4. **Enable tracing selectively**: Only trace specific patterns you're investigating
5. **Convert to tests**: Turn working debug cases into regression tests
6. **Document expectations**: Use `expected_patterns` to validate behavior
7. **Group related cases**: Create themed collections of debug cases
8. **Use pytest fixtures**: Leverage debug utilities in your test fixtures

## Troubleshooting

### Common Issues

**"Tokens not available from service"**
- The PatternAnalysisService doesn't expose internal tokens by default
- This is expected behavior - functional analysis still works

**"Pattern X not found in library"**
- Check pattern ID spelling in the patterns.json file
- Use `--list` to see available debug cases and their expected patterns

**"Could not access matcher from service"**
- The service may not expose the internal matcher
- Pattern analysis will still work, but detailed tracing won't be available

### Debug Output Interpretation

- **Found patterns**: Patterns successfully detected by the engine
- **Missing expected patterns**: Patterns you expected but weren't found
- **Unexpected patterns**: Extra patterns that were detected
- **Token dump**: Internal representation used by pattern matcher
- **Trace results**: Detailed matching attempts for specific patterns

This integration makes debugging pattern analysis issues much more systematic and integrated with the test workflow, while preserving the flexibility of standalone debugging.
