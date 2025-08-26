# Development Guide

## Development Commands

### Development Workflow
```bash
# Setup development environment
pip install -e .
pip install -r requirements-dev.txt

# Pre-commit hooks (installed)
pre-commit install
pre-commit run --all-files

# Code quality
black src/ tests/ scripts/
isort src/ tests/ scripts/
flake8 src/ tests/ scripts/
mypy src/ --ignore-missing-imports
```

### Maintenance Scripts
```bash
# Confidence calibration analysis (essential for debugging)
python scripts/confidence_calibration_analysis.py

# Regenerate comprehensive test data (when needed)
python scripts/generate_comprehensive_multi_layer_tests.py
```

**Key Maintenance Tools:**
- **`scripts/confidence_calibration_analysis.py`**: Essential for confidence calibration and debugging. Used to identify critical bugs that improved functional harmony success rates.
- **`scripts/generate_comprehensive_multi_layer_tests.py`**: Generates 427+ comprehensive test cases with multi-layer expectations for comprehensive validation.

See `scripts/README.md` for detailed documentation of maintenance scripts.

## Critical Development Notes

### Code Quality Standards
- All code must pass: black, isort, flake8, mypy
- Test coverage should remain above 60%
- Pre-commit hooks prevent quality regressions

### Music Theory Accuracy
- Maintain theoretical consistency across all analysis types
- Preserve Parent Key + Local Tonic approach for modal analysis
- Ensure confidence scoring reflects actual analytical certainty

## Key Files for Maintenance

### Core Analysis
- `src/harmonic_analysis/enhanced_modal_analyzer.py` - Modal analysis engine
- `src/harmonic_analysis/functional_harmony.py` - Functional harmony engine
- `src/harmonic_analysis/multiple_interpretation_service.py` - Main orchestrator
- `src/harmonic_analysis/comprehensive_analysis.py` - Unified analysis entry point

### Configuration
- `pyproject.toml` - Package configuration and test settings
- `.pre-commit-config.yaml` - Code quality hooks
- `.github/workflows/` - CI/CD pipeline configuration

## Current Development Status and Next Phase

### ✅ Completed: Confidence Calibration System
**Achievement**: Comprehensive confidence calibration completed with music theory validation
- **C-F-C (Plagal)**: 0.712 confidence (Expected: 0.60 ±0.15) ✅ Within tolerance
- **C-Am-F-G (I-vi-IV-V)**: 0.864 confidence (Expected: 0.95 ±0.15) ✅ Within tolerance
- **Test Performance**: Modal (56%+), Functional (50%+) now passing validation targets
- **Theoretical Soundness**: All confidence values validated by music theory expert analysis

### 🔧 Next Phase: Modal Contextless Analysis
**Current Challenge**: Modal progressions without parent key context (0% success rate)
- **Issue**: G-F-G progression needs to infer C major parent key from harmonic content
- **Scope**: ~168 test cases requiring contextless modal detection
- **Impact**: Addresses remaining gap to achieve 50%+ overall system performance

### 🚀 Future Enhancements
**Architecture Extensions** (post-production):
- **Jazz Harmony Patterns**: Tritone substitutions, altered dominants
- **Voice Leading Analysis**: Factor voice leading quality into confidence scores
- **Cultural Harmony Systems**: Adapt framework for non-Western harmonic systems
- **Machine Learning Integration**: User feedback-driven confidence refinement

## Next Steps for Library Maintenance

### Immediate Priorities (Next Session)

1. **Confidence Calibration Deep Dive**
   ```bash
   # Analyze confidence scoring patterns
   python scripts/analyze_confidence_patterns.py

   # Compare test expectations vs actual output
   python scripts/compare_test_vs_actual.py
   ```

2. **Functional Harmony Debugging**
   ```bash
   # Debug functional harmony detection
   python -c "
   from src.harmonic_analysis.functional_harmony import FunctionalHarmonyAnalyzer
   analyzer = FunctionalHarmonyAnalyzer()
   result = analyzer.analyze_functionally(['C', 'F', 'G', 'C'])
   print(f'Confidence: {result.confidence}, Roman: {[c.roman_numeral for c in result.chords]}')
   "
   ```

3. **Test Expectation Validation**
   - Review comprehensive test generator logic and expectations
   - Identify unrealistic test expectations
   - Ensure consistent behavioral patterns across test cases

### Medium-Term Improvements

4. **Performance Optimization**
   - Current coverage: 58% (room for improvement)
   - Focus on `chord_parser.py` (17% coverage)
   - Optimize `comprehensive_analysis.py` (29% coverage)

5. **Test Suite Refinement**
   - Increase functional harmony success rate to 50%+
   - Achieve 70%+ overall system performance
   - Add regression tests for edge cases

6. **Documentation Enhancement**
   - Add usage examples for each analysis engine
   - Create API documentation with confidence scoring explanations
   - Document modal vs functional analysis decision tree

### Long-Term Roadmap

7. **Integration Support**
   - Provide web API integration examples
   - Add REST API endpoint patterns for chord progression analysis
   - Design application integration patterns

8. **Advanced Features**
   - Voice leading analysis
   - Harmonic rhythm detection
   - Real-time MIDI analysis support
   - Extended jazz harmony analysis
