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
Use SQLite (embedded database in a single `peluqueria.db` file) managed with Python's standard module (`sqlite3`).

### Alternatives considered
- **PostgreSQL:** powerful and scalable, but requires a server, installation, credentials and maintenance, all unacceptable for the deployment environment.

### Consequences
- Zero server configuration; the file is created automatically by running the database manager.
- No background processes that can stop; high tolerance to power cuts.
- The data access layer is designed decoupled (repository pattern) so it can be migrated to PostgreSQL without rewriting the business logic if the project grows.