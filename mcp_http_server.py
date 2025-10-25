"""HTTP-based MCP Server for Memorizer using SSE.

This allows MCP clients to connect via HTTP/SSE instead of stdio.
Useful for Docker containers and remote access.
"""
import asyncio
import json
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import uvicorn

from config import settings
from mcp_server import app as mcp_app, list_tools, call_tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app for HTTP-based MCP
http_app = FastAPI(
    title="Memorizer MCP HTTP Server",
    version=settings.app_version,
    description="HTTP/SSE interface for Memorizer MCP tools"
)

# Add CORS
http_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@http_app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Memorizer MCP HTTP Server",
        "version": settings.app_version,
        "protocol": "MCP over HTTP/SSE",
        "endpoints": {
            "sse": "/sse",
            "messages": "/messages"
        }
    }


@http_app.get("/healthz")
async def health():
    """Health check compatible with main API."""
    return {"status": "healthy", "service": "mcp-http", "version": settings.app_version}


# MCP protocol discovery endpoint
@http_app.get("/mcp")
async def mcp_discovery():
    """MCP protocol discovery endpoint."""
    return {
        "jsonrpc": "2.0",
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "memorizer",
                "version": settings.app_version
            },
            "endpoints": {
                "sse": "/sse",
                "messages": "/messages"
            }
        }
    }


@http_app.post("/mcp")
async def mcp_handler(request: Request):
    """Handle MCP JSON-RPC requests at /mcp endpoint."""
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        msg_id = body.get("id")

        logger.info(f"MCP request at /mcp: {method}")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "memorizer",
                        "version": settings.app_version
                    }
                }
            }

        elif method == "tools/list":
            tools = await list_tools()
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        }
                        for tool in tools
                    ]
                }
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            result = await call_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": content.type,
                            "text": content.text
                        }
                        for content in result
                    ]
                }
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

    except Exception as e:
        logger.error(f"Error handling /mcp request: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "id": msg_id if 'msg_id' in locals() else None,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


# MCP over SSE endpoints
@http_app.get("/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for MCP protocol."""
    async def event_generator():
        logger.info("MCP SSE client connected")

        # Send initialization message
        init_message = {
            "jsonrpc": "2.0",
            "id": 0,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "memorizer",
                    "version": settings.app_version
                }
            }
        }

        yield {
            "event": "message",
            "data": json.dumps(init_message)
        }

        # Keep connection alive
        try:
            while True:
                if await request.is_disconnected():
                    logger.info("MCP SSE client disconnected")
                    break

                # Send ping every 30 seconds
                await asyncio.sleep(30)
                yield {
                    "event": "ping",
                    "data": ""
                }

        except Exception as e:
            logger.error(f"SSE error: {e}")

    return EventSourceResponse(event_generator())


@http_app.post("/messages")
async def messages_endpoint(request: Request):
    """Handle MCP JSON-RPC messages."""
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        msg_id = body.get("id")

        logger.info(f"MCP request: {method}")

        if method == "initialize":
            # Respond to initialize
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "memorizer",
                        "version": settings.app_version
                    }
                }
            }

        elif method == "tools/list":
            # List available tools
            tools = await list_tools()
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        }
                        for tool in tools
                    ]
                }
            }

        elif method == "tools/call":
            # Call a tool
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            result = await call_tool(tool_name, arguments)

            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": content.type,
                            "text": content.text
                        }
                        for content in result
                    ]
                }
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "id": msg_id if 'msg_id' in locals() else None,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


# Legacy endpoints for backwards compatibility
@http_app.get("/mcp/tools")
async def get_tools():
    """List available MCP tools (legacy endpoint)."""
    try:
        tools = await list_tools()
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools
            ]
        }
    except Exception as e:
        logger.error(f"Error listing tools: {e}", exc_info=True)
        return {"error": str(e)}


@http_app.post("/mcp/call")
async def call_mcp_tool(request: Request):
    """Call an MCP tool (legacy endpoint)."""
    try:
        body = await request.json()
        tool_name = body.get("name")
        arguments = body.get("arguments", {})

        if not tool_name:
            return {"error": "Missing 'name' field"}

        logger.info(f"Calling tool: {tool_name}")
        result = await call_tool(tool_name, arguments)

        return {
            "result": [
                {
                    "type": content.type,
                    "text": content.text
                }
                for content in result
            ]
        }

    except Exception as e:
        logger.error(f"Error calling tool: {e}", exc_info=True)
        return {"error": str(e)}


if __name__ == "__main__":
    logger.info("Starting Memorizer MCP HTTP Server...")
    logger.info(f"Listening on http://0.0.0.0:8800")
    logger.info(f"MCP SSE endpoint: http://0.0.0.0:8800/sse")
    logger.info(f"MCP messages endpoint: http://0.0.0.0:8800/messages")

    uvicorn.run(
        http_app,
        host="0.0.0.0",
        port=8800,
        log_level="info"
    )
