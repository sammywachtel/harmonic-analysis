# Corpus Mining and Unified Target Construction Guide

This guide covers the Iteration 3 corpus mining pipeline and unified target construction system that replaces split functional/modal target builders with single reliability targets `p(correct | evidence)`.

## Overview

The corpus mining system implements Section 5 of the engine redesign plan, providing:

1. **Music21-based corpus extraction** from multiple sources
2. **Pattern-based labeling** with adjudication heuristics
3. **Unified target construction** replacing per-track builders
4. **Stratified calibration buckets** for difficulty-aware calibration
5. **Integration pipeline** for seamless deployment

## Architecture

```
Corpus Mining Pipeline:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Corpus          │───▶│ Pattern         │───▶│ Unified Target  │
│ Extractor       │    │ Labeler         │    │ Builder         │
│                 │    │                 │    │                 │
│ - music21 data  │    │ - adjudication  │    │ - p(correct|e)  │
│ - transposition │    │ - heuristics    │    │ - stratification│
│ - normalization │    │ - soft labels   │    │ - calibration   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
corpus_samples_raw.json  labeled_samples.jsonl  corpus_samples.jsonl
```

## Quick Start

### 1. Run Complete Pipeline

```bash
cd .local_docs/music/alg/corpus_miner
python pipeline.py --output-dir ./output
```

### 2. Use in Main System

```python
from harmonic_analysis.core.pattern_engine import TargetBuilder

# The unified target builder automatically replaces legacy per-track builders
builder = TargetBuilder()
targets = builder.build_targets(evidences)
```

### 3. Check Outputs

- `corpus_samples.jsonl` - Final labeled training data
- `unified_targets/` - Calibration-ready targets and buckets
- `target_construction_report.md` - Quality assessment report

## Components

### Corpus Extractor

**Purpose**: Extract musical data from corpus sources and normalize for analysis.

**Key Features**:
- **Music21 integration**: Bach chorales, jazz standards, classical works
- **Transposition generation**: All major/minor keys for invariance
- **Quality filtering**: Minimum chord counts, key signature requirements
- **Normalized output**: Consistent chord symbols, roman numerals, melody

**Configuration**: `.local_docs/music/alg/corpus_miner/config/extraction_config.json`

```json
{
  \"corpus_sources\": [\"bach/chorales\", \"jazz/standards\"],
  \"max_samples_per_source\": 50,
  \"transposition_keys\": [\"C\", \"D\", \"E♭\", \"F\", \"G\", \"A\", \"B♭\"],
  \"min_chord_count\": 4,
  \"max_chord_count\": 16
}
```

### Pattern Labeler

**Purpose**: Generate reliability labels using pattern analysis and adjudication heuristics.

**Adjudication Rules**:

1. **Strong Evidence** (reliability ≥ 0.9): Consensus patterns with high confidence
2. **Pattern Consensus** (reliability ≥ 0.8): Multiple patterns agreeing
3. **Contradictory Evidence** (reliability ≤ 0.3): Conflicting pattern signals
4. **Weak Evidence** (0.3-0.7): Soft labels for ambiguous cases
5. **Default Confidence**: Adjusted primary confidence with safeguards

**Example**:
```python
# Perfect authentic cadence with soprano on tonic
pattern_match = PatternMatch(
    pattern_id=\"cadence.authentic.perfect\",
    span=(2, 4),
    raw_score=0.92,
    evidence_features={\"soprano_degree\": 1}
)
# → reliability = 0.88 (strong evidence heuristic)
```

### Unified Target Builder

**Purpose**: Replace split functional/modal targets with single `p(correct | evidence)` targets.

**Key Changes from Legacy**:

| Legacy Approach | Unified Approach |
|----------------|------------------|
| Separate functional/modal targets | Single reliability target |
| Per-track weight splitting | Evidence-based adjudication |
| Manual threshold tuning | Corpus-driven calibration |
| Limited stratification | Difficulty-aware buckets |

**Stratification**:
- **Diatonic Simple**: Basic progressions, common cadences
- **Chromatic Moderate**: Secondary dominants, jazz harmony
- **Modal Complex**: Dorian/Phrygian characteristics
- **Atonal Difficult**: Extreme dissonance, twelve-tone elements

## Integration with Main System

### Automatic Migration

The unified target builder provides a drop-in replacement for legacy `TargetBuilder`:

```python
# Legacy code continues to work unchanged
from harmonic_analysis.core.pattern_engine import TargetBuilder

builder = TargetBuilder()
targets = builder.build_targets(evidences, annotations)
```

### Enhanced Capabilities

