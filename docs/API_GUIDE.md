# API Usage Guide

## Core API Usage Examples

### Basic Chord Progression Analysis
```python
from harmonic_analysis import analyze_progression_multiple
from harmonic_analysis.types import AnalysisOptions

# Simple analysis
result = await analyze_progression_multiple(['C', 'F', 'G', 'C'])
print(f"Primary: {result.primary_analysis.analysis}")
print(f"Confidence: {result.primary_analysis.confidence:.2f}")

# With options
options = AnalysisOptions(
    parent_key="C major",
    pedagogical_level="intermediate",
    confidence_threshold=0.6,
    max_alternatives=2
)
result = await analyze_progression_multiple(['Am', 'F', 'C', 'G'], options)
```

### Multiple Interpretation Results
```python
# Access primary analysis
primary = result.primary_analysis
print(f"Type: {primary.type}")           # FUNCTIONAL, MODAL, or CHROMATIC
print(f"Analysis: {primary.analysis}")   # Human-readable description
print(f"Roman: {primary.roman_numerals}")# I vi IV V
print(f"Key: {primary.key_signature}")   # C major

# Access alternatives
for alt in result.alternative_analyses:
    print(f"Alternative: {alt.analysis} (confidence: {alt.confidence:.2f})")
    print(f"Relationship: {alt.relationship_to_primary}")
```

### Evidence and Reasoning Access
```python
# Examine analytical evidence
for evidence in result.primary_analysis.evidence:
    print(f"Evidence: {evidence.description}")
    print(f"Strength: {evidence.strength:.2f}")
    print(f"Type: {evidence.type}")
    print(f"Basis: {evidence.musical_basis}")
```

## Integration Patterns

### Web API Integration
The library is designed for seamless web API integration:

```python
from harmonic_analysis import analyze_progression_multiple

# Simple REST endpoint integration
async def analyze_progression_endpoint(progression: List[str]):
    result = await analyze_progression_multiple(progression)
    return {
        "primary_analysis": result.primary_analysis,
        "alternatives": result.alternative_analyses,
        "metadata": result.metadata
    }
```

### Application Integration
The library provides structured output for application consumption:

```python
# Structured output for application integration
result = await analyze_progression_multiple(['C', 'F', 'G', 'C'])

# Access structured data
analysis_data = {
    "type": result.primary_analysis.type,
    "analysis": result.primary_analysis.analysis,
    "confidence": result.primary_analysis.confidence,
    "roman_numerals": result.primary_analysis.roman_numerals,
    "key_signature": result.primary_analysis.key_signature,
    "evidence": [e.description for e in result.primary_analysis.evidence]
}
```

## Library Purpose and Intended Usage

### Primary Use Case
This library provides comprehensive harmonic analysis capabilities for chord progressions, offering:

1. **Multiple Analytical Perspectives**: Functional harmony, modal analysis, and chromatic harmony
2. **Educational Context**: Explanations suitable for different pedagogical levels (beginner/intermediate/advanced)
3. **Confidence-Based Results**: Analytical certainty scores to guide decision making
4. **Evidence-Based Reasoning**: Detailed justification for analytical conclusions

### Integration Use Cases
The library is designed for:
- **Web Applications**: REST API endpoints for harmonic progression analysis
- **Music Software**: Integration into music theory and composition tools
- **Educational Applications**: Music theory learning and analysis applications
- **Research Tools**: Academic and professional harmonic analysis utilities
- **Command Line Tools**: Standalone harmonic analysis scripts
