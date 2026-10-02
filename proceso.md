# Proceso

Mi objetivo con este proyecto es ir construyendo el backend en Python (FastAPI) a mano, para entender cada línea 
## Día 1

- Aprendí qué es un entorno virtual (`venv`) y creé el de este proyecto (`barberShopFAPI_React/`).
- Escribí a mano `init_db.py`(borrado, actualmente database_manager.py) para crear la base de datos `peluqueria.db` con SQLite.
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

## Día 4
- Implementé `update_appointment()` y `update_client()` para completar el CRUD (Crear, Leer, Actualizar, Borrar).
- Usé el patrón de construcción dinámica de SQL con dos listas (`fields` para las columnas y `params` para los valores): solo se actualizan los campos que se pasan, sin machacar el resto con `None`.
- Aprendí que el `id` del `WHERE` tiene que ir el último en la lista de `params`, que el `SET` se construye con `fields` (nombres de columna) y que hay que unirlo con `", ".join(fields)`.
- Añadí `self.connection.row_factory = sqlite3.Row` en `connect()` para poder acceder a las columnas por nombre (`fila["phone"]`) en vez de por índice, lo que me ahorrará trabajo cuando llegue a FastAPI.
- Verifiqué que el update parcial funciona, que sin cambios devuelve `0`, que un id inexistente devuelve `0` y que el `UNIQUE` del teléfono sigue protegiendo contra duplicados al editar.

## Día 5
- Desarrollé el menú interactivo CLI en `main.py` con tres funciones separadas: `show_menu()` (bucle principal con `try/except` para que un error no cierre el programa), `logic_menu()` (el `match` con la lógica de cada opción) y `print_appointments()` (función auxiliar que formatea e imprime cualquier lista de citas mostrando `[ID]`, fecha, hora, nombre, teléfono y servicio).
- Implementé los seis casos del menú. Las opciones 3 (cancelar) y 4 (editar) primero muestran todas las citas con su ID antes de pedir el ID al usuario. La opción 4 usa `input().strip() or None` para que dejar un campo en blanco no machaque el valor existente (aprovecha el UPDATE dinámico del Día 4).
- Añadí `db.create_tables()` y `db.close_connection()` al ciclo de vida: la BD se inicializa al arrancar y la conexión se cierra limpiamente al salir (opción 7).
- Refactoricé los cuatro métodos de lectura de `database_manager.py` para que todos usen JOIN y devuelvan siempre las mismas columnas: `appointment_id`, `name`, `phone`, `appointment_date`, `appointment_time`, `service`. Antes tres de ellos hacían `SELECT *` de `appointments` sin datos del cliente. Incluir `appointment_id` en el SELECT era imprescindible para que el CLI pudiera mostrárselo al usuario.
- Corregí tres bugs: (1) `input()` devuelve `str`, comparar con el entero `7` nunca salía del bucle; (2) typo de SQL (`EXIsdadadSTS`) que habría roto `create_tables()` con una BD nueva; (3) faltaba `return self.cursor.fetchall()` en `get_all_appointments_left()`.
- Creé la carpeta `tests/` con `run_tests.py`, que usa su propia BD aislada (`test_peluqueria.db`, en `.gitignore`) y la recrea desde cero en cada ejecución para garantizar resultados reproducibles.
