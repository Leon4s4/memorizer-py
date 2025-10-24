#!/bin/bash

# Script to download LLM models for Memorizer
# Run this before building the Docker image if you want to include the LLM model

set -e

echo "==================================="
echo "Memorizer Model Downloader"
echo "==================================="
echo ""

mkdir -p models

# Check if model already exists
if [ -f "models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]; then
    echo "TinyLlama model already exists."
    echo ""
    read -p "Do you want to download it again? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping download."
        exit 0
    fi
fi

echo "Downloading TinyLlama 1.1B model (~600MB)..."
echo "This may take a few minutes depending on your connection."
echo ""

wget --progress=bar:force \
  https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
  -O models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf

echo ""
echo "✅ Model downloaded successfully!"
echo ""
echo "Model location: models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
echo ""
echo "You can now:"
echo "  1. Run locally: ./run-local.sh"
echo "  2. Build Docker: docker build -t memorizer:latest ."
echo ""

# Optional: Offer to download other models
echo "==================================="
echo "Other model options:"
echo "==================================="
echo ""
echo "1. TinyLlama 1.1B (600MB) - ✅ Already downloaded"
echo "2. Phi-2 (1.6GB) - Better quality"
echo "3. Mistral-7B Q4 (4.1GB) - High quality"
echo ""
read -p "Download another model? (1/2/3/n): " -n 1 -r
echo ""

case $REPLY in
    2)
        echo "Downloading Phi-2..."
        wget --progress=bar:force \
          https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf \
          -O models/phi-2.Q4_K_M.gguf
        echo "✅ Phi-2 downloaded!"
        echo "To use: Set MEMORIZER_LLM_MODEL_PATH=./models/phi-2.Q4_K_M.gguf"
        ;;
    3)
        echo "Downloading Mistral-7B (this will take a while)..."
        wget --progress=bar:force \
          https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf \
          -O models/mistral-7b-instruct-v0.2.Q4_K_M.gguf
        echo "✅ Mistral-7B downloaded!"
        echo "To use: Set MEMORIZER_LLM_MODEL_PATH=./models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
        ;;
    *)
        echo "No additional models downloaded."
        ;;
esac

echo ""
echo "Done!"
