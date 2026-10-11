# Barber Shop

> **Full-Stack Appointment Management System & Automated WhatsApp Reminders**
> Built for a real-world local barbershop to eliminate client no-shows, streamline scheduling, and replace paper ledgers with a responsive, offline-tolerant web application.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5+-646CFF?style=flat&logo=vite&logoColor=white)](https://vitejs.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Google Cloud Tasks](https://img.shields.io/badge/Google_Cloud_Tasks-Serverless-4285F4?style=flat&logo=googlecloud&logoColor=white)](https://cloud.google.com/tasks)
[![Meta Cloud API](https://img.shields.io/badge/Meta_WhatsApp-Cloud_API-25D366?style=flat&logo=whatsapp&logoColor=white)](https://developers.facebook.com/docs/whatsapp/cloud-api)
[![Tests](https://img.shields.io/badge/Tests-52%2F52_Passing-brightgreen?style=flat)]()
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 1. Overview & Problem Statement

Independent barbershops often rely on paper appointment books or messaging chats, causing three main business bottlenecks:
1. **Client No-Shows:** Clients forget bookings without automated reminders, causing idle time and lost revenue.
2. **Scheduling Friction:** Inability to quickly inspect remaining day slots, view client booking history, or autocomplete recurring clients.
3. **Machine Dependence:** Standard desktop schedulers only send notifications if the computer stays powered on overnight.

**Barber Shop** solves these challenges with a lightweight, high-performance architecture:
- A responsive **React + Vite** single-page application featuring a dual-pane timeline and calendar.
- A robust **FastAPI + SQLite** REST backend enforcing relational integrity and strict Pydantic schemas.
- A serverless **WhatsApp Automation Engine** powered by **Google Cloud Tasks** and **Meta Cloud API**, delivering reminders exactly 24 hours prior even when the barbershop computer is turned off.
- A built-in **Simulation Mode** that allows 100% full-stack development and testing locally with zero cloud credentials or costs.

---

## 2. Key Features

- **Dual-Pane Timeline & Calendar:** Interactive mini-calendar coupled with an hourly slot ledger. Inspect today's appointments, filter by date, or view upcoming slots at a glance.
- **Search-as-You-Type Client Autocomplete:** Dynamic client search by partial name or phone number, instantly showing visit count and previous services to speed up repeat bookings.
- **24-Hour Automated WhatsApp Reminders:** Calculates exact target send times in `Europe/Madrid` (with automatic Daylight Saving Time adjustment). If an appointment is modified or cancelled, scheduled cloud tasks are automatically revoked.
- **Zero-Dependency Mock/Simulation Mode:** When cloud keys are absent, the system seamlessly operates in safe simulation mode (`status = 'simulado'`), logging mock tasks without throwing errors.
- **Startup Reconciliation Engine (`lifespan`):** On application startup, the server automatically audits the database: schedules future bookings, catches pending items entering the 30-day window, and purges orphaned tasks.
- **Architecture Decision Records (ADRs):** Comprehensive technical rationales recorded in [`decisions.md`](decisions.md), covering database key choices, SQLite concurrency, and REST conventions.

---

## 3. System Architecture

```mermaid
flowchart TD
    subgraph Frontend["React (Vite) Frontend"]
        UI["Dual-Pane Timeline & Calendar"]
        Modal["Booking & Edit Modal"]
        Search["Live Client Autocomplete"]
    end

    subgraph Backend["FastAPI REST API"]
        Router["Endpoints (/appointments, /clients)"]
        Lifespan["Startup Reconciler (lifespan)"]
        RemEngine["Reminders Engine (reminders.py)"]
    end

    subgraph Storage["SQLite Database"]
        DB[(peluqueria.db)]
        T_Clients[clients table]
        T_Appts[appointments table]
        T_Reminders[whatsapp_reminders table]
    end

    subgraph Cloud["External Cloud Services"]
        GCP["Google Cloud Tasks (europe-west1)"]
        Meta["Meta WhatsApp Cloud API"]
        ClientPhone["Client Phone (WhatsApp)"]
    end

    UI -->|HTTP Requests| Router
    Modal -->|POST / PUT / DELETE| Router
    Search -->|GET /clients/search| Router

    Router -->|CRUD Queries| DB
    Router -->|Trigger Reminders| RemEngine
    Lifespan -->|Audit on boot| RemEngine

    RemEngine -.->|If No Keys: Mock Mode| DB
    RemEngine -->|If Keys Set: Schedule Task| GCP
    GCP -->|Trigger at send_at (24h prior)| Meta
    Meta -->|Utility Template Message| ClientPhone
```

---

## 4. Tech Stack

| Domain | Technology | Rationale |
|---|---|---|
| **Frontend** | React 18, Vite, Vanilla CSS | Ultra-fast build times, modular component hierarchy, no bloated UI framework dependencies. |
| **Backend** | Python 3.11+, FastAPI, Pydantic | High-performance asynchronous REST API with automatic OpenAPI documentation and strict data validation. |
| **Database** | SQLite 3 (`check_same_thread=False`) | Single-file embedded zero-maintenance database. Relational foreign key enforcement (`PRAGMA foreign_keys = ON;`). |
| **Cloud Scheduling** | Google Cloud Tasks | Serverless task scheduling supporting HTTP targets up to 30 days in advance. Generous free tier (1,000,000 tasks/month). |
| **Messaging** | Meta WhatsApp Cloud API | Official WhatsApp Business Platform utility template delivery. |
| **Testing** | `unittest`, `FastAPI TestClient`, `zoneinfo` | Comprehensive isolated unit tests and 37 boundary edge case assertions. |

---

## 5. Quickstart & Installation

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Git

### 1. Clone the repository
```bash
git clone https://github.com/your-username/peluqueria-barber shop.git
cd peluqueria-barber shop
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the backend server
python -m uvicorn --app-dir backend/src api.api:app --reload --port 8000
```
Backend API will be running at `http://localhost:8000`. Interactive Swagger UI is available at `http://localhost:8000/docs`.

### 3. Environment Configuration & API Keys (`.env`)
The application looks for environment variables in a `.env` file placed in the **project root directory**. A ready-to-use template is included in [`.env.example`](.env.example):

```bash
# Copy the template to .env (Windows PowerShell)
Copy-Item .env.example .env

# Or in Linux / macOS / Bash:
cp .env.example .env
```

#### Dual-Mode Execution:
- **Local Simulation Mode (Default — No keys needed):**
  If `.env` is empty or omitted, the application runs **100% locally out-of-the-box**. Reminders are computed with Madrid timezone awareness, validated, and recorded as mock tasks (`status = 'simulado'`) with zero network dependencies and $0.00 cost.
- **Production Mode (Live WhatsApp Delivery):**
  To enable automated WhatsApp delivery via Meta and Google Cloud Tasks, populate your credentials inside `.env`:
  ```env
  # Meta WhatsApp Cloud API
  META_ACCESS_TOKEN=your_permanent_system_user_token
  META_PHONE_NUMBER_ID=your_whatsapp_phone_number_id
  META_API_VERSION=v21.0
  META_TEMPLATE_NAME=recordatorio_cita
  META_TEMPLATE_LANG=es

  # Google Cloud Tasks (External Scheduler)
  GCP_PROJECT=your_google_cloud_project_id
  GCP_LOCATION=europe-west1
  GCP_QUEUE=recordatorios-whatsapp
  GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account-key.json
  ```
  > For complete step-by-step instructions on obtaining Meta tokens, setting up the WhatsApp template, and configuring Google Cloud Tasks, see the dedicated [**WhatsApp Credentials & Cloud Setup Guide (`WHATSAPP_SETUP.md`)**](WHATSAPP_SETUP.md).

### 4. Frontend Setup (Development)
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

### 5. Unified Production Launch (Single Process)
Alternatively, you can build the frontend once and run both the API and the React SPA from a single FastAPI server on port 8000:
```bash
# Build React bundle into frontend/dist
cd frontend && npm run build && cd ..

# Launch unified server (or double-click run_app.bat on Windows)
.\run_app.bat
```
Visit `http://localhost:8000` to access the full application.

---

## 6. Testing & Quality Assurance

The codebase includes two dedicated test suites running on isolated, ephemeral SQLite databases:

```bash
# 1. Core integration tests (15 tests)
.\.venv\Scripts\python.exe tests/run_tests.py

# 2. Comprehensive edge cases suite (37 tests)
$env:PYTHONPATH="backend/src"; .\.venv\Scripts\python.exe tests/test_edge_cases.py
```

### Edge Cases Covered (37/37 Passing):
- **Daylight Saving Time (DST):** Spring-forward (March) and fall-back (October) transitions in `Europe/Madrid`.
- **Phone Sanitization:** Robust handling of `+34`, `0034`, leading spaces, dashes, and already-prefixed numbers.
- **Client Name Fallbacks:** Graceful fallback to `"Cliente"` for `None`, empty string, and whitespace-only names. Unicode support for special characters and accents.
- **24-Hour Horizon:** Correct omission (`status = 'omitido'`) for appointments booked with less than 24h notice.
- **30-Day GCP Queue Threshold:** Seamless deferral (`status = 'pendiente'`) for appointments booked further than 30 days ahead.
- **Rescheduling & Cancellation:** Instant task revocation and database status synchronization on booking edits.
- **Startup Reconciliation:** Automated detection of orphan reminders from deleted bookings and missing future tasks.

---

## 7. Documentation Index

- **[`DATABASE_SCHEMA.md`](DATABASE_SCHEMA.md):** Complete database schema reference, entity-relationship diagrams, column constraints, and reminder state machine.
- **[`WHATSAPP_SETUP.md`](WHATSAPP_SETUP.md):** Step-by-step configuration guide for Meta Cloud API and Google Cloud Tasks credentials, including local simulation mode instructions.
- **[`decisions.md`](decisions.md):** Architecture Decision Records (ADRs) documenting rationale for data models, primary key selection, and framework patterns.
- **[`.env.example`](.env.example):** Copy-paste template for production environment variables.

---

## 8. License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for more information.
