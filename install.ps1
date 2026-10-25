# Automated Installer for AI Token Optimizer Pack (OpenCode & Antigravity)
# Supports Windows (PowerShell)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Installing AI Token Optimizer Pack (OpenCode & AGY)     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$npmDir = "$env:APPDATA\npm"
$docslimDir = "$HOME\.gemini\config\tools\docslim"
$opencodePluginDir = "$HOME\.config\opencode\plugins"
$agyPluginsBase = "$HOME\.gemini\config\plugins"

# 1. Install DocSlim CLI & MCP
Write-Host "[1/6] Installing DocSlim CLI and MCP Server..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $docslimDir -Force | Out-Null
Copy-Item ".\docslim\docslim.py" "$docslimDir\docslim.py" -Force
Copy-Item ".\docslim\docslim.cmd" "$npmDir\docslim.cmd" -Force

# 2. OpenCode Plugins (In-Process)
Write-Host "[2/6] Installing OpenCode In-Process Plugins (RTK & DocSlim Guard)..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $opencodePluginDir -Force | Out-Null
Copy-Item ".\opencode\plugins\rtk.ts" "$opencodePluginDir\rtk.ts" -Force
Copy-Item ".\opencode\plugins\docslim-guard.ts" "$opencodePluginDir\docslim-guard.ts" -Force
Copy-Item ".\opencode\instructions.md" "$HOME\.config\opencode\instructions.md" -Force

# 3. Antigravity Plugins (RTK & DocSlim bundles)
Write-Host "[3/6] Installing Antigravity Plugins (RTK & DocSlim)..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "$agyPluginsBase\rtk\rules" -Force | Out-Null
Copy-Item ".\antigravity\plugins\rtk\plugin.json" "$agyPluginsBase\rtk\plugin.json" -Force
Copy-Item ".\antigravity\plugins\rtk\hooks.json" "$agyPluginsBase\rtk\hooks.json" -Force
Copy-Item ".\antigravity\plugins\rtk\rules\AGENTS.md" "$agyPluginsBase\rtk\rules\AGENTS.md" -Force

New-Item -ItemType Directory -Path "$agyPluginsBase\docslim\rules" -Force | Out-Null
Copy-Item ".\antigravity\plugins\docslim\plugin.json" "$agyPluginsBase\docslim\plugin.json" -Force
Copy-Item ".\antigravity\plugins\docslim\mcp_config.json" "$agyPluginsBase\docslim\mcp_config.json" -Force
Copy-Item ".\antigravity\plugins\docslim\rules\AGENTS.md" "$agyPluginsBase\docslim\rules\AGENTS.md" -Force
Copy-Item ".\antigravity\config-snippets\GEMINI.md" "$HOME\.gemini\config\GEMINI.md" -Force

# 4. Set Always-On by Default in Antigravity config.json
Write-Host "[4/6] Setting plugins enabled by default in Antigravity config..." -ForegroundColor Yellow
$cfgFile = "$HOME\.gemini\config\config.json"
if (Test-Path $cfgFile) {
    try {
        $cfg = Get-Content $cfgFile -Raw | ConvertFrom-Json
    } catch {
        $cfg = [PSCustomObject]@{}
    }
} else {
    $cfg = [PSCustomObject]@{}
}
if (-not $cfg.plugins) {
    $cfg | Add-Member -MemberType NoteProperty -Name "plugins" -Value ([PSCustomObject]@{}) -Force
}
$cfg.plugins | Add-Member -MemberType NoteProperty -Name "rtk" -Value ([PSCustomObject]@{ enabled = $true }) -Force
$cfg.plugins | Add-Member -MemberType NoteProperty -Name "docslim" -Value ([PSCustomObject]@{ enabled = $true }) -Force
$cfg | ConvertTo-Json -Depth 10 | Set-Content -Path $cfgFile -Encoding utf8

# 5. Global Junctions for OpenCode Desktop
Write-Host "[5/6] Configuring OpenCode Desktop Junctions..." -ForegroundColor Yellow
if (-not (Test-Path "$HOME\.opencode")) { New-Item -ItemType Junction -Path "$HOME\.opencode" -Target "$HOME\.config\opencode" -Force | Out-Null }
if (-not (Test-Path "$env:APPDATA\opencode")) { New-Item -ItemType Junction -Path "$env:APPDATA\opencode" -Target "$HOME\.config\opencode" -Force | Out-Null }

# 6. Global MCP Configurations
Write-Host "[6/6] Updating global MCP configuration..." -ForegroundColor Yellow
$mcpTarget = "$HOME\.gemini\config\mcp_config.json"
Copy-Item ".\antigravity\config-snippets\mcp_config.json" $mcpTarget -Force

Write-Host "`n✓ Token Optimizer Pack installed & configured as ALWAYS-ON by default!" -ForegroundColor Green
Write-Host "Restart OpenCode (CLI/Desktop) and Antigravity to take full effect." -ForegroundColor Green
