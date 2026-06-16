# ZJSN UI 冒烟套件 — 登录 + 各模块「页面可打开」核心用例
# 用法（在项目根目录 ZJSN_Test-master526 下）：
#   powershell -ExecutionPolicy Bypass -File .\run_smoke.ps1
# 可选环境变量：$env:HEADLESS="true"

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "========== ZJSN Smoke Tests ==========" -ForegroundColor Cyan
python -m pytest -m smoke -v --tb=short @args
exit $LASTEXITCODE
