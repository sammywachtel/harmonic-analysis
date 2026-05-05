# Harmonic Analysis Library 🎵

A comprehensive Python library that analyzes music the way musicians think about it - identifying chord progressions,
scales, modes, and harmonic relationships with detailed explanations of *why* it hears what it hears. Now featuring
unified scale analysis, roman numeral input, and advanced modal detection.

## ✅ UNIFIED PATTERN ENGINE — Production Ready

**Major Milestone Achieved**: The library now features a complete **unified pattern engine** that provides sophisticated harmonic analysis through a single, configurable architecture. This replaces the previous functional/modal analysis split with a more robust and extensible system.

### Pattern Engine Features
- **36 Unified Patterns**: Comprehensive pattern library covering harmonic, modal, chromatic, and melodic analysis
- **Scale Analysis**: Automatic mode detection for all major scale modes with pattern integration
- **Roman Numeral Input**: Direct roman numeral analysis with automatic chord conversion
- **Melody Analysis (NEW)**: Comprehensive melodic line analysis with tonic inference and modal recognition
- **Quality-Gated Calibration**: Conservative calibration with identity fallback prevents degradation
- **Evidence Aggregation**: Sophisticated conflict resolution and track-based scoring
- **Plugin Architecture**: Extensible system for custom pattern evaluators
- **100% Test Coverage**: All 76 pattern engine tests passing with comprehensive validation
- **Production Ready**: Complete migration from legacy analyzers with full backward compatibility

### Quick Pattern Analysis Example

```python
from harmonic_analysis import PatternAnalysisService

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

### ✅ Enhanced Key Processing

**Unified Engine**: The pattern engine provides intelligent key processing with modal parent key conversion and advanced key inference:

```python
# ✅ Correct: Provide key context
result = await service.analyze_with_patterns(['Am', 'G', 'F', 'E'], key_hint='A minor')

# ✅ Scale analysis with key context
result = await service.analyze_with_patterns_async(
    notes=['D', 'E', 'F', 'G', 'A', 'B', 'C'],
    key_hint='D dorian',
    profile='classical'
)

# ✅ Melody analysis with tonic inference (NEW)
result = await service.analyze_with_patterns_async(
    melody=['C4', 'D4', 'E4', 'F4', 'G4'],
    key_hint='C major',
    profile='classical'
)

# ✅ Roman numeral analysis with key context (NEW)
result = await service.analyze_with_patterns_async(
    romans=['I', 'vi', 'IV', 'V'],
    key_hint='C major',
    profile='classical'
)

# ❌ Without key context, scale/roman analysis will raise ValueError
```

**Why Key Context Matters**:
- **Modal Analysis**: Requires key context to distinguish between modes (Dorian vs. Natural Minor)
- **Roman Numerals**: Modal symbols (♭VII, ♯IV) need key validation for proper analysis
- **Pattern Recognition**: Many patterns depend on harmonic context within a key center

### Advanced Pattern Analysis Options

The pattern analysis service provides sophisticated configuration options:

```python
from harmonic_analysis import PatternAnalysisService

