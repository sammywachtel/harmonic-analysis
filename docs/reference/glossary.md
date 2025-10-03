# Musical Terminology and API Glossary

This reference provides definitions for musical terms and API concepts used throughout the Harmonic Analysis library.

## Musical Terms

### Analysis Types

**Functional Analysis**
: Traditional Western harmonic analysis focusing on chord function and voice leading. Emphasizes tonic-dominant relationships and cadential patterns.

**Modal Analysis**
: Analysis based on modal scales and their characteristic intervals. Focuses on modal centers and non-functional harmonic relationships.

**Chromatic Analysis**
: Analysis of music using extensive chromatic harmony, altered chords, and non-diatonic progressions.

### Harmonic Concepts

**Cadence**
: A harmonic progression that provides closure or resolution. Types include authentic (V-I), plagal (IV-I), half (ending on V), and deceptive (V-vi).

**Roman Numeral Analysis**
: A system using Roman numerals (I, ii, iii, IV, V, vi, vii°) to represent chord functions relative to a key center.

**Voice Leading**
: The melodic movement of individual musical lines (voices) in a harmonic progression.

**Modal Interchange**
: Borrowing chords from parallel modes (e.g., using chords from C minor in C major).

**Tonicization**
: Temporarily establishing a new tonal center through secondary dominants or other harmonic means.

### Scale and Mode Terms

**Diatonic**
: Using only the seven notes of a major or minor scale, without chromatic alterations.

**Modes**
: Variations of the major scale starting from different degrees:
- **Ionian**: Major scale (1-2-3-4-5-6-7)
- **Dorian**: Minor with raised 6th (1-2-♭3-4-5-6-♭7)
- **Phrygian**: Minor with lowered 2nd (1-♭2-♭3-4-5-♭6-♭7)
- **Lydian**: Major with raised 4th (1-2-3-♯4-5-6-7)
- **Mixolydian**: Major with lowered 7th (1-2-3-4-5-6-♭7)
- **Aeolian**: Natural minor scale (1-2-♭3-4-5-♭6-♭7)
- **Locrian**: Minor with lowered 2nd and 5th (1-♭2-♭3-4-♭5-♭6-♭7)

**Parent Key**
: The major key that shares the same key signature as a modal scale.

**Local Tonic**
: The note functioning as the tonal center in modal analysis.

### Chord Types

**Triad**
: Three-note chord consisting of root, third, and fifth.

**Seventh Chord**
: Four-note chord adding the seventh interval to a triad.

**Extended Chord**
: Chord including ninths, elevenths, or thirteenths.

**Altered Chord**
: Chord with chromatic modifications (♯5, ♭5, ♯9, ♭9, etc.).

**Secondary Dominant**
: Dominant chord of a scale degree other than tonic (e.g., V/V = dominant of the dominant).

### Progressions

**ii-V-I**
: Common progression in jazz and classical music providing strong resolution.

**vi-IV-I-V**
: Popular progression in contemporary music, especially pop and rock.

**Circle of Fifths**
: Progression moving by perfect fifths (e.g., C-F-B♭-E♭-A♭-D♭-G♭).

**Plagal Motion**
: Movement by fourth (e.g., IV-I), characteristic of folk and gospel music.

## API Terms

### Core Classes

**PatternAnalysisService**
: Main service class for performing harmonic analysis. Provides both synchronous and asynchronous analysis methods.

**AnalysisEnvelope**
: Container for analysis results including primary interpretation, alternatives, and evidence.

**PatternEngine**
: Core engine responsible for pattern matching and evidence aggregation.

**Calibrator**
: Component responsible for confidence score calibration and quality gates.

### Analysis Parameters

**chord_symbols**
: List of chord symbols in standard notation (e.g., ["Cmaj7", "Am7", "Dm7", "G7"]).

**romans**
: List of Roman numeral symbols (e.g., ["I", "vi", "ii", "V"]).

**notes**
: List of note names for melody or scale analysis (e.g., ["C4", "D4", "E4"]).

**key_hint**
: Optional key context to guide analysis (e.g., "C major", "A minor", "D dorian").

**profile**
: Musical style affecting interpretation priority:
- `"classical"`: Functional harmony and voice leading
- `"jazz"`: Extended chords and modal interchange
- `"pop"`: Loop-based progressions and modal borrowing
- `"folk"`: Modal scales and pentatonic patterns
- `"choral"`: Voice leading and traditional harmony

### Result Structure

