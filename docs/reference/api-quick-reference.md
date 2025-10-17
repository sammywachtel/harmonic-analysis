# API Quick Reference

Comprehensive guide to all user-facing functions in the harmonic-analysis library.

## Core Analysis Functions

### Chord Progression Analysis

#### `analyze_chord_progression(chords, options=None)`

**Purpose**: Primary analysis function for chord progressions with multiple interpretations.

**Input Formats**:
- `List[str]` - Chord symbols: `["C", "Am", "F", "G"]`
- `str` - Space-separated (auto-converted): `"C Am F G"`

**Optional Parameters** (`AnalysisOptions`):
```python
parent_key: Optional[str]          # Force key context ("C major", "A minor")
pedagogical_level: str             # "beginner", "intermediate", "advanced"
confidence_threshold: float = 0.5  # Minimum confidence for alternatives
max_alternatives: int = 3          # Maximum alternative analyses
include_borrowed_chords: bool = True
include_secondary_dominants: bool = True
```

**Returns**: `MultipleInterpretationResult` with:
- `primary_analysis` - Best interpretation with confidence score
- `alternative_analyses` - Other valid interpretations
- `suggestions` - Bidirectional key/analysis improvements
- `metadata` - Analysis statistics

**Example**:
```python
from harmonic_analysis import analyze_chord_progression

result = analyze_chord_progression(["C", "Am", "F", "G"])
print(f"Key: {result.primary_analysis.key_signature}")
print(f"Romans: {result.primary_analysis.roman_numerals}")
print(f"Confidence: {result.primary_analysis.confidence:.2f}")
```

---

### Scale & Melody Analysis

#### `analyze_scale(notes, parent_key=None, melody=False)`

**Purpose**: Identify scales, modes, and harmonic implications.

**Input Formats**:
- `List[str]` - Note names: `["D", "E", "F", "G", "A", "B", "C"]`
- `str` - Space-separated: `"D E F G A B C"`

**Parameters**:
- `parent_key` (optional) - Modal analysis context
- `melody` (bool) - True for melodic tonal hierarchy, False for scale pattern matching

**Returns**: `ScaleMelodyAnalysisResult` with mode classification, parent key, confidence, and modal labels.

#### `analyze_melody(notes, parent_key=None)`

**Purpose**: Analyze melodic contour, intervals, and harmonic implications.

**Returns**: Melodic contour description, intervallic analysis, and phrase structure.

---

### Pattern Analysis Service

#### `PatternAnalysisService.analyze_with_patterns_async(chords, profile="classical", key_hint=None)`

**Purpose**: Unified pattern engine analysis with profile-specific patterns.

**Profiles**:
- `"classical"` - Common Practice period patterns
- `"jazz"` - Jazz harmony patterns
- `"pop"` - Contemporary pop patterns

**Example**:
```python
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

service = PatternAnalysisService()
result = await service.analyze_with_patterns_async(
    chord_symbols=['Dm7', 'G7', 'Cmaj7'],
    profile='jazz',
    key_hint='C major'
)

print(f"Patterns detected: {len(result.pattern_matches)}")
for match in result.pattern_matches:
    print(f"  - {match.name}: {match.score:.2f}")
```

---

## Character & Emotional Analysis

### `analyze_progression_character(chords, key_context=None)`

**Purpose**: Emotional and character analysis of progressions.

**Returns**: `ProgressionCharacter` with mood, emotional trajectory, and cadence strength.

### `get_mode_emotional_profile(mode_name)`

**Purpose**: Get emotional characteristics of musical modes.

**Returns**: `EmotionalProfile` with brightness, energy, tension, and typical genres.

**Example**:
```python
from harmonic_analysis import get_mode_emotional_profile

profile = get_mode_emotional_profile("Dorian")
print(f"Brightness: {profile.brightness}")  # "neutral"
print(f"Primary emotions: {profile.primary_emotions}")
```

### `get_modes_by_brightness(brightness_category)`

**Purpose**: Get modes organized by emotional brightness.

**Input**: `"bright"`, `"neutral"`, or `"dark"`

**Returns**: List of mode names matching the brightness category.

---

## Utility Functions

### `get_interval_name(semitones)`

Convert semitone distance (0-11) to interval name.

**Example**: `get_interval_name(7)` → `"Perfect Fifth"`

### `get_modal_characteristics(mode_name)`

Get theoretical characteristics of a mode.

**Returns**: `ModalCharacteristics` with characteristic degrees, harmonic implications, and typical applications.

### `describe_contour(contour_pattern)`

Convert melodic contour pattern to human-readable description.

**Input**: `["U", "D", "R"]` (Up/Down/Repeat)

**Returns**: Narrative contour description

---

## Input Format Summary

| Function Type | Primary Input | Alternative Formats | Key Parameters |
|---------------|---------------|---------------------|----------------|
| Chord Progression | `List[str]` | `"C Am F G"` | `parent_key`, `pedagogical_level` |
| Scale Analysis | `List[str]` | `"D E F G A B C"` | `parent_key`, `melody` (bool) |
| Melody Analysis | `List[str]` | Sequential notes | `parent_key` |
| Character Analysis | Various | Context-dependent | `target_emotion`, `brightness_level` |
| Reference Data | `str` | Mode/scale names | None (read-only) |

---

## Output Confidence Levels

| Analysis Type | Typical Range | High (>0.8) | Low (<0.5) |
|---------------|---------------|-------------|------------|
| Functional Harmony | 0.6-0.95 | Clear I-IV-V | Ambiguous tonality |
| Modal Analysis | 0.5-0.9 | Strong characteristics | Mixed signals |
| Scale Recognition | 0.7-1.0 | Exact matches | Incomplete scales |
| Character Analysis | 0.3-0.8 | Strong emotion | Neutral |

**Confidence Interpretation**:
- **0.85-1.0**: Very confident - clear, unambiguous patterns
- **0.6-0.85**: Confident - some ambiguity, clear primary interpretation
- **0.4-0.6**: Moderate - multiple valid interpretations
- **0.0-0.4**: Low - highly ambiguous or insufficient context

---

## Analysis Flow

```
INPUT PARSING
    ↓
FUNCTIONAL ANALYSIS (Primary)
├─ Roman Numeral Analysis
├─ Chord Function Identification
└─ Cadence Detection
    ↓
MODAL ENHANCEMENT (If Applicable)
├─ Modal Characteristics Detection
├─ Parent Key Relationship
└─ Modal Implications
    ↓
CHROMATIC ANALYSIS (Advanced)
├─ Secondary Dominants
├─ Borrowed Chords
└─ Chromatic Mediants
    ↓
CHARACTER ANALYSIS (Optional)
├─ Emotional Profile
├─ Mood Analysis
└─ Character Suggestions
    ↓
ENHANCEMENT SUGGESTIONS
├─ Key Context Improvements
├─ Alternative Interpretations
└─ Emotional Enhancements
```

---

## Available Constants

Access these constants for reference data:

```python
from harmonic_analysis import (
    ALL_MAJOR_KEYS,      # All major key signatures
    ALL_MINOR_KEYS,      # All minor key signatures
    ALL_MODES,           # Complete modal system
    MODAL_CHARACTERISTICS  # Mode characteristic degrees
)
```

---

## Educational Content System

### `EducationalService`

**Purpose**: Provide learning context for analysis results.

**Example**:
```python
from harmonic_analysis.educational import (
    EducationalService,
    EducationalFormatter,
    LearningLevel
)

service = EducationalService()

# Get educational context
context = service.explain_pattern(
    "cadence.authentic.perfect",
    LearningLevel.BEGINNER
)

# Format for display
formatter = EducationalFormatter()
print(formatter.format_text(context))

# Generate practice suggestions
suggestions = service.generate_practice_suggestions(
    ["cadence.authentic.perfect", "functional.ii_V_I"],
    LearningLevel.INTERMEDIATE
)
```

**Learning Levels**:
- `BEGINNER` - Simple language, emotional context
- `INTERMEDIATE` - Theory concepts, Roman numerals
- `ADVANCED` - Technical depth, historical context

---

## Music21 Integration

### `Music21Adapter`

**Purpose**: Parse MusicXML and MIDI files for analysis.

**Example**:
```python
from harmonic_analysis.integrations import Music21Adapter

adapter = Music21Adapter()

# From MusicXML
score, metadata = adapter.from_musicxml("chorale.xml")
chords = adapter._extract_chord_symbols(score)

# From MIDI
score, metadata = adapter.from_midi("progression.mid")
key = adapter._extract_key(score)
```

**Features**:
- MusicXML and MIDI parsing
- Chord symbol extraction with chordify
- Key and metadata extraction
- Structural analysis (measures, parts, sections)

---

## Complete API Documentation

For full details on all functions, data structures, and advanced usage:

- **[API Guide](API_GUIDE.md)** - Comprehensive API documentation
- **[Tutorials](../tutorials/)** - Step-by-step learning guides
- **[How-to Guides](../how-to/)** - Specific task solutions
- **[Architecture](../explanation/architecture.md)** - System design and internals

---

## Quick Start Examples

### Basic Progression Analysis
```python
from harmonic_analysis import analyze_chord_progression

result = analyze_chord_progression(["C", "F", "G", "C"])
print(f"Analysis: {result.primary_analysis.analysis}")
print(f"Confidence: {result.primary_analysis.confidence:.0%}")
```

### Scale with Modal Analysis
```python
from harmonic_analysis import analyze_scale

result = analyze_scale(
    notes=["D", "E", "F", "G", "A", "B", "C"],
    parent_key="D dorian"
)
print(f"Mode: {result.primary_analysis.classification}")
```

### Pattern-Based Analysis
```python
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService
import asyncio

async def analyze():
    service = PatternAnalysisService()
    result = await service.analyze_with_patterns_async(
        ['Dm7', 'G7', 'Cmaj7'],
        profile='jazz'
    )
    for pattern in result.pattern_matches:
        print(f"{pattern.name}: {pattern.score:.2f}")

asyncio.run(analyze())
```

---

For questions or issues, see [CONTRIBUTING.md](../../CONTRIBUTING.md) or [TROUBLESHOOTING.md](../TROUBLESHOOTING.md).
