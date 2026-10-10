import React, { useState } from "react";

// Component that displays today's appointments schedule.
// Handles time-based visual distinction (active vs past) and item actions.
export default function AgendaToday({
  appointments,
  filterMode,
  setFilterMode,
  customDate,
  setCustomDate,
  onEdit,
  onDelete,
  onNewAppointmentClick,
}) {
  const [deletingId, setDeletingId] = useState(null);

  // Handle appointment cancellation with browser confirmation
  const handleDelete = async (id, clientName) => {
    const confirmMessage = `¿Cancelar la cita de ${clientName || "este cliente"}?`;
    if (window.confirm(confirmMessage)) {
      setDeletingId(id);
      try {
        await onDelete(id);
      } finally {
        setDeletingId(null);
      }
    }
  };

  // Current system time formatted as HH:MM for time comparisons
  const now = new Date();
  const currentHours = String(now.getHours()).padStart(2, "0");
  const currentMinutes = String(now.getMinutes()).padStart(2, "0");
  const currentTimeString = `${currentHours}:${currentMinutes}`;

  return (
    <section className="agenda-section">
      <div className="section-toolbar">
        <div className="filter-group">
          <button
            className={`filter-btn ${filterMode === "today-all" ? "active" : ""}`}
            onClick={() => setFilterMode("today-all")}
          >
            Todas de Hoy
          </button>
          <button
            className={`filter-btn ${filterMode === "today-left" ? "active" : ""}`}
            onClick={() => setFilterMode("today-left")}
          >
            Solo Restantes
          </button>
          <button
            className={`filter-btn ${filterMode === "custom-date" ? "active" : ""}`}
            onClick={() => setFilterMode("custom-date")}
          >
            Por Fecha
          </button>
        </div>

        {filterMode === "custom-date" && (
          <div className="date-picker-inline">
            <label htmlFor="custom-date-input">Fecha:</label>
            <input
              id="custom-date-input"
              type="date"
              value={customDate}
              onChange={(e) => setCustomDate(e.target.value)}
              className="input-field-compact"
            />
          </div>
        )}

        <button className="btn-primary" onClick={onNewAppointmentClick}>
          Nueva Cita
        </button>
      </div>

      {appointments.length === 0 ? (
        <div className="empty-state">
          <h3 className="empty-title">Sin Citas Registradas</h3>
          <p className="empty-desc">
            {filterMode === "today-left"
              ? "No quedan más citas pendientes por atender hoy."
              : "No se han encontrado citas para el filtro seleccionado."}
          </p>
          <button className="btn-ghost" onClick={onNewAppointmentClick}>
            Crear Nueva Cita
          </button>
        </div>
      ) : (
        <div className="appointments-grid">
          {appointments.map((appt) => {
            const isPast =
              filterMode !== "custom-date" &&
              appt.appointment_time < currentTimeString;

            return (
              <div
                key={appt.appointment_id}
                className={`appointment-card ${isPast ? "card-past" : "card-active"}`}
              >
                <div className="card-header">
                  <div className="time-badge">
                    <span>{appt.appointment_time}</span>
                  </div>
                  {isPast ? (
                    <span className="badge badge-past">Completada</span>
                  ) : (
                    <span className="badge badge-active">Pendiente</span>
                  )}
                </div>

                <div className="card-body">
                  <h3 className="client-name">
                    {appt.name
                      ? `${appt.name} ${appt.last_name || ""}`.trim()
                      : "Cliente Sin Nombre"}
                  </h3>

                  <div className="client-contact">
                    <span>{appt.phone}</span>
                  </div>

                  <div className="service-info">
                    <span className="service-pill">
                      {appt.service || "Corte Estándar"}
                    </span>
                  </div>
                </div>

                <div className="card-footer">
                  <button
                    className="btn-action btn-edit"
                    onClick={() => onEdit(appt)}
                  >
                    Editar
                  </button>
                  <button
                    className="btn-action btn-cancel"
                    disabled={deletingId === appt.appointment_id}
                    onClick={() =>
                      handleDelete(appt.appointment_id, appt.name)
                    }
                  >
                    {deletingId === appt.appointment_id
                      ? "Cancelando..."
                      : "Cancelar"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
