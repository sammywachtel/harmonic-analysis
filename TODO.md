# Development TODO List

## Overview

This file tracks development tasks, feature requests, and technical debt for the harmonic-analysis library.

**Status Legend**:
- 🔴 **Not Started** - Task not yet begun
- 🟡 **In Progress** - Currently being worked on
- 🟢 **Completed** - Task finished
- 🔵 **On Hold** - Paused/waiting for dependencies
- ⚪ **Planned** - Scheduled for future iteration

---

## Current Iteration: Production Ready Status

### 🟢 Pattern Engine (Iterations 1-15) - COMPLETED

**Status**: Production ready with all major features implemented

**Achievements**:
- ✅ 36+ comprehensive patterns across harmonic, modal, chromatic tracks
- ✅ Unified pattern engine architecture replacing legacy analyzers
- ✅ Quality-gated calibration with identity fallback
- ✅ Evidence aggregation and conflict resolution
- ✅ 100% test coverage (76 pattern engine tests, 451+ total tests passing)
- ✅ Modal accuracy 56%+, Functional accuracy 50%+ (exceeds targets)
- ✅ Complete migration with full backward compatibility

---

## High Priority (Next Iteration)

### 🟡 music21 Integration - Hybrid Architecture

**Priority**: HIGH
**Effort**: Medium (2-3 weeks Phase 1)
**Impact**: Very High
**Status**: Planning complete, ready to implement

**Phase 1: Foundation** (2-3 weeks)
- [ ] Create `src/harmonic_analysis/integrations/` module structure
- [ ] Implement `Music21Adapter` class
  - [ ] `from_musicxml()` - Parse MusicXML files
  - [ ] `from_midi()` - Parse MIDI files
  - [ ] `_chord_to_symbol()` - Convert music21 Chord → string
  - [ ] `_extract_structure()` - Extract sections, measures, parts
- [ ] Implement `Music21OutputFormatter` class
  - [ ] `to_annotated_score()` - Create annotated music21 Score
  - [ ] `_add_roman_numerals()` - Add roman numerals as lyrics
  - [ ] `_add_cadence_markers()` - Add cadence text expressions
- [ ] Update `api/analysis.py` with `analyze_score()` function
- [ ] Add integration tests for MusicXML/MIDI parsing
- [ ] Update documentation with file input examples
- [ ] Add to optional dependencies in `pyproject.toml`

**Phase 2: Structural Analysis** (3-4 weeks)
- [ ] Implement `ScoreAnalyzer` class
  - [ ] `_extract_metadata()` - Title, composer, tempo, time signature
  - [ ] `_analyze_structure()` - Sections, repeats, form
  - [ ] `_detect_sections()` - Rehearsal marks, section boundaries
  - [ ] `_extract_harmonic_content()` - Chords, bass line
  - [ ] `_analyze_voice_leading()` - Voice motion between chords
- [ ] Implement `ScoreAnnotator` class
  - [ ] `create_analysis_score()` - Complete annotation pipeline
  - [ ] `_add_section_labels()` - Section boundary markers
  - [ ] `_highlight_chromatic()` - Color-code chromatic elements
  - [ ] `_add_pattern_brackets()` - Visual pattern spans
  - [ ] `_add_analysis_summary()` - Summary text box
- [ ] Implement `ScoreVisualizer` pipeline
- [ ] Create example Jupyter notebooks
- [ ] Add documentation with workflow examples

**Phase 3: Advanced Features** (4-6 weeks)
- [ ] Enhanced voice leading visualization
- [ ] Pattern bracket spanners
- [ ] Multiple export formats (PDF, PNG, MusicXML)
- [ ] Color-coding by harmonic function
- [ ] Performance optimization

**Phase 4: Polish** (2-3 weeks)
- [ ] Comprehensive documentation
- [ ] Tutorial videos/guides
- [ ] Example gallery
- [ ] User testing and feedback

**Reference**: See `.local_docs/music21_integration_strategy.md` for complete architecture

---

## Medium Priority

### 🔴 Modal Contextless Analysis

**Priority**: MEDIUM
**Effort**: High (4-6 weeks)
**Impact**: Medium
**Status**: Not started (blocked by prioritizing music21 integration)

**Goal**: Enable modal analysis without explicit parent key context

**Tasks**:
- [ ] Design automatic parent key inference algorithm
- [ ] Implement contextless modal detection
  - [ ] Detect characteristic modal intervals from chord content
  - [ ] Infer parent key from harmonic patterns
  - [ ] Test with G-F-G → infer C major parent
- [ ] Add 168 contextless test cases
- [ ] Target: 50%+ success rate on contextless modal progressions

**Current Status**: 0% success rate (~168 failing test cases)

### 🔴 Additional Scale Mode Pattern Recognition

**Priority**: MEDIUM
**Effort**: Medium (3-4 weeks)
**Impact**: Medium
**Status**: Not started

**Goal**: Add mode-specific patterns for exotic modes (melodic minor, harmonic minor, etc.)

**Tasks**:
- [ ] Add ~39 new mode-specific patterns to `patterns.json`
  - [ ] Melodic Minor modes (7 patterns): Altered, Lydian Dominant, etc.
  - [ ] Harmonic Minor modes (7 patterns): Phrygian Dominant, Hungarian Minor, etc.
  - [ ] Harmonic Major modes (7 patterns)
  - [ ] Double Harmonic modes (7 patterns)
  - [ ] Pentatonic patterns (5 patterns)
  - [ ] Blues patterns (6 patterns)
- [ ] Enhance pattern matcher constraints
  - [ ] `mode_any_of` constraint for specific modes
  - [ ] `characteristic_interval` constraint (♭2, ♯4, ♭6, etc.)
- [ ] Pass scale system context to pattern engine
- [ ] Add pattern documentation for each mode family

**Reference**: See `.local_docs/scale_mode_integration_status.md`

**Note**: Infrastructure is complete (all 46 modes detected in scale/melody analysis), this task adds pattern-level recognition for chord progressions.

---

## Low Priority / Future Enhancements

### ⚪ Educational Content System Enhancement

**Priority**: LOW
**Effort**: Medium
**Impact**: Low
**Status**: Planned

**Tasks**:
- [ ] Expand knowledge base with more patterns
- [ ] Add interactive examples
- [ ] Create learning pathways by pedagogical level

### ⚪ Jazz Harmony Patterns

**Priority**: LOW
**Effort**: High
**Impact**: Medium
**Status**: Planned

**Tasks**:
- [ ] Add tritone substitution patterns
- [ ] Add altered dominant patterns
- [ ] Add modal interchange patterns
- [ ] Add jazz-specific cadences

### ⚪ Voice Leading Quality Scoring

**Priority**: LOW
**Effort**: High
**Impact**: Low
**Status**: Planned

**Tasks**:
- [ ] Implement voice leading analyzer
- [ ] Factor voice leading quality into confidence scores
- [ ] Add voice leading pattern detection

### ⚪ Machine Learning Integration

**Priority**: LOW
**Effort**: Very High
**Impact**: Medium
**Status**: Research phase

**Tasks**:
- [ ] Design user feedback collection system
- [ ] Implement confidence refinement based on feedback
- [ ] Create training pipeline

---

## Technical Debt

### 🔴 Code Quality Improvements

**Priority**: MEDIUM
**Effort**: Low (ongoing)
**Impact**: Medium
**Status**: Ongoing

**Current Issues**:
- [ ] Reduce line length violations (41 remaining)
- [ ] Clean up unused imports (~12 remaining)
- [ ] Address remaining flake8 warnings
- [ ] Improve type hints coverage

**Progress**: 65% reduction in flake8 errors achieved (from 43+ to ~12)

### 🔴 Documentation Updates

**Priority**: MEDIUM
**Effort**: Medium
**Impact**: High
**Status**: Ongoing

**Tasks**:
- [ ] Complete migration to Diátaxis framework
  - [ ] Migrate API_GUIDE.md → API Reference
  - [ ] Migrate ARCHITECTURE.md → Architecture Explanation
  - [ ] Migrate TROUBLESHOOTING.md → Troubleshooting How-To
  - [ ] Migrate CONFIDENCE_CALIBRATION.md → Theory Explanation
- [ ] Update all code examples to use latest API
- [ ] Add more tutorial content
- [ ] Create video walkthroughs

---

## Completed (Recent)

### 🟢 Pattern Engine Redesign (Iterations 1-15)

**Completed**: 2025-10-05
**Duration**: 15 iterations over ~3 months
**Impact**: Transformational

**Major Achievements**:
- ✅ Unified pattern engine replacing functional/modal split
- ✅ 36+ comprehensive patterns
- ✅ Quality-gated calibration system
- ✅ Evidence aggregation and conflict resolution
- ✅ 100% test coverage (451+ tests passing)
- ✅ Production-ready status achieved

### 🟢 Scale/Melody Analysis Enhancement (Iteration 15)

**Completed**: 2025-10-04
**Impact**: High

**Achievements**:
- ✅ Rich scale summaries with mode detection
- ✅ Comprehensive melody summaries with contour analysis
- ✅ All 46 modes fully integrated and detected
- ✅ Educational context for modal characteristics

### 🟢 Confidence Calibration System

**Completed**: 2025-09-28
**Impact**: High

**Achievements**:
- ✅ Theoretically sound cadence-specific scoring
- ✅ Quality gates prevent degradation
- ✅ Identity fallback for poor data quality
- ✅ Modal accuracy 56%+, Functional accuracy 50%+

---

## Archive / Backlog Ideas

### Research Topics

- [ ] Cultural harmony systems (non-Western)
- [ ] Microtonal harmony analysis
- [ ] Algorithmic composition suggestions
- [ ] Real-time MIDI analysis
- [ ] Audio-to-harmony extraction (via audio ML models)

### Infrastructure

- [ ] Performance benchmarking suite
- [ ] Profiling and optimization
- [ ] Caching layer for repeated analyses
- [ ] Async batch processing

### Developer Experience

- [ ] CLI tool for quick analysis
- [ ] VS Code extension
- [ ] Web playground
- [ ] Docker container for reproducibility

---

## Notes

### Development Workflow

1. **Check this TODO.md** for current priorities
2. **Create iteration log** in `.local_docs/iteration_logs/` when starting major work
3. **Update status** as tasks progress
4. **Mark completed** and move to "Completed" section
5. **Document** in DEVELOPMENT.md when releasing features

### Task Estimation Guide

- **Low Effort**: 1-3 days
- **Medium Effort**: 1-2 weeks
- **High Effort**: 3-6 weeks
- **Very High Effort**: 6+ weeks

### Priority Guidelines

- **HIGH**: Blocks other features or critical user need
- **MEDIUM**: Important but not blocking
- **LOW**: Nice to have, quality of life improvement

---

**Last Updated**: 2025-10-05
**Next Review**: After music21 integration Phase 1 completion
