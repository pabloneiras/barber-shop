@echo off
setlocal enabledelayedexpansion
title Barber Shop Launcher
echo ========================================================
echo   BARBER SHOP - SISTEMA DE CITAS Y RECORDATORIOS
echo ========================================================
echo.

cd /d "%~dp0"
set PYTHONPATH=backend\src

REM 1. Verificar o preparar entorno de Python
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    echo [*] Detectando Python del sistema...
    where python >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] No se ha encontrado Python en el sistema.
        echo Instala Python 3.11 o superior para ejecutar la aplicacion.
        pause
        exit /b 1
    )
    echo [*] Creando entorno virtual local (.venv)...
    python -m venv .venv
    if exist ".venv\Scripts\python.exe" (
        set "PYTHON_EXE=.venv\Scripts\python.exe"
        echo [*] Instalando dependencias desde requirements.txt...
        "%PYTHON_EXE%" -m pip install -r requirements.txt
    ) else (
        set "PYTHON_EXE=python"
    )
)

REM 2. Verificar si el frontend esta compilado en frontend/dist
if not exist "frontend\dist\index.html" (
    echo [*] Frontend no compilado. Construyendo paquetes por primera vez...
    where npm >nul 2>nul
    if %errorlevel% equ 0 (
        cd frontend
        if not exist "node_modules" (
            echo [*] Instalando paquetes de frontend (npm install)...
            call npm install
        )
        echo [*] Generando build de produccion (npm run build)...
        call npm run build
        cd ..
    ) else (
        echo [AVISO] Node/npm no detectado. El servidor se iniciara en modo API.
    )
)

REM 3. Iniciar la aplicacion y abrir navegador
echo.
echo [*] Abriendo aplicacion en http://localhost:8000 ...
start "" http://localhost:8000

echo [*] Servidor en ejecucion. Pulsa Ctrl+C para detener.
echo ========================================================
"%PYTHON_EXE%" -m uvicorn api.api:app --host 127.0.0.1 --port 8000
pause
