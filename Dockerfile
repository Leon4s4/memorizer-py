# Air-Gapped Dockerfile - Includes ALL models (no internet needed at runtime)
# This version pre-downloads the LLM model during build for fully offline deployment
# Size: ~2GB (vs ~800MB without LLM)

FROM python:3.11-slim AS builder

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
RUN pip install --no-cache-dir --user -r requirements.txt && \
    find /root/.local -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /root/.local -type f -name "*.pyc" -delete 2>/dev/null || true


# Final stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    libgomp1 \
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

# Download embedding models during build (for air-gapped deployment)
# L6 model (~90MB) for fast embeddings, L12 model (~133MB) for high-quality embeddings
RUN python3 -c "from sentence_transformers import SentenceTransformer; \
    print('Downloading primary embedding model...'); \
    model1 = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder='${SENTENCE_TRANSFORMERS_HOME}'); \
    print('✅ Primary model downloaded'); \
    print('Downloading secondary embedding model...'); \
    model2 = SentenceTransformer('sentence-transformers/all-MiniLM-L12-v2', cache_folder='${SENTENCE_TRANSFORMERS_HOME}'); \
    print('✅ Secondary model downloaded')" && \
    echo "Models embedded in image at: ${SENTENCE_TRANSFORMERS_HOME}" && \
    ls -lh /app/models/sentence-transformers/ && \
    find /app/models -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /app/models -type f -name "*.pyc" -delete 2>/dev/null || true

# Switch to root to download LLM model
USER root

# Download LLM model for air-gapped deployment (~600MB) - using cache mount
RUN --mount=type=cache,target=/root/.wget-cache \
    if [ ! -f "/root/.wget-cache/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]; then \
        echo "Downloading LLM model for air-gapped deployment..."; \
        wget -q --show-progress --progress=bar:force \
        https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
        -O /root/.wget-cache/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf; \
    else \
        echo "✅ Using cached LLM model"; \
    fi && \
    cp /root/.wget-cache/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf /app/models/ && \
    chown memorizer:memorizer /app/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf && \
    echo "✅ LLM model ready"

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
EXPOSE 8000 8501 8800

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
# Start MCP HTTP server in background\n\
echo "Starting MCP HTTP server on port 8800..."\n\
python mcp_http_server.py &\n\
MCP_PID=$!\n\
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
echo "MCP HTTP:   http://localhost:8800/mcp"\n\
echo "Health:     http://localhost:8000/healthz"\n\
echo ""\n\
echo "Features:"\n\
echo "  ✅ Semantic search (ChromaDB)"\n\
echo "  ✅ Vector embeddings (all-MiniLM-L6-v2)"\n\
echo "  ✅ Title generation (TinyLlama 1.1B)"\n\
echo "  ✅ MCP HTTP server (stdio + HTTP)"\n\
echo "  ✅ Fully air-gapped"\n\
echo ""\n\
echo "========================================"\n\
echo ""\n\
\n\
# Wait for all processes\n\
wait $API_PID $MCP_PID $STREAMLIT_PID\n\
' > /app/start.sh && chmod +x /app/start.sh

USER memorizer

# Start command
CMD ["/app/start.sh"]
