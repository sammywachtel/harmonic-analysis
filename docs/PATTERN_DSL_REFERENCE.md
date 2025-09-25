# Pattern DSL Reference

This document provides a complete reference for the Unified Pattern Engine's Domain-Specific Language (DSL) used to define musical patterns declaratively.

## Overview

The Pattern DSL allows you to define musical patterns in JSON format that can detect harmonic progressions, cadences, modal characteristics, and chromatic elements. Patterns are **config-first** and **testable**, enabling rapid development and validation.

## File Structure

```json
{
  "version": 1,
  "metadata": {
    "description": "Pattern collection description",
    "author": "Author name",
    "created": "2024-01-01"
  },
  "patterns": [
    {
      "id": "pattern.identifier",
      "name": "Human Readable Name",
      "scope": ["harmonic"],
      "track": ["functional"],
      "matchers": { /* matching criteria */ },
      "evidence": { /* scoring configuration */ },
      "metadata": { /* pattern metadata */ }
    }
  ]
}
```

## Field Reference

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | integer | ✅ | Schema version (currently 1) |
| `metadata` | object | ❌ | File metadata (description, author, dates) |
| `patterns` | array | ✅ | Array of pattern definitions |

### Pattern Definition Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Unique pattern identifier (e.g., "cadence.authentic.perfect") |
| `name` | string | ✅ | Human-readable pattern name |
| `scope` | array | ✅ | Analysis scopes: `["harmonic", "melodic", "scale"]` |
| `track` | array | ✅ | Analysis tracks: `["functional", "modal"]` |
| `matchers` | object | ✅ | Pattern matching criteria |
| `evidence` | object | ✅ | Evidence configuration and scoring |
| `metadata` | object | ❌ | Pattern metadata (tags, priority, examples) |

### Matcher Configuration

The `matchers` object defines what musical content triggers this pattern:

#### Sequence Matchers

| Matcher | Type | Description | Example |
|---------|------|-------------|---------|
| `roman_seq` | array | Roman numeral sequence | `["V", "I"]` |
| `chord_seq` | array | Chord symbol sequence | `["G", "C"]` |
| `interval_seq` | array | Melodic interval sequence | `[2, -5]` |
| `scale_degrees` | array | Scale degree sequence | `[5, 1]` |

#### Context Matchers

| Matcher | Type | Description | Values |
|---------|------|-------------|--------|
| `mode` | string | Required mode context | `"major"`, `"minor"`, `"dorian"`, `"phrygian"`, `"lydian"`, `"mixolydian"`, `"aeolian"`, `"locrian"` |
| `transposition_invariant` | boolean | Apply to all keys | `true` (default), `false` |

#### Constraint System

The `constraints` object provides additional matching criteria:

| Constraint | Type | Description | Values |
|------------|------|-------------|--------|
| `soprano_degree` | array | Required soprano scale degrees | `[1, 3, 5]` |
| `bass_motion` | string | Bass line movement | `"ascending"`, `"descending"`, `"leap"`, `"step"` |
| `key_context` | string | Harmonic context | `"diatonic"`, `"chromatic"`, `"mixed"` |
| `position` | string | Position in progression | `"start"`, `"middle"`, `"end"`, `"any"` |

#### Window Configuration

The `window` object controls match timing and overlaps:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `len` | integer | pattern length | Window length in chords |
| `overlap_ok` | boolean | `true` | Allow overlapping matches |
| `min_gap` | integer | `0` | Minimum gap between matches |

### Evidence Configuration

The `evidence` object configures pattern scoring and features:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `weight` | number | ✅ | Base evidence weight (0.0-1.0) |
| `features` | array | ❌ | Features to extract |
| `confidence_fn` | string | ❌ | Confidence function name (default: "identity") |
| `uncertainty` | number | ❌ | Uncertainty measure (0.0-1.0) |

#### Supported Features

| Feature | Description |
|---------|-------------|
| `outside_key_ratio` | Proportion of notes outside diatonic scale |
| `has_auth_cadence` | Authentic cadence presence |
| `modal_char_score` | Modal vs functional characteristics |
| `chromatic_density` | Amount of chromatic alteration |
| `voice_leading_smoothness` | Quality of melodic motion |
| `harmonic_rhythm` | Rate of chord change |
| `tonal_clarity` | Strength of functional progression |

#### Confidence Functions

