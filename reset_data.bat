@echo off
REM ThreatIQ Database & Telemetry Reset Script
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe scripts\refresh_all_data.py %*
) else (
    python scripts\refresh_all_data.py %*
)
pause
