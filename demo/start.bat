@echo off
chcp 65001 >nul
title AITest Platform Demo — v0.5

echo.
echo ============================================================
echo   AITest Platform v0.5 — Demo Quick Start
echo ============================================================
echo.
echo   [1/3] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)
echo   [OK]   Python found

echo   [2/3] Checking trace seed data...
if exist "governance\.traces\trace_log.jsonl" (
    echo   [OK]   Trace data exists
) else (
    echo   [INFO] Generating seed trace data...
    python demo\seed_traces.py
)

echo   [3/3] Starting AITest Platform server...
echo.
echo   Dashboard:   http://localhost:8000
echo   Chat:        http://localhost:8000/chat
echo   Trace:       http://localhost:8000/trace
echo   Governance:  http://localhost:8000/governance
echo   API Docs:    http://localhost:8000/docs
echo.
echo   Press Ctrl+C to stop.
echo ============================================================
echo.

start "" http://localhost:8000

aitest server start --port 8000

pause
