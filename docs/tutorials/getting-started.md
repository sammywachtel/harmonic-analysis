# Getting Started with Harmonic Analysis

This tutorial will guide you through your first steps with the Harmonic Analysis library. By the end, you'll understand how to perform basic analysis and interpret the results.

## What You'll Learn

- How to install and set up the library
- How to analyze your first chord progression
- How to understand confidence scores
- How to interpret different analysis types

## Prerequisites

- Python 3.8 or higher
- Basic understanding of music theory (chords, keys)
- 10-15 minutes

## Step 1: Installation

Install the library using pip:

```bash
pip install harmonic-analysis
```

For development installation:

```bash
git clone https://github.com/your-repo/harmonic-analysis.git
cd harmonic-analysis
pip install -e .
```

## Step 2: Your First Analysis

Let's analyze a simple chord progression. Create a new Python file and add:

```python
from harmonic_analysis.services.unified_pattern_service import UnifiedPatternService

# Create the analysis service
service = UnifiedPatternService()

# Analyze a classic vi-IV-I-V progression
result = service.analyze_with_patterns(
    chords=["Am", "F", "C", "G"],
    key_hint="C major",
    profile="pop"
)

# Print the primary interpretation
print(f"Analysis Type: {result.primary.type}")
print(f"Key: {result.primary.key_signature}")
print(f"Roman Numerals: {result.primary.roman_numerals}")
print(f"Confidence: {result.primary.confidence:.2f}")
```

**Expected Output:**
```
Analysis Type: functional
Key: C major
Roman Numerals: ['vi', 'IV', 'I', 'V']
Confidence: 0.85
```

## Step 3: Understanding the Results

Your analysis returns an `AnalysisEnvelope` containing:

- **Primary interpretation**: The most confident analysis
- **Alternative interpretations**: Other possible analyses
- **Evidence**: Why the analysis chose this interpretation

Let's explore the evidence:

```python
# Look at the evidence for this analysis
print("\nEvidence:")
for evidence in result.evidence:
    print(f"- {evidence['reason']}: {evidence['details']['raw_score']:.2f}")
```

## Step 4: Try Different Musical Styles

The `profile` parameter affects how ambiguous progressions are interpreted:

```python
# Analyze the same progression as jazz
jazz_result = service.analyze_with_patterns(
    chords=["Am", "F", "C", "G"],
    key_hint="C major",
    profile="jazz"  # Try "classical", "pop", "folk", "choral"
)

print(f"\nJazz interpretation: {jazz_result.primary.type}")
print(f"Confidence: {jazz_result.primary.confidence:.2f}")
```

## Step 5: Analyzing Different Input Types

You can analyze various musical elements:

### Chord Progressions
```python
# Extended jazz progression
result = service.analyze_with_patterns(
    chords=["Dm7", "G7", "Cmaj7", "A7"],
    key_hint="C major",
    profile="jazz"
)
```

### Roman Numerals
```python
# Classical progression with accidentals
result = service.analyze_with_patterns(
    romans=["ii", "V7", "I", "♭VII"],  # Now supports accidentals like ♭VII, bVII
    key_hint="C major",
    profile="classical"
)
```

### Melodies
```python
# Simple melody - shows scale degrees and contour patterns
result = service.analyze_with_patterns(
    melody=["C4", "D4", "E4", "F4", "G4"],
    key_hint="C major",
    profile="classical"
)
print(f"Detected patterns: {len(result.evidence)} melodic patterns")
```

### Scales
```python
# Modal scale - shows degree relationships and characteristics
result = service.analyze_with_patterns(
    notes=["D", "E", "F", "G", "A", "B", "C"],
    key_hint="C major",  # Parent key for modal analysis
    profile="folk"
)
print(f"Modal characteristics: {result.primary.modal_characteristics}")
```

## Step 6: Working with Confidence

Confidence scores help you understand how certain the analysis is:

- **0.8-1.0**: High confidence - clear patterns detected
- **0.6-0.8**: Moderate confidence - some ambiguity
- **0.4-0.6**: Low confidence - consider alternatives
- **Below 0.4**: Very uncertain - may need more context

```python
# Check if analysis is confident enough
if result.primary.confidence > 0.7:
    print("High confidence analysis ✓")
else:
    print("Consider alternative interpretations")
    for alt in result.alternatives:
        print(f"Alternative: {alt.type} (confidence: {alt.confidence:.2f})")
```

## Step 7: Using the Demo Interface

For interactive exploration, try the Gradio demo:

```bash
python demo/full_library_demo.py --gradio
```

This opens a web interface where you can:
- Try different progressions
- Compare analysis profiles
- See detailed evidence
- Export results

## What's Next?

Now that you've mastered the basics:

1. **Learn about confidence calibration**: [Understanding Confidence Scoring](understanding-confidence.md)
2. **Explore musical styles**: [Working with Different Musical Styles](musical-styles.md)
3. **Dive deeper into modal analysis**: [Modal Analysis Deep Dive](modal-analysis.md)
4. **Integrate into your app**: [API Integration Guide](../how-to/api-integration.md)

## Troubleshooting

**Import errors?** Make sure you've installed all dependencies:
```bash
pip install -r requirements.txt
```

## Step 8: Command Line Interface

You can also use the analysis from the command line, which matches what you'll see in the web demo:

### Chord Progressions
```bash
python demo/full_library_demo.py --chords "C Am F G" --key "C major" --profile pop
```

### Roman Numerals
```bash
python demo/full_library_demo.py --romans "I vi IV V" --key "C major" --profile classical
```

### Melodies
```bash
python demo/full_library_demo.py --melody "C D E F G A B C" --key "C major" --profile folk
```

### Scales
```bash
python demo/full_library_demo.py --scale "C D E F G A B" --key "C major" --profile classical
```

### Interactive Web Demo
```bash
python demo/full_library_demo.py --gradio
```

**Unexpected results?** Try:
- Providing a more specific `key_hint`
- Using a different `profile`
- Checking the confidence score

**Need help?** See our [Troubleshooting Guide](../how-to/troubleshooting.md)

---

**Congratulations!** You've completed your first harmonic analysis. The library can now help you understand chord progressions, melodies, and scales across different musical styles.

*Next: [Understanding Confidence Scoring](understanding-confidence.md)*
