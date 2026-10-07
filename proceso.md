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

## Día 6: Reestructuración Modular y Arquitectura Inicial de FastAPI
- Reorganicé la arquitectura del proyecto separando responsabilidades: creé la estructura modular `backend/src/app` (capa de datos y CLI) y `backend/src/api` (capa de controladores HTTP/FastAPI).
- Diseñé `backend/src/app/database.py` para instanciar la conexión de forma centralizada (`db: DatabaseManager`) y resolviendo las rutas con `pathlib.Path(__file__).resolve()`.
- Solucioné el bloqueo de concurrencia de SQLite en entornos web: por defecto, `sqlite3` prohíbe usar conexiones en hilos diferentes (`ProgrammingError`), pero FastAPI atiende peticiones en un pool de hilos asíncrono. Lo solucioné configurando `check_same_thread=False` en `connect()` (documentado en ADR-008).
- Escribí los primeros endpoints de lectura en `backend/src/api/api.py` (`/`, `/appointments/today/left`, `/appointments/today/`, `/appointments/left` y `/appointments/clients/{client_id}`).
- Creé el archivo `requirements.txt` con las dependencias fijadas del backend (`fastapi`, `uvicorn`, `pydantic`).

## Día 7: Schemas con Pydantic, CRUD Completo en FastAPI y Conceptos Clave
- Completé el ciclo **CRUD** completo en FastAPI (`POST` para crear citas, `PUT` para actualizarlas y `DELETE` para cancelarlas).
- Diseñé y separé los tres Schemas principales de Pydantic según su responsabilidad (ADR-007):
  - `AppointmentCreate`: para peticiones `POST` (no incluye `appointment_id` porque lo genera la BD con `AUTOINCREMENT`).
  - `AppointmentResponse`: para respuestas `GET` (incluye `appointment_id` y todos los datos del cliente combinados por el `JOIN`).
  - `AppointmentUpdate`: para peticiones `PUT` (con campos opcionales `= None` para no obligar al cliente a reenviar datos inmutables de cliente como teléfono o nombre al cambiar solo la hora o servicio).
- **Conceptos clave y dudas más importantes resueltas durante este día:**
  1. **La cadena de transformación `sqlite3.Row` ➔ `dict()` ➔ `BaseModel` ➔ JSON:**
     - Aunque `row_factory = sqlite3.Row` permite acceder a los campos por nombre (`fila["name"]`), internamente es un objeto híbrido de C/Python, **no una instancia nativa de `dict`**.
     - El serializador de FastAPI y Pydantic requiere tipos nativos de Python. Por eso es obligatorio hacer `[dict(row) for row in ...]` para empaquetarlo en diccionarios estándar que Pydantic sabe validar y traducir a texto JSON.
  2. **Cómo entiende Pydantic los datos y flexibilidad de contenedores:**
     - Para que Pydantic valide o instancie un `BaseModel`, la unidad de datos básica **debe ser un diccionario (`clave: valor`)**, porque empareja las claves del diccionario con los atributos de la clase.
     - El contenedor exterior puede variar según el endpoint (`list[AppointmentResponse]`, `tuple[AppointmentResponse, ...]`, o un objeto individual `AppointmentResponse`), pero cada elemento interior debe tener estructura de clave-valor (`dict`).
  3. **Dónde se escriben los Type Hints y dónde NUNCA:**
     - Los tipos (`: str`, `: int`) solo se escriben en las **definiciones** de funciones (`def f(x: str):`) y en clases `BaseModel`.
     - Al **llamar** a una función (como `db.update_appointment(appointment_id, date=...)`), **nunca** se ponen tipos (`: str` provoca `SyntaxError`). Solo se pasan valores o variables existentes.
  4. **Parámetros sueltos vs Schemas `BaseModel` en el Request Body:**
     - Si en un endpoint `POST` pones parámetros sueltos (`phone: str, name: str`), FastAPI los interpreta como **Query Parameters en la URL** (`/appointments/?phone=...`), exponiendo datos sensibles en logs y en el historial del navegador.
     - Al usar una clase `BaseModel` (`appointment: AppointmentCreate`), FastAPI sabe que deben viajar en el **Cuerpo (Body) HTTP en formato JSON**, protegidos y validados de golpe antes de ejecutar la función.
  5. **Diseño de URLs REST (Colección vs Recurso Individual):**
     - `POST /appointments/`: la cita **aún no existe** ni tiene ID asignado; por eso la petición apunta a la colección general para que la base de datos la inserte y le asigne su ID autoincremental.
     - `GET /appointments/{id}`, `PUT /appointments/{id}`, `DELETE /appointments/{id}`: la cita **ya existe** en la base de datos con una clave primaria única; por tanto, la URL debe identificar exactamente sobre qué registro físico se va a operar.
  6. **Lógica de negocio en la creación de citas:**
     - Al crear una cita llamamos a `db.get_or_create_client(phone, name, last_name)`. Este método comprueba si el cliente ya existe y, si no, lo registra automáticamente en la tabla `clients`. Por tanto, **el cliente se da de alta automáticamente al pedir su cita**, sin necesidad de un formulario o endpoint separado de clientes, lo que da pleno sentido al endpoint de historial por cliente (`/appointments/clients/{client_id}`).
- Añadí `CORSMiddleware` a `api.py` para permitir peticiones HTTP desde el frontend de React (`localhost:5173`) sin bloqueos por política de mismo origen del navegador.
- Corregí `get_appointment()` en `database_manager.py` añadiendo `return self.cursor.fetchone()` que faltaba.
- Adapté las rutas de importación de `tests/run_tests.py` y `backend/src/app/main.py` para ser compatibles con la nueva estructura de paquetes, logrando que el 100% de la suite de pruebas unitarias pase con éxito (`ALL TESTS COMPLETED`).

