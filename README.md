# Harmonic Analysis Library 🎵

A comprehensive Python library that analyzes music the way musicians think about it - identifying chord progressions,
scales, modes, and harmonic relationships with detailed explanations of *why* it hears what it hears.

## 🆕 NEW: Advanced Pattern Matching Engine

**Revolutionary Update**: The library now features a sophisticated **pattern matching engine** that recognizes specific musical patterns in chord progressions with unprecedented accuracy and detail.

### What's New in Pattern Analysis
- **Pattern Recognition**: Identifies authentic cadences, Neapolitan cadences, circle of fifths progressions, jazz turnarounds, and 40+ other musical patterns
- **Event-Based Detection**: Analyzes bass motion, voice leading, and harmonic texture to validate pattern matches
- **Confidence Scoring**: Each pattern match includes confidence scores and detailed evidence
- **Profile-Aware**: Classical, jazz, and pop patterns are filtered by musical style context
- **Replaces Legacy Analysis**: The new pattern engine supersedes the older `analyze_chord_progression` system

### Quick Pattern Analysis Example

```python
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

async def analyze_patterns():
    service = PatternAnalysisService()

    # Classic authentic cadence
    result = await service.analyze_with_patterns(
        chord_symbols=['F', 'G7', 'C'],
        profile='classical',
        key_hint='C major'
    )

    print("Pattern matches found:")
    for match in result['pattern_matches']:
        print(f"  - {match['name']}: {match['score']:.2f} confidence")
        print(f"    Evidence: {match['evidence']}")

    # Output:
    # - Authentic Cadence (Classical): 0.95 confidence
    #   Evidence: Perfect cadence V7→I with strong resolution
```

### 🔄 Migration from Legacy Analysis

**Important**: If you were using the previous `analyze_chord_progression()` function, it's now **deprecated** in favor of the new pattern analysis system:

```python
# ❌ OLD WAY (deprecated)
from harmonic_analysis import analyze_chord_progression
result = await analyze_chord_progression(['C', 'Am', 'F', 'G'])

# ✅ NEW WAY (recommended)
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService
service = PatternAnalysisService()
result = await service.analyze_with_patterns(
    chord_symbols=['C', 'Am', 'F', 'G'],
    profile='classical',
    best_cover=False,
    key_hint='C major'
)
```

The new system provides:
- **More accurate pattern recognition** with evidence-based matching
- **Style-aware analysis** (classical/jazz/pop profiles)
- **Detailed confidence scoring** for each detected pattern
- **Event-based validation** using bass motion and harmonic texture
- **Future-proof architecture** designed for advanced musical analysis

## What This Library Does (For Musicians)

This library listens to your chord progressions, scales, and melodies and tells you:

- **What key you're in** and how confident it is about that
- **The function of each chord** (tonic, dominant, subdominant, etc.) with full inversion analysis
- **What mode you might be using** (Dorian, Mixolydian, Phrygian, etc.)
- **Advanced harmonic techniques** you're employing (secondary dominants, borrowed chords, chromatic mediants)
- **Chord inversions with proper figured bass notation** (⁶, ⁶⁴, ⁴²)
- **Multiple valid interpretations** when your music is ambiguous (which is often!)
- **Chromatic harmony analysis** including tonicization, modal mixture, and voice leading
- **Emotional character** of your progressions and scales
- **Intelligent key suggestions** that consider both harmonic function and context
- **Perfect bidirectional conversion** between chord symbols and Roman numerals

Think of it as having three music theory professors analyze your work simultaneously - one specializing in classical harmony, one in modal jazz, and one in chromatic/contemporary techniques - each explaining their reasoning with evidence-based analysis.

## Installation

```bash
pip install harmonic-analysis
```

## 📁 Project Structure

```
harmonic-analysis/
│
├── 📁 src/harmonic_analysis/           # Core library source code
│   ├── __init__.py                     # Main library exports and API
│   ├── analysis_types.py               # Analysis result type definitions
│   ├── scales.py                       # Scale and mode definitions
│   │
│   ├── 📁 api/                         # High-level public API
│   │   ├── analysis.py                 # Main analysis functions
│   │   ├── character.py                # Musical character analysis
│   │   └── musical_data.py             # Musical data structures
│   │
│   ├── 📁 core/                        # Core analysis engines
│   │   ├── functional_harmony.py       # Roman numeral & functional analysis
│   │   ├── enhanced_modal_analyzer.py  # Modal analysis (Dorian, Mixolydian, etc.)
│   │   ├── chromatic_analysis.py       # Advanced chromatic harmony
│   │   ├── scale_melody_analysis.py    # Scale and melody analysis
│   │   │
│   │   └── 📁 pattern_engine/          # 🆕 NEW: Pattern matching system
│   │       ├── matcher.py              # Core pattern matching logic
│   │       ├── low_level_events.py     # Bass motion & voice leading detection
│   │       ├── token_converter.py      # Analysis → pattern tokens
│   │       ├── patterns.json           # Pattern definitions (40+ patterns)
│   │       └── glossary_service.py     # Musical term definitions
│   │
│   ├── 📁 services/                    # High-level analysis services
│   │   ├── pattern_analysis_service.py # 🆕 NEW: Main pattern analysis API
│   │   ├── multiple_interpretation_service.py # Multiple analysis perspectives
│   │   ├── bidirectional_suggestion_engine.py # Key suggestion system
│   │   └── algorithmic_suggestion_engine.py   # Analysis optimization
│   │
│   ├── 📁 specialized/                 # Specialized analysis modules
│   │   ├── algorithms.py               # Advanced analysis algorithms
│   │   ├── chromatic.py                # Chromatic harmony tools
│   │   ├── midi.py                     # MIDI integration utilities
│   │   └── theory.py                   # Music theory constants & utilities
│   │
│   └── 📁 utils/                       # Utility functions
│       ├── chord_parser.py             # Chord symbol parsing
│       ├── chord_logic.py              # Chord analysis logic
│       ├── chord_inversions.py         # Inversion analysis
│       ├── roman_numeral_converter.py  # Roman numeral conversion
│       ├── scales.py                   # Scale utilities
│       └── music_theory_constants.py   # Constants and mappings
│
├── 📁 tests/                           # Comprehensive test suite (1500+ tests)
│   ├── test_pattern_engine.py          # 🆕 Pattern engine tests
│   ├── test_comprehensive_multi_layer_validation.py # 427 sophisticated tests
│   ├── test_inversion_regression.py    # Bidirectional inversion tests
│   ├── test_edge_case_behavior.py      # Edge case handling
│   ├── test_chromatic_analysis.py      # Chromatic harmony tests
│   ├── test_enhanced_modal_analyzer.py # Modal analysis tests
│   └── unit/test_chord_logic.py        # Unit tests for core logic
│
├── 📁 scripts/                         # Development and maintenance scripts
│   ├── quality_check.py                # Linting, typing, and test runner
│   ├── confidence_calibration_analysis.py # Confidence scoring validation
│   └── music_expert_review.py          # Expert review validation
│
├── 📁 docs/                            # Documentation
│   ├── API_GUIDE.md                    # Complete API documentation
│   ├── ARCHITECTURE.md                 # System architecture overview
│   ├── TESTING.md                      # Testing strategy and guides
│   └── TROUBLESHOOTING.md              # Common issues and solutions
│
├── 📁 .local_docs/                     # Development documentation
│   ├── music-alg.md                    # 🆕 Pattern engine implementation guide
│   ├── PYPI_SETUP.md                   # Package publishing guide
│   └── music_alg/                      # Pattern engine development docs
│
├── 📁 examples/                        # Usage examples
│   └── character_analysis_demo.py      # Modal character analysis demo
│
├── 📁 demo/                            # Interactive demo application
│   ├── frontend/                       # React frontend demo
│   └── backend/                        # FastAPI backend demo
│
├── 📄 test_stage_b.py                  # 🆕 Pattern engine Stage B tests
├── 📄 debug_stage_b.py                 # 🆕 Pattern debugging tools
├── 📄 pyproject.toml                   # Project configuration
├── 📄 requirements.txt                 # Production dependencies
├── 📄 requirements-dev.txt             # Development dependencies
└── 📄 README.md                        # This file
```

