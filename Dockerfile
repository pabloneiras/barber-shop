FROM python:3.12-slim

WORKDIR /app

# Copiar dependencias e instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del backend y frontend compilado
COPY backend/ backend/
COPY frontend/dist/ frontend/dist/
COPY Database/.gitkeep Database/.gitkeep

ENV PYTHONPATH=/app/backend/src
ENV PORT=8000

EXPOSE 8000

# Iniciar servidor Uvicorn en el puerto indicado por la plataforma
CMD ["sh", "-c", "python -m uvicorn api.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
