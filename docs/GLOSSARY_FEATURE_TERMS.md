# Glossary & Feature Terms

## Overview

The Pattern Engine integrates with the existing glossary system to provide human-readable labels, tooltips, and definitions for backend feature names. This enables UIs to display clear explanations of technical terms without requiring music theory expertise from end users.

## Architecture

### Components

1. **`glossary.json`** - Contains structured music theory definitions and explanations
2. **`GlossaryService`** - Existing service for educational context and pattern explanations
3. **`glossary.py`** - New helper functions for feature enrichment
4. **Pattern Engine Integration** - Automatic enrichment of evidence and analysis results

### Data Flow

```
Backend Feature → Glossary Lookup → UI Label + Tooltip → User Interface
     ↓                    ↓                  ↓                ↓
"modal_char_score"  →  "Modal Character"  →  "Strength of modal vs functional characteristics"
```

## Using the Glossary System

### Automatic Enrichment

The pattern engine automatically enriches evidence and analysis results:

```python
from harmonic_analysis.core.pattern_engine import PatternEngine

engine = PatternEngine()  # Automatically loads glossary
envelope = engine.analyze(context)

# Evidence contains enriched features
for evidence in envelope.evidence:
    features = evidence.details["features"]
    if "features_ui" in features:
        ui_features = features["features_ui"]
        for key, ui_info in ui_features.items():
            print(f"{key}: {ui_info['label']} - {ui_info['tooltip']}")
```

### Manual Feature Explanation

```python
from harmonic_analysis.core.pattern_engine.glossary import explain_feature, load_default_glossary

glossary = load_default_glossary()
label, tooltip = explain_feature(glossary, "modal_char_score")
print(f"Label: {label}")        # "Modal Character"
print(f"Tooltip: {tooltip}")    # "Strength of modal vs functional characteristics"
```

### Feature Enrichment

```python
from harmonic_analysis.core.pattern_engine.glossary import enrich_features

features = {
    "tonal_clarity": 0.85,
    "modal_char_score": 0.72,
    "unknown_feature": 0.5
}

enriched = enrich_features(glossary, features)
# Original features preserved + features_ui added with labels/tooltips
```

## Feature Mappings

### Supported Feature Categories

#### Cadence Features
- `has_auth_cadence` → "Authentic Cadence" + definition
- `has_plagal_cadence` → "Plagal Cadence" + IV-I explanation
- `has_half_cadence` → "Half Cadence" + expectation description
- `has_deceptive_cadence` → "Deceptive Cadence" + V-vi explanation

#### Modal Features
- `modal_char_score` → "Modal Character" + strength description
- `dorian_character` → "Dorian Character" + raised 6th explanation
- `phrygian_character` → "Phrygian Character" + lowered 2nd explanation
- `mixolydian_character` → "Mixolydian Character" + lowered 7th explanation

#### Functional Features
- `tonal_clarity` → "Tonal Clarity" + functional harmony explanation
- `predominant_function` → "Predominant Function" + pre-dominant area description
- `dominant_function` → "Dominant Function" + tension creation explanation

#### Chromatic Features
- `outside_key_ratio` → "Chromatic Content" + diatonic proportion explanation
- `chromatic_density` → "Chromatic Density" + alteration amount description
- `secondary_dominants` → "Secondary Dominants" + V/x explanation

#### Voice Leading Features
- `voice_leading_smoothness` → "Voice Leading" + melodic motion description
- `soprano_degree` → "Soprano Degree" + scale degree explanation

#### Pattern Features
- `pattern_weight` → "Pattern Weight" + base confidence explanation
- `harmonic_rhythm` → "Harmonic Rhythm" + chord change rate explanation

### Legacy Feature Support

The system maintains compatibility with legacy feature names:

- `lt_suppression` → "Leading Tone Suppression"
- `raised6_ratio` → "Raised Sixth"
- `flat7_ratio` → "Lowered Seventh"

## Integration Points

### AnalysisSummary.terms

Analysis results automatically include a `terms` field with feature explanations:

```python
envelope = engine.analyze(context)
terms = envelope.primary.terms

# Standard fields
assert "analysis_method" in terms

# Feature-specific terms (populated automatically)
if "modal_char_score" in detected_features:
    assert "modal_char_score" in terms
    assert terms["modal_char_score"]["label"] == "Modal Character"
    assert "modal" in terms["modal_char_score"]["tooltip"].lower()
```

### EvidenceDTO.details.features_ui

Evidence details include UI-friendly feature information:

