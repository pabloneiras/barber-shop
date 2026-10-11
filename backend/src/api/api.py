from contextlib import asynccontextmanager
import logging
from pathlib import Path
from app.database import db
from app.reminders import (
    programar_recordatorio,
    cancelar_recordatorio,
    reprogramar_recordatorio,
    sincronizar_recordatorios,
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

logger = logging.getLogger("api")
FRONTEND_DIST = Path(__file__).resolve().parents[3] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: synchronize scheduled WhatsApp reminders
    try:
        sincronizar_recordatorios()
    except Exception as exc:
        logger.error("Error during reminder synchronization on startup: %s", exc)
    yield


app = FastAPI(title="Barber Shop API", lifespan=lifespan)

# Enable CORS for frontend integration (React development server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Output schema: Represents data returned to the client (GET requests).
# Includes appointment_id because the record already exists in the database.
class AppointmentResponse(BaseModel):
    appointment_id: int
    name: str 
    last_name: str | None = None
    phone: str
    appointment_date: str
    appointment_time: str
    service: str | None = None


# Input schema: Represents incoming data from the client to create an appointment (POST requests).
# Does NOT include appointment_id because the database generates it automatically via AUTOINCREMENT.
class AppointmentCreate(BaseModel):
    phone: str
    appointment_date: str
    appointment_time: str
    name: str
    last_name: str | None = None
    service: str | None = None

#For the put
class AppointmentUpdate(BaseModel):
    appointment_date: str | None = None
    appointment_time: str | None = None
    service: str | None = None


# Autocomplete search response schema for clients
class ClientSearchResponse(BaseModel):
    client_id: int
    phone: str
    name: str | None = None
    last_name: str | None = None
    visits_count: int = 0
    last_service: str | None = None



# Health check & Frontend root: serves React app if built, otherwise JSON status
@app.get("/")
def root():
    index_file = FRONTEND_DIST / "index.html"
    if FRONTEND_DIST.exists() and index_file.exists():
        return FileResponse(index_file)
    return {"message": "API de Barber Shop funcionando"}


# Searches clients by substring query for autocompletion.
@app.get("/clients/search", response_model=list[ClientSearchResponse])
def fapi_search_clients(q: str = ""):
    if not q or not q.strip():
        return []
    return [dict(row) for row in db.search_clients(q.strip())]



# Retrieves remaining appointments scheduled for today from the current time onward.
@app.get("/appointments/today/left", response_model=list[AppointmentResponse])
def fapi_get_all_appointments_left_today():
    return [dict(row) for row in db.get_appointments_left_today()]


# Retrieves all appointments scheduled for the entire current day.
@app.get("/appointments/today/")
def fapi_get_all_appointments_today():
    return [dict(row) for row in db.get_day_appointments()]


# Retrieves all appointments scheduled for a specific date (YYYY-MM-DD).
@app.get("/appointments/date/{appointment_date}", response_model=list[AppointmentResponse])
def fapi_get_appointments_by_date(appointment_date: str):
    return [dict(row) for row in db.get_appointments_with_client(date=appointment_date)]



# Retrieves all pending appointments from the current moment into the future.
@app.get("/appointments/left")
def fapi_get_all_appointments_left():
    return [dict(row) for row in db.get_all_appointments_left()]


# Retrieves the full appointment history for a specific client identified by client_id.
@app.get("/appointments/clients/{client_id}")
def fapi_get_appointments_client(client_id: int):
    rows_json = db.get_appointments_with_client(client_id)
    return [dict(row) for row in rows_json]


# Single resource lookup: uses {appointment_id} in the path because the appointment already exists.
# In REST design, path parameters identify a unique existing resource within the collection.
# Reuses AppointmentResponse (without list) because it returns a single matching appointment object.
@app.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
def fapi_get_appointment(appointment_id: int):
    row = db.get_appointment(appointment_id)
    return dict(row)


# Creation (POST): targets the collection endpoint without an ID because the appointment does not exist yet.
# The client sends payload data in the HTTP request body; the database generates the primary key via AUTOINCREMENT.
# Automatically links an existing client or creates a new one via get_or_create_client before inserting.
@app.post("/appointments/")
def fapi_intert_post_appointment(appointment: AppointmentCreate):
    client_id = db.get_or_create_client(appointment.phone, appointment.name, appointment.last_name)
    appointment_id = db.insert_appointment(client_id, appointment.appointment_date, appointment.appointment_time, appointment.service)
    try:
        programar_recordatorio(appointment_id)
    except Exception as exc:
        logger.error("Error scheduling reminder for appointment #%s: %s", appointment_id, exc)
    return {"mensaje": "cita creada correctamente", "appointment_id": appointment_id}


# Update (PUT): targets {appointment_id} in the URL because it modifies a specific existing appointment.
# In REST architecture, modification requests must specify exactly which record to update via its path ID.
# Uses AppointmentUpdate so the client only sends the fields they want to change (date, time, service).
@app.put("/appointments/{appointment_id}")
def fapi_put_updt_appointment(appointment_id: int, new_appointment: AppointmentUpdate):
    existent_appointment = db.get_appointment(appointment_id)
    if existent_appointment:
        bool_rc = db.update_appointment(
            appointment_id,
            date=new_appointment.appointment_date,
            time=new_appointment.appointment_time,
            service=new_appointment.service,
        )
        if bool_rc == 1:
            if new_appointment.appointment_date is not None or new_appointment.appointment_time is not None:
                try:
                    reprogramar_recordatorio(appointment_id)
                except Exception as exc:
                    logger.error("Error rescheduling reminder for appointment #%s: %s", appointment_id, exc)
            return {"mensaje": "cita actualizada correctamente"}
        else:
            return {"mensaje": "no se realizaron cambios"}
    else:
        return {"mensaje": "cita no encontrada"}


# Deletion (DELETE): targets {appointment_id} in the path to cancel/remove a specific appointment.
@app.delete("/appointments/{appointment_id}")
def fapi_delete_appointment(appointment_id: int):
    try:
        cancelar_recordatorio(appointment_id)
    except Exception as exc:
        logger.error("Error canceling reminder for appointment #%s: %s", appointment_id, exc)
    bool_dl = db.delete_appointment(appointment_id)
    if bool_dl == 0:
        return {"mensaje": "la cita no existia"}
    else:
        return {"mensaje": "cita eliminada"}


# Single reminder lookup: returns the WhatsApp reminder details and schedule status
@app.get("/appointments/{appointment_id}/reminder")
def fapi_get_appointment_reminder(appointment_id: int):
    reminder = db.get_reminder(appointment_id)
    if reminder:
        return dict(reminder)
    return {"mensaje": "recordatorio no encontrado"}


# Mount production frontend static assets and SPA route handling when built
if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend_spa(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"mensaje": "Frontend not found"}

