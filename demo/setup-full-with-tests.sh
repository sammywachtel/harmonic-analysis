#!/bin/bash

echo "🎵 Setting up Harmonic Analysis Demo (Full - With E2E Tests)..."

# Check if we're in the demo directory
if [ ! -f "README.md" ] || ! grep -q "Harmonic Analysis Library Demo" README.md; then
    echo "❌ Error: This script must be run from the demo/ directory"
    echo "   Run: cd demo && ./setup-full-with-tests.sh"
    exit 1
fi

# Check for required tools
echo "🔍 Checking required tools..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    echo "   Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    echo "   Please install Python 3.11+ from https://python.org/"
    exit 1
fi

if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip is required but not installed"
    echo "   Please install pip with your Python installation"
    exit 1
fi

echo "✅ All required tools found"

# Setup frontend
echo ""
echo "📱 Setting up demo frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
else
    echo "✅ Frontend dependencies already installed"
fi
cd ..

# Setup backend
echo ""
echo "🐍 Setting up demo backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install backend dependencies
echo "📦 Installing backend dependencies..."
pip install -r requirements.txt

# Install the main harmonic analysis library in the virtual environment
echo "📦 Installing harmonic analysis library in backend virtual environment..."
pip install -e ../..

cd ..

# Setup e2e tests
echo ""
echo "🧪 Setting up e2e tests..."
cd e2e-tests
if [ ! -d "node_modules" ]; then
    echo "📦 Installing e2e test dependencies..."
    npm install
    echo "🌐 Installing Playwright browsers..."
    npx playwright install
else
    echo "✅ E2E test dependencies already installed"
fi
cd ..

# Create docs directory
echo ""
echo "📚 Setting up documentation..."
mkdir -p docs

# Check if setup-only flag is provided
if [ "$1" = "--setup-only" ]; then
    echo ""
    echo "🎉 Demo setup complete!"
    echo ""
    echo "🚀 To run the demo:"
    echo "   ./run-demo.sh"
    echo ""
    echo "🧪 To run tests:"
    echo "   cd e2e-tests && npm run test:e2e"
    echo ""
    echo "📖 See README.md for more information"
    exit 0
fi

# Ask if user wants to start the demo
echo ""
echo "🎉 Demo setup complete!"
echo ""
read -p "🚀 Would you like to start the demo now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting demo..."
    ./run-demo.sh
else
    echo ""
    echo "🚀 To run the demo later:"
    echo "   ./run-demo.sh"
    echo ""
    echo "🧪 To run tests:"
    echo "   cd e2e-tests && npm run test:e2e"
    echo ""
    echo "📖 See README.md for more information"
fi
