#!/bin/bash

echo "🎵 Setting up Harmonic Analysis Demo (Basic - Fast Setup)..."
echo

# Check if we're in the demo directory
if [ ! -f "setup-basic.sh" ]; then
    echo "❌ Please run this script from the demo/ directory"
    echo "   cd demo && ./setup-basic.sh"
    exit 1
fi

# Install the main library from parent directory
echo "📦 Installing harmonic analysis library..."
pip install -e ..

# Install backend dependencies
echo "🚀 Installing backend dependencies..."
pip install -r backend/requirements.txt

# Install the main library in backend virtual environment too
echo "📦 Installing harmonic analysis library for backend..."
cd backend
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install -e ../..
    deactivate
fi
cd ..

# Install frontend dependencies
echo "⚛️ Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Install demo-level dependencies for concurrent execution
echo "🔧 Installing demo orchestration tools..."
npm install

echo
echo "✅ Demo setup complete!"
echo
echo "🎯 Quick start:"
echo "   npm start         # Starts both frontend and backend"
echo
echo "🌐 Alternative commands:"
echo "   npm run frontend  # Frontend only"
echo "   npm run backend   # Backend API only"
echo "   npm run stop      # Stop all running services"
echo
echo "📖 The demo will open at: http://localhost:3010"
echo "🔧 Backend API runs at: http://localhost:8010"