**primary**
: The highest-confidence analysis result containing:
- `type`: Analysis type (functional, modal, chromatic)
- `confidence`: Numerical confidence score (0.0-1.0)
- `key_signature`: Detected or confirmed key
- `roman_numerals`: Chord functions as Roman numerals
- `reasoning`: Text explanation of analysis logic

**alternatives**
: List of alternative interpretations above confidence threshold.

**evidence**
: Detailed evidence supporting the analysis including:
- Pattern matches found
- Confidence scores for each pattern
- Span of musical material analyzed

**analysis_time_ms**
: Processing time in milliseconds.

### Confidence Scores

**Confidence Ranges**
: - 0.8-1.0: High confidence, clear pattern matches
- 0.6-0.8: Moderate confidence, some ambiguity
- 0.4-0.6: Low confidence, consider alternatives
- 0.0-0.4: Very uncertain, may need more context

**Calibration**
: Process of adjusting confidence scores based on historical accuracy data.

**Quality Gates**
: Validation checks ensuring confidence scores accurately reflect analysis certainty.

### Pattern System

**Pattern**
: Template for recognizing harmonic, melodic, or structural features in music.

**Pattern Family**
: Category of related patterns (harmonic, modal, chromatic, cadential, melodic).

**Pattern Weight**
: Base confidence assigned to a pattern match.

**Evidence Type**
: Classification of analytical evidence:
- `HARMONIC`: Chord-based evidence
- `STRUCTURAL`: Large-scale form evidence
- `CADENTIAL`: Cadence-based evidence
- `INTERVALLIC`: Interval relationship evidence
- `CONTEXTUAL`: Key and mode context evidence

**Track**
: Analysis pathway (functional, modal, chromatic) with specific pattern priorities.

### Error Types

**ValueError**
: Raised for invalid input parameters or missing required data.

**AnalysisError**
: Raised when analysis cannot be completed due to insufficient or ambiguous data.

**CalibrationError**
: Raised when confidence calibration fails quality gates.

## Musical Style Profiles

### Classical Profile
- Prioritizes functional harmony
- Emphasizes voice leading and cadences
- Recognizes common practice period patterns
- Values traditional chord progressions

### Jazz Profile
- Recognizes extended and altered chords
- Emphasizes ii-V-I progressions
- Handles modal interchange and substitutions
- Values harmonic sophistication

### Pop Profile
- Focuses on loop-based progressions
- Emphasizes vi-IV-I-V and variations
- Handles power chords and simple triads
- Values repetitive harmonic patterns

### Folk Profile
- Emphasizes modal scales and progressions
- Recognizes pentatonic patterns
- Handles traditional folk harmonic structures
- Values modal characteristics over functional harmony

### Choral Profile
- Emphasizes four-part voice leading
- Recognizes traditional hymn harmonies
- Values smooth voice leading and cadences
- Handles traditional choral progressions

## Pattern Families

### Harmonic Patterns
- Chord progressions and sequences
- Functional harmonic relationships
- Common chord substitutions

### Modal Patterns
- Modal scale characteristics
- Non-functional harmonic movements
- Modal cadences and closures

### Chromatic Patterns
- Altered chords and progressions
- Chromatic voice leading
- Non-diatonic harmonic relationships

### Cadential Patterns
- Authentic, plagal, half, and deceptive cadences
- Secondary dominants and tonicizations
- Modal and chromatic cadences

### Melodic Patterns
- Scale passages and arpeggios
- Leading tone resolutions
- Motivic patterns and sequences

## Usage Examples

### Key Hint Formats
```
"C major"          # Major key
"A minor"          # Minor key
"D dorian"         # Modal key
"F# mixolydian"    # Modal with accidentals
"Bb major"         # Major with flats
```

### Chord Symbol Formats
```
["C", "F", "G"]                    # Simple triads
["Cmaj7", "Am7", "Dm7", "G7"]     # Seventh chords
["C", "C/E", "F", "G"]            # Slash chords (inversions)
["A5", "D5", "E5"]                # Power chords
```

### Roman Numeral Formats
```
["I", "vi", "IV", "V"]            # Basic triads
["Imaj7", "vi7", "ii7", "V7"]     # Seventh chords
["ii65", "V7", "I"]               # Figured bass notation
["bVI", "bVII", "I"]              # Borrowed chords
```

---

For implementation details, see [API Reference](api-reference.md).
For conceptual explanations, see [Architecture Overview](../explanation/architecture.md).
