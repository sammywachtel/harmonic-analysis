#!/bin/bash

echo "🎵 Starting Harmonic Analysis Demo..."

# Check if we're in the demo directory
if [ ! -f "README.md" ] || ! grep -q "Harmonic Analysis Library Demo" README.md; then
    echo "❌ Error: This script must be run from the demo/ directory"
    echo "   Run: cd demo && ./run-demo.sh"
    exit 1
fi

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down demo..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "✅ Backend stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "✅ Frontend stopped"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if setup has been run
if [ ! -d "frontend/node_modules" ] || [ ! -d "backend/venv" ]; then
    echo "❌ Demo not set up yet. Running setup first..."
    ./setup-full-with-tests.sh --setup-only
fi

# Start backend
echo "🐍 Starting demo backend..."
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8010 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 3

# Check if backend is running
if ! curl -s http://localhost:8010/health > /dev/null; then
    echo "❌ Backend failed to start"
    cleanup
    exit 1
fi

echo "✅ Backend running on http://localhost:8010"

# Start frontend
echo "📱 Starting demo frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
sleep 5

# Check if frontend is running
if ! curl -s http://localhost:3010 > /dev/null; then
    echo "❌ Frontend failed to start"
    cleanup
    exit 1
fi

echo "✅ Frontend running on http://localhost:3010"

echo ""
echo "🎉 Demo is now running!"
echo ""
echo "🌐 Open your browser to: http://localhost:3010"
echo "📡 API documentation: http://localhost:8010/docs"
echo "🏥 Backend health check: http://localhost:8010/health"
echo ""
echo "🧪 To run e2e tests (in another terminal):"
echo "   cd demo/e2e-tests && npm run test:e2e"
echo ""
echo "⌨️  Press Ctrl+C to stop the demo"

# Keep script running and wait for interrupt
wait
