# MCP Client Setup for VS Code / Claude Code

## The Problem

The MCP server (`mcp_server.py`) runs in **stdio mode** (communicates via standard input/output), but your client was configured for **HTTP mode** (trying to connect to `http://localhost:9000/mcp`).

**Error you saw:**
```
Connection state: Error Error sending message to http://localhost:9000/mcp: TypeError: fetch failed
```

## The Solution

### Option 1: Use stdio Mode (RECOMMENDED - Already Fixed!)

The `.vscode/settings.json` has been updated to use stdio mode:

```json
{
    "mcp.servers": {
        "memorizer-self": {
            "command": "python",
            "args": ["/Users/Git/memorizer-py/mcp_server.py"],
            "env": {
                "MEMORIZER_DATA_DIR": "/Users/Git/memorizer-py/data",
                "MEMORIZER_CHROMA_DIR": "/Users/Git/memorizer-py/data/chroma",
                "MEMORIZER_MODELS_DIR": "/Users/Git/memorizer-py/models"
            }
        }
    }
}
```

**How it works:**
1. VS Code/Claude Code launches `python mcp_server.py`
2. Communicates via stdin/stdout (no HTTP needed)
3. Direct, fast, no network ports

**Restart VS Code/Claude Code** for changes to take effect.

---

### Option 2: Add HTTP Support to MCP Server (Alternative)

If you want to use HTTP mode instead, you need to create a separate HTTP-based MCP server.

**Create a new file:** `mcp_http_server.py`

```python
"""HTTP-based MCP Server for Memorizer."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from mcp.server import Server
from mcp.server.fastapi import add_mcp_routes
import asyncio

from mcp_server import app as mcp_app
from config import settings

# Create FastAPI app
http_app = FastAPI(
    title="Memorizer MCP HTTP Server",
    version=settings.app_version
)

# Add CORS
http_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add MCP routes
add_mcp_routes(http_app, mcp_app, "/mcp")

# Health check
@http_app.get("/")
async def root():
    return {"status": "running", "service": "Memorizer MCP HTTP Server"}

if __name__ == "__main__":
    uvicorn.run(
        http_app,
        host="0.0.0.0",
        port=8800,
        log_level="info"
    )
```

**Then update `.vscode/settings.json`:**

```json
{
    "mcp.servers": {
        "memorizer-self": {
            "url": "http://localhost:8800/mcp",
            "type": "http"
        }
    }
}
```

**And run it:**
```bash
python mcp_http_server.py
```

---

## Comparison

| Feature | stdio Mode (Default) | HTTP Mode |
|---------|---------------------|-----------|
| **Setup** | ✅ Simple - Just works | Requires separate server |
| **Performance** | ✅ Fast - Direct communication | Slower - Network overhead |
| **Security** | ✅ Local only | Exposed on network |
| **Debugging** | Harder - Logs mixed with stdio | ✅ Easier - HTTP logs |
| **Port Required** | ❌ No | ✅ Yes (8800) |
| **Multi-client** | ❌ No (1 client at a time) | ✅ Yes (multiple clients) |

## Recommended Setup

**For local development:** Use **stdio mode** (Option 1 - already configured!)

**For remote/shared access:** Use **HTTP mode** (Option 2)

---

## Testing stdio Mode

After restarting VS Code/Claude Code:

1. The MCP server should start automatically
2. Check the MCP output panel in VS Code
3. You should see:
   ```
   Starting Memorizer MCP server...
   Storage: /Users/Git/memorizer-py/data/chroma
   Embedding model: all-MiniLM-L6-v2
   LLM available: True/False
   ```

4. Test by asking Claude Code to store a memory:
   ```
   "Store a test memory with title 'Test', type 'test', text 'Hello world', source 'test'"
   ```

---

## Troubleshooting

### Still getting "fetch failed"?

1. **Restart VS Code/Claude Code** - Settings changes require restart
2. **Check Python path** - Make sure `python` command works
3. **Check dependencies** - Run `pip install -r requirements.txt`
4. **Check logs** - Look at MCP output panel in VS Code

### "Command not found: python"?

Update `.vscode/settings.json` to use full path:

```json
{
    "mcp.servers": {
        "memorizer-self": {
            "command": "/usr/local/bin/python3",  // Or /usr/bin/python3
            "args": ["/Users/Git/memorizer-py/mcp_server.py"],
            ...
        }
    }
}
```

Find your Python path:
```bash
which python3
```

### "Module not found" errors?

Install dependencies:
```bash
cd /Users/Git/memorizer-py
pip install -r requirements.txt
```

Or use a virtual environment:
```bash
cd /Users/Git/memorizer-py
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then update settings to use venv Python:
```json
{
    "mcp.servers": {
        "memorizer-self": {
            "command": "/Users/Git/memorizer-py/venv/bin/python",
            "args": ["/Users/Git/memorizer-py/mcp_server.py"],
            ...
        }
    }
}
```

---

## Key Differences: stdio vs HTTP

### stdio Mode (Current Setup)

```
Claude Code → python mcp_server.py → stdin/stdout → MCP Protocol
```

**Pros:**
- No HTTP server needed
- No ports to configure
- Faster (no network overhead)
- More secure (no network exposure)

**Cons:**
- One client at a time
- Harder to debug
- Can't access remotely

### HTTP Mode (Alternative)

```
Claude Code → HTTP Request → FastAPI → MCP HTTP Server → MCP Protocol
```

**Pros:**
- Multiple clients can connect
- Easier to debug (HTTP logs)
- Can access remotely
- Works with Docker containers

**Cons:**
- Requires running separate server
- Network port required (8800)
- Slight performance overhead
- More complex setup

---

## Current Configuration Status

✅ **stdio mode is now configured** in `.vscode/settings.json`
✅ **Data directories created** at `/Users/Git/memorizer-py/data`
✅ **MCP server ready** to run via `python mcp_server.py`

**Next step:** Restart VS Code/Claude Code and the MCP server should connect automatically!

---

## Docker Container Note

If you're running the Memorizer API in Docker (on port 9000), that's **separate** from the MCP server:

- **Docker container** (port 9000): Runs `api.py` - REST API for memories
- **MCP server** (stdio): Runs `mcp_server.py` - MCP protocol for Claude Code

They both access the same data but via different interfaces:
- REST API: HTTP endpoints (`/api/memories`, `/api/search`, etc.)
- MCP Server: MCP protocol tools (`store`, `search`, `get`, etc.)

You can run both at the same time!

```bash
# Terminal 1: Run Docker container (REST API)
docker-compose up

# Terminal 2: MCP server runs automatically via VS Code
# (Just restart VS Code/Claude Code)
```

Both will share the same data directory if you mount it correctly.
