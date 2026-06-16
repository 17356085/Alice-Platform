@echo off
cd /d "%~dp0"
echo ========== ZJSN Smoke Tests ==========
python -m pytest -m smoke -v --tb=short %*
exit /b %ERRORLEVEL%