service = PatternAnalysisService()
result = await service.analyze_with_patterns_async(
    chord_symbols=['C', 'Am', 'F', 'G'],
    profile='classical',  # or 'jazz', 'pop'
    best_cover=True,     # Find optimal pattern coverage
    key_hint='C major'   # Optional key context
)
```

Configuration options:
- **Profile Selection**: Choose from classical, jazz, or pop pattern libraries
- **Coverage Optimization**: Find the best combination of overlapping patterns
- **Key Context**: Provide key hints for more accurate Roman numeral analysis
- **Confidence Thresholds**: Filter patterns by minimum confidence scores
- **Future-proof architecture** designed for advanced musical analysis

## What This Library Does (For Musicians)

This library listens to your chord progressions, scales, and melodies and tells you:

- **What key you're in** and how confident it is about that
- **The function of each chord** (tonic, dominant, subdominant, etc.) with full inversion analysis
- **What mode you might be using** (Dorian, Mixolydian, Phrygian, etc.)
- **Scale analysis with automatic mode detection** - recognizes all 7 modes of major scale
- **Roman numeral analysis with direct input** - analyze progressions using roman numerals
- **Advanced harmonic techniques** you're employing (secondary dominants, borrowed chords, chromatic mediants)
- **Chord inversions with proper figured bass notation** (⁶, ⁶⁴, ⁴²)
- **Multiple valid interpretations** when your music is ambiguous (which is often!)
- **Chromatic harmony analysis** including tonicization, modal mixture, and voice leading
- **Emotional character** of your progressions and scales
- **Intelligent key suggestions** that consider both harmonic function and context
- **Perfect bidirectional conversion** between chord symbols and Roman numerals

Think of it as having three music theory professors analyze your work simultaneously - one specializing in classical harmony, one in modal jazz, and one in chromatic/contemporary techniques - each explaining their reasoning with evidence-based analysis.

### User-Friendly API Design

The library provides a clean, focused API that exports only what you need:
- **Two main analysis services** for chord progressions (PatternAnalysisService, UnifiedPatternService)
- **Simple analysis functions** for scales and melodies (analyze_scale, analyze_melody)
- **Rich musical data access** for building UIs and applications (30+ helper functions)
- **Character analysis** for emotional profiling of modes and progressions
- **Result types** with comprehensive analysis information

**Optional features** are cleanly separated:
- Educational content: `from harmonic_analysis.educational import EducationalService`
- File I/O: `from harmonic_analysis.integrations import Music21Adapter`

## Installation

### Standard Installation (Core Features)

```bash
pip install harmonic-analysis
```

This installs the core harmonic analysis library with full pattern detection,
confidence scoring, and analysis capabilities.

### With Optional Features

```bash
# With educational features (Bernstein-style explanations)
pip install harmonic-analysis[educational]

# With music21 integration (file upload support)
pip install harmonic-analysis[music21]

# Multiple features
pip install harmonic-analysis[educational,music21,audio]
```

**Note:** The REST API is now part of the demo project (`demo/backend/rest_api/`) rather than the core library. See the [REST API Demo](#-rest-api-demo-new) section below for setup instructions.

### Development Installation

```bash
git clone https://github.com/sammywachtel/harmonic-analysis.git
cd harmonic-analysis
pip install -e .[dev]
```

The `dev` extra includes all optional features plus development tools (pytest, black, mypy, etc.).

### Understanding What's Available

The library has a **clean separation** between core features and optional extensions:

#### ✅ **Always Available** (Standard Installation)

Import directly from `harmonic_analysis`:

```python
from harmonic_analysis import (
    # Analysis Services
    PatternAnalysisService,          # Main chord progression analysis
    UnifiedPatternService,            # Next-gen unified engine

    # Simple Analysis Functions
    analyze_melody,                   # Analyze melodic sequences
    analyze_scale,                    # Analyze scale/mode

    # Musical Data API (30+ functions)
    get_circle_of_fifths,            # Circle of fifths data
    get_scale_notes,                 # Get notes for any scale
    get_relative_major_minor_pairs,  # Key relationships
    get_all_scale_systems,           # All available scale systems

    # Character Analysis
    get_mode_emotional_profile,      # Emotional profiling
    get_modes_by_brightness,         # Find modes by mood

    # Music Theory Constants
    MODAL_CHARACTERISTICS,           # Mode definitions
    ALL_KEYS,                        # All major/minor keys

    # Result Types
    AnalysisEnvelope,                # Main result container
    AnalysisSummary,                 # Analysis details
    ScaleMelodyAnalysisResult,       # Scale/melody results
)
```

#### 📦 **Optional Features** (Separate Installations)

**Educational Content** (Bernstein-style explanations):
```bash
pip install harmonic-analysis[educational]
```
```python
from harmonic_analysis.educational import EducationalService
service = EducationalService(level="intermediate")
```

**Music21 Integration** (File I/O for MusicXML, MIDI):
```bash
pip install harmonic-analysis[music21]
```
```python
from harmonic_analysis.integrations import Music21Adapter
adapter = Music21Adapter()
```

**Audio Analysis** (Analyze WAV/MP3 files for key, chords, and cadences):
```bash
pip install harmonic-analysis[audio]
```
```python
from harmonic_analysis import analyze_audio_async
result = await analyze_audio_async("path/to/file.wav")
```

#### 🔒 **Internal Components** (Not Exported)

These are used internally by the library but not exposed in the public API:
- Pattern engine internals (`PatternEngine`, `GlossaryProvider`, etc.)
- Calibration systems
- Corpus mining tools

If you need advanced customization, you can still import these via their full paths:
```python
# Advanced usage only - not recommended for most users
from harmonic_analysis.core.pattern_engine import PatternEngine
from harmonic_analysis.corpus_miner import CorpusExtractor
```

### Checking Feature Availability

You can check at runtime whether optional features are installed:

```python
from harmonic_analysis.educational import is_available, get_missing_dependencies

