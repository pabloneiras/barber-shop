import sqlite3
from pathlib import Path
from utils import normalize_phone


class DatabaseManager:

    def __init__(self, db_path: str | Path):
        self.db_path = db_path
        self.connection = None
        self.cursor = None

    # creates the file if it doesn't exist
    def connect(self):
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

    def create_tables(self):
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
        FOREIGN KEY (client_id) REFERENCES clients(client_id))
        """)
        self.connection.commit()

    def close_connection(self):
        if self.connection:
            self.connection.commit()
            self.connection.close()

    def insert_client(self, phone: str, name=None, last_name=None):
        phone = normalize_phone(phone)
        self.cursor.execute("""INSERT INTO clients(name, last_name, phone) 
        VALUES (?,?,?)""", (name, last_name, phone))
        self.connection.commit()

    def insert_appointment(self, client_id, appointment_date, appointment_time, service=None):
        self.cursor.execute("""
        INSERT INTO appointments (client_id, appointment_date, appointment_time, service) VALUES (?,?,?,?)""", (client_id, appointment_date, appointment_time, service))
        self.connection.commit()

    def find_client(self, phone):
        self.cursor.execute("SELECT client_id FROM clients WHERE phone = ?", (phone,))
        client = self.cursor.fetchone()
        return client