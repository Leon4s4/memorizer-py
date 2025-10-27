# Memorizer - Self-Contained Memory System with MCP Support

**Air-gapped ready!** Everything bundled in a single Docker container with NO internet required at runtime.

## Features

- 🎯 **MCP Server** - Full Model Context Protocol support for AI assistants
- 🧠 **Dual Embeddings** - L6 + L12 models for superior search accuracy
- 📦 **Self-Contained** - Single Docker container with all models
- 🔌 **Air-Gapped Ready** - All models embedded (~879MB)
- 🎨 **Web UI** - Streamlit interface with statistics and tools
- 🚀 **REST API** - FastAPI with OpenAPI docs
- 🤖 **Auto Titles** - LLM-powered title generation (TinyLlama 1.1B)
- 🔗 **Relationships** - Link memories together with typed relationships
- 🔧 **Maintenance Tools** - Database health checks and auto-fix

## Requirements

- Docker 20.10+ and Docker Compose
- 4GB RAM minimum
- 5GB disk space

## Quick Start with Docker

### 1. Clone and Build

```bash
git clone <repository>
cd memorizer-py
docker-compose build
```

This bundles:
- Dual embedding models: L6 (~90MB) + L12 (~133MB)
- LLM model: TinyLlama (~600MB)
- All dependencies

### 2. Run

```bash
docker-compose up -d
```

### 3. Access

- **Web UI:** http://localhost:8501
- **API:** http://localhost:9000
- **API Docs:** http://localhost:9000/docs
- **MCP HTTP:** http://localhost:8800

## MCP (Model Context Protocol) Setup

Connect Memorizer to AI assistants like Claude Desktop, Claude Code, or GitHub Copilot for persistent memory management.

### Available MCP Tools

- `store` - Store new memories with optional relationships
- `search` - Semantic search with dual embeddings
- `get` - Retrieve specific memory by ID
- `getMany` - Fetch multiple memories
- `delete` - Remove memories
- `createRelationship` - Link memories together

### Claude Desktop Configuration

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "memorizer": {
      "command": "curl",
      "args": [
        "-N",
        "-H",
        "Accept: text/event-stream",
        "http://localhost:8800/sse"
      ]
    }
  }
}
```

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json` (use same config)

### VS Code (Claude Code) Configuration

**macOS:** `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

**Windows:** `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`

```json
{
  "mcpServers": {
    "memorizer": {
      "command": "curl",
      "args": [
        "-N",
        "-H",
        "Accept: text/event-stream",
        "http://localhost:8800/sse"
      ]
    }
  }
}
```

### GitHub Copilot Configuration

**macOS:** `~/Library/Application Support/Code - Insiders/User/mcp.json` or `~/Library/Application Support/Code/User/mcp.json`

**Windows:** `%APPDATA%\Code\User\mcp.json`

```json
{
  "memorizer-python": {
    "url": "http://localhost:8000",
    "type": "http"
  }
}
```

### System Prompt for AI Agents

Add this to your `AGENT.md`, Cursor Rules, or AI agent configuration for better integration:

```markdown
You have access to a long-term memory system via the Model Context Protocol (MCP) at the endpoint **memorizer**. Use the following tools:

- **store**: Store a new memory. Parameters: `type`, `content` (markdown), `source`, `tags`, `confidence`, `relatedTo` (optional, memory ID), `relationshipType` (optional).
- **search**: Search for similar memories. Parameters: `query`, `limit`, `minSimilarity`, `filterTags`.
- **get**: Retrieve a memory by ID. Parameter: `id`.
- **getMany**: Retrieve multiple memories by their IDs. Parameter: `ids` (list of IDs).
- **delete**: Delete a memory by ID. Parameter: `id`.
- **createRelationship**: Create a relationship between two memories. Parameters: `fromId`, `toId`, `type`.

Use these tools to remember, recall, relate, and manage information as needed to assist the user.
```

## Local Development (Without Docker)

### Prerequisites

- Python 3.11+
- pip

### Quick Start

```bash
# Run the setup script
./run-local.sh
```

This will:
1. Create virtual environment
2. Install dependencies
3. Start API server (port 8000)
4. Start Streamlit UI (port 8501)

### Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start API server
uvicorn api:app --reload --host 0.0.0.0 --port 8000 &

# Start Streamlit UI
streamlit run app.py --server.port 8501
```

## Usage

### Web UI Features

1. **All Memories** - Browse, search, and filter memories
2. **Create Memory** - Add new memories with rich content
3. **Statistics** - View memory counts, tags, and performance metrics
4. **Tools**:
   - Title Generation - Auto-generate titles using LLM
   - Dual Embedding - Use both L6 and L12 models for better accuracy
   - Performance Analytics - Track tool usage and quality metrics
   - Memory Maintenance - Database health checks with auto-fix
5. **MCP Config** - Setup instructions for all AI assistants
6. **System Config** - View system settings

### REST API Examples

**Create memory:**
```bash
curl -X POST "http://localhost:9000/api/memories" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "note",
    "content": {"text": "This is a test memory"},
    "source": "api",
    "tags": ["test"]
  }'
```