if is_available():
    print("Educational features are installed!")
    from harmonic_analysis.educational import EducationalService
    service = EducationalService(level="intermediate")
else:
    missing = get_missing_dependencies()
    print(f"Educational features not available.")
    print(f"Install with: pip install harmonic-analysis[educational]")
```

## 📚 Documentation

- **[API Quick Reference](docs/reference/api-quick-reference.md)** - Complete function signatures, parameters, and examples
- **[Getting Started Tutorial](docs/tutorials/getting-started.md)** - Step-by-step introduction
- **[How-to Guides](docs/how-to/)** - Task-specific solutions
- **[API Guide](docs/API_GUIDE.md)** - Comprehensive API documentation
- **[Development Guide](docs/DEVELOPMENT.md)** - Contributing and development workflow

### Audio Analysis (Optional)

- **[Audio Quick Start](docs/tutorials/audio-quickstart.md)** - 5-minute hands-on tutorial for analyzing audio files
- **[How to Analyze Audio](docs/how-to/audio-analysis.md)** - Task-oriented guide with toolkit migration recipes

## 📁 Project Structure

```
harmonic-analysis/
│
├── 📁 src/harmonic_analysis/           # Core library source code
│   ├── __init__.py                     # Main library exports and API
│   ├── analysis_types.py               # Analysis result type definitions
│   ├── dto.py                          # Data transfer objects
│   │
│   ├── 📁 core/                        # Core analysis engines
│   │   ├── functional_harmony.py       # Roman numeral & functional analysis
│   │   ├── chromatic_analysis.py       # Advanced chromatic harmony
│   │   ├── scale_melody_analysis.py    # Scale and melody analysis
│   │   ├── arbitration.py              # Analysis type arbitration logic
│   │   ├── validation_errors.py        # Input validation errors
│   │   ├── telemetry.py                # Analysis telemetry
│   │   │
│   │   └── 📁 pattern_engine/          # Pattern matching system (internal)
│   │       ├── pattern_engine.py       # Main pattern engine (internal use only)
│   │       ├── pattern_loader.py       # Pattern definition loader
│   │       ├── matcher.py              # Core pattern matching logic
│   │       ├── aggregator.py           # Evidence aggregation
│   │       ├── calibration.py          # Confidence calibration
│   │       ├── evidence.py             # Evidence data structures
│   │       ├── low_level_events.py     # Bass motion & voice leading detection
│   │       ├── token_converter.py      # Analysis → pattern tokens
│   │       ├── target_builder_unified.py # Unified target building
│   │       ├── plugin_registry.py      # Plugin system for evaluators
│   │       ├── glossary.py             # Musical term definitions
│   │       ├── glossary_provider.py    # Glossary lookup (internal)
│   │       └── schemas/                # Pattern definition schemas
│   │
│   ├── 📁 services/                    # High-level analysis services
│   │   ├── pattern_analysis_service.py # Main pattern analysis API
│   │   ├── unified_pattern_service.py  # Unified pattern service
│   │   └── analysis_arbitration_service.py # Analysis type arbitration
│   │
│   ├── 📁 utils/                       # Utility functions
│   │   ├── chord_logic.py              # Chord analysis logic
│   │   ├── chord_inversions.py         # Inversion analysis
│   │   ├── scales.py                   # Scale utilities
│   │   ├── music_theory_constants.py   # Constants and mappings
│   │   ├── analysis_helpers.py         # Analysis helper functions
│   │   └── api_helpers.py              # API utility functions
│   │
│   ├── 📁 integrations/                # 🆕 External library integrations
│   │   └── music21_adapter.py          # music21 library integration
│   │
│   ├── 📁 educational/                 # Educational content system
│   │   ├── educational_service.py      # Educational content service
│   │   ├── knowledge_base.py           # Music theory knowledge base
│   │   ├── formatter.py                # Educational content formatting
│   │   └── types.py                    # Educational content types
│   │
│   ├── 📁 corpus_miner/                # Corpus mining tools
│   │   ├── corpus_extractor.py         # Extract patterns from corpus
│   │   ├── pattern_labeler.py          # Label patterns in data
│   │   ├── target_builder.py           # Build training targets
│   │   └── types.py                    # Corpus mining types
│   │
│   └── 📁 resources/                   # Static resources
│       └── educational/                # Educational content resources
│
├── 📁 tests/                           # Comprehensive test suite (450+ tests)
│   ├── patterns/                        # Pattern engine tests
│   ├── integration/                     # Integration tests
│   │   ├── test_scale_analysis.py      # Scale analysis tests
│   │   ├── test_roman_numeral_analysis.py # Roman numeral tests
│   │   ├── test_melody_analysis.py     # Melody analysis tests
│   │   └── test_music21_adapter.py     # 🆕 music21 integration tests
│   └── unit/                            # Unit tests
│       └── test_chord_logic.py         # Chord parsing and logic tests
│
├── 📁 scripts/                         # Development and maintenance scripts
│   ├── quality_check.py                # Linting, typing, and test runner
│   ├── generate_comprehensive_multi_layer_tests.py # Test case generation
│   └── music_expert_review.py          # Expert review validation
│
├── 📁 docs/                            # Documentation (Diátaxis framework)
│   ├── tutorials/                       # Learning-oriented guides
│   ├── how-to/                          # Problem-solving guides
│   ├── reference/                       # Technical reference
│   ├── explanation/                     # Concept explanations
│   ├── TESTING.md                       # Testing strategy and guides
│   ├── DEVELOPMENT.md                   # Development workflow
│   └── (legacy docs being migrated)     # API_GUIDE.md, ARCHITECTURE.md, etc.
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
│   ├── start_demo.sh                   # Launcher script - starts backend + frontend servers
│   ├── frontend/                       # React frontend demo
│   ├── backend/                        # FastAPI REST API (moved from core library)
│   │   └── rest_api/                   # REST API endpoints and models
│
├── 📄 test_stage_b.py                  # 🆕 Pattern engine Stage B tests
├── 📄 debug_stage_b.py                 # 🆕 Pattern debugging tools
├── 📄 pyproject.toml                   # Project configuration
├── 📄 requirements.txt                 # Production dependencies
├── 📄 requirements-dev.txt             # Development dependencies
└── 📄 README.md                        # This file
```

### Key Architecture Highlights

#### 🎯 Clean Public API
- **Analysis Services**: `PatternAnalysisService` (legacy) and `UnifiedPatternService` (recommended)
- **Simple Functions**: `analyze_scale()`, `analyze_melody()` for quick analysis
- **Musical Data API**: 30+ helper functions for accessing musical theory data
- **Result Types**: Rich DTOs with comprehensive analysis information
- **Optional Features**: Educational and Music21 integration via separate imports

#### 🔒 Internal Architecture (Not Exported)
- **Unified Pattern Engine**: 36 patterns, quality-gated calibration, evidence aggregation
- **Multi-Engine Analysis**: Functional, modal, and chromatic analyzers run in parallel
- **Plugin System**: Extensible evaluator registry for custom patterns
- **Location**: `src/harmonic_analysis/core/pattern_engine/` (internal use only)

#### 🧠 Analysis Capabilities
- **Functional**: Roman numerals, cadences, traditional harmony
- **Modal**: Mode detection, modal interchange, characteristic tones
- **Chromatic**: Secondary dominants, borrowed chords, advanced harmony
- **Character**: Emotional profiling and brightness classification

#### 🔄 Bidirectional System
- **Analysis → Patterns**: Detects patterns in chord progressions
- **Suggestions**: Recommends optimal analysis approaches
- **Validation**: Cross-validates results across multiple engines

## Quick Start for Musicians

### Analyzing Chord Progressions

```python
import asyncio
from harmonic_analysis import PatternAnalysisService

