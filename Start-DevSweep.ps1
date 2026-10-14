[CmdletBinding()]
param(
    [switch]$CheckOnly,
    [switch]$LiveAI,
    [switch]$SkipInstall
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $repoRoot 'backend'
$frontendDir = Join-Path $repoRoot 'frontend'
$python = Join-Path $backendDir '.venv\Scripts\python.exe'
$vite = Join-Path $frontendDir 'node_modules\vite\bin\vite.js'
$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
$npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
$requiredFiles = @(
    (Join-Path $backendDir 'requirements.txt'),
    (Join-Path $frontendDir 'package.json'),
    (Join-Path $frontendDir 'package-lock.json'),
    (Join-Path $repoRoot 'generate_demo.py')
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Required project file is missing: $file" }
}
if (-not $nodeCommand -or -not $npmCommand) { throw 'Node.js and npm are required. Install a supported Node.js LTS release, then reopen PowerShell.' }

$nodeVersionText = (& $nodeCommand.Source --version).TrimStart('v')
$nodeVersion = [version]$nodeVersionText
if ($nodeVersion.Major -lt 18) { throw "Node.js 18 or later is required; found $nodeVersionText." }
Write-Host "Node.js $nodeVersionText detected."

$createdVenv = $false
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    if ($SkipInstall) { throw 'Backend virtual environment is missing. Re-run without -SkipInstall to create it.' }
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pyLauncher) { & $pyLauncher.Source -3 -m venv (Join-Path $backendDir '.venv') }
    elseif ($pythonCommand) { & $pythonCommand.Source -m venv (Join-Path $backendDir '.venv') }
    else { throw 'Python 3.10 or later is required. Install Python and reopen PowerShell.' }
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the backend virtual environment.' }
    $createdVenv = $true
}

$pythonVersion = (& $python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))").Trim()
if ($LASTEXITCODE -ne 0 -or [version]$pythonVersion -lt [version]'3.10') { throw "Python 3.10 or later is required; backend environment reports $pythonVersion." }
Write-Host "Backend Python $pythonVersion detected."

if ($createdVenv) {
    if ($SkipInstall) { throw 'Backend dependencies need installation. Re-run without -SkipInstall.' }
    Write-Host 'Installing backend dependencies from backend/requirements.txt...'
    & $python -m pip install -r (Join-Path $backendDir 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Backend dependency installation failed.' }
}

if (-not (Test-Path -LiteralPath $vite -PathType Leaf)) {
    if ($SkipInstall) { throw 'Frontend dependencies are missing. Re-run without -SkipInstall to install them.' }
    Write-Host 'Installing frontend dependencies from the lockfile...'
    Push-Location $frontendDir
    try { & $npmCommand.Source ci; if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' } }
    finally { Pop-Location }
}

$demoFixture = Join-Path $repoRoot 'demo-project'
if (-not (Test-Path -LiteralPath $demoFixture -PathType Container)) {
    Write-Host 'Creating the isolated synthetic demo fixture...'
    & $python (Join-Path $repoRoot 'generate_demo.py')
    if ($LASTEXITCODE -ne 0) { throw 'Synthetic demo fixture generation failed.' }
}

if ($CheckOnly) {
    Write-Host 'Setup checks passed. No services were started.' -ForegroundColor Green
    return
}

foreach ($port in @(8000, 5173)) {
    $probe = [System.Net.Sockets.TcpClient]::new()
    try {
        $pending = $probe.BeginConnect('127.0.0.1', $port, $null, $null)
        if ($pending.AsyncWaitHandle.WaitOne(250) -and $probe.Connected) {
            throw "Port $port is already in use. Stop the existing DevSweep service or choose another port."
        }
    } finally { $probe.Dispose() }
}

$logDir = Join-Path $env:TEMP 'DevSweepAI'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$backendLog = Join-Path $logDir 'backend.log'
$backendErrorLog = Join-Path $logDir 'backend-error.log'
$frontendLog = Join-Path $logDir 'frontend.log'
$frontendErrorLog = Join-Path $logDir 'frontend-error.log'
$savedEnvironment = @{}
foreach ($name in @('DEVSWEEP_WORKSPACE_ROOT', 'BACKEND_HOST', 'DEVSWEEP_DEMO_MODE', 'NEBIUS_API_KEY')) {
    $savedEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}

$backendProcess = $null
$frontendProcess = $null
try {
    $env:DEVSWEEP_WORKSPACE_ROOT = $repoRoot
    $env:BACKEND_HOST = '127.0.0.1'
    if ($LiveAI) {
        $env:DEVSWEEP_DEMO_MODE = 'false'
        # Leave the key unset in this process so the backend can load the user's
        # private .env configuration. Never print or forward the key to the UI.
        [Environment]::SetEnvironmentVariable('NEBIUS_API_KEY', $null, 'Process')
        Write-Host 'Optional live AI enabled; the backend will read its private local configuration.'
    } else {
        $env:DEVSWEEP_DEMO_MODE = 'true'
        $env:NEBIUS_API_KEY = ''
        Write-Host 'Starting in no-key demo mode. Scanning and deterministic review plans work without external AI.'
    }

    $backendProcess = Start-Process -FilePath $python -ArgumentList @('-m','uvicorn','main:app','--host','127.0.0.1','--port','8000') -WorkingDirectory $backendDir -PassThru -WindowStyle Hidden -RedirectStandardOutput $backendLog -RedirectStandardError $backendErrorLog
    $frontendProcess = Start-Process -FilePath $nodeCommand.Source -ArgumentList @("`"$vite`"",'--host','127.0.0.1') -WorkingDirectory $frontendDir -PassThru -WindowStyle Hidden -RedirectStandardOutput $frontendLog -RedirectStandardError $frontendErrorLog

    $ready = $false
    for ($attempt = 0; $attempt -lt 45; $attempt++) {
        if ($backendProcess.HasExited -or $frontendProcess.HasExited) { break }
        try {
            $null = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 2
            $frontendResponse = Invoke-WebRequest -Uri 'http://127.0.0.1:5173/' -TimeoutSec 2 -UseBasicParsing
            if ($frontendResponse.StatusCode -eq 200) { $ready = $true; break }
        } catch { Start-Sleep -Milliseconds 500 }
    }
    if (-not $ready) {
        Write-Host 'The services did not become ready. Check the private local logs:' -ForegroundColor Red
        Write-Host "  $backendLog"
        Write-Host "  $backendErrorLog"
        Write-Host "  $frontendLog"
        Write-Host "  $frontendErrorLog"
        throw 'DevSweep startup failed.'
    }

    Write-Host ''
    Write-Host 'DevSweep AI is ready at http://127.0.0.1:5173' -ForegroundColor Green
    Write-Host 'Press Ctrl+C in this window to stop both services.'
    Start-Process 'http://127.0.0.1:5173'
    while (-not $backendProcess.HasExited -and -not $frontendProcess.HasExited) { Start-Sleep -Seconds 1 }
    if ($backendProcess.HasExited) { throw "Backend stopped unexpectedly. Check $backendLog" }
    if ($frontendProcess.HasExited) { throw "Frontend stopped unexpectedly. Check $frontendLog" }
} finally {
    foreach ($process in @($frontendProcess, $backendProcess)) {
        if ($null -ne $process -and -not $process.HasExited) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
    }
    foreach ($name in $savedEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($name, $savedEnvironment[$name], 'Process')
    }
}