| Function | Description | Use Case |
|----------|-------------|----------|
| `identity` | Returns raw score unchanged | Simple patterns |
| `logistic_default` | Standard logistic scaling | General patterns |
| `logistic_dorian` | Dorian-optimized scaling | Modal patterns |

### Pattern Metadata

The `metadata` object provides documentation and prioritization:

| Field | Type | Description |
|-------|------|-------------|
| `tags` | array | Classification tags |
| `priority` | integer | Evaluation priority (0-100, default 50) |
| `description` | string | Detailed pattern description |
| `examples` | array | Example progressions |
| `false_positives` | array | Known false positive cases |
| `references` | array | Academic/theoretical references |

## Pattern Examples

### Basic Authentic Cadence

```json
{
  "id": "cadence.authentic.perfect",
  "name": "Perfect Authentic Cadence",
  "scope": ["harmonic"],
  "track": ["functional"],
  "matchers": {
    "roman_seq": ["V", "I"],
    "constraints": {
      "soprano_degree": [1],
      "key_context": "diatonic"
    },
    "window": {
      "len": 2,
      "overlap_ok": false
    }
  },
  "evidence": {
    "weight": 0.95,
    "features": ["has_auth_cadence", "tonal_clarity"],
    "confidence_fn": "logistic_default"
  },
  "metadata": {
    "tags": ["cadence", "functional", "closure"],
    "priority": 90,
    "description": "V-I with soprano on tonic, strongest functional cadence"
  }
}
```

### Modal Pattern with Mode Context

```json
{
  "id": "modal.dorian.i_bVII",
  "name": "Dorian i-♭VII",
  "scope": ["harmonic"],
  "track": ["modal"],
  "matchers": {
    "roman_seq": ["i", "♭VII"],
    "mode": "dorian",
    "transposition_invariant": true,
    "window": {
      "len": 2
    }
  },
  "evidence": {
    "weight": 0.80,
    "features": ["modal_char_score"],
    "confidence_fn": "logistic_dorian"
  },
  "metadata": {
    "tags": ["modal", "dorian", "characteristic"],
    "priority": 75,
    "description": "Characteristic Dorian progression using ♭VII"
  }
}
```

### Complex Multi-Track Pattern

```json
{
  "id": "cadence.plagal",
  "name": "Plagal Cadence",
  "scope": ["harmonic"],
  "track": ["functional", "modal"],
  "matchers": {
    "roman_seq": ["IV", "I"],
    "window": {
      "len": 2,
      "overlap_ok": false
    }
  },
  "evidence": {
    "weight": 0.75,
    "features": ["modal_char_score"],
    "confidence_fn": "logistic_default"
  },
  "metadata": {
    "tags": ["cadence", "plagal", "modal"],
    "priority": 70,
    "description": "IV-I 'Amen' cadence, weaker functional closure"
  }
}
```

### Chromatic Pattern with Regex

```json
{
  "id": "chromatic.secondary_dominant",
  "name": "Secondary Dominant",
  "scope": ["harmonic"],
  "track": ["functional"],
  "matchers": {
    "roman_seq": ["V/.*", ".*"],
    "constraints": {
      "key_context": "chromatic"
    },
    "window": {
      "len": 2
    }
  },
  "evidence": {
    "weight": 0.70,
    "features": ["chromatic_density", "outside_key_ratio"],
    "confidence_fn": "logistic_default"
  },
  "metadata": {
    "tags": ["chromatic", "secondary_dominant", "tonicization"],
    "priority": 65,
    "description": "Secondary dominant resolution"
  }
}
```

## Plugin Integration

For patterns that cannot be expressed declaratively, you can reference plugin evaluators:

### Plugin Function Signature

```python
def custom_evaluator(pattern: Dict[str, Any], context: Dict[str, Any]) -> Evidence:
    """
    Custom pattern evaluator plugin.

    Args:
        pattern: Pattern definition from JSON
        context: Analysis context with span, key, chords, metadata

    Returns:
        Evidence object with pattern_id, track_weights, features, raw_score, etc.
    """
    # Custom evaluation logic here
    return Evidence(
        pattern_id=pattern["id"],
        track_weights={"functional": 0.8},
        features={"custom_feature": 0.9},
        raw_score=0.85,
        uncertainty=None,
        span=context["span"]
    )
```