async def analyze_my_progression():
    # Classic I-vi-IV-V progression
    service = PatternAnalysisService()
    result = await service.analyze_with_patterns_async(['C', 'Am', 'F', 'G'], profile="classical")

    print(f"Roman numerals: {' - '.join(result.primary.roman_numerals)}")
    print(f"Key: {result.primary.key_signature}")
    # Output: Roman numerals: I - vi - IV - V
    # Output: Key: C major

    print(f"Confidence: {result.primary.confidence:.0%}")
    # Output: "Confidence: 75%"


asyncio.run(analyze_my_progression())
```

### 🌐 REST API Demo (NEW!)

The demo project includes a production-ready REST API built with FastAPI. Perfect for web applications, microservices, and remote analysis:

```bash
# Clone the repository
git clone https://github.com/sammywachtel/harmonic-analysis.git
cd harmonic-analysis

# Install demo dependencies
pip install -r demo/requirements.txt

# Start both backend and frontend with the demo launcher
cd demo
./start_demo.sh

# Or start the backend API server only:
cd demo
uvicorn demo.backend.rest_api.main:app --reload

# API is now running at http://localhost:8000
# OpenAPI docs available at http://localhost:8000/docs
```

#### API Endpoints

**Analyze Chord Progressions** (POST `/api/analyze`)
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "chords": ["Dm", "G7", "C"],
    "key": "C major",
    "profile": "classical"
  }'
```