**Search memories:**
```bash
curl -X POST "http://localhost:9000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "test memory", "limit": 10}'
```

**Full API documentation:** http://localhost:9000/docs

## Dual Embedding System

Memorizer uses two embedding models in parallel for superior search accuracy:

- **L6 Model** (all-MiniLM-L6-v2): Fast, 384D embeddings - 40% weight
- **L12 Model** (all-MiniLM-L12-v2): High quality, 384D embeddings - 60% weight

Results are combined using weighted scoring for optimal relevance.

## Air-Gapped Deployment

Deploy to completely offline environments:

```bash
# 1. Build on internet-connected machine
docker-compose build

# 2. Save image to file
docker save memorizer:latest | gzip > memorizer.tar.gz

# 3. Transfer to air-gapped machine (USB, secure transfer, etc.)

# 4. Load and run (NO internet needed!)
docker load < memorizer.tar.gz
docker-compose up -d
```

**Everything included:**
- ✅ Dual embedding models (L6 + L12)
- ✅ LLM model (TinyLlama 1.1B)
- ✅ All Python dependencies
- ✅ ChromaDB database

## Configuration

Environment variables (all prefixed with `MEMORIZER_`):

**Models:**
- `EMBEDDING_MODEL_PRIMARY` - L6 model (default: all-MiniLM-L6-v2)
- `EMBEDDING_MODEL_SECONDARY` - L12 model (default: all-MiniLM-L12-v2)
- `USE_DUAL_EMBEDDINGS` - Enable dual embeddings (default: true)
- `EMBEDDING_WEIGHT_PRIMARY` - L6 weight (default: 0.4)
- `EMBEDDING_WEIGHT_SECONDARY` - L12 weight (default: 0.6)
- `LLM_MODEL_PATH` - Path to GGUF model file

**Search:**
- `SIMILARITY_THRESHOLD` - Min similarity for search (default: 0.7)
- `FALLBACK_THRESHOLD` - Fallback threshold (default: 0.6)
- `SEARCH_LIMIT` - Default result limit (default: 10)

**Paths:**
- `DATA_DIR` - Base data directory (default: ./data)
- `CHROMA_DIR` - ChromaDB path (default: ./data/chroma)
- `MODELS_DIR` - Model storage (default: ./models)

**Jobs:**
- `ENABLE_BACKGROUND_JOBS` - Auto title generation (default: true)

See `.env.example` for complete configuration options.

## Memory Relationships

Link memories together with typed relationships:

- `related-to` - General relationship
- `example-of` - Link examples to concepts
- `explains` - Link explanations to topics
- `contradicts` - Conflicting information
- `depends-on` - Dependencies
- `supersedes` - Newer version replaces older

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

## Troubleshooting

### Startup Warnings

You may see harmless warnings like:
- ChromaDB telemetry failures
- PyTorch Metal warnings
- GGML bf16 notices

These don't affect functionality. To suppress, copy `.env.example` to `.env`.

### Common Issues

**Port already in use:**
Edit `docker-compose.yml` to change port mappings.

**Out of memory:**
Increase Docker memory limit to 4GB or more.

**MCP not connecting:**
1. Ensure container is running: `docker ps`
2. Check MCP server logs: `docker logs memorizer`
3. Test MCP endpoint: `curl http://localhost:8800/mcp/tools`
4. Restart your AI assistant after config changes

### Model Files

Models are embedded in the Docker image by default. If you want to use local models:

1. Uncomment the volume mount in `docker-compose.yml`:
   ```yaml
   - ./models:/app/models
   ```

2. Download models locally:
   ```bash
   python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='./models/sentence-transformers')"
   python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L12-v2', cache_folder='./models/sentence-transformers')"
   ```

## Architecture

**Components:**
- **ChromaDB** - Embedded vector database with dual collections
- **Sentence Transformers** - Dual embedding generation (L6 + L12)
- **Llama.cpp + TinyLlama** - Local LLM for title generation
- **FastAPI** - REST API with background jobs
- **Streamlit** - Interactive web UI
- **MCP HTTP Server** - Model Context Protocol for AI integration

**Storage:**
- Primary collection: L6 embeddings (fast)
- Secondary collection: L12 embeddings (quality)
- Weighted search combines both for optimal results

**Image Size:** ~2GB (all models + dependencies)

## Project Structure

```
memorizer-py/
├── api.py                  # FastAPI REST API
├── app.py                  # Streamlit UI
├── mcp_server.py          # MCP server implementation
├── models.py              # Pydantic data models
├── config.py              # Configuration management
├── services/              # Business logic
│   ├── embeddings.py      # Dual embedding generation
│   ├── llm.py             # LLM service
│   └── storage.py         # ChromaDB storage
├── Dockerfile             # Docker build
├── docker-compose.yml     # Container orchestration
├── requirements.txt       # Python dependencies
└── models/                # Embedded models (not in git by default)
    ├── sentence-transformers/  # L6 + L12 models
    └── tinyllama-*.gguf   # LLM model
```

## Contributing

For development guidelines and architecture details, see [CLAUDE.md](CLAUDE.md).

---

**Version:** 2.0.0 | **Built for air-gapped environments with dual embeddings** ❤️
