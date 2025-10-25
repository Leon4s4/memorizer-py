"""HTTP-based MCP Server for Memorizer.

This allows MCP clients to connect via HTTP instead of stdio.
Useful for Docker containers and remote access.
"""
import asyncio
import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import Any

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
    description="HTTP interface for Memorizer MCP tools"
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
        "endpoints": {
            "tools": "/mcp/tools",
            "call": "/mcp/call"
        }
    }


@http_app.get("/mcp/tools")
async def get_tools():
    """List available MCP tools."""
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
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@http_app.post("/mcp/call")
async def call_mcp_tool(request: Request):
    """Call an MCP tool.

    Request body:
    {
        "name": "store",
        "arguments": {
            "type": "test",
            "text": "Hello world",
            "source": "test",
            "title": "Test Memory"
        }
    }
    """
    try:
        body = await request.json()
        tool_name = body.get("name")
        arguments = body.get("arguments", {})

        if not tool_name:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing 'name' field"}
            )

        logger.info(f"Calling tool: {tool_name} with args: {arguments}")

        # Call the MCP tool
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
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@http_app.get("/healthz")
async def health():
    """Health check compatible with main API."""
    return {"status": "healthy", "service": "mcp-http", "version": settings.app_version}


if __name__ == "__main__":
    logger.info("Starting Memorizer MCP HTTP Server...")
    logger.info(f"Listening on http://0.0.0.0:8800")
    logger.info(f"MCP endpoint: http://0.0.0.0:8800/mcp")

    uvicorn.run(
        http_app,
        host="0.0.0.0",
        port=8800,
        log_level="info"
    )
