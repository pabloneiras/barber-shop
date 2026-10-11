@echo off
title Barber Shop Launcher
echo ========================================================
echo   BARBER SHOP - INICIANDO APLICACION
echo ========================================================
echo.

cd /d "%~dp0"
set PYTHONPATH=backend\src

REM Detect virtual environment
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo Abriendo navegador en http://localhost:8000 ...
start "" http://localhost:8000

echo Iniciando servidor...
"%PYTHON_EXE%" -m uvicorn api.api:app --host 127.0.0.1 --port 8000
pause
