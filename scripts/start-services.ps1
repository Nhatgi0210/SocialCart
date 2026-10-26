<#
.SYNOPSIS
    Khởi động các service SocialCart backend ở background với log và PID tracking.

.DESCRIPTION
    Chạy từ root repository.
    Dùng: .\scripts\start-services.ps1 [-Milestone M0]
    
    M0: api-gateway, auth-service
    M1: + conversation-service, customer-service, realtime-service
    M2: + product-service, order-service
    (M3+ cần INT-01 và EXT credentials)

    Log: logs/<service-name>.log
    PID: logs/pids/<service-name>.pid

    Dừng: .\scripts\stop-services.ps1 (hoặc Ctrl+C nếu chạy foreground)

.PARAMETER Milestone
    Mốc triển khai: M0, M1, M2 (mặc định M0)

.PARAMETER Service
    Chạy một service cụ thể theo tên (e.g. auth-service)
#>
param(
    [ValidateSet("M0","M1","M2")]
    [string]$Milestone = "M0",
    [string]$Service = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = $PSScriptRoot | Split-Path -Parent
$LogDir   = Join-Path $RepoRoot "logs"
$PidDir   = Join-Path $LogDir "pids"
$VenvPy   = Join-Path $RepoRoot ".venv\Scripts\python.exe"

# Kiểm tra venv
if (-not (Test-Path $VenvPy)) {
    Write-Error "Không tìm thấy .venv. Chạy: py -3.11 -m venv .venv && .venv\Scripts\python -m pip install -r backend/requirements-dev.txt"
    exit 1
}

New-Item -ItemType Directory -Force -Path $LogDir  | Out-Null
New-Item -ItemType Directory -Force -Path $PidDir  | Out-Null

# Mapping service → port
$ServiceMap = [ordered]@{
    "api-gateway"           = 8000
    "auth-service"          = 8001
    "conversation-service"  = 8002
    "customer-service"      = 8003
    "product-service"       = 8004
    "order-service"         = 8005
    "ai-service"            = 8006
    "webhook-service"       = 8007
    "dashboard-service"     = 8008
    "realtime-service"      = 8009
    "platform-service"      = 8010
}

# Services theo mốc
$MilestoneServices = @{
    "M0" = @("api-gateway", "auth-service")
    "M1" = @("api-gateway", "auth-service", "conversation-service", "customer-service", "realtime-service")
    "M2" = @("api-gateway", "auth-service", "conversation-service", "customer-service", "product-service", "order-service", "realtime-service")
}

$ToStart = if ($Service) { @($Service) } else { $MilestoneServices[$Milestone] }

foreach ($svc in $ToStart) {
    $SvcDir = Join-Path $RepoRoot "backend\$svc"
    if (-not (Test-Path (Join-Path $SvcDir "app\main.py"))) {
        Write-Warning "[$svc] app/main.py chưa tồn tại — bỏ qua (task BOOT chưa scaffold)"
        continue
    }

    $port    = $ServiceMap[$svc]
    $logFile = Join-Path $LogDir "$svc.log"
    $pidFile = Join-Path $PidDir "$svc.pid"

    # Kiểm tra đã chạy chưa
    if (Test-Path $pidFile) {
        $oldPid = Get-Content $pidFile -Raw
        try {
            $proc = Get-Process -Id ([int]$oldPid.Trim()) -ErrorAction Stop
            Write-Host "[$svc] Đã chạy (PID $($proc.Id)) — bỏ qua"
            continue
        } catch {
            Remove-Item $pidFile -Force
        }
    }

    $env_PYTHONPATH = Join-Path $RepoRoot "backend"

    $startArgs = @{
        FilePath         = $VenvPy
        ArgumentList     = @(
            "-m", "uvicorn", "app.main:app",
            "--app-dir", $SvcDir,
            "--host", "127.0.0.1",
            "--port", "$port",
            "--reload"
        )
        WindowStyle      = "Hidden"
        PassThru         = $true
        RedirectStandardOutput = $logFile
        RedirectStandardError  = $logFile
    }

    # Set PYTHONPATH cho process
    $envBlock = [System.Environment]::GetEnvironmentVariables()
    $envBlock["PYTHONPATH"] = $env_PYTHONPATH

    $proc = Start-Process @startArgs
    $proc.Id | Out-File -FilePath $pidFile -Encoding ascii -Force
    Write-Host "[$svc] Khởi động PID $($proc.Id) port $port — log: logs\$svc.log"
}

Write-Host ""
Write-Host "Dừng services: .\scripts\stop-services.ps1"
Write-Host "Kiểm tra health: Invoke-WebRequest http://127.0.0.1:8000/health"
