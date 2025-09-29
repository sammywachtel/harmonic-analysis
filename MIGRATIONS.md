# Migration Guide - Harmonic Analysis Engine Redesign

This document captures the migration story from the legacy pattern analysis system to the new unified pattern engine architecture, implemented across Iterations 1-5 of the engine redesign.

## Overview

The harmonic analysis library underwent a complete architectural transformation to address scalability, maintainability, and accuracy issues in the legacy system. This migration provides:

- **Unified Analysis**: Single pattern engine for functional, modal, and chromatic analysis
- **Quality-Gated Calibration**: Advanced confidence calibration with strict validation
- **Config-First Patterns**: Declarative pattern definitions in JSON
- **Evidence-Based Architecture**: Transparent analysis reasoning
- **Production-Ready Performance**: Optimized pipeline with comprehensive testing

## What Was Removed

### Legacy Services and Analyzers (Iteration 5)

#### ❌ Deleted Components
- `enhanced_modal_analyzer.py` - Legacy modal analysis engine
- `modal_analysis_service.py` - Standalone modal analysis service
- `target_builder_legacy.py` - Legacy target construction system
- `test_unified_vs_legacy_parity.py` - Legacy comparison tests

#### ❌ Archived Documentation
- All `music-alg-*` iteration documents moved to `.local_docs/archive/`
- Legacy calibration pipeline documentation (JSON-based system)
- Iteration adjustment documents (`iteration*-adj.md`)

### Legacy Calibration System (Iteration 4)
- `CalibrationService` class and JSON-based calibration files
- `confidence_baseline.json` and associated calibration assets
- Notebook-driven calibration deployment pipeline

### Legacy Pattern Matching (Iterations 1-3)
- Split functional/modal/chromatic analysis pipelines
- Per-track target builders with separate confidence calculations
- Hardcoded pattern definitions scattered across multiple files

## Migration Path

### For End Users

#### ✅ Before (Legacy API)
```python
# Old: Complex initialization with multiple services
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService
from harmonic_analysis.services.modal_analysis_service import ModalAnalysisService
from harmonic_analysis.services.calibration_service import CalibrationService

# Multiple service setup
pattern_service = PatternAnalysisService(
    functional_analyzer=...,
    modal_analyzer=...,
    chromatic_analyzer=...,
    calibration_service=CalibrationService()
)

modal_service = ModalAnalysisService()
```

#### ✅ After (Unified API)
```python
# New: Simple initialization - everything unified
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

# Single service handles everything
service = PatternAnalysisService()  # Auto-calibration enabled by default
result = await service.analyze_with_patterns_async(['C', 'F', 'G', 'C'])
```

### For Library Developers

#### Analysis Architecture
```python
# Before: Manual analyzer coordination
functional_result = functional_analyzer.analyze(...)
modal_result = modal_analyzer.analyze(...)
chromatic_result = chromatic_analyzer.analyze(...)
# Complex arbitration logic...

# After: Unified pattern engine
from harmonic_analysis.core.pattern_engine import PatternEngine

engine = PatternEngine()
result = engine.analyze(chords, profile="classical")
# Automatic evidence aggregation and arbitration
```

#### Calibration System
```python
# Before: JSON-based calibration deployment
with open('calibration_mapping.json') as f:
    calibration_data = json.load(f)

# After: Quality-gated in-memory calibration
from harmonic_analysis.core.pattern_engine.calibration import Calibrator

calibrator = Calibrator()
mapping = calibrator.fit(raw_scores, targets)
if mapping.passed_gates:
    calibrated_score = mapping.apply(raw_score)
```

#### Pattern Definition
```python
# Before: Hardcoded patterns in Python
class LegacyPatterns:
    PAC = FunctionalPattern(
        degrees=[5, 1],
        labels=["V", "I"],
        confidence=0.9
    )

# After: Declarative JSON patterns
{
  "patterns": [{
    "id": "perfect_authentic_cadence",
    "sequence": ["V", "I"],
    "context_constraints": {
      "key_stability": {"min": 0.7},
      "voice_leading": {"type": "smooth"}
    },
    "evidence": {
      "cadential_strength": 0.9,
      "resolution_quality": 0.8
    }
  }]
}
```

## New Features Available

### Quality-Gated Calibration
```python
# Automatic quality validation prevents degradation
service = PatternAnalysisService()  # Auto-calibrate=True
# System automatically:
# 1. Collects training data
# 2. Applies quality gates (correlation, sample count, variance, ECE)
# 3. Selects best method (Platt/Isotonic/Identity)
# 4. Validates improvement before deployment
```

### Evidence-Based Analysis
```python
result = await service.analyze_with_patterns_async(['C', 'F', 'G', 'C'])
print(f"Confidence: {result.primary.confidence}")

# Inspect evidence that led to the analysis
for evidence in result.primary.evidence:
    print(f"- {evidence.pattern_id}: {evidence.strength}")
```

