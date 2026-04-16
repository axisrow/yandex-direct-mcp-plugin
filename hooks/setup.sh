#!/bin/bash
# Auto-install dependencies for yandex-direct plugin on session start

_pip_install() {
    pip install --user --quiet --disable-pip-version-check "$@" 2>/dev/null || \
    pip install --break-system-packages --quiet --disable-pip-version-check "$@" 2>/dev/null || \
    true
}

# Install direct-cli if not available
if ! command -v direct &> /dev/null; then
    _pip_install direct-cli
fi

# Install MCP server Python dependencies if missing
if ! python3 -c "import mcp, httpx" &> /dev/null; then
    _pip_install mcp "httpx>=0.27" python-dotenv
fi
