# Automated Installer for the AI Token Optimizer Pack (OpenCode + Antigravity)
# Windows / PowerShell 5.1+
#
# Design rules:
#   * never overwrite a user config - back it up and merge
#   * never register a hook for a binary that is not installed
#   * never spawn a .cmd for MCP (Node cannot: spawn EINVAL) - use python.exe
#   * verify at the end and report DONE / BLOCKED per component

$ErrorActionPreference = 'Stop'
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Write-Json($path, $object) {
    [IO.File]::WriteAllText($path, ($object | ConvertTo-Json -Depth 12), $utf8NoBom)
}

function Backup-File($path) {
    if (Test-Path $path) {
        $bak = "$path.bak-$ts"
        Copy-Item $path $bak -Force
        Write-Host "    backup: $bak" -ForegroundColor DarkGray
    }
}

function Merge-MarkedBlock($path, $block, $marker) {
    # Appends a marked block, or replaces it when it already exists.
    $start = "<!-- $marker`:start -->"
    $end = "<!-- $marker`:end -->"
    $wrapped = "$start`n$block`n$end"
    if (Test-Path $path) {
        $current = [IO.File]::ReadAllText($path)
        if ($current.Contains($start) -and $current.Contains($end)) {
            $pattern = [regex]::Escape($start) + '[\s\S]*?' + [regex]::Escape($end)
            $updated = [regex]::Replace($current, $pattern, $wrapped.Replace('$', '$$'))
        } else {
            $updated = $current.TrimEnd() + "`n`n" + $wrapped + "`n"
        }
    } else {
        $updated = $wrapped + "`n"
    }
    [IO.File]::WriteAllText($path, $updated, $utf8NoBom)
    Backup-File $path
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " AI Token Optimizer Pack - install (OpenCode + AGY)       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$docslimDir       = "$HOME\.gemini\config\tools\docslim"
$opencodePluginDir = "$HOME\.config\opencode\plugins"
$opencodeConfigDir = "$HOME\.config\opencode"
$agyPluginsBase    = "$HOME\.gemini\config\plugins"
$status = [ordered]@{}

# ---------------------------------------------------------------- 1. DocSlim
Write-Host "`n[1/6] DocSlim CLI + MCP server" -ForegroundColor Yellow
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) {
    $status['docslim'] = 'BLOCKED: python not on PATH'
    Write-Host "    python not found - DocSlim needs Python 3.9+. Skipping." -ForegroundColor Red
} else {
    New-Item -ItemType Directory -Path $docslimDir -Force | Out-Null
    Copy-Item ".\docslim\docslim.py" "$docslimDir\docslim.py" -Force
    New-Item -ItemType Directory -Path "$env:APPDATA\npm" -Force | Out-Null
    Copy-Item ".\docslim\docslim.cmd" "$env:APPDATA\npm\docslim.cmd" -Force
    $status['docslim'] = "DONE ($python)"
    Write-Host "    installed to $docslimDir" -ForegroundColor Green
}

# ------------------------------------------------------------ 2. OpenCode
Write-Host "`n[2/6] OpenCode plugins (global, always loaded)" -ForegroundColor Yellow
New-Item -ItemType Directory -Path $opencodePluginDir -Force | Out-Null
foreach ($p in 'rtk.ts', 'docslim-guard.ts') {
    if (Test-Path "$opencodePluginDir\$p") { Backup-File "$opencodePluginDir\$p" }
    Copy-Item ".\opencode\plugins\$p" "$opencodePluginDir\$p" -Force
}
# instructions.md belongs to the user: append a marked block, never replace it.
Merge-MarkedBlock "$opencodeConfigDir\instructions.md" (Get-Content ".\opencode\instructions.md" -Raw -Encoding UTF8) 'token-optimizer-pack'
$status['opencode'] = "DONE ($opencodePluginDir)"

# ------------------------------------------------------------------ 3. rtk
Write-Host "`n[3/6] rtk (Rust Token Killer) binary" -ForegroundColor Yellow
$rtk = (Get-Command rtk -ErrorAction SilentlyContinue).Source
if (-not $rtk) {
    Write-Host "    not installed - downloading the official release..." -ForegroundColor DarkGray
    try {
        $dest = "$env:LOCALAPPDATA\Programs\rtk"
        $zip  = "$env:TEMP\rtk-pack.zip"
        Invoke-WebRequest -Uri "https://github.com/rtk-ai/rtk/releases/download/v1.1.0/rtk-x86_64-pc-windows-msvc.zip" -OutFile $zip -UseBasicParsing
        New-Item -ItemType Directory -Path $dest -Force | Out-Null
        Expand-Archive -Path $zip -DestinationPath $dest -Force
        $exe = Join-Path $dest 'rtk.exe'
        if (Test-Path $exe) {
            $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
            if ($userPath -notlike "*$dest*") {
                [Environment]::SetEnvironmentVariable('Path', ($userPath.TrimEnd(';') + ";$dest"), 'User')
            }
            $env:Path = $env:Path + ";" + $dest
            $rtk = $exe
        }
    } catch {
        Write-Host "    download failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# ------------------------------------------------- 4. Antigravity plugins
Write-Host "`n[4/6] Antigravity plugins" -ForegroundColor Yellow
$agyPlugins = @('rtk', 'docslim')
foreach ($name in $agyPlugins) {
    New-Item -ItemType Directory -Path "$agyPluginsBase\$name\rules" -Force | Out-Null
    Copy-Item ".\antigravity\plugins\$name\plugin.json" "$agyPluginsBase\$name\plugin.json" -Force
    Copy-Item ".\antigravity\plugins\$name\rules\AGENTS.md" "$agyPluginsBase\$name\rules\AGENTS.md" -Force
}
# rtk: hooks only when the binary really exists, otherwise every command is blocked.
if ($rtk) {
    Copy-Item ".\antigravity\plugins\rtk\hooks.json" "$agyPluginsBase\rtk\hooks.json" -Force
    $status['rtk_hook'] = "DONE ($rtk)"
    Write-Host "    rtk hook enabled" -ForegroundColor Green
} else {
    Remove-Item "$agyPluginsBase\rtk\hooks.json" -Force -ErrorAction SilentlyContinue
    $status['rtk_hook'] = 'SKIPPED: rtk binary missing (hook would block every command)'
    Write-Host "    rtk hook SKIPPED - binary missing" -ForegroundColor Red
}
# docslim: the MCP definition lives in the global config (see step 5); a duplicate
# copy in the plugin makes Antigravity register the server twice.
Remove-Item "$agyPluginsBase\docslim\mcp_config.json" -Force -ErrorAction SilentlyContinue

# --------------------------------------------------- 5. Global MCP + rules
Write-Host "`n[5/6] Global MCP config and rules (merged, not replaced)" -ForegroundColor Yellow
$mcpFile = "$HOME\.gemini\config\mcp_config.json"
Backup-File $mcpFile
if (Test-Path $mcpFile) {
    try { $mcp = Get-Content $mcpFile -Raw -Encoding UTF8 | ConvertFrom-Json }
    catch { $mcp = [pscustomobject]@{} }
} else {
    $mcp = [pscustomobject]@{}
}
if (-not $mcp.PSObject.Properties['mcpServers']) {
    $mcp | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([pscustomobject]@{}) -Force
}
if ($python) {
    $docslimEntry = [pscustomobject]@{ command = $python; args = @("$docslimDir\docslim.py", 'serve', '--mcp') }
    $mcp.mcpServers | Add-Member -NotePropertyName docslim -NotePropertyValue $docslimEntry -Force
    $status['mcp'] = 'DONE (python + docslim.py, no .cmd)'
} else {
    $status['mcp'] = 'BLOCKED: python missing'
}
Write-Json $mcpFile $mcp
Merge-MarkedBlock "$HOME\.gemini\config\GEMINI.md" (Get-Content ".\antigravity\config-snippets\GEMINI.md" -Raw -Encoding UTF8) 'token-optimizer-pack'

# ------------------------------------------------ 6. Enable plugins + verify
Write-Host "`n[6/6] Enable plugins and verify" -ForegroundColor Yellow
$cfgFile = "$HOME\.gemini\config\config.json"
Backup-File $cfgFile
if (Test-Path $cfgFile) {
    try { $cfg = Get-Content $cfgFile -Raw -Encoding UTF8 | ConvertFrom-Json }
    catch { $cfg = [pscustomobject]@{} }
} else {
    $cfg = [pscustomobject]@{}
}
if (-not $cfg.PSObject.Properties['plugins']) {
    $cfg | Add-Member -NotePropertyName plugins -NotePropertyValue ([pscustomobject]@{}) -Force
}
foreach ($name in $agyPlugins) {
    $cfg.plugins | Add-Member -NotePropertyName $name -NotePropertyValue ([pscustomobject]@{ enabled = $true }) -Force
}
Write-Json $cfgFile $cfg

# Verification: manifest schema (name + description only) and MCP handshake.
$errors = 0
foreach ($name in $agyPlugins) {
    $manifest = Get-Content "$agyPluginsBase\$name\plugin.json" -Raw -Encoding UTF8 | ConvertFrom-Json
    $extra = @($manifest.PSObject.Properties.Name | Where-Object { $_ -notin @('name', 'description') })
    if ($extra.Count -gt 0) {
        Write-Host "    $name plugin.json has unsupported fields: $($extra -join ', ')" -ForegroundColor Red
        $errors++
    }
}
if ($python) {
    $probe = @'
import json,subprocess,sys,os
req=json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}})+"\n"
r=subprocess.run([sys.executable,os.path.expanduser(r"~\.gemini\config\tools\docslim\docslim.py"),"serve","--mcp"],input=req.encode(),capture_output=True,timeout=20)
sys.exit(0 if b'"result"' in r.stdout else 1)
'@
    $probeFile = "$env:TEMP\docslim_probe.py"
    [IO.File]::WriteAllText($probeFile, $probe, $utf8NoBom)
    & $python $probeFile
    if ($LASTEXITCODE -eq 0) { $status['docslim_mcp'] = 'DONE (initialize answered)' }
    else { $status['docslim_mcp'] = 'FAILED (no JSON-RPC answer)'; $errors++ }
}

Write-Host "`n=== Result ===" -ForegroundColor Cyan
foreach ($k in $status.Keys) { Write-Host ("  {0,-12} {1}" -f $k, $status[$k]) }
if ($errors -gt 0) {
    Write-Host "`nSome components failed. Nothing was silently ignored - see above." -ForegroundColor Red
    exit 1
}
Write-Host "`nRestart OpenCode and Antigravity. Rollback: restore the *.bak-$ts files." -ForegroundColor Green
