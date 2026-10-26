#!/usr/bin/env bash
# Automated Installer for the AI Token Optimizer Pack (OpenCode + Antigravity)
# Linux / macOS
#
# Rules: merge instead of overwrite, never register a hook for a missing binary,
# and verify instead of assuming.

set -euo pipefail

TS="$(date +%Y%m%d-%H%M%S)"
DOCSLIM_DIR="$HOME/.gemini/config/tools/docslim"
OPENCODE_PLUGIN_DIR="$HOME/.config/opencode/plugins"
OPENCODE_CONFIG_DIR="$HOME/.config/opencode"
AGY_PLUGINS_BASE="$HOME/.gemini/config/plugins"
PYTHON="$(command -v python3 || command -v python || true)"

backup() { [ -f "$1" ] && cp "$1" "$1.bak-$TS" && echo "    backup: $1.bak-$TS"; }

echo "=========================================================="
echo " AI Token Optimizer Pack - install (OpenCode + AGY)"
echo "=========================================================="

echo ""
echo "[1/5] DocSlim CLI + MCP server"
if [ -z "$PYTHON" ]; then
    echo "    python3 not found - DocSlim needs Python 3.9+. Skipping MCP setup."
else
    mkdir -p "$DOCSLIM_DIR"
    cp ./docslim/docslim.py "$DOCSLIM_DIR/docslim.py"
    chmod +x "$DOCSLIM_DIR/docslim.py"
    if [ -d /usr/local/bin ] && [ -w /usr/local/bin ]; then
        ln -sf "$DOCSLIM_DIR/docslim.py" /usr/local/bin/docslim
    fi
    echo "    installed to $DOCSLIM_DIR"
fi

echo ""
echo "[2/5] OpenCode plugins (global)"
mkdir -p "$OPENCODE_PLUGIN_DIR"
for p in rtk.ts docslim-guard.ts; do
    backup "$OPENCODE_PLUGIN_DIR/$p"
    cp "./opencode/plugins/$p" "$OPENCODE_PLUGIN_DIR/$p"
done
mkdir -p "$OPENCODE_CONFIG_DIR"
touch "$OPENCODE_CONFIG_DIR/instructions.md"
if grep -q '<!-- token-optimizer-pack:start -->' "$OPENCODE_CONFIG_DIR/instructions.md"; then
    echo "    instructions.md already contains the pack block - left as is"
else
    backup "$OPENCODE_CONFIG_DIR/instructions.md"
    { echo ""; echo "<!-- token-optimizer-pack:start -->"; cat ./opencode/instructions.md; echo "<!-- token-optimizer-pack:end -->"; } >> "$OPENCODE_CONFIG_DIR/instructions.md"
    echo "    appended a marked block to instructions.md"
fi

echo ""
echo "[3/5] Antigravity plugins"
for name in rtk docslim; do
    mkdir -p "$AGY_PLUGINS_BASE/$name/rules"
    cp "./antigravity/plugins/$name/plugin.json" "$AGY_PLUGINS_BASE/$name/plugin.json"
    cp "./antigravity/plugins/$name/rules/AGENTS.md" "$AGY_PLUGINS_BASE/$name/rules/AGENTS.md"
done

RTK_BIN="$(command -v rtk || true)"
if [ -n "$RTK_BIN" ]; then
    cp ./antigravity/plugins/rtk/hooks.json "$AGY_PLUGINS_BASE/rtk/hooks.json"
    echo "    rtk hook enabled ($RTK_BIN)"
else
    rm -f "$AGY_PLUGINS_BASE/rtk/hooks.json"
    echo "    rtk hook SKIPPED - install rtk first, a hook without it blocks every command"
fi
# The docslim MCP server is defined once, in the global config.
rm -f "$AGY_PLUGINS_BASE/docslim/mcp_config.json"

echo ""
echo "[4/5] Global MCP config and rules (merged, not replaced)"
MCP_FILE="$HOME/.gemini/config/mcp_config.json"
backup "$MCP_FILE"
if [ -n "$PYTHON" ]; then
    DOCSLIM_PY="$DOCSLIM_DIR/docslim.py" MCP_FILE="$MCP_FILE" "$PYTHON" - <<'PY'
import json, os
path = os.environ["MCP_FILE"]
try:
    with open(path, encoding="utf-8") as fh:
        cfg = json.load(fh)
except Exception:
    cfg = {}
servers = cfg.setdefault("mcpServers", {})
servers["docslim"] = {
    "command": os.environ.get("DOCSLIM_PYTHON") or os.sys.executable,
    "args": [os.environ["DOCSLIM_PY"], "serve", "--mcp"],
}
with open(path, "w", encoding="utf-8") as fh:
    json.dump(cfg, fh, indent=4)
    fh.write("\n")
PY
fi
touch "$HOME/.gemini/config/GEMINI.md"
if grep -q '<!-- token-optimizer-pack:start -->' "$HOME/.gemini/config/GEMINI.md"; then
    echo "    GEMINI.md already contains the pack block - left as is"
else
    backup "$HOME/.gemini/config/GEMINI.md"
    { echo ""; echo "<!-- token-optimizer-pack:start -->"; cat ./antigravity/config-snippets/GEMINI.md; echo "<!-- token-optimizer-pack:end -->"; } >> "$HOME/.gemini/config/GEMINI.md"
    echo "    appended the rules block to GEMINI.md"
fi

echo ""
echo "[5/5] Enable plugins and verify"
CFG_FILE="$HOME/.gemini/config/config.json"
backup "$CFG_FILE"
if [ -n "$PYTHON" ]; then
    CFG_FILE="$CFG_FILE" "$PYTHON" - <<'PY'
import json, os
path = os.environ["CFG_FILE"]
try:
    with open(path, encoding="utf-8") as fh:
        cfg = json.load(fh)
except Exception:
    cfg = {}
plugins = cfg.setdefault("plugins", {})
for name in ("rtk", "docslim"):
    entry = plugins.get(name)
    if not isinstance(entry, dict):
        entry = {}
    entry["enabled"] = True
    plugins[name] = entry
with open(path, "w", encoding="utf-8") as fh:
    json.dump(cfg, fh, indent=4)
    fh.write("\n")
PY

    "$PYTHON" - <<'PY'
import json, os, subprocess, sys
script = os.path.expanduser("~/.gemini/config/tools/docslim/docslim.py")
req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                  "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                             "clientInfo": {"name": "probe", "version": "1"}}}) + "\n"
r = subprocess.run([sys.executable, script, "serve", "--mcp"], input=req.encode(), capture_output=True, timeout=20)
ok = b'"result"' in r.stdout
print("    docslim MCP handshake:", "OK" if ok else "FAILED")
sys.exit(0 if ok else 1)
PY
fi

# Manifest schema check: plugin.json v1 allows only name and description.
"$PYTHON" - <<'PY'
import json, os, sys
base = os.path.expanduser("~/.gemini/config/plugins")
bad = 0
for name in ("rtk", "docslim"):
    path = os.path.join(base, name, "plugin.json")
    if not os.path.exists(path):
        continue
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    extra = [k for k in data if k not in ("name", "description")]
    if extra:
        print(f"    {name}/plugin.json has unsupported fields: {', '.join(extra)}")
        bad += 1
sys.exit(1 if bad else 0)
PY

echo ""
echo "Done. Restart OpenCode and Antigravity."
echo "Rollback: restore the *.bak-$TS files."
