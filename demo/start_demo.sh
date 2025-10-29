#!/bin/bash
set -e

# Trap Ctrl-C and cleanup
cleanup() {
    echo ""
    echo "🛑 Shutting down demo..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo "✅ Demo stopped"
    exit 0
}
trap cleanup SIGINT SIGTERM

echo "🚀 Starting Harmonic Analysis Demo..."
echo ""

# Get the directory where this script lives (demo/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Change to project root (parent of demo/) so Python can import demo module
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Start backend
echo "📦 Starting backend (uvicorn on port 8000)..."
uvicorn demo.backend.rest_api.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Start frontend
echo "🎨 Starting frontend (dev server)..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

echo ""
echo "✅ Demo running!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173 (or port shown above)"
echo ""
echo "Press Ctrl-C to stop both servers"

# Wait for processes
wait
