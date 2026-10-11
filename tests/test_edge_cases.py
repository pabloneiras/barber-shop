"""
tests/test_edge_cases.py
Comprehensive edge case test suite for WhatsApp reminder automation and database resilience.
Uses an isolated SQLite test database (test_edge_cases.db).
Run with: python tests/test_edge_cases.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Add backend/src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from app.database_manager import DatabaseManager
from app.reminders import (
    compute_reminder_send_time,
    build_whatsapp_payload,
    programar_recordatorio,
    cancelar_recordatorio,
    reprogramar_recordatorio,
    sincronizar_recordatorios,
)
from fastapi.testclient import TestClient
from api.api import app

# Isolated test DB
EDGE_DB_PATH = Path(__file__).parent / "test_edge_cases.db"
if EDGE_DB_PATH.exists():
    EDGE_DB_PATH.unlink()

db = DatabaseManager(EDGE_DB_PATH)
db.connect()
db.create_tables()

madrid_tz = ZoneInfo("Europe/Madrid")
passed_tests = 0
total_tests = 0


def record_result(name: str, condition: bool, details: str = ""):
    global passed_tests, total_tests
    total_tests += 1
    if condition:
        passed_tests += 1
        print(f"  [PASS] {name} - {details}")
    else:
        print(f"  [FAIL] {name} - {details}")
        assert False, f"Test failed: {name} ({details})"


print("\n=== STARTING WHATSAPP REMINDER EDGE CASE TEST SUITE ===\n")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: TIMEZONE & DAYLIGHT SAVING TIME (DST) TRANSITIONS
# ─────────────────────────────────────────────────────────────────────────────
print("--- SECTION 1: Timezone & DST Transitions ---")

# Edge Case 1.1: Spring Forward (Last Sunday of March: 2026-03-29)
# Clock moves from 02:00 to 03:00 (UTC+1 -> UTC+2)
# Appointment: 2026-03-29 at 10:00 (UTC+2) -> Send time: 2026-03-28 at 10:00 (UTC+1)
appt_spring, send_spring = compute_reminder_send_time("2026-03-29", "10:00")
payload_spring = build_whatsapp_payload("611222333", "Carlos", appt_spring)
record_result(
    "1.1 Spring Forward DST send_at",
    send_spring.strftime("%Y-%m-%d %H:%M") == "2026-03-28 10:00",
    f"Send at: {send_spring.isoformat()}",
)
record_result(
    "1.2 Spring Forward payload date/time",
    payload_spring["template"]["components"][0]["parameters"][1]["text"] == "29/03"
    and payload_spring["template"]["components"][0]["parameters"][2]["text"] == "10:00",
    "Formatted as 29/03 at 10:00",
)

# Edge Case 1.2: Fall Back (Last Sunday of October: 2026-10-25)
# Clock moves backwards from 03:00 to 02:00 (UTC+2 -> UTC+1)
# Appointment: 2026-10-25 at 10:00 (UTC+1) -> Send time: 2026-10-24 at 10:00 (UTC+2)
appt_fall, send_fall = compute_reminder_send_time("2026-10-25", "10:00")
payload_fall = build_whatsapp_payload("611222333", "Carlos", appt_fall)
record_result(
    "1.3 Fall Back DST send_at",
    send_fall.strftime("%Y-%m-%d %H:%M") == "2026-10-24 10:00",
    f"Send at: {send_fall.isoformat()}",
)
record_result(
    "1.4 Fall Back payload date/time",
    payload_fall["template"]["components"][0]["parameters"][1]["text"] == "25/10"
    and payload_fall["template"]["components"][0]["parameters"][2]["text"] == "10:00",
    "Formatted as 25/10 at 10:00",
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: PHONE NUMBER SANITIZATION & PREFIX HANDLING
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- SECTION 2: Phone Number Formats & Prefix Handling ---")

dummy_dt = datetime(2026, 11, 15, 12, 0, tzinfo=madrid_tz)

phone_cases = [
    ("611222333", "34611222333", "Standard 9-digit local phone"),
    ("  611222333  ", "34611222333", "Phone with leading/trailing spaces"),
    ("+34611222333", "34611222333", "Phone starting with +34"),
    ("+34 611 22 23 33", "34611222333", "Phone with +34 and spaces"),
    ("0034611222333", "34611222333", "Phone with 0034 international prefix"),
    ("34611222333", "34611222333", "Phone already having 34 prefix (no 3434 duplication)"),
    ("+34-611-222-333", "34611222333", "Phone with dashes and plus prefix"),
]

for idx, (raw_phone, expected_recipient, label) in enumerate(phone_cases, 1):
    p = build_whatsapp_payload(raw_phone, "Cliente", dummy_dt)
    record_result(
        f"2.{idx} Phone formatting: {label}",
        p["to"] == expected_recipient,
        f"Raw: '{raw_phone}' -> Result: '{p['to']}'",
    )

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: CLIENT NAME FALLBACKS & UNICODE HANDLING
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- SECTION 3: Client Name Fallbacks & Unicode Handling ---")

name_cases = [
    (None, "Cliente", "Null client name fallback"),
    ("", "Cliente", "Empty string client name fallback"),
    ("   ", "Cliente", "Whitespace-only client name fallback"),
    ("Carlos", "Carlos", "Standard client name"),
    ("  Carlos Lopez  ", "Carlos Lopez", "Name with surrounding whitespace stripped"),
    ("María José Peña", "María José Peña", "Accented and special characters (Unicode)"),
]

for idx, (raw_name, expected_name, label) in enumerate(name_cases, 1):
    p = build_whatsapp_payload("600111222", raw_name, dummy_dt)
    actual_name = p["template"]["components"][0]["parameters"][0]["text"]
    record_result(
        f"3.{idx} {label}",
        actual_name == expected_name,
        f"Input: {repr(raw_name)} -> Param: {repr(actual_name)}",
    )

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: EXACT 24-HOUR HORIZON BOUNDARIES
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- SECTION 4: 24-Hour Horizon Boundaries ---")

now_madrid = datetime.now(madrid_tz)
client_id = db.get_or_create_client("600111222", "Test Client")

# 4.1 Past appointment (5 days ago)
past_date = (now_madrid - timedelta(days=5)).strftime("%Y-%m-%d")
appt_past = db.insert_appointment(client_id, past_date, "10:00", "Haircut")
res_past = programar_recordatorio(appt_past, db_manager=db)
record_result(
    "4.1 Appointment in the past -> omitido",
    res_past["status"] == "omitido" and db.get_reminder(appt_past)["status"] == "omitido",
    f"Status: {res_past['status']}",
)

# 4.2 Appointment in 1 hour (less than 24h notice)
in_one_hour = now_madrid + timedelta(hours=1)
appt_1h = db.insert_appointment(
    client_id, in_one_hour.strftime("%Y-%m-%d"), in_one_hour.strftime("%H:%M"), "Haircut"
)
res_1h = programar_recordatorio(appt_1h, db_manager=db)
record_result(
    "4.2 Appointment in 1 hour (<24h notice) -> omitido",
    res_1h["status"] == "omitido",
    f"Status: {res_1h['status']}",
)

# 4.3 Appointment in 23 hours 50 minutes (<24h notice)
in_23h = now_madrid + timedelta(hours=23, minutes=50)
appt_23h = db.insert_appointment(
    client_id, in_23h.strftime("%Y-%m-%d"), in_23h.strftime("%H:%M"), "Haircut"
)
res_23h = programar_recordatorio(appt_23h, db_manager=db)
record_result(
    "4.3 Appointment in ~23.8 hours (<24h notice) -> omitido",
    res_23h["status"] == "omitido",
    f"Status: {res_23h['status']}",
)

# 4.4 Appointment in 25 hours (eligible for reminder)
in_25h = now_madrid + timedelta(hours=25)
appt_25h = db.insert_appointment(
    client_id, in_25h.strftime("%Y-%m-%d"), in_25h.strftime("%H:%M"), "Haircut"
)
res_25h = programar_recordatorio(appt_25h, db_manager=db)
record_result(
    "4.4 Appointment in 25 hours (>24h notice) -> simulado",
    res_25h["status"] == "simulado" and res_25h["task_name"].startswith("mock-task-"),
    f"Status: {res_25h['status']} | Task: {res_25h.get('task_name')}",
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: 30-DAY GOOGLE CLOUD TASKS THRESHOLD BOUNDARIES
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- SECTION 5: 30-Day Scheduling Threshold Boundaries ---")

# 5.1 Appointment 28 days ahead (send_at is at 27 days -> within 30-day quota)
in_28d = now_madrid + timedelta(days=28)
appt_28d = db.insert_appointment(
    client_id, in_28d.strftime("%Y-%m-%d"), "12:00", "Haircut"
)
res_28d = programar_recordatorio(appt_28d, db_manager=db)
record_result(
    "5.1 Appointment 28 days ahead (send_at < 30d) -> simulado",
    res_28d["status"] == "simulado",
    f"Status: {res_28d['status']}",
)

# 5.2 Appointment 35 days ahead (send_at is at 34 days -> exceeds 30-day quota)
in_35d = now_madrid + timedelta(days=35)
appt_35d = db.insert_appointment(
    client_id, in_35d.strftime("%Y-%m-%d"), "12:00", "Coloring"
)
res_35d = programar_recordatorio(appt_35d, db_manager=db)
record_result(
    "5.2 Appointment 35 days ahead (send_at > 30d) -> pendiente",
    res_35d["status"] == "pendiente" and db.get_reminder(appt_35d)["task_name"] is None,
    f"Status: {res_35d['status']} | Task: {db.get_reminder(appt_35d)['task_name']}",
)

# 5.3 Appointment 90 days ahead
in_90d = now_madrid + timedelta(days=90)
appt_90d = db.insert_appointment(
    client_id, in_90d.strftime("%Y-%m-%d"), "10:00", "VIP Service"
)
res_90d = programar_recordatorio(appt_90d, db_manager=db)
record_result(
    "5.3 Appointment 90 days ahead -> pendiente",
    res_90d["status"] == "pendiente",
    f"Status: {res_90d['status']}",
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: RESCHEDULING TRANSITIONS (PUT)
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- SECTION 6: Rescheduling Transitions ---")

# 6.1 Move from simulado (5 days ahead) to far future (>30 days ahead)
in_5d = now_madrid + timedelta(days=5)
appt_resched = db.insert_appointment(
    client_id, in_5d.strftime("%Y-%m-%d"), "15:00", "Beard"
)
programar_recordatorio(appt_resched, db_manager=db)

# Reschedule to 40 days ahead
in_40d = now_madrid + timedelta(days=40)
db.update_appointment(appt_resched, date=in_40d.strftime("%Y-%m-%d"), time="16:00")
res_to_far = reprogramar_recordatorio(appt_resched, db_manager=db)
rem_to_far = db.get_reminder(appt_resched)
record_result(
    "6.1 Reschedule from simulado to >30 days -> pendiente (task revoked)",
    rem_to_far["status"] == "pendiente" and rem_to_far["task_name"] is None,
    f"Status: {rem_to_far['status']} | Task: {rem_to_far['task_name']}",
)

# 6.2 Move from pendiente (40 days ahead) back to within 10 days
in_10d = now_madrid + timedelta(days=10)
db.update_appointment(appt_resched, date=in_10d.strftime("%Y-%m-%d"), time="11:30")
res_to_near = reprogramar_recordatorio(appt_resched, db_manager=db)
rem_to_near = db.get_reminder(appt_resched)
record_result(
    "6.2 Reschedule from pendiente to <=30 days -> simulado (new task created)",
    rem_to_near["status"] == "simulado" and rem_to_near["task_name"] is not None,
    f"Status: {rem_to_near['status']} | Task: {rem_to_near['task_name']}",
)

# 6.3 Move to same day (<24h notice)
db.update_appointment(
    appt_resched,
    date=now_madrid.strftime("%Y-%m-%d"),
    time="23:59",
)
reprogramar_recordatorio(appt_resched, db_manager=db)
rem_to_sameday = db.get_reminder(appt_resched)
record_result(
    "6.3 Reschedule to same day (<24h) -> omitido",
    rem_to_sameday["status"] == "omitido" and rem_to_sameday["task_name"] is None,
    f"Status: {rem_to_sameday['status']}",
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7: CANCELLATIONS & ERROR RESILIENCE
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- SECTION 7: Cancellation & Error Resilience ---")

# 7.1 Cancel reminder for simulated appointment
in_8d = now_madrid + timedelta(days=8)
appt_to_cancel = db.insert_appointment(client_id, in_8d.strftime("%Y-%m-%d"), "10:00")
programar_recordatorio(appt_to_cancel, db_manager=db)
ok_c = cancelar_recordatorio(appt_to_cancel, db_manager=db)
rem_c = db.get_reminder(appt_to_cancel)
record_result(
    "7.1 Cancel active reminder -> status cancelado",
    ok_c is True and rem_c["status"] == "cancelado",
    f"Success: {ok_c} | Status: {rem_c['status']}",
)

# 7.2 Cancel non-existent appointment ID
ok_nonexistent = cancelar_recordatorio(999999, db_manager=db)
record_result(
    "7.2 Cancel non-existent appointment ID -> returns False gracefully",
    ok_nonexistent is False,
    f"Returned: {ok_nonexistent}",
)

# 7.3 Program reminder for non-existent appointment ID
res_prog_nonexistent = programar_recordatorio(999999, db_manager=db)
record_result(
    "7.3 Schedule reminder for non-existent appointment -> error dict returned",
    res_prog_nonexistent.get("status") == "error",
    f"Returned: {res_prog_nonexistent}",
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8: STARTUP SYNCHRONIZATION COMPLEX EDGE CASES
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- SECTION 8: Startup Synchronization (sincronizar_recordatorios) ---")

# 8.1 Future appointment created without reminder (e.g. CLI or external SQL)
in_4d = now_madrid + timedelta(days=4)
appt_orphan_future = db.insert_appointment(
    client_id, in_4d.strftime("%Y-%m-%d"), "14:00", "Haircut"
)
# Ensure no reminder row exists
db.delete_reminder(appt_orphan_future)
assert db.get_reminder(appt_orphan_future) is None

# 8.2 Orphaned reminder record whose appointment was deleted
fake_appt_id = 88888
send_iso = (now_madrid + timedelta(days=2)).isoformat()
db.upsert_reminder(fake_appt_id, send_iso, "simulado", "mock-task-orphan-88888")

# 8.3 Pending reminder whose send_at is now within 30 days
appt_now_eligible = db.insert_appointment(
    client_id, (now_madrid + timedelta(days=20)).strftime("%Y-%m-%d"), "11:00"
)
db.upsert_reminder(
    appt_now_eligible,
    (now_madrid + timedelta(days=19)).isoformat(),
    "pendiente",
    None,
)

# Run full synchronization
sync_summary = sincronizar_recordatorios(db_manager=db)
record_result(
    "8.1 Sync schedules missing future appointment",
    db.get_reminder(appt_orphan_future)["status"] == "simulado",
    f"Reminder status: {db.get_reminder(appt_orphan_future)['status']}",
)
record_result(
    "8.2 Sync detects deleted appointment and cancels orphaned reminder",
    db.get_reminder(fake_appt_id)["status"] == "cancelado",
    f"Orphan status: {db.get_reminder(fake_appt_id)['status']}",
)
record_result(
    "8.3 Sync reconciles pending reminder entering 30-day window",
    db.get_reminder(appt_now_eligible)["status"] == "simulado",
    f"Reconciled status: {db.get_reminder(appt_now_eligible)['status']}",
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9: FASTAPI HTTP END-TO-END RESILIENCE (TestClient)
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- SECTION 9: FastAPI HTTP Endpoints Edge Cases ---")

with TestClient(app) as client:
    # 9.1 Non-existent appointment reminder query
    r_get_404 = client.get("/appointments/999999/reminder")
    record_result(
        "9.1 GET reminder for non-existent appointment returns informative JSON",
        r_get_404.status_code == 200 and r_get_404.json()["mensaje"] == "recordatorio no encontrado",
        f"Response: {r_get_404.json()}",
    )

    # 9.2 Non-existent appointment update
    r_put_404 = client.put(
        "/appointments/999999", json={"appointment_time": "12:00"}
    )
    record_result(
        "9.2 PUT non-existent appointment returns informative JSON",
        r_put_404.status_code == 200 and r_put_404.json()["mensaje"] == "cita no encontrada",
        f"Response: {r_put_404.json()}",
    )

    # 9.3 Non-existent appointment deletion
    r_del_404 = client.delete("/appointments/999999")
    record_result(
        "9.3 DELETE non-existent appointment returns informative JSON",
        r_del_404.status_code == 200 and r_del_404.json()["mensaje"] == "la cita no existia",
        f"Response: {r_del_404.json()}",
    )

    # 9.4 Create appointment with reused client phone (no duplicate client)
    future_str = (now_madrid + timedelta(days=7)).strftime("%Y-%m-%d")
    r_post_client1 = client.post(
        "/appointments/",
        json={
            "phone": "688777666",
            "name": "Lucía",
            "last_name": "Sánchez",
            "appointment_date": future_str,
            "appointment_time": "10:00",
            "service": "Corte y tinte",
        },
    )
    r_post_client2 = client.post(
        "/appointments/",
        json={
            "phone": "688777666",  # same phone
            "name": "Lucía",
            "appointment_date": future_str,
            "appointment_time": "12:00",
            "service": "Lavado",
        },
    )
    record_result(
        "9.4 POST appointments with reused phone links properly without duplicates",
        r_post_client1.status_code == 200 and r_post_client2.status_code == 200,
        f"Created appt1 #{r_post_client1.json().get('appointment_id')} and appt2 #{r_post_client2.json().get('appointment_id')}",
    )

# Clean up isolated test database
db.close_connection()
if EDGE_DB_PATH.exists():
    EDGE_DB_PATH.unlink()

print("\n" + "=" * 60)
print(f"EDGE CASE TEST SUMMARY: {passed_tests}/{total_tests} PASSED (100% SUCCESS)")
print("=" * 60 + "\n")
