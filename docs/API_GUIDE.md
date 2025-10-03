# API Usage Guide

## 🎯 Unified Pattern Engine API

**Production Ready**: The library now uses a unified pattern engine that provides comprehensive harmonic analysis through a single, robust architecture. The engine automatically handles key inference, modal parent key conversion, and provides quality-gated confidence scoring.

```python
# ✅ REQUIRED: Always provide key_hint for harmonic analysis
result = await service.analyze_with_patterns_async(
    ['Cm', 'F', 'Bb', 'Cm'],
    key_hint='C dorian',  # Essential for modal analysis
    profile='classical'
)

# ✅ Scale analysis requires key_hint parameter
result = await service.analyze_with_patterns_async(
    notes=['D', 'E', 'F', 'G', 'A', 'B', 'C'],
    key_hint='D dorian',  # Required for scale analysis
    profile='classical'
)

# ✅ Roman numeral analysis requires key_hint parameter
result = await service.analyze_with_patterns_async(
    romans=['i', 'iv', 'V', 'i'],
    key_hint='A minor',  # Required for roman analysis
    profile='classical'
)

# ✅ Melody analysis requires key_hint parameter
result = await service.analyze_with_patterns_async(
    melody=['C4', 'D4', 'E4', 'F4', 'G4'],
    key_hint='C major',  # Required for melody analysis
    profile='classical'
)

# ❌ Without key context: ValueError will be raised
result = await service.analyze_with_patterns_async(notes=['C', 'D', 'E'])  # Error!
```

**Unified Engine Benefits**:
- **Automatic Key Inference**: Advanced algorithms detect appropriate key context from progressions
- **Modal Parent Key Conversion**: Intelligent conversion between local and modal parent keys
- **Quality-Gated Calibration**: Conservative confidence scoring with identity fallback
- **Evidence-Based Analysis**: Detailed pattern matching with theoretical justification

## Core API Usage Examples

### Basic Chord Progression Analysis
```python
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

# Simple analysis
service = PatternAnalysisService()
result = await service.analyze_with_patterns_async(['C', 'F', 'G', 'C'], profile="classical")
print(f"Primary: {' - '.join(result.primary.roman_numerals)}")
print(f"Confidence: {result.primary.confidence:.2f}")

# With options
service = PatternAnalysisService()
result = await service.analyze_with_patterns_async(
    ['Am', 'F', 'C', 'G'],
    profile="classical",
    key_hint="C major",
    best_cover=True  # Enable multiple interpretations
)
```

### Multiple Interpretation Results
```python
# Access primary analysis
primary = result.primary
print(f"Type: {primary.type.value}")         # functional, modal, etc.
print(f"Roman: {' - '.join(primary.roman_numerals)}")  # I - vi - IV - V
print(f"Key: {primary.key_signature}")       # C major
print(f"Confidence: {primary.confidence:.2f}")

# Access alternatives
for alt in result.alternatives:
    print(f"Alternative: {' - '.join(alt.roman_numerals)} (confidence: {alt.confidence:.2f})")
    print(f"Type: {alt.type.value}")
```

### Evidence and Reasoning Access
```python
# Examine analytical evidence
for evidence in result.evidence:
    print(f"Evidence: {evidence.reason}")
    print(f"Details: {evidence.details}")

# Examine detected patterns
for pattern in result.primary.patterns:
    print(f"Pattern: {pattern.name}")
    print(f"Score: {pattern.score:.2f}")
    print(f"Span: chords {pattern.start}-{pattern.end}")
```

### Scale Analysis (NEW in Iteration 12)

The unified pattern engine now supports comprehensive scale analysis with automatic mode detection:

