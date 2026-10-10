import React, { useState } from "react";

const MONTH_NAMES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
];

// Interactive calendar sidebar for date selection and monthly navigation.
export default function CalendarSidebar({
  selectedDate,
  setSelectedDate,
  appointmentsCount,
}) {
  const [currentDate, setCurrentDate] = useState(new Date());

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const changeMonth = (offset) => {
    setCurrentDate(new Date(year, month + offset, 1));
  };

  const firstDayIndex = new Date(year, month, 1).getDay();
  const adjustedFirstDay = (firstDayIndex + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const days = [];
  for (let i = 0; i < adjustedFirstDay; i++) {
    days.push(null);
  }
  for (let d = 1; d <= daysInMonth; d++) {
    days.push(d);
  }

  const todayISO = new Date().toISOString().split("T")[0];

  return (
    <aside className="sidebar-pane">
      <div className="calendar-card">
        <div className="calendar-nav-bar">
          <button
            className="calendar-arrow-btn"
            onClick={() => changeMonth(-1)}
            title="Mes anterior"
          >
            ←
          </button>
          <span className="calendar-month-label">
            {MONTH_NAMES[month]} {year}
          </span>
          <button
            className="calendar-arrow-btn"
            onClick={() => changeMonth(1)}
            title="Mes siguiente"
          >
            →
          </button>
        </div>

        <div className="calendar-weekdays">
          <div className="weekday-header">Lun</div>
          <div className="weekday-header">Mar</div>
          <div className="weekday-header">Mié</div>
          <div className="weekday-header">Jue</div>
          <div className="weekday-header">Vie</div>
          <div className="weekday-header">Sáb</div>
          <div className="weekday-header">Dom</div>
        </div>

        <div className="calendar-days-grid">
          {days.map((dayNum, idx) => {
            if (dayNum === null) {
              return (
                <div
                  key={`empty-${idx}`}
                  className="calendar-day-cell day-empty"
                ></div>
              );
            }

            const monthStr = String(month + 1).padStart(2, "0");
            const dayStr = String(dayNum).padStart(2, "0");
            const dateStr = `${year}-${monthStr}-${dayStr}`;

            const isSelected = dateStr === selectedDate;
            const isToday = dateStr === todayISO;

            return (
              <button
                key={dateStr}
                type="button"
                className={`calendar-day-cell ${isSelected ? "day-selected" : ""} ${isToday ? "day-today" : ""}`}
                onClick={() => setSelectedDate(dateStr)}
              >
                <span>{dayNum}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="sidebar-info-card">
        <div className="sidebar-info-title">Resumen de Agenda</div>
        <div className="sidebar-info-stat">
          <span className="stat-num">{appointmentsCount}</span>
          <span className="stat-label">Citas en el día</span>
        </div>
        <p className="sidebar-info-desc">
          Selecciona cualquier fecha en el calendario para consultar o gestionar las citas.
        </p>
      </div>
    </aside>
  );
}
