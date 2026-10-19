# reset-db.ps1 - Khoi phuc CSDL EShop ve trang thai sach sau khi test Lab 2 (SQLi).
# Dung ban sao luu backend/database.sqlite.bak de ghi de backend/database.sqlite.
# Chay tu thu muc goc eshop-sut:  powershell -ExecutionPolicy Bypass -File Phat/P1_labs/reset-db.ps1

$ErrorActionPreference = 'Stop'
$root   = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
$db     = Join-Path $root 'backend/database.sqlite'
$backup = Join-Path $root 'backend/database.sqlite.bak'

if (-not (Test-Path $backup)) {
    Write-Error "Khong tim thay ban sao luu: $backup. Hay tao bang: Copy-Item '$db' '$backup' TRUOC khi test."
    exit 1
}

# Dung backend truoc khi reset de tranh file dang bi khoa (neu dang chay thi tat tay).
Copy-Item -Path $backup -Destination $db -Force
Write-Host "Da khoi phuc database.sqlite tu database.sqlite.bak." -ForegroundColor Green
Write-Host "Luu y: khoi dong lai backend (npm start trong backend/) de nap lai CSDL sach."
