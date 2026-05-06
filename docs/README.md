# Harmonic Analysis Library Documentation

Documentation organized using the [Diátaxis framework](https://diataxis.fr/).

## 📚 Documentation Map

### 🎓 [Tutorials](tutorials/) — *Learning-oriented*

Step-by-step lessons that take you from zero to working code.

- [Getting Started](tutorials/getting-started.md) — your first chord progression analysis
- [Audio Quick Start](tutorials/audio-quickstart.md) — analyze a WAV/MP3 in five minutes (requires `[audio]` extra)

### 🔧 [How-to Guides](how-to/) — *Problem-oriented*

Practical recipes for specific tasks.

- [API Integration](how-to/api-integration.md) — drop the library into Flask, FastAPI, async apps, or desktop UIs
- [Audio Analysis](how-to/audio-analysis.md) — recover key, chords, and cadences from recordings; ensemble key detection and diagnostic panel
- [Music21 Integration](how-to/music21-integration.md) — parse MusicXML and MIDI files
- [Debugging Patterns](how-to/debugging-patterns.md) — inspect the pattern engine when results surprise you
- [Troubleshooting](how-to/troubleshooting.md) — common errors and how to fix them

### 📖 [Reference](reference/) — *Information-oriented*

Look-up material: signatures, schemas, glossaries.

- [API Reference](reference/api-reference.md) — full public-API surface for the analysis services
- [API Quick Reference](reference/api-quick-reference.md) — condensed cheat sheet
- [Audio API Reference](reference/audio-api.md) — `analyze_audio_async`, `AudioAdapter`, ensemble parameters, result shapes
- [Pattern DSL](reference/pattern-dsl.md) — schema for defining patterns
- [Glossary](reference/glossary.md) — musical terminology used throughout the library
- [Theory References](reference/theory-references.md) — open-access music theory sources cross-referenced to library features

### 🧠 [Explanation](explanation/) — *Understanding-oriented*

Why the system works the way it does.

- [Architecture Overview](explanation/architecture.md) — service layer, pattern engine, audio pipeline
- [Pattern Engine Architecture](explanation/pattern-engine-architecture.md) — internal design of the unified pattern engine
- [Audio Analysis Internals](explanation/audio-analysis-internals.md) — chroma, chord recognition, ensemble key detection
- [Confidence Calibration Theory](explanation/confidence-calibration.md) — music-theory grounding for confidence scores
- [Calibration Methods](explanation/calibration-methods.md) — technical calibration approaches (Platt, isotonic, identity)
- [Glossary System](explanation/glossary-system.md) — feature enrichment and UI labels
- [Corpus Mining](explanation/corpus-mining.md) — training-data extraction pipeline

### 🗂️ [Archive](archive/)

Historical library development notes — design proposals, music21 integration strategy planning, dev workflow guides. Not part of the user-facing surface; preserved for context. See [archive/README](archive/README.md) (if present) or browse the folder.

## 🚀 Quick Start

**New?** → [Getting Started Tutorial](tutorials/getting-started.md)

**Solving a specific problem?** → [How-to Guides](how-to/)

**Looking up an API?** → [API Quick Reference](reference/api-quick-reference.md) or [API Reference](reference/api-reference.md)

**Curious how it works?** → [Architecture Overview](explanation/architecture.md)

## 🔄 Maintaining These Docs

- **Same-commit rule:** code changes update docs in the same commit. Documentation drift is worse than no documentation.
- **Diátaxis routing:** new docs go in exactly one of tutorials/how-to/reference/explanation. If unsure, ask: "is this teaching, doing, looking up, or understanding?"
- **Archive lib-dev artifacts:** design proposals, planning docs, and contributor workflow notes belong in `archive/`, not the user-facing tree.

---

*This documentation follows the [Diátaxis framework](https://diataxis.fr/) for systematic documentation architecture.*
