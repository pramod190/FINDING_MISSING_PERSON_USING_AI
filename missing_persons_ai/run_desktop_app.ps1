# ============================================================
#  Missing Persons AI — Desktop App Launcher
# ============================================================

Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser -Force

$PY = "C:\Program Files\Python39\python.exe"

# Silence pip upgrade warning
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Missing Persons AI - Desktop App" -ForegroundColor Green
Write-Host "  http://localhost:8501" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

& $PY -m streamlit run Home.py --server.port 8501
