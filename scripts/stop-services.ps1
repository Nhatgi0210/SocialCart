<#
.SYNOPSIS
    Dừng tất cả service SocialCart đang chạy (theo PID file).
#>
$RepoRoot = $PSScriptRoot | Split-Path -Parent
$PidDir   = Join-Path $RepoRoot "logs\pids"

if (-not (Test-Path $PidDir)) {
    Write-Host "Không có PID file nào — không có service nào cần dừng."
    exit 0
}

Get-ChildItem -Path $PidDir -Filter "*.pid" | ForEach-Object {
    $svc  = $_.BaseName
    $pidStr = Get-Content $_.FullName -Raw
    try {
        $pid = [int]$pidStr.Trim()
        Stop-Process -Id $pid -Force -ErrorAction Stop
        Write-Host "[$svc] Đã dừng (PID $pid)"
    } catch {
        Write-Warning "[$svc] PID $pidStr không còn tồn tại"
    }
    Remove-Item $_.FullName -Force
}

Write-Host "Hoàn tất."
