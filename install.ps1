$ErrorActionPreference = 'Stop'

$Repository = 'https://github.com/sklearner26/agentdac.git'
$Package = 'agentdac'

function Write-Info([string] $Message) { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Ok([string] $Message) { Write-Host "[OK]   $Message" -ForegroundColor Green }

$python = Get-Command py -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $python) { throw 'Python 3.12 or 3.13 is required. Install it from https://python.org' }

$version = & $python.Source -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'
if ($version -notin @('3.12', '3.13')) {
    throw "Python 3.12 or 3.13 is required. Found $version"
}

Write-Info "Installing $Package from PyPI"
& $python.Source -m pip install --upgrade $Package
if ($LASTEXITCODE -ne 0) {
    Write-Info 'PyPI install failed; installing the tagged repository source'
    & $python.Source -m pip install --upgrade "git+$Repository"
}
if ($LASTEXITCODE -ne 0) { throw 'AgentDAC installation failed' }

Write-Ok "AgentDAC installed for Python $version"
Write-Host ''
Write-Host 'Use: from agentdac import AgentDAC'
Write-Host 'Claude Code hook: agentdac-claude-hook'
