# Calibration Guide - Quality-Gated Confidence Calibration

This guide documents the advanced calibration system implemented in Iteration 4 of the harmonic analysis engine redesign.

## Overview

The calibration system implements **quality-gated** confidence calibration with strict validation to prevent degradation when insufficient signal exists in the data. This represents a major improvement over the previous calibration approaches.

## Key Features

### ✅ Quality Gates
- **Correlation Gate**: Minimum correlation between raw scores and targets
- **Sample Count Gate**: Minimum number of samples required
- **Variance Gate**: Minimum variance in target values
- **ECE Degradation Gate**: Maximum allowed increase in Expected Calibration Error

### ✅ Multiple Calibration Methods
- **Platt Scaling**: Logistic regression calibration for global bias correction
- **Isotonic Regression**: Non-parametric monotonic calibration for shape correction
- **Identity Fallback**: No calibration when quality gates fail

### ✅ Comprehensive Evaluation
- **ECE (Expected Calibration Error)**: Primary calibration metric
- **Brier Score**: Reliability assessment
- **Monotonicity Checking**: Ensures rank preservation
- **Reliability Curves**: Visual calibration assessment

## Architecture

```python
from harmonic_analysis.core.pattern_engine.calibration import Calibrator, CalibrationMapping

# Initialize with quality gate thresholds
calibrator = Calibrator(
    min_correlation=0.1,    # Minimum |correlation| required
    min_samples=50,         # Minimum sample count required
    min_variance=0.01,      # Minimum target variance required
    max_ece_increase=0.05   # Maximum allowed ECE increase
)

# Fit calibration with automatic method selection
mapping = calibrator.fit(raw_scores, targets, method="auto")

# Apply calibration
calibrated_score = mapping.apply(raw_confidence)
```

## Usage Examples

### Basic Calibration

```python
import numpy as np
from harmonic_analysis.core.pattern_engine.calibration import Calibrator

# Sample data
raw_scores = np.array([0.3, 0.7, 0.9, 0.2, 0.8])
targets = np.array([0.0, 1.0, 1.0, 0.0, 1.0])

# Fit calibration
calibrator = Calibrator()
mapping = calibrator.fit(raw_scores, targets)

# Check if calibration passed quality gates
if mapping.passed_gates:
    print(f"✅ Calibration successful ({mapping.mapping_type})")
    calibrated = mapping.apply(0.75)
    print(f"Raw: 0.75 → Calibrated: {calibrated:.3f}")
else:
    print("⚠️ Quality gates failed - using identity mapping")
```

### Comprehensive Evaluation

```python
# Generate detailed evaluation report
report = calibrator.evaluate_calibration(raw_scores, targets, mapping)

print(f"Mapping Type: {report.mapping_type}")
print(f"Quality Gates: {'✅ Passed' if report.passed_quality_gates else '❌ Failed'}")

# Improvement metrics
improvements = report.improvement_summary
print(f"ECE Improvement: {improvements['ece_improvement']:.4f}")
print(f"Brier Improvement: {improvements['brier_improvement']:.4f}")

# Quality warnings
if report.warnings:
    print("⚠️ Warnings:")
    for warning in report.warnings:
        print(f"  - {warning}")

# Reliability curve data for plotting
curve = report.reliability_bins
print(f"Reliability bins: {len(curve['bin_centers'])} bins")
```

## Quality Gates

### 1. Correlation Gate
Ensures meaningful relationship between raw scores and targets:
```
|correlation(raw_scores, targets)| ≥ min_correlation
```
**Default**: 0.1 (weak but detectable correlation)

### 2. Sample Count Gate
Ensures sufficient data for reliable calibration:
```
len(samples) ≥ min_samples
```
**Default**: 50 samples

### 3. Variance Gate
Ensures targets have sufficient spread:
```
var(targets) ≥ min_variance
```
**Default**: 0.01 (prevents constant targets)

### 4. ECE Degradation Gate
Ensures calibration doesn't make things worse:
```
ECE_after - ECE_before ≤ max_ece_increase
```
**Default**: 0.05 (small tolerance for noise)

## Calibration Methods

### Platt Scaling
Fits logistic regression: `calibrated = sigmoid(A * raw + B)`

**Pros**:
- Fast and stable
- Good for global bias correction
- Parametric (2 parameters)

**Cons**:
- Limited flexibility
- Assumes logistic relationship

### Isotonic Regression
Fits monotonic non-parametric mapping

