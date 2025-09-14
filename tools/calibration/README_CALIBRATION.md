# Confidence Calibration System

This directory contains a **complete 4-stage confidence calibration system** for the harmonic-analysis library. The system provides theoretically-sound confidence calibration through an interactive notebook, CLI scripts, and production integration.

## 📁 Directory Structure

```
tools/calibration/
├── README_CALIBRATION.md                        # This file - complete system overview
├── notebooks/
│   ├── Confidence_Calibration_Enhanced.ipynb   # Main interactive calibration notebook
│   ├── calibration_utils.py                    # Utility functions for calibration
│   └── README.md                               # Notebook-specific documentation
├── calibration_mapping.json                    # Generated calibration parameters (development)
├── confidence_baseline.json                    # Raw analysis baseline for training
└── confidence_calibrated.json                  # Post-calibration results (validation)
```

## 🎯 System Overview

### 4-Stage Calibration Pipeline

The system implements a sophisticated 4-stage calibration process:

1. **Stage 0: Data Hygiene** - Deduplication, evidence filtering, stratified cross-validation
2. **Stage 1: Platt Scaling** - Global bias correction via logistic regression
3. **Stage 2: Isotonic Regression** - Non-linear monotonic shape correction
4. **Stage 4: Uncertainty Learning** - Confidence down-weighting for high-uncertainty cases

### Bucket-Based Routing

Different harmonic analysis types receive specialized calibration:

- **`functional_simple`** - Basic I-V-I progressions, clear tonal centers
- **`modal_marked`** - Clear modal characteristics (b7, modal patterns)
- **`chromatic_borrowed`** - Non-diatonic elements, secondary dominants
- **`ambiguous_sparse`** - Short/unclear progressions (< 4 chords)
- **`melodic_short`** - Scale/melody analysis (< 8 notes)

## 🚀 Quick Start

### Option 1: Complete Workflow (Interactive Notebook)

```bash
# 1. Open the comprehensive notebook
jupyter lab notebooks/Confidence_Calibration_Enhanced.ipynb

# The notebook handles everything:
# - Baseline generation from test suite
# - 4-stage calibration training with visualizations
# - Performance validation and analysis
# - Production deployment with automatic backup
```

### Option 2: Baseline Export (CLI Script)

```bash
# Export baseline from test suite (for notebook input)
python scripts/export_baseline.py \
    --tests tests/data/generated/comprehensive-multi-layer-tests.json \
    --out tools/calibration/confidence_baseline.json

# Note: Calibration training is done in the notebook using the 4-stage pipeline
# The notebook handles all calibration training, validation, and deployment
```

## 📓 Interactive Notebook Features

The main notebook (`Confidence_Calibration_Enhanced.ipynb`) provides:

### ✅ Complete Analysis Pipeline
- **Section 1**: Setup and test suite loading
- **Section 2**: Baseline generation and raw performance analysis
- **Section 3**: Data hygiene and quality validation
- **Section 4**: Stage 1 - Platt scaling calibration
- **Section 5**: Stage 2 - Isotonic regression refinement
- **Section 6**: Stage 4 - Uncertainty learning integration
- **Section 7**: Performance validation and bucket analysis
- **Section 8**: Production deployment with backup management

### ✅ Rich Visualizations
- Calibration plots showing before/after confidence distributions
- Reliability diagrams for assessing calibration quality
- Bucket-specific performance analysis
- Cross-validation stability metrics
- MAE and bias tracking across calibration stages

### ✅ Production Integration
- Automated deployment to `src/harmonic_analysis/assets/`
- Backup rotation with datetime stamps
- CalibrationService validation testing
- Performance monitoring setup

## 🔧 CLI Scripts Reference

### `export_baseline.py`
Generates raw confidence baseline from test suite (input for notebook calibration training).

```bash
python scripts/export_baseline.py \
    --tests tests/data/generated/comprehensive-multi-layer-tests.json \
    --out tools/calibration/confidence_baseline.json \
    --key-hint "C major"                    # Optional key hint filter
    --max-cases 1000                        # Optional limit for testing
```

**Output**: `confidence_baseline.json` with raw analysis results and expected outcomes.

**Note**: This is the only CLI script currently used. All calibration training, validation, and deployment is handled by the interactive notebook which implements the advanced 4-stage calibration pipeline.

## 🏗️ Library Integration

### Automatic Integration
The PatternAnalysisService automatically loads calibration when available:

```python
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

# Loads calibration from src/harmonic_analysis/assets/calibration_mapping.json
service = PatternAnalysisService()  # auto_calibrate=True by default
result = await service.analyze_with_patterns_async(['C', 'F', 'G', 'C'])
# Confidence scores are automatically calibrated using 4-stage pipeline
```

