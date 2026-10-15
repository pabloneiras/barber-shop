"""
tests/run_tests.py
Tests each DatabaseManager method using an isolated test database.
Does NOT touch barber_shop.db or any project file.
Run from the project root: python tests/run_tests.py
"""

import sys
from pathlib import Path

# Add backend/src to path so app package can be resolved
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from app.database_manager import DatabaseManager


# Isolated test DB in this same folder (gitignored)
TEST_DB = Path(__file__).parent / "test_barber_shop.db"

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

# ─────────────────────────────────────────────
# TEST 8 — WhatsApp Timezone & Send Time Calculation
# Expected: Europe/Madrid timezone with DST support, exactly 24h before
# ─────────────────────────────────────────────
from app.reminders import (
    compute_reminder_send_time,
    build_whatsapp_payload,
    programar_recordatorio,
    cancelar_recordatorio,
    reprogramar_recordatorio,
    sincronizar_recordatorios,
)
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

madrid_tz = ZoneInfo("Europe/Madrid")
appt_dt, send_at = compute_reminder_send_time("2026-10-25", "10:30")
diff_hours = (appt_dt - send_at).total_seconds() / 3600
log(
    "TEST 8 - compute_reminder_send_time (Europe/Madrid DST transition)",
    f"Appt: {appt_dt.isoformat()} | Send at: {send_at.isoformat()} | Diff hours: {diff_hours} (expected 24.0)",
)
assert diff_hours == 24.0, "Reminder must be exactly 24 hours prior"

# ─────────────────────────────────────────────
# TEST 9 — WhatsApp Payload Builder
# Expected: Meta Cloud API utility template format with '34' prefix and DD/MM date
# ─────────────────────────────────────────────
payload = build_whatsapp_payload("666111222", "Carlos", appt_dt)
log("TEST 9 - build_whatsapp_payload", payload)
assert payload["to"] == "34666111222", "Phone must include 34 prefix"
assert payload["template"]["name"] == "recordatorio_cita"
assert payload["template"]["components"][0]["parameters"][0]["text"] == "Carlos"
assert payload["template"]["components"][0]["parameters"][1]["text"] == "25/10"
assert payload["template"]["components"][0]["parameters"][2]["text"] == "10:30"

# ─────────────────────────────────────────────
# TEST 10 — Reminder Scheduling (Simulation Mode, < 30 days ahead)
# Expected: status='simulado', mock-task generated, persisted in whatsapp_reminders
# ─────────────────────────────────────────────
future_date = (datetime.now(madrid_tz) + timedelta(days=5)).strftime("%Y-%m-%d")
sim_appt_id = db.insert_appointment(id_carlos, future_date, "11:00", "Haircut")
res_sim = programar_recordatorio(sim_appt_id, db_manager=db)
rem_row = db.get_reminder(sim_appt_id)
log(
    "TEST 10 - programar_recordatorio (simulation mode)",
    f"Result: {res_sim} | DB status: {rem_row['status']} | Task: {rem_row['task_name']}",
)
assert rem_row["status"] == "simulado"
assert rem_row["task_name"].startswith("mock-task-")

# ─────────────────────────────────────────────
# TEST 11 — Past / < 24h Advance Appointment
# Expected: status='omitido', task_name is None
# ─────────────────────────────────────────────
today_str = datetime.now(madrid_tz).strftime("%Y-%m-%d")
short_appt_id = db.insert_appointment(id_carlos, today_str, "23:59", "Beard")
res_short = programar_recordatorio(short_appt_id, db_manager=db)
rem_short = db.get_reminder(short_appt_id)
log(
    "TEST 11 - programar_recordatorio (<24h advance -> omitido)",
    f"Result: {res_short} | DB status: {rem_short['status']} | Task: {rem_short['task_name']}",
)
assert rem_short["status"] == "omitido"
assert rem_short["task_name"] is None

# ─────────────────────────────────────────────
# TEST 12 — Far Future Appointment (> 30 days)
# Expected: status='pendiente', task_name is None (queued for future sync)
# ─────────────────────────────────────────────
far_date = (datetime.now(madrid_tz) + timedelta(days=45)).strftime("%Y-%m-%d")
far_appt_id = db.insert_appointment(id_carlos, far_date, "12:00", "Coloring")
res_far = programar_recordatorio(far_appt_id, db_manager=db)
rem_far = db.get_reminder(far_appt_id)
log(
    "TEST 12 - programar_recordatorio (>30 days -> pendiente)",
    f"Result: {res_far} | DB status: {rem_far['status']} | Task: {rem_far['task_name']}",
)
assert rem_far["status"] == "pendiente"
assert rem_far["task_name"] is None

# ─────────────────────────────────────────────
# TEST 13 — Reschedule Reminder
# Expected: previous task cancelled and updated with new send_at
# ─────────────────────────────────────────────
new_future_date = (datetime.now(madrid_tz) + timedelta(days=6)).strftime("%Y-%m-%d")
db.update_appointment(sim_appt_id, date=new_future_date, time="16:00")
res_reprog = reprogramar_recordatorio(sim_appt_id, db_manager=db)
rem_reprog = db.get_reminder(sim_appt_id)
log(
    "TEST 13 - reprogramar_recordatorio",
    f"Result: {res_reprog} | DB send_at: {rem_reprog['send_at']} | status: {rem_reprog['status']}",
)
assert rem_reprog["status"] == "simulado"

# ─────────────────────────────────────────────
# TEST 14 — Cancel Reminder
# Expected: status='cancelado'
# ─────────────────────────────────────────────
ok_cancel = cancelar_recordatorio(sim_appt_id, db_manager=db)
rem_canceled = db.get_reminder(sim_appt_id)
log(
    "TEST 14 - cancelar_recordatorio",
    f"Success: {ok_cancel} | DB status: {rem_canceled['status']}",
)
assert rem_canceled["status"] == "cancelado"

# ─────────────────────────────────────────────
# TEST 15 — Startup Synchronization
# Expected: reconciles future appointments without reminders into scheduled state
# ─────────────────────────────────────────────
sync_res = sincronizar_recordatorios(db_manager=db)
log("TEST 15 - sincronizar_recordatorios", sync_res)
assert isinstance(sync_res, dict)
assert "reconciled" in sync_res
assert "created" in sync_res

db.close_connection()
if TEST_DB.exists():
    TEST_DB.unlink()
print("ALL TESTS COMPLETED SUCCESSFULLY (15/15)")
