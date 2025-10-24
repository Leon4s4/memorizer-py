# MCP (Model Context Protocol) Setup Guide

The **MCP server is the core feature** of Memorizer - it allows AI assistants like Claude to store and retrieve memories, creating a persistent knowledge base that grows over time.

## What is MCP?

Model Context Protocol (MCP) allows AI assistants to access external tools and data sources. When you connect Memorizer's MCP server to Claude Desktop, Claude can:

- 📝 **Store memories** - Save reference materials, how-tos, coding standards, examples
- 🔍 **Search memories** - Find relevant information using semantic similarity
- 🔗 **Create relationships** - Link related memories together (e.g., "example-of", "explains")
- 📊 **Retrieve context** - Load related memories automatically for better responses

## Available MCP Tools

### 1. `store`
Store a new memory with optional relationships.

**Use cases:**
- Save coding standards and best practices
- Store how-to guides and tutorials
- Keep reference documentation
- Remember project-specific patterns
- Archive important conversations

**Parameters:**
- `type` (required): Type of memory (e.g., 'reference', 'how-to', 'example')
- `text` (required): The content to store (markdown, code, etc.)
- `source` (required): Source identifier (use 'LLM' for AI-stored knowledge)
- `title` (required): Descriptive title
- `tags` (optional): Tags for organization (e.g., ['python', 'testing'])
- `confidence` (optional): Confidence score 0.0-1.0
- `relatedTo` (optional): UUID of related memory
- `relationshipType` (optional): Type of relationship ('example-of', 'explains', etc.)

### 2. `search`
Search for memories using semantic similarity.

**Use cases:**
- Find relevant how-tos for current task
- Retrieve coding standards
- Look up examples
- Get related reference materials

**Parameters:**
- `query` (required): Search query (natural language)
- `limit` (optional): Max results (default: 10)
- `minSimilarity` (optional): Similarity threshold 0.0-1.0 (default: 0.7)
- `filterTags` (optional): Filter by tags

### 3. `get`
Retrieve a specific memory by ID.

**Parameters:**
- `id` (required): UUID of the memory

### 4. `get_many`
Fetch multiple memories by IDs (useful for loading related memories).

**Parameters:**
- `ids` (required): Array of UUIDs

### 5. `delete`
Remove a memory by ID.

**Parameters:**
- `id` (required): UUID of the memory to delete

### 6. `create_relationship`
Link two memories together.

**Relationship Types:**
- `related-to` - General relationship
- `example-of` - One memory is an example of another
- `explains` - One memory explains another
- `contradicts` - Conflicting information
- `depends-on` - Dependency relationship
- `supersedes` - Newer version replaces older

**Parameters:**
- `fromId` (required): Source memory UUID
- `toId` (required): Target memory UUID
- `type` (required): Relationship type

---

## Setup Instructions

### Option 1: Local Development (Recommended for Testing)

1. **Start Memorizer services:**
   ```bash
   cd memorizer-python
   ./run-local.sh
   ```

2. **In another terminal, start the MCP server:**
   ```bash
   cd memorizer-python
   source venv/bin/activate  # If using virtual environment
   python mcp_server.py
   ```

3. **Configure Claude Desktop** (see below)

### Option 2: Direct Python Installation

1. **Install dependencies:**
   ```bash
   cd memorizer-python
   pip install -r requirements.txt
   ```

2. **Run MCP server:**
   ```bash
   python mcp_server.py
   ```

### Option 3: Using Docker (For Production)

The MCP server can run inside the Docker container, but it needs to communicate via stdio with Claude Desktop.

**TODO:** Docker setup for MCP requires additional configuration for stdio communication.

---

## Configuration Methods

Memorizer MCP can be configured three ways:

1. **stdio (Local Python)** - Direct Python execution, best for single-user local setup
2. **HTTP (REST API)** - Access via REST API, best for Docker/remote deployments
3. **Docker** - Run in container, access via HTTP

---

## VS Code (Claude Code) Configuration

### Method 1: HTTP via Docker (Recommended)

**Step 1:** Start Memorizer with Docker

```bash
cd memorizer-python
docker-compose up -d
```

**Step 2:** Configure VS Code MCP settings

Create/edit `.vscode/settings.json` in your workspace:

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

**When to use:**
- ✅ Running Memorizer in Docker
- ✅ Remote Memorizer instance
- ✅ Multiple users/projects sharing one instance
- ✅ Production deployments

### Method 2: stdio with Local Python

**Step 1:** Install dependencies locally

```bash
cd memorizer-python
pip install -r requirements.txt
```

**Step 2:** Configure VS Code

Create/edit `.vscode/settings.json`:

```json
{
  "mcp.servers": {
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

**Helper:** Run `./get_full_path.sh` to generate exact paths.

**When to use:**
- ✅ Local development without Docker
- ✅ Direct file system access needed
- ✅ Debugging MCP server code

---

## Docker Setup

### Option 1: Docker with HTTP Access (Recommended)

**Step 1:** Build and run container

```bash
cd memorizer-python
docker build -t memorizer:latest .
docker run -d \
  -p 8000:8000 \
  -p 8501:8501 \
  -v memorizer-data:/app/data \
  --name memorizer \
  memorizer:latest
```

**Step 2:** Verify API is accessible

```bash
curl http://localhost:8000/healthz
# Should return: {"status":"healthy","version":"2.0.0"}
```

**Step 3:** Configure your client (VS Code or Claude Desktop)

Use HTTP configuration (see sections above/below)

### Option 2: Docker Compose

**Step 1:** Start services

```bash
cd memorizer-python
docker-compose up -d
```

**Step 2:** Check logs

```bash
docker-compose logs -f memorizer
```

**Step 3:** Configure HTTP access in your client

Services available at:
- API: http://localhost:8000
- UI: http://localhost:8501

---

## HTTP API Configuration Details

When using HTTP mode, Memorizer MCP tools map to REST API endpoints:

| MCP Tool | HTTP Endpoint | Method |
|----------|---------------|--------|
| `store` | `/api/memories` | POST |
| `search` | `/api/search` | POST |
| `get` | `/api/memories/{id}` | GET |
| `get_many` | `/api/memories` | GET (with IDs) |
| `delete` | `/api/memories/{id}` | DELETE |
| `create_relationship` | `/api/relationships` | POST |

**Test HTTP API:**

```bash
# Store a memory
curl -X POST http://localhost:8000/api/memories \
  -H "Content-Type: application/json" \
  -d '{
    "type": "test",
    "content": {"text": "Test memory"},
    "source": "api",
    "title": "Test"
  }'

# Search
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 10}'
```

---

## Claude Desktop Configuration

### Method 1: stdio with Local Python (Recommended for Desktop)

#### For macOS

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "memorizer": {
      "command": "python",
      "args": [
        "/Users/YourUsername/Git/memorizer-v1/memorizer-python/mcp_server.py"
      ],
      "env": {
        "MEMORIZER_DATA_DIR": "/Users/YourUsername/Git/memorizer-v1/memorizer-python/data",
        "MEMORIZER_CHROMA_DIR": "/Users/YourUsername/Git/memorizer-v1/memorizer-python/data/chroma",
        "MEMORIZER_MODELS_DIR": "/Users/YourUsername/Git/memorizer-v1/memorizer-python/models"
      }
    }
  }
}
```

### For Windows

Edit: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "memorizer": {
      "command": "python",
      "args": [
        "C:\\Users\\YourUsername\\Git\\memorizer-v1\\memorizer-python\\mcp_server.py"
      ],
      "env": {
        "MEMORIZER_DATA_DIR": "C:\\Users\\YourUsername\\Git\\memorizer-v1\\memorizer-python\\data",
        "MEMORIZER_CHROMA_DIR": "C:\\Users\\YourUsername\\Git\\memorizer-v1\\memorizer-python\\data\\chroma",
        "MEMORIZER_MODELS_DIR": "C:\\Users\\YourUsername\\Git\\memorizer-v1\\memorizer-python\\models"
      }
    }
  }
}
```

### For Linux

Edit: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "memorizer": {
      "command": "python3",
      "args": [
        "/home/yourusername/Git/memorizer-v1/memorizer-python/mcp_server.py"
      ],
      "env": {
        "MEMORIZER_DATA_DIR": "/home/yourusername/Git/memorizer-v1/memorizer-python/data",
        "MEMORIZER_CHROMA_DIR": "/home/yourusername/Git/memorizer-v1/memorizer-python/data/chroma",
        "MEMORIZER_MODELS_DIR": "/home/yourusername/Git/memorizer-v1/memorizer-python/models"
      }
    }
  }
}
```

#### Using Virtual Environment

If you're using a Python virtual environment:

```json
{
  "mcpServers": {
    "memorizer": {
      "command": "/full/path/to/memorizer-python/venv/bin/python",
      "args": [
        "/full/path/to/memorizer-v1/memorizer-python/mcp_server.py"
      ],
      "env": {
        "MEMORIZER_DATA_DIR": "/full/path/to/memorizer-python/data",
        "MEMORIZER_CHROMA_DIR": "/full/path/to/memorizer-python/data/chroma",
        "MEMORIZER_MODELS_DIR": "/full/path/to/memorizer-python/models"
      }
    }
  }
}
```

### Method 2: HTTP with Docker (For Remote/Production)

If you're running Memorizer in Docker or on a remote server, you can access it via HTTP.

**Note:** Claude Desktop's native MCP protocol primarily supports stdio. For HTTP access, you would need to:

1. **Run Memorizer in Docker** (see Docker Setup section above)
2. **Use the REST API directly** from your applications
3. **Or use a wrapper/bridge** that converts HTTP to stdio for Claude Desktop

**Example HTTP REST API usage:**

```bash
# From any application/script
curl -X POST http://localhost:8000/api/memories \
  -H "Content-Type: application/json" \
  -d '{
    "type": "note",
    "content": {"text": "This is stored via HTTP"},
    "source": "api",
    "title": "HTTP Example"
  }'
```

**For remote Docker instance:**

```bash
# Access Memorizer running on another machine
curl -X POST http://your-server.com:8000/api/memories \
  -H "Content-Type: application/json" \
  -d '{...}'
```

---

## Testing the MCP Connection

1. **Restart Claude Desktop** after updating the configuration

2. **Check for the Memorizer tools** - In Claude Desktop, you should see the MCP tools available

3. **Test with a simple store command:**
   ```
   You: Store a test memory with title "Test Memory",
        type "test", text "This is a test", source "user"

   Claude: [Uses store tool and returns memory ID]
   ```

4. **Test search:**
   ```
   You: Search for memories about "test"

   Claude: [Uses search tool and finds your test memory]
   ```

---

## Usage Examples

### Example 1: Store a Coding Standard

```
You: Please store this Python coding standard for me:

Title: "Python Type Hints Standard"
Type: "coding-standard"
Tags: ["python", "best-practices", "type-hints"]

Content:
# Python Type Hints Standard

Always use type hints in function signatures:

```python
def process_data(items: list[str], max_count: int = 100) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in items[:max_count]:
        result[item] = len(item)
    return result
```

Benefits:
- Better IDE autocomplete
- Catch type errors early
- Self-documenting code
```

Claude will use the `store` tool to save this for future reference.

### Example 2: Search for Best Practices

```
You: I'm writing a Python function. What coding standards should I follow?

Claude: [Uses search tool with query "Python coding standards best practices"]
Claude: [Retrieves and shows your stored coding standards]
```

### Example 3: Create Related Memories

```
You: Store this example of the type hints standard:

```python
# Good example
def calculate_total(prices: list[float], tax_rate: float = 0.1) -> float:
    subtotal = sum(prices)
    return subtotal * (1 + tax_rate)
```

And link it to the "Python Type Hints Standard" memory as an example.

Claude will:
1. Store the example memory
2. Use create_relationship with type "example-of" to link them
```

### Example 4: Retrieve Related Knowledge

```
You: Show me the Python type hints standard and all its examples

Claude will:
1. Search for "Python type hints"
2. Get the main memory
3. See it has relationships
4. Use get_many to fetch related examples
5. Show you everything together
```

---

## Best Practices

### For AI Assistants (Claude)

1. **Use Descriptive Titles**
   - Good: "Python Type Hints Best Practices"
   - Bad: "Coding stuff"

2. **Tag Appropriately**
   - Use consistent tag naming
   - Include language, framework, and topic
   - Examples: ['python', 'fastapi', 'testing', 'best-practices']

3. **Create Relationships**
   - Link examples to their parent concepts
   - Connect related how-tos
   - Mark superseding information

4. **Store Rich Context**
   - Include code examples with markdown
   - Add explanations and rationale
   - Include links to official documentation

5. **Use Appropriate Types**
   - `reference` - Documentation, official standards
   - `how-to` - Step-by-step guides
   - `example` - Code samples, use cases
   - `conversation` - Important discussions
   - `project-context` - Project-specific info

### For Users

1. **Review Stored Memories**
   - Use the Streamlit UI at http://localhost:8501
   - Check what Claude is storing
   - Delete outdated information

2. **Organize with Tags**
   - Establish tag conventions
   - Use the statistics page to see tag distribution