### Corpus Mining Integration
```python
from harmonic_analysis.corpus_miner import UnifiedTargetBuilder

# Mine corpus for training data
builder = UnifiedTargetBuilder()
samples = builder.mine_corpus(["bach_chorales", "jazz_standards"])
targets = builder.build_targets(samples)
```

## Backward Compatibility

### ✅ Maintained APIs
- `PatternAnalysisService.analyze_with_patterns_async()` - Core analysis method
- `AnalysisEnvelope` and `AnalysisSummary` DTOs - Result format unchanged
- `analyze_chord_progression()` - Top-level convenience function
- All main library exports continue to work

### ✅ Facade Pattern
The legacy `PatternAnalysisService` is now a thin facade over `UnifiedPatternService`:

```python
# This still works but now delegates to unified engine
service = PatternAnalysisService(
    functional_analyzer=old_analyzer,  # Ignored - compatibility only
    modal_analyzer=old_modal,          # Ignored - compatibility only
    chromatic_analyzer=old_chromatic   # Ignored - compatibility only
)
```

## Testing Migration

### Legacy Test Cleanup
- Removed tests specific to deleted components (`enhanced_modal_analyzer`, `modal_analysis_service`)
- Archived parity tests that compared legacy vs unified systems
- Maintained all behavior and integration tests

### New Test Coverage
- Quality-gated calibration regression tests (18 test cases)
- Unified pattern engine validation (400+ test cases)
- Evidence aggregation and scoring tests
- Corpus mining pipeline tests

## Performance Improvements

### Before (Legacy System)
- Multiple analyzer initialization overhead
- Redundant pattern matching across analyzers
- Manual arbitration between analysis types
- JSON-based calibration file I/O

### After (Unified System)
- Single pattern engine initialization
- Shared pattern definitions across analysis types
- Automatic evidence-based arbitration
- In-memory calibration with quality gates

## Documentation Updates

### New Documentation
- [`docs/PATTERN_ENGINE_ARCHITECTURE.md`](docs/PATTERN_ENGINE_ARCHITECTURE.md) - Complete architectural overview
- [`docs/PATTERN_DSL_REFERENCE.md`](docs/PATTERN_DSL_REFERENCE.md) - Pattern definition language
- [`docs/CALIBRATION_GUIDE.md`](docs/CALIBRATION_GUIDE.md) - Quality-gated calibration system
- [`docs/CORPUS_MINING_GUIDE.md`](docs/CORPUS_MINING_GUIDE.md) - Corpus mining and target construction

### Updated Documentation
- [`docs/API_GUIDE.md`](docs/API_GUIDE.md) - Reflects unified API patterns
- [`src/harmonic_analysis/assets/README.md`](src/harmonic_analysis/assets/README.md) - New calibration workflow
- [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) - Unified engine debugging

## Migration Checklist

For teams adopting the new architecture:

### ✅ Immediate (No Code Changes Required)
- [x] Existing `PatternAnalysisService` calls continue to work
- [x] Result formats (`AnalysisEnvelope`, `AnalysisSummary`) unchanged
- [x] Top-level analysis functions maintained

### ✅ Recommended (Better Performance)
- [ ] Switch to `UnifiedPatternService` for new development
- [ ] Use quality-gated calibration (enabled by default)
- [ ] Adopt evidence-based analysis inspection
- [ ] Migrate custom patterns to JSON DSL format

### ✅ Advanced (Full Migration)
- [ ] Implement custom pattern plugins using `PluginRegistry`
- [ ] Integrate corpus mining for domain-specific training
- [ ] Use `PatternEngine` directly for maximum control
- [ ] Contribute patterns to shared pattern library

## Support and Resources

### Documentation
- **Quick Start**: [`README.md`](README.md) - Basic usage examples
- **API Reference**: [`docs/API_GUIDE.md`](docs/API_GUIDE.md) - Complete API documentation
- **Architecture**: [`docs/PATTERN_ENGINE_ARCHITECTURE.md`](docs/PATTERN_ENGINE_ARCHITECTURE.md) - Technical deep dive
- **Development**: [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) - Contributing guidelines

### Migration Support
- Legacy code preserved as `pattern_analysis_service_legacy.py` (backup reference)
- Comprehensive test suite validates behavior preservation
- All migration changes documented in [`CHANGELOG.md`](CHANGELOG.md)

### Performance Monitoring
- Test suite success rates maintained above 50% for all analysis types
- Calibration quality gates prevent confidence degradation
- Comprehensive regression testing across 400+ test cases

---

**Migration Completed**: September 2024
**Architecture Version**: Unified Pattern Engine v1.0
**Status**: Production Ready with Calibrated Confidence Scoring
