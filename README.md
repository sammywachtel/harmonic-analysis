# Harmonic Analysis 🎵

A Python library that listens to music the way musicians do — chord progressions, scales, melodies, and audio recordings — and tells you what it hears, why it hears it that way, and how confident it is.

It handles the boring stuff (parsing, key inference, Roman numerals, inversions) and the interesting stuff (modal interchange, secondary dominants, ensemble key detection on real audio) in one place, with explanations you can actually read.

```python
import asyncio
from harmonic_analysis import PatternAnalysisService

async def main():
    service = PatternAnalysisService()
    result = await service.analyze_with_patterns_async(
        ["F", "G7", "C"], profile="classical"
    )
    print(" - ".join(result.primary.roman_numerals))   # IV - V7 - I
    print(f"{result.primary.confidence:.0%}")          # ~92%
    print(result.primary.reasoning)
    # "Authentic cadence (V7 → I) with strong predominant motion."

asyncio.run(main())
```

---

## What it does

- **Chord progressions** → Roman numerals, key, cadences, inversions, multiple interpretations when the music is genuinely ambiguous.
- **Scales** → mode detection across all 7 modes of major + harmonic minor + melodic minor families.
- **Melodies** → contour, range, characteristic intervals, tonic inference.
- **Audio recordings** → key (via a multi-approach ensemble that disambiguates relative pairs like B minor vs D major), chord events with timestamps, cadence detection, region classification (stable / modulation / modal shift).
- **Style awareness** → classical, jazz, and pop pattern profiles produce different (and reasonable) interpretations of the same input.
- **Honest confidence** → calibrated 0.0–1.0 scores. Ambiguous music returns moderate scores, not fake certainty.

---

## Installation

```bash
# Core library
pip install harmonic-analysis

# With audio analysis (librosa + soundfile + ffmpeg)
pip install harmonic-analysis[audio]

# With music21 (MusicXML / MIDI parsing)
pip install harmonic-analysis[music21]

# With Bernstein-style educational explanations
pip install harmonic-analysis[educational]

# Everything (development)
pip install harmonic-analysis[dev]
```

The bare `import harmonic_analysis` works with just the core install. Audio symbols are exported as stubs that raise `AudioImportError` on first use if `librosa`/`soundfile` aren't installed — so you can grep for `analyze_audio_async` from the top level and the IDE will autocomplete it whether or not the extra is installed.

> **MP3/AAC support** also requires `ffmpeg` on your system PATH. WAV files load directly without it.

---

## Quick start

### Chord progression

```python
from harmonic_analysis import PatternAnalysisService

service = PatternAnalysisService()
result = service.analyze_with_patterns(   # sync wrapper; async version available
    chord_symbols=["C", "Am", "F", "G"],
    key_hint="C major",          # optional but improves Roman numerals
    profile="classical",          # "classical" | "jazz" | "pop"
)

print(result.primary.roman_numerals)   # ["I", "vi", "IV", "V"]
print(result.primary.confidence)       # e.g. 0.78
print(result.primary.reasoning)        # human-readable explanation

for alt in result.alternatives:
    print(alt.type, alt.confidence)    # other valid interpretations
```

### Scale and modal analysis

```python
from harmonic_analysis import UnifiedPatternService

service = UnifiedPatternService()
result = await service.analyze_with_patterns_async(
    notes=["D", "E", "F", "G", "A", "B", "C"],
    key_hint="D dorian",        # required for scale input
    profile="classical",
)

summary = result.primary.scale_summary
print(summary.detected_mode)            # "Dorian"
print(summary.parent_key)               # "C major"
print(summary.characteristic_notes)     # ["♭3", "♮6"]
```

### Melody analysis

```python
result = await service.analyze_with_patterns_async(
    melody=["C4", "D4", "E4", "G4", "E4", "D4", "C4"],
    key_hint="C major",
    profile="classical",
)

melody = result.primary.melody_summary
print(melody.contour)                   # "arch"
print(melody.range_semitones)           # 7
print(melody.melodic_characteristics)   # ["stepwise motion"]
```

### Audio (requires `[audio]` extra)

```python
from harmonic_analysis import analyze_audio_async

result = await analyze_audio_async(
    "song.wav",
    key_detection="default",          # ensemble of 4 approaches
    show_analysis_details=True,        # opt into the diagnostic panel
)

print(result.global_key.tonic, result.global_key.mode)   # "B" "Aeolian"
print(result.global_key.confidence)                       # 0.88
print(result.region.type)                                  # "stable"

for chord in result.chords:
    print(f"{chord.start_time:6.2f}s  {chord.chord_label}  conf={chord.confidence:.2f}")
```

The audio path uses an ensemble of independent key-detection approaches (template correlation, boundary chords, bass dominance, cadential motion). Single K-S correlation can't tell B Aeolian from D Ionian apart — they share the same notes — so orthogonal evidence breaks the tie. See [Audio Analysis Internals](docs/explanation/audio-analysis-internals.md) for the design rationale.

---

## Documentation