3. **Leverage Relationships**
   - Ask Claude to link related information
   - Use get_many to traverse knowledge graphs

---

## Troubleshooting

### MCP Server Not Appearing in Claude Desktop

1. **Check the config file path:**
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. **Verify JSON syntax:**
   - Use a JSON validator
   - Check for missing commas, quotes

3. **Check Python path:**
   ```bash
   which python3  # macOS/Linux
   where python   # Windows
   ```

4. **Test MCP server manually:**
   ```bash
   python mcp_server.py
   # Should start without errors
   ```

5. **Check Claude Desktop logs:**
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`

### "Memory Not Found" Errors

- Ensure the data directory exists and has write permissions
- Check that ChromaDB is initialized properly
- Verify the MEMORIZER_DATA_DIR environment variable

### Slow Search Performance

- Reduce the number of memories being searched
- Use tag filters to narrow results
- Increase minSimilarity threshold

---

## Advanced Configuration

### Custom Embedding Model

```json
{
  "mcpServers": {
    "memorizer": {
      "command": "python",
      "args": ["/path/to/mcp_server.py"],
      "env": {
        "MEMORIZER_EMBEDDING_MODEL": "all-mpnet-base-v2"
      }
    }
  }
}
```

### Adjust Search Thresholds

```json
{
  "mcpServers": {
    "memorizer": {
      "command": "python",
      "args": ["/path/to/mcp_server.py"],
      "env": {
        "MEMORIZER_SIMILARITY_THRESHOLD": "0.8",
        "MEMORIZER_FALLBACK_THRESHOLD": "0.7"
      }
    }
  }
}
```

---

## MCP vs REST API vs Streamlit UI

| Feature | MCP Server | REST API | Streamlit UI |
|---------|-----------|----------|--------------|
| **Purpose** | AI assistant integration | Programmatic access | Human interaction |
| **Port** | stdio (no port) | 8000 | 8501 |
| **Usage** | Claude Desktop | curl, code | Web browser |
| **Authentication** | None (local) | None (add if needed) | None |
| **Best For** | AI memory storage | Automation, integration | Manual management |

---

## Security Considerations

### Local Usage (Current)
- MCP server runs locally
- No network exposure
- Data stored on local disk
- No authentication needed

### Production Deployment (Future)
If deploying for team use:
- Add authentication to REST API
- Use HTTPS/TLS
- Implement user isolation
- Add audit logging

---

## Performance Tips

1. **Tag your memories well** - Filtering by tags is much faster than semantic search
2. **Use specific queries** - More specific searches return better results
3. **Leverage relationships** - Get related memories in one call with get_many
4. **Monitor memory growth** - Use the Streamlit UI to check statistics

---

## What Makes This Special?

Unlike simple RAG (Retrieval-Augmented Generation) systems, Memorizer offers:

✅ **Persistent Knowledge Graph** - Memories can reference each other
✅ **Semantic Search** - Find by meaning, not just keywords
✅ **Dual Embeddings** - Search by content OR metadata
✅ **Relationship Types** - Explicitly model how knowledge connects
✅ **Tag Organization** - Flexible categorization
✅ **Self-Contained** - No external services needed
✅ **AI-Managed** - Claude can organize its own knowledge

---

## Next Steps

1. **Set up Claude Desktop configuration** (see above)
2. **Restart Claude Desktop**
3. **Test the connection** with a simple store/search
4. **Start building your knowledge base!**

---

## Example Workflow

```
Day 1:
You: "I'm starting a FastAPI project. What should I know?"
Claude: [Searches, finds nothing]
Claude: "Let me store some FastAPI best practices for you..."
Claude: [Stores reference materials with tags: fastapi, python, best-practices]

Day 2:
You: "How do I handle errors in FastAPI?"
Claude: [Searches with "FastAPI error handling"]
Claude: [Finds reference, provides answer]
Claude: [Stores example code as new memory]
Claude: [Links it to FastAPI best practices with "example-of" relationship]

Day 7:
You: "Show me everything about FastAPI we've discussed"
Claude: [Searches for "FastAPI"]
Claude: [Loads related memories via relationships]
Claude: [Provides comprehensive overview with all examples]
```

**Your knowledge base grows smarter over time!** 🧠

---

## Support

- **Documentation:** See [README.md](README.md)
- **Warnings:** See [WARNINGS_QUICK_FIX.txt](WARNINGS_QUICK_FIX.txt) for startup warning solutions
- **Issues:** Check logs in Claude Desktop and MCP server output
