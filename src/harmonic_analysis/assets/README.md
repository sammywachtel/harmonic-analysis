# Harmonic Analysis Assets

This directory contains **production assets** for the harmonic analysis library that are loaded at runtime.

## Quality-Gated Calibration System (Iteration 4+)

The harmonic analysis library now uses a **quality-gated calibration system** that automatically trains and applies confidence calibration with strict validation to prevent degradation.

### Key Features

- **Quality Gates**: Prevents calibration when insufficient signal exists (correlation, sample count, variance, ECE degradation checks)
- **Multiple Methods**: Automatic selection between Platt scaling, Isotonic regression, or Identity fallback
- **Comprehensive Evaluation**: ECE (Expected Calibration Error), Brier score, and reliability curve analysis
- **Conservative Fallback**: Uses identity mapping when quality gates fail to maintain system reliability

## How Quality-Gated Calibration Works

### Automatic Initialization
Both `PatternAnalysisService` and `UnifiedPatternService` automatically initialize calibration:

```python
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

# Automatically initializes quality-gated calibration
service = PatternAnalysisService()  # auto_calibrate=True by default
result = await service.analyze_with_patterns_async(['C', 'F', 'G', 'C'])
# Result confidence scores are automatically calibrated if quality gates pass
```

### Manual Calibration Control
For explicit control over calibration:

```python
from harmonic_analysis.core.pattern_engine.calibration import Calibrator
import numpy as np

# Initialize calibrator with custom quality gate thresholds
calibrator = Calibrator(
    min_correlation=0.1,    # Minimum |correlation| required
    min_samples=50,         # Minimum sample count required
    min_variance=0.01,      # Minimum target variance required
    max_ece_increase=0.05   # Maximum allowed ECE increase
)

# Fit calibration with synthetic or real training data
raw_scores = np.random.uniform(0.1, 0.9, 200)
targets = raw_scores * 0.8 + 0.1  # Simulated ground truth
mapping = calibrator.fit(raw_scores, targets)

# Check if quality gates passed
if mapping.passed_gates:
    print(f"✅ Calibration successful ({mapping.mapping_type})")
    calibrated = mapping.apply(0.75)
    print(f"Raw: 0.75 → Calibrated: {calibrated:.3f}")
else:
    print("⚠️ Quality gates failed - using identity mapping")
```

### Comprehensive Evaluation
Generate detailed calibration assessment:

```python
# Evaluate calibration performance
report = calibrator.evaluate_calibration(raw_scores, targets, mapping)

print(f"Mapping Type: {report.mapping_type}")
print(f"Quality Gates: {'✅ Passed' if report.passed_quality_gates else '❌ Failed'}")

# Check improvement metrics
improvements = report.improvement_summary
print(f"ECE Improvement: {improvements['ece_improvement']:.4f}")
print(f"Brier Improvement: {improvements['brier_improvement']:.4f}")

# Review quality warnings
if report.warnings:
    print("⚠️ Warnings:")
    for warning in report.warnings:
        print(f"  - {warning}")
```

## Quality Gates Explained

### 1. Correlation Gate
Ensures meaningful relationship between raw scores and targets:
- **Threshold**: |correlation| ≥ 0.1 (default)
- **Purpose**: Prevents calibration on noise

### 2. Sample Count Gate
Ensures sufficient data for reliable calibration:
- **Threshold**: sample_count ≥ 50 (default)
- **Purpose**: Prevents overfitting on small datasets

### 3. Variance Gate
Ensures targets have sufficient spread:
- **Threshold**: variance ≥ 0.01 (default)
- **Purpose**: Prevents calibration on constant targets

### 4. ECE Degradation Gate
Ensures calibration doesn't make things worse:
- **Threshold**: ECE_increase ≤ 0.05 (default)
- **Purpose**: Conservative safety check

## Calibration Methods

### Auto Method Selection (Recommended)
1. Try **Platt Scaling** first (logistic regression - stable, parametric)
2. Fall back to **Isotonic Regression** if Platt fails (non-parametric, flexible)
3. Fall back to **Identity** if both fail quality gates (no calibration)

### Manual Method Selection
```python
# Force specific calibration method
mapping_platt = calibrator.fit(raw_scores, targets, method="platt")
mapping_isotonic = calibrator.fit(raw_scores, targets, method="isotonic")
mapping_identity = calibrator.fit(raw_scores, targets, method="identity")
```

## Monitoring and Debugging

### Service Initialization Logs
```python
import logging
logging.basicConfig(level=logging.INFO)

service = PatternAnalysisService()
# Look for: "✅ Quality-gated calibration initialized: platt"
# Or: "⚠️ Calibration quality gates failed - using identity mapping"
```

### Analysis Logs
```python
# Enable debug logging to see calibration application
logging.basicConfig(level=logging.DEBUG)

result = await service.analyze_with_patterns_async(['C', 'F', 'G', 'C'])
# Look for: "Calibrated functional confidence: 0.650 → 0.720 (delta: +0.070)"
```

## Migration from Legacy System

The old `CalibrationService` and JSON-based calibration has been replaced:

### ❌ Old (Removed)
```python
from harmonic_analysis.services.calibration_service import CalibrationService  # No longer exists
```

### ✅ New (Iteration 4+)
```python
from harmonic_analysis.core.pattern_engine.calibration import Calibrator
calibrator = Calibrator()
mapping = calibrator.fit(training_data)
```

## Documentation Links

- **📚 Complete Calibration Guide**: [`docs/CALIBRATION_GUIDE.md`](../../../docs/CALIBRATION_GUIDE.md)
- **🔬 Technical Architecture**: [`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md)
- **⚙️ Development Setup**: [`docs/DEVELOPMENT.md`](../../../docs/DEVELOPMENT.md)

## File Structure

```
src/harmonic_analysis/assets/
├── README.md                                    # This file (calibration documentation)
├── __init__.py                                  # Python package init
└── glossary.json                                # Music theory glossary data
```

**Note**: This directory now serves as documentation. The new quality-gated calibration system operates entirely in-memory with synthetic training data, eliminating the need for external calibration files.