### Key Architecture Highlights

#### 🎯 Pattern Engine (NEW)
- **Location**: `src/harmonic_analysis/core/pattern_engine/`
- **Purpose**: Recognizes specific musical patterns (cadences, progressions, sequences)
- **Features**: Event-based detection, confidence scoring, style profiles
- **Status**: Stage A & B complete, Stage C (voice-leading) planned

#### 🧠 Multi-Engine Analysis
- **Functional**: Roman numerals, cadences, traditional harmony
- **Modal**: Mode detection, modal interchange, characteristic tones
- **Chromatic**: Secondary dominants, borrowed chords, advanced harmony
- **Pattern**: Specific musical idioms and compositional techniques

#### 🔄 Bidirectional System
- **Analysis → Patterns**: Detects patterns in chord progressions
- **Suggestions**: Recommends optimal analysis approaches
- **Validation**: Cross-validates results across multiple engines

## Quick Start for Musicians

### Analyzing Chord Progressions

```python
import asyncio
from harmonic_analysis import analyze_chord_progression

async def analyze_my_progression():
    # Classic I-vi-IV-V progression
    result = await analyze_chord_progression(['C', 'Am', 'F', 'G'])

    print(f"What it is: {result.primary_analysis.analysis}")
    # Output: "Functional progression in C major: I - vi - IV - V"

    print(f"Confidence: {result.primary_analysis.confidence:.0%}")
    # Output: "Confidence: 75%"

    print(f"Roman numerals: {result.primary_analysis.roman_numerals}")
    # Output: "Roman numerals: ['I', 'vi', 'IV', 'V']"

asyncio.run(analyze_my_progression())
```

### Analyzing Scales

When you give the library a set of notes, it tells you what scales contain those notes:

```python
from harmonic_analysis import analyze_scale

async def what_scale_is_this():
    # The notes of D Dorian
    result = await analyze_scale(['D', 'E', 'F', 'G', 'A', 'B', 'C'])

    print(result.parent_scales)
    # Output: ['C major', 'F major']
    # (D Dorian uses the notes of C major but centers on D)

    print(result.modal_labels)
    # Output: {'D': 'D Dorian', 'G': 'G Mixolydian', ...}
    # (Shows what mode each note would create as a tonic)

asyncio.run(what_scale_is_this())
```

### Analyzing Melodies

Melodies are special - the library tries to figure out what note feels like "home":

```python
from harmonic_analysis import analyze_melody

async def analyze_my_melody():
    # A melody that emphasizes D within C major scale
    melody = ['D', 'E', 'F', 'G', 'A', 'C', 'B', 'A', 'G', 'F', 'E', 'D']
    result = await analyze_melody(melody)

    print(f"Suggested tonic: {result.suggested_tonic}")
    # Output: "Suggested tonic: D"
    # (The melody centers around D)

    print(f"Confidence: {result.confidence:.0%}")
    # Output: "Confidence: 78%"

    print(f"This creates: {result.modal_labels.get('D')}")
    # Output: "This creates: D Dorian"

asyncio.run(analyze_my_melody())
```

### Analyzing Chord Inversions 🎼

The library provides comprehensive inversion analysis with proper figured bass notation:

```python
import asyncio
from harmonic_analysis import analyze_chord_progression, AnalysisOptions

async def analyze_inversions():
    # Progression with multiple inversions in F major
    chords = ['D', 'Gm/Bb', 'D/A', 'Gm', 'F/C', 'C', 'F']

    result = await analyze_chord_progression(
        chords,
        AnalysisOptions(parent_key='F major')
    )

    print("Analysis:", result.primary_analysis.analysis)
    # Output: "Functional progression with secondary dominants"

    print("Roman numerals:", result.primary_analysis.roman_numerals)
    # Output: ['V/ii', 'ii⁶', 'V/ii⁶⁴', 'ii', 'I⁶⁴', 'V', 'I']

    # Perfect bidirectional conversion
    from harmonic_analysis.utils.roman_numeral_converter import convert_roman_numerals_to_chords

    romans_str = " ".join(result.primary_analysis.roman_numerals)
    reconstructed = convert_roman_numerals_to_chords(romans_str, "F major")
    print("Reconstructed chords:", reconstructed)
    # Output: ['D', 'Gm/Bb', 'D/A', 'Gm', 'F/C', 'C', 'F']
    # Perfect round-trip conversion preserves all inversions!

asyncio.run(analyze_inversions())
```

**Inversion Notation Used:**
- **⁶** = First inversion (third in bass)
- **⁶⁴** = Second inversion (fifth in bass)
- **⁴²** = Third inversion of seventh chords (seventh in bass)

The library provides **perfect bidirectional conversion** - you can go from chord symbols → Roman numerals → chord symbols with complete inversion preservation.

## How the Analysis Works (The Musical Logic)

### Stage 1: Chord Parsing 🎸

First, the library understands what you typed:

- `"Cmaj7"` → C major 7th chord (C-E-G-B)
- `"Dm"` → D minor chord (D-F-A)
- `"G7"` → G dominant 7th (G-B-D-F)
- Handles slash chords (`"C/E"`), extensions (`"Am9"`), alterations (`"F#dim"`)

### Stage 2: Parallel Analysis 🔍

Three specialized "musicians" analyze your progression simultaneously:

