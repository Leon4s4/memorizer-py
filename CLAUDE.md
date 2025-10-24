# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Memorizer is a self-contained memory system with vector search and LLM capabilities. It allows AI assistants (like Claude) to store and retrieve memories using the Model Context Protocol (MCP), creating a persistent knowledge base.

**Requirements:**
- Python 3.11+ (3.11-slim used in Docker)
- ~1GB disk space (with embedding model)
- ~2GB disk space (with embedding + LLM model)

**Core Technologies:**
- FastAPI (REST API server)
- Streamlit (Web UI)
- ChromaDB (Vector database for semantic search)
- Sentence Transformers (Embeddings: all-MiniLM-L6-v2)
- Llama.cpp (Optional LLM for title generation: TinyLlama 1.1B)
- MCP Server (Model Context Protocol for AI assistant integration)

## Architecture

### Three-Interface System

1. **MCP Server** ([mcp_server.py](mcp_server.py)) - Primary interface for AI assistants
   - Runs via stdio protocol
   - Provides 6 tools: `store`, `search`, `get`, `get_many`, `delete`, `create_relationship`
   - Used by Claude Desktop or Claude Code to manage persistent memories

2. **REST API** ([api.py](api.py)) - Programmatic access
   - Port 8000
   - Full CRUD operations on memories
   - Search endpoints with semantic similarity
   - Background job scheduler for title generation

3. **Streamlit UI** ([app.py](app.py)) - Human interaction
   - Port 8501
   - Visual memory browsing and search
   - Statistics and tag distribution
   - Manual memory management

### Data Models ([models.py](models.py))

**Memory:**
- Core entity with UUID, type, content, tags, confidence, title
- Supports dual embeddings: content embedding + metadata embedding
- Relationships: `related-to`, `example-of`, `explains`, `contradicts`, `depends-on`, `supersedes`

**Key Model Classes:**
- `Memory` - Main memory entity
- `MemoryRelationship` - Links between memories
- `MemoryCreate`, `MemoryUpdate` - Request models
- `MemorySearchRequest`, `MemorySearchResponse` - Search operations

### Configuration ([config.py](config.py))

Uses `pydantic-settings` with environment variable support:
- All settings prefixed with `MEMORIZER_`
- Configurable via `.env` file (see `.env.example`)
- Key settings: embedding model, LLM path, search thresholds, data directories

### Storage Service (MISSING IMPLEMENTATION)

**IMPORTANT:** The codebase imports `from services import get_storage_service, get_llm_service` but the `services/` directory is currently empty. This needs to be implemented.

Expected structure:
- `services/__init__.py` - Exports service singletons
- `services/storage.py` - ChromaDB storage implementation
- `services/llm.py` - LLM service for title generation
- `services/embeddings.py` - Embedding generation

## Development Commands

### Local Development

```bash
# Quick start (recommended)
./run-local.sh

# Or manually
make install          # Create venv and install dependencies
make run             # Start API + Streamlit
```

**What `run-local.sh` does:**
1. Creates/activates venv
2. Installs dependencies
3. Creates data/chroma and models directories
4. Starts FastAPI (port 8000) in background
5. Starts Streamlit (port 8501) in foreground
6. Kills API on exit

### Docker Deployment

```bash
# Using docker-compose (recommended)
docker-compose up -d        # Start services
docker-compose logs -f      # View logs
docker-compose down         # Stop services

# Or using Makefile
make build              # Build image
make docker-run         # Run container
make docker-stop        # Stop container

# Or using docker directly
docker build -t memorizer:latest .
docker run -d -p 8000:8000 -p 8501:8501 \
  -v memorizer-data:/app/data \
  --name memorizer memorizer:latest
```

**Docker Features:**
- Air-gapped deployment (includes all models in image)
- Pre-downloads embedding model (~90MB) and LLM model (~600MB) during build
- No internet required at runtime
- Health checks on port 8000/healthz
- Multi-platform support (AMD64, ARM64)

**GitHub Actions CI/CD:**
- Automated builds on push to main/master
- Automatic Docker Hub deployment with version tags
- Multi-platform builds (AMD64 + ARM64)
- See [.github/DOCKER_HUB_SETUP.md](.github/DOCKER_HUB_SETUP.md) for setup instructions

### MCP Server Setup

**For Claude Desktop (stdio mode):**

macOS config: `~/Library/Application Support/Claude/claude_desktop_config.json`
```json
{
  "mcpServers": {
    "memorizer": {
      "command": "python",
      "args": ["/full/path/to/memorizer-py/mcp_server.py"],
      "env": {
        "MEMORIZER_DATA_DIR": "/full/path/to/memorizer-py/data",
        "MEMORIZER_CHROMA_DIR": "/full/path/to/memorizer-py/data/chroma",
        "MEMORIZER_MODELS_DIR": "/full/path/to/memorizer-py/models"
      }
    }
  }
}
```

Use `./get_full_path.sh` to generate exact paths.

**For Claude Code (HTTP mode):**

When running in Docker:
```json
{
  "mcp.servers": {
    "memorizer": {
      "url": "http://localhost:8000",
      "type": "http"
    }
  }
}
```

### Useful Scripts

```bash
./run-local.sh           # Start local dev environment
./download-models.sh     # Download LLM model (~600MB)
./get_full_path.sh       # Generate full paths for MCP config

make clean              # Remove __pycache__, venv, temp files
make models             # Download LLM model
```

**Model Options** (via `./download-models.sh`):
1. TinyLlama 1.1B (600MB) - Default, fast
2. Phi-2 (1.6GB) - Better quality
3. Mistral-7B Q4 (4.1GB) - Highest quality

