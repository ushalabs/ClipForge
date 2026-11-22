@echo off
title ClipForge
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-windows.ps1"
if errorlevel 1 (
    echo.
    echo   ClipForge could not start. Press any key to close this window.
    pause >nul
)
