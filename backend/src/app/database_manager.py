import sqlite3
from datetime import datetime
from pathlib import Path

from app.utils import normalize_phone


class DatabaseManager:
    def __init__(self, db_path: str | Path):
        self.db_path = db_path
        self.connection = None
        self.cursor = None

    # creates the file if it doesn't exist
    def connect(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        # Set row_factory to sqlite3.Row: rows behave like dictionaries,
        # allowing access by column name (e.g., row['phone']) instead of index (row[0])
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def create_tables(self):
        self.cursor.execute("PRAGMA foreign_keys = ON;")
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients(
        client_id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL UNIQUE,
        name TEXT,
        last_name TEXT)
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments(
        appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        service TEXT,
        reminder_sent INTEGER DEFAULT 0,
        price REAL DEFAULT 0.0,
        color TEXT DEFAULT '#3b82f6',
        FOREIGN KEY (client_id) REFERENCES clients(client_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT)
        """)

        # Add price and color columns to existing appointments table if missing
        try:
            self.cursor.execute("ALTER TABLE appointments ADD COLUMN price REAL DEFAULT 0.0;")
        except sqlite3.OperationalError:
            pass

        try:
            self.cursor.execute("ALTER TABLE appointments ADD COLUMN color TEXT DEFAULT '#3b82f6';")
        except sqlite3.OperationalError:
            pass

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS whatsapp_reminders(
        appointment_id INTEGER PRIMARY KEY,
        task_name TEXT,
        send_at TEXT NOT NULL,
        status TEXT NOT NULL)
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS services(
        service_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        price REAL NOT NULL DEFAULT 0.0,
        default_color TEXT DEFAULT '#3b82f6')
        """)

        # Prepopulate default services if empty
        self.cursor.execute("SELECT COUNT(*) FROM services")
        if self.cursor.fetchone()[0] == 0:
            default_services = [
                ("Corte caballero", 12.0, "#3b82f6"),
                ("Arreglo de barba", 8.0, "#10b981"),
                ("Corte y barba", 18.0, "#f59e0b"),
                ("Tinte / Tratamiento", 20.0, "#8b5cf6"),
            ]
            self.cursor.executemany(
                "INSERT INTO services (name, price, default_color) VALUES (?, ?, ?)",
                default_services,
            )

        self.connection.commit()

    def close_connection(self):
        if self.connection:
            self.connection.commit()
            self.connection.close()

    def insert_client(self, phone: str, name=None, last_name=None):
        phone = normalize_phone(phone)
        self.cursor.execute(
            """INSERT INTO clients(name, last_name, phone) 
        VALUES (?,?,?)""",
            (name, last_name, phone),
        )
        self.connection.commit()
        return (
            self.cursor.lastrowid
        )  # returns the new client's id so we can chain it into insert_appointment

    def insert_appointment(
        self, client_id, appointment_date, appointment_time, service=None, price=None, color=None
    ):
        if price is None and service:
            self.cursor.execute("SELECT price, default_color FROM services WHERE name = ?", (service,))
            svc_row = self.cursor.fetchone()
            if svc_row:
                price = svc_row["price"]
                if color is None:
                    color = svc_row["default_color"]

        if price is None:
            price = 0.0
        if color is None:
            color = "#3b82f6"

        self.cursor.execute(
            """
        INSERT INTO appointments (client_id, appointment_date, appointment_time, service, price, color) VALUES (?,?,?,?,?,?)""",
            (client_id, appointment_date, appointment_time, service, float(price), str(color)),
        )
        self.connection.commit()
        return self.cursor.lastrowid

    def find_client(self, phone):
        phone = normalize_phone(
            phone
        )  # normalize before searching so the format always matches
        self.cursor.execute("SELECT client_id FROM clients WHERE phone = ?", (phone,))
        client = self.cursor.fetchone()
        return client

    def get_or_create_client(self, phone, name=None, last_name=None):
        phone = normalize_phone(phone)
        client = self.find_client(phone)
        if client is not None:
            return client[0]  # client already exists: return its id
        else:
            return self.insert_client(
                phone, name, last_name
            )  # new client: insert and return the new id

    def search_clients(self, query: str, limit: int = 10):
        # Searches clients matching query substring by phone, name, or last name.
        clean_query = query.strip()
        if not clean_query:
            return []

        search_pattern = f"%{clean_query}%"
        sql = """
            SELECT c.client_id, c.phone, c.name, c.last_name,
                   (SELECT COUNT(*) FROM appointments a WHERE a.client_id = c.client_id) AS visits_count,
                   (SELECT a.service 
                    FROM appointments a 
                    WHERE a.client_id = c.client_id 
                    ORDER BY a.appointment_date DESC, a.appointment_time DESC 
                    LIMIT 1) AS last_service
            FROM clients c
            WHERE c.phone LIKE ? OR c.name LIKE ? OR c.last_name LIKE ?
            ORDER BY visits_count DESC, c.name ASC
            LIMIT ?
        """
        self.cursor.execute(sql, (search_pattern, search_pattern, search_pattern, limit))
        return self.cursor.fetchall()

    def get_appointment(self, appointment_id):
        self.cursor.execute("SELECT * FROM clients JOIN appointments " \
        "ON appointments.client_id = clients.client_id " \
        "WHERE appointment_id = ?", (appointment_id,))
        return self.cursor.fetchone()

    def get_appointments_with_client(self, client_id=None, date=None):
        # Query built in parts because filters are optional.
        # appointments.appointment_id is included so the CLI can show it to the user (needed for edit/cancel).
        query = """
            SELECT appointments.appointment_id,
                   clients.name, clients.phone,
                   appointments.appointment_date, appointments.appointment_time, appointments.service,
                   appointments.price, appointments.color
            FROM appointments
            JOIN clients ON appointments.client_id = clients.client_id
        """
        params = []
        if client_id is not None and date is not None:
            query += "WHERE clients.client_id = ? AND appointments.appointment_date = ?"
            params += [client_id, date]
        elif client_id is not None:
            query += "WHERE clients.client_id = ?"
            params.append(client_id)
        elif date is not None:
            query += "WHERE appointments.appointment_date = ?"
            params.append(date)
        query += " ORDER BY appointment_date, appointment_time"
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def delete_appointment(self, appointment_id):
        query = "DELETE FROM appointments WHERE appointment_id = ?"
        self.cursor.execute(query, [appointment_id])
        self.connection.commit()
        return self.cursor.rowcount  # 1 if deleted, 0 if the id didn't exist

    # Only updates the fields that are passed — does not override the rest with None
    def update_appointment(self, appointment_id, date=None, time=None, service=None, price=None, color=None):

        params = []
        fields = []
        if date is not None:
            fields.append("appointment_date = ?")
            params.append(date)
        if time is not None:
            fields.append("appointment_time = ?")
            params.append(time)
        if service is not None:
            fields.append("service = ?")
            params.append(service)
        if price is not None:
            fields.append("price = ?")
            params.append(float(price))
        if color is not None:
            fields.append("color = ?")
            params.append(str(color))

        if not fields:
            return 0  # nothing to update

        param_list_str = ", ".join(fields)
        query = f"UPDATE appointments SET {param_list_str} WHERE appointment_id = ? "
        params.append(appointment_id)  # WHERE param goes last
        self.cursor.execute(query, params)
        self.connection.commit()
        return self.cursor.rowcount

    # Same dynamic pattern as update_appointment
    def update_client(self, client_id, name=None, last_name=None, phone=None):
        params = []
        fields = []
        if name is not None:
            fields.append("name = ?")
            params.append(name)
        if last_name is not None:
            fields.append("last_name = ?")
            params.append(last_name)
        if phone is not None:
            phone = normalize_phone(phone)
            fields.append("phone = ?")
            params.append(phone)

        if not fields:
            return 0

        param_list_str = ", ".join(fields)
        query = f"UPDATE clients SET {param_list_str} WHERE client_id = ? "
        params.append(client_id)
        self.cursor.execute(query, params)
        self.connection.commit()
        return self.cursor.rowcount

    def get_all_appointments(self):
        self.cursor.execute("SELECT * FROM appointments ORDER BY appointment_date")
        return self.cursor.fetchall()

    def get_day_appointments(self):
        # Returns all appointments for today with client info (JOIN).
        # Uses .astimezone() to read the local time from the PC, not UTC.
        today = datetime.now().astimezone().date().isoformat()
        self.cursor.execute(
            """
            SELECT appointments.appointment_id,
                   clients.name, clients.phone,
                   appointments.appointment_date, appointments.appointment_time, appointments.service
            FROM appointments
            JOIN clients ON appointments.client_id = clients.client_id
            WHERE appointment_date = ?
            ORDER BY appointment_time
        """,
            (today,),
        )
        return self.cursor.fetchall()

    def get_appointments_left_today(self):
        # Returns appointments for today that haven't happened yet (time >= now).
        local = datetime.now().astimezone()
        today = local.date().isoformat()
        current_time = local.strftime("%H:%M:%S")
        self.cursor.execute(
            """
            SELECT appointments.appointment_id,
                   clients.name, clients.phone,
                   appointments.appointment_date, appointments.appointment_time, appointments.service
            FROM appointments
            JOIN clients ON appointments.client_id = clients.client_id
            WHERE appointment_date = ? AND appointment_time >= ?
            ORDER BY appointment_time
        """,
            (today, current_time),
        )
        return self.cursor.fetchall()

    def get_all_appointments_left(self):
        # Returns: today's remaining appointments + all future days.
        # OR condition: (today AND time not passed) OR (any day strictly after today).
        local = datetime.now().astimezone()
        today = local.date().isoformat()
        current_time = local.strftime("%H:%M:%S")
        self.cursor.execute(
            """
            SELECT appointments.appointment_id,
                   clients.name, clients.phone,
                   appointments.appointment_date, appointments.appointment_time, appointments.service
            FROM appointments
            JOIN clients ON appointments.client_id = clients.client_id
            WHERE (appointment_date = ? AND appointment_time >= ?) OR appointment_date > ?
            ORDER BY appointment_date, appointment_time
        """,
            (today, current_time, today),
        )
        return self.cursor.fetchall()

    def upsert_reminder(self, appointment_id: int, send_at: str, status: str, task_name: str | None = None):
        # Inserts or updates a WhatsApp reminder record for an appointment.
        self.cursor.execute(
            """
            INSERT INTO whatsapp_reminders (appointment_id, task_name, send_at, status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(appointment_id) DO UPDATE SET
                task_name = excluded.task_name,
                send_at = excluded.send_at,
                status = excluded.status
            """,
            (appointment_id, task_name, send_at, status),
        )
        self.connection.commit()

    def get_reminder(self, appointment_id: int):
        # Retrieves the WhatsApp reminder associated with an appointment ID.
        self.cursor.execute(
            "SELECT * FROM whatsapp_reminders WHERE appointment_id = ?",
            (appointment_id,),
        )
        return self.cursor.fetchone()

    def update_reminder_status(self, appointment_id: int, status: str, task_name: str | None = None):
        # Updates status and optionally task_name for an existing reminder.
        if task_name is not None:
            self.cursor.execute(
                "UPDATE whatsapp_reminders SET status = ?, task_name = ? WHERE appointment_id = ?",
                (status, task_name, appointment_id),
            )
        else:
            self.cursor.execute(
                "UPDATE whatsapp_reminders SET status = ? WHERE appointment_id = ?",
                (status, appointment_id),
            )
        self.connection.commit()

    def delete_reminder(self, appointment_id: int):
        # Deletes a reminder record manually.
        self.cursor.execute(
            "DELETE FROM whatsapp_reminders WHERE appointment_id = ?",
            (appointment_id,),
        )
        self.connection.commit()

    def get_services(self):
        # Returns all services configured in the database ordered by ID.
        self.cursor.execute("SELECT service_id, name, price, default_color FROM services ORDER BY service_id ASC")
        return self.cursor.fetchall()

    def create_service(self, name: str, price: float, default_color: str = "#3b82f6"):
        # Creates a new service in the catalog.
        self.cursor.execute(
            "INSERT INTO services (name, price, default_color) VALUES (?, ?, ?)",
            (name.strip(), float(price), default_color.strip() if default_color else "#3b82f6"),
        )
        self.connection.commit()
        return self.cursor.lastrowid

    def update_service(self, service_id: int, name: str | None = None, price: float | None = None, default_color: str | None = None):
        # Updates service properties in the catalog.
        fields = []
        params = []
        if name is not None:
            fields.append("name = ?")
            params.append(name.strip())
        if price is not None:
            fields.append("price = ?")
            params.append(float(price))
        if default_color is not None:
            fields.append("default_color = ?")
            params.append(default_color.strip())
        if not fields:
            return 0
        params.append(service_id)
        self.cursor.execute(f"UPDATE services SET {', '.join(fields)} WHERE service_id = ?", params)
        self.connection.commit()
        return self.cursor.rowcount

    def delete_service(self, service_id: int):
        # Deletes a service from the catalog.
        self.cursor.execute("DELETE FROM services WHERE service_id = ?", (service_id,))
        self.connection.commit()
        return self.cursor.rowcount

    def get_appointments_range(self, start_date: str, end_date: str):
        # Retrieves all appointments between start_date and end_date (inclusive) for weekly/monthly calendar views.
        sql = """
            SELECT a.appointment_id, c.client_id, c.name, c.last_name, c.phone,
                   a.appointment_date, a.appointment_time, a.service, a.price, a.color
            FROM appointments a
            JOIN clients c ON a.client_id = c.client_id
            WHERE a.appointment_date >= ? AND a.appointment_date <= ?
            ORDER BY a.appointment_date ASC, a.appointment_time ASC
        """
        self.cursor.execute(sql, (start_date, end_date))
        return self.cursor.fetchall()

    def get_statistics(self, start_date: str, end_date: str):
        # Aggregates financial and appointment metrics between start_date and end_date.
        self.cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(price), 0.0)
            FROM appointments
            WHERE appointment_date >= ? AND appointment_date <= ?
        """, (start_date, end_date))
        total_row = self.cursor.fetchone()
        total_count = total_row[0] if total_row else 0
        total_revenue = round(float(total_row[1]), 2) if total_row else 0.0

        self.cursor.execute("""
            SELECT COALESCE(service, 'Sin especificar') AS service_name,
                   COUNT(*) AS count,
                   ROUND(COALESCE(SUM(price), 0.0), 2) AS revenue,
                   COALESCE(color, '#3b82f6') AS color
            FROM appointments
            WHERE appointment_date >= ? AND appointment_date <= ?
            GROUP BY service_name
            ORDER BY count DESC
        """, (start_date, end_date))
        by_service = self.cursor.fetchall()

        return {
            "total_appointments": total_count,
            "total_revenue": total_revenue,
            "average_ticket": round(total_revenue / total_count, 2) if total_count > 0 else 0.0,
            "services": [dict(r) for r in by_service],
        }

