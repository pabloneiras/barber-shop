"""
tests/run_tests.py
Tests each DatabaseManager method using an isolated test database.
Does NOT touch peluqueria.db or any project file.
Run from the project root: python tests/run_tests.py
"""

import sys
from pathlib import Path

# Add backend/src to path so app package can be resolved
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from app.database_manager import DatabaseManager


# Isolated test DB in this same folder (gitignored)
TEST_DB = Path(__file__).parent / "test_peluqueria.db"

# Always start clean: delete and recreate the test DB
if TEST_DB.exists():
    TEST_DB.unlink()

db = DatabaseManager(TEST_DB)
db.connect()
db.create_tables()


def log(section, data):
    print(f"[{section}]")
    if isinstance(data, list):
        for row in data:
            print(" ", row)
    else:
        print(" ", data)
    print()


# ─────────────────────────────────────────────
# SEED: populate the test DB with sample data
# ─────────────────────────────────────────────
id_carlos = db.get_or_create_client("666 111 222", "Carlos", "Lopez")
id_maria = db.get_or_create_client("+34 677-888-999", "Maria", "Gomez")
id_juan = db.get_or_create_client("600000001", "Juan", None)  # no last name
id_no_name = db.get_or_create_client("600000002")  # phone only

db.insert_appointment(id_carlos, "2026-10-02", "09:00", "Haircut")
db.insert_appointment(id_carlos, "2026-10-02", "11:00", "Beard")
db.insert_appointment(id_maria, "2026-10-02", "10:00", "Haircut & Beard")
db.insert_appointment(id_juan, "2026-10-10", "09:30", "Haircut")
db.insert_appointment(id_no_name, "2026-10-15", "16:00", None)  # no service

log(
    "SEED - clients created",
    [
        f"id={id_carlos}  -> Carlos Lopez  | phone: 666111222 (normalized)",
        f"id={id_maria}   -> Maria Gomez   | phone: 677888999 (normalized, +34 and dashes removed)",
        f"id={id_juan}    -> Juan (no last name)",
        f"id={id_no_name} -> (no name, phone only)",
    ],
)

# ─────────────────────────────────────────────
# TEST 1 — get_or_create_client: existing client
# Expected: returns same id, no duplicate inserted
# ─────────────────────────────────────────────
id_repeated = db.get_or_create_client("666111222")
log(
    "TEST 1 - get_or_create_client (existing client)",
    f"Returned id={id_repeated} | Expected: {id_carlos} | Pass: {id_repeated == id_carlos}",
)

# ─────────────────────────────────────────────
# TEST 2 — get_appointments_with_client (JOIN, optional filters)
# Expected: returns appointment_id, name, phone alongside appointment data
# ─────────────────────────────────────────────
rows = db.get_appointments_with_client(date="2026-10-02")
log(
    "TEST 2 - get_appointments_with_client(date='2026-10-02')",
    [{col: row[col] for col in row.keys()} for row in rows],
)
log("  -> columns returned", list(rows[0].keys()) if rows else "No rows")

# ─────────────────────────────────────────────
# TEST 3 — get_day_appointments (today filtered automatically)
# Expected: 0 rows because today != 2026-10-02 (correct behaviour)
# ─────────────────────────────────────────────
rows_today = db.get_day_appointments()
log(
    "TEST 3 - get_day_appointments() [today != 2026-10-02 -> 0 rows expected]",
    [{col: row[col] for col in row.keys()} for row in rows_today]
    or "No appointments today (correct)",
)

# ─────────────────────────────────────────────
# TEST 4 — delete_appointment
# Expected: rowcount = 1 on success, 0 if id not found
# ─────────────────────────────────────────────
db.cursor.execute(
    "SELECT appointment_id FROM appointments ORDER BY appointment_id LIMIT 1"
)
first_id = db.cursor.fetchone()["appointment_id"]
deleted = db.delete_appointment(first_id)
log(
    "TEST 4 - delete_appointment",
    f"Deleted appointment_id={first_id} | rowcount={deleted} (1=success, 0=not found)",
)

# ─────────────────────────────────────────────
# TEST 5 — update_appointment (partial update, dynamic SQL)
# Expected: only the passed fields change, others stay untouched
# ─────────────────────────────────────────────
db.cursor.execute(
    "SELECT appointment_id FROM appointments ORDER BY appointment_id LIMIT 1"
)
appt_id = db.cursor.fetchone()["appointment_id"]
updated = db.update_appointment(appt_id, time="13:00", service="Premium Haircut")
db.cursor.execute("SELECT * FROM appointments WHERE appointment_id = ?", (appt_id,))
row_after = db.cursor.fetchone()
log(
    "TEST 5 - update_appointment(time, service) — date must stay unchanged",
    {col: row_after[col] for col in row_after.keys()},
)

# Called with no fields -> must return 0 without touching the DB
no_change = db.update_appointment(appt_id)
log("  -> update_appointment() with no arguments", f"Returns: {no_change} (expected 0)")

# ─────────────────────────────────────────────
# TEST 6 — get_appointments_left_today
# Expected: 0 rows (all test appointments are past or on a different date)
# ─────────────────────────────────────────────
rows_left = db.get_appointments_left_today()
log(
    "TEST 6 - get_appointments_left_today()",
    [{col: row[col] for col in row.keys()} for row in rows_left]
    or "No remaining appointments today (correct)",
)
log(
    "  -> columns returned",
    list(rows_left[0].keys()) if rows_left else "No rows to inspect",
)

# ─────────────────────────────────────────────
# TEST 7 — get_all_appointments_left (today remaining + all future)
# Expected: future appointments (2026-10-10 and 2026-10-15) returned with client name+phone
# ─────────────────────────────────────────────
rows_future = db.get_all_appointments_left()
log(
    "TEST 7 - get_all_appointments_left()",
    [{col: row[col] for col in row.keys()} for row in rows_future],
)
log("  -> columns returned", list(rows_future[0].keys()) if rows_future else "No rows")

db.close_connection()
print("ALL TESTS COMPLETED")
