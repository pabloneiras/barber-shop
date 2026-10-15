[🇪🇸 Versión en Español](README_es.md) | [🇬🇧 English Version](README.md)

# Barber Shop

> **Sistema Completo de Gestión de Citas, Matriz Semanal, Métricas y Recordatorios Automatizados por WhatsApp**
> Desarrollado para una barbería real con el objetivo de eliminar las inasistencias de clientes (*no-shows*), agilizar la planificación semanal y sustituir los libros de papel por una aplicación web moderna, responsiva y lista para usar.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-71%2F71_Superados-brightgreen?style=flat)]()
[![Licencia](https://img.shields.io/badge/Licencia-MIT-blue.svg)](LICENSE)

---

## 1. Guía Rápida: Cómo Arrancar la Aplicación (Para quien no sepa programar)

No necesitas conocimientos técnicos ni instalar Node.js. El diseño visual ya viene compilado y listo en la aplicación. Solo necesitas tener **Python** instalado en tu ordenador.

### En Windows (1 solo clic)
1. Descarga o descomprime la carpeta del proyecto.
2. Haz **doble clic en el archivo `run_app.bat`**.
3. El programa detectará todo automáticamente, configurará el entorno por primera vez y **abrirá tu navegador en `http://localhost:8000`**.

### En Linux o macOS
1. Abre una terminal dentro de la carpeta del proyecto.
2. Ejecuta el script lanzador:
   ```bash
   bash run_app.sh
   ```
   *(o dale permisos con `chmod +x run_app.sh` y haz `./run_app.sh`)*.
3. El navegador se abrirá automáticamente con la aplicación lista.

---

## 2. Cómo Funciona la Aplicación

La aplicación cuenta con 3 vistas principales accesibles desde la barra superior:

### A. Vista Semanal (Matriz de Trabajo)
- **Cuadrícula Semanal**: Muestra los días de la semana en columnas y las horas en filas (de 09:30 a 20:30 o según tu horario configurado).
- **Siempre sabes en qué día estás**: La columna del día actual aparece resaltada en azul intenso con el distintivo **HOY**.
- **Cabecera Fija (Sticky)**: Al bajar con la rueda del ratón para revisar las horas de la tarde, los nombres de los días y la fecha permanecen siempre fijos en la parte superior de la pantalla.
- **Citas con Colores**: Distingue visualmente citas normales de citas especiales/VIP (paleta rápida de azul, dorado, verde, púrpura, rosa o cualquier color con el selector libre).
- **Agendar en 1 clic**: Haz clic en cualquier hueco libre (`+`) para reservar esa hora, o pulsa sobre una cita existente para editarla.

### B. Vista Diaria (Agenda Clásica)
- Visualización detallada de un solo día con listado cronológico de turnos y mini-calendario mensual lateral para navegar entre fechas.

### C. Estadísticas y Facturación
- Consulta los ingresos totales acumulados (€), el número de citas y el ticket medio por cliente.
- Filtra por **Semana**, **Mes** o **Año completo**.
- **Desglose por servicio**: Conoce cuántos cortes de cada tipo se han realizado (caballero, barba, corte y barba, tinte...) y cuántos euros ha generado cada uno.

### D. Ajustes (Precios y Horarios)
- Botón **"Ajustes"** en la cabecera:
  - **Servicios y Precios**: Cambia el precio de cada corte o añade nuevos servicios con su color asignado.
  - **Horario Semanal**: Ajusta los días que abres (Lunes a Viernes, Lunes a Sábado o toda la semana), tu hora de apertura, cierre y si quieres tramos de 30 o 60 minutos.

---

## 3. Recordatorios Automatizados por WhatsApp

La aplicación incluye un motor inteligente de avisos 24 horas antes de cada cita:
- **Modo Simulación (Por defecto, 100% gratuito y sin configurar nada):**
  Calcula con precisión de zona horaria cuándo debe enviarse el recordatorio y lo registra en la base de datos (`status = 'simulado'`). Puedes probar la app al completo sin gastar ni un céntimo.
- **Modo Real (Envíos a clientes):**
  Si configuras tus credenciales en el archivo `.env` (Meta WhatsApp Cloud API y Google Cloud Tasks), los mensajes se entregarán automáticamente al WhatsApp del cliente 24 horas antes, **incluso si el ordenador de la barbería está apagado**. Consulta la guía detallada en [`WHATSAPP_SETUP.md`](WHATSAPP_SETUP.md).

---

## 4. Estructura del Proyecto

```text
barber-shop/
├── run_app.bat               # Lanzador automático con 1 clic para Windows
├── run_app.sh                # Lanzador automático para Linux y macOS
├── requirements.txt          # Dependencias exactas de Python fijadas
├── backend/
│   └── src/
│       ├── api/
│       │   └── api.py        # Endpoints REST (FastAPI) y servidor del frontend
│       └── app/
│           ├── database.py           # Conexión principal SQLite
│           ├── database_manager.py   # Consultas, servicios, precios y citas
│           ├── reminders.py          # Automatización de WhatsApp
│           └── utils.py              # Normalización de teléfonos (+34)
├── frontend/
│   ├── dist/                 # Frontend compilado listo para producción (sin npm requerido)
│   └── src/
│       ├── components/
│       │   ├── AgendaWeekly.jsx      # Matriz semanal con cabecera fija
│       │   ├── AgendaToday.jsx       # Agenda diaria
│       │   ├── StatsDashboard.jsx    # Panel de métricas y facturación
│       │   ├── SettingsModal.jsx     # Configuración de precios y horarios
│       │   └── BookingModal.jsx      # Modal de reserva con autocompletado y colores
│       ├── App.jsx                   # Enrutamiento de vistas y estado
│       └── translations.js           # Traducciones (Español / Inglés)
├── Database/
│   ├── .gitkeep              # Mantiene la carpeta en Git
│   └── barber_shop.db        # Base de datos SQLite local (en .gitignore)
└── tests/
    ├── run_tests.py                  # Pruebas de base de datos (15 tests)
    ├── test_edge_cases.py            # Pruebas de límites y WhatsApp (37 tests)
    └── test_services_and_stats.py    # Pruebas de precios y estadísticas (19 tests)
```

---

## 5. Pruebas Automatizadas y Calidad

El proyecto incluye 3 suites de pruebas que corren sobre bases de datos temporales aisladas:

```bash
# 1. Pruebas de lógica y base de datos (15 tests)
python tests/run_tests.py

# 2. Pruebas de casos límite, prefijos y WhatsApp (37 tests)
python tests/test_edge_cases.py

# 3. Pruebas de servicios, precios y estadísticas (19 tests)
python tests/test_services_and_stats.py
```
**Resultado actual: 71/71 tests superados (100% éxito)**.

---

## 6. Licencia

Distribuido bajo la Licencia MIT. Consulta [`LICENSE`](LICENSE) para más información.