**Analyze Scales** (POST `/api/analyze/scale`)
```bash
curl -X POST "http://localhost:8000/api/analyze/scale" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": ["C", "D", "E", "F", "G", "A", "B"],
    "key": "C major"
  }'
```

**Analyze Melodies** (POST `/api/analyze/melody`)
```bash
curl -X POST "http://localhost:8000/api/analyze/melody" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": ["C4", "D4", "E4", "F4", "G4"],
    "key": "C major"
  }'
```

**Upload Music Files** (POST `/api/analyze/file`)
```bash
curl -X POST "http://localhost:8000/api/analyze/file" \
  -F "file=@my_score.musicxml" \
  -F "add_chordify=true" \
  -F "label_chords=true" \
  -F "run_analysis=true" \
  -F "profile=classical"
```

**Glossary Lookup** (GET `/glossary/{term}`)
```bash
curl "http://localhost:8000/glossary/half_cadence"
```

> **Note**: The glossary endpoint is part of the demo REST API. The underlying `GlossaryProvider` is an internal component not exported in the main library API.

#### Python Client Example

```python
import httpx
import asyncio

async def analyze_via_api():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/analyze",
            json={
                "chords": ["Dm", "G7", "C"],
                "key": "C major",
                "profile": "classical"
            }
        )
        result = response.json()
        print(f"Analysis: {result['summary']}")
        print(f"Roman numerals: {result['analysis']['primary']['roman_numerals']}")

asyncio.run(analyze_via_api())
```

#### JavaScript/TypeScript Client Example

```typescript
const response = await fetch('http://localhost:8000/api/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    chords: ['Dm', 'G7', 'C'],
    key: 'C major',
    profile: 'classical'
  })
});

const result = await response.json();
console.log('Analysis:', result.summary);
```

#### API Features

- **🔥 FastAPI Framework**: High-performance async API with automatic validation
- **📖 OpenAPI Documentation**: Interactive docs at `/docs` (Swagger UI)
- **🎼 File Upload Support**: Analyze MusicXML and MIDI files
- **🔒 CORS Configured**: Ready for frontend integration
- **✅ Pydantic Validation**: Automatic request/response validation
- **📊 Comprehensive Responses**: JSON-formatted analysis with full details
- **🎯 Multiple Endpoints**: Dedicated endpoints for chords, scales, melodies, and files

#### Running in Production

```bash
# Production deployment with Gunicorn + Uvicorn (from demo directory)
cd demo
gunicorn backend.rest_api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

See [API tests](demo/tests/api/test_rest_api.py) for comprehensive usage examples.

### Analyzing Scales with Enhanced Summaries (NEW!)

The unified pattern service provides comprehensive scale analysis with mode detection and characteristic intervals:

```python
from harmonic_analysis import UnifiedPatternService

async def analyze_modal_scales():
    service = UnifiedPatternService()

    # Dorian scale analysis with rich summary data
    result = await service.analyze_with_patterns_async(
        notes=['D', 'E', 'F', 'G', 'A', 'B', 'C'],
        key_hint='D dorian'  # Required for scale analysis
    )

    # Access enhanced scale summary (NEW in Iteration 15!)
    if result.primary.scale_summary:
        scale_summary = result.primary.scale_summary
        print(f"Detected Mode: {scale_summary.detected_mode}")           # "Dorian"
        print(f"Parent Key: {scale_summary.parent_key}")                 # "C major"
        print(f"Characteristic Notes: {scale_summary.characteristic_notes}")  # ["♭3", "♮6"]
        print(f"Scale Notes: {' - '.join(scale_summary.notes)}")         # "D - E - F - G - A - B - C"

    # Enhanced reasoning explains the mode
    print(f"Analysis: {result.primary.reasoning}")
    # "Detected Dorian scale with characteristic ♭3 and ♮6 intervals"

