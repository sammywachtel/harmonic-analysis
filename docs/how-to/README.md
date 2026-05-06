# How-to Guides — Problem-Oriented

Practical recipes for specific tasks.

## Available Guides

### 🔌 [API Integration](api-integration.md)

**Solve:** "How do I integrate this library into my application?"
**Covers:** Flask, FastAPI, async patterns, desktop apps, error handling, caching.

### 🎧 [Audio Analysis](audio-analysis.md)

**Solve:** "How do I analyze a WAV/MP3 file?"
**Covers:** `analyze_audio_async`, ensemble key detection (`key_detection="default"|"ks_only"|"full"`), the diagnostic panel (`show_analysis_details=True`), per-approach weight overrides, segment selection, toolkit migration recipes.

### 🎼 [Music21 Integration](music21-integration.md)

**Solve:** "How do I parse MusicXML or MIDI files?"
**Covers:** `Music21Adapter`, chord extraction, key inference, feeding score data into the pattern services.

### 🐛 [Debugging Patterns](debugging-patterns.md)

**Solve:** "Why did the pattern engine match (or miss) this progression?"
**Covers:** Inspecting evidence, tracing pattern matches, understanding scoring decisions.

### 🔍 [Troubleshooting](troubleshooting.md)

**Solve:** "Something's wrong — where do I start?"
**Covers:** Common errors (ImportError, missing extras, async/sync confusion), result-field gotchas, low-confidence diagnoses.

## Quick Problem Solver

**…analyze chord progressions in my web app**
→ [API Integration](api-integration.md)

**…analyze a recording**
→ [Audio Analysis](audio-analysis.md)

**…figure out why the analyzer disagreed with me**
→ [Debugging Patterns](debugging-patterns.md) + [Troubleshooting](troubleshooting.md)

**…parse MusicXML / MIDI**
→ [Music21 Integration](music21-integration.md)

## Related

- **Before starting:** [Getting Started Tutorial](../tutorials/getting-started.md)
- **Looking up methods:** [API Reference](../reference/api-reference.md)
- **Understanding the system:** [Architecture Overview](../explanation/architecture.md)
- **Pattern definitions:** [Pattern DSL](../reference/pattern-dsl.md)

---

*Need immediate help? Start with [Troubleshooting](troubleshooting.md).*
