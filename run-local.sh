#!/bin/bash

# Local development runner for Memorizer

set -e

echo "==================================="
echo "Memorizer - Local Development"
echo "==================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create directories
echo "Creating data directories..."
mkdir -p data/chroma models

# Check for LLM model
if [ ! -f "models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]; then
    echo ""
    echo "WARNING: LLM model not found!"
    echo "Title generation will be disabled."
    echo ""
    echo "To download the model, run:"
    echo "  wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf -O models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    echo ""
fi

# Start API in background
echo "Starting API server..."
python api.py &
API_PID=$!

# Wait for API to be ready
echo "Waiting for API to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/healthz > /dev/null 2>&1; then
        echo "API is ready!"
        break
    fi
    sleep 1
done

# Start Streamlit
echo "Starting Streamlit UI..."
echo ""
echo "==================================="
echo "Memorizer is running!"
echo ""
echo "API:        http://localhost:8000"
echo "API Docs:   http://localhost:8000/docs"
echo "UI:         http://localhost:8501"
echo "==================================="
echo ""
echo "Press Ctrl+C to stop"
echo ""

streamlit run app.py

# Cleanup
kill $API_PID 2>/dev/null || true
