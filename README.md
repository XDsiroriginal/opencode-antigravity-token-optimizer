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
| **CodeGraph MCP** | OpenCode & Antigravity | **-50% to -70%** | Pre-indexes codebase AST & call-graph. Replaces 30+ grep/read cycles with a single surgical query. |
| **OpenSlimedit** | OpenCode | **-25% to -45%** | Strips verbose tool descriptions and enables line-range editing (`"55-64"`). |
| **Dynamic Context Pruning (DCP)** | OpenCode | **-30% to -50%** | Prunes stale tool outputs from conversation history. |

---

## 🔒 Always-On by Default

All components in this pack are engineered to be **permanently enabled by default**:
* **OpenCode (CLI & Desktop):** 
  * In-process TypeScript hooks (`rtk.ts`, `docslim-guard.ts`) are placed in `~/.config/opencode/plugins/` and automatically executed upon engine startup.
  * Directory junctions bridge `~/.opencode` and `%APPDATA%\opencode` to `~/.config/opencode`, guaranteeing identical behavior in OpenCode Desktop.
* **Google Antigravity:** 
  * Plugins (`rtk`, `docslim`) are explicitly registered with `"enabled": true` in `~/.gemini/config/config.json`.
  * MCP servers (`docslim`, `codegraph`) run automatically in background on agent invocation.

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
Clone this repository and run the automated installer:

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

## 📄 License
MIT License. Created for high-efficiency AI agent pairing.
