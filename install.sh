#!/usr/bin/env bash
# Automated Installer for AI Token Optimizer Pack (OpenCode & Antigravity)
# Supports Linux and macOS

set -euo pipefail

echo "=========================================================="
echo " Installing AI Token Optimizer Pack (OpenCode & AGY)     "
echo "=========================================================="

DOCSLIM_DIR="$HOME/.gemini/config/tools/docslim"
OPENCODE_PLUGIN_DIR="$HOME/.config/opencode/plugins"
AGY_PLUGINS_BASE="$HOME/.gemini/config/plugins"

# 1. Install DocSlim CLI & MCP
echo "[1/5] Installing DocSlim CLI and MCP Server..."
mkdir -p "$DOCSLIM_DIR"
cp ./docslim/docslim.py "$DOCSLIM_DIR/docslim.py"
chmod +x "$DOCSLIM_DIR/docslim.py"
if [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
    ln -sf "$DOCSLIM_DIR/docslim.py" "/usr/local/bin/docslim"
fi

# 2. OpenCode Plugins (In-Process)
echo "[2/5] Installing OpenCode In-Process Plugins (RTK & DocSlim Guard)..."
mkdir -p "$OPENCODE_PLUGIN_DIR"
cp ./opencode/plugins/rtk.ts "$OPENCODE_PLUGIN_DIR/rtk.ts"
cp ./opencode/plugins/docslim-guard.ts "$OPENCODE_PLUGIN_DIR/docslim-guard.ts"
cp ./opencode/instructions.md "$HOME/.config/opencode/instructions.md"

# 3. Antigravity Plugins (RTK & DocSlim bundles)
echo "[3/5] Installing Antigravity Plugins (RTK & DocSlim)..."
mkdir -p "$AGY_PLUGINS_BASE/rtk/rules"
cp ./antigravity/plugins/rtk/plugin.json "$AGY_PLUGINS_BASE/rtk/plugin.json"
cp ./antigravity/plugins/rtk/hooks.json "$AGY_PLUGINS_BASE/rtk/hooks.json"
cp ./antigravity/plugins/rtk/rules/AGENTS.md "$AGY_PLUGINS_BASE/rtk/rules/AGENTS.md"

mkdir -p "$AGY_PLUGINS_BASE/docslim/rules"
cp ./antigravity/plugins/docslim/plugin.json "$AGY_PLUGINS_BASE/docslim/plugin.json"
cp ./antigravity/plugins/docslim/mcp_config.json "$AGY_PLUGINS_BASE/docslim/mcp_config.json"
cp ./antigravity/plugins/docslim/rules/AGENTS.md "$AGY_PLUGINS_BASE/docslim/rules/AGENTS.md"
cp ./antigravity/config-snippets/GEMINI.md "$HOME/.gemini/config/GEMINI.md"

# 4. Global MCP Configurations
echo "[4/5] Updating global MCP configuration..."
mkdir -p "$HOME/.gemini/config"
cp ./antigravity/config-snippets/mcp_config.json "$HOME/.gemini/config/mcp_config.json"

echo ""
echo "✓ Token Optimizer Pack installed & configured as ALWAYS-ON by default!"
echo "Restart OpenCode and Antigravity to take full effect."
