#!/bin/bash

# Helper script to get full paths for Claude Desktop config
# Run this script and copy the output to your claude_desktop_config.json

echo "==================================="
echo "Memorizer MCP Configuration Paths"
echo "==================================="
echo ""

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Copy these paths to your Claude Desktop config:"
echo ""
echo "MCP Server Path:"
echo "  $DIR/mcp_server.py"
echo ""
echo "Data Directory:"
echo "  $DIR/data"
echo ""
echo "Chroma Directory:"
echo "  $DIR/data/chroma"
echo ""
echo "Models Directory:"
echo "  $DIR/models"
echo ""
echo "==================================="
echo "Example Configuration:"
echo "==================================="
echo ""

cat <<EOF
{
  "mcpServers": {
    "memorizer": {
      "command": "python",
      "args": [
        "$DIR/mcp_server.py"
      ],
      "env": {
        "MEMORIZER_DATA_DIR": "$DIR/data",
        "MEMORIZER_CHROMA_DIR": "$DIR/data/chroma",
        "MEMORIZER_MODELS_DIR": "$DIR/models"
      }
    }
  }
}
EOF

echo ""
echo "==================================="
echo ""
echo "Configuration file locations:"
echo "  macOS:   ~/Library/Application Support/Claude/claude_desktop_config.json"
echo "  Windows: %APPDATA%\\Claude\\claude_desktop_config.json"
echo "  Linux:   ~/.config/Claude/claude_desktop_config.json"
echo ""