```python
# Access corpus mining features when available
builder = TargetBuilder(use_corpus_pipeline=True)

# Unified targets with stratification
raw_scores, reliability_targets, stats = builder.corpus_builder.build_unified_targets(labeled_samples)

# Calibration buckets for difficulty-aware modeling
buckets = builder.corpus_builder.build_stratified_targets(labeled_samples)
```

## Quality Assessment

### Target Statistics

The system generates comprehensive quality metrics:

```python
stats = TargetStatistics(
    total_samples=500,
    label_distribution={
        \"adjudication_heuristic\": 300,
        \"weak_supervision\": 150,
        \"trusted_annotation\": 50
    },
    difficulty_distribution={
        \"diatonic_simple\": 200,
        \"chromatic_moderate\": 150,
        \"modal_complex\": 100,
        \"atonal_difficult\": 50
    },
    reliability_range=(0.2, 0.95),
    correlation_stats={
        \"raw_reliability_corr\": 0.73,
        \"reliability_variance\": 0.18
    }
)
```

### Validation Gates

The system includes quality gates as specified in Section 5.3:

- **Minimum correlation**: `|corr| >= 0.1` (targets must be learnable)
- **Minimum variance**: `var(y) > 0.01` (sufficient label diversity)
- **Sample size**: `n >= 10` per calibration bucket
- **Target range**: `[0.0, 1.0]` (valid probability values)

### Calibration Integration

Targets are exported in format ready for calibration system:

```
unified_targets/
├── raw_scores.npy              # Pattern confidence scores
├── reliability_targets.npy     # Unified reliability labels
├── calibration_buckets.json    # Stratification metadata
└── target_construction_report.md
```

## Best Practices

### Corpus Quality

1. **Diverse Sources**: Include classical, jazz, folk, and contemporary works
2. **Transposition Coverage**: Test pattern invariance across keys
3. **Difficulty Balance**: Ensure representation across all strata
4. **Quality Filtering**: Remove incomplete or corrupted samples

### Labeling Strategy

1. **Conservative Heuristics**: Prefer false negatives over false positives
2. **Soft Labels**: Use range [0.3, 0.7] for genuinely ambiguous cases
3. **Pattern Consensus**: Trust when multiple patterns agree
4. **Expert Validation**: Spot-check high-impact samples

### Integration Testing

1. **Backward Compatibility**: Ensure legacy code continues working
2. **Performance Testing**: Compare target quality vs. legacy approach
3. **Calibration Validation**: Test with actual calibration pipeline
4. **Edge Case Handling**: Verify graceful degradation

## Troubleshooting

### Common Issues

**Low Correlation (`< 0.1`)**:
- Check pattern definitions for musical accuracy
- Verify evidence features align with labels
- Increase sample diversity across difficulty strata

**Insufficient Variance (`< 0.01`)**:
- Add more diverse corpus sources
- Review adjudication rules for over-conservative labeling
- Include more ambiguous cases with soft labels

**Empty Calibration Buckets**:
- Reduce minimum bucket size requirement
- Merge similar difficulty strata
- Increase total corpus sample count

**Music21 Import Errors**:
- Install music21: `pip install music21`
- Configure corpus access: `python -m music21.configure`
- Use mock samples if music21 unavailable

### Performance Optimization

1. **Caching**: Enable pipeline caching for development
2. **Parallel Processing**: Use async corpus extraction
3. **Incremental Updates**: Only regenerate when patterns change
4. **Batch Processing**: Process samples in configurable batch sizes

## Migration Checklist

- [ ] Install music21 and configure corpus access
- [ ] Run pipeline to generate `corpus_samples.jsonl`
- [ ] Verify unified target builder imports correctly
- [ ] Test backward compatibility with existing code
- [ ] Run calibration system with unified targets
- [ ] Update documentation and training materials
- [ ] Archive legacy target builder code

## Advanced Usage

### Custom Adjudication Rules

```python
from pattern_labeler import PatternLabeler, AdjudicationRules

custom_rules = AdjudicationRules(
    strong_evidence_threshold=0.95,
    consensus_patterns=[\"custom.pattern.type\"],
    contradiction_patterns=[\"problematic.pattern\"]
)

labeler = PatternLabeler(custom_rules)
```

### Corpus Source Extension

```python
from corpus_extractor import CorpusExtractor, ExtractionConfig

config = ExtractionConfig(
    corpus_sources=[\"custom/corpus\", \"proprietary/dataset\"],
    max_samples_per_source=100
)

extractor = CorpusExtractor(config)
```

### Export Format Customization

```python
builder.export_targets_for_calibration(
    raw_scores, targets, buckets,
    output_dir=Path(\"custom/output\"),
    include_debug_info=True
)
```

This unified approach provides a robust foundation for pattern-based harmonic analysis with corpus-driven calibration and quality gates.