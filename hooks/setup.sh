#!/bin/bash
# Auto-install dependencies for yandex-direct plugin on session start

# Install direct-cli if not available
if ! command -v direct &> /dev/null; then
    pip install direct-cli --quiet --disable-pip-version-check 2>/dev/null
fi

# Install MCP server Python dependencies if missing
if ! python3 -c "import mcp, httpx" &> /dev/null; then
    pip install mcp "httpx>=0.27" python-dotenv --quiet --disable-pip-version-check 2>/dev/null
fi