### Manual Control
For explicit calibration control:

```python
from harmonic_analysis.services.calibration_service import CalibrationService

# Load calibration mapping
calibration = CalibrationService("src/harmonic_analysis/assets/calibration_mapping.json")

# Apply 4-stage calibration
calibrated_confidence = calibration.calibrate_confidence(
    raw_confidence=0.85,
    track="functional",  # "functional" or "modal"
    features={
        "chord_count": 4,
        "evidence_strength": 0.7,
        "outside_key_ratio": 0.2,
        "has_flat7": False,
        "has_secondary_dominants": True,
        "is_melody": False,
        "progression_length": 4
    }
)
```

### Feature Extraction
The system automatically extracts routing features from analyses:

- **`chord_count`** - Number of chords in progression
- **`evidence_strength`** - Average evidence confidence
- **`outside_key_ratio`** - Proportion of non-diatonic chords
- **`has_flat7`** - Presence of modal flat-7 chords
- **`has_secondary_dominants`** - Presence of secondary dominant patterns
- **`is_melody`** - Whether analysis is melodic (vs harmonic)
- **`progression_length`** - Total length for bucket classification

## 📊 Performance Monitoring

### Target Metrics
- **MAE (Mean Absolute Error)**: ≤ 0.10 per bucket
- **Bias**: ±0.05 across functional/modal tracks
- **Cross-validation stability**: < 10% variance across folds

### Quality Indicators
- 🟢 **Green**: MAE < 0.1 (excellent calibration)
- 🟡 **Orange**: MAE 0.1-0.2 (acceptable, monitor closely)
- 🔴 **Red**: MAE > 0.2 (recalibration needed)

### Monitoring Commands

```python
# Enable calibration logging
import logging
logging.basicConfig(level=logging.INFO)

service = PatternAnalysisService()
# Watch for calibration messages:
# "✅ Loaded calibration service from ..."
# "🎯 Calibrated functional confidence: 0.850 → 0.780 (delta: -0.070)"
# "Confidence calibration completed: 3 scores calibrated in 2.1ms"
```

## 🔄 Development Workflow

### 1. Development Phase
```bash
# Work in tools/calibration/
cd tools/calibration/
jupyter lab notebooks/Confidence_Calibration_Enhanced.ipynb

# Generated files stay in tools/calibration/:
# - confidence_baseline.json (raw analysis results)
# - calibration_mapping.json (trained parameters)
# - confidence_calibrated.json (validation results)
```

### 2. Production Deployment
```bash
# Use notebook deployment cell or manual copy:
cp tools/calibration/calibration_mapping.json \
   src/harmonic_analysis/assets/calibration_mapping.json

# Library automatically picks up the new calibration
```

### 3. Validation & Monitoring
```bash
# Test calibration integration
python -c "
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService
import logging
logging.basicConfig(level=logging.INFO)
service = PatternAnalysisService()
print('Calibration ready!' if service.calibration_service else 'No calibration loaded')
"
```

## 📚 Documentation Links

- **📊 Confidence Theory**: [`docs/CONFIDENCE_CALIBRATION.md`](../../docs/CONFIDENCE_CALIBRATION.md)
- **🏗️ Library Assets**: [`src/harmonic_analysis/assets/README.md`](../../src/harmonic_analysis/assets/README.md)
- **⚙️ Integration Guide**: [`.local_docs/music-alg-3b-calibration.md`](../../.local_docs/music-alg-3b-calibration.md)
- **📓 Notebook Documentation**: [`notebooks/README.md`](notebooks/README.md)

## 🚨 Troubleshooting

### Common Issues

**"No calibration mapping found"**
```bash
# Verify file exists
ls -la src/harmonic_analysis/assets/calibration_mapping.json

# If missing, run deployment from notebook or copy manually
cp tools/calibration/calibration_mapping.json \
   src/harmonic_analysis/assets/calibration_mapping.json
```

**"sklearn warnings about small sample sizes"**
```bash
# Normal during bucket training with limited data
# Check notebook cell outputs for "✅ Advanced calibration mapping complete!"
# Warnings are automatically suppressed in production
```

**"Calibration delta is 0.000"**
```bash
# Could indicate:
# 1. Calibration mapping not loaded (check logs)
# 2. Analysis already well-calibrated (expected for some cases)
# 3. Features don't match any trained buckets (falls back to global)
```

---

**🎯 Advanced 4-stage confidence calibration system ready for production deployment** ✨
