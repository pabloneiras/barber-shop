import React from "react";
import { useLanguage } from "../context/LanguageContext";

const STANDARD_SLOTS = [
  "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
  "12:00", "12:30", "13:00", "13:30",
  "16:00", "16:30", "17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00"
];

// Formats a YYYY-MM-DD date string using localized header formatting
function formatDateHeader(isoDateString, t) {
  const [sYear, sMonth, sDay] = isoDateString.split("-").map(Number);
  const selectedDateObj = new Date(sYear, sMonth - 1, sDay);
  const dayName = t.weekdayNames[selectedDateObj.getDay()];
  const monthName = t.monthNames[selectedDateObj.getMonth()];
  return t.dateHeaderFormat(dayName, sDay, monthName, sYear);
}

// Indexes an appointment array into an object keyed by appointment_time for O(1) slot lookup
function buildAppointmentsTimeIndex(appointmentsList) {
  const map = {};
  appointmentsList.forEach((appointment) => {
    map[appointment.appointment_time] = appointment;
  });
  return map;
}

// Combines standard shop working hours with any custom appointment times into a sorted, unique time array
function mergeStandardWithBookedTimeSlots(appointmentsByTimeMap) {
  return Array.from(
    new Set([...STANDARD_SLOTS, ...Object.keys(appointmentsByTimeMap)])
  ).sort();
}

// Vertical day timeline ledger displaying scheduled appointment slots and available times.
export default function AgendaToday({
  appointments,
  selectedDate,
  onEdit,
  onDelete,
  onBookSlot,
}) {
  const { t } = useLanguage();
  const formattedDayTitle = formatDateHeader(selectedDate, t);
  const appointmentsByTimeMap = buildAppointmentsTimeIndex(appointments);
  const allChronologicalSlots = mergeStandardWithBookedTimeSlots(appointmentsByTimeMap);
  const totalAppointmentsCount = appointments.length;

  return (
    <section className="timeline-pane">
      <div className="timeline-header">
        <div>
          <h2 className="timeline-date-title">{formattedDayTitle}</h2>
          <div className="timeline-day-stats">
            {totalAppointmentsCount === 0
              ? t.noAppointments
              : totalAppointmentsCount === 1
              ? t.oneAppointment
              : `${totalAppointmentsCount} ${t.appointmentsRegistered}`}
          </div>
        </div>
        <button
          type="button"
          className="btn-ghost"
          onClick={() => onBookSlot("10:00")}
        >
          {t.bookForDay}
        </button>
      </div>

      <div className="slots-container">
        {allChronologicalSlots.map((timeSlot) => {
          const appointmentAtSlot = appointmentsByTimeMap[timeSlot];

          if (appointmentAtSlot) {
            const clientFullName = (
              appointmentAtSlot.name
                ? `${appointmentAtSlot.name} ${appointmentAtSlot.last_name || ""}`
                : t.unnamedClient
            ).trim();

            return (
              <div
                key={appointmentAtSlot.appointment_id || timeSlot}
                className="slot-row"
              >
                <div className="slot-time-col">{timeSlot}</div>
                <div className="slot-booked">
                  <div className="booked-main">
                    <div className="booked-client">{clientFullName}</div>
                    <div className="booked-meta">
                      <a
                        href={`tel:${appointmentAtSlot.phone}`}
                        className="booked-phone"
                      >
                        {appointmentAtSlot.phone}
                      </a>
                      {appointmentAtSlot.service && (
                        <span className="booked-service">
                          {appointmentAtSlot.service}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="booked-actions">
                    <button
                      type="button"
                      className="btn-slot-edit"
                      onClick={() => onEdit(appointmentAtSlot)}
                      title={t.edit}
                    >
                      {t.edit}
                    </button>
                    <button
                      type="button"
                      className="btn-slot-cancel"
                      onClick={() =>
                        onDelete(appointmentAtSlot.appointment_id, clientFullName)
                      }
                      title={t.cancel}
                    >
                      {t.cancel}
                    </button>
                  </div>
                </div>
              </div>
            );
          }

          return (
            <div key={timeSlot} className="slot-row">
              <div className="slot-time-col">{timeSlot}</div>
              <button
                type="button"
                className="slot-empty"
                onClick={() => onBookSlot(timeSlot)}
              >
                <span>{t.availableSlot}</span>
                <span className="btn-book-slot">{t.bookSlot}</span>
              </button>
            </div>
          );
        })}
      </div>
    </section>
  );
}
