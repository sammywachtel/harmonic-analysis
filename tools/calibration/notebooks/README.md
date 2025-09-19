# Calibration Analysis Notebooks

This directory contains enhanced Jupyter notebooks for comprehensive confidence calibration analysis.

## 📊 Available Notebooks

### `Confidence_Calibration_Analyses.ipynb`
**Enhanced analysis and visualization notebook with detailed statistical insights and professional charts.**

**Enhanced Features:**
- 📊 **Pre-calibration performance analysis** with bias and variance decomposition
- ⚙️ **Post-calibration validation results** showing improvement metrics
- 🎯 **Visual calibration quality assessment** with color-coded quality zones
- 📈 **Enhanced reliability plots** with sample-size proportional markers
- 🎼 **Category-specific performance breakdown** by progression type
- 🔍 **Detailed ECE calculations** with per-track analysis (functional/modal)
- 📊 **Tail error analysis** for low and high confidence regions
- 💡 **Good vs bad calibration examples** with concrete musical progressions
- 📉 **Bin-level statistics** with sample counts and error analysis
- 💨 **Professional charts** with statistical annotations and quality indicators

**Prerequisites:**
Run the calibration pipeline first to generate required data:
```bash
# From tools/calibration/ directory
python calibration_pipeline.py all

# Or run stages individually:
python calibration_pipeline.py generate
python calibration_pipeline.py validate
python calibration_pipeline.py deploy
```

**Usage:**
1. Ensure prerequisites are met (calibration pipeline completed)
2. Start Jupyter: `jupyter lab` or `jupyter notebook`
3. Open `Confidence_Calibration_Analyses.ipynb`
4. Run all cells to generate comprehensive analysis with enhanced visualizations

**Output Highlights:**
- Visual calibration plots with green/orange/red quality zones
- Reliability plots showing where calibration works best
- Statistical summaries with actionable recommendations
- ECE monitoring for production quality assurance

## 🔧 Requirements

**Generated Data Files (from calibration pipeline):**
- `../confidence_baseline.json` - Raw analysis baseline with test expectations
- `../calibration_mapping.json` - 4-stage calibration parameters and bucket mappings
- `../calibration_validation_df.json` - Validation results for ECE and performance analysis

**Python Dependencies:**
- `matplotlib`, `seaborn` - Enhanced visualizations
- `numpy`, `pandas` - Statistical analysis
- `sklearn` - Isotonic regression utilities
- Harmonic analysis library modules (automatically configured)

## 📈 Enhanced Output

**Statistical Analysis:**
- **Performance metrics** (MAE, ECE, bias) with detailed breakdowns
- **Pre/post-calibration comparisons** showing system improvements
- **Quality zone analysis** (Excellent < 0.05, Good < 0.10, Fair < 0.15, Poor > 0.15)

**Professional Visualizations:**
- **Calibration scatter plots** with color-coded quality zones and error magnitude
- **Reliability plots** with sample-size proportional markers and calibration quality coloring
- **Category performance charts** showing case counts with MAE overlays
- **Error distribution histograms** with bias indicators and reference lines

**Production Insights:**
- **ECE monitoring** for each track (functional/modal) with < 0.03 targets
- **Tail error analysis** for extreme confidence regions (< 0.1, > 0.9)
- **Concrete examples** of good vs poor calibration with musical progressions
- **Actionable recommendations** for calibration improvements and quality gates

**Quality Monitoring:**
- **Bin-level statistics** with sample counts and individual point analysis
- **Statistical significance** indicators for reliability assessment
- **Production readiness** assessment with specific quality thresholds

## 🎯 Quality Standards

**Calibration Quality Thresholds:**
- 🟢 **Excellent**: Error < 0.05 (Green zones)
- 🟠 **Good**: Error 0.05-0.10 (Orange zones)
- 🟡 **Fair**: Error 0.10-0.15 (Light orange zones)
- 🔴 **Poor**: Error > 0.15 (Red zones)

**Production Targets:**
- ECE < 0.03 per track for production deployment
- Tail MAE < 0.15 in extreme confidence regions
- Bias within ±0.05 for excellent, ±0.10 for acceptable

---
*Part of the Harmonic Analysis Confidence Calibration System*
*Enhanced with professional statistical analysis and actionable insights*