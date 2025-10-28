# Harmonic Analysis Frontend

React/TypeScript/Vite frontend for the Harmonic Analysis Library demo.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Development

### Prerequisites

- Node.js 18+
- Backend API running on `http://localhost:8000`

### Environment Variables

Create a `.env.development` file (see `.env.example`):

```env
VITE_DEMO_MODE=true
VITE_API_ENDPOINT=http://localhost:8000
```

### Running the Backend

```bash
# From the project root
cd demo
uvicorn demo.backend.rest_api.main:app --reload
```

### Running the Frontend

```bash
# From this directory
npm run dev
```

Visit `http://localhost:5173` in your browser.

## Project Structure

```
src/
├── api/              # API client and analysis functions
│   ├── client.ts     # Axios HTTP client
│   └── analysis.ts   # Analysis API functions
├── components/       # React components
│   ├── Header.tsx    # Library branding and navigation
│   ├── Footer.tsx    # Version info and links
│   ├── Layout.tsx    # Page layout wrapper
│   ├── TabNavigation.tsx  # Tab switcher
│   └── AnalysisResults.tsx  # Results display
├── tabs/            # Tab content components
│   ├── Tab1.tsx     # Manual chord entry form
│   └── Tab2.tsx     # File upload placeholder
├── types/           # TypeScript type definitions
│   └── analysis.ts  # API request/response types
├── config/          # Configuration
│   └── environment.ts  # Environment mode detection
├── App.tsx          # Main app with routing
└── main.tsx         # React entrypoint
```

## Features

### Tab 1: Manual Entry
- Enter chords manually (comma or space separated)
- Optional key hint dropdown (auto-detect by default)
- Analysis profile selection (Classical, Jazz, Pop, Modal)
- Quick example buttons for common progressions
- Loading states and error handling
- Results display with primary interpretation and alternatives
- Pattern detection highlights

### Tab 2: File Upload
- Placeholder for future file upload functionality
- Will support MIDI, MusicXML, and MP3 files

## Technology Stack

- **React 19** - UI framework
- **TypeScript 5** - Type safety
- **Vite 7** - Build tool and dev server
- **Tailwind CSS 4** - Utility-first styling
- **React Router 6** - Client-side routing
- **Axios** - HTTP client
- **Headless UI** - Accessible components

## Demo Mode

When `VITE_DEMO_MODE=true`, the app shows:
- Python code examples
- GitHub link in header
- Developer-friendly language

For production deployment, set `VITE_DEMO_MODE=false`.

## Build Output

```bash
npm run build
```

Generates optimized static files in `dist/`:
- `index.html` - HTML entry point
- `assets/` - JavaScript and CSS bundles

## API Integration

The frontend calls the backend REST API at `/api/analyze`:

**Request:**
```json
{
  "chords": ["Dm", "G7", "C"],
  "key": "C major",
  "profile": "classical"
}
```

**Response:**
```json
{
  "summary": "...",
  "analysis": {
    "primary": {
      "key": "C major",
      "roman_numerals": ["ii", "V7", "I"],
      "confidence": 0.95,
      "interpretation": "..."
    },
    "alternatives": [...]
  },
  "enhanced_summaries": {
    "patterns_detected": [...]
  }
}
```

## License

MIT License - see LICENSE file in project root
