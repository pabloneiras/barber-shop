# Design Decisions

Record of the project's structural decisions, with their context, the decision taken and the alternatives considered.

---

## ADR-001: Database schema with two related tables

- **Status:** Accepted
- **Date:** 2026-09-21

### Context
The application keeps track of appointments for a local business. The same person can have multiple appointments, so their basic information (name, phone) should not be repeated in every record.

### Decision
Separate the data into two tables related by foreign key:
- `clients`: the person's data (identification, contact).
- `appointments`: each booking, linked to a client via `client_id -> clients.client_id`.

### Alternatives considered
- **Single table with all the data:** simpler, but repeats the client's information in every appointment and makes it hard to correct a single piece of data (it would require updating multiple rows).
- **Four tables (clients, services, appointments, appointment_services):** more normalized, but overengineering for a business with a single user.
- **Phone as natural primary key:** rejected (see ADR-002).

### Consequences
- No duplication of client data.
- Every appointment depends on an existing client (integrity enforced by foreign key).
- The model is ready to grow if the business expands.

---

## ADR-002: Artificial key (`INTEGER AUTOINCREMENT`) instead of a natural key

- **Status:** Accepted
- **Date:** 2026-09-21

### Context
The phone number is the data that identifies the client to the business, so it may look like an ideal natural key.

### Decision
Use an artificial, auto-incrementing primary key (`client_id INTEGER PRIMARY KEY AUTOINCREMENT`) as the internal identifier, and mark the phone as `UNIQUE` to guarantee that each client is unique at business level.

### Alternatives considered
- **Phone as natural primary key:** rejected because phone numbers can change (updating one would drag through every appointment), are prone to typos ("ghost" clients) and force the number to be duplicated in every row of the `appointments` table. Also, text indexes worse than an integer.
- **Manual numbering:** rejected as risky.
- **Another human-readable key:** none is reliably unique.

### Consequences
- The internal key is stable and immutable even if the client changes phone number.
- `phone UNIQUE` prevents duplicates at business level.
- The `id`s are invisible to the end user: the application uses the phone to identify clients.

---

## ADR-003: The phone is the only mandatory field and is stored as normalized text

- **Status:** Accepted
- **Date:** 2026-09-21

### Context
The application's user (a non-technical person) will only reliably fill in the phone number. Name, last name and service are optional.

### Decision
- `phone` column as `TEXT NOT NULL UNIQUE`: the only mandatory and uniqueness constraint at database level.
- Remaining columns (`name`, `last_name`, `service`) are optional (`NULL` allowed).
- Phone normalization happens in the application layer, before inserting (strip spaces, hyphens and prefixes such as +34), so the database always receives a canonical format of digits only.

### Alternatives considered
- **Phone as `INTEGER`:** rejected. Even though after normalization only digits remain, an integer loses leading zeros, silently mutates formats (e.g. `+34...` or `00...`) and does not convey that it is an identifier, not a quantity.
- **Mandatory name:** rejected by business decision.

### Consequences
- Minimal user experience for the barber (only asks for the phone).
- Consistent and searchable data (`LIKE '%...%'` over normalized text).
- Normalization stays separate from validation (Pydantic validates; the logic normalizes; the DB stores clean).

---

## ADR-004: SQLite as the database

- **Status:** Accepted
- **Date:** 2026-09-21

### Context
The application runs locally on a single machine, managed by a person without technical knowledge. It needs robustness and zero maintenance.

### Decision
Use SQLite (embedded database in a single `barber_shop.db` file) managed with Python's standard module (`sqlite3`).

### Alternatives considered
- **PostgreSQL:** powerful and scalable, but requires a server, installation, credentials and maintenance, all unacceptable for the deployment environment.

### Consequences
- Zero server configuration; the file is created automatically by running the database manager.
- No background processes that can stop; high tolerance to power cuts.
- The data access layer is designed decoupled (repository pattern) so it can be migrated to PostgreSQL without rewriting the business logic if the project grows.

---

## ADR-005: Enabling Foreign Keys and data integrity rules

- **Status:** Accepted
- **Date:** 2026-09-24

### Context
SQLite disables foreign key enforcement by default. To ensure data integrity, especially for preventing deletion of clients that have existing historical appointments, we need to explicitly enable these constraints.

### Decision
- Execute `PRAGMA foreign_keys = ON;` in `create_tables()` to activate SQLITE FK support.
- Apply `ON DELETE RESTRICT` on the `appointments` foreign key constraint to block deleting a client if they have appointments.
- Apply `ON UPDATE CASCADE` for referential integrity (even if the `client_id` PK is immutable).

### Consequences
- Data integrity is guaranteed at database level.
- Attempting to delete a client with active appointments will raise an `IntegrityError`, protecting historical records.
- Added complexity: code must now handle potential `IntegrityError` when attempting deletes or updates.

---

## ADR-006: Using local system time instead of UTC for date/time queries

- **Status:** Accepted
- **Date:** 2026-10-02

### Context
Three methods (`get_day_appointments`, `get_appointments_left_today`, `get_all_appointments_left`) need to compare the current date and time against values stored in the database. Python's `datetime.now()` returns the system time with no timezone info, which can differ from UTC depending on the machine.

### Decision
Use `datetime.now().astimezone()` to obtain the current local date and time including the system's timezone offset. Extract `.date().isoformat()` for the date (`YYYY-MM-DD`) and `.strftime("%H:%M:%S")` for the time, matching the format stored in the database.

### Alternatives considered
- **`datetime.utcnow()`:** rejected. The database stores times as entered by the barber (local time, no timezone). Comparing against UTC would produce wrong results during any hour where local time differs from UTC.
- **`datetime.now()` without `.astimezone()`:** works on most systems but is not timezone-aware. Using `.astimezone()` makes the intent explicit and is safer across environments.

### Consequences
- Queries always use the machine's local clock, which matches the barber's working timezone.
- If the application is ever moved to a server in a different timezone, the stored times and the comparison timezone must be kept consistent.

---

## ADR-007: Separation of Pydantic Schemas (Request vs Response vs Update)

- **Status:** Accepted
- **Date:** 2026-10-07

### Context
FastAPI uses Pydantic models for request validation and response serialization. Initially, it may seem simpler to use a single data model or loose endpoint parameters, but input constraints differ fundamentally from database outputs.

### Decision
Define distinct Pydantic models for each HTTP role:
- `AppointmentCreate`: Schema for incoming creation requests (`POST`). Omits `appointment_id` because SQLite generates it automatically via `AUTOINCREMENT`.
- `AppointmentResponse`: Schema for outgoing responses (`GET`). Includes `appointment_id` and all resolved client data (`name`, `phone`) produced by database `JOIN`s.
- `AppointmentUpdate`: Schema for partial modifications (`PUT`/`PATCH`). Contains optional fields (`str | None = None`) so clients can update specific appointment details without resending immutable client information.

### Alternatives considered
- **Loose function arguments in route handlers:** rejected. FastAPI treats non-path primitive parameters as URL query parameters, forcing payload data into URLs rather than the HTTP request body.
- **Single monolithic model:** rejected. Forces optional IDs on creation and complicates validation when updating.

### Consequences
- Clean separation between incoming payloads and outgoing JSON contracts.
- Automatic interactive documentation in Swagger UI (`/docs`) with exact schemas.
- Strict runtime data validation and sanitization.

---

## ADR-008: Enabling `check_same_thread=False` for SQLite with FastAPI

- **Status:** Accepted
- **Date:** 2026-10-07

### Context
FastAPI processes incoming requests concurrently across worker threads in its async threadpool. By default, Python's standard `sqlite3` library enforces single-thread affinity, raising `ProgrammingError: SQLite objects created in a thread can only be used in that same thread` when accessed across requests.

### Decision
Initialize the database connection with `sqlite3.connect(..., check_same_thread=False)` inside `DatabaseManager.connect()`, exposed through a centralized instance in `backend/src/app/database.py`.

### Alternatives considered
- **Creating a new connection per HTTP request via FastAPI dependency injection:** viable, but adds connection setup overhead and complexity for this single-user local deployment stage.
- **Immediate migration to async SQLAlchemy:** rejected as unnecessary complexity at this stage of the project.

### Consequences
- Allows FastAPI route handlers running on multiple threads to safely query the shared database instance.
- SQLite handles concurrent writes through its standard file-level locking mechanisms.

---

## ADR-009: RESTful URL path conventions for collection vs single-resource endpoints

- **Status:** Accepted
- **Date:** 2026-10-08

### Context
The backend API requires clear, predictable endpoint paths for creating, reading, updating, and deleting appointments.

### Decision
Follow standard REST conventions:
- **Collection endpoint (`/appointments/`):** used for `POST` (creating a new appointment before any ID exists) and `GET` (listing appointments).
- **Single-resource endpoint (`/appointments/{appointment_id}`):** used for operations on a specific, existing appointment (`GET`, `PUT`, `DELETE`), targeting the record explicitly via its path parameter.

### Alternatives considered
- **Passing IDs exclusively via query parameters (`/appointments?id=1`):** rejected to follow standard RESTful conventions.
- **Including artificial IDs in `POST` requests:** rejected because the ID does not exist until inserted into the database.

### Consequences
- Follows industry-standard REST API conventions.
- Clear distinction between collection-level and resource-level actions.