#!/bin/bash
# ANBIMA Scraper Web UI Launcher
# Run this script to start the Streamlit web interface locally

echo "=========================================="
echo "  ANBIMA Fund Data Scraper - Web UI"
echo "=========================================="
echo ""
echo "Starting Streamlit server..."
echo "The app will open automatically in your browser at:"
echo "  http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run Streamlit
python3 -m streamlit run streamlit_app.py
