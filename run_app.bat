@echo off
title Barber Shop Launcher
echo ========================================================
echo   BARBER SHOP - SISTEMA DE CITAS Y RECORDATORIOS
echo ========================================================
echo.

cd /d "%~dp0"
set PYTHONPATH=backend\src

REM Verificar si existe el entorno virtual; si no, configurarlo automaticamente
if exist ".venv\Scripts\python.exe" goto start_server

echo [*] Preparando entorno por primera vez...
python -m venv .venv
if errorlevel 1 goto fallback_python

echo [*] Instalando dependencias exactas...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fallback_python

:start_server
set "PYTHON_EXE=.venv\Scripts\python.exe"
goto run

:fallback_python
echo [*] Usando Python del sistema...
set "PYTHON_EXE=python"

:run
REM Abrir navegador tras esperar a que Uvicorn arranque
start "" cmd /c "timeout /t 2 >nul & start http://localhost:8000"

echo [*] Servidor iniciando en http://localhost:8000 ...
echo [*] Pulsa Ctrl+C en esta ventana para detener.
echo ========================================================
echo.

"%PYTHON_EXE%" -m uvicorn api.api:app --host 127.0.0.1 --port 8000

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se pudo iniciar el servidor.
    pause
)