asyncio.run(analyze_modal_scales())
```

### Analyzing Melodies

Melodies are special - the library tries to figure out what note feels like "home":

```python
from harmonic_analysis import UnifiedPatternService

async def analyze_my_melody():
    service = UnifiedPatternService()

    # A melody that emphasizes D within C major scale
    result = await service.analyze_with_patterns_async(
        melody=['D4', 'E4', 'F4', 'G4', 'A4', 'C5', 'B4', 'A4', 'G4', 'F4', 'E4', 'D4'],
        key_hint='D dorian',  # Required for melody analysis
        profile='classical'
    )

    print(f"Analysis type: {result.primary.type}")
    # Output: "Analysis type: AnalysisType.MODAL"

    print(f"Key signature: {result.primary.key_signature}")
    # Output: "Key signature: D dorian"

    print(f"Confidence: {result.primary.confidence:.0%}")
    # Output: "Confidence: 78%"

    # Access rich melody summary (NEW!)
    if result.primary.melody_summary:
        melody_summary = result.primary.melody_summary
        print(f"Melodic contour: {melody_summary.contour}")           # "arch"
        print(f"Range: {melody_summary.range_semitones} semitones")   # 14
        print(f"Characteristics: {melody_summary.melodic_characteristics}")  # ["stepwise motion"]
        print(f"Leading tone resolutions: {melody_summary.leading_tone_resolutions}")  # 2

asyncio.run(analyze_my_melody())
```

### Analyzing Chord Inversions 🎼

The library provides comprehensive inversion analysis with proper figured bass notation:

```python
import asyncio
from harmonic_analysis import PatternAnalysisService

async def analyze_inversions():
    # Progression with multiple inversions in F major
    chords = ['D', 'Gm/Bb', 'D/A', 'Gm', 'F/C', 'C', 'F']

    service = PatternAnalysisService()
    result = await service.analyze_with_patterns_async(
        chords,
        key_hint='F major',
        profile='classical'
    )

    print("Analysis:", result.primary.reasoning)
    # Output: "Functional progression with secondary dominants"

    print("Roman numerals:", result.primary.roman_numerals)
    # Output: ['V/ii', 'ii⁶', 'V/ii⁶⁴', 'ii', 'I⁶⁴', 'V', 'I']

    # The library handles inversions through the pattern analysis system
    # All inversion symbols (⁶, ⁶⁴, ⁴²) are preserved in roman numeral analysis

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
from harmonic_analysis import PatternAnalysisService

async def explore_interpretations():
    # This progression can be heard multiple ways
    chords = ['Am', 'F', 'C', 'G']

    # Initialize the analysis service
    service = PatternAnalysisService()

    # Analyze with classical profile (functional harmony focus)
    result = await service.analyze_with_patterns_async(
        chords,
        profile="classical",
        best_cover=True  # Enable multiple interpretations
    )

    print(f"Primary interpretation: {result.primary.type.value}")
    print(f"  Roman numerals: {' - '.join(result.primary.roman_numerals)}")
    print(f"  Confidence: {result.primary.confidence:.0%}")

    print(f"\nAlternative interpretations ({len(result.alternatives)}):")
    for i, alt in enumerate(result.alternatives, 1):
        print(f"  {i}. {alt.type.value}: {' - '.join(alt.roman_numerals)}")
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

    service = PatternAnalysisService()
    result = await service.analyze_with_patterns_async(chords, profile="classical")

    if result.primary.type.value == "functional":
        print("Chromatic elements detected:")

        # Chromatic elements
        if result.primary.chromatic_elements:
            print("\n🎯 Chromatic Elements:")
            for ce in result.primary.chromatic_elements:
                print(f"  {ce.type}: {ce.chord_symbol}")
                if ce.resolution_to:
                    print(f"    Resolves to: {ce.resolution_to}")

        # Detected patterns
        if result.primary.patterns:
            print("\n🎨 Harmonic Patterns:")
            for pattern in result.primary.patterns:
                print(f"  {pattern.name} (score: {pattern.score:.2f})")

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

    service = PatternAnalysisService()
    for chords, description in progressions:
        result = await service.analyze_with_patterns_async(chords, profile="classical")
        print(f"\n{description}: {' - '.join(chords)}")
        print(f"  Primary: {result.primary.type.value}")
        print(f"  Roman numerals: {' - '.join(result.primary.roman_numerals)}")
        print(f"  Alternatives: {len(result.alternatives)}")

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
service = PatternAnalysisService()
result = await service.analyze_with_patterns_async(['Em', 'F', 'Em'], profile="classical")

# Get detected mode
if result.primary.type.value == 'modal':
    mode_name = result.primary.mode  # "E Phrygian"

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
from harmonic_analysis import UnifiedPatternService

service = UnifiedPatternService()

# Scale analysis with enhanced modal detection
scale_result = await service.analyze_with_patterns_async(
    notes=['D', 'E', 'F', 'G', 'A', 'B', 'C'],
    key_hint='D dorian',  # Required for scale analysis
    profile='classical'
)

# Access rich scale summary (NEW!)
if scale_result.primary.scale_summary:
    scale_summary = scale_result.primary.scale_summary
    print(f"Detected mode: {scale_summary.detected_mode}")           # "Dorian"
    print(f"Parent key: {scale_summary.parent_key}")                 # "C major"
    print(f"Characteristic notes: {scale_summary.characteristic_notes}")  # ["♭3", "♮6"]

# Melody analysis with contour detection
melody_result = await service.analyze_with_patterns_async(
    melody=['C4', 'D4', 'E4', 'G4', 'E4', 'D4', 'C4'],
    key_hint='C major',  # Required for melody analysis
    profile='classical'
)

# Access rich melody summary (NEW!)
if melody_result.primary.melody_summary:
    melody_summary = melody_result.primary.melody_summary
    print(f"Melodic contour: {melody_summary.contour}")             # "arch"
    print(f"Range: {melody_summary.range_semitones} semitones")     # 7
    print(f"Characteristics: {melody_summary.melodic_characteristics}")  # ["stepwise motion"]
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
from harmonic_analysis import PatternAnalysisService

async def add_key_example():
    service = PatternAnalysisService()

    # Classic ii-V-I progression without key context
    progression = ['Dm7', 'G7', 'Cmaj7']
    result = await service.analyze_with_patterns_async(progression, profile='classical')

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
        better_result = await service.analyze_with_patterns_async(
            progression,
            key_hint=suggestion.suggested_key,
            profile='classical'
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
    service = PatternAnalysisService()

    # Jazz progression with WRONG parent key
    jazz_progression = ['A', 'E/G#', 'B7sus4/F#', 'E', 'A/C#', 'G#m/B', 'F#m/A', 'E/G#']

    # Force wrong key (C major doesn't fit this progression)
    result = await service.analyze_with_patterns_async(
        jazz_progression,
        key_hint='C major',
        profile='jazz'
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
        no_key_result = await service.analyze_with_patterns_async(
            jazz_progression,
            profile='jazz'
        )
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
    service = PatternAnalysisService()

    # Ambiguous progression with suboptimal key
    progression = ['Am', 'F', 'C', 'G']

    # Provide A minor key (works, but C major might be better)
    result = await service.analyze_with_patterns_async(
        progression,
        key_hint='A minor',
        profile='classical'
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
service = PatternAnalysisService()
chords = ['Am', 'Dm', 'G', 'C']

# In C major context: vi - ii - V - I
result1 = await service.analyze_with_patterns_async(
    chords,
    key_hint="C major",
    profile="classical"
)

# In A minor context: i - iv - bVII - bIII
result2 = await service.analyze_with_patterns_async(
    chords,
    key_hint="A minor",
    profile="classical"
)
```

### It Recognizes Musical Idioms

The library knows common patterns:

- **Cadences**: Perfect authentic, plagal, deceptive, half
- **Progressions**: Circle of fifths, descending thirds, chromatic bass lines
- **Modal characteristics**: bVII in Mixolydian, #IV in Lydian, etc.
- **Jazz conventions**: ii-V-I, tritone substitutions, modal interchange

### It Handles Edge Cases Gracefully

```python
service = PatternAnalysisService()

# Single chord - lower confidence
result = await service.analyze_with_patterns_async(['C'], profile="classical")
# Result: "Single chord: C major" (confidence: ~45%)

# Ambiguous progression
result = await service.analyze_with_patterns_async(
    ['C', 'Dm', 'Eb', 'F'],
    profile="classical"
)
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
from harmonic_analysis import PatternAnalysisService

# Initialize the service
service = PatternAnalysisService()

# Fine-tune the analysis with various options
result = await service.analyze_with_patterns_async(
    chord_symbols=['G', 'C', 'D', 'Em'],
    key_hint="G major",      # Provide tonal context
    profile="classical",     # Choose pattern library (classical/jazz/pop)
    best_cover=True         # Find optimal pattern coverage
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

## 🔧 Common Usage Examples

### Working with Musical Data API
```python
from harmonic_analysis import (
    get_circle_of_fifths,
    get_relative_major_minor_pairs,
    get_scale_notes,
    get_all_scale_systems,
    normalize_note_name
)

# Get circle of fifths for UI display
circle = get_circle_of_fifths()
print(circle['major'])  # ['C', 'G', 'D', 'A', 'E', 'B', 'F♯', ...]

# Get relative major/minor pairs
pairs = get_relative_major_minor_pairs()
print(pairs['C major'])  # 'A minor'

# Get scale notes for any mode
notes = get_scale_notes('D', 'Dorian')
print(notes)  # ['D', 'E', 'F', 'G', 'A', 'B', 'C']

# Explore all scale systems
systems = get_all_scale_systems()
print(list(systems.keys()))  # ['major_scale', 'melodic_minor', 'harmonic_minor', ...]

# Normalize user input
normalized = normalize_note_name('Db')  # Returns 'D♭' with proper unicode
```

### Character and Emotional Analysis
```python
from harmonic_analysis import (
    get_mode_emotional_profile,
    get_modes_by_brightness,
    analyze_progression_character
)

# Get emotional profile for a mode
profile = get_mode_emotional_profile('Dorian')
print(f"Brightness: {profile.brightness}")  # "neutral"
print(f"Energy: {profile.energy}")  # "medium"
print(f"Primary emotions: {profile.primary_emotions}")  # ["contemplative", "jazzy"]

# Find modes by emotional quality
bright_modes = get_modes_by_brightness('bright')
print(bright_modes)  # ["Ionian", "Lydian", "Mixolydian"]

dark_modes = get_modes_by_brightness('dark')
print(dark_modes)  # ["Phrygian", "Aeolian", "Locrian"]
```

### Music Theory Utilities
```python
from harmonic_analysis import (
    get_interval_name,
    MODAL_CHARACTERISTICS,
    get_modal_characteristics,
    ALL_KEYS,
    canonicalize_key_signature
)

# Interval analysis
print(get_interval_name(7))  # "Perfect 5th"
print(get_interval_name(3))  # "Minor 3rd"

# Modal characteristics
characteristics = get_modal_characteristics('Dorian')
print(characteristics.brightness)  # "neutral"
print(characteristics.characteristic_degrees)  # ['1', '♭3', '6', '♭7']

# Key signature utilities
print(ALL_KEYS[:5])  # ['C major', 'G major', 'D major', ...]
canonical = canonicalize_key_signature('D♭ major')  # Standardizes notation
```

### Advanced Chromatic Analysis
```python
from harmonic_analysis import PatternAnalysisService

async def chromatic_example():
    service = PatternAnalysisService()
    chords = ['C', 'A7', 'Dm', 'G7', 'C']

    # Analyze with chromatic pattern detection
    result = await service.analyze_with_patterns_async(
        chords,
        key_hint='C major',
        profile='classical'
    )

    # Access detected chromatic elements
    if result.primary.chromatic_elements:
        print(f"Chromatic elements found: {len(result.primary.chromatic_elements)}")
        for elem in result.primary.chromatic_elements:
            print(f"  {elem.type}: {elem.chord_symbol}")
            if elem.resolution_to:
                print(f"    → Resolves to: {elem.resolution_to}")
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

- **Scale**: `notes=['C', 'D', 'E', 'F', 'G', 'A', 'B']` - A collection of notes (unordered, no rhythm)
    - Returns: Scale summary with mode detection, parent key, and characteristic intervals
- **Melody**: `melody=['C4', 'D4', 'E4', 'F4', 'G4']` - A sequence of notes (ordered, implies rhythm/contour)
    - Returns: Melody summary with contour analysis, range, intervals, and melodic characteristics

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
