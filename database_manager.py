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
        FOREIGN KEY (client_id) REFERENCES clients(client_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT)
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
        return self.cursor.lastrowid

    def insert_appointment(self, client_id, appointment_date, appointment_time, service=None):
        self.cursor.execute("""
        INSERT INTO appointments (client_id, appointment_date, appointment_time, service) VALUES (?,?,?,?)""", (client_id, appointment_date, appointment_time, service))
        self.connection.commit()

    def find_client(self, phone):
        phone = normalize_phone(phone)
        self.cursor.execute("SELECT client_id FROM clients WHERE phone = ?", (phone,))
        client = self.cursor.fetchone()
        return client

    def get_or_create_client(self, phone, name = None, last_name = None):
        phone = normalize_phone(phone)
        client = self.find_client(phone)
        if client is not None:
            return client[0] #returns the client id (the first of the tuple)
        else:
            return self.insert_client(phone, name, last_name) #if it doesn't exist -> we insert and returns the id


    def get_appointments_with_client(self, client_id= None, date= None):
        #The SQL query is constructed in parts because some values ​​are optional, and ts makes the process easier.
        query = " SELECT name, phone, appointment_date, appointment_time, service FROM clients JOIN appointments ON clients.client_id = appointments.client_id "
        params = []
        if client_id is not None and date is not None:
            params += [client_id, date]
            query += "WHERE clients.client_id = ? AND appointments.appointment_date = ?"
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
        return self.cursor.rowcount
        


        




