# ============================================================
#  Missing Persons AI — Full Setup Script (Windows)
#  Run this ONCE to upgrade pip and install all dependencies.
# ============================================================

Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser -Force

$PY = "C:\Program Files\Python39\python.exe"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Missing Persons AI — Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Upgrade pip ───────────────────────────────────────
Write-Host "[1/3] Upgrading pip..." -ForegroundColor Yellow
& $PY -m pip install --upgrade pip
Write-Host "pip upgraded successfully." -ForegroundColor Green
Write-Host ""

# ── Step 2: Install dependencies ─────────────────────────────
Write-Host "[2/3] Installing project dependencies..." -ForegroundColor Yellow
& $PY -m pip install -r requirements.txt
Write-Host "Dependencies installed." -ForegroundColor Green
Write-Host ""

# ── Step 3: Generate hashed passwords ────────────────────────
Write-Host "[3/3] Generating secure password hashes..." -ForegroundColor Yellow
& $PY generate_passwords.py
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup complete! Run the app with:" -ForegroundColor Green
Write-Host "  .\run_desktop_app.ps1" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Pause
