import os
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from app.database import db

# Automatically load environment variables from .env in project root if present
def _load_env_file():
    candidates = [
        Path(__file__).resolve().parents[3] / ".env",
        Path.cwd() / ".env",
    ]
    for env_path in candidates:
        if env_path.is_file():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, val = line.split("=", 1)
                            key = key.strip()
                            val = val.strip().strip('"').strip("'")
                            if key not in os.environ:
                                os.environ[key] = val
                break
            except Exception:
                pass

_load_env_file()

# Set up logging for reminder automation
logger = logging.getLogger("reminders")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# Optional import of Google Cloud Tasks library with graceful fallback
try:
    from google.cloud import tasks_v2
    from google.protobuf import timestamp_pb2
    HAS_GCP_LIBRARY = True
except ImportError:
    HAS_GCP_LIBRARY = False


def has_cloud_credentials() -> bool:
    # Verifies if all necessary Meta and Google Cloud environment variables are defined
    return bool(
        HAS_GCP_LIBRARY
        and os.getenv("META_ACCESS_TOKEN")
        and os.getenv("META_PHONE_NUMBER_ID")
        and os.getenv("GCP_PROJECT")
        and os.getenv("GCP_LOCATION")
        and os.getenv("GCP_QUEUE")
    )


def compute_reminder_send_time(appointment_date: str, appointment_time: str) -> tuple[datetime, datetime]:
    # Calculates appointment datetime and send time (24h before) in Europe/Madrid timezone
    tz = ZoneInfo("Europe/Madrid")
    appointment_dt = datetime.fromisoformat(f"{appointment_date}T{appointment_time}").replace(tzinfo=tz)
    send_at_dt = appointment_dt - timedelta(hours=24)
    return appointment_dt, send_at_dt


def build_whatsapp_payload(phone: str, name: str | None, appointment_dt: datetime) -> dict:
    # Formats the Meta Cloud API utility template payload
    clean_phone = phone.strip().replace("+", "").replace("-", "").replace(" ", "")
    if clean_phone.startswith("0034"):
        clean_phone = clean_phone[4:]
    recipient_phone = clean_phone if clean_phone.startswith("34") else f"34{clean_phone}"
    client_name = name.strip() if name and name.strip() else "Cliente"
    date_formatted = appointment_dt.strftime("%d/%m")
    time_formatted = appointment_dt.strftime("%H:%M")

    template_name = os.getenv("META_TEMPLATE_NAME", "recordatorio_cita")
    template_lang = os.getenv("META_TEMPLATE_LANG", "es")

    return {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": template_lang},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": client_name},
                        {"type": "text", "text": date_formatted},
                        {"type": "text", "text": time_formatted},
                    ],
                }
            ],
        },
    }


def schedule_cloud_task(send_at_dt: datetime, payload: dict) -> str:
    # Schedules an HTTP target task in Google Cloud Tasks targeting Meta Cloud API
    if not has_cloud_credentials():
        raise RuntimeError("Cloud credentials not configured")

    project = os.getenv("GCP_PROJECT")
    location = os.getenv("GCP_LOCATION", "europe-west1")
    queue = os.getenv("GCP_QUEUE", "recordatorios-whatsapp")
    meta_token = os.getenv("META_ACCESS_TOKEN")
    phone_number_id = os.getenv("META_PHONE_NUMBER_ID")
    api_version = os.getenv("META_API_VERSION", "v21.0")

    url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"

    client = tasks_v2.CloudTasksClient()
    queue_path = client.queue_path(project, location, queue)

    schedule_timestamp = timestamp_pb2.Timestamp()
    schedule_timestamp.FromDatetime(send_at_dt.astimezone(timezone.utc))

    import json
    task = {
        "schedule_time": schedule_timestamp,
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": url,
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {meta_token}",
            },
            "body": json.dumps(payload).encode("utf-8"),
        },
    }

    created_task = client.create_task(parent=queue_path, task=task)
    return created_task.name


def delete_cloud_task(task_name: str) -> bool:
    # Deletes an existing scheduled task in Google Cloud Tasks
    if not has_cloud_credentials() or not task_name:
        return False
    try:
        client = tasks_v2.CloudTasksClient()
        client.delete_task(name=task_name)
        logger.info("Successfully deleted Cloud Task: %s", task_name)
        return True
    except Exception as exc:
        logger.error("Failed to delete Cloud Task %s: %s", task_name, exc)
        return False


def programar_recordatorio(appointment_id: int, db_manager=None) -> dict:
    # Main workflow: calculates send time, schedules task (or mock), and updates database
    target_db = db_manager or db
    appointment = target_db.get_appointment(appointment_id)
    if not appointment:
        logger.warning("Cannot schedule reminder: Appointment #%s not found", appointment_id)
        return {"status": "error", "message": "Appointment not found"}

    appt_dict = dict(appointment)
    appt_dt, send_at_dt = compute_reminder_send_time(
        appt_dict["appointment_date"], appt_dict["appointment_time"]
    )

    send_at_iso = send_at_dt.astimezone(timezone.utc).isoformat()
    now_dt = datetime.now(ZoneInfo("Europe/Madrid"))

    # Case 1: Send time is already in the past (appointment created less than 24h in advance)
    if send_at_dt <= now_dt:
        logger.info(
            "[WHATSAPP] Cita #%s creada con menos de 24h de antelacion (send_at en el pasado). Omitiendo.",
            appointment_id
        )
        target_db.upsert_reminder(appointment_id, send_at_iso, "omitido", task_name=None)
        return {"status": "omitido", "send_at": send_at_iso}

    # Case 2: Send time exceeds Google Cloud Tasks maximum scheduling horizon (30 days)
    if send_at_dt > now_dt + timedelta(days=30):
        logger.info(
            "[WHATSAPP] Cita #%s a mas de 30 dias vista. Guardada como 'pendiente' para sincronizacion.",
            appointment_id
        )
        target_db.upsert_reminder(appointment_id, send_at_iso, "pendiente", task_name=None)
        return {"status": "pendiente", "send_at": send_at_iso}

    payload = build_whatsapp_payload(
        appt_dict["phone"], appt_dict["name"], appt_dt
    )

    # Case 3: Real cloud execution when credentials are provided
    if has_cloud_credentials():
        try:
            task_name = schedule_cloud_task(send_at_dt, payload)
            target_db.upsert_reminder(appointment_id, send_at_iso, "programado", task_name=task_name)
            logger.info("Cloud Task creada con exito para cita #%s: %s", appointment_id, task_name)
            return {"status": "programado", "task_name": task_name, "send_at": send_at_iso}
        except Exception as exc:
            logger.error("Error al crear Cloud Task para cita #%s: %s", appointment_id, exc)
            target_db.upsert_reminder(appointment_id, send_at_iso, "pendiente", task_name=None)
            return {"status": "pendiente", "error": str(exc)}

    # Case 4: Simulation mode (no credentials configured)
    mock_task_name = f"mock-task-{appointment_id}-{int(datetime.now().timestamp())}"
    target_db.upsert_reminder(appointment_id, send_at_iso, "simulado", task_name=mock_task_name)
    logger.info(
        "[WHATSAPP MOCK] Programado recordatorio para cita #%s (%s a las %s) -> Envio: %s | Tarea: %s",
        appointment_id,
        appt_dict["name"] or "Cliente",
        appt_dict["appointment_time"],
        send_at_iso,
        mock_task_name,
    )
    return {"status": "simulado", "task_name": mock_task_name, "send_at": send_at_iso}


def cancelar_recordatorio(appointment_id: int, db_manager=None) -> bool:
    # Cancels an existing reminder, deleting the task from the cloud if scheduled
    target_db = db_manager or db
    reminder = target_db.get_reminder(appointment_id)
    if not reminder:
        return False

    rem_dict = dict(reminder)
    task_name = rem_dict.get("task_name")

    if task_name and not task_name.startswith("mock-task-"):
        delete_cloud_task(task_name)

    target_db.update_reminder_status(appointment_id, "cancelado")
    logger.info("[WHATSAPP] Recordatorio de cita #%s marcado como cancelado", appointment_id)
    return True


def reprogramar_recordatorio(appointment_id: int, db_manager=None) -> dict:
    # Cancels existing task and schedules a new one with updated appointment date/time
    cancelar_recordatorio(appointment_id, db_manager=db_manager)
    return programar_recordatorio(appointment_id, db_manager=db_manager)


def sincronizar_recordatorios(db_manager=None) -> dict:
    # Reconciles pending appointments into Cloud Tasks (runs at FastAPI startup lifespan)
    target_db = db_manager or db
    logger.info("[WHATSAPP SYNC] Iniciando sincronizacion de recordatorios...")
    now_dt = datetime.now(ZoneInfo("Europe/Madrid"))
    thirty_days_ahead = now_dt + timedelta(days=30)

    # 1. Fetch pending reminders whose send_at is now within 30 days
    target_db.cursor.execute("SELECT * FROM whatsapp_reminders WHERE status = 'pendiente'")
    pending_rows = target_db.cursor.fetchall()
    reconciled_count = 0

    for row in pending_rows:
        row_dict = dict(row)
        appt_id = row_dict["appointment_id"]
        send_at_dt = datetime.fromisoformat(row_dict["send_at"])
        if send_at_dt <= thirty_days_ahead:
            programar_recordatorio(appt_id, db_manager=target_db)
            reconciled_count += 1

    # 2. Check future appointments that don't have a record in whatsapp_reminders
    future_appts = target_db.get_all_appointments_left()
    created_count = 0
    for appt in future_appts:
        appt_dict = dict(appt)
        appt_id = appt_dict["appointment_id"]
        existing = target_db.get_reminder(appt_id)
        if not existing:
            programar_recordatorio(appt_id, db_manager=target_db)
            created_count += 1

    # 3. Check reminders whose appointment was deleted (e.g. from main.py)
    target_db.cursor.execute(
        """
        SELECT whatsapp_reminders.appointment_id, whatsapp_reminders.task_name
        FROM whatsapp_reminders
        LEFT JOIN appointments ON whatsapp_reminders.appointment_id = appointments.appointment_id
        WHERE appointments.appointment_id IS NULL AND whatsapp_reminders.status NOT IN ('cancelado', 'omitido')
        """
    )
    orphan_rows = target_db.cursor.fetchall()
    orphans_cancelled = 0
    for row in orphan_rows:
        row_dict = dict(row)
        appt_id = row_dict["appointment_id"]
        task_name = row_dict.get("task_name")
        if task_name and not task_name.startswith("mock-task-"):
            delete_cloud_task(task_name)
        target_db.update_reminder_status(appt_id, "cancelado")
        orphans_cancelled += 1

    logger.info(
        "[WHATSAPP SYNC] Sincronizacion completada: %s reconciliados, %s nuevos creados, %s huerfanos cancelados",
        reconciled_count,
        created_count,
        orphans_cancelled,
    )
    return {
        "reconciled": reconciled_count,
        "created": created_count,
        "orphans_cancelled": orphans_cancelled,
    }