Organized using the [Diátaxis framework](https://diataxis.fr/). All docs live under [`docs/`](docs/).

| If you want to… | Start here |
|---|---|
| Run your first analysis | [Tutorials → Getting Started](docs/tutorials/getting-started.md) |
| Analyze a recording | [Tutorials → Audio Quick Start](docs/tutorials/audio-quickstart.md) |
| Solve a specific problem | [How-to Guides](docs/how-to/) |
| Look up an API | [Reference → API Quick Reference](docs/reference/api-quick-reference.md) |
| Understand the architecture | [Explanation → Architecture](docs/explanation/architecture.md) |
| Understand audio internals | [Explanation → Audio Analysis Internals](docs/explanation/audio-analysis-internals.md) |
| Cross-reference music theory | [Reference → Theory References](docs/reference/theory-references.md) |
| Read the doc index | [docs/README](docs/README.md) |

---

## Public API at a glance

```python
from harmonic_analysis import (
    # Chord progression / scale / melody / Roman numerals
    PatternAnalysisService,        # main service
    UnifiedPatternService,         # next-gen unified engine

    # Per-input simple functions
    analyze_scale,
    analyze_melody,

    # Result types
    AnalysisEnvelope,              # has .primary and .alternatives
    AnalysisSummary,
    ScaleMelodyAnalysisResult,
    AnalysisType,

    # Music theory data (30+ helpers)
    get_scale_notes,
    get_modal_characteristics,
    get_circle_of_fifths,
    get_relative_major_minor_pairs,
    get_modes_by_brightness,
    MODAL_CHARACTERISTICS,
    ALL_KEYS,
    # ... and many more

    # Character / emotional analysis
    get_mode_emotional_profile,
    analyze_progression_character,

    # Audio (requires [audio] extra; stubs raise AudioImportError otherwise)
    analyze_audio_async,
    analyze_audio,
    AudioAdapter,
    AudioAnalysisResult,
    ChordEvent,
    AudioImportError,
)

# Optional: educational content (requires [educational] extra)
from harmonic_analysis.educational import EducationalService

# Optional: MusicXML / MIDI parsing (requires [music21] extra)
from harmonic_analysis.integrations import Music21Adapter
```

Internal modules (`harmonic_analysis.core.*`, `harmonic_analysis.corpus_miner`, etc.) are intentionally not in `__all__`. They can be imported via their full paths if you really need them, but they aren't part of the stable contract.

---

## How it works (the short version)

The library runs three analytical lenses in parallel:

- **Functional** — Roman numerals, cadences, traditional voice-leading. Best for classical, pop, folk.
- **Modal** — mode detection, characteristic intervals, modal interchange. Best for jazz, rock, world music.
- **Chromatic** — secondary dominants, borrowed chords, chromatic mediants. Best for jazz, classical, progressive.

Each lens gathers evidence (cadential, structural, intervallic, harmonic, contextual). A unified pattern engine evaluates 36+ patterns across all three lenses simultaneously, aggregates the evidence, and applies quality-gated calibration to produce confidence scores. When confidences are close, the library returns multiple interpretations rather than picking one.

For audio, the chord-recognition layer feeds a four-approach key-detection ensemble that breaks relative-pair ties the K-S baseline can't.

For the full picture, read [Architecture Overview](docs/explanation/architecture.md) and [Pattern Engine Architecture](docs/explanation/pattern-engine-architecture.md).

---

## Confidence scores, briefly

| Range | Meaning |
|---|---|
| 0.85–1.00 | Very confident — clear, unambiguous patterns |
| 0.60–0.85 | Confident — some ambiguity, clear primary interpretation |
| 0.40–0.60 | Moderate — multiple valid interpretations likely |
| < 0.40    | Low — highly ambiguous or outside Western tonal/modal harmony |

When confidence is moderate, look at `result.alternatives`. The library is telling you the music is genuinely ambiguous, not failing.

---

## Demo

The repo ships an interactive demo (FastAPI backend + React frontend) at [`demo/`](demo/). It's not part of the published package — it's a reference integration showing how to wire the library into a web app.

```bash
cd demo && ./start_demo.sh
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

See `demo/README.md` for setup details.

---

## Project structure

```
harmonic-analysis/
├── src/harmonic_analysis/      # The library
│   ├── __init__.py             # Public API surface
│   ├── api/                    # Simple per-input functions (analyze_scale, etc.)
│   ├── audio/                  # Audio pipeline (chroma, chords, ensemble key detection)
│   ├── core/                   # Pattern engine, harmony analyzers, scale analysis
│   ├── corpus_miner/           # Training-data extraction (internal)
│   ├── dto.py                  # Result types (AnalysisEnvelope, AnalysisSummary, ...)
│   ├── educational/            # Optional Bernstein-style explanations
│   ├── integrations/           # music21 + audio adapters
│   ├── resources/              # Static assets (educational content, glossary)
│   ├── services/               # PatternAnalysisService, UnifiedPatternService
│   └── utils/                  # Helpers, constants, scales
│
├── tests/                      # Test suite
├── docs/                       # User-facing documentation (Diátaxis)
│   ├── tutorials/              # Learning-oriented
│   ├── how-to/                 # Problem-oriented
│   ├── reference/              # Look-up material
│   ├── explanation/            # Understanding-oriented
│   └── archive/                # Historical lib-dev notes
│
├── demo/                       # Reference web demo (not part of the package)
├── examples/                   # Standalone usage examples
└── scripts/                    # Maintenance scripts (test data generation, quality checks)
```

---

## License

MIT. See [LICENSE](LICENSE).

## Citation

```bibtex
@software{harmonic_analysis,
  title  = {Harmonic Analysis: A Musician-Focused Python Library},
  author = {Wachtel, Sam},
  year   = {2026},
  url    = {https://github.com/sammywachtel/harmonic-analysis}
}
```

## Acknowledgments

This library was extracted from the [Music Modes App](https://github.com/sammywachtel/music_modes_app), a comprehensive music theory toolkit. Special thanks to the music theory community for invaluable feedback on modal analysis and harmonic interpretation.
