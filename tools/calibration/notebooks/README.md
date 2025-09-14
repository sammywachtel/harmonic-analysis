# 🎯 Confidence Calibration Notebooks

This directory contains Jupyter notebooks for analyzing and calibrating confidence scores from the harmonic analysis system.

## 📚 Available Notebooks

### 🌟 **Confidence_Calibration_Enhanced.ipynb** (Recommended)
**Enhanced visualization and analysis notebook** with:
- **Color-coded calibration zones** (🟢 Good, 🟡 Fair, 🔴 Poor)
- **Good vs Bad calibration examples** with specific progressions
- **Problem area highlighting** in error distribution plots
- **Category-specific analysis** showing which progression types need calibration
- **Downloadable results** and calibration mappings

**Features:**
- Visual indicators showing exactly where calibration is needed
- Detailed explanations of what good/bad calibration looks like
- Interactive charts with colored zones and error statistics
- Real examples from the test suite

### 📊 **Confidence_Calibration_Consolidated.ipynb**
**Original comprehensive notebook** covering:
- Basic baseline generation and analysis
- Simple calibration mapping learning
- Pre/post calibration comparisons
- Standard scatter plots and histograms

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install jupyter matplotlib seaborn pandas numpy
   ```

2. **Run the enhanced notebook:**
   ```bash
   cd tools/calibration/notebooks/
   jupyter notebook Confidence_Calibration_Enhanced.ipynb
   ```

3. **Follow the guided workflow:**
   - Generate or load confidence baseline
   - Analyze pre-calibration performance
   - Learn calibration mapping
   - Apply and validate calibration

## 📈 Understanding the Visualizations

### Color Zones
- 🟢 **Green Zone**: Well-calibrated (error < 0.1)
- 🟡 **Yellow Zone**: Needs adjustment (error 0.1-0.2)
- 🔴 **Red Zone**: Poorly calibrated (error > 0.2)

### Key Metrics
- **MAE (Mean Absolute Error)**: Average prediction error
- **Bias**: Systematic over/under-confidence
- **Pass Rate**: Percentage of cases within tolerance

### Good vs Bad Examples
The enhanced notebook shows specific chord progressions that demonstrate:
- **Good calibration**: Expected vs actual confidence match closely
- **Bad calibration**: Significant mismatch requiring adjustment

## 🔧 Integration with Tests

The notebooks work with the test suite:
```python
# Generate baseline from test data
python scripts/export_baseline.py \
    --tests tests/data/generated/comprehensive-multi-layer-tests.json \
    --out tools/calibration/confidence_baseline.json

# Run calibration validation test
python -m pytest tests/integration/test_confidence_against_baseline.py -v
```

## 📊 Output Files

The notebooks generate:
- **`confidence_baseline.json`**: Raw analysis results
- **`calibration_mapping.json`**: Learned calibration offsets
- **`confidence_calibrated.json`**: Calibrated results for validation

## 🎨 Customization

You can adjust the analysis by modifying:
- **Tolerance thresholds**: Change `HA_PER_CASE_TOL` and `HA_MAE_TOL`
- **Visualization colors**: Modify the color zones in plotting functions
- **Categories**: Add category-specific calibration rules

## 🤝 Contributing

To add new calibration methods:
1. Add the method in a new cell
2. Include visualizations showing before/after
3. Update the summary section with recommendations
4. Test with the validation suite

## ⚡ Tips for Best Results

1. **Run on representative data**: Use comprehensive test suite
2. **Check category-specific patterns**: Some progression types behave differently
3. **Validate on held-out data**: Don't overfit to training set
4. **Monitor edge cases**: Pay attention to extreme confidence values
5. **Update regularly**: Re-calibrate as the analysis system evolves