#### The Functional Harmony Analyst

Thinks in Roman numerals and classical harmony:

```python
# Example: ['C', 'Am', 'F', 'G']
# Sees: I - vi - IV - V in C major
# Identifies: Authentic cadence (V → I)
# Confidence boosted by: Clear tonal center, strong cadence
```

#### The Modal Analyst

Looks for modal characteristics and color tones:

```python
# Example: ['G', 'F', 'C', 'G']
# Sees: I - bVII - IV - I in G Mixolydian
# Identifies: Flat-7 characteristic of Mixolydian
# Confidence boosted by: Modal interchange, characteristic tones
```

#### The Chromatic Analyst

Spots advanced harmonic techniques:

```python
# Example: ['C', 'A7', 'Dm', 'G7', 'C']
# Sees: I - V7/ii - ii - V7 - I
# Identifies: Secondary dominant (A7 is V of Dm)
# Confidence boosted by: Chromatic voice leading
```

### Stage 3: Evidence Collection 📊

Each analyst gathers evidence for their interpretation:

```python
# Evidence types with examples:
CADENTIAL:   "Authentic cadence (G7 → C)" - strength: 0.9
STRUCTURAL:  "Tonic at beginning and end" - strength: 0.6
INTERVALLIC: "Contains bVII chord" - strength: 0.7
HARMONIC:    "Clear functional progression" - strength: 0.8
CONTEXTUAL:  "Modal characteristics present" - strength: 0.65
```

### Stage 4: Confidence Calculation 🎯

The library weighs all evidence to determine confidence:

```python
# High confidence (>80%):
['C', 'F', 'G', 'C']  # Crystal clear I-IV-V-I

# Medium confidence (60-80%):
['Am', 'F', 'C', 'G']  # Could be A minor or C major

# Multiple interpretations:
['Dm', 'G', 'C']  # ii-V-I in C? Or i-IV-bVII in D Dorian?
```

### Stage 5: Generating Results 📝

The library explains its reasoning in musical terms:

```python
result = await analyze_chord_progression(['Dm', 'G', 'C'])

# Primary interpretation:
"Functional progression in C major: ii - V - I"
# Why: Strong ii-V-I cadence, clear tonal resolution

# Alternative interpretation (if confidence is close):
"D Dorian modal progression: i - IV - bVII"
# Why: Dm as tonic, characteristic modal motion
```

## Multiple Interpretations & Advanced Harmonic Analysis 🎭

Music is often ambiguous, and good musicians can hear the same progression multiple ways. This library embraces that reality by providing **multiple valid interpretations** when appropriate.

### Getting All Interpretations

```python
import asyncio
from harmonic_analysis import analyze_progression_multiple, AnalysisOptions

async def explore_interpretations():
    # This progression can be heard multiple ways
    chords = ['Am', 'F', 'C', 'G']

    # Request multiple interpretations with low threshold
    options = AnalysisOptions(
        confidence_threshold=0.3,  # Show more alternatives
        max_alternatives=5         # Up to 5 alternatives
    )

    result = await analyze_progression_multiple(chords, options)

    print(f"Primary interpretation: {result.primary_analysis.type.value}")
    print(f"  {result.primary_analysis.analysis}")
    print(f"  Confidence: {result.primary_analysis.confidence:.0%}")

    print(f"\nAlternative interpretations ({len(result.alternative_analyses)}):")
    for i, alt in enumerate(result.alternative_analyses, 1):
        print(f"  {i}. {alt.type.value}: {alt.analysis}")
        print(f"     Confidence: {alt.confidence:.0%}")

asyncio.run(explore_interpretations())
```

**Output:**
```
Primary interpretation: functional
  Functional progression in C major: vi - IV - I - V
  Confidence: 70%

Alternative interpretations (2):
  1. modal: A Aeolian progression with borrowed major chords
     Confidence: 65%
  2. chromatic: Chromatic progression featuring borrowed chords (F)
     Confidence: 55%
```

### Chromatic Harmony Analysis 🎨

The library detects and analyzes advanced chromatic techniques:

```python
async def analyze_chromatic_harmony():
    # Progression with secondary dominants
    chords = ['C', 'A7', 'Dm', 'G7', 'C']

    result = await analyze_progression_multiple(chords)

    if result.primary_analysis.type.value == "chromatic":
        print("Chromatic elements detected:")

        # Secondary dominants
        if result.primary_analysis.secondary_dominants:
            print("\n🎯 Secondary Dominants:")
            for sd in result.primary_analysis.secondary_dominants:
                print(f"  {sd['chord']} → {sd['target']}")
                print(f"  Function: {sd['roman_numeral']}")

        # Borrowed chords
        if result.primary_analysis.borrowed_chords:
            print("\n🎨 Borrowed Chords:")
            for bc in result.primary_analysis.borrowed_chords:
                print(f"  {bc['chord']} borrowed from {bc['borrowed_from']}")

        # Chromatic mediants
        if result.primary_analysis.chromatic_mediants:
            print("\n✨ Chromatic Mediants:")
            for cm in result.primary_analysis.chromatic_mediants:
                print(f"  {cm['chord']}: {cm['relationship']}")

asyncio.run(analyze_chromatic_harmony())
```

**Output:**
```
Chromatic elements detected:

🎯 Secondary Dominants:
  A7 → Dm
  Function: V7/ii

The A7 acts as the dominant of Dm (V of ii), creating a brief tonicization before returning to the main key.
```

### Understanding the Three Analysis Types

The library uses three complementary analytical approaches:

#### 1. **Functional Analysis** (Traditional Harmony)
- Roman numeral analysis (I, ii, V7, etc.)
- Identifies tonic, dominant, subdominant functions
- Recognizes cadences and voice leading
- Best for: Classical, pop, folk music

#### 2. **Modal Analysis** (Modal Harmony)
- Identifies modes (Dorian, Mixolydian, etc.)
- Detects characteristic modal intervals
- Finds parent scales and modal interchange
- Best for: Jazz, rock, world music

#### 3. **Chromatic Analysis** (Advanced Harmony)
- Secondary dominants (V/V, V7/ii, etc.)
- Borrowed chords and modal mixture
- Chromatic mediants and voice leading
- Best for: Jazz, classical, progressive music

### Real-World Examples

