# Automated Installer for AI Token Optimizer Pack (OpenCode & Antigravity)
# Supports Windows (PowerShell)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Installing AI Token Optimizer Pack (OpenCode & AGY)     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$npmDir = "$env:APPDATA\npm"
$docslimDir = "$HOME\.gemini\config\tools\docslim"
$opencodePluginDir = "$HOME\.config\opencode\plugins"
$agyPluginDir = "$HOME\.gemini\config\plugins\rtk"

# 1. Install DocSlim CLI & MCP
Write-Host "[1/5] Installing DocSlim CLI and MCP Server..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $docslimDir -Force | Out-Null
Copy-Item ".\docslim\docslim.py" "$docslimDir\docslim.py" -Force
Copy-Item ".\docslim\docslim.cmd" "$npmDir\docslim.cmd" -Force

# 2. OpenCode Plugins (In-Process)
Write-Host "[2/5] Installing OpenCode Plugins (RTK & DocSlim Guard)..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $opencodePluginDir -Force | Out-Null
Copy-Item ".\opencode\plugins\rtk.ts" "$opencodePluginDir\rtk.ts" -Force
Copy-Item ".\opencode\plugins\docslim-guard.ts" "$opencodePluginDir\docslim-guard.ts" -Force

# 3. Antigravity Plugins (RTK Plugin Bundle)
Write-Host "[3/5] Installing Antigravity Plugins..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "$agyPluginDir\rules" -Force | Out-Null
Copy-Item ".\antigravity\plugins\rtk\plugin.json" "$agyPluginDir\plugin.json" -Force
Copy-Item ".\antigravity\plugins\rtk\hooks.json" "$agyPluginDir\hooks.json" -Force
Copy-Item ".\antigravity\plugins\rtk\rules\AGENTS.md" "$agyPluginDir\rules\AGENTS.md" -Force
Copy-Item ".\antigravity\config-snippets\GEMINI.md" "$HOME\.gemini\config\GEMINI.md" -Force

# 4. Global Junctions for OpenCode Desktop
Write-Host "[4/5] Configuring OpenCode Desktop Junctions..." -ForegroundColor Yellow
if (-not (Test-Path "$HOME\.opencode")) { New-Item -ItemType Junction -Path "$HOME\.opencode" -Target "$HOME\.config\opencode" -Force | Out-Null }
if (-not (Test-Path "$env:APPDATA\opencode")) { New-Item -ItemType Junction -Path "$env:APPDATA\opencode" -Target "$HOME\.config\opencode" -Force | Out-Null }

# 5. MCP Configurations
Write-Host "[5/5] Updating MCP configuration for Antigravity & OpenCode..." -ForegroundColor Yellow
$mcpTarget = "$HOME\.gemini\config\mcp_config.json"
Copy-Item ".\antigravity\config-snippets\mcp_config.json" $mcpTarget -Force

Write-Host "`n✓ Token Optimizer Pack installed successfully!" -ForegroundColor Green
Write-Host "Restart OpenCode (CLI/Desktop) and Antigravity to take full effect." -ForegroundColor Green
