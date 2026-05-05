# Music21 Integration - Acceptance Criteria & Test Plan

This document defines acceptance criteria and testing requirements for each phase of the music21 integration project.

## Testing Philosophy

Each iteration MUST include:
1. **Unit Tests** - Test individual components in isolation with mocks
2. **Integration Tests** - Test components working together with real music21
3. **Regression Tests** - Ensure existing functionality remains intact
4. **Acceptance Tests** - Validate user-facing features work as expected

## Phase 1: Foundation (2-3 weeks)

### Iteration 1.1: Music21Adapter ✅ COMPLETED

**Status**: Completed - commit bb26028

**Features Delivered**:
- [x] Parse MusicXML files (`from_musicxml()`)
- [x] Parse MIDI files (`from_midi()`)
- [x] Extract chord symbols from scores
- [x] Extract key information for analysis
- [x] Extract metadata (title, composer, tempo, time signature)
- [x] Extract structural information (measures, parts)
- [x] Convert music21 objects to internal string format

**Acceptance Criteria**:
- [x] ✅ Music21Adapter can parse valid MusicXML files without errors
- [x] ✅ Music21Adapter can parse valid MIDI files without errors
- [x] ✅ Adapter extracts chord symbols correctly when present
- [x] ✅ Adapter infers chords from notes when symbols absent
- [x] ✅ Adapter extracts key information or provides sensible fallback
- [x] ✅ Adapter provides clear error when music21 not installed
- [x] ✅ All internal data structures use string format (no music21 objects leak)

**Testing Status**:
- [x] ✅ **Unit Tests**: 20 tests passing (100% coverage of adapter methods)
  - Initialization and availability checks
  - File parsing (MusicXML and MIDI)
  - Key extraction with fallback
  - Chord symbol extraction
  - Chord inference from notes
  - Metadata extraction
  - Structure extraction
- [ ] ⏳ **Integration Tests**: NOT YET IMPLEMENTED
  - Real MusicXML file parsing
  - Real MIDI file parsing
  - Comparison with expected outputs
- [ ] ⏳ **Regression Tests**: NOT YET IMPLEMENTED
  - Existing analysis pipeline unaffected
  - No performance degradation
  - All existing tests still pass

**Testing Requirements (To Complete)**:
1. Create `tests/integrations/test_music21_integration.py`
2. Add real test files: `tests/data/test_files/*.{xml,mid}`
3. Test end-to-end: file → adapter → analysis → results
4. Verify no regressions in existing test suite

---

### Iteration 1.2: Music21OutputFormatter (NEXT)

**Features to Deliver**:
- [ ] Generate annotated MusicXML from analysis results
- [ ] Add Roman numeral annotations to scores
- [ ] Add chord symbol annotations
- [ ] Add key signature markers
- [ ] Preserve original score structure and metadata
- [ ] Export to multiple formats (MusicXML, PDF via MuseScore)

**Acceptance Criteria**:
- [ ] Formatter can annotate a parsed score with analysis results
- [ ] Roman numerals appear correctly positioned in output
- [ ] Chord symbols are added if not present in original
- [ ] Original score structure preserved (measures, parts, tempo)
- [ ] Output can be opened in MuseScore/Finale
- [ ] No data loss between input → analyze → annotate → output

**Testing Requirements**:
1. **Unit Tests** (15-20 tests):
   - Test annotation placement logic
   - Test Roman numeral formatting
   - Test chord symbol addition
   - Test metadata preservation
   - Test error handling
2. **Integration Tests** (5-10 tests):
   - Parse → Analyze → Annotate → Verify output
   - Test with various file types (different instruments, keys)
   - Verify output opens in music21.show()
3. **Regression Tests**:
   - Ensure formatter doesn't affect adapter
   - All Phase 1.1 tests still pass

---

### Iteration 1.3: API Integration

**Features to Deliver**:
- [ ] Add `analyze_score()` to `api/analysis.py`
- [ ] Support file path and music21 Score object inputs
- [ ] Return annotated score object
- [ ] Update CLI to accept file inputs
- [ ] Add example scripts showing usage

**Acceptance Criteria**:
- [ ] `analyze_score(file_path)` works with MusicXML/MIDI
- [ ] `analyze_score(score_object)` works with music21 objects
- [ ] Returns dict with analysis + annotated score
- [ ] CLI can analyze files: `harmonic-analysis analyze file.xml`
- [ ] Documentation includes file input examples

**Testing Requirements**:
1. **Unit Tests** (10-15 tests):
   - Test API function with various inputs
   - Test error handling (invalid files, unsupported formats)
   - Test both sync and async variants
2. **Integration Tests** (8-12 tests):
   - End-to-end: file → API → annotated output
   - CLI integration tests
   - Test with different musical styles
3. **Regression Tests**:
   - All existing API functions still work
   - Existing CLI commands unchanged
   - No breaking changes to public API

---

### Iteration 1.4: Documentation & Dependencies

**Features to Deliver**:
- [ ] Add music21 to `pyproject.toml` as optional dependency
- [ ] Update README with file input examples
- [ ] Add tutorial: "Analyzing MusicXML Files"
- [ ] Update API documentation
- [ ] Add troubleshooting guide for music21 installation

**Acceptance Criteria**:
- [ ] `pip install harmonic-analysis[music21]` installs music21
- [ ] README shows file input example in quick start
- [ ] Tutorial walks through complete file analysis workflow
- [ ] API docs include all new functions
- [ ] Installation guide covers common issues (MuseScore, etc.)

**Testing Requirements**:
1. **Integration Tests** (5-8 tests):
   - Test installation with optional dependencies
   - Verify examples in docs actually work
   - Test without music21 (graceful degradation)
2. **Documentation Tests**:
   - All code examples execute successfully
   - Links to external resources valid
   - Screenshots current

---

## Phase 2: Structural Analysis (3-4 weeks)

### Iteration 2.1: ScoreAnalyzer

**Features to Deliver**:
- [ ] Implement `ScoreAnalyzer` class
- [ ] Phrase detection and segmentation
- [ ] Cadence point identification
- [ ] Section detection (intro, verse, chorus, etc.)
- [ ] Formal analysis (sonata, binary, etc.)

**Acceptance Criteria**:
- [ ] Analyzer detects phrase boundaries accurately
- [ ] Cadence points identified at >80% accuracy
- [ ] Section markers placed correctly
- [ ] Works with various musical forms
- [ ] Integrates with existing pattern engine

**Testing Requirements**:
1. **Unit Tests** (20-25 tests):
   - Phrase boundary detection logic
   - Cadence identification algorithms
   - Section detection heuristics
   - Edge cases and error handling
2. **Integration Tests** (10-15 tests):
   - Real scores with known phrase structure
   - Comparison with music theory analysis
   - Cross-validation with pattern engine results
3. **Regression Tests**:
   - Phase 1 functionality unaffected
   - Performance benchmarks maintained

---

### Iteration 2.2: ScoreAnnotator

**Features to Deliver**:
- [ ] Implement `ScoreAnnotator` class
- [ ] Add phrase brackets to scores
- [ ] Add cadence markers
- [ ] Add section labels
- [ ] Add formal analysis annotations
- [ ] Support multiple annotation layers

**Acceptance Criteria**:
- [ ] Phrase brackets appear visually clear
- [ ] Cadence markers positioned correctly
- [ ] Section labels readable and properly placed
- [ ] Multiple annotation layers don't overlap
- [ ] Output opens in notation software

**Testing Requirements**:
1. **Unit Tests** (15-20 tests):
   - Annotation placement algorithms
   - Visual layout logic
   - Layer management
   - Text formatting
2. **Integration Tests** (8-12 tests):
   - Complete workflow: analyze → annotate → verify
   - Visual inspection tests (screenshot comparison)
   - Compatibility with MuseScore/Finale
3. **Regression Tests**:
   - Phase 1 & 2.1 functionality preserved
   - No performance degradation

---

## Phase 3: Advanced Features (4-6 weeks)

### Iteration 3.1: Voice Leading Analysis

**Features to Deliver**:
- [ ] Implement voice leading tracker
- [ ] Detect parallel fifths/octaves
- [ ] Identify voice crossing
- [ ] Track individual voice lines
- [ ] Annotate voice leading issues

**Acceptance Criteria**:
- [ ] Parallel fifths detected at >90% accuracy
- [ ] Voice crossing identified correctly
- [ ] Individual voices tracked through score
- [ ] Annotations highlight issues clearly
- [ ] Works with 2-8 voice textures

**Testing Requirements**:
1. **Unit Tests** (25-30 tests):
   - Voice tracking algorithms
   - Parallel motion detection
   - Voice crossing logic
   - Multi-voice handling
2. **Integration Tests** (12-15 tests):
   - Real scores with known voice leading
   - Comparison with theory textbook examples
   - Various textures (homophonic, polyphonic)
3. **Regression Tests**:
   - All Phase 1-2 features working
   - No impact on chord analysis accuracy

---

### Iteration 3.2: Pattern Visualization

**Features to Deliver**:
- [ ] Add pattern brackets to scores
- [ ] Color-code pattern types
- [ ] Add pattern labels (sequence, cadential 6-4, etc.)
- [ ] Support overlapping patterns
- [ ] Legend/key for pattern colors

**Acceptance Criteria**:
- [ ] Pattern brackets clear and readable
- [ ] Color coding consistent and meaningful
- [ ] Overlapping patterns visually distinct
- [ ] Legend explains all colors/symbols
- [ ] Works with complex scores

**Testing Requirements**:
1. **Unit Tests** (15-20 tests):
   - Bracket drawing logic
   - Color assignment algorithms
   - Legend generation
   - Overlap resolution
2. **Integration Tests** (10-12 tests):
   - Real scores with multiple patterns
   - Visual clarity validation
   - Color blind accessibility
3. **Regression Tests**:
   - All previous features functional
   - Performance within acceptable limits

---

## Phase 4: Polish (2-3 weeks)

### Iteration 4.1: Performance Optimization

**Features to Deliver**:
- [ ] Profile and optimize slow operations
- [ ] Add caching for repeated analyses
- [ ] Parallelize where possible
- [ ] Reduce memory footprint
- [ ] Add progress indicators

**Acceptance Criteria**:
- [ ] Large scores (100+ measures) analyze in <10 seconds
- [ ] Memory usage <500MB for typical scores
- [ ] No memory leaks during repeated analyses
- [ ] Progress feedback for long operations
- [ ] Caching improves repeat analysis by >50%

**Testing Requirements**:
1. **Performance Tests** (10-15 tests):
   - Benchmark suite with various score sizes
   - Memory profiling tests
   - Cache effectiveness tests
   - Concurrency/thread safety tests
2. **Regression Tests**:
   - All functionality unchanged
   - Accuracy metrics maintained
   - No new bugs introduced

---

### Iteration 4.2: Final Polish & Documentation

**Features to Deliver**:
- [ ] Comprehensive tutorial series
- [ ] Video demonstrations
- [ ] API reference complete
- [ ] Example score library
- [ ] Troubleshooting guide expanded

**Acceptance Criteria**:
- [ ] 5+ complete tutorials published
- [ ] Video walkthrough of key features
- [ ] Every public function documented
- [ ] 20+ example scores with expected outputs
- [ ] Common issues have documented solutions

**Testing Requirements**:
1. **Documentation Tests**:
   - All examples execute without errors
   - Code snippets up to date
   - Links valid and current
2. **User Acceptance Tests**:
   - Beta users can complete tasks from docs
   - Example scores produce expected results
   - Installation process smooth

---

## Regression Test Suite

**Core Regression Tests (Run after every iteration)**:

### Existing Functionality Tests
1. **Pattern Analysis** (150+ tests)
   - All pattern tests still pass
   - No degradation in accuracy metrics
   - Performance within baseline

2. **Chord Analysis** (100+ tests)
   - Chord parsing unchanged
   - Roman numeral generation correct
   - Inversion detection working

3. **Modal Analysis** (80+ tests)
   - Modal detection accuracy maintained
   - 46 scale modes still supported
   - Parent key detection working

4. **API Compatibility** (50+ tests)
   - All public APIs backward compatible
   - No breaking changes
   - Deprecations properly warned

### Integration Regression Tests
1. **Demo Application**
   - Gradio interface functional
   - All example progressions work
   - Educational content displays

2. **CLI Tools**
   - All commands execute
   - Output format unchanged
   - Error messages clear

3. **Performance Baselines**
   - Analysis speed within 10% of baseline
   - Memory usage within acceptable limits
   - No memory leaks

---

## Test Execution Strategy

### Per-Iteration Testing
1. **During Development**
   - Write unit tests alongside features (TDD)
   - Run tests frequently (`pytest -x`)
   - Maintain >80% code coverage

2. **Before Commit**
   - Run full unit test suite
   - Run pre-commit hooks (black, isort, flake8, mypy)
   - Ensure all tests pass

3. **Before Merge**
   - Run full regression suite
   - Run integration tests
   - Perform manual acceptance testing
   - Update documentation

### Continuous Integration
- GitHub Actions runs full suite on push
- Coverage reports generated
- Performance benchmarks tracked
- Documentation builds validated

---

## Success Metrics

### Phase 1 Success Criteria
- [x] Music21Adapter: 20+ unit tests, 100% pass rate ✅
- [ ] Integration tests: 10+ tests, >90% pass rate
- [ ] Regression tests: All existing tests pass
- [ ] Code coverage: >80% for new code
- [ ] Documentation: Complete with examples

### Overall Project Success Criteria
- [ ] All 4 phases completed
- [ ] 200+ total tests (unit + integration + regression)
- [ ] 100% backward compatibility maintained
- [ ] Performance within 10% of baseline
- [ ] User documentation complete
- [ ] Beta users can successfully use features

---

## Current Status

**Completed**:
- ✅ Phase 1.1: Music21Adapter (20 unit tests passing)

**In Progress**:
- ⏳ Phase 1.1: Integration & regression tests

**Next**:
- 📋 Phase 1.2: Music21OutputFormatter
- 📋 Phase 1.3: API Integration
- 📋 Phase 1.4: Documentation & Dependencies

**Blockers**: None

**Risks**:
- music21 dependency size (50MB+) - mitigated by optional install
- MuseScore requirement for PDF export - documented in troubleshooting
- Performance with large scores - will address in Phase 4
