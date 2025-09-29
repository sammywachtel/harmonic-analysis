# API Usage Guide

## 🎯 Unified Pattern Engine API

**Production Ready**: The library now uses a unified pattern engine that provides comprehensive harmonic analysis through a single, robust architecture. The engine automatically handles key inference, modal parent key conversion, and provides quality-gated confidence scoring.

```python
# ✅ REQUIRED: Always provide key_hint for harmonic analysis
result = await service.analyze_with_patterns_async(
    ['Cm', 'F', 'Bb', 'Cm'],
    key_hint='C dorian',  # Essential for modal analysis
    profile='classical'
)

# ✅ Scale analysis requires key parameter
from harmonic_analysis import analyze_scale
result = await analyze_scale(['D', 'E', 'F', 'G', 'A', 'B', 'C'], key='C major')

# ✅ Melody analysis requires key parameter
from harmonic_analysis import analyze_melody
result = await analyze_melody(['G', 'A', 'B', 'C'], key='G major')

# ❌ Without key context: MissingKeyError will be raised
result = await analyze_scale(['C', 'D', 'E'])  # Error!
```

**Unified Engine Benefits**:
- **Automatic Key Inference**: Advanced algorithms detect appropriate key context from progressions
- **Modal Parent Key Conversion**: Intelligent conversion between local and modal parent keys
- **Quality-Gated Calibration**: Conservative confidence scoring with identity fallback
- **Evidence-Based Analysis**: Detailed pattern matching with theoretical justification

## Core API Usage Examples

### Basic Chord Progression Analysis
```python
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

# Simple analysis
service = PatternAnalysisService()
result = await service.analyze_with_patterns_async(['C', 'F', 'G', 'C'], profile="classical")
print(f"Primary: {' - '.join(result.primary.roman_numerals)}")
print(f"Confidence: {result.primary.confidence:.2f}")

# With options
service = PatternAnalysisService()
result = await service.analyze_with_patterns_async(
    ['Am', 'F', 'C', 'G'],
    profile="classical",
    key_hint="C major",
    best_cover=True  # Enable multiple interpretations
)
```

### Multiple Interpretation Results
```python
# Access primary analysis
primary = result.primary
print(f"Type: {primary.type.value}")         # functional, modal, etc.
print(f"Roman: {' - '.join(primary.roman_numerals)}")  # I - vi - IV - V
print(f"Key: {primary.key_signature}")       # C major
print(f"Confidence: {primary.confidence:.2f}")

# Access alternatives
for alt in result.alternatives:
    print(f"Alternative: {' - '.join(alt.roman_numerals)} (confidence: {alt.confidence:.2f})")
    print(f"Type: {alt.type.value}")
```

### Evidence and Reasoning Access
```python
# Examine analytical evidence
for evidence in result.evidence:
    print(f"Evidence: {evidence.reason}")
    print(f"Details: {evidence.details}")

# Examine detected patterns
for pattern in result.primary.patterns:
    print(f"Pattern: {pattern.name}")
    print(f"Score: {pattern.score:.2f}")
    print(f"Span: chords {pattern.start}-{pattern.end}")
```

## Integration Patterns

### Web API Integration
The library is designed for seamless web API integration:

```python
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

# Simple REST endpoint integration
async def analyze_progression_endpoint(progression: List[str]):
    service = PatternAnalysisService()
    result = await service.analyze_with_patterns_async(progression, profile="classical")
    return {
        "primary_analysis": result.primary.to_dict(),
        "alternatives": [alt.to_dict() for alt in result.alternatives],
        "analysis_time_ms": result.analysis_time_ms
    }
```

### Application Integration
The library provides structured output for application consumption:

```python
# Structured output for application integration
service = PatternAnalysisService()
result = await service.analyze_with_patterns_async(['C', 'F', 'G', 'C'], profile="classical")

# Access structured data
analysis_data = {
    "type": result.primary.type.value,
    "roman_numerals": result.primary.roman_numerals,
    "confidence": result.primary.confidence,
    "key_signature": result.primary.key_signature,
    "patterns": [p.name for p in result.primary.patterns],
    "evidence": [e.reason for e in result.evidence]
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
