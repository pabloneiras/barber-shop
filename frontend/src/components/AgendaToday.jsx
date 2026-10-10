import React from "react";

const STANDARD_SLOTS = [
  "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
  "12:00", "12:30", "13:00", "13:30",
  "16:00", "16:30", "17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00"
];

const MONTH_NAMES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
];

const WEEKDAY_NAMES = [
  "Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"
];

// Vertical day timeline ledger displaying scheduled appointment slots and available times.
export default function AgendaToday({
  appointments,
  selectedDate,
  onEdit,
  onDelete,
  onBookSlot,
}) {
  // Format selected date header in Spanish
  const [sYear, sMonth, sDay] = selectedDate.split("-").map(Number);
  const selectedDateObj = new Date(sYear, sMonth - 1, sDay);
  const dayName = WEEKDAY_NAMES[selectedDateObj.getDay()];
  const monthName = MONTH_NAMES[selectedDateObj.getMonth()];
  const formattedDayTitle = `${dayName}, ${sDay} de ${monthName} de ${sYear}`;

  // Map appointments by start time
  const apptMap = {};
  appointments.forEach((a) => {
    apptMap[a.appointment_time] = a;
  });

  // Combine standard work slots and existing appointments
  const allSlots = Array.from(
    new Set([...STANDARD_SLOTS, ...Object.keys(apptMap)])
  ).sort();

  const totalAppointments = appointments.length;

  return (
    <section className="timeline-pane">
      <div className="timeline-header">
        <div>
          <h2 className="timeline-date-title">{formattedDayTitle}</h2>
          <div className="timeline-day-stats">
            {totalAppointments === 0
              ? "SIN CITAS REGISTRADAS"
              : `${totalAppointments} ${totalAppointments === 1 ? "CITA REGISTRADA" : "CITAS REGISTRADAS"}`}
          </div>
        </div>
        <button className="btn-ghost" onClick={() => onBookSlot("10:00")}>
          + Agendar en este día
        </button>
      </div>

      <div className="slots-container">
        {allSlots.map((time) => {
          const appt = apptMap[time];

          if (appt) {
            const clientFullName = (
              appt.name
                ? `${appt.name} ${appt.last_name || ""}`
                : "Cliente sin nombre"
            ).trim();

            return (
              <div key={appt.appointment_id || time} className="slot-row">
                <div className="slot-time-col">{time}</div>
                <div className="slot-booked">
                  <div className="booked-main">
                    <div className="booked-client">{clientFullName}</div>
                    <div className="booked-meta">
                      <a href={`tel:${appt.phone}`} className="booked-phone">
                        {appt.phone}
                      </a>
                      {appt.service && (
                        <span className="booked-service">{appt.service}</span>
                      )}
                    </div>
                  </div>

                  <div className="booked-actions">
                    <button
                      type="button"
                      className="btn-slot-edit"
                      onClick={() => onEdit(appt)}
                      title="Editar cita"
                    >
                      Editar
                    </button>
                    <button
                      type="button"
                      className="btn-slot-cancel"
                      onClick={() => onDelete(appt.appointment_id, clientFullName)}
                      title="Cancelar cita"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              </div>
            );
          }

          return (
            <div key={time} className="slot-row">
              <div className="slot-time-col">{time}</div>
              <button
                className="slot-empty"
                onClick={() => onBookSlot(time)}
              >
                <span>Hueco Disponible</span>
                <span className="btn-book-slot">+ Reservar</span>
              </button>
            </div>
          );
        })}
      </div>
    </section>
  );
}
