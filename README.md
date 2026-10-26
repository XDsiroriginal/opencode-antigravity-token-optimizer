# 🚀 Ultimate AI Token Optimizer Pack (OpenCode & Google Antigravity)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenCode](https://img.shields.io/badge/OpenCode-CLI%20%26%20Desktop-blueviolet.svg)](https://opencode.ai)
[![Google Antigravity](https://img.shields.io/badge/Google-Antigravity%20AGY-blue.svg)](https://antigravity.google)
[![Always On](https://img.shields.io/badge/Configuration-Always--On%20(Default)-brightgreen.svg)](#always-on-by-default)
[![Token Savings](https://img.shields.io/badge/Token%20Savings-Up%20to%2095%25-brightgreen.svg)](#benchmarks)

A production-grade collection of plugins, MCP servers, and in-process hooks designed to **slash LLM token consumption by 60% to 95%** across **OpenCode (CLI & Desktop)** and **Google Antigravity** without losing reasoning accuracy or developer performance.

---

## ⚡ What’s Included in This Pack?

| Component | Target Agent | Token Reduction | Purpose |
|---|---|---|---|
| **DocSlim MCP Server** | OpenCode & Antigravity | **-80% to -95%** | Smart document, web, PDF, table (CSV/XLSX), and image (Vision) token optimizer. |
| **DocSlim Guard Plugin** | OpenCode (In-Process) | **-90%** | Intercepts `curl`, `cat *.csv`, `cat *.pdf` before execution and rewrites them into token-optimized calls. |
| **RTK (Rust Token Killer)** | OpenCode & Antigravity | **-60% to -90%** | Intercepts terminal commands (`git status`, `pytest`, `npm test`, `cargo build`) and condenses output. |
| **CodeGraph MCP** *(optional, not bundled)* | OpenCode & Antigravity | **-50% to -70%** | Pre-indexes codebase AST & call-graph. Replaces 30+ grep/read cycles with a single surgical query. Requires a separate install and an index run; the pack does not ship it. |
| **OpenSlimedit** | OpenCode | **-25% to -45%** | Strips verbose tool descriptions and enables line-range editing (`"55-64"`). |
| **Dynamic Context Pruning (DCP)** | OpenCode | **-30% to -50%** | Prunes stale tool outputs from conversation history. |

---

## 🔒 Always-On by Default

Components are enabled at the **global** scope, so every session loads them:
* **OpenCode (CLI & Desktop):**
  * In-process TypeScript hooks (`rtk.ts`, `docslim-guard.ts`) are placed in
    `~/.config/opencode/plugins/` and loaded at engine startup.
  * `rtk.ts` self-disables with a warning when no `rtk` binary is on `PATH`, so a missing
    binary never breaks a session.
* **Google Antigravity:**
  * Plugins (`rtk`, `docslim`) live in `~/.gemini/config/plugins/<name>/` and are marked
    `"enabled": true` in `~/.gemini/config/config.json`.
  * The `docslim` MCP server is registered **once**, in the global
    `~/.gemini/config/mcp_config.json`, and started as `python .../docslim.py serve --mcp`.
  * `GEMINI.md` tells the agent *when* to call these tools - a registered tool the agent
    never chooses saves nothing.

> ⚠️ The installers **merge** `mcp_config.json`, `config.json`, `GEMINI.md` and
> `instructions.md` (with backups) instead of replacing them. Earlier versions copied
> whole files over the user's config, which silently wiped unrelated MCP servers and SSH
> instructions.


---

## 📊 Benchmarks & Impact

### 1. Web Extraction (`docslim web`)
* **Raw `curl` / HTML dump:** ~42,000 tokens (scripts, CSS, tracking, SVG, navbars)
* **DocSlim Readability Markdown:** ~1,450 tokens (**-96.5% savings**)

### 2. Tabular Data (`docslim table`)
* **Raw CSV read (5,000 rows):** ~65,000 tokens (often blows context)
* **DocSlim Schema + 5 Sample Rows + Type Inference:** ~180 tokens (**-99.7% savings**)

### 3. PDF Documents (`docslim pdf`)
* **Raw PDF extract (30 pages):** ~45,000 tokens (noisy headers/footers)
* **DocSlim Page-Windowed / Query mode:** ~800 tokens (**-98.2% savings**)

### 4. Vision & Images (`docslim image`)
* **Raw 4K / 1080p Screenshot:** ~3,485 vision tokens
* **DocSlim Lanczos Downscaled WebP (1024px):** ~425 vision tokens (**-87.8% savings**)

---

## 🛠️ Quick Installation

### Windows (PowerShell)
Prerequisites: Python 3.9+ on `PATH`, and a restart of both apps afterwards.
The installer backs up every file it touches and merges rather than replaces.

```powershell
git clone https://github.com/XDsiroriginal/opencode-antigravity-token-optimizer.git
cd opencode-antigravity-token-optimizer
.\install.ps1
```

### Linux / macOS (Bash)
```bash
git clone https://github.com/XDsiroriginal/opencode-antigravity-token-optimizer.git
cd opencode-antigravity-token-optimizer
chmod +x install.sh
./install.sh
```

---

## 🔍 Verification

To verify that the MCP servers and plugins are running properly:

```bash
# In OpenCode:
opencode mcp list

# Expected:
# • ✓ codegraph connected
# • ✓ docslim connected
```

To run the verification test suite:

```bash
python docslim/test_docslim.py
```

Expected output:
```text
✓ Web extraction passed!
✓ Table analyzer passed!
✓ PDF reader passed!
✓ Image optimizer passed!
✓ Document outline passed!
✓ MCP Server stdio protocol passed!
ALL 6 DOCSLIM MODULE TESTS PASSED 100%!
```

---

## 🩺 Troubleshooting (symptoms seen in the wild)

These four failures are silent - nothing crashes, the agent just stops acting. All of
them are fixed in this version.

| Symptom | Root cause | Fix |
|---|---|---|
| Antigravity ignores the prompt; every terminal command fails; the agent "does nothing" | `~/.gemini/config/plugins/rtk/hooks.json` runs `rtk hook antigravity` on every `run_command`, but no `rtk` binary exists → the PreToolUse hook exits non-zero and blocks the call | install `rtk`, or delete `hooks.json` (the installer now only writes it when the binary is present) |
| `language_server.log`: `MCP: 1 server(s) still connecting after 30s: docslim` | two causes: (1) Node/Electron cannot spawn `docslim.cmd` (`spawn EINVAL`); (2) newer MCP clients (protocol `2026-07-28`) open with `server/discover`, and DocSlim answered unknown methods with **silence**, so the client waited forever | point the server at `python.exe` + `docslim.py` and answer unknown methods with JSON-RPC `-32601` |
| A plugin was copied into `~/.gemini/config/plugins/` but never loads | `plugin.json` contained `"version"`, which the manifest schema rejects (`additionalProperties: false`) | keep only `name` and `description` |
| Other MCP servers (git, databases, ...) disappeared after installing the pack | the installer overwrote the global `mcp_config.json` | merge, back up, and only touch the `docslim` key |

Diagnose in one command:

```powershell
Get-Content "$env:APPDATA\Antigravity\logs\language_server.log" -Tail 40 |
  Select-String 'MCP|sidecar|error'
```

Also check whether the binary a hook calls actually exists before blaming the model:

```powershell
(Get-Command rtk, python -ErrorAction SilentlyContinue).Source
```

> A registered MCP server is not a used MCP server. Keep the `GEMINI.md` routing rules
> installed, otherwise the agent will keep calling `curl` instead of `smart_read_web`.

---

## 📄 License
MIT License. Created for high-efficiency AI agent pairing.
