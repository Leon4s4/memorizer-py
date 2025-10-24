# Memorizer - Self-Contained Memory System

**Air-gapped ready!** Everything bundled in a single Docker container with NO internet required at runtime.

## 🔥 Key Feature: MCP Server

**MCP (Model Context Protocol) server** lets AI assistants like Claude Desktop:
- 💾 Store persistent memories
- 🔍 Search semantically using natural language
- 🔗 Create knowledge graphs between memories
- 🧠 Build persistent knowledge that grows over time

**➡️ [MCP Setup Guide](MCP_SETUP.md)**

## Features

- 🎯 **MCP Server** - Full Model Context Protocol support
- 🧠 **Semantic Search** - Vector-based similarity search
- 📦 **Self-Contained** - Single Docker container
- 🔌 **Air-Gapped Ready** - All models bundled (~2GB)
- 🎨 **Web UI** - Streamlit interface
- 🚀 **REST API** - FastAPI with docs
- 🤖 **Auto Titles** - LLM-powered title generation
- 🔗 **Relationships** - Link memories together

## Requirements

- Docker 20.10+
- 4GB RAM minimum
- 5GB disk space

## Quick Start

### 1. Build (downloads all models)

```bash
cd memorizer-python
docker build -t memorizer:latest .
```

This bundles:
- Embedding model (~90MB)
- LLM model (~600MB)
- All dependencies

### 2. Run (no internet needed!)

```bash
docker run -d \
  -p 8000:8000 \
  -p 8501:8501 \
  -v memorizer-data:/app/data \
  --name memorizer \
  memorizer:latest
```

### 3. Access

- **Web UI:** http://localhost:8501
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## MCP Setup (IMPORTANT!)

### Quick Setup for Claude Desktop (stdio mode)

1. **Configure Claude Desktop** - Edit config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add this configuration:**

```json
{
  "mcpServers": {
    "memorizer": {
      "command": "python",
      "args": ["/FULL/PATH/TO/memorizer-v1/memorizer-python/mcp_server.py"],
      "env": {
        "MEMORIZER_DATA_DIR": "/FULL/PATH/TO/memorizer-v1/memorizer-python/data",
        "MEMORIZER_CHROMA_DIR": "/FULL/PATH/TO/memorizer-v1/memorizer-python/data/chroma",
        "MEMORIZER_MODELS_DIR": "/FULL/PATH/TO/memorizer-v1/memorizer-python/models"
      }
    }
  }
}
```

**Helper:** Run `./get_full_path.sh` to generate exact paths for your system.

3. **Restart Claude Desktop**

4. **Test:** Ask Claude to "Store a test memory"

### Quick Setup for VS Code (HTTP mode with Docker)

1. **Start Memorizer:**
```bash
docker-compose up -d
```

2. **Create `.vscode/settings.json` in your workspace:**
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

3. **Reload VS Code** and test the MCP connection

### Available MCP Tools

- `store` - Store new memories
- `search` - Semantic search
- `get` - Retrieve specific memory
- `get_many` - Fetch multiple memories
- `delete` - Remove memories
- `create_relationship` - Link memories

**Full guide:** [MCP_SETUP.md](MCP_SETUP.md)

## Air-Gapped Deployment

Deploy to completely offline environments:

```bash
# 1. Build on internet-connected machine
docker build -t memorizer:latest .

# 2. Save to file
docker save memorizer:latest | gzip > memorizer.tar.gz

# 3. Transfer to air-gapped machine (USB, secure transfer, etc.)

# 4. Load and run (NO internet needed!)
docker load < memorizer.tar.gz
docker run -d -p 8000:8000 -p 8501:8501 -v memorizer-data:/app/data memorizer:latest
```

**Everything included:**
- ✅ Embedding model (all-MiniLM-L6-v2)
- ✅ LLM model (TinyLlama 1.1B)
- ✅ All Python dependencies
- ✅ ChromaDB database

## Usage

### Web UI

1. **Search:** Enter query, filter by tags, view results with scores
2. **Add Memory:** Fill form (type, source, content, tags)
3. **Statistics:** View total memories, tags, relationships
4. **Settings:** View config, trigger title generation

### REST API

**Create memory:**
```bash
curl -X POST "http://localhost:8000/api/memories" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "note",
    "content": {"text": "This is a test memory"},
    "source": "api",
    "tags": ["test"]
  }'
```

**Search:**
```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "test memory", "limit": 10}'
```

**Full docs:** http://localhost:8000/docs

## Configuration

Copy `.env.example` to `.env` to customize:

```bash
cp .env.example .env
```

Key settings:
- `MEMORIZER_SIMILARITY_THRESHOLD` - Min similarity for search (0.7)
- `MEMORIZER_SEARCH_LIMIT` - Default result limit (10)
- `MEMORIZER_ENABLE_BACKGROUND_JOBS` - Auto title generation (true)

## Troubleshooting

### Startup Warnings (Harmless!)

You'll see warnings like:
```
Failed to send telemetry event...
ggml_metal_init: skipping kernel...
```

**These are normal!** They don't affect functionality.

**To suppress:** Copy `.env.example` to `.env` (includes suppression settings)

**Full explanation:** [WARNINGS_QUICK_FIX.txt](WARNINGS_QUICK_FIX.txt)

### Common Issues

**Port already in use:**
```bash
docker run -d -p 9000:8000 -p 9501:8501 memorizer:latest
```

**Out of memory:**
- Increase Docker memory limit
- Or use a smaller LLM model

**LLM not working:**
- Check logs: `docker logs memorizer`
- Verify model file exists in container

## Data Backup

**Backup:**
```bash
docker run --rm -v memorizer-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/memorizer-backup.tar.gz /data
```

**Restore:**
```bash
docker run --rm -v memorizer-data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/memorizer-backup.tar.gz -C /
```

## Architecture

**Single Container:**
- ChromaDB (embedded vector database)
- sentence-transformers (embeddings)
- llama-cpp-python + TinyLlama (LLM)
- FastAPI (REST API)
- Streamlit (Web UI)

**Size:** ~2GB (all models bundled)

---

**Version:** 2.0.0 | **Built for air-gapped environments** ❤️