```python
async def analyze_real_progressions():
    progressions = [
        # Pop: vi-IV-I-V
        (['Am', 'F', 'C', 'G'], "Pop progression"),

        # Jazz: ii-V-I with alterations
        (['Dm7', 'G7alt', 'Cmaj7'], "Jazz ii-V-I"),

        # Modal: i-bVII-IV-i (Dorian)
        (['Dm', 'C', 'G', 'Dm'], "Dorian vamp"),

        # Chromatic: Circle of fifths with secondary dominants
        (['C', 'E7', 'Am', 'D7', 'G', 'C'], "Chromatic circle"),
    ]

    for chords, description in progressions:
        result = await analyze_progression_multiple(chords)
        print(f"\n{description}: {' - '.join(chords)}")
        print(f"  Primary: {result.primary_analysis.type.value}")
        print(f"  Analysis: {result.primary_analysis.analysis}")
        print(f"  Alternatives: {len(result.alternative_analyses)}")

asyncio.run(analyze_real_progressions())
```

## Musical Character and Emotional Analysis 🎨

The library provides detailed **character analysis** for scales and progressions, describing their emotional and aesthetic qualities:

### Modal Character Analysis

```python
from harmonic_analysis import get_modal_characteristics

# Get complete character profile for any mode
dorian_character = get_modal_characteristics("Dorian")

print(f"Name: {dorian_character.name}")                    # "Dorian"
print(f"Brightness: {dorian_character.brightness}")        # "neutral"
print(f"Character: {dorian_character.harmonic_implications[0]}")
# "Natural 6th creates brighter minor sound"

print(f"Applications: {dorian_character.typical_applications}")
# ["Jazz and folk music", "Celtic and medieval music", ...]
```

### Musical Brightness Classification

The library classifies all modes by emotional brightness:

```python
from harmonic_analysis import MODAL_CHARACTERISTICS

# Get all bright, neutral, and dark modes
bright_modes = [name for name, chars in MODAL_CHARACTERISTICS.items()
                if chars.brightness == "bright"]
# Result: ["Ionian", "Lydian", "Mixolydian"] - happy, uplifting sounds

neutral_modes = [name for name, chars in MODAL_CHARACTERISTICS.items()
                 if chars.brightness == "neutral"]
# Result: ["Dorian", "Phrygian Dominant"] - balanced, complex emotions

dark_modes = [name for name, chars in MODAL_CHARACTERISTICS.items()
              if chars.brightness == "dark"]
# Result: ["Phrygian", "Aeolian", "Locrian"] - sad, mysterious, tense
```

### Emotional Context in Analysis

Modal analysis includes character descriptions:

```python
# Analyze a modal progression
result = await analyze_progression_multiple(['Em', 'F', 'Em'])

# Get detected mode
if result.primary_analysis.type == 'modal':
    mode_name = result.primary_analysis.mode  # "E Phrygian"

    # Get character information
    if "Phrygian" in mode_name:
        phrygian_info = get_modal_characteristics("Phrygian")
        print(f"Character: {phrygian_info.brightness}")  # "dark"
        print(f"Implications: {phrygian_info.harmonic_implications}")
        # ["Flat 2nd creates exotic, Spanish flavor", "Dark minor character", ...]
```

### Character-Based Music Recommendations

```python
# Find modes by emotional quality
from harmonic_analysis import MODAL_CHARACTERISTICS

def get_modes_by_character(desired_brightness):
    """Get all modes matching emotional character"""
    return [
        {
            "mode": name,
            "description": chars.harmonic_implications[0],
            "applications": chars.typical_applications[0]
        }
        for name, chars in MODAL_CHARACTERISTICS.items()
        if chars.brightness == desired_brightness
    ]

# Get happy/uplifting modes
bright_modes = get_modes_by_character("bright")
# Result includes: Ionian ("Strong tonal center"), Lydian ("bright, dreamy quality")

# Get sad/melancholic modes
dark_modes = get_modes_by_character("dark")
# Result includes: Aeolian ("Classic minor scale character"), Phrygian ("Dark minor character")
```

### Melodic Character Analysis

The library also analyzes melodic contour and emotional character:

```python
from harmonic_analysis import describe_contour

# Analyze melodic shape and character
contour = ['U', 'U', 'D', 'D', 'U']  # Up, Up, Down, Down, Up
character_description = describe_contour(contour)
# "Rising then falling with final lift - creates tension and resolution"

# Character implications:
# - Rising contours: Building energy, excitement, hope
# - Falling contours: Relaxation, sadness, resolution
# - Arch shapes: Classical, balanced, satisfying
# - Zigzag patterns: Playful, energetic, unstable
```

## Understanding the Output

### For Chord Progressions

```python
result = await analyze_chord_progression(['C', 'Am', 'Dm', 'G'])

# What you get:
result.primary_analysis.type         # 'functional', 'modal', or 'chromatic'
result.primary_analysis.analysis     # Human-readable explanation
result.primary_analysis.confidence   # 0.0 to 1.0 (like a percentage)
result.primary_analysis.roman_numerals  # ['I', 'vi', 'ii', 'V']
result.primary_analysis.key_signature   # 'C major'
result.primary_analysis.cadences        # Detected cadences
result.primary_analysis.evidence        # Why it thinks what it thinks

# Character information (for modal analysis)
result.primary_analysis.modal_characteristics  # Character descriptions
```

### For Scales and Melodies

```python
# Scale analysis tells you what scales contain your notes
scale_result = await analyze_scale(['D', 'E', 'F', 'G', 'A', 'B', 'C'])

scale_result.parent_scales     # ['C major', 'F major']
scale_result.modal_labels      # {'D': 'D Dorian', 'G': 'G Mixolydian', ...}
scale_result.classification    # 'diatonic', 'modal_borrowing', or 'modal_candidate'

# Melody analysis adds tonic detection
melody_result = await analyze_melody(['C', 'D', 'E', 'G', 'E', 'D', 'C'])

melody_result.suggested_tonic  # 'C' - what note feels like home
melody_result.confidence       # 0.85 - how sure about the tonic
```

### When You Get `suggested_tonic` (and When You Don't)

**You GET a suggested tonic when:**

- Analyzing a **melody** (sequence of single notes meant to be heard in order)
- The library detects emphasis on particular notes through:
    - Frequency (how often a note appears)
    - Position (especially the final note)
    - Melodic patterns (like returning to a note after leaps)

**You DON'T get a suggested tonic when:**

- Analyzing a **scale** (just a collection of notes without melodic context)
- Analyzing **chord progressions** (the tonic is determined differently)
- The melody is too ambiguous or short

## 💡 Intelligent Bidirectional Key Suggestions

**New Feature**: The library intelligently suggests when to **add**, **remove**, or **change** parent keys to optimize
your analysis results. This breakthrough bidirectional system helps you get the best possible harmonic analysis.

### How the Suggestion System Works

The library analyzes your progression **with** and **without** key context, then uses algorithmic scoring to determine
if a parent key would help or hurt your analysis:

```python
# Key Relevance Scoring (0.0 - 1.0):
# • Roman numeral improvement (30% weight)
# • Confidence improvement (20% weight)
# • Analysis type improvement (20% weight)
# • Pattern clarity improvement (30% weight)
```

### Type 1: "Add Key" Suggestions

When no parent key is provided but one would unlock better analysis:

```python
import asyncio
from harmonic_analysis import analyze_chord_progression, AnalysisOptions

async def add_key_example():
    # Classic ii-V-I progression without key context
    progression = ['Dm7', 'G7', 'Cmaj7']
    result = await analyze_chord_progression(progression)

    # Initial analysis (likely modal)
    print(f"Without key: {result.primary_analysis.analysis}")
    # → "D Dorian modal progression"
    print(f"Roman numerals: {result.primary_analysis.roman_numerals}")
    # → [] (empty - modal analysis provides no Roman numerals)
    print(f"Confidence: {result.primary_analysis.confidence:.0%}")
    # → 77%

    # Check for "add key" suggestions
    if result.suggestions and result.suggestions.parent_key_suggestions:
        suggestion = result.suggestions.parent_key_suggestions[0]
        print(f"\n✅ ADD KEY suggestion found!")
        print(f"   Try: parent_key='{suggestion.suggested_key}'")
        print(f"   Reason: {suggestion.reason}")
        print(f"   Benefit: {suggestion.potential_improvement}")
        print(f"   Confidence: {suggestion.confidence:.0%}")
        # → "Try: parent_key='C major'"
        # → "Reason: Contains ii-V-I progression"
        # → "Benefit: Roman numeral analysis and functional relationships"
        # → "Confidence: 78%"

        # Follow the suggestion
        better_result = await analyze_chord_progression(
            progression,
            AnalysisOptions(parent_key=suggestion.suggested_key)
        )
        print(f"\n🎯 With suggested key:")
        print(f"   Analysis: {better_result.primary_analysis.analysis}")
        print(f"   Roman numerals: {better_result.primary_analysis.roman_numerals}")
        print(f"   Type: {better_result.primary_analysis.type.value}")
        # → "Functional progression: ii7 - V7 - I7"
        # → "['ii7', 'V7', 'I7']"
        # → "functional"
    else:
        print("❌ No 'add key' suggestions")

asyncio.run(add_key_example())
```

### Type 2: "Remove Key" Suggestions

When a parent key is provided but actually makes analysis worse:

```python
async def remove_key_example():
    # Jazz progression with WRONG parent key
    jazz_progression = ['A', 'E/G#', 'B7sus4/F#', 'E', 'A/C#', 'G#m/B', 'F#m/A', 'E/G#']

    # Force wrong key (C major doesn't fit this progression)
    result = await analyze_chord_progression(
        jazz_progression,
        AnalysisOptions(parent_key='C major')
    )

    print(f"With wrong key (C major):")
    print(f"   Analysis: {result.primary_analysis.analysis}")
    print(f"   Type: {result.primary_analysis.type.value}")
    print(f"   Roman numerals: {result.primary_analysis.roman_numerals}")
    print(f"   Confidence: {result.primary_analysis.confidence:.0%}")
    # → "E Dorian modal progression"
    # → "modal"
    # → []
    # → 84%

    # Check for "remove key" suggestions
    if result.suggestions and result.suggestions.unnecessary_key_suggestions:
        suggestion = result.suggestions.unnecessary_key_suggestions[0]
        print(f"\n⚠️  REMOVE KEY suggestion found!")
        print(f"   Remove: '{result.input_options.parent_key}'")
        print(f"   Reason: {suggestion.reason}")
        # → "Remove: 'C major'"
        # → "Reason: Parent key doesn't improve analysis confidence"

        # Compare with no key
        no_key_result = await analyze_chord_progression(jazz_progression)
        print(f"\n🎯 Without the problematic key:")
        print(f"   Analysis: {no_key_result.primary_analysis.analysis}")
        print(f"   Type: {no_key_result.primary_analysis.type.value}")
        print(f"   Roman numerals: {no_key_result.primary_analysis.roman_numerals}")
        print(f"   Confidence: {no_key_result.primary_analysis.confidence:.0%}")
        # → "Functional progression: I - V⁶ - V7/V⁶ - V..."
        # → "functional"
        # → ['I', 'V⁶', 'V7/V⁶', 'V', 'I⁶', 'vii⁶', 'vi⁶', 'V⁶']
        # → 86% (HIGHER than with wrong key!)
    else:
        print("✅ No 'remove key' suggestions (key is helpful)")

asyncio.run(remove_key_example())
```

### Type 3: "Change Key" Suggestions

When a different parent key would work better than the current one:

```python
async def change_key_example():
    # Ambiguous progression with suboptimal key
    progression = ['Am', 'F', 'C', 'G']

    # Provide A minor key (works, but C major might be better)
    result = await analyze_chord_progression(
        progression,
        AnalysisOptions(parent_key='A minor')
    )

    print(f"With A minor key:")
    print(f"   Analysis: {result.primary_analysis.analysis}")
    print(f"   Confidence: {result.primary_analysis.confidence:.0%}")

    # Check for "change key" suggestions
    if result.suggestions and result.suggestions.key_change_suggestions:
        suggestion = result.suggestions.key_change_suggestions[0]
        print(f"\n🔄 CHANGE KEY suggestion found!")
        print(f"   Change to: '{suggestion.suggested_key}'")
        print(f"   Reason: {suggestion.reason}")
        print(f"   Confidence: {suggestion.confidence:.0%}")
        # → "Change to: 'C major'"
        # → "Reason: Provides clearer functional analysis"
        # → "Confidence: 82%"
    else:
        print("✅ No 'change key' suggestions (current key is optimal)")

asyncio.run(change_key_example())
```

### Complete Suggestion Logic Flow

The system makes decisions using this logic tree:

```python
# For any chord progression:
if no_parent_key_provided:
    if adding_key_improves_analysis():
        return "ADD KEY" suggestions
    else:
        return no_suggestions  # Analysis is fine as-is

elif parent_key_provided:
    without_key_score = analyze_without_key()
    with_key_score = analyze_with_key()
    alternative_keys = test_related_keys()

    if with_key_score < without_key_score:
        return "REMOVE KEY" suggestions
    elif any(alt > with_key_score for alt in alternative_keys):
        return "CHANGE KEY" suggestions
    else:
        return no_suggestions  # Current key is optimal
```

### What Triggers Each Suggestion Type

**ADD KEY suggestions triggered by:**

- ii-V-I patterns without Roman numeral analysis
- vi-IV-I-V progressions defaulting to modal analysis
- Modal primary analysis when functional would provide Roman numerals
- Common jazz/pop patterns that benefit from key context

**REMOVE KEY suggestions triggered by:**

- Parent key forcing modal analysis when functional works better without it
- Key providing no confidence improvement (<5%)
- Key eliminating Roman numerals that were available without it
- Wrong key making analysis less accurate

**CHANGE KEY suggestions triggered by:**

- Related keys scoring significantly higher (>15% confidence improvement)
- Alternative keys unlocking Roman numeral analysis
- Better pattern recognition with different tonal centers

### Understanding Suggestion Confidence

Each suggestion comes with its own confidence score:

```python
suggestion = result.suggestions.parent_key_suggestions[0]
print(f"Suggestion confidence: {suggestion.confidence:.0%}")

# Confidence levels:
# 85-100%: Very confident this key will help
# 70-84%:  Likely beneficial
# 55-69%:  Worth trying
# Below 55%: Filtered out (not shown)
```

### No Suggestions = Good Analysis

When you see no suggestions, it means:

- Your current analysis is already optimal
- Adding/removing/changing keys wouldn't improve results
- The system is confident in the current interpretation

```python
result = await analyze_chord_progression(['C', 'F', 'G', 'C'])
# Strong I-IV-V-I progression needs no suggestions!

if not (result.suggestions and any([
    result.suggestions.parent_key_suggestions,
    result.suggestions.unnecessary_key_suggestions,
    result.suggestions.key_change_suggestions
])):
    print("✅ No suggestions needed - analysis is already optimal!")
```

## Advanced Examples for Different Musical Styles

### Jazz Progressions

```python
# A ii-V-I with extensions
jazz = await analyze_chord_progression(['Dm7', 'G7', 'Cmaj7'])
# Recognizes: "Jazz ii7-V7-Imaj7 cadence in C major"

# Modal jazz
modal_jazz = await analyze_chord_progression(['Dm7', 'Em7', 'Dm7', 'Em7'])
# Recognizes: "D Dorian modal vamp: i7 - ii7"
```

### Rock and Pop

```python
# Classic rock progression
rock = await analyze_chord_progression(['C', 'G', 'Am', 'F'])
# Recognizes: "I - V - vi - IV pop progression in C major"

# Power chord riff
power = await analyze_chord_progression(['E5', 'G5', 'A5', 'E5'])
# Recognizes: "Modal power chord progression suggesting E minor"
```

### Classical and Baroque

```python
# Circle of fifths
classical = await analyze_chord_progression(['C', 'Am', 'Dm', 'G', 'C'])
# Recognizes: "Circle of fifths progression: I - vi - ii - V - I"

# Deceptive cadence
deceptive = await analyze_chord_progression(['C', 'F', 'G', 'Am'])
# Recognizes: "Deceptive cadence (V → vi) in C major"
```

### Modal and Folk Music

```python
# Dorian mode
dorian = await analyze_chord_progression(['Dm', 'G', 'Dm', 'C'])
# Recognizes: "D Dorian: i - IV - i - bVII"

# Mixolydian (common in rock/folk)
mixo = await analyze_chord_progression(['G', 'F', 'C', 'G'])
# Recognizes: "G Mixolydian: I - bVII - IV - I"
```

## Understanding Confidence Scores

The library's confidence reflects how clearly your music fits established patterns:

### High Confidence (80-100%)

```python
['C', 'F', 'G', 'C']  # Textbook I-IV-V-I
```

**Why:** Clear tonal center, strong cadence, no ambiguity

### Medium Confidence (60-80%)

```python
['Am', 'F', 'C', 'G']  # vi-IV-I-V? Or i-VI-III-VII?
```

**Why:** Could be C major or A minor, both make sense

### Lower Confidence (40-60%)

```python
['Cmaj7', 'Fmaj7#11', 'Bm7b5', 'E7alt']  # Complex jazz
```

**Why:** Highly chromatic, multiple valid interpretations

### Multiple Interpretations

When confidence levels are close, you get alternatives:

```python
result = await analyze_chord_progression(['Dm', 'G', 'C'])
# Primary: "ii-V-I in C major" (confidence: 75%)
# Alternative: "i-IV-bVII in D Dorian" (confidence: 68%)
```

## Special Musical Considerations

### The Library Understands Context

```python
# Same chords, different context
options_major = AnalysisOptions(parent_key="C major")
options_minor = AnalysisOptions(parent_key="A minor")

chords = ['Am', 'Dm', 'G', 'C']

# In C major context: vi - ii - V - I
result1 = await analyze_chord_progression(chords, options_major)

# In A minor context: i - iv - bVII - bIII
result2 = await analyze_chord_progression(chords, options_minor)
```

### It Recognizes Musical Idioms

The library knows common patterns:

- **Cadences**: Perfect authentic, plagal, deceptive, half
- **Progressions**: Circle of fifths, descending thirds, chromatic bass lines
- **Modal characteristics**: bVII in Mixolydian, #IV in Lydian, etc.
- **Jazz conventions**: ii-V-I, tritone substitutions, modal interchange

### It Handles Edge Cases Gracefully

```python
# Single chord - lower confidence
await analyze_chord_progression(['C'])
# Result: "Single chord: C major" (confidence: ~45%)

# Ambiguous progression
await analyze_chord_progression(['C', 'Dm', 'Eb', 'F'])
# Provides multiple interpretations with reasoning
```

## For Developers: Under the Hood

### The Three-Layer Architecture

```python
# 1. Input Layer - Parse and validate
chords = parse_chord_symbols(['Cmaj7', 'Dm7', 'G7'])

# 2. Analysis Layer - Three parallel engines
functional_result = functional_analyzer.analyze(chords)
modal_result = modal_analyzer.analyze(chords)
chromatic_result = chromatic_analyzer.analyze(chords)

# 3. Synthesis Layer - Combine and rank interpretations
final_result = synthesize_interpretations(
    functional_result,
    modal_result,
    chromatic_result
)
```

### Customizing Analysis

```python
from harmonic_analysis import analyze_chord_progression, AnalysisOptions

# Fine-tune the analysis
options = AnalysisOptions(
    parent_key="G major",           # Provide context
    pedagogical_level="advanced",   # Get more detailed analysis
    confidence_threshold=0.6,       # Show alternatives above 60%
    max_alternatives=3              # Maximum alternative interpretations
)

result = await analyze_chord_progression(
    ['G', 'C', 'D', 'Em'],
    options
)
```

## Installation and Testing

### Full Installation with Development Tools

```bash
# Clone the repository
git clone https://github.com/yourusername/harmonic-analysis.git
cd harmonic-analysis

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Try the interactive demo
cd demo
./setup.sh
npm start
```

### Running the Test Suite

```bash
# All tests (1500+ test cases)
pytest

# Comprehensive multi-layer validation (427 sophisticated test cases)
pytest tests/test_comprehensive_multi_layer_validation.py -v

# Inversion analysis regression tests (perfect bidirectional conversion)
pytest tests/test_inversion_regression.py -v

# Focused bidirectional inversion test
python tests/test_inversion_bidirectional.py

# Edge case behavior and confidence calibration
pytest tests/test_edge_case_behavior.py -v

# Quality check (all linting, typing, and tests)
python scripts/quality_check.py --fix
```

