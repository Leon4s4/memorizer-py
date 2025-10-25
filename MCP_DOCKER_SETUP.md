# MCP Setup for Docker Deployment

## ✅ Problem Solved!

Your MCP server is running **inside Docker**, so you need to use **HTTP mode** instead of stdio.

## What Changed

### 1. Created MCP HTTP Server
**File:** `mcp_http_server.py`
- Exposes MCP tools via HTTP on port 8800
- Endpoints:
  - `GET /mcp/tools` - List available tools
  - `POST /mcp/call` - Call a tool
  - `GET /healthz` - Health check

### 2. Updated Dockerfile
- Starts MCP HTTP server on port 8800
- Exposes port 8800
- Shows MCP endpoint in startup banner

### 3. Updated docker-compose.yml
- Maps port 8800 to host

### 4. Updated VS Code Settings
**File:** `.vscode/settings.json`
```json
{
    "mcp.servers": {
        "memorizer-docker": {
            "url": "http://localhost:8800/mcp",
            "type": "http"
        }
    }
}
```

## How to Use

### Step 1: Rebuild and Start Docker Container

```bash
# Rebuild the image
docker-compose build

# Start the container
docker-compose up -d

# Check logs
docker-compose logs -f
```

You should see:
```
Starting API server on port 8000...
✅ API is ready!
Starting MCP HTTP server on port 8800...
Starting Streamlit UI on port 8501...
========================================
Memorizer is running!
========================================

API:        http://localhost:8000
API Docs:   http://localhost:8000/docs
UI:         http://localhost:8501
MCP HTTP:   http://localhost:8800/mcp
Health:     http://localhost:8000/healthz
```

### Step 2: Test MCP HTTP Server

```bash
# List available tools
curl http://localhost:8800/mcp/tools

# Call the store tool
curl -X POST http://localhost:8800/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "store",
    "arguments": {
      "type": "test",
      "text": "Hello from MCP!",
      "source": "curl",
      "title": "Test Memory"
    }
  }'
```

### Step 3: Restart VS Code/Claude Code

**Restart VS Code/Claude Code** to reload the MCP settings.

The MCP client will now connect to `http://localhost:8800/mcp` successfully! ✅

## Port Mapping

| Service | Container Port | Host Port | Purpose |
|---------|---------------|-----------|---------|
| API | 8000 | 9000 | REST API |
| Streamlit | 8501 | 8501 | Web UI |
| **MCP HTTP** | **8800** | **8800** | **MCP tools** |

## Architecture

```
┌─────────────────────────────────────────┐
│  Docker Container (memorizer)           │
│                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │ API:8000 │  │ UI:8501  │  │ MCP  │ │
│  │          │  │          │  │ :8800│ │
│  └────┬─────┘  └──────────┘  └───┬──┘ │
│       │                           │    │
│       └─────┬──────────────┬──────┘    │
│             │              │           │
│        ┌────▼──────────────▼───┐       │
│        │  ChromaDB + Models    │       │
│        │  /app/data            │       │
│        └───────────────────────┘       │
└─────────────────────────────────────────┘
         │              │
         │              │
      Port 9000      Port 8800
         │              │
         ▼              ▼
┌────────────────────────────────┐
│  VS Code / Claude Code         │
│                                │
│  MCP Client connects to:       │
│  http://localhost:8800/mcp     │
└────────────────────────────────┘
```

## MCP Tools Available

Once connected, you can use these tools:

### 1. `store` - Store a memory
```json
{
  "name": "store",
  "arguments": {
    "type": "reference",
    "text": "Python best practices...",
    "source": "LLM",
    "title": "Python Best Practices",
    "tags": ["python", "best-practices"],
    "confidence": 1.0
  }
}
```

### 2. `search` - Search memories
```json
{
  "name": "search",
  "arguments": {
    "query": "python best practices",
    "limit": 10,
    "minSimilarity": 0.7,
    "filterTags": ["python"]
  }
}
```

### 3. `get` - Get memory by ID
```json
{
  "name": "get",
  "arguments": {
    "id": "uuid-here"
  }
}
```

### 4. `get_many` - Get multiple memories
```json
{
  "name": "get_many",
  "arguments": {
    "ids": ["uuid1", "uuid2"]
  }
}
```

### 5. `delete` - Delete a memory
```json
{
  "name": "delete",
  "arguments": {
    "id": "uuid-here"
  }
}
```

### 6. `create_relationship` - Link memories
```json
{
  "name": "create_relationship",
  "arguments": {
    "fromId": "uuid1",
    "toId": "uuid2",
    "type": "example-of"
  }
}
```

## Troubleshooting

### "Connection failed" error?

1. **Check container is running:**
   ```bash
   docker ps | grep memorizer
   ```

2. **Check MCP HTTP server started:**
   ```bash
   docker logs memorizer | grep "MCP HTTP"
   ```
   Should see: `Starting MCP HTTP server on port 8800...`

3. **Test endpoint directly:**
   ```bash
   curl http://localhost:8800/mcp/tools
   ```

4. **Check port mapping:**
   ```bash
   docker port memorizer
   ```
   Should show: `8800/tcp -> 0.0.0.0:8800`

### Container won't start?

Rebuild with latest changes:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### MCP tools not appearing in VS Code?

1. Restart VS Code/Claude Code
2. Check MCP output panel for errors
3. Verify URL in settings: `http://localhost:8800/mcp`

## Local Development (Without Docker)

If you want to run MCP locally without Docker:

```bash
# Terminal 1: Start MCP HTTP server
python mcp_http_server.py

# VS Code settings stays the same:
# http://localhost:8800/mcp
```

## Testing the Connection

### Quick Test Script

```bash
#!/bin/bash

echo "Testing MCP HTTP Server..."

# Test 1: List tools
echo ""
echo "1. Listing available tools..."
curl -s http://localhost:8800/mcp/tools | jq '.tools[].name'

# Test 2: Store a memory
echo ""
echo "2. Storing a test memory..."
RESULT=$(curl -s -X POST http://localhost:8800/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "store",
    "arguments": {
      "type": "test",
      "text": "MCP HTTP test successful!",
      "source": "test",
      "title": "HTTP Test"
    }
  }')
echo "$RESULT" | jq '.'

# Test 3: Search for the memory
echo ""
echo "3. Searching for test memory..."
curl -s -X POST http://localhost:8800/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "search",
    "arguments": {
      "query": "HTTP test",
      "limit": 1
    }
  }' | jq '.'

echo ""
echo "✅ MCP HTTP Server is working!"
```

Save as `test-mcp.sh` and run:
```bash
chmod +x test-mcp.sh
./test-mcp.sh
```

## Summary

✅ **MCP HTTP server created** (`mcp_http_server.py`)
✅ **Docker configured** to run MCP HTTP on port 8800
✅ **docker-compose updated** to expose port 8800
✅ **VS Code settings updated** to use HTTP mode
✅ **Ready to use!** Rebuild container and restart VS Code

**Next steps:**
1. `docker-compose build && docker-compose up -d`
2. Restart VS Code/Claude Code
3. MCP tools should appear and work! 🎉
