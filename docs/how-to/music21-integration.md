# Using music21 Integration

## Overview

The harmonic-analysis library provides seamless integration with [music21](https://web.mit.edu/music21/), enabling you to analyze musical scores in MusicXML and MIDI formats directly. The `Music21Adapter` converts music21 objects into the library's internal format while preserving key information, chord symbols, and structural metadata.

## Installation

Install the library with music21 support:

```bash
pip install harmonic-analysis[music21]
```

Or install music21 separately:

```bash
pip install music21
```

## Basic Usage

### Analyzing MusicXML Files

```python
from harmonic_analysis.integrations.music21_adapter import Music21Adapter
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

# Initialize adapter and service
adapter = Music21Adapter()
service = PatternAnalysisService()

# Parse MusicXML file
data = adapter.from_musicxml('chopin_prelude.xml')

# Analyze the extracted chords
result = await service.analyze_with_patterns_async(
    data['chord_symbols'],
    key_hint=data['key_hint'],
    profile='classical'
)

print(f"Detected key: {data['key_hint']}")
print(f"Chord progression: {' - '.join(data['chord_symbols'])}")
print(f"Analysis: {result.primary.reasoning}")
```

### Analyzing MIDI Files

```python
# Parse MIDI file (chords inferred from simultaneous notes)
data = adapter.from_midi('progression.mid')

# Same analysis workflow
result = await service.analyze_with_patterns_async(
    data['chord_symbols'],
    key_hint=data['key_hint'],
    profile='jazz'
)
```

## What Gets Extracted

The adapter extracts comprehensive information from scores:

```python
data = adapter.from_musicxml('score.xml')

# Extracted data structure:
{
    'chord_symbols': ['C', 'Am', 'F', 'G'],      # Chord progression
    'key_hint': 'C major',                        # Detected key
    'metadata': {                                 # Score metadata
        'title': 'Prelude in C',
        'composer': 'Johann Sebastian Bach',
        'tempo': 120,
        'time_signature': '4/4',
        'file_path': 'score.xml'
    },
    'structure': {                                # Structural info
        'measure_count': 35,
        'part_count': 4,
        'sections': []
    },
    'score_object': <Score object>                # Original music21 Score
}
```

## Chord Symbol Extraction

The adapter tries multiple strategies to extract chords:

### 1. Explicit Chord Symbols (Best)

If your MusicXML file contains `<harmony>` elements with chord symbols:

```xml
<harmony>
  <root>
    <root-step>C</root-step>
  </root>
  <kind>major</kind>
</harmony>
```

These are extracted directly and accurately.

### 2. Inferred from Chord Objects

For scores without chord symbols, the adapter analyzes simultaneous notes:

```python
# MusicXML with notes but no chord symbols
data = adapter.from_musicxml('piano_score.xml')
# Chords inferred from vertical sonorities
# Warning: "No chord symbols found, inferring from notes"
```

### 3. MIDI Files

MIDI files rarely contain chord symbols, so they're always inferred:

```python
data = adapter.from_midi('progression.mid')
# Warning: "MIDI files may not contain chord symbols..."
```

## Key Detection

The adapter uses multiple methods to detect the key:

```python
# Priority order:
# 1. Explicit key signatures in the score
# 2. music21's key analysis (Krumhansl-Schmuckler algorithm)
# 3. Fallback to 'C major' with warning
```

If key detection fails or is uncertain, you can override:

```python
data = adapter.from_musicxml('ambiguous_score.xml')

# Override detected key
result = await service.analyze_with_patterns_async(
    data['chord_symbols'],
    key_hint='D minor',  # Override with your key
    profile='classical'
)
```

## Accessing Metadata

Use metadata to inform your analysis:

```python
data = adapter.from_musicxml('beethoven_sonata.xml')

# Determine profile from composer or era
profile = 'classical'
if data['metadata']['composer']:
    composer = data['metadata']['composer'].lower()
    if 'bach' in composer or 'beethoven' in composer:
        profile = 'classical'
    elif 'coltrane' in composer or 'davis' in composer:
        profile = 'jazz'

# Use metadata in analysis
result = await service.analyze_with_patterns_async(
    data['chord_symbols'],
    key_hint=data['key_hint'],
    profile=profile
)

print(f"Analyzing {data['metadata']['title']} by {data['metadata']['composer']}")
```

## Error Handling

Handle common errors gracefully:

```python
from harmonic_analysis.integrations.music21_adapter import (
    Music21Adapter,
    Music21ImportError
)

try:
    adapter = Music21Adapter()
    data = adapter.from_musicxml('score.xml')

except Music21ImportError:
    print("music21 not installed. Install with: pip install music21")

except FileNotFoundError as e:
    print(f"Score file not found: {e}")

except ValueError as e:
    print(f"Failed to parse score: {e}")
```

## Working with the Original Score

Keep the original music21 Score object for advanced operations:

```python
data = adapter.from_musicxml('score.xml')

# Access the original music21 Score
score = data['score_object']

# Use music21 features
score.show('text')                    # Display as text
score.write('musicxml', 'output.xml') # Export modified score
score.analyze('key')                  # Run music21 analysis

# Extract additional information
notes = score.flatten().notes
intervals = score.flatten().getElementsByClass('Interval')
```

## Batch Processing

Process multiple files efficiently:

```python
import os
from pathlib import Path

def analyze_score_directory(directory: str, profile: str = 'classical'):
    """Analyze all MusicXML files in a directory."""
    adapter = Music21Adapter()
    service = PatternAnalysisService()

    results = []

    for file_path in Path(directory).glob('*.xml'):
        try:
            # Parse file
            data = adapter.from_musicxml(str(file_path))

            # Analyze
            result = await service.analyze_with_patterns_async(
                data['chord_symbols'],
                key_hint=data['key_hint'],
                profile=profile
            )

            results.append({
                'file': file_path.name,
                'title': data['metadata']['title'],
                'key': data['key_hint'],
                'analysis': result.primary.reasoning
            })

        except Exception as e:
            print(f"Failed to analyze {file_path.name}: {e}")

    return results

# Analyze all files
results = analyze_score_directory('./scores/', profile='classical')
for r in results:
    print(f"{r['title']}: {r['analysis']}")
```

## Limitations and Caveats

### MusicXML Files

- **Chord Symbols**: Best results with explicit chord symbols in the file
- **Multiple Parts**: Adapter analyzes all parts together (chordify)
- **Key Ambiguity**: May not detect modulations or complex tonal centers

### MIDI Files

- **No Chord Symbols**: Always inferred from simultaneous notes
- **Limited Metadata**: MIDI files lack title, composer information
- **Interpretation Varies**: Chord inference depends on voicing and spacing
- **Best For**: Simple chord progressions with clear vertical sonorities

### General Limitations

- **Relies on music21**: Requires music21 installation and licensing
- **Parsing Errors**: Complex scores may fail to parse
- **Memory Usage**: Large scores consume significant memory
- **Processing Time**: Complex files may take several seconds

## Advanced: Custom Extraction

Extend the adapter for custom extraction needs:

```python
class CustomMusic21Adapter(Music21Adapter):
    """Extended adapter with custom extraction."""

    def extract_melody(self, score):
        """Extract melodic line from highest part."""
        highest_part = score.parts[0]  # Assume first part is melody
        notes = highest_part.flatten().notes
        return [str(n.pitch) for n in notes]

    def extract_bass_line(self, score):
        """Extract bass line from lowest part."""
        lowest_part = score.parts[-1]  # Assume last part is bass
        notes = lowest_part.flatten().notes
        return [str(n.pitch) for n in notes]

# Use custom adapter
adapter = CustomMusic21Adapter()
data = adapter.from_musicxml('score.xml')
melody = adapter.extract_melody(data['score_object'])
bass = adapter.extract_bass_line(data['score_object'])
```

## See Also

- [API Reference](../reference/api-reference.md) - Complete API documentation
- [music21 Documentation](https://web.mit.edu/music21/doc/) - music21 library reference
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
