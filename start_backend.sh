#!/bin/bash

# Start the FastAPI backend server
echo "Starting Excel Skills Assessment Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip first
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies with force reinstall for groq
echo "Installing dependencies..."
pip install -r requirements.txt --force-reinstall

# Start the server
echo "Starting FastAPI server on http://localhost:8000"
echo "API key is hardcoded for development"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
