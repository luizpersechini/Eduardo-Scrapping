#!/bin/bash

# Start Web Application for ANBIMA Scraper
# This script starts the Flask web server

echo "════════════════════════════════════════════════════════════════"
echo "           ANBIMA Data Scraper - Web Application"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if we're in the right directory
if [ ! -d "web_app" ]; then
    echo "❌ Error: web_app directory not found"
    echo "   Please run this script from the project root directory"
    exit 1
fi

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    echo "   Please install Python 3.8 or higher"
    exit 1
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask not installed. Installing dependencies..."
    pip3 install -r requirements.txt
fi

echo ""
echo "✅ All dependencies OK"
echo ""

# Start the web application
echo "🚀 Starting web application..."
echo ""
echo "   Server will be available at:"
echo "   ➜  Local:   http://localhost:5000"
echo "   ➜  Network: http://0.0.0.0:5000"
echo ""
echo "   Press Ctrl+C to stop the server"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Change to web_app directory and run
cd web_app && python3 app.py







