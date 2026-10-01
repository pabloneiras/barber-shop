# Proceso

Mi objetivo con este proyecto es ir construyendo el backend en Python (FastAPI) a mano, para entender cada línea 
## Día 1

- Aprendí qué es un entorno virtual (`venv`) y creé el de este proyecto (`barberShopFAPI_React/`).
- Escribí a mano `init_db.py` para crear la base de datos `peluqueria.db` con SQLite.
- Diseñé el esquema de datos:
  - Tabla `clientes`: el teléfono es `TEXT NOT NULL UNIQUE` (el único campo obligatorio, ya que mi tío solo pone siempre el teléfono; nombre y apellido son opcionales).
  - Tabla `citas`: enlazada a `clientes` por `id_cliente` (clave foránea), con el servicio opcional y `recordatorio_enviado` a 0 por defecto.
- Decidí usar `id` artificial incremental en vez de usar el teléfono como clave, porque los teléfonos pueden cambiar y son propensos a erratas. Lo justifiqué en `decisions.md` (ADR-002).
- Verifiqué que la base de datos se crea correctamente: tablas y columnas comprobadas con `PRAGMA table_info`.
- Corregí el `.gitignore` para que Git no suba el entorno virtual ni la base de datos con los datos reales del negocio.
- Hice el primer commit real del proyecto con lo del Día 1.

Idea para el futuros dias: normalizar el teléfono (quitar espacios, guiones, +34) en la capa de aplicación antes de guardarlo, y así la base de datos siempre recibe un formato limpio.



Día 2: Separé la lógica en `database_manager.py` (capa de datos) y `utils.py` (funciones puras). Empecé a crear la clase con `connect()`, `create_tables()`, `close_connection()`. 

## Día 3
- Implementé los métodos principales del CRUD: `insert_client()` (devolviendo `lastrowid`), `insert_appointment()`, `find_client()` (normalizando el teléfono antes) y `get_or_create_client()` (lógica de negocio para reutilizar clientes existentes).
- Implementé `get_appointments_with_client()` usando `JOIN` para enlazar clientes con citas y devolver los datos enriquecidos (nombre, teléfono).
- Implementé `delete_appointment()` para cancelar citas.
- Protegí la base de datos activando `PRAGMA foreign_keys = ON` y aplicando `ON DELETE RESTRICT` para proteger el historial de citas al intentar borrar clientes.
- Recreé la base de datos `peluqueria.db` con el nuevo esquema en inglés.
- Traduje todo el proyecto (código, variables, decisiones) al inglés, manteniendo `proceso.md` en español.
- Plan Día 4: `UPDATE` (editar cita y cliente) para completar el CRUD.