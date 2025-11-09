#!/bin/bash
# CoCo Web Commander - Startup Script

echo "========================================"
echo "CoCo Web Commander"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed!"
    echo "Please install Python 3.7 or higher"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $PYTHON_VERSION"

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo ""
    echo "Flask is not installed!"
    echo "Installing requirements..."
    pip3 install -r requirements.txt

    if [ $? -ne 0 ]; then
        echo ""
        echo "Error: Failed to install requirements"
        echo "Please run manually: pip3 install Flask flask-cors"
        exit 1
    fi
fi

echo ""
echo "Starting CoCo Web Commander on port 6809..."
echo "Access the interface at: http://localhost:6809"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================"
echo ""

# Start the server
python3 coco_web_server.py
