# Harmonic Analysis Library - Comprehensive Functionality Matrix

## Overview
This matrix documents all user-facing functions, their input formats, optional parameters, analysis modes, and expected output structures for the harmonic-analysis library.

---

## 🎯 Core Analysis Functions (Layer 1 - Main API)

### 1. `analyze_chord_progression(chords, options=None)`
**Purpose**: Comprehensive harmonic analysis of chord progressions

#### Input Formats
- **Primary**: `List[str]` - Chord symbols (e.g., `["C", "Am", "F", "G"]`)
- **Optional**: String format auto-converted (e.g., `"C Am F G"`)

#### Optional Parameters (AnalysisOptions)
- `parent_key: Optional[str]` - Force specific key context (e.g., `"C major"`, `"A minor"`)
- `pedagogical_level: Literal["beginner", "intermediate", "advanced"]` - Analysis complexity
- `confidence_threshold: float = 0.5` - Minimum confidence for alternatives
- `max_alternatives: int = 3` - Maximum alternative analyses
- `include_borrowed_chords: bool = True` - Include modal interchange analysis
- `include_secondary_dominants: bool = True` - Include V/V analysis

#### Analysis Modes
- **Functional Harmony** (primary) - Roman numeral analysis, cadences, chord functions
- **Modal Analysis** - Modal characteristics, parent key relationships
- **Chromatic Harmony** - Secondary dominants, borrowed chords, chromatic mediants

#### Expected Outputs
```python
MultipleInterpretationResult:
  - input_chords: List[str]
  - primary_analysis: InterpretationAnalysis
    - type: AnalysisType (FUNCTIONAL/MODAL/CHROMATIC)
    - confidence: float (0.0-1.0)
    - analysis: str (human-readable description)
    - roman_numerals: List[str]
    - key_signature: str
    - mode: str
    - reasoning: str
    - evidence: List[Evidence]
    - modal_characteristics: List[str]
    - secondary_dominants: List[str]
    - borrowed_chords: List[str]
    - cadences: List[str]
    - chord_functions: List[str]
  - alternative_analyses: List[AlternativeAnalysis]
  - suggestions: AnalysisSuggestions (bidirectional improvements)
  - metadata: AnalysisMetadata
```

---

### 2. `analyze_scale(notes, parent_key=None, melody=False)`
**Purpose**: Scale/mode identification and harmonic implications

#### Input Formats
- **Primary**: `List[str]` - Note names (e.g., `["D", "E", "F", "G", "A", "B", "C"]`)
- **String**: Space-separated notes (e.g., `"D E F G A B C"`)

#### Optional Parameters
- `parent_key: Optional[str]` - Parent key context for modal analysis
- `melody: bool = False` - True for melodic analysis (tonal hierarchy), False for scale analysis

#### Analysis Modes
- **Scale Pattern Recognition** (`melody=False`) - Direct pattern matching
- **Melodic Tonal Hierarchy** (`melody=True`) - Weight-based tonal center detection

#### Expected Outputs
```python
ScaleMelodyAnalysisResult:
  - input_scale: str
  - primary_analysis:
    - classification: str (e.g., "D Dorian", "Natural Minor Scale")
    - mode_name: str
    - parent_key: str
    - confidence: float
    - scale_degrees: List[str]
    - modal_labels: Dict[str, str] (all possible tonics)
    - harmonic_implications: List[str]
  - parent_scales: List[str]
  - non_diatonic_pitches: List[str]
  - metadata: Dict (analysis time, scale type)
```

---

### 3. `analyze_melody(notes, parent_key=None)`
**Purpose**: Melodic contour, intervallic content, and harmonic implications

#### Input Formats
- **Primary**: `List[str]` - Melodic note sequence (e.g., `["C", "D", "E", "F", "G", "A", "B", "C"]`)

#### Optional Parameters
- `parent_key: Optional[str]` - Key context for harmonic implications

#### Expected Outputs
```python
Dict:
  - input_melody: List[str]
  - primary_analysis:
    - type: "MELODY"
    - confidence: float
    - melodic_contour: str (contour description)
    - scale_context: str
    - harmonic_implications: str
    - phrase_analysis: str
  - intervallic_analysis:
    - intervals: List[str] (interval names)
    - largest_leap: str
    - melodic_range: str
    - directional_tendency: str
  - phrase_structure:
    - phrase_length: str
    - cadential_points: List[str]
    - motivic_content: str
```