#### Advanced Test Features

The library includes a **comprehensive multi-layer test framework** with 427+ sophisticated test cases covering:

- **Modal Characteristics**: 168 tests validating modal detection and analysis
- **Functional Harmony**: 60 tests ensuring proper Roman numeral analysis
- **Chromatic Analysis**: Advanced harmonic technique detection
- **Edge Cases**: Single chords, ambiguous progressions, pathological inputs
- **Inversion Analysis**: Perfect bidirectional conversion testing
- **Confidence Calibration**: Ensuring appropriate uncertainty for ambiguous cases

**Example Test Results:**
```bash
$ python tests/test_inversion_bidirectional.py
🎯 Testing progression: D Gm/Bb D/A Gm F/C C F in F major
Expected result: V/ii - ii⁶ - V/ii⁶⁴ - ii - I⁶⁴ - V - I

✅ Actual Roman numerals: V/ii - ii⁶ - V/ii⁶⁴ - ii - I⁶⁴ - V - I
✅ Reconstructed chords: D - Gm/Bb - D/A - Gm - F/C - C - F
🎉 ALL TESTS PASSED - Perfect bidirectional inversion conversion!
```

## 🔧 Specialized Module Examples

### MIDI Integration
```python
from harmonic_analysis.midi import parse_chord, find_chords_from_midi

# Parse chord symbols
chord_info = parse_chord('Cmaj7')
print(chord_info['quality'])  # 'major7'

# Analyze MIDI notes
midi_notes = [60, 64, 67]  # C major triad
matches = find_chords_from_midi(midi_notes)
print(matches[0].chord_name)  # 'Major'
```

### Advanced Chromatic Analysis
```python
from harmonic_analysis.chromatic import ChromaticAnalyzer, analyze_chromatic_harmony
from harmonic_analysis.core.functional_harmony import FunctionalHarmonyAnalyzer

async def chromatic_example():
    # First get functional analysis
    functional_analyzer = FunctionalHarmonyAnalyzer()
    chords = ['C', 'A7', 'Dm', 'G7', 'C']
    functional_result = await functional_analyzer.analyze_functionally(chords, 'C major')

    # Then analyze chromatic elements
    chromatic_result = analyze_chromatic_harmony(functional_result)
    if chromatic_result:
        print(f"Secondary dominants: {len(chromatic_result.secondary_dominants)}")
        print(f"Borrowed chords: {len(chromatic_result.borrowed_chords)}")
```

### Music Theory Utilities
```python
from harmonic_analysis.theory import (
    get_interval_name,
    MODAL_CHARACTERISTICS,
    get_modal_characteristics
)

# Interval analysis
print(get_interval_name(7))  # "Perfect 5th"

# Modal characteristics
characteristics = get_modal_characteristics('Dorian')
print(characteristics.brightness)  # "neutral"
print(characteristics.characteristic_degrees)  # ['1', '♭3', '6', '♭7']
```

### Algorithmic Suggestions
```python
from harmonic_analysis.algorithms import BidirectionalSuggestionEngine, AnalysisOptions

async def suggestion_example():
    engine = BidirectionalSuggestionEngine()
    chords = ['Dm7', 'G7', 'Cmaj7']
    options = AnalysisOptions()

    suggestions = await engine.generate_bidirectional_suggestions(
        chords, options, current_analysis_confidence=0.6
    )

    if suggestions.parent_key_suggestions:
        suggestion = suggestions.parent_key_suggestions[0]
        print(f"Try: {suggestion.suggested_key}")
        print(f"Reason: {suggestion.reason}")
```

## Common Questions

### "Why doesn't it recognize my progression?"

The library focuses on Western tonal and modal harmony. It might struggle with:

- Highly chromatic or atonal music
- Non-Western musical systems
- Very ambiguous progressions

### "Why are there multiple interpretations?"

Music is often ambiguous! The same progression can function different ways:

- `Am - F - C - G` could be vi-IV-I-V in C major
- Or i-VI-III-VII in A natural minor
- Or even have modal implications

The library shows you the most likely interpretations with confidence scores.

### "What's the difference between a scale and a melody?"

- **Scale**: `analyze_scale_melody(notes, melody=False)` - A collection of notes (unordered, no rhythm)
    - Returns: What scales contain these notes
- **Melody**: `analyze_scale_melody(notes, melody=True)` - A sequence of notes (ordered, implies rhythm)
    - Returns: Same as scale PLUS suggested tonic and confidence

### "How accurate is the confidence score?"

Confidence reflects:

- **90-100%**: Textbook clear (rare in real music)
- **70-90%**: Strong interpretation (common for clear progressions)
- **50-70%**: Valid but with alternatives (normal for interesting music)
- **Below 50%**: Ambiguous or outside the library's expertise

## Contributing

We welcome contributions from musicians and developers! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Citation

If you use this library in academic work:

```bibtex
@software{harmonic_analysis,
  title = {Harmonic Analysis: A Musician-Focused Python Library},
  author = {Wachtel, Sam},
  year = {2025},
  url = {https://github.com/sammywachtel/harmonic-analysis-py}
}
```

## Open, Downloadable Theory References (for the AI assistant)

All sources below are open-access and provide **downloadable** versions (PDF/EPUB). These are the primary references the AI assistant will cite when explaining analyses and filling gaps.

### Core sources
- **Open Music Theory, v2 (OMT2)** — HTML + downloads
  - Website: https://viva.pressbooks.pub/openmusictheory/
  - Open Textbook Library entry (lists downloadable EPUB/PDF formats): https://open.umn.edu/opentextbooks/textbooks/1254
  - Internet Archive mirror (direct **PDF** available): https://archive.org/details/open-music-theory
- **Music Theory for the 21st‑Century Classroom (MT21C)** — HTML + full **PDF**
  - Website & TOC: https://musictheory.pugetsound.edu/
  - Full textbook **PDF** (current compiled edition): https://musictheory.pugetsound.edu/hw/MusicTheory.pdf
- **Fundamentals, Function, and Form (FFF)** — HTML + **PDF**
  - Book page (HTML with download): https://milnepublishing.geneseo.edu/fundamentals-function-form/
  - Open Textbook Library entry: https://open.umn.edu/opentextbooks/textbooks/fundamentals-function-and-form-theory-and-analysis-of-tonal-western-art-music
