#!/usr/bin/env bash
# Barber Shop - Launcher para Linux y macOS
# 100% Gratuito y sin configuración previa
set -e

cd "$(dirname "$0")"

echo "========================================================"
echo "  BARBER SHOP - SISTEMA DE CITAS Y RECORDATORIOS"
echo "========================================================"
echo ""

# Verificar si existe el entorno virtual; si no, crearlo automáticamente
if [ ! -f ".venv/bin/python" ]; then
    echo "[*] Preparando entorno por primera vez..."
    python3 -m venv .venv
    echo "[*] Instalando dependencias exactas..."
    .venv/bin/pip install -r requirements.txt
fi

export PYTHONPATH=backend/src

echo "[*] Servidor iniciando en http://localhost:8000 ..."
echo "[*] Pulsa Ctrl+C en esta terminal para detener."
echo "========================================================"
echo ""

# Abrir el navegador por defecto tras breve espera
(sleep 2 && (xdg-open http://localhost:8000 2>/dev/null || open http://localhost:8000 2>/dev/null)) &

# Ejecutar servidor Uvicorn
.venv/bin/python -m uvicorn api.api:app --host 127.0.0.1 --port 8000