---

### 4. `analyze_progression_multiple(chords, options)`
**Purpose**: Multi-perspective analysis with alternatives and suggestions

#### Input Formats
- Same as `analyze_chord_progression`

#### Analysis Modes
- **Comprehensive** - All analysis types with confidence ranking
- **Pedagogical Levels**:
  - `beginner` - Simple functional analysis
  - `intermediate` - Modal and secondary dominant analysis
  - `advanced` - Full chromatic analysis with alternatives

#### Expected Outputs
- Same as `analyze_chord_progression` but with guaranteed multiple perspectives
- Always includes bidirectional suggestions for improvement

---

## 🎭 Character & Emotional Analysis Functions

### 5. `analyze_progression_character(chords, key_context=None)`
**Purpose**: Emotional and character analysis of progressions

#### Input Formats
- **Primary**: `List[str]` - Chord progression
- `key_context: Optional[str]` - Key signature context

#### Expected Outputs
```python
ProgressionCharacter:
  - overall_mood: str
  - emotional_trajectory: str
  - emotional_keywords: List[str]
  - cadence_strength: float
```

---

### 6. `get_mode_emotional_profile(mode_name)`
**Purpose**: Emotional characteristics of musical modes

#### Input Formats
- **Primary**: `str` - Mode name (e.g., `"Dorian"`, `"Mixolydian"`)

#### Expected Outputs
```python
EmotionalProfile:
  - brightness: EmotionalBrightness (very_bright/bright/neutral/dark/very_dark)
  - energy: EmotionalEnergy (high/medium_high/medium/medium_low/low)
  - tension: EmotionalTension (very_tense/tense/moderate/relaxed/very_relaxed)
  - primary_emotions: List[str]
  - typical_genres: List[str]
```

---

### 7. `get_character_suggestions(target_emotion, brightness_level=0.5)`
**Purpose**: Suggestions for achieving specific emotional character

#### Expected Outputs
```python
CharacterSuggestion:
  - target_emotion: str
  - modification_tips: List[str]
  - suggested_modes: List[str]
  - chord_substitutions: List[str]
```

---

### 8. `get_modes_by_brightness(brightness_category)`
**Purpose**: Modes organized by brightness characteristics

#### Input Formats
- **Primary**: `str` - Categories: `"bright"`, `"neutral"`, `"dark"`

#### Expected Outputs
- `List[str]` - Mode names ordered by brightness

---

### 9. `describe_emotional_contour(progression)`
**Purpose**: Describe emotional movement through a progression

#### Expected Outputs
- `str` - Narrative description of emotional flow

---

## 🔧 Utility & Helper Functions

### 10. `analyze_scale_melody(notes, parent_key=None, melody=False)`
**Purpose**: Core scale/melody analysis engine

#### Input Modes
- **Scale Mode** (`melody=False`) - Pattern-based recognition
- **Melody Mode** (`melody=True`) - Tonal hierarchy analysis

#### Expected Outputs
```python
ScaleMelodyAnalysisResult:
  - classification: str
  - parent_scales: List[str]
  - modal_labels: Dict[str, str]
  - non_diatonic_pitches: List[str]
  - confidence: float
  - rationale: str
```

---

### 11. `get_interval_name(semitones)`
**Purpose**: Convert semitone distance to interval name

#### Input Formats
- **Primary**: `int` - Semitone distance (0-11)

#### Expected Outputs
- `str` - Interval name (e.g., `"Perfect Fifth"`, `"Major Third"`)

---

### 12. `get_modal_characteristics(mode_name)`
**Purpose**: Theoretical characteristics of modes

#### Expected Outputs
```python
ModalCharacteristics:
  - characteristic_degrees: List[str]
  - harmonic_implications: List[str]
  - typical_applications: List[str]
  - brightness: str
```

---

### 13. `describe_contour(contour_pattern)`
**Purpose**: Convert contour patterns to descriptive text

#### Input Formats
- **Primary**: `List[str]` - Contour codes (`["U", "D", "R"]` for Up/Down/Repeat)

#### Expected Outputs
- `str` - Human-readable contour description

---

## 🌐 API Endpoints (Backend Integration)

### REST API Functions

#### 1. `POST /api/analyze`
Maps to: `analyze_progression_multiple()`

#### 2. `POST /api/analyze-scale`
Maps to: `analyze_scale_notes()`

#### 3. `POST /api/analyze-melody`
Maps to: `analyze_melody_notes()`

#### 4. `POST /api/analyze/unified`
**Unified Analysis** - Combines harmonic + character + enhancement analysis
- **Input Types**: `progression`, `scale`, `melody`
- **Optional Features**: Character analysis, enhancement suggestions
- **Output**: Comprehensive multi-layer analysis

#### 5. `POST /api/analyze/character`
**Character-Only Analysis**
- **Analysis Types**: `progression`, `mode`, `mood`
- Maps to character analysis functions

#### 6. `POST /api/analyze/enhancements`
**Enhancement Suggestions**
- Uses bidirectional suggestion engine
- Provides key context and emotional enhancement suggestions

#### 7. `GET /api/reference/all`
**Complete Music Theory Reference**
- All modes, keys, scales, intervals
- Modal characteristics and chord mappings

#### 8. `GET /api/reference/modes`
**Modal Reference Data**
- Modal chord progressions
- Characteristic degrees and harmonic implications

#### 9. `GET /api/reference/scale/{scale_name}`
**Specific Scale Reference**
- Scale intervals, notes, characteristics
- Related modes and chord types

---

## 📊 Input Format Summary

| Function Type | Primary Input | Alternative Formats | Optional Parameters |
|---------------|---------------|-------------------|-------------------|
| **Chord Progression** | `List[str]` | `"C Am F G"` (string) | parent_key, pedagogical_level, confidence_threshold |
| **Scale Analysis** | `List[str]` | `"D E F G A B C"` | parent_key, melody (bool) |
| **Melody Analysis** | `List[str]` | Sequential notes only | parent_key |
| **Character Analysis** | Various | Depends on analysis type | target_emotion, brightness_level |
| **Reference Data** | `str` (identifiers) | Mode/scale names | None (read-only) |

---

## 🎯 Output Confidence Levels

| Analysis Type | Typical Range | High Confidence (>0.8) | Low Confidence (<0.5) |
|---------------|---------------|----------------------|---------------------|
| **Functional Harmony** | 0.6-0.95 | Clear I-IV-V progressions | Ambiguous tonality |
| **Modal Analysis** | 0.5-0.9 | Strong modal characteristics | Mixed modal signals |
| **Scale Recognition** | 0.7-1.0 | Exact pattern matches | Incomplete scales |
| **Character Analysis** | 0.3-0.8 | Strong emotional content | Neutral progressions |

---

## 🔄 Analysis Flow Hierarchy

```
1. INPUT PARSING
   ↓
2. FUNCTIONAL ANALYSIS (Primary)
   ├─ Roman Numeral Analysis
   ├─ Chord Function Identification
   └─ Cadence Detection
   ↓
3. MODAL ENHANCEMENT (If Applicable)
   ├─ Modal Characteristics Detection
   ├─ Parent Key Relationship
   └─ Modal Implications
   ↓
4. CHROMATIC ANALYSIS (Advanced)
   ├─ Secondary Dominants
   ├─ Borrowed Chords
   └─ Chromatic Mediants
   ↓
5. CHARACTER ANALYSIS (Optional)
   ├─ Emotional Profile
   ├─ Mood Analysis
   └─ Character Suggestions
   ↓
6. ENHANCEMENT SUGGESTIONS (Optional)
   ├─ Key Context Improvements
   ├─ Alternative Interpretations
   └─ Emotional Enhancements
```

---

## 📋 Constants & Reference Data

### Available Constants
- `ALL_MAJOR_KEYS` - All major key signatures
- `ALL_MINOR_KEYS` - All minor key signatures
- `ALL_MODES` - Complete modal system
- `MODAL_CHARACTERISTICS` - Mode characteristic degrees
- Scale systems, pitch class names, interval mappings
- Chord-scale relationships

### Reference Data Functions
- Complete music theory database access
- Modal progressions and chord mappings
- Scale patterns and intervallic structures
- Emotional profiles and character mappings

---

This comprehensive matrix covers all user-facing functionality with complete input/output specifications for both direct library usage and API integration.