**Pros**:
- Very flexible
- Preserves monotonicity
- No distributional assumptions

**Cons**:
- Can overfit with small samples
- More complex

### Auto Method Selection
1. Try Platt scaling first (simpler, more stable)
2. Fall back to isotonic if Platt fails validation
3. Fall back to identity if both fail quality gates

## Metrics

### Expected Calibration Error (ECE)
Measures how far predicted confidences are from actual accuracy:
```
ECE = Σ (|accuracy_i - confidence_i| * weight_i)
```
**Lower is better** (0.0 = perfect calibration)

### Brier Score
Measures prediction accuracy:
```
Brier = mean((predictions - targets)²)
```
**Lower is better** (0.0 = perfect predictions)

### Correlation
Measures linear relationship between predictions and targets:
```
correlation = corr(predictions, targets)
```
**Higher absolute value is better** (-1.0 or 1.0 = perfect linear relationship)

## Best Practices

### 1. Data Quality
- Ensure diverse range of confidence scores
- Avoid constant or near-constant targets
- Use representative validation data

### 2. Quality Gate Tuning
- Adjust `min_correlation` based on domain (lower for noisy domains)
- Increase `min_samples` for more stable calibration
- Tune `max_ece_increase` to balance robustness vs. improvement

### 3. Evaluation
- Always check `passed_gates` before trusting calibration
- Monitor ECE improvement to detect overfitting
- Use reliability curves for visual validation

### 4. Integration
```python
# Recommended pattern for services
class AnalysisService:
    def __init__(self):
        self.calibrator = Calibrator()
        self.calibration_mapping = None

    def calibrate_confidence(self, raw_confidence: float) -> float:
        if self.calibration_mapping and self.calibration_mapping.passed_gates:
            return self.calibration_mapping.apply(raw_confidence)
        return raw_confidence  # Identity fallback
```

## Troubleshooting

### Quality Gates Failing

**Low Correlation**:
- Check if targets are meaningful
- Verify raw scores have reasonable range
- Consider if relationship is non-linear

**Insufficient Samples**:
- Collect more training data
- Lower `min_samples` if domain-appropriate
- Use simpler calibration method

**Low Variance**:
- Check for constant or near-constant targets
- Verify target generation is working correctly
- Consider if domain has inherent low variance

**ECE Increase**:
- May indicate overfitting
- Try simpler calibration method (Platt vs Isotonic)
- Check for outliers in data

### Poor Calibration Performance

1. **Check baseline ECE**: If already well-calibrated, improvement may be minimal
2. **Verify data quality**: Look for outliers, errors, or bias
3. **Examine reliability curve**: Visual inspection often reveals issues
4. **Consider domain factors**: Some domains may be inherently difficult to calibrate

## Technical Details

### Mathematical Foundation
The calibration system implements the framework from:
- Platt, J. (1999). Probabilistic outputs for support vector machines
- Zadrozny & Elkan (2002). Transforming classifier scores into accurate multiclass probability estimates

### Implementation Notes
- Uses scikit-learn for Platt scaling and isotonic regression
- ECE calculation follows standard binning approach (10 bins default)
- Monotonicity checking allows small violations (10% tolerance)
- All floating-point operations use double precision

### Performance Characteristics
- **Memory**: O(n) where n = number of samples
- **Time**: O(n log n) for isotonic, O(n) for Platt scaling
- **Numerical Stability**: Robust to extreme values and edge cases

## Migration from Legacy System

The old `CalibrationService` has been replaced with this quality-gated system:

### ❌ Old (Deprecated)
```python
from harmonic_analysis.services.calibration_service import CalibrationService
service = CalibrationService("calibration_mapping.json")
calibrated = service.calibrate_confidence(raw_score, track, features)
```

### ✅ New (Iteration 4+)
```python
from harmonic_analysis.core.pattern_engine.calibration import Calibrator
calibrator = Calibrator()
mapping = calibrator.fit(training_data)
calibrated = mapping.apply(raw_score) if mapping.passed_gates else raw_score
```

### Key Differences
1. **Quality Gates**: New system prevents degradation
2. **Simplicity**: No complex feature extraction or routing
3. **Transparency**: Clear metrics and evaluation
4. **Robustness**: Conservative fallback to identity mapping

## References

- **Iteration 4 Specification**: `music-alg-6a-engine-redesign.md`
- **Implementation**: `src/harmonic_analysis/core/pattern_engine/calibration.py`
- **Original Calibration Research**: `.local_docs/music-alg-3a-calibration.md`