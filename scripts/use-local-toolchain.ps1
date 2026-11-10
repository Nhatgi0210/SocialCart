# Dot-source: . .\scripts\use-local-toolchain.ps1
# Only changes PATH in this terminal; never changes the machine-wide toolchain.
$taskRepo = Split-Path -Parent $PSScriptRoot
$env:PYTHONUTF8 = '1'
$taskNodeVersion = (Get-Content -LiteralPath (Join-Path $taskRepo '.node-version') -Raw).Trim()
$taskNodeDir = Join-Path $taskRepo ".cache/toolchain/node-v$taskNodeVersion-win-x64"
if (Test-Path -LiteralPath (Join-Path $taskNodeDir 'node.exe')) {
    $env:PATH = $taskNodeDir + ';' + $env:PATH
}
$taskVenvDir = Join-Path $taskRepo '.venv/Scripts'
if (-not (Test-Path -LiteralPath (Join-Path $taskVenvDir 'python.exe'))) { throw 'Create .venv with Python 3.11 first (docs/setup.md).' }
$env:PATH = $taskVenvDir + ';' + $env:PATH
if ((node --version) -ne "v$taskNodeVersion") { throw "Install Node $taskNodeVersion; see docs/setup.md" }
python -c "import sys; assert sys.version_info[:2] == (3, 11), 'Python 3.11 required'; print(sys.version.split()[0])"
if ($LASTEXITCODE -ne 0) { throw 'Incorrect Python virtualenv' }
node --version
npm.cmd --version
