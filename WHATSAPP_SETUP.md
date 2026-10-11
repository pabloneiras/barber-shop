# WhatsApp Automated Reminders — Setup & Credentials Guide

This guide explains how automated 24-hour WhatsApp appointment reminders work in **Barber Shop**, where to configure your API keys and credentials, and how to operate the system in both **local simulation mode** (zero keys required) and **live cloud production mode**.

---

## 1. Quick Summary: Dual-Mode Architecture

The reminder subsystem in [`backend/src/app/reminders.py`](backend/src/app/reminders.py) is built to be resilient and zero-friction:

| Mode | Credentials Needed? | What happens when a booking is created? | Cost |
|---|---|---|---|
| **Simulation Mode** (Default) | **None** | Calculates target 24h `send_at` time in `Europe/Madrid`, validates payload, logs `[WHATSAPP MOCK]`, and registers `status = 'simulado'`. | **$0.00** |
| **Live Cloud Mode** | **Meta & GCP** | Enqueues a scheduled HTTP task into Google Cloud Tasks pointing directly to Meta's Cloud API at `send_at`. When the time arrives, Meta delivers the WhatsApp message. | ~€0.0166 per delivered message |

> **Key Advantage:** You do **not** need any API keys or credit cards to develop, test, or demonstrate the application locally. It works 100% out of the box.

---

## 2. Where to Put Your Credentials

All secret keys and cloud configuration belong in a **`.env`** file placed directly in the **project root folder**:

```text
barber-shop/
├── .env                  <-- CREATE THIS FILE HERE
├── .env.example          <-- Reference template
├── .gitignore            <-- Configured to NEVER commit .env or *.json keys
├── Database/
├── backend/
├── frontend/
└── tests/
```

### Security Warning: Git Protection
The project's [`.gitignore`](.gitignore) file is pre-configured with:
```gitignore
.env
*.env
service-account*.json
gcp-key*.json
```
**Never** commit your `.env` file or your service account JSON keys to GitHub.

---

## 3. Environment Variables Reference

Create a file named `.env` in the root folder with the following variables (you can copy `.env.example`):

```env
# -----------------------------------------------------------------------------
# META WHATSAPP CLOUD API CONFIGURATION
# -----------------------------------------------------------------------------
# Permanent Access Token generated for a System User in Meta Business Suite
META_ACCESS_TOKEN=EAAG...your_permanent_system_user_token_here...

# WhatsApp Business Phone Number ID (NOT your personal phone number)
META_PHONE_NUMBER_ID=123456789012345

# Meta Graph API version
META_API_VERSION=v21.0

# Name of the approved WhatsApp template
META_TEMPLATE_NAME=recordatorio_cita

# Language code of the approved template
META_TEMPLATE_LANG=es

# -----------------------------------------------------------------------------
# GOOGLE CLOUD TASKS CONFIGURATION
# -----------------------------------------------------------------------------
# Google Cloud Project ID
GCP_PROJECT=barber-shop-prod

# Region where your Cloud Tasks queue is created
GCP_LOCATION=europe-west1

# Name of the Cloud Tasks queue
GCP_QUEUE=recordatorios-whatsapp

# Absolute path to your Google Service Account JSON key
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account-key.json
```

---

## 4. Step-by-Step: How to Obtain the Credentials

### Step 4.1. Meta WhatsApp Cloud API Setup

