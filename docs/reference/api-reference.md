# API Usage Guide

## 🎯 Unified Pattern Engine API

**Production Ready**: The library now uses a unified pattern engine that provides comprehensive harmonic analysis through a single, robust architecture. The engine automatically handles key inference, modal parent key conversion, and provides quality-gated confidence scoring.

```python
# ✅ REQUIRED: Always provide key_hint for harmonic analysis
result = await service.analyze_with_patterns_async(
    chords=['Cm', 'F', 'Bb', 'Cm'],
    key_hint='C dorian',  # Essential for modal analysis
    profile='classical'
)

# ✅ Scale analysis requires key_hint parameter
result = await service.analyze_with_patterns_async(
    notes=['D', 'E', 'F', 'G', 'A', 'B', 'C'],
    key_hint='C major',  # Parent key for modal analysis
    profile='classical'
)

# ✅ Roman numeral analysis with accidentals support
result = await service.analyze_with_patterns_async(
    romans=['i', 'iv', 'V', 'i', '♭VII'],  # Now supports ♭VII, bVII accidentals
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
from harmonic_analysis.services.unified_pattern_service import UnifiedPatternService

# Simple analysis
service = UnifiedPatternService()
result = await service.analyze_with_patterns_async(['C', 'F', 'G', 'C'], profile="classical")
print(f"Primary: {' - '.join(result.primary.roman_numerals)}")
print(f"Confidence: {result.primary.confidence:.2f}")

# With options
service = UnifiedPatternService()
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
from harmonic_analysis.services.unified_pattern_service import UnifiedPatternService

service = UnifiedPatternService()

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
    chords=['C', 'F', 'G', 'C'],
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
        chords=['C', 'F'],
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
from harmonic_analysis.services.unified_pattern_service import UnifiedPatternService

service = UnifiedPatternService()

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

## Audio Analysis API

### AudioAdapter

The `AudioAdapter` class orchestrates audio file I/O and the analysis pipeline (key estimation, cadence detection, region classification, and chord estimation) into a single `from_audio()` call.

```python
from harmonic_analysis.integrations.audio_adapter import AudioAdapter, analyze_audio, analyze_audio_async

# Using the adapter directly
adapter = AudioAdapter(
    quiet=False,              # Suppress ffmpeg-missing warning
    include_chords=True,      # Enable chord estimation (default: True)
    chord_window_size_s=0.5,  # Chord analysis window size in seconds
    chord_hop_size_s=0.25,    # Chord analysis hop size in seconds
    tonal_bias=0.15,          # Diatonic similarity bonus (0.0 to disable)
)
result = adapter.from_audio("path/to/audio.wav")

# Or use the convenience wrappers
result = analyze_audio("path/to/audio.wav", quiet=True)
result = await analyze_audio_async("path/to/audio.wav", quiet=True)
```

**Constructor Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `quiet` | `bool` | `False` | Suppresses the ffmpeg-missing warning log. |
| `include_chords` | `bool` | `True` | Enable chord estimation in `from_audio()`. Set `False` to skip. |
| `chord_window_size_s` | `float` | `0.5` | Chord estimation analysis window in seconds. |
| `chord_hop_size_s` | `float` | `0.25` | Chord estimation hop size in seconds. |
| `tonal_bias` | `float` | `0.15` | Bonus added to cosine similarity for diatonic chord templates. Auto-zeroed when global key confidence < 0.5. |

### ChordEvent

A frozen dataclass representing a contiguous time region where the chord estimation layer detected the same chord label.

```python
from harmonic_analysis.integrations.audio_adapter import ChordEvent
```

| Field | Type | Description |
|-------|------|-------------|
| `start_time` | `float` | Start of the chord event in seconds. |
| `end_time` | `float` | End of the chord event in seconds. |
| `chord_label` | `str` | Chord name (e.g. `"C"`, `"Am"`, `"F#m"`). Major triads use root name only; minor triads append `"m"`. |
| `confidence` | `float` | Cosine similarity (post-tonal-bias) averaged over constituent windows. Clipped to [0, 1]. |
| `is_diatonic` | `bool` | `True` if the chord root is in the global key's diatonic pitch class set. |

### AudioAnalysisResult

Returned by `from_audio()`, `analyze_audio()`, and `analyze_audio_async()`.

```python
result = await analyze_audio_async("song.wav", quiet=True)

# Access chord events
for chord in result.chords:
    print(f"{chord.start_time:.2f}-{chord.end_time:.2f}: {chord.chord_label} "
          f"(conf={chord.confidence:.2f}, diatonic={chord.is_diatonic})")

# Get chord labels for pattern analysis
symbols = result.chords_as_symbols()  # e.g. ["C", "G", "Am", "F"]

# Chain into pattern analysis
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService
service = PatternAnalysisService()
envelope = await service.analyze_with_patterns_async(
    chord_symbols=symbols,
    key_hint=result.key_hint,
)
```

**Key properties:**

| Property/Method | Return Type | Description |
|-----------------|-------------|-------------|
| `chords` | `list[ChordEvent]` | Timestamped chord events from the chord estimation layer. Empty when `include_chords=False`. |
| `chords_as_symbols()` | `list[str]` | Extracts `chord_label` from each `ChordEvent`. Directly compatible with `PatternAnalysisService`. |
| `key_hint` | `str` | `"<tonic> <mode>"` string for passing to pattern analysis. |

## Integration Patterns

### Web API Integration
The library is designed for seamless web API integration:

```python
from harmonic_analysis.services.unified_pattern_service import UnifiedPatternService

# Simple REST endpoint integration
async def analyze_progression_endpoint(progression: List[str]):
    service = UnifiedPatternService()
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
service = UnifiedPatternService()
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
