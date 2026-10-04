Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$layaLauncher = Join-Path $root 'laya-engine\JARVIS Laya Engine.vbs'
$frontDoorDir = Join-Path $root 'jarvis-frontdoor'
$frontDoorScript = Join-Path $frontDoorDir 'server.py'

function Test-LocalPort([int]$Port) {
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $result = $client.BeginConnect('127.0.0.1', $Port, $null, $null)
        if (-not $result.AsyncWaitHandle.WaitOne(500)) { return $false }
        $client.EndConnect($result)
        return $true
    } catch {
        return $false
    } finally {
        $client.Dispose()
    }
}

function Wait-ForLocalPort([int]$Port, [int]$Seconds) {
    $until = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $until) {
        if (Test-LocalPort $Port) { return $true }
        Start-Sleep -Milliseconds 500
    }
    return (Test-LocalPort $Port)
}

Write-Host 'Starting JARVIS from the canonical my-agent installation.' -ForegroundColor Cyan

if (-not (Test-Path -LiteralPath $layaLauncher)) {
    throw "Laya launcher not found: $layaLauncher"
}
if (-not (Test-Path -LiteralPath $frontDoorScript)) {
    throw "Front Door not found: $frontDoorScript"
}

if (-not (Test-LocalPort 8090)) {
    Start-Process -FilePath 'wscript.exe' -ArgumentList ('"{0}"' -f $layaLauncher) -WindowStyle Hidden
}
if (-not (Wait-ForLocalPort 8090 30)) {
    throw 'Laya did not start on 127.0.0.1:8090. No duplicate server was launched.'
}

$layaHealth = Invoke-RestMethod -Uri 'http://127.0.0.1:8090/health' -TimeoutSec 5
if (-not $layaHealth.ok -or $layaHealth.engine -ne 'laya (real)') {
    throw 'Port 8090 is responding, but it is not the expected JARVIS Laya service.'
}
Write-Host 'Laya is responding on port 8090.' -ForegroundColor Green

if (-not (Test-LocalPort 4719)) {
    Start-Process -FilePath 'python' -ArgumentList @('-u', $frontDoorScript) -WorkingDirectory $frontDoorDir -WindowStyle Normal
}
if (-not (Wait-ForLocalPort 4719 15)) {
    throw 'JARVIS Front Door did not start on 127.0.0.1:4719.'
}

$frontHealth = Invoke-RestMethod -Uri 'http://127.0.0.1:4719/health' -TimeoutSec 5
if (-not $frontHealth.ok) {
    throw 'Port 4719 is responding, but the JARVIS Front Door health check failed.'
}
Write-Host ("JARVIS Front Door is healthy; {0} notes indexed." -f $frontHealth.notes_indexed) -ForegroundColor Green

if (-not $env:OPENROUTER_API_KEY) {
    Write-Host 'OpenRouter routing is disabled; JARVIS will use its local Laya fallback.' -ForegroundColor Yellow
}
Start-Process 'http://127.0.0.1:4719'
Write-Host 'JARVIS is ready at http://127.0.0.1:4719' -ForegroundColor Cyan