1. **Create a Meta Developer Account:**
   - Go to [developers.facebook.com](https://developers.facebook.com/) and register or log in.
2. **Create an App:**
   - Click **My Apps** > **Create App**.
   - Select **Business** as the app type.
   - Give it an app name (e.g., `Barber Shop Reminders`) and select your Business Portfolio.
3. **Add the WhatsApp Product:**
   - In the App Dashboard, click **Set Up** on the **WhatsApp** card.
4. **Locate your Phone Number ID:**
   - Navigate to **WhatsApp** > **API Setup**.
   - Under *Step 1: Select phone numbers*, copy the **Phone number ID** into `META_PHONE_NUMBER_ID`.
5. **Create & Submit the Message Template:**
   - Go to **WhatsApp** > **Message Templates** (or in Meta Business Manager: *WhatsApp Manager* > *Message Templates*).
   - Click **Create Template**:
     - **Category:** `Utility`
     - **Name:** `recordatorio_cita`
     - **Language:** `Spanish` (`es`)
     - **Body Text:**
       ```text
       Hola {{1}}, te recordamos tu cita en Barber Shop el {{2}} a las {{3}}. Si no puedes asistir o deseas modificarla, por favor avísanos.
       ```
     - **Samples:** Provide sample values (e.g. `1` = `Carlos`, `2` = `15/10`, `3` = `12:00`).
   - Submit for review (Meta typically approves Utility templates automatically within minutes).
6. **Generate a Permanent Access Token:**
   - *Temporary tokens from the API setup tab expire in 24 hours.*
   - Go to [business.facebook.com/settings](https://business.facebook.com/settings/) > **Users** > **System Users**.
   - Create a System User with the `Admin` role.
   - Under **Assigned Assets**, assign your App and WhatsApp Account with **Full Control**.
   - Click **Generate Token**:
     - Check permissions: `whatsapp_business_messaging` and `whatsapp_business_management`.
   - Copy this token into `META_ACCESS_TOKEN` in your `.env`.

---

### Step 4.2. Google Cloud Tasks Setup

Google Cloud Tasks acts as the external scheduling engine. It holds the reminder until the exact UTC send time, then sends an HTTP POST request to Meta even if the barber's computer is turned off.

1. **Create a Google Cloud Project:**
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project (e.g., `barber-shop`).
   - Link a billing account (Cloud Tasks includes **1,000,000 free operations per month**; usage for a local barbershop is 100% free).
2. **Enable the Cloud Tasks API:**
   - Run in your terminal (with Google Cloud SDK installed):
     ```bash
     gcloud services enable cloudtasks.googleapis.com --project=YOUR_PROJECT_ID
     ```
3. **Create the Tasks Queue:**
   - Run:
     ```bash
     gcloud tasks queues create recordatorios-whatsapp \
         --location=europe-west1 \
         --max-attempts=3 \
         --project=YOUR_PROJECT_ID
     ```
     *(Setting `--max-attempts=3` prevents endless retries and duplicate messages if Meta encounters an issue).*
4. **Create a Service Account & Download the JSON Key:**
   - In Cloud Console, go to **IAM & Admin** > **Service Accounts**.
   - Click **Create Service Account** (e.g., `reminders-worker`).
   - Grant the following roles:
     - `Cloud Tasks Enqueuer` (allows scheduling tasks).
     - `Cloud Tasks Task Deleter` or `Cloud Tasks Admin` (allows cancelling tasks when an appointment is deleted/updated).
   - Click **Done**, then click the created service account > **Keys** > **Add Key** > **Create new key** > **JSON**.
   - Save the downloaded JSON file in your project directory (e.g. `service-account-key.json`).
   - Set `GOOGLE_APPLICATION_CREDENTIALS` in your `.env` to the absolute path of this file.

---

## 5. How Simulation Mode Works (Zero Keys)

If any of the environment variables above are missing or empty:
1. The backend automatically switches to **Simulation Mode**.
2. When creating a booking:
   - Calculates the target send time 24 hours in advance in Madrid local time.
   - Normalizes the phone number (e.g., `666111222` -> `34666111222`).
   - Generates a mock task identifier: `mock-task-<appointment_id>-<timestamp>`.
   - Records the state in SQLite: `status = 'simulado'`.
   - Logs the simulated event to the console:
     ```text
     INFO:reminders:[WHATSAPP MOCK] Programado recordatorio para cita #10 (Carlos a las 17:00) -> Envio: 2026-10-19T15:00:00+00:00 | Tarea: mock-task-10-1791676079
     ```
3. If an appointment is modified via `PUT /appointments/{id}`, the simulation cancels the previous mock task and reschedules a new one.
4. If an appointment is cancelled via `DELETE /appointments/{id}`, the simulation marks it as `status = 'cancelado'`.

---

## 6. How to Verify & Test

### Run Automated Tests
Execute the test suites from the repository root:
```bash
# Unit & integration tests
.\.venv\Scripts\python.exe tests/run_tests.py

# Complete 37/37 edge case suite
.\.venv\Scripts\python.exe tests/test_edge_cases.py
```

### Check an Appointment's Reminder Status via API
Once the server is running (`python -m uvicorn --app-dir backend/src api.api:app --reload`), inspect any reminder via HTTP:
```http
GET http://127.0.0.1:8000/appointments/{appointment_id}/reminder
```

**Example JSON Response:**
```json
{
  "appointment_id": 10,
  "task_name": "mock-task-10-1791676079",
  "send_at": "2026-10-19T15:00:00+00:00",
  "status": "simulado"
}
```
