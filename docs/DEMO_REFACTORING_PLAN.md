# Demo Refactoring Plan: Separate Business Logic from Display Logic

## Current Problem

**File:** `demo/full_library_demo.py`
**Current Size:** 4,999 lines
**Issue:** Single monolithic file mixing chord detection, file processing, HTML generation, analysis orchestration, API routes, and UI code.

## Goals

1. **Separation of Concerns** - Business logic separate from display logic
2. **Maintainability** - Smaller, focused modules easier to understand and modify
3. **Testability** - Isolated business logic easier to unit test
4. **Reusability** - Shared code can be imported across demo, API, and tests
5. **Clarity** - Clear boundaries between music processing and UI rendering

## Proposed Module Structure

```
demo/
├── full_library_demo.py          # Main entry point (~150 lines)
├── lib/
│   ├── __init__.py
│   ├── chord_detection.py         # Chord recognition logic
│   ├── music_file_processing.py   # MIDI/MusicXML processing with music21
│   ├── key_conversion.py          # Key signature conversions
│   ├── analysis_orchestration.py  # Analysis pipeline coordination
│   └── constants.py               # Shared constants, regex patterns
├── ui/
│   ├── __init__.py
│   ├── html_formatters.py         # HTML generation for analysis display
│   ├── gradio_components.py       # Gradio UI component definitions
│   └── gradio_handlers.py         # Event handler wrappers
└── api/
    ├── __init__.py
    └── fastapi_routes.py          # FastAPI route definitions
```

## Detailed Module Breakdown

### 1. **`demo/lib/chord_detection.py`** (~500 lines)

**Purpose:** Pure music theory - chord recognition from pitches

**Functions to Move:**
- `detect_chord_from_pitches()` - Main chord detection algorithm
- `_calculate_confidence()` - Confidence scoring
- `detect_chord_with_music21()` - music21-based detection fallback
- `CHORD_TEMPLATES` - Chord interval definitions
- `NOTE_NAMES_FOR_DETECTION` - Note name constants

**Why Separate:**
- Pure music theory logic with no UI dependencies
- Highly reusable across demo, API, and tests
- Can be unit tested in isolation
- May eventually move to main library

---

### 2. **`demo/lib/music_file_processing.py`** (~1200 lines)

**Purpose:** File upload processing, chordify, tempo detection, windowing

**Functions to Move:**
- `analyze_uploaded_file()` - Main file processing pipeline
- `detect_tempo_from_score()` - Tempo detection from music21 Score
- `calculate_initial_window()` - Tempo-based window size calculation
- Chordify logic, measure tracking, chord labeling
- MusicXML/PNG export generation

**Dependencies:**
- `chord_detection.py` for chord symbols
- `key_conversion.py` for key hint processing
- `analysis_orchestration.py` for running analysis

**Why Separate:**
- Complex file processing logic independent of display
- Can be tested with sample MIDI/MusicXML files
- Reusable for batch processing or API endpoints

---

### 3. **`demo/lib/key_conversion.py`** (~150 lines)

**Purpose:** Key signature interpretation and conversion

**Functions to Move:**
- `convert_key_signature_to_mode()` - Sharps/flats to major/minor keys
- `parse_key_signature_from_hint()` - Extract sharps/flats from hint string
- Major and minor key mapping dictionaries

**Why Separate:**
- Pure music theory logic
- No UI dependencies
- Highly testable (well-defined input/output)
- May be useful in main library

---

### 4. **`demo/lib/analysis_orchestration.py`** (~200 lines)

**Purpose:** Coordinate analysis pipeline, parse inputs, call service

**Functions to Move:**
- `run_analysis_sync()` - Synchronous analysis wrapper
- `parse_csv()` - CSV input parsing
- `parse_melody()` - Melody input parsing
- `parse_scales()` - Scale input parsing
- `validate_list()` - Input validation
- `validate_exclusive_input()` - Mutual exclusivity checks
- `resolve_key_input()` - Key hint resolution
- `get_service()` - Service singleton getter

**Why Separate:**
- Orchestration logic separate from UI and display
- Reusable for API endpoints
- Testable with mock inputs

---

### 5. **`demo/lib/constants.py`** (~50 lines)

**Purpose:** Shared constants across demo modules

**Constants to Move:**
- `DEFAULT_PROFILE`
- `VALID_PROFILES`
- `ROMAN_RE` - Roman numeral regex
- `NOTE_RE` - Note name regex
- Profile descriptions

**Why Separate:**
- Single source of truth for constants
- Prevents circular imports
- Easy to modify defaults

---

### 6. **`demo/ui/html_formatters.py`** (~1400 lines)

**Purpose:** Generate HTML for displaying analysis results in Gradio

**Functions to Move:**
- `format_file_analysis_html()` - Structured table for file analysis
- `format_analysis_html()` - Envelope-based analysis display
- `generate_enhanced_evidence_cards()` - Evidence card HTML
- `generate_chord_progression_display()` - Chord progression display
- `format_evidence_html()` - Evidence list formatting
- `format_confidence_badge()` - Confidence badge HTML
- `get_chord_function_description()` - Roman numeral descriptions
- `generate_code_snippet()` - Python code snippet generation
- `summarize_envelope()` - Envelope summary formatting
- `generate_osmd_html_file()` - Standalone OSMD HTML
- `generate_osmd_viewer()` - Embedded OSMD viewer

**Why Separate:**
- Pure display logic with no business logic
- Makes HTML templates easy to find and modify
- Can be replaced with Jinja2 templates in future
- No analysis logic mixed in

---

### 7. **`demo/ui/gradio_components.py`** (~400 lines)

**Purpose:** Define all Gradio UI components (inputs, outputs, layouts)

**Components to Move:**
- All `gr.Textbox()`, `gr.Radio()`, `gr.Checkbox()` definitions
- Component layout with `gr.Row()`, `gr.Column()`, `gr.Accordion()`
- Component IDs and labels
- Help text and info messages

**Why Separate:**
- Clear separation of UI structure from business logic
- Easy to modify layouts without touching logic
- Can be refactored to use Gradio Blocks composition

---

### 8. **`demo/ui/gradio_handlers.py`** (~600 lines)

**Purpose:** Event handler wrappers that connect UI to business logic

**Functions to Move:**
- `process_uploaded_file_wrapper()` - File upload handler
- `handle_progression_analysis()` - Progression analysis handler
- `handle_auto_window_toggle()` - Window size toggle
- All `.click()`, `.change()`, `.submit()` event handlers

**Dependencies:**
- `music_file_processing.py` for file processing
- `analysis_orchestration.py` for analysis
- `html_formatters.py` for display

**Why Separate:**
- Clean adapter layer between UI and business logic
- Event handlers isolated from Gradio component definitions
- Easy to debug and test

---

### 9. **`demo/api/fastapi_routes.py`** (~600 lines)

**Purpose:** FastAPI route definitions for REST API

**Functions to Move:**
- `create_api_app()` - FastAPI app factory
- All `@app.post()` route handlers
- Request/response models
- API documentation strings

**Dependencies:**
- `analysis_orchestration.py` for analysis logic
- `music_file_processing.py` for file uploads

**Why Separate:**
- API completely independent of Gradio UI
- Can be deployed separately as REST service
- Clear API contract with request/response models

---

### 10. **`demo/full_library_demo.py`** (~150 lines)

**Purpose:** Main entry point that ties everything together

**Remaining Content:**
- Imports from new modules
- `main()` function - argument parsing and launch
- CLI argument definitions
- Minimal setup code

**Why Small:**
- Just a thin orchestration layer
- Easy to understand flow at a glance
- All complexity delegated to focused modules

---

## Migration Strategy

### Phase 1: Create Module Structure (Safe Setup)
1. Create `demo/lib/` and `demo/ui/` directories
2. Create empty `__init__.py` files
3. Create `constants.py` with shared constants
4. Verify imports work

### Phase 2: Extract Pure Logic (No UI Dependencies)
1. Move `chord_detection.py` functions
2. Move `key_conversion.py` functions
3. Update imports in main file
4. Test chord detection still works

### Phase 3: Extract Business Logic (UI-Independent)
1. Move `music_file_processing.py` functions
2. Move `analysis_orchestration.py` functions
3. Update imports and dependencies
4. Test file processing pipeline

### Phase 4: Extract Display Logic
1. Move `html_formatters.py` functions
2. Update imports in handlers
3. Test HTML generation

### Phase 5: Extract UI Components
1. Move `gradio_components.py` definitions
2. Move `gradio_handlers.py` event handlers
3. Refactor `launch_gradio_demo()` to use imports
4. Test full UI workflow

### Phase 6: Extract API
1. Move `fastapi_routes.py` code
2. Update `main()` to import API factory
3. Test API endpoints

### Phase 7: Cleanup and Testing
1. Remove all moved code from `full_library_demo.py`
2. Verify `main()` is ~150 lines
3. Run full integration tests
4. Update demo documentation

---

## Testing Strategy

After each phase:
1. **Import Test** - Verify no import errors
2. **Unit Test** - Test extracted functions in isolation
3. **Integration Test** - Run demo and verify workflow
4. **Regression Test** - Compare output before/after refactoring

---

## Benefits After Refactoring

### 1. **Maintainability**
- ~500 lines per module vs 5000 lines
- Clear responsibility for each module
- Easy to locate and modify specific functionality

### 2. **Testability**
- Pure functions can be unit tested in isolation
- Mock dependencies easily in tests
- Business logic tested without UI

### 3. **Reusability**
- `chord_detection.py` can be used in tests, API, batch processing
- `music_file_processing.py` can power CLI tools
- `html_formatters.py` can be replaced with templates

### 4. **Collaboration**
- Multiple developers can work on different modules
- Clear module boundaries reduce merge conflicts
- Easier onboarding with focused modules

### 5. **Future Enhancements**
- Swap Gradio for Streamlit without touching business logic
- Add CLI interface reusing business logic
- Export analysis orchestration to main library
- Replace HTML formatters with Jinja2 templates

---

## Implementation Timeline

**Estimated Effort:** 6-8 hours total

- Phase 1: 30 minutes (setup)
- Phase 2: 1.5 hours (pure logic)
- Phase 3: 2 hours (business logic)
- Phase 4: 1.5 hours (display logic)
- Phase 5: 2 hours (UI components)
- Phase 6: 1 hour (API)
- Phase 7: 1 hour (cleanup + testing)

---

## Success Criteria

- [ ] `demo/full_library_demo.py` reduced from 4999 to ~150 lines
- [ ] All functions moved to appropriate modules
- [ ] No functionality broken (full integration test passes)
- [ ] All imports clean (no circular dependencies)
- [ ] Documentation updated to reflect new structure
- [ ] Can run `python demo/full_library_demo.py --gradio` successfully
- [ ] Can run `python demo/full_library_demo.py --api` successfully

---

## Notes

- **Backwards Compatibility:** Main entry point remains `demo/full_library_demo.py`
- **No Breaking Changes:** API and Gradio interfaces unchanged
- **Gradual Migration:** Can be done incrementally, testing after each phase
- **Documentation:** Update `docs/DEVELOPMENT.md` with new structure
