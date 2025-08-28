# Harmonic Analysis Library 🎵

A comprehensive Python library that analyzes music the way musicians think about it - identifying chord progressions,
scales, modes, and harmonic relationships with detailed explanations of *why* it hears what it hears.

## What This Library Does (For Musicians)

This library listens to your chord progressions, scales, and melodies and tells you:

- **What key you're in** and how confident it is about that
- **The function of each chord** (tonic, dominant, subdominant, etc.)
- **What mode you might be using** (Dorian, Mixolydian, Phrygian, etc.)
- **Advanced harmonic techniques** you're employing (secondary dominants, borrowed chords, etc.)
- **Multiple valid interpretations** when your music is ambiguous (which is often!)

Think of it as having a music theory professor analyze your work and explain their reasoning.

## Installation

```bash
pip install harmonic-analysis
```

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

# Just the scale and melody tests
pytest tests/test_comprehensive_multi_layer_validation.py::TestComprehensiveMultiLayerValidation::test_scale_melody_analysis_cases -v

# See how it handles edge cases
pytest tests/test_edge_case_behavior.py -v
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

## Acknowledgments

This library was extracted from the [Music Modes App](https://github.com/sammywachtel/music_modes_app), a comprehensive
music theory toolkit. Special thanks to the music theory community for invaluable feedback on modal analysis and
harmonic interpretation.