## Key Implementation Details

### Dual Embedding Strategy

Memorizer uses TWO embeddings per memory:
1. **Content Embedding** - Embeds the actual text/content for semantic search
2. **Metadata Embedding** - Embeds type, tags, title for metadata-aware search

Search combines both with tag boosting for better relevance.

### Search Thresholds

- `MEMORIZER_SIMILARITY_THRESHOLD=0.7` - Primary threshold
- `MEMORIZER_FALLBACK_THRESHOLD=0.6` - Fallback if no results
- `MEMORIZER_TAG_BOOST=0.05` - Boost for tag matches

### Background Jobs

API runs APScheduler for:
- **Title Generation** - Runs every 30 minutes
- Generates titles for memories without titles using LLM
- Batch size: 10 memories per run
- Disable with `MEMORIZER_ENABLE_BACKGROUND_JOBS=false`

### Memory Relationships

Link memories together with typed relationships:
- `example-of` - Link examples to concepts
- `explains` - Link explanations to topics
- `related-to` - General relationships
- `depends-on` - Dependencies
- `supersedes` - Version updates
- `contradicts` - Conflicting information

Use relationships to build knowledge graphs.

## Common Patterns

### Storing Reference Material (via MCP)

```python
# Claude would call the 'store' tool with:
{
  "type": "reference",
  "text": "# Python Type Hints\n\nAlways use type hints...",
  "source": "LLM",
  "title": "Python Type Hints Best Practices",
  "tags": ["python", "best-practices", "type-hints"],
  "confidence": 1.0
}
```

### Searching for Knowledge

```python
# Claude would call the 'search' tool with:
{
  "query": "python type hints",
  "limit": 10,
  "minSimilarity": 0.7,
  "filterTags": ["python", "best-practices"]
}
```

### Creating Relationships

```python
# After storing an example, link it to the reference:
{
  "fromId": "example-uuid",
  "toId": "reference-uuid",
  "type": "example-of"
}
```

## Ports and Endpoints

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| FastAPI | 8000 | http://localhost:8000 | REST API |
| API Docs | 8000 | http://localhost:8000/docs | OpenAPI/Swagger |
| Streamlit | 8501 | http://localhost:8501 | Web UI |
| Health Check | 8000 | http://localhost:8000/healthz | Status |
| MCP Server | stdio | - | AI assistant protocol |

**Note:** docker-compose maps API to port 9000 on host (to avoid conflicts)

## Environment Variables

Key variables (all prefixed with `MEMORIZER_`):

**Storage:**
- `DATA_DIR` - Base data directory (default: ./data)
- `CHROMA_DIR` - ChromaDB path (default: ./data/chroma)
- `MODELS_DIR` - Model storage (default: ./models)

**Embeddings:**
- `EMBEDDING_MODEL` - Model name (default: all-MiniLM-L6-v2)
- `EMBEDDING_DIMENSION` - Vector size (default: 384)

**LLM:**
- `LLM_MODEL_PATH` - GGUF model file path
- `LLM_CONTEXT_SIZE` - Context window (default: 2048)
- `LLM_MAX_TOKENS` - Max generation (default: 256)

**Search:**
- `SIMILARITY_THRESHOLD` - Primary threshold (default: 0.7)
- `FALLBACK_THRESHOLD` - Fallback threshold (default: 0.6)

**Warning Suppression:**
- `CHROMA_TELEMETRY_IMPL=none` - Disable ChromaDB telemetry
- `PYTORCH_ENABLE_MPS_FALLBACK=1` - Suppress PyTorch warnings

See [.env.example](.env.example) for complete list.

## Startup Warnings

Memorizer produces harmless warnings on startup (ChromaDB telemetry, PyTorch Metal, GGML bf16). These can be safely ignored. See [WARNINGS_QUICK_FIX.txt](WARNINGS_QUICK_FIX.txt) for details.

**Quick fix:** Copy `.env.example` to `.env` - it includes warning suppression settings.

## Testing

To verify everything works:

```bash
# Start services
./run-local.sh

# In another terminal:
# Test API
curl http://localhost:8000/healthz

# Test memory creation
curl -X POST http://localhost:8000/api/memories \
  -H "Content-Type: application/json" \
  -d '{
    "type": "test",
    "content": {"text": "Test memory"},
    "source": "api",
    "title": "Test"
  }'

# Test search
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 10}'
```

## Important Files

- [mcp_server.py](mcp_server.py) - MCP server implementation (main AI integration point)
- [api.py](api.py) - FastAPI REST API with background jobs
- [app.py](app.py) - Streamlit UI for manual management
- [models.py](models.py) - Pydantic data models
- [config.py](config.py) - Settings and configuration
- [MCP_SETUP.md](MCP_SETUP.md) - Detailed MCP setup guide for users
- [.env.example](.env.example) - Environment variable template

## MCP Tool Reference

When working with the MCP server, these tools are available:

1. **store** - Create new memory with optional relationship
2. **search** - Semantic search with similarity threshold
3. **get** - Retrieve specific memory by ID
4. **get_many** - Fetch multiple memories by IDs
5. **delete** - Remove memory by ID
6. **create_relationship** - Link two memories

See [MCP_SETUP.md](MCP_SETUP.md) for detailed usage examples and best practices.

## TODO: Missing Implementation

The `services/` module needs to be implemented with:
1. Storage service (ChromaDB integration)
2. LLM service (llama-cpp-python wrapper)
3. Embedding service (sentence-transformers wrapper)
4. Service initialization and singleton management

Currently, imports will fail because these are not implemented.
