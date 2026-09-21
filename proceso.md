# Proceso

Mi objetivo con este proyecto es ir construyendo el backend en Python (FastAPI) a mano, para entender cada línea 
## Día 1

- Aprendí qué es un entorno virtual (`venv`) y creé el de este proyecto (`barberShopFAPI_React/`).
- Escribí a mano `init_db.py` para crear la base de datos `peluqueria.db` con SQLite.
- Diseñé el esquema de datos:
  - Tabla `clientes`: el teléfono es `TEXT NOT NULL UNIQUE` (el único campo obligatorio, ya que mi tío solo pone siempre el teléfono; nombre y apellido son opcionales).
  - Tabla `citas`: enlazada a `clientes` por `id_cliente` (clave foránea), con el servicio opcional y `recordatorio_enviado` a 0 por defecto.
- Decidí usar `id` artificial incremental en vez de usar el teléfono como clave, porque los teléfonos pueden cambiar y son propensos a erratas. Lo justifiqué en `decisiones.md` (ADR-002).
- Verifiqué que la base de datos se crea correctamente: tablas y columnas comprobadas con `PRAGMA table_info`.
- Corregí el `.gitignore` para que Git no suba el entorno virtual ni la base de datos con los datos reales del negocio.
- Hice el primer commit real del proyecto con lo del Día 1.

Idea para el futuros dias: normalizar el teléfono (quitar espacios, guiones, +34) en la capa de aplicación antes de guardarlo, y así la base de datos siempre recibe un formato limpio.