# Harmonic Analysis Library Demo

A completely independent React frontend demo that showcases the harmonic analysis library capabilities.

## Quick Start

```bash
# Setup and run demo (from project root)
cd demo
./setup.sh
npm start
```

Opens http://localhost:3010 with a comprehensive demo showing ALL library parameters.

## What This Demo Shows

### Complete Library Output
- **Primary Analysis**: Type, confidence, analysis text, Roman numerals, key, mode
- **Reasoning & Theory**: Full analytical reasoning and theoretical basis
- **Evidence Framework**: All evidence types with musical basis and strength
- **Alternative Interpretations**: Multiple analytical perspectives with relationships
- **Analysis Metadata**: Performance metrics, thresholds, pedagogical levels
- **Raw Debug Data**: Complete JSON output for developers

### Interactive Features
- **Real-time Analysis**: Updates as you type chord progressions
- **Tab Cycling**: Press Tab to cycle through example progressions
- **Keyboard-Only Interface**: No mouse required
- **Educational Display**: Shows how the analysis reasoning works
- **Comprehensive Coverage**: Every library parameter is visible

### Example Progressions
- **`C Am F G`** - Classic functional harmony (I-vi-IV-V)
- **`G F G`** - Modal analysis (G Mixolydian) with alternatives
- **`Dm G C`** - Strong functional (ii-V-I)
- **`C Am Dm G C`** - Extended functional progression

## Architecture

### Complete Independence
- **Self-contained**: All dependencies isolated in demo/
- **Library Import**: Uses the main library as external dependency
- **No Bleeding**: Zero impact on main project if demo/ is deleted
- **Separate Dependencies**: Own package.json and requirements.txt

### Components
- **Frontend**: React app with comprehensive parameter display
- **Backend**: FastAPI wrapper that imports the main library
- **Setup**: One-command setup script handles everything
- **Fallback**: Works with demo data when backend unavailable

## Files Structure

```
demo/
├── README.md                    # This file
├── setup-basic.sh               # Quick demo setup (30 seconds)
├── setup-full-with-tests.sh     # Full setup with E2E tests (2-3 minutes)
├── run-demo.sh                  # Demo launch script
├── package.json                 # Demo scripts
├── frontend/                    # React frontend
│   ├── package.json            # Frontend dependencies
│   ├── src/
│   │   ├── App.js              # Main demo component
│   │   ├── index.js            # React entry
│   │   └── index.css           # Complete styling
│   └── public/index.html       # HTML shell
├── backend/                     # FastAPI backend
│   ├── main.py                 # API server
│   └── requirements.txt        # Backend dependencies
└── e2e-tests/                   # End-to-end test suite
    ├── package.json            # E2E test dependencies
    ├── playwright.config.ts     # Playwright configuration
    ├── tests/                  # Comprehensive test suite
    └── test-results/           # Test execution reports
```

## Running the Demo

**Choose your setup based on your needs:**

| Setup Script | Time | Purpose | Includes |
|--------------|------|---------|----------|
| `setup-basic.sh` | ~30 seconds | Quick demo showcase | React frontend + FastAPI backend |
| `setup-full-with-tests.sh` | ~2-3 minutes | Development & testing | Everything + 427 E2E tests + Playwright |

### Option 1: Quick Basic Demo (Fast - 30 seconds)
```bash
cd demo
./setup-basic.sh     # Quick setup - just working demo
npm start           # Starts both frontend and backend
```

### Option 2: Full Demo with E2E Tests (Comprehensive - 2-3 minutes)
```bash
cd demo
./setup-full-with-tests.sh  # Full setup including 427 E2E tests
./run-demo.sh              # Starts both frontend and backend
```

### Option 3: Frontend Only
```bash
cd demo/frontend
npm install
npm start       # Uses demo data, no backend needed
```

### Option 4: Manual Setup
```bash
cd demo

# Basic setup (same as setup-basic.sh)
pip install -e ..                    # Install main library
pip install -r backend/requirements.txt  # Backend dependencies
cd frontend && npm install && cd ..   # Frontend dependencies
npm install                          # Demo orchestration tools

# For E2E tests (additional step from setup-full-with-tests.sh)
cd e2e-tests && npm install && npx playwright install && cd ..

# Start demo manually
npm start                            # Or use ./run-demo.sh
```

## Design Philosophy

This demo prioritizes **complete functionality demonstration** over visual polish:

- **Shows Everything**: Every library parameter visible
- **Educational**: Clear evidence and reasoning display
- **Keyboard-First**: Tab navigation, no mouse required
- **Real-time**: Immediate analysis feedback
- **Developer-Friendly**: Raw JSON debug output
- **Basic Styling**: Fast development, no fancy UI libraries

Perfect for:
- Library evaluation and testing
- Understanding analysis capabilities
- Developer integration examples
- Educational demonstrations
- Quick capability assessment

## E2E Testing Suite

The demo now includes a comprehensive end-to-end testing suite with **427 test cases** validating:

- **Chord Progression Analysis** - Functional, modal, and chromatic progressions
- **Scale Detection** - All 7 modes with characteristic interval detection
- **Melody Analysis** - Tonal center detection and contour analysis
- **Multi-layer Analysis** - Layered harmonic analysis validation
- **UI Interactions** - Complete user interface validation
- **Cross-browser Testing** - Chrome, Firefox, Safari compatibility

### Running E2E Tests
```bash
cd demo/e2e-tests
npm install              # Install test dependencies
npm run test:e2e         # Run full test suite
npm run test:e2e:headed  # Run with browser visible (debugging)
```

### Test Categories
- **Library Results Validation** - Validates analysis accuracy against unit tests
- **Chord Progression Validation** - Tests various harmonic progressions
- **Scale Analysis Validation** - Tests all modal scale detection
- **Melody Analysis Validation** - Tests melodic analysis capabilities
- **UI Interactions Validation** - Tests complete user interface

## Independence Guarantee

This entire `demo/` folder can be **deleted without any impact** on the main harmonic analysis library. It's completely self-contained with its own dependencies and setup.