```python
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

service = PatternAnalysisService()

# Major scale analysis
result = await service.analyze_with_patterns_async(
    notes=['C', 'D', 'E', 'F', 'G', 'A', 'B'],
    key_hint='C major',
    profile='classical'
)
print(f"Mode: {result.primary.mode}")           # Ionian
print(f"Key: {result.primary.key_signature}")   # C major

# Modal scale analysis with automatic mode detection
result = await service.analyze_with_patterns_async(
    notes=['D', 'E', 'F', 'G', 'A', 'B', 'C'],
    key_hint='D dorian',  # Required for scale analysis
    profile='classical'
)
print(f"Detected mode: {result.primary.mode}")  # Dorian
print(f"Analysis type: {result.primary.type}")  # AnalysisType.MODAL

# Multiple modal scales
modal_scales = [
    (['G', 'A', 'B', 'C', 'D', 'E', 'F'], 'G mixolydian'),  # ♭7
    (['E', 'F', 'G', 'A', 'B', 'C', 'D'], 'E phrygian'),   # ♭2
    (['F', 'G', 'A', 'B', 'C', 'D', 'E'], 'F lydian'),     # ♯4
]

for notes, key_hint in modal_scales:
    result = await service.analyze_with_patterns_async(
        notes=notes,
        key_hint=key_hint,
        profile='classical'
    )
    print(f"{key_hint}: confidence={result.primary.confidence:.2f}")
```

**Scale Analysis Features:**
- **Automatic Mode Detection**: Recognizes all 7 modes of major scale
- **Key Requirement**: Scale analysis requires explicit `key_hint` parameter
- **Input Flexibility**: Supports various note formats (sharps, flats, mixed case)
- **Validation**: Comprehensive error handling for invalid scales or mismatched keys
- **Pattern Integration**: Uses the same unified pattern engine as chord analysis

### Enhanced Scale Analysis with Summaries (NEW in Iteration 15)

The unified pattern service now provides rich scale summary data with comprehensive modal analysis:

```python
from harmonic_analysis.services.unified_pattern_service import UnifiedPatternService

service = UnifiedPatternService()

# Enhanced Dorian scale analysis with detailed summary
result = await service.analyze_with_patterns_async(
    notes=['C', 'D', 'E♭', 'F', 'G', 'A', 'B♭'],
    key_hint='C dorian'
)

# Access rich scale summary (NEW!)
if result.primary.scale_summary:
    scale_summary = result.primary.scale_summary

    print(f"Detected Mode: {scale_summary.detected_mode}")           # "Dorian"
    print(f"Parent Key: {scale_summary.parent_key}")                 # "C major"
    print(f"Characteristic Notes: {scale_summary.characteristic_notes}")  # ["♭3", "♮6"]
    print(f"Scale Notes: {' - '.join(scale_summary.notes)}")         # "C - D - Eb - F - G - A - Bb"
    print(f"Scale Degrees: {scale_summary.degrees}")                 # [1, 2, 3, 4, 5, 6, 7]

# Enhanced reasoning includes scale information
print(f"Enhanced Reasoning: {result.primary.reasoning}")
# "Detected Dorian scale with characteristic ♭3 and ♮6 intervals"
```

**Scale Summary Features:**
- **Mode Detection**: Automatic identification of Ionian, Dorian, Phrygian, Lydian, Mixolydian, Aeolian, Locrian
- **Characteristic Intervals**: Identifies defining intervals (♭2, ♭3, ♯4, ♭6, ♭7) for each mode
- **Parent Key Mapping**: Shows relationship between modal and parent major keys
- **Normalized Notation**: Consistent enharmonic spelling and degree numbering
- **Full Serialization**: JSON-compatible for API responses and data storage

### Melody Analysis with Contour Detection (NEW in Iteration 15)

Comprehensive melodic analysis with contour, range, and pattern detection:

```python
# Ascending melody analysis
result = await service.analyze_with_patterns_async(
    melody=['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5'],
    key_hint='C major'
)

# Access rich melody summary (NEW!)
if result.primary.melody_summary:
    melody_summary = result.primary.melody_summary

    print(f"Melodic Contour: {melody_summary.contour}")                    # "ascending"
    print(f"Range: {melody_summary.range_semitones} semitones")            # 12
    print(f"Intervals: {melody_summary.intervals}")                        # [2, 2, 1, 2, 2, 2, 1]
    print(f"Leading Tone Resolutions: {melody_summary.leading_tone_resolutions}")  # 2
    print(f"Characteristics: {melody_summary.melodic_characteristics}")    # ["stepwise motion"]

# Complex melody with leaps and chromatic motion
result = await service.analyze_with_patterns_async(
    melody=['C4', 'A4', 'F4', 'D#4', 'C4'],
    key_hint='C major'
)

if result.primary.melody_summary:
    melody_summary = result.primary.melody_summary
    print(f"Contour: {melody_summary.contour}")                 # "descending" or "arch"
    print(f"Characteristics: {melody_summary.melodic_characteristics}")
    # ["leap emphasis", "chromatic motion"]
    print(f"Chromatic Notes: {melody_summary.chromatic_notes}") # ["D#"]
```

**Melody Analysis Features:**
- **Contour Detection**: Identifies ascending, descending, arch, wave, and mixed patterns
- **Range Calculation**: Total melodic span in semitones
- **Interval Analysis**: Precise semitone intervals between consecutive notes
- **Pattern Recognition**: Leading tone resolutions, suspensions, and harmonic patterns
- **Chromatic Analysis**: Identifies non-diatonic notes and chromatic motion
- **Characteristic Classification**: Stepwise motion, leap emphasis, scalar passages

### Combined Harmonic and Melodic Analysis

```python
# Comprehensive analysis with chord progression and melody
result = await service.analyze_with_patterns_async(
    chords=['C', 'Am', 'F', 'G'],
    melody=['C4', 'E4', 'F4', 'G4'],
    key_hint='C major'
)

# Access both harmonic and melodic insights
print(f"Harmonic Analysis: {' - '.join(result.primary.roman_numerals)}")  # "I - vi - IV - V"
print(f"Confidence: {result.primary.confidence:.3f}")

if result.primary.melody_summary:
    print(f"Melodic Contour: {result.primary.melody_summary.contour}")     # "ascending"
    print(f"Melodic Range: {result.primary.melody_summary.range_semitones} semitones")  # 7

# Enhanced reasoning combines harmonic and melodic analysis
print(f"Complete Reasoning: {result.primary.reasoning}")
# "I-vi-IV-V progression with ascending melodic contour and stepwise motion"
```

### Roman Numeral Analysis (NEW in Iteration 11)

Direct roman numeral input is now supported with automatic chord conversion:

```python
# Roman numeral analysis with key hint
result = await service.analyze_with_patterns_async(
    romans=['I', 'vi', 'IV', 'V'],
    key_hint='C major',  # Required for roman analysis
    profile='classical'
)
print(f"Converted chords: {result.primary.chord_symbols}")  # ['C', 'Am', 'F', 'G']
print(f"Roman analysis: {result.primary.roman_numerals}")   # ['I', 'vi', 'IV', 'V']

# Modal roman numeral analysis
result = await service.analyze_with_patterns_async(
    romans=['i', 'ii', '♭III', 'IV'],
    key_hint='D dorian',
    profile='classical'
)
print(f"Modal analysis: {result.primary.type}")  # AnalysisType.MODAL
```

**Roman Analysis Features:**
- **Direct Roman Input**: Bypasses chord symbol conversion step
- **Key Context Required**: Must provide `key_hint` for proper interpretation
- **Modal Support**: Handles modal roman numerals (♭II, ♭III, ♭VI, ♭VII)
- **Automatic Conversion**: Converts romans to chords for pattern analysis

### Input Type Validation

The unified service enforces input exclusivity and validation:

```python
# ✅ Valid: Single input type with required key_hint
result = await service.analyze_with_patterns_async(
    chord_symbols=['C', 'F', 'G', 'C'],
    profile='classical'
)

# ✅ Valid: Roman analysis with key
result = await service.analyze_with_patterns_async(
    romans=['I', 'IV', 'V', 'I'],
    key_hint='C major',
    profile='classical'
)

# ✅ Valid: Scale analysis with key
result = await service.analyze_with_patterns_async(
    notes=['C', 'D', 'E', 'F', 'G', 'A', 'B'],
    key_hint='C major',
    profile='classical'
)

# ❌ Error: Multiple input types
try:
    result = await service.analyze_with_patterns_async(
        chord_symbols=['C', 'F'],
        romans=['I', 'IV'],  # Cannot provide both
        key_hint='C major'
    )
except ValueError as e:
    print(f"Error: {e}")  # Cannot provide multiple input types

# ❌ Error: Missing key for scale analysis
try:
    result = await service.analyze_with_patterns_async(
        notes=['C', 'D', 'E', 'F', 'G', 'A', 'B']
        # Missing key_hint
    )
except ValueError as e:
    print(f"Error: {e}")  # Scale analysis requires key_hint parameter
```

