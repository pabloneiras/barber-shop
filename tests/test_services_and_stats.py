"""
tests/test_services_and_stats.py
Automated tests for v2 features:
- Services & pricing catalog CRUD
- Appointment price and color persistence
- Date-range appointment queries (weekly view)
- Revenue and service statistics aggregation
- FastAPI HTTP endpoints for services, range, and stats
Uses an isolated SQLite database and cleans it up on completion.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend/src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from app.database_manager import DatabaseManager
from fastapi.testclient import TestClient
import api.api as fastapi_module
from api.api import app

TEST_DB_PATH = Path(__file__).parent / "test_services_stats.db"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

db = DatabaseManager(TEST_DB_PATH)
db.connect()
db.create_tables()

# Point API to our test database
fastapi_module.db = db

passed = 0
total = 0

def check(name, condition, detail=""):
    global passed, total
    total += 1
    if condition:
        passed += 1
        print(f"  [PASS] {name} {detail}")
    else:
        print(f"  [FAIL] {name} {detail}")
        raise AssertionError(f"Test failed: {name}")

print("\n=== STARTING SERVICES & STATS TEST SUITE ===\n")

# 1. Default Services Seed
services = db.get_services()
check("1.1 Default services created", len(services) >= 4, f"Found {len(services)} services")
svc_names = [s["name"] for s in services]
check("1.2 Standard service names present", "Corte caballero" in svc_names and "Corte y barba" in svc_names)

# 2. Services CRUD
new_svc_id = db.create_service("Afeitado clásico", 9.5, "#06b6d4")
check("2.1 Create custom service", new_svc_id > 0, f"ID={new_svc_id}")

db.update_service(new_svc_id, price=10.0, default_color="#0891b2")
updated_svc = [s for s in db.get_services() if s["service_id"] == new_svc_id][0]
check("2.2 Update service price and color", updated_svc["price"] == 10.0 and updated_svc["default_color"] == "#0891b2")

# 3. Appointments with Price and Color
client_id = db.get_or_create_client("611222333", "Carlos", "Perez")

# Appointment with auto-fetched price & color from service
appt1_id = db.insert_appointment(client_id, "2026-10-20", "10:00", service="Corte caballero")
appt1 = db.get_appointment(appt1_id)
check("3.1 Insert appointment auto-price from service", appt1["price"] == 12.0 and appt1["color"] == "#3b82f6")

# Appointment with explicit custom price and color
appt2_id = db.insert_appointment(client_id, "2026-10-21", "11:30", service="Corte y barba", price=15.0, color="#f59e0b")
appt2 = db.get_appointment(appt2_id)
check("3.2 Insert appointment custom price & color", appt2["price"] == 15.0 and appt2["color"] == "#f59e0b")

# Update appointment price & color
db.update_appointment(appt2_id, price=16.5, color="#ec4899")
appt2_upd = db.get_appointment(appt2_id)
check("3.3 Update appointment price & color", appt2_upd["price"] == 16.5 and appt2_upd["color"] == "#ec4899")

# 4. Weekly Range Query
range_appts = db.get_appointments_range("2026-10-19", "2026-10-25")
check("4.1 Get appointments range", len(range_appts) == 2, f"Retrieved {len(range_appts)} appts")

empty_range = db.get_appointments_range("2026-11-01", "2026-11-07")
check("4.2 Get appointments empty range", len(empty_range) == 0)

# 5. Financial Statistics Aggregation
# Add a third appointment in range
db.insert_appointment(client_id, "2026-10-22", "16:00", service="Corte caballero", price=12.0)
stats = db.get_statistics("2026-10-19", "2026-10-25")
# appt1 (12.0) + appt2 (16.5) + appt3 (12.0) = 40.5
check("5.1 Total appointments in stats", stats["total_appointments"] == 3)
check("5.2 Total revenue in stats", abs(stats["total_revenue"] - 40.5) < 0.01, f"Revenue={stats['total_revenue']}")
check("5.3 Average ticket calculation", abs(stats["average_ticket"] - 13.5) < 0.01, f"Avg={stats['average_ticket']}")
check("5.4 Breakdown by service count", len(stats["services"]) == 2)

# 6. HTTP API Endpoints via TestClient
client = TestClient(app)

res_range = client.get("/appointments/range/?start_date=2026-10-19&end_date=2026-10-25")
check("6.1 GET /appointments/range/", res_range.status_code == 200 and len(res_range.json()) == 3)

res_services = client.get("/services/")
check("6.2 GET /services/", res_services.status_code == 200 and len(res_services.json()) >= 5)

res_post_svc = client.post("/services/", json={"name": "Tratamiento Keratina", "price": 25.0, "default_color": "#a855f7"})
check("6.3 POST /services/", res_post_svc.status_code == 200 and "service_id" in res_post_svc.json())
created_id = res_post_svc.json()["service_id"]

res_put_svc = client.put(f"/services/{created_id}", json={"price": 28.0})
check("6.4 PUT /services/{id}", res_put_svc.status_code == 200)

res_del_svc = client.delete(f"/services/{created_id}")
check("6.5 DELETE /services/{id}", res_del_svc.status_code == 200)

res_stats = client.get("/stats/?start_date=2026-10-19&end_date=2026-10-25")
check("6.6 GET /stats/", res_stats.status_code == 200 and res_stats.json()["total_appointments"] == 3)

# 7. Cleanup
db.close_connection()
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

print("\n" + "=" * 60)
print(f"SERVICES & STATS SUMMARY: {passed}/{total} PASSED (100% SUCCESS)")
print("=" * 60 + "\n")
