# Docker Build Optimization - Model Caching

## Problem
Previously, every Docker build would download:
- **Embedding model** (~90MB): 10-15 seconds
- **LLM model** (~638MB): 30-35 seconds

This meant **~45 seconds of unnecessary downloads** on every build!

## Solution
Implemented **Docker BuildKit cache mounts** to cache downloaded models between builds.

### Changes Made

#### 1. Dockerfile Updates
- Added `--mount=type=cache` for both model downloads
- **Embedding model**: Caches to `/root/.cache/huggingface`
- **LLM model**: Caches to `/root/.wget-cache` with conditional download

```dockerfile
# Embedding model with cache
RUN --mount=type=cache,target=/root/.cache/huggingface \
    python -c "from sentence_transformers import SentenceTransformer; ..."

# LLM model with cache and conditional logic
RUN --mount=type=cache,target=/root/.wget-cache \
    if [ ! -f "/root/.wget-cache/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]; then \
        echo "Downloading LLM model..."; \
        wget ... \
    else \
        echo "✅ Using cached LLM model"; \
    fi && \
    cp /root/.wget-cache/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf /app/models/
```

#### 2. docker-compose.yml Updates
- Added volume mount: `./models:/app/models`
- Models persist in the host filesystem for runtime access

```yaml
volumes:
  - memorizer-data:/app/data
  - ./models:/app/models  # Models available at runtime
```

## Results

### First Build (Cold Cache)
```
#17 ... Downloading LLM model for air-gapped deployment...
#17 36.28 ✅ LLM model ready
```
**Time**: ~36 seconds to download LLM + ~12 seconds for embedding = **~48 seconds**

### Subsequent Builds (Warm Cache)
```
#18 0.039 ✅ Using cached LLM model
#18 0.389 ✅ LLM model ready
```
**Time**: **~0.4 seconds** 🎉

## Performance Improvement
- **First build**: Normal download time (~48s for models)
- **Subsequent builds**: **~99% faster** (0.4s vs 48s)
- **Cache persists** across builds until you manually clear it

## How to Use

### Normal Build (Uses Cache)
```bash
docker-compose build
docker-compose up -d
```

### Clear Cache (Force Re-download)
```bash
# Clear all Docker build caches
docker builder prune -a

# Or clear specific cache
docker buildx prune --filter type=cache.mount
```

### Check Cache Usage
```bash
# See cache mount usage
docker buildx du

# See what's in your local models directory
ls -lh ./models/
```

## Architecture

```
Build Time:
┌─────────────────────────────────────┐
│  Docker BuildKit Cache Mounts       │
│  ┌────────────────────────────────┐ │
│  │ /root/.cache/huggingface       │ │  ← Embedding model cache
│  │ /root/.wget-cache              │ │  ← LLM model cache
│  └────────────────────────────────┘ │
│              ↓                       │
│  Models copied to /app/models       │
└─────────────────────────────────────┘

Runtime:
┌─────────────────────────────────────┐
│  Host: ./models                     │  ← Persisted on disk
│         ↕                            │
│  Container: /app/models             │  ← Volume mounted
└─────────────────────────────────────┘
```

## Benefits

1. **Faster Development**: Rebuild images instantly without re-downloading models
2. **Bandwidth Savings**: Models only downloaded once
3. **Disk Efficiency**: Cache is shared across all builds
4. **Air-Gapped Ready**: Models bundled in final image
5. **Runtime Flexibility**: Models can be updated in `./models/` directory

## Notes

- BuildKit cache mounts require Docker BuildKit (enabled by default in Docker 20.10+)
- Cache is stored in Docker's build cache (not in the image layers)
- The final image still contains the models (air-gapped deployment)
- Volume mount at runtime allows for model updates without rebuilding

## Verification

Check that caching is working:
```bash
# First build
time docker-compose build  # Should show "Downloading LLM model..."

# Second build
time docker-compose build  # Should show "✅ Using cached LLM model"
```

The second build should be **significantly faster** (40-45 seconds saved)!