- **Public‑domain classics for figured‑bass & harmony cross‑checks**
  - Prout, *Harmony: Its Theory and Practice* — IMSLP **PDF**: https://imslp.org/wiki/Harmony%3A_Its_Theory_and_Practice_(Prout%2C_Ebenezer)  • Internet Archive **PDF**: https://archive.org/details/harmonyitstheor00prouiala
  - Goetschius, *The Theory and Practice of Tone‑Relations* — Internet Archive **PDF**: https://archive.org/details/cu31924060020462

> Tip: OMT2 also ships chapter worksheets as combined **PDFs** (see each chapter’s “Assignments” or the **PDF Workbook** page), which are handy for unit tests.

---

### Theory Crosswalk (library features → where to read more)

| Library feature / output | OMT2 (HTML) | MT21C (HTML/PDF) | FFF (HTML) |
|---|---|---|---|
| **Roman numerals (basics)** | Roman Numeral Analysis: https://viva.pressbooks.pub/openmusictheory/chapter/roman-numerals/ | Book TOC (core chapters): https://musictheory.pugetsound.edu/mt21c/MusicTheory.html | Overview across diatonic harmony & analysis |
| **Figured‑bass & inversions** | Inversion & Figured Bass: https://viva.pressbooks.pub/openmusictheory/chapter/inversion-and-figured-bass/ • Figured Bass (notation): https://viva.pressbooks.pub/openmusictheory/chapter/figured-bass/ | Figured‑Bass Inversion Symbols: https://musictheory.pugetsound.edu/mt21c/FiguredBassInversionSymbols.html • Types of 6‑4 chords: https://musictheory.pugetsound.edu/mt21c/TypesOfSixFourChords.html | — |
| **Cadences (types & strength)** | Intro to Harmony & Cadences: https://viva.pressbooks.pub/openmusictheory/chapter/intro-to-harmony/ • Subtle Color Changes (cadence roundup): https://viva.pressbooks.pub/openmusictheory/chapter/subtle-color-changes/ • Cadential 6/4: https://viva.pressbooks.pub/openmusictheory/chapter/cadential-64/ | Cadences: https://musictheory.pugetsound.edu/mt21c/cadences.html | — |
| **Modal analysis** | Diatonic Modes: https://viva.pressbooks.pub/openmusictheory/chapter/diatonic-modes/ • Intro to Modes & Chromatic Scale: https://viva.pressbooks.pub/openmusictheory/chapter/intro-to-diatonic-modes-and-the-chromatic-scale/ • Modal Schemas: https://viva.pressbooks.pub/openmusictheory/chapter/modal-schemas/ • Analyzing with Collections/Modes: https://viva.pressbooks.pub/openmusictheory/chapter/analyzing-with-collections-scales-and-modes/ | — | — |
| **Secondary/applied dominants & tonicization** | Tonicization: https://viva.pressbooks.pub/openmusictheory/chapter/tonicization/ • Applied (secondary) chords: https://viva.pressbooks.pub/openmusictheorycopy/chapter/applied-chords/ | Writing Secondary Dominants: https://musictheory.pugetsound.edu/mt21c/WritingSecondaryDominants.html | Modulation vs. tonicization discussed in Ch. 28 |
| **Modulation (vs tonicization)** | Extended Tonicization & Modulation: https://viva.pressbooks.pub/openmusictheory/part/diatonic-harmony/ (see topics list on page) | — | Modulation (Ch. 28): https://milnepublishing.geneseo.edu/fundamentals-function-form/chapter/28-modulation/ |
| **Chromatic techniques (aug6, N6, CT°, tritone sub, sequences)** | Augmented Sixth Chords: https://viva.pressbooks.pub/openmusictheory/chapter/augmented-sixth-chords/ • Neapolitan ♭II⁶: https://viva.pressbooks.pub/openmusictheory/chapter/bii6/ • Common‑Tone chords: https://viva.pressbooks.pub/openmusictheory/chapter/common-tone-chords/ • Chromatic Sequences: https://viva.pressbooks.pub/openmusictheory/chapter/chromatic-sequences/ • Substitutions (tritone): https://viva.pressbooks.pub/openmusictheory/chapter/substitutions/ | Practice sets across chapters; see textbook PDF for cross‑refs | — |
| **Predominant sevenths (ii⁷ etc.)** | Predominant Seventh Chords: https://viva.pressbooks.pub/openmusictheory/chapter/predominant-seventh-chords/ | — | — |
| **Four‑chord schemas / pop progressions** | Four‑Chord Schemas: https://viva.pressbooks.pub/openmusictheory/chapter/4-chord-schemas/ • Classical Schemas (pop context): https://viva.pressbooks.pub/openmusictheory/chapter/classical-schemas/ | — | Binary/ternary/etc. forms elsewhere |
| **Modes "brightness" / character** | Diatonic Modes (color notes): https://viva.pressbooks.pub/openmusictheory/chapter/diatonic-modes/ • Analyzing with Modes: https://viva.pressbooks.pub/openmusictheory/chapter/analyzing-with-collections-scales-and-modes/ | — | — |

> **Unit‑test anchor (inversions):** The regression case `D  Gm/B♭  D/A  Gm  F/C  C  F` in F major yields
> `V/ii – ii⁶ – V/ii⁶⁴ – ii – I⁶⁴ – V – I` with **perfect bidirectional conversion**. This validates the centralized
> inversion analysis architecture across all library components. Cross‑check definitions in OMT2 "Inversion & Figured‑Bass" and MT21C "Figured‑Bass Inversion Symbols."

> **Quality Assurance:** The library maintains **100% test pass rate** with comprehensive multi-layer validation covering 427+ sophisticated test cases, inversion regression testing, edge case behavior, and confidence calibration.

### Downloadables for testing (quick links)
- OMT2 PDF Workbook hub (chapter worksheets as combined PDFs): https://viva.pressbooks.pub/openmusictheory/chapter/pdf-workbook/
- MT21C Homework/Practice (PDFs): https://musictheory.pugetsound.edu/ (see “Click here to download…”) and the compiled book **PDF**: https://musictheory.pugetsound.edu/hw/MusicTheory.pdf
- FFF student workbook (Open SUNY, **PDF**): https://milnepublishing.geneseo.edu/fundamentals-function-form-workbook/

---

#### How the assistant will use these
- Prefer OMT2 for concise topic pages and consistent terminology.
- Use MT21C when step‑by‑step practice or figures are helpful (e.g., figured‑bass symbols and 6‑4 chord types).
- Use FFF for formal modulation topics and longer analytical examples.
- Use Prout/Goetschius when a historical/public‑domain definition strengthens an edge case (e.g., figured‑bass conventions).

## Acknowledgments

This library was extracted from the [Music Modes App](https://github.com/sammywachtel/music_modes_app), a comprehensive
music theory toolkit. Special thanks to the music theory community for invaluable feedback on modal analysis and
harmonic interpretation.
