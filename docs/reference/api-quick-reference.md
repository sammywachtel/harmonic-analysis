# API Quick Reference

Condensed cheat sheet for the public API. For full signatures and examples, see [api-reference.md](api-reference.md). For audio analysis specifically, see [audio-api.md](audio-api.md).

## Imports at a glance

```python
# Pattern analysis services (chord progressions, scales, melodies, romans)
from harmonic_analysis import PatternAnalysisService, UnifiedPatternService

# Simple per-input analysis functions
from harmonic_analysis import analyze_scale, analyze_melody

# Result types
from harmonic_analysis import (
    AnalysisEnvelope,        # the wrapper returned by analyze_with_patterns
    AnalysisSummary,         # primary + alternatives are this type
    ScaleMelodyAnalysisResult,
    AnalysisType,            # enum: FUNCTIONAL, MODAL, CHROMATIC
)

# Audio analysis (requires `pip install harmonic-analysis[audio]`)
from harmonic_analysis import (
    analyze_audio_async,
    analyze_audio,
    AudioAdapter,
    AudioAnalysisResult,
    ChordEvent,
    AudioImportError,
)
```

## Chord progression analysis

```python
service = PatternAnalysisService()  # or UnifiedPatternService for the next-gen path
result = await service.analyze_with_patterns_async(
    chord_symbols=["C", "Am", "F", "G"],
    key_hint="C major",          # optional; required for some scale/roman inputs
    profile="classical",          # "classical" | "jazz" | "pop"
)

# Sync wrapper exists too:
result = service.analyze_with_patterns(chord_symbols=["C", "Am", "F", "G"])
```

**Returns:** `AnalysisEnvelope` with:

| Field | Type | What it is |
|-------|------|------------|
| `primary` | `AnalysisSummary` | Highest-confidence interpretation |
| `alternatives` | `List[AnalysisSummary]` | Other interpretations above threshold |
| `evidence` | `List[EvidenceDTO]` | Pattern matches and supporting evidence |
| `analysis_time_ms` | `Optional[float]` | Wall-clock time |
| `chord_symbols` | `List[str]` | Echo of the input |
| `schema_version` | `str` | DTO schema version (currently `"1.0"`) |

**Reading the result:**

```python
result.primary.type            # AnalysisType.FUNCTIONAL | MODAL | CHROMATIC
result.primary.key_signature   # e.g. "C major"
result.primary.roman_numerals  # e.g. ["I", "vi", "IV", "V"]
result.primary.confidence      # 0.0–1.0
result.primary.reasoning       # human-readable explanation
result.primary.patterns        # list of detected patterns
result.primary.chromatic_elements  # secondary dominants, borrowed chords, etc.

for alt in result.alternatives:
    print(alt.type, alt.confidence, alt.reasoning)
```

## Roman numeral input

```python
result = await service.analyze_with_patterns_async(
    romans=["ii", "V7", "I"],
    key_hint="C major",   # required for roman input
    profile="classical",
)
```

## Scale analysis

```python
# Via the service (richer summary)
result = await service.analyze_with_patterns_async(
    notes=["D", "E", "F", "G", "A", "B", "C"],
    key_hint="D dorian",   # required for scale input
    profile="classical",
)
result.primary.scale_summary  # detected_mode, parent_key, characteristic_notes, ...

# Or the simple function
from harmonic_analysis import analyze_scale
res = analyze_scale(notes=["D", "E", "F", "G", "A", "B", "C"])
```

## Melody analysis

```python
result = await service.analyze_with_patterns_async(
    melody=["C4", "D4", "E4", "G4", "E4", "D4", "C4"],
    key_hint="C major",
    profile="classical",
)
result.primary.melody_summary  # contour, range_semitones, characteristics, ...

from harmonic_analysis import analyze_melody
res = analyze_melody(notes=["C4", "D4", "E4", "F4", "G4"])
```

## Audio analysis

```python
from harmonic_analysis import analyze_audio_async

result = await analyze_audio_async(
    "song.wav",
    key_detection="default",          # or "ks_only" / "full" / list / dict
    show_analysis_details=True,        # populates result.key_analysis_details
    segment=(0.0, 30.0),               # optional (start, end) in seconds
)

result.global_key.tonic       # e.g. "B"
result.global_key.mode        # e.g. "Aeolian"
result.global_key.confidence  # 0.0–1.0
result.local_key              # KeyInfo for the analyzed segment
result.cadences.detected      # bool
result.cadences.strength      # 0.0–1.0
result.region.type            # "stable" | "modulation" | "modal_shift"
result.region.borrowed        # list of pitch-class names borrowed from outside the global key
result.chords                 # list[ChordEvent] with start_time, end_time, chord_label, confidence, is_diatonic
result.key_hint               # property: "<tonic> <mode>" — feed back to PatternAnalysisService.key_hint
```

When `show_analysis_details=True`:

```python
details = result.key_analysis_details
details["approaches"]    # per-approach top-3 with weights
details["synthesis"]     # winner, runner_up, margin, key_score_table (24 keys)
details["modulations"]   # None until iteration_02 ships HMM
```

See [audio-api.md](audio-api.md) for the full ensemble parameter, weights table, and result schema.

## Musical data API (always available)

```python
from harmonic_analysis import (
    # Mode and scale data
    get_scale_notes,                     # ("D", "Dorian") → ["D", "E", "F", ...]
    get_modal_characteristics,           # ("Dorian") → ModalCharacteristics
    get_modes_by_brightness,             # "bright" → ["Ionian", "Lydian", ...]
    get_circle_of_fifths,                # → {"major": [...], "minor": [...]}
    get_relative_major_minor_pairs,      # → {"C major": "A minor", ...}
    get_all_scale_systems,               # → {"major_scale": {...}, ...}

    # Note utilities
    normalize_note_name,                 # "Db" → "D♭"
    note_to_pitch_class,                 # "C#" → 1
    pitch_class_to_note,                 # 1 → "C#"
    canonicalize_key_signature,          # "D♭ major" → standardized form

    # Constants
    ALL_KEYS, ALL_MAJOR_KEYS, ALL_MINOR_KEYS, ALL_MODES,
    MODAL_CHARACTERISTICS, NOTE_TO_PITCH_CLASS,
)
```

## Character analysis

```python
from harmonic_analysis import (
    get_mode_emotional_profile,    # "Dorian" → EmotionalProfile
    analyze_progression_character, # chord list → ProgressionCharacter
    describe_emotional_contour,    # contour pattern → narrative string
    describe_contour,              # ["U", "D", "U"] → narrative
)
```

## Optional features

```python
# Educational explanations (Bernstein-style)
from harmonic_analysis.educational import EducationalService
# pip install harmonic-analysis[educational]

# MusicXML / MIDI parsing
from harmonic_analysis.integrations import Music21Adapter
# pip install harmonic-analysis[music21]
```

## Confidence interpretation

| Range | Meaning |
|-------|---------|
| 0.85–1.0 | Very confident — clear, unambiguous patterns |
| 0.6–0.85 | Confident — some ambiguity, clear primary interpretation |
| 0.4–0.6  | Moderate — multiple valid interpretations likely |
| < 0.4    | Low — highly ambiguous or outside the library's expertise |

## See also

- [Full API Reference](api-reference.md) — complete signatures and examples
- [Audio API Reference](audio-api.md) — audio-only surface
- [Getting Started Tutorial](../tutorials/getting-started.md)
- [Architecture Overview](../explanation/architecture.md)