## Melody Analysis

The unified pattern engine supports comprehensive melody analysis with tonic inference and modal pattern recognition:

```python
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

service = PatternAnalysisService()

# Simple melodic line analysis
result = await service.analyze_with_patterns_async(
    melody=['C4', 'D4', 'E4', 'F4', 'G4'],
    key_hint='C major',  # Required for melody analysis
    profile='classical'
)
print(f"Key: {result.primary.key_signature}")     # C major
print(f"Confidence: {result.primary.confidence:.2f}")

# Modal melody analysis
result = await service.analyze_with_patterns_async(
    melody=['D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5'],
    key_hint='D dorian',
    profile='classical'
)
print(f"Mode: {result.primary.mode}")            # Dorian characteristics
print(f"Key: {result.primary.key_signature}")    # D dorian

# Melody with suspensions and voice leading
result = await service.analyze_with_patterns_async(
    melody=['F4', 'E4', 'C4', 'B3', 'C4'],  # 4-3 and 7-1 movement
    key_hint='C major',
    profile='classical'
)

# Mixolydian melody with characteristic b7
result = await service.analyze_with_patterns_async(
    melody=['G4', 'A4', 'B4', 'C5', 'D5', 'E5', 'F5'],
    key_hint='G mixolydian',
    profile='classical'
)
```

**Melody Analysis Features**:
- **Tonic Inference**: Automatic detection of melodic tonic centers
- **Modal Recognition**: Pattern matching for all seven modes
- **Voice Leading Analysis**: Detection of suspensions, resolutions, and characteristic movements
- **Octave Support**: Handles octave specifications (C4, C5, etc.)
- **Accidental Support**: Processes sharps and flats correctly
- **Confidence Scoring**: Quality-gated confidence assessment

**Supported Input Formats**:
- Note names with octaves: `['C4', 'D4', 'E4']`
- Mixed case handling: `['c4', 'D4', 'e4']`
- Chromatic alterations: `['F#4', 'Bb4', 'C5']`
- Enharmonic equivalents: Both `F#4` and `Gb4` work correctly

## Integration Patterns

### Web API Integration
The library is designed for seamless web API integration:

```python
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

# Simple REST endpoint integration
async def analyze_progression_endpoint(progression: List[str]):
    service = PatternAnalysisService()
    result = await service.analyze_with_patterns_async(progression, profile="classical")
    return {
        "primary_analysis": result.primary.to_dict(),
        "alternatives": [alt.to_dict() for alt in result.alternatives],
        "analysis_time_ms": result.analysis_time_ms
    }
```

### Application Integration
The library provides structured output for application consumption:

```python
# Structured output for application integration
service = PatternAnalysisService()
result = await service.analyze_with_patterns_async(['C', 'F', 'G', 'C'], profile="classical")

# Access structured data
analysis_data = {
    "type": result.primary.type.value,
    "roman_numerals": result.primary.roman_numerals,
    "confidence": result.primary.confidence,
    "key_signature": result.primary.key_signature,
    "patterns": [p.name for p in result.primary.patterns],
    "evidence": [e.reason for e in result.evidence]
}
```

## Library Purpose and Intended Usage

### Primary Use Case
This library provides comprehensive harmonic analysis capabilities for chord progressions, offering:

1. **Multiple Analytical Perspectives**: Functional harmony, modal analysis, and chromatic harmony
2. **Educational Context**: Explanations suitable for different pedagogical levels (beginner/intermediate/advanced)
3. **Confidence-Based Results**: Analytical certainty scores to guide decision making
4. **Evidence-Based Reasoning**: Detailed justification for analytical conclusions

### Integration Use Cases
The library is designed for:
- **Web Applications**: REST API endpoints for harmonic progression analysis
- **Music Software**: Integration into music theory and composition tools
- **Educational Applications**: Music theory learning and analysis applications
- **Research Tools**: Academic and professional harmonic analysis utilities
- **Command Line Tools**: Standalone harmonic analysis scripts