```json
{
  "reason": "modal.dorian.i_bVII",
  "details": {
    "features": {
      "modal_char_score": 0.8,
      "pattern_weight": 0.7,
      "features_ui": {
        "modal_char_score": {
          "label": "Modal Character",
          "tooltip": "Strength of modal vs functional characteristics",
          "value": 0.8
        },
        "pattern_weight": {
          "label": "Pattern Weight",
          "tooltip": "Base confidence weight for this pattern",
          "value": 0.7
        }
      }
    }
  }
}
```

## Extending the System

### Adding New Feature Mappings

Update the `feature_mappings` dictionary in `glossary.py`:

```python
feature_mappings = {
    # Existing mappings...
    "new_feature_key": ("Human Label", "Detailed explanation for users"),
}
```

### Adding New Glossary Entries

Update `glossary.json` with new categories or terms:

```json
{
  "analysis_terms": {
    "new_term": "Definition and explanation of the new term"
  },
  "new_category": {
    "term1": "Definition 1",
    "term2": {
      "definition": "More complex definition",
      "example": "Usage example"
    }
  }
}
```

### Custom Feature Explanations

For complex features requiring custom logic:

```python
def explain_custom_feature(glossary, key):
    if key == "complex_feature":
        # Custom logic for explanation
        return "Custom Label", "Custom detailed explanation"
    return explain_feature(glossary, key)  # Fallback
```

## UI Integration Guidelines

### Displaying Feature Information

```typescript
// TypeScript example for UI integration
interface FeatureUI {
  label: string;
  tooltip: string;
  value: number;
}

interface AnalysisEvidence {
  reason: string;
  details: {
    features: Record<string, any>;
    features_ui?: Record<string, FeatureUI>;
  };
}

// Display features with enriched UI info
function displayFeatures(evidence: AnalysisEvidence) {
  const features = evidence.details.features;
  const featuresUI = evidence.details.features_ui || {};

  Object.entries(features).forEach(([key, value]) => {
    if (key !== 'features_ui' && featuresUI[key]) {
      const ui = featuresUI[key];
      displayFeature(ui.label, ui.tooltip, ui.value);
    } else {
      displayFeature(key, key, value); // Fallback
    }
  });
}
```

### Tooltip Implementation

```javascript
// Example tooltip implementation
function createTooltip(label, tooltip) {
  return `
    <span class="feature-label" title="${tooltip}">
      ${label}
      <i class="info-icon">ℹ️</i>
    </span>
  `;
}
```

## Quality Assurance

### Validation Requirements

1. **All pattern features should have mappings** - Unknown features fall back gracefully
2. **Tooltips should be educational** - Provide value to users learning music theory
3. **Labels should be concise** - 1-3 words maximum for UI space
4. **Backwards compatibility** - Legacy feature names continue to work

### Testing Strategy

```python
def test_feature_coverage():
    """Ensure all commonly used features have explanations."""
    common_features = ["modal_char_score", "tonal_clarity", "has_auth_cadence"]

    for feature in common_features:
        label, tooltip = explain_feature(glossary, feature)
        assert label != feature, f"No mapping for {feature}"
        assert tooltip != feature, f"No explanation for {feature}"
```

### Performance Considerations

- Glossary loaded once at engine initialization
- Feature lookups are O(1) dictionary operations
- UI enrichment only added when beneficial (not for unknown features)
- Memory footprint minimal (~10KB for glossary data)

## Migration from Legacy Systems

### Compatibility Layer

The new system maintains full compatibility with existing `GlossaryService`:

```python
# Old approach still works
service = GlossaryService()
definition = service.get_term_definition("functional_harmony")

# New approach provides additional UI benefits
label, tooltip = explain_feature(service.glossary, "functional_harmony")
enriched = enrich_features(service.glossary, features)
```

### Gradual Adoption

UIs can adopt the new enriched features incrementally:

1. **Phase 1**: Use existing features without enrichment
2. **Phase 2**: Display `features_ui` when available, fallback to raw keys
3. **Phase 3**: Full integration with tooltips and educational context

## Future Enhancements

### Planned Improvements

1. **Multi-language Support** - Glossary entries in multiple languages
2. **Dynamic Loading** - Hot-reload glossary without restarting
3. **User Customization** - Allow users to add/modify explanations
4. **Rich Tooltips** - Support for examples, audio clips, notation
5. **Contextual Help** - Link to detailed music theory documentation

### Extension Points

The system is designed for easy extension:

- Plugin-based feature explanation functions
- Custom glossary sources (database, external APIs)
- Template-based tooltip generation
- Integration with music education platforms

---

This glossary system bridges the gap between technical analysis features and user-friendly explanations, making harmonic analysis results accessible to musicians at all theory levels.