# Air-Gapped Dockerfile - Includes ALL models (no internet needed at runtime)
# This version pre-downloads the LLM model during build for fully offline deployment
# Size: ~2GB (vs ~800MB without LLM)

FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt


# Final stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 memorizer

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/memorizer/.local

# Copy application code
COPY --chown=memorizer:memorizer . .

# Create directories for data and models
RUN mkdir -p /app/data /app/models /app/data/chroma && \
    chown -R memorizer:memorizer /app/data /app/models

# Download embedding model during build (pre-bundled)
USER memorizer
ENV PATH=/home/memorizer/.local/bin:$PATH
ENV SENTENCE_TRANSFORMERS_HOME=/app/models/sentence-transformers

# Pre-download the embedding model (~90MB)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='/app/models/sentence-transformers')"

# Switch to root to download LLM model
USER root

# Download LLM model for air-gapped deployment (~600MB)
RUN echo "Downloading LLM model for air-gapped deployment..." && \
    wget --progress=bar:force \
    https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
    -O /app/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf && \
    chown memorizer:memorizer /app/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf && \
    echo "✅ LLM model downloaded and bundled in image"

# Environment variables
USER memorizer
ENV PYTHONUNBUFFERED=1
ENV MEMORIZER_DATA_DIR=/app/data
ENV MEMORIZER_CHROMA_DIR=/app/data/chroma
ENV MEMORIZER_MODELS_DIR=/app/models
ENV MEMORIZER_EMBEDDING_MODEL=all-MiniLM-L6-v2
ENV MEMORIZER_LLM_MODEL_PATH=/app/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf

# Suppress warnings
ENV CHROMA_TELEMETRY_IMPL=none
ENV PYTORCH_ENABLE_MPS_FALLBACK=1

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Create startup script
USER root
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "========================================"\n\
echo "Memorizer - Air-Gapped Version"\n\
echo "========================================"\n\
echo ""\n\
echo "✅ Embedding model: Pre-bundled"\n\
echo "✅ LLM model: Pre-bundled (TinyLlama 1.1B)"\n\
echo "✅ No internet connection required"\n\
echo ""\n\
\n\
# Verify models exist\n\
if [ -f "/app/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]; then\n\
    LLM_SIZE=$(du -h "/app/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" | cut -f1)\n\
    echo "✅ LLM model verified: $LLM_SIZE"\n\
else\n\
    echo "⚠️  Warning: LLM model not found!"\n\
fi\n\
\n\
echo ""\n\
echo "Starting services..."\n\
echo ""\n\
\n\
# Start FastAPI in background\n\
echo "Starting API server on port 8000..."\n\
python api.py &\n\
API_PID=$!\n\
\n\
# Wait for API to be ready\n\
echo "Waiting for API to be ready..."\n\
for i in {1..30}; do\n\
    if curl -s http://localhost:8000/healthz > /dev/null 2>&1; then\n\
        echo "✅ API is ready!"\n\
        break\n\
    fi\n\
    sleep 1\n\
done\n\
\n\
# Start Streamlit\n\
echo "Starting Streamlit UI on port 8501..."\n\
streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true &\n\
STREAMLIT_PID=$!\n\
\n\
echo ""\n\
echo "========================================"\n\
echo "Memorizer is running!"\n\
echo "========================================"\n\
echo ""\n\
echo "API:        http://localhost:8000"\n\
echo "API Docs:   http://localhost:8000/docs"\n\
echo "UI:         http://localhost:8501"\n\
echo "Health:     http://localhost:8000/healthz"\n\
echo ""\n\
echo "Features:"\n\
echo "  ✅ Semantic search (ChromaDB)"\n\
echo "  ✅ Vector embeddings (all-MiniLM-L6-v2)"\n\
echo "  ✅ Title generation (TinyLlama 1.1B)"\n\
echo "  ✅ MCP server ready"\n\
echo "  ✅ Fully air-gapped"\n\
echo ""\n\
echo "========================================"\n\
echo ""\n\
\n\
# Wait for both processes\n\
wait $API_PID $STREAMLIT_PID\n\
' > /app/start.sh && chmod +x /app/start.sh

USER memorizer

# Start command
CMD ["/app/start.sh"]
