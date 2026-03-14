# ============================================================
#  Missing Persons AI — Mobile/Public Submission App
# ============================================================

Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser -Force

$PY = "C:\Program Files\Python39\python.exe"

# Silence pip upgrade warning
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Missing Persons AI - Mobile App" -ForegroundColor Cyan
Write-Host "  http://localhost:8502" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

& $PY -m streamlit run mobile_app.py --server.port 8502
