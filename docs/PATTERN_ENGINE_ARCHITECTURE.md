# Pattern Engine Architecture

## Overview

The Unified Pattern Engine represents a complete redesign of harmonic analysis in the library, unifying functional and modal analysis through a single, configurable pipeline. This architecture addresses the limitations of the previous fork-based approach and implements the vision described in `music-alg-6a-engine-redesign.md`.

## Core Design Principles

### 1. Single Source of Truth
- **One Engine**: All pattern matching goes through the unified `PatternEngine`
- **One Schema**: Shared pattern definitions for functional and modal analysis
- **One Aggregator**: Unified evidence combination and scoring

### 2. Config-First Patterns
- **Declarative**: Most patterns defined in JSON, not code
- **Testable**: Pattern definitions are data, not logic
- **Extensible**: New patterns added via configuration

### 3. Evidence-Based Architecture
- **Evidence Collection**: Patterns produce `Evidence` objects with features and track contributions
- **Aggregation**: Evidence combined using configurable strategies (soft-NMS, max-pooling)
- **Calibration**: Raw scores calibrated using corpus-based mappings with quality gates

### 4. Quality Gates
- **Conservative Calibration**: Strict thresholds prevent degradation
- **Identity Fallback**: When data is insufficient, use raw scores
- **Validation**: Schema validation ensures pattern integrity

## Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Pattern Engine                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐   │
│  │   Pattern   │ │   Plugin     │ │   Analysis          │   │
│  │   Loader    │ │   Registry   │ │   Context           │   │
│  └─────────────┘ └──────────────┘ └─────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                Evidence Matching                        │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │ │
│  │  │  Sequence   │ │  Constraint │ │    Plugin       │   │ │
│  │  │  Matching   │ │  Checking   │ │  Evaluation     │   │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────┘   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                               │                             │
│                               ▼                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                  Aggregator                             │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │ │
│  │  │ Conflict    │ │ Track       │ │   Diversity     │   │ │
│  │  │ Resolution  │ │ Weighting   │ │   Bonus         │   │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────┘   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                               │                             │
│                               ▼                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 Calibrator                              │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │ │
│  │  │ Quality     │ │ Platt/      │ │   Identity      │   │ │
│  │  │ Gates       │ │ Isotonic    │ │   Fallback      │   │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────┘   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                               │                             │
│                               ▼                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              AnalysisEnvelope                           │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │ │
│  │  │  Primary    │ │ Alternatives│ │    Evidence     │   │ │
│  │  │  Analysis   │ │             │ │    Traces       │   │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────┘   │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### Pattern Loader (`pattern_loader.py`)
- **Purpose**: Load and validate pattern definitions from JSON
- **Features**:
  - JSON Schema validation
  - Pattern merging from multiple files
  - Helpful error messages with path context
- **Schema**: Enforces required fields, valid enums, proper structure

### Plugin Registry (`plugin_registry.py`)
- **Purpose**: Registry for confidence evaluation functions
- **Built-in Evaluators**:
  - `identity`: Pass-through evaluation
  - `logistic_default`: Standard functional analysis
  - `logistic_dorian`: Modal-specific evaluation
- **Custom Plugins**: Register functions that take `(pattern, context) -> Evidence`

### Evidence System (`evidence.py`)
- **Purpose**: Internal representation of pattern match evidence
- **Structure**:
  ```python
  Evidence(
      pattern_id="cadence.authentic.perfect",
      track_weights={"functional": 0.9, "modal": 0.1},
      features={"has_auth_cadence": 1.0, "tonal_clarity": 0.85},
      raw_score=0.87,
      uncertainty=0.05,
      span=(2, 4)  # Chord indices
  )
  ```

### Aggregator (`aggregator.py`)
- **Purpose**: Combine evidence from multiple patterns into unified scores
- **Conflict Resolution**:
  - **Soft NMS**: Decay overlapping evidence exponentially
  - **Max Pool**: Keep only highest-scoring in overlapping regions
  - **None**: No conflict resolution
- **Track Aggregation**: Soft-OR combination prevents score inflation
- **Diversity Bonus**: Reward evidence from multiple pattern families

### Calibrator (`calibration.py`)
- **Purpose**: Map raw confidence scores to calibrated probabilities
- **Quality Gates**:
  - Minimum sample count (default: 50)
  - Minimum target variance (default: 0.01)
  - Minimum correlation (default: 0.1)
  - Maximum ECE increase (default: 0.05)
- **Methods**: Platt scaling, Isotonic regression, Identity fallback
- **Validation**: ECE and Brier score monitoring

### Target Builder (`target_builder.py`)
- **Purpose**: Construct training targets for calibration
- **Sources**:
  - Corpus annotations
  - Expert judgments
  - Heuristic rules
- **Combination**: Weighted averaging for overlapping annotations

## Pattern Definition Format

### JSON Schema
Patterns are defined in JSON files following this structure:

```json
{
  "version": 1,
  "patterns": [
    {
      "id": "cadence.authentic.perfect",
      "name": "Perfect Authentic Cadence",
      "scope": ["harmonic"],
      "track": ["functional"],
      "matchers": {
        "roman_seq": ["V", "I"],
        "constraints": {
          "soprano_degree": [1],
          "position": "end"
        }
      },
      "evidence": {
        "weight": 0.95,
        "features": ["has_auth_cadence", "tonal_clarity"],
        "confidence_fn": "logistic_default"
      },
      "metadata": {
        "tags": ["cadence", "functional"],
        "priority": 90
      }
    }
  ]
}
```

### Pattern Fields

- **id**: Unique identifier (e.g., `"cadence.authentic.perfect"`)
- **name**: Human-readable name
- **scope**: Analysis domains (`"harmonic"`, `"melodic"`, `"scale"`)
- **track**: Analysis tracks (`"functional"`, `"modal"`)
- **matchers**: Pattern matching criteria
- **evidence**: Scoring configuration
- **metadata**: Tags, priority, documentation

### Matcher Types

1. **Sequence Matchers**:
   - `chord_seq`: Match chord symbol sequences
   - `roman_seq`: Match roman numeral sequences
   - `interval_seq`: Match melodic intervals

2. **Constraints**:
   - `soprano_degree`: Required soprano scale degrees
   - `bass_motion`: Bass line movement patterns
   - `key_context`: Diatonic vs chromatic context
   - `position`: Location in progression (start/middle/end)

3. **Window Options**:
   - `len`: Pattern length in chords
   - `overlap_ok`: Allow overlapping matches
   - `min_gap`: Minimum gap between matches

## Analysis Flow

### 1. Context Preparation
```python
context = AnalysisContext(
    key="C major",
    chords=["C", "F", "G", "C"],
    roman_numerals=["I", "IV", "V", "I"],
    melody=[],
    scales=[],
    metadata={}
)
```

### 2. Pattern Matching
- Load patterns from JSON
- Apply matchers to find sequence matches
- Check constraints for each match
- Call confidence functions to generate evidence

### 3. Evidence Aggregation
- Apply conflict resolution to overlapping evidence
- Aggregate evidence by analysis track (functional/modal)
- Add diversity bonus for multiple pattern types
- Generate debug breakdown

### 4. Calibration
- Apply quality-gated calibration mapping
- Fall back to identity if gates fail
- Preserve ranking while improving calibration

### 5. Result Construction
- Determine primary analysis type
- Generate alternatives for ambiguous cases
- Convert evidence to public DTOs
- Package in AnalysisEnvelope

## Configuration and Extensibility

### Adding New Patterns
1. Define pattern in JSON following schema
2. Test pattern matches expected progressions
3. Add to pattern file or separate module
4. Validate with schema checker

### Custom Evaluators
```python
def custom_evaluator(pattern, context):
    # Extract features from context
    features = extract_features(context)

    # Calculate raw score
    raw_score = compute_score(features, pattern)

    # Return evidence
    return Evidence(
        pattern_id=pattern["id"],
        track_weights={"functional": 0.8},
        features=features,
        raw_score=raw_score,
        uncertainty=None,
        span=context["span"]
    )

# Register evaluator
engine.plugins.register("custom", custom_evaluator)
```

### Corpus Integration
```python
# Build training data from corpus
annotations = target_builder.build_corpus_annotations(corpus_data)

# Train calibration mapping
evidences = collect_training_evidences()
targets = target_builder.build_targets(evidences, annotations)
mapping = calibrator.fit(raw_scores, targets)

# Apply to engine
engine._calibration_mapping = mapping
```

## Migration Strategy

### Phase 1: Scaffolding (✅ Complete)
- Core architecture components
- Basic pattern definitions
- Unit test coverage
- Documentation framework

### Phase 2: Pattern Migration
- Port high-impact patterns from existing analyzer
- Maintain parity testing during transition
- Begin deprecating old analysis paths

### Phase 3: Integration
- Wire unified engine into main analysis service
- Update calibration to use new pipeline
- Remove legacy fork logic

### Phase 4: Optimization
- Performance optimization for large corpora
- Advanced pattern matching features
- Enhanced calibration methods

## Quality Assurance

### Testing Strategy
1. **Unit Tests**: Each component tested in isolation
2. **Integration Tests**: End-to-end analysis flow
3. **Property Tests**: Transposition invariance, monotonicity
4. **Golden Tests**: Known progressions with expected outputs
5. **Calibration Tests**: Quality gate validation

### Performance Considerations
- Pattern enumeration cost scales with pattern count
- Conflict resolution algorithms (O(n²) for soft-NMS)
- Calibration overhead negligible with precomputed mappings
- Caching opportunities for repeated pattern matching

### Error Handling
- Schema validation with helpful error messages
- Graceful degradation when patterns fail to match
- Identity fallback when calibration gates fail
- Comprehensive logging for debugging

## Development Workflow

### Adding Patterns
1. Design pattern logic and constraints
2. Add to patterns JSON file
3. Write test cases for pattern
4. Validate against schema
5. Test integration with engine

### Debugging Analysis
1. Check evidence traces in AnalysisEnvelope
2. Review aggregator debug breakdown
3. Validate pattern matches expected progressions
4. Verify calibration mapping applied correctly

### Performance Profiling
1. Measure pattern matching time
2. Profile aggregation algorithms
3. Monitor calibration overhead
4. Optimize critical path components

## API Integration

The unified engine integrates with the existing library through the DTO contracts:

```python
# Engine produces standard DTOs
envelope = engine.analyze(context)
assert isinstance(envelope, AnalysisEnvelope)
assert isinstance(envelope.primary, AnalysisSummary)

# Evidence traces available for debugging
for evidence in envelope.evidence:
    print(f"Pattern: {evidence.reason}")
    print(f"Details: {evidence.details}")
```

This architecture provides a solid foundation for continued development while maintaining compatibility with existing code that depends on the DTO interfaces.