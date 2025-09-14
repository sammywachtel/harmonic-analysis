# Troubleshooting and Common Issues

## Debugging Analysis Results

### Issue: Unexpected Modal Analysis Results
**Symptoms**: Modal analysis returns incorrect mode or no modal interpretation
**Common Causes**:
1. Missing parent key context - modal analysis needs harmonic context
2. Chord spelling variations (C vs B#) affecting pattern recognition
3. Insufficient modal evidence (need characteristic intervals like bVII)

**Debugging Steps**:
```python
# Check modal evidence collection
from src.harmonic_analysis.enhanced_modal_analyzer import EnhancedModalAnalyzer

analyzer = EnhancedModalAnalyzer()
result = analyzer.analyze_modal_characteristics(['G', 'F', 'G'])
print(f"Mode: {result.mode_name}")
print(f"Confidence: {result.confidence}")
print(f"Evidence: {[str(e) for e in result.evidence]}")
print(f"Parent Key: {result.parent_key_signature}")
```

### Issue: Low Functional Confidence Scores
**Symptoms**: Functional analysis returns confidence below expected thresholds
**Common Causes**:
1. Weak cadential evidence (no V-I or other strong resolutions)
2. Ambiguous chord progressions without clear tonal center
3. Evidence weight distribution favoring other analysis types

**Debugging Steps**:
```python
# Trace functional analysis confidence calculation
from src.harmonic_analysis.functional_harmony import FunctionalHarmonyAnalyzer

analyzer = FunctionalHarmonyAnalyzer()
result = analyzer.analyze_functionally(['C', 'F', 'G', 'C'])
print(f"Base Confidence: {result.confidence}")
print(f"Cadences: {[str(c) for c in result.cadences]}")
print(f"Roman Numerals: {[c.roman_numeral for c in result.chords]}")

# Check evidence generation in multiple interpretation service
from src.harmonic_analysis.multiple_interpretation_service import MultipleInterpretationService
service = MultipleInterpretationService()
evidence = service._collect_functional_evidence(['C', 'F', 'G', 'C'], result)
for e in evidence:
    print(f"Evidence: {e.description} (strength: {e.strength})")
```

### Issue: Test Case Failures
**Symptoms**: Comprehensive tests failing with confidence mismatches
**Root Cause Analysis Process**:
1. **Identify Pattern**: Are failures in specific categories (functional, modal, chromatic)?
2. **Compare Expectations**: Check test generator logic vs actual output
3. **Validate Music Theory**: Ensure test expectations are theoretically sound

**Example Investigation**:
```python
# Analyze specific failing test case
import json
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

# Load test case
with open('tests/generated/comprehensive-multi-layer-tests.json') as f:
    tests = json.load(f)

failing_test = next(t for t in tests if t['id'] == 'multi-337')  # Replace with actual failing ID
chords = failing_test['chords']
expected = failing_test['expected_functional']

# Run analysis
service = PatternAnalysisService()
result = await service.analyze_with_patterns_async(chords, profile="classical")
actual = result.primary

print(f"Test ID: {failing_test['id']}")
print(f"Chords: {chords}")
print(f"Expected Key: {expected['key_center']} (conf: {expected['confidence']})")
print(f"Actual Key: {actual.key_signature} (conf: {actual.confidence})")
print(f"Evidence Count: {len(result.evidence)}")
print(f"Evidence Types: {[e.reason for e in result.evidence]}")
```

## Performance Optimization

### Memory Usage Optimization
**Current Usage**: Minimal due to stateless design
**Optimization Opportunities**:
1. **Cache Tuning**: Adjust cache size and TTL for usage patterns
2. **Chord Parser Optimization**: Most complex module (17% coverage)
3. **Test Data Generation**: Large JSON files can be streamed

```python
# Optimize cache for specific usage patterns
from src.harmonic_analysis.multiple_interpretation_service import AnalysisCache

# Custom cache configuration
cache = AnalysisCache(max_size=1000, ttl_minutes=30)  # Increased for high-volume usage
```

### Analysis Speed Optimization
**Current Speed**: ~2ms per progression
**Bottlenecks**:
1. Evidence collection (multiple loops over chord progressions)
2. Parallel analysis coordination (async overhead)
3. Confidence calculation (weighted evidence processing)

**Optimization Strategies**:
```python
# Profile analysis performance
import time
import asyncio
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

async def profile_analysis():
    service = PatternAnalysisService()
    test_progressions = [
        ['C', 'F', 'G', 'C'],
        ['Am', 'F', 'C', 'G'],
        ['G', 'F', 'G'],
        ['C', 'Am', 'Dm', 'G']
    ]

    start = time.time()
    for progression in test_progressions:
        result = await service.analyze_with_patterns_async(progression, profile="classical")
    end = time.time()

    print(f"Average analysis time: {(end - start) / len(test_progressions) * 1000:.2f}ms")

asyncio.run(profile_analysis())
```

## Error Handling and Edge Cases

### Malformed Chord Input
**Handling Strategy**: Graceful degradation with informative errors
```python
# Example error handling patterns
try:
    service = PatternAnalysisService()
    result = await service.analyze_with_patterns_async(['C', 'InvalidChord', 'G'], profile="classical")
except ValueError as e:
    print(f"Chord parsing error: {e}")
    # Fallback to partial analysis or chord validation
```

### Empty or Single Chord Progressions
**Current Behavior**: Library handles single chords and empty inputs
**Edge Cases**:
- Single chord: Returns basic harmonic information
- Empty progression: Raises ValueError with clear message
- Duplicate chords: Analyzes as intended (e.g., 'C C C' for pedal tones)

### Enharmonic Equivalents
**Handling**: Library normalizes enharmonic spellings
**Examples**:
- C# and Db are treated as equivalent
- F# and Gb major scales produce identical analysis
- Modal analysis preserves enharmonic context when relevant

## Advanced Usage Patterns

### Custom Evidence Types
**Use Case**: Adding domain-specific analytical evidence
**Implementation**:
```python
from src.harmonic_analysis.multiple_interpretation_service import EvidenceType, AnalysisEvidence

# Extend evidence types for specific musical domains
class CustomEvidenceType(EvidenceType):
    JAZZ_SUBSTITUTION = "jazz_substitution"
    VOICE_LEADING = "voice_leading"
    HARMONIC_RHYTHM = "harmonic_rhythm"

# Create custom evidence
custom_evidence = AnalysisEvidence(
    type=CustomEvidenceType.JAZZ_SUBSTITUTION,
    strength=0.8,
    description="Tritone substitution detected",
    supported_interpretations=[InterpretationType.CHROMATIC],
    musical_basis="bII7 substitutes for V7 in jazz harmony"
)
```

### Batch Analysis Processing
**Use Case**: Analyzing large datasets of chord progressions
**Implementation**:
```python
async def batch_analyze_progressions(progressions_batch):
    """Efficiently analyze multiple progressions with shared context"""
    service = PatternAnalysisService()
    results = await asyncio.gather(*[
        service.analyze_with_patterns_async(progression, profile="classical")
        for progression in progressions_batch
    ])

    # Aggregate results for pattern analysis
    analysis_summary = {
        'total_progressions': len(results),
        'functional_dominant': sum(1 for r in results if r.primary_analysis.type == InterpretationType.FUNCTIONAL),
        'modal_dominant': sum(1 for r in results if r.primary_analysis.type == InterpretationType.MODAL),
        'average_confidence': sum(r.primary_analysis.confidence for r in results) / len(results)
    }

    return results, analysis_summary
```

### Custom Confidence Calibration
**Use Case**: Domain-specific confidence adjustments
**Implementation**:
```python
class CustomMultipleInterpretationService(MultipleInterpretationService):
    """Extended service with custom confidence calibration"""

    def _calculate_confidence(self, evidence):
        base_confidence = super()._calculate_confidence(evidence)

        # Custom calibration for specific domains
        if self._is_jazz_context(evidence):
            return min(1.0, base_confidence + 0.1)  # Boost jazz confidence
        elif self._is_classical_context(evidence):
            return max(0.3, base_confidence - 0.1)  # More conservative for classical

        return base_confidence

    def _is_jazz_context(self, evidence):
        jazz_indicators = ['extended', 'substitution', 'chromatic']
        return any(indicator in e.description.lower() for e in evidence for indicator in jazz_indicators)
```

## Integration Testing Strategies

### Web API Integration Validation
```python
# Test web API integration
import pytest
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

async def test_api_wrapper():
    """Test API wrapper function for web services"""
    progression = ["C", "F", "G", "C"]
    service = PatternAnalysisService()
    result = await service.analyze_with_patterns_async(progression, profile="classical")

    # Verify API response structure
    assert hasattr(result, 'primary')
    assert hasattr(result, 'alternative_analyses')
    assert hasattr(result, 'metadata')
    assert result.primary_analysis.confidence > 0.5
```

### Application Integration Validation
```python
# Test application interface compatibility
async def test_application_interface_compatibility():
    """Ensure Python output provides expected data structure"""
    service = PatternAnalysisService()
    result = await service.analyze_with_patterns_async(['C', 'F', 'G', 'C'], profile="classical")

    # Verify required fields for application consumption
    assert hasattr(result.primary, 'type')
    assert hasattr(result.primary_analysis, 'analysis')
    assert hasattr(result.primary_analysis, 'confidence')
    assert hasattr(result, 'alternative_analyses')
    assert hasattr(result, 'metadata')

    # Verify data types match application expectations
    assert isinstance(result.primary_analysis.confidence, float)
    assert 0.0 <= result.primary_analysis.confidence <= 1.0
```
