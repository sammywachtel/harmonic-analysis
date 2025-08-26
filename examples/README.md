# Examples Directory 📚

This directory contains interactive examples and tutorials for the Harmonic Analysis library.

## Files

### `harmonic_analysis_tutorial.ipynb`
A comprehensive Jupyter notebook containing all the examples from the main README, organized into runnable sections:

- **Basic chord progression analysis** - Understanding how the library works
- **Scale and melody analysis** - When you get `suggested_tonic` and why
- **Style-specific examples** - Jazz, rock, classical, modal music
- **Multiple interpretations** - Handling ambiguous progressions
- **Advanced options** - Fine-tuning analysis with context
- **Confidence scores** - Understanding what the percentages mean
- **Your own experiments** - Cells to try your own progressions

## Running the Tutorial

### Option 1: Jupyter Lab/Notebook
```bash
# From the project root
pip install jupyter
cd examples
jupyter notebook harmonic_analysis_tutorial.ipynb
```

### Option 2: VS Code
1. Open `harmonic_analysis_tutorial.ipynb` in VS Code
2. Install the Python + Jupyter extensions
3. Select the project's Python interpreter
4. Run cells interactively

### Option 3: Google Colab
1. Upload the notebook to Google Colab
2. Add this cell at the beginning:
```python
!pip install harmonic-analysis
```

## Tips for Best Experience

1. **Run cells in order** - Each section builds on the previous ones
2. **Experiment freely** - Modify the chord progressions and scales to see how analysis changes
3. **Try your own music** - Use the "Your Turn" sections to analyze your compositions
4. **Compare results** - Look at how the same notes are analyzed differently as scales vs melodies

## What You'll Learn

By working through this tutorial, you'll understand:
- How the library's 5-stage analysis process works
- When to expect different types of analysis (functional, modal, chromatic)
- Why confidence scores vary and what they mean
- The difference between scale analysis and melody analysis
- How to provide context to guide analysis
- How to interpret multiple valid interpretations

Perfect for musicians who want to understand what the library is doing and developers who want to see comprehensive usage examples!

## Next Steps

After completing the tutorial:
- Check out the [API documentation](../docs/API_GUIDE.md)
- Explore the [interactive demo](../demo/README.md)
- Read about the [theoretical background](../docs/ARCHITECTURE.md)