### Plugin Registration

```python
from harmonic_analysis.core.pattern_engine import PatternEngine

engine = PatternEngine()
engine.plugins.register("custom_evaluator", custom_evaluator)
```

### Plugin Reference in JSON

```json
{
  "id": "custom.pattern",
  "name": "Custom Pattern",
  "scope": ["harmonic"],
  "track": ["functional"],
  "matchers": {
    "roman_seq": ["I", "V"]
  },
  "evidence": {
    "weight": 0.8,
    "confidence_fn": "custom_evaluator"
  }
}
```

## Validation and Schema

All pattern files are validated against a comprehensive JSON schema. Common validation errors:

### Pattern ID Format
- **Valid**: `"cadence.authentic.perfect"`
- **Invalid**: `"cadence with spaces"` (no spaces allowed)

### Weight Range
- **Valid**: `0.0` to `1.0`
- **Invalid**: `1.5` (exceeds maximum)

### Scope Values
- **Valid**: `["harmonic", "melodic", "scale"]`
- **Invalid**: `["invalid_scope"]` (not in enum)

### Track Values
- **Valid**: `["functional", "modal"]`
- **Invalid**: `["invalid_track"]` (not in enum)

## Best Practices

### Pattern Design

1. **Use descriptive IDs**: Follow the pattern `category.type.specifics`
2. **Set appropriate priorities**: Higher values for more specific/important patterns
3. **Include metadata**: Tags, descriptions, and examples aid debugging
4. **Test thoroughly**: Use golden tests for all patterns

### Performance Optimization

1. **Order by priority**: Higher priority patterns evaluated first
2. **Minimize window overlap**: Use `overlap_ok: false` when appropriate
3. **Constrain appropriately**: Add constraints to reduce false positives
4. **Use specific matchers**: Prefer roman_seq over regex when possible

### Debugging Patterns

1. **Check golden tests**: Ensure expected matches are found
2. **Review priorities**: Conflicts may be due to priority ordering
3. **Validate features**: Ensure referenced features exist
4. **Test transpositions**: Verify transposition_invariant behavior

## File Organization

### Recommended Structure

```
patterns/
├── cadences.json           # Cadential patterns
├── modal.json             # Modal characteristic patterns
├── functional.json        # Functional harmony patterns
├── chromatic.json         # Chromatic and jazz patterns
└── experimental.json      # Development patterns
```

### Pattern Naming Conventions

- **Cadences**: `cadence.{type}.{specifics}`
- **Modal**: `modal.{mode}.{progression}`
- **Functional**: `functional.{function}.{specifics}`
- **Chromatic**: `chromatic.{type}.{specifics}`

### Version Management

- Increment `version` for breaking schema changes
- Use semantic versioning for pattern collections
- Document changes in pattern metadata

## Migration from Legacy Analyzers

When migrating from imperative analyzers:

1. **Identify core patterns**: Extract the most important rules first
2. **Create golden tests**: Establish expected behavior before migration
3. **Port declaratively**: Use JSON for 80%+ of patterns
4. **Plugin for complex rules**: Use plugins only when JSON is insufficient
5. **Validate parity**: Ensure migrated patterns match legacy behavior
6. **Remove legacy code**: Delete old analyzers after successful migration

## Troubleshooting

### Common Issues

| Issue | Symptoms | Solution |
|-------|----------|----------|
| Pattern not matching | Expected progression doesn't trigger | Check roman_seq case sensitivity |
| False positives | Pattern triggers incorrectly | Add constraints or increase specificity |
| Low confidence | Pattern matches but weak score | Adjust weight or confidence_fn |
| Schema validation | JSON loading fails | Check required fields and enum values |
| Performance issues | Slow pattern evaluation | Review priority ordering and constraints |

### Debugging Tools

```python
# Load and validate patterns
from harmonic_analysis.core.pattern_engine import PatternLoader
loader = PatternLoader()
patterns = loader.load(Path("patterns.json"))

# Test individual pattern
from harmonic_analysis.core.pattern_engine import PatternEngine
engine = PatternEngine()
engine.load_patterns(Path("patterns.json"))
context = AnalysisContext(key="C major", chords=["G", "C"], ...)
matches = engine._find_pattern_matches(pattern, context)
```

This DSL provides a powerful, flexible foundation for musical pattern recognition while maintaining clarity and testability.