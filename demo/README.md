# Harmonic Analysis Demo

This directory contains demonstrations of the harmonic analysis library.

## Components

### 1. CLI Demo (`full_library_demo.py`)

Command-line demonstration of the library's Python API. This script shows how to use the harmonic analysis library directly in Python code.

**Purpose:** Demonstrates the **library API** (Python functions), not the REST API.

**Usage:**

```bash
# Analyze chord progression
python full_library_demo.py --chords "Dm G7 C" --key "C major"

# Analyze with Roman numerals
python full_library_demo.py --romans "ii V I" --key "C major"

# Analyze melody
python full_library_demo.py --melody "D E F G A" --key "C major"

# Analyze scale
python full_library_demo.py --scale "D E F G A B C" --key "D dorian"

# See all options
python full_library_demo.py --help
```

**Examples:**

```bash
# Classic ii-V-I progression
python full_library_demo.py --chords "Dm7 G7 Cmaj7" --key "C major" --profile classical

# Modal progression
python full_library_demo.py --chords "Dm C G Dm" --key "D dorian" --profile jazz

# Melody analysis
python full_library_demo.py --melody "C4 D4 E4 F4 G4 A4 B4 C5" --key "C major"
```

---

### 2. Web Demo (`backend/` + `frontend/`)

Full-stack web application with REST API backend and interactive React frontend.

**Purpose:** Demonstrates the **complete demo system** with web interface and REST API.

**Quick Start:**

```bash
# Start both backend and frontend with one command
./start_demo.sh

# Access the demo:
# - Backend API:  http://localhost:8000
# - API Docs:     http://localhost:8000/docs
# - Frontend UI:  http://localhost:5173

# Stop with Ctrl-C
```

**Manual Startup (for development):**

```bash
# Terminal 1 - Start backend
cd demo
uvicorn demo.backend.rest_api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Start frontend
cd demo/frontend
npm run dev
```

**Components:**

- **`backend/rest_api/`** - FastAPI server with analysis endpoints
  - `main.py` - FastAPI app factory with CORS config
  - `routes.py` - All API endpoints (analyze, scale, melody, file upload, glossary)
  - `models.py` - Pydantic request/response models
- **`frontend/`** - Interactive React web interface
  - Modern TypeScript + React + Tailwind CSS
  - Interactive chord/scale/melody input
  - Visual analysis display with pattern highlighting
- **`start_demo.sh`** - Launcher script for both servers
  - Starts backend on port 8000
  - Starts frontend on port 5173 (default Vite dev server)
  - Graceful shutdown with Ctrl-C

---

## Architecture Clarification

**Before the move_rest refactor:**
- `full_library_demo.py` had dual personality: CLI demo AND web server launcher (confusing!)
- Mixed library usage demonstration with web deployment concerns

**After the move_rest refactor:**
- **`full_library_demo.py`** → Pure CLI demo showing how to use the library in Python code
- **`start_demo.sh`** → Web demo launcher for the full-stack application
- **Clear separation:** Library API vs REST API

**Benefits:**
1. **Clarity:** Each demo has a single, clear purpose
2. **Simplicity:** Users wanting CLI examples don't see server code
3. **Consistency:** Web demo uses standard deployment patterns (dedicated launcher)
4. **Maintenance:** Easier to update either demo independently

---

## Demo Helper Modules

The `lib/` directory contains shared helper modules used by both demos:

- **`analysis_orchestration.py`** - Service initialization, input parsing, validation
- **`chord_detection.py`** - Chord detection utilities
- **`constants.py`** - Shared constants (profiles, validation patterns)
- **`music_file_processing.py`** - Music file upload and analysis

These modules demonstrate how to build reusable analysis utilities on top of the core library.

---

## Testing

The `tests/` directory contains demo-specific tests, including REST API integration tests.

```bash
# Run all demo tests
pytest demo/tests/

# Run only REST API tests
pytest demo/tests/api/test_rest_api.py -v
```

**Note:** Core library tests are in the top-level `tests/` directory. Demo tests validate the REST API and web interface, not the core analysis engines.

---

## Development Workflow

### Working on the CLI Demo

1. Edit `full_library_demo.py`
2. Test changes: `python full_library_demo.py --chords "C F G C" --key "C major"`
3. Verify help text: `python full_library_demo.py --help`

### Working on the Web Demo

1. Start both servers: `./start_demo.sh`
2. Edit backend code in `backend/rest_api/` (hot reload enabled)
3. Edit frontend code in `frontend/src/` (hot reload enabled)
4. Backend changes reload automatically (uvicorn --reload)
5. Frontend changes reload automatically (Vite HMR)

### Adding New API Endpoints

1. Add Pydantic models to `backend/rest_api/models.py`
2. Add route handler to `backend/rest_api/routes.py`
3. Test with curl or the API docs at http://localhost:8000/docs
4. Add frontend integration in `frontend/src/`

---

## Troubleshooting

### CLI Demo Issues

**Problem:** Import errors when running `full_library_demo.py`

**Solution:** Ensure you're running from the repository root and the library is installed:
```bash
cd /path/to/harmonic-analysis
pip install -e .
python demo/full_library_demo.py --help
```

---

### Web Demo Issues

**Problem:** Backend won't start - "No module named 'demo.backend'"

**Solution:** Run uvicorn from the repository root, not from the demo directory:
```bash
# From repository root:
cd /path/to/harmonic-analysis
uvicorn demo.backend.rest_api.main:app --reload
```

---

**Problem:** Frontend can't connect to backend - CORS errors

**Solution:** Ensure backend is running on port 8000 and frontend is configured correctly:
```bash
# Check backend is running:
curl http://localhost:8000/health

# Frontend API client should point to http://localhost:8000
# Check demo/frontend/src/api/client.ts
```

---

**Problem:** `start_demo.sh` script not found or permission denied

**Solution:** Make the script executable:
```bash
chmod +x demo/start_demo.sh
./demo/start_demo.sh
```

---

## Requirements

### CLI Demo Requirements

- Python 3.10+
- Core library installed: `pip install -e .`
- Demo dependencies: `pip install -r demo/requirements.txt`

### Web Demo Requirements

**Backend:**
- All CLI demo requirements
- FastAPI: `pip install fastapi uvicorn[standard] python-multipart`

**Frontend:**
- Node.js 18+ and npm
- Dependencies: `cd demo/frontend && npm install`

---

## See Also

- **[Main README](../README.md)** - Complete library documentation
- **[API Guide](../docs/API_GUIDE.md)** - Library API reference
- **[REST API Tests](tests/api/test_rest_api.py)** - Comprehensive API usage examples
- **[Frontend README](frontend/README.md)** - Frontend-specific documentation
