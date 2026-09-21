# Decisiones de Diseño

Registro de decisiones estructurales del proyecto, con su contexto, la decision tomada y las alternativas consideradas.

---

## ADR-001: Esquema de base de datos con dos tablas relacionadas

- **Estado:** Aceptada
- **Fecha:** 2026-09-21

### Contexto
La aplicacion registra citas para un negocio local. Una misma persona puede tener multiples citas, por lo que su informacion basica (nombre, telefono) no debe repetirse en cada registro.

### Decision
Separar los datos en dos tablas relacionadas por clave foranea:
- `clientes`: datos de la persona (identificacion, contacto).
- `citas`: cada reserva, enlazada a un cliente mediante `cliente_id -> clientes.id_cliente`.

### Alternativas consideradas
- **Tabla unica con todos los datos:** mas simple, pero repite la informacion del cliente en cada cita y dificulta corregir un dato (requeriria actualizar multiples filas).
- **Cuatro tablas (clientes, servicios, citas, citas_servicios):** mas normalizada, pero sobreingenieria para un negocio con un unico usuario.
- **Telefono como clave primaria natural:** se descarto (ver ADR-002).

### Consecuencias
- No hay duplicidad de datos de cliente.
- Cada cita depende de un cliente existente (integritad por clave foranea).
- Modelo listo para extenderse si el negocio crece.

---

## ADR-002: Clave artificial (`INTEGER AUTOINCREMENT`) en lugar de clave natural

- **Estado:** Aceptada
- **Fecha:** 2026-09-21

### Contexto
El telefono es el dato que identifica al cliente en el negocio, por lo que puede parecer la clave natural ideal.

### Decision
Usar una clave primaria artificial e incremental (`id_cliente INTEGER PRIMARY KEY AUTOINCREMENT`) como identificador interno, y marcar el telefono como `UNIQUE` para garantizar que cada cliente sea unico a nivel de negocio.

### Alternativas consideradas
- **Telefono como clave primaria natural:** se descarto porque los telefonos pueden cambiar (actualizarlo arrastraria a todas las citas), son propensos a erratas (clientes "fantasma") y fuerzan a duplicar el numero en cada fila de la tabla `citas`. Ademas, texto como clave indexa peor que un entero.
- **Numeracion manual:** descartada por arriesgada.
- **Otro dato humano como clave:** ninguno es establemente unico.

### Consecuencias
- La clave interna es estable e inmutable aunque el cliente cambie de telefono.
- `telefono UNIQUE` impide duplicados a nivel de negocio.
- Los `id` son invisibles para el usuario final: la aplicacion usa el telefono para identificar clientes.

---

## ADR-003: El telefono es el unico campo obligatorio y se guarda como texto normalizado

- **Estado:** Aceptada
- **Fecha:** 2026-09-21

### Contexto
El usuario de la aplicacion (persona no tecnica) solo rellenara de forma garantizada el numero de telefono. El nombre, apellido y servicio son opcionales.

### Decision
- Columna `telefono` como `TEXT NOT NULL UNIQUE`: unica restriccion de obligatoriedad y unicidad a nivel de base de datos.
- Demas columnas (`nombre`, `apellido`, `servicio`) como opcionales (`NULL` permitido).
- Normalizacion del telefono en la capa de aplicacion, antes de insertar (quitar espacios, guiones y prefijos como +34), de modo que la base de datos siempre recibe un formato canonico de solo digitos.

### Alternativas consideradas
- **Telefono como `INTEGER`:** se descarto. Pese a que tras normalizar solo quedan digitos, un entero pierde ceros a la izquierda, muta silenciosamente formatos (ej. `+34...` o `00...`) y no transmite que es un identificador, no una cantidad.
- **Nombre obligatorio:** descartado por decision de negocio.

### Consecuencias
- Experiencia de usuario minima para el barbero (solo pide el telefono).
- Datos coherentes y buscables (`LIKE '%...%'` sobre texto normalizado).
- La normalizacion permanece separada de la validacion (Pydantic valida; la logica normaliza; la DB almacena limpio).

---

## ADR-004: SQLite como base de datos

- **Estado:** Aceptada
- **Fecha:** 2026-09-21

### Contexto
La aplicacion se ejecuta de forma local en un unico equipo, gestionada por una persona sin conocimientos tecnicos. Se necesita robustez y cero mantenimiento.

### Decision
Usar SQLite (base de datos embebida en un solo archivo `barber_shop.db`) gestionada con el modulo estandar de Python (`sqlite3()`).

### Alternativas consideradas
- **PostgreSQL:** potente y escalable, pero requiere servidor, instalacion, credenciales y mantenimiento, inaceptables para el entorno de despliegue.

### Consecuencias
- Cero configuracion de servidor; el archivo se crea solo con `init_db.py`.
- Sin procesos en segundo plano que se puedan detener; alta tolerancia a cortes de luz.
- Se disena la capa de acceso a datos desacoplada (patron repositorio) para permitir migrar a PostgreSQL sin reescribir la logica de negocio si el proyecto crece.