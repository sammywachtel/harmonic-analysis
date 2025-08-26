# Architecture Guide

## Technical Background and Architecture

### Music Theory Foundation

#### Parent Key + Local Tonic Approach
**Critical Concept**: This library uses a sophisticated modal analysis approach that separates:
- **Parent Key Signature**: The underlying scale (e.g., C major scale, no sharps/flats)
- **Local Tonic**: The note functioning as the tonal center (e.g., G)
- **Resulting Mode**: The combination (e.g., G Mixolydian = C major scale with G as tonic)

This approach provides **pedagogically valuable** analysis that helps users understand modal relationships within familiar key signatures.

#### Analytical Hierarchy
The library implements a **layered analysis approach** based on music theory pedagogy:

1. **Functional Harmony (Foundation) - 80% of Western Music**
   - Roman numeral analysis (I-IV-V progressions)
   - Chord function identification (tonic, predominant, dominant)
   - Cadence analysis and voice leading
   - Should be the primary analysis for most progressions

2. **Modal Analysis (Specialized) - 15% of Western Music**
   - Applied when functional analysis reveals modal characteristics
   - Maintains existing modal detection strengths
   - Presented as enhancement to functional analysis, not replacement

3. **Chromatic Harmony (Advanced) - 5% of Western Music**
   - Secondary dominants (V/V, V/vi)
   - Borrowed chords and modal interchange
   - Non-functional progressions

### Implementation Architecture

#### Core Analysis Pipeline
```
Input: ['Am', 'F', 'C', 'G']
    ↓
1. Parallel Analysis
   ├── Functional Harmony Analyzer
   ├── Enhanced Modal Analyzer
   └── Chromatic Analysis
    ↓
2. Evidence Collection
   ├── Cadential Evidence (bVII-I, V-I patterns)
   ├── Structural Evidence (first/last chord relationships)
   ├── Intervallic Evidence (distinctive scale degrees)
   └── Harmonic Evidence (chord qualities, progressions)
    ↓
3. Confidence Calculation
   ├── Weighted Evidence Scoring
   ├── Evidence Type Diversity Bonus
   └── Final Confidence Assignment
    ↓
4. Multiple Interpretation Generation
   ├── Primary Analysis (highest confidence)
   ├── Alternative Analyses (above threshold)
   └── Relationship Descriptions
    ↓
Output: MultipleInterpretationResult
```

#### Analysis Engine Interaction
```python
# How the engines work together
class MultipleInterpretationService:
    def __init__(self):
        self.functional_analyzer = FunctionalHarmonyAnalyzer()
        self.modal_analyzer = EnhancedModalAnalyzer()

    async def analyze_progression(self, chords):
        # Run analyzers in parallel
        functional_result, modal_result = await asyncio.gather(
            self._run_functional_analysis(chords),
            self._run_modal_analysis(chords)
        )

        # Create interpretations with evidence
        interpretations = await self._calculate_interpretations(
            chords, functional_result, modal_result
        )

        # Rank by confidence and filter
        return self._create_final_result(interpretations)
```

### Key Technical Concepts

#### Evidence-Based Analysis
The library uses **music theory evidence** to build confidence scores:

```python
class AnalysisEvidence:
    type: EvidenceType          # CADENTIAL, STRUCTURAL, INTERVALLIC, etc.
    strength: float             # 0.0 to 1.0
    description: str            # Human-readable evidence
    musical_basis: str          # Theoretical justification
```

**Evidence Types and Weights:**
- **CADENTIAL (0.4)**: Strong harmonic resolutions (V-I, bVII-I)
- **STRUCTURAL (0.25)**: Chord framing and positioning
- **INTERVALLIC (0.2)**: Distinctive modal scale degrees
- **HARMONIC (0.15)**: Chord quality patterns
- **CONTEXTUAL (0.15)**: Overall harmonic context

#### Confidence Framework Philosophy
The confidence scoring reflects **analytical certainty** rather than musical quality:

- **0.85-1.0 (Definitive)**: Unambiguous harmonic markers present
- **0.65-0.84 (Strong)**: Clear evidence with minimal ambiguity
- **0.45-0.64 (Moderate)**: Valid interpretation with competing possibilities
- **0.25-0.44 (Weak)**: Theoretically possible but lacks context
- **0.0-0.24 (Insufficient)**: Requires significant assumptions

#### Pedagogical Level Adaptation
```python
class PedagogicalLevel(Enum):
    BEGINNER = "beginner"       # Show only high-confidence primary analysis
    INTERMEDIATE = "intermediate"   # Show alternatives when reasonably strong
    ADVANCED = "advanced"       # Always show multiple perspectives
```

## Critical Architecture Components

### Core Analysis Engines
- **`enhanced_modal_analyzer.py`**: Sophisticated modal detection with pattern matching
- **`functional_harmony.py`**: Complete Roman numeral analysis and cadence detection
- **`chromatic_analysis.py`**: Secondary dominants and borrowed chord analysis
- **`multiple_interpretation_service.py`**: Orchestrates multiple analytical perspectives
- **`comprehensive_analysis.py`**: Main entry point for unified analysis

### Analysis Approach: Parent Key + Local Tonic
**CRITICAL**: All modal analysis uses consistent Parent Key Signature + Local Tonic approach
- Parent Key Signature: Underlying scale (e.g., C major, no sharps/flats)
- Local Tonic: Note functioning as tonal center (e.g., G)
- Mode: Combination (e.g., G Mixolydian = C major scale with G as tonic)

### Confidence Framework
Current thresholds based on music theory expert guidance:
- **Functional**: 0.4+ (Display threshold)
- **Modal**: 0.6+ (Display threshold)
- **Chromatic**: 0.5+ (Display threshold)

## Performance and Optimization

### Current Performance Characteristics
- **Test Coverage**: 72% (good foundation, room for improvement)
- **Analysis Speed**: ~2ms per progression (includes caching)
- **Memory Usage**: Minimal (stateless analyzers, LRU cache)
- **Concurrency**: Full async support with parallel analysis engines

### Optimization Opportunities
1. **Chord Parser (17% coverage)**: Most complex module, needs attention
2. **Comprehensive Analysis (29% coverage)**: Main orchestrator optimization
3. **Test Suite Performance**: Currently 32% overall success rate (target: 70%+)

## Integration Considerations

### Web API Integration
The library is designed for seamless web API integration:

```python
from harmonic_analysis import analyze_progression_multiple

# API endpoint implementation
async def analyze_progression_endpoint(progression: List[str]):
    result = await analyze_progression_multiple(progression)
    return {
        "primary_analysis": result.primary_analysis,
        "alternatives": result.alternative_analyses,
        "metadata": result.metadata
    }
```

### Application Integration Pattern
The library provides structured output for application consumption:

```python
# Structured data access
result = await analyze_progression_multiple(['C', 'F', 'G', 'C'])

# Extract key information
analysis_summary = {
    "type": result.primary_analysis.type,
    "analysis": result.primary_analysis.analysis,
    "confidence": result.primary_analysis.confidence,
    "key_signature": result.primary_analysis.key_signature,
    "evidence_count": len(result.primary_analysis.evidence)
}
```
