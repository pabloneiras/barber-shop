import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useLanguage } from "../context/LanguageContext";
import { api } from "../services/api";

function formatISO(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function getMondayOfDate(d) {
  const date = new Date(d);
  const day = date.getDay();
  const diff = date.getDate() - day + (day === 0 ? -6 : 1);
  return new Date(date.setDate(diff));
}

export default function AgendaWeekly({
  onEdit,
  onBookSlot,
  config = {},
  refreshKey = 0,
}) {
  const { t, language } = useLanguage();

  // Settings from config or defaults
  const daysMode = config.daysMode || "mon-sat"; // 'mon-fri', 'mon-sat', 'mon-sun'
  const startHourStr = config.startHour || "09:30";
  const endHourStr = config.endHour || "20:30";
  const intervalMinutes = parseInt(config.intervalMinutes || 30, 10);

  // Active anchor date (defaults to today)
  const [anchorDate, setAnchorDate] = useState(() => new Date());
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(false);

  const todayStr = useMemo(() => formatISO(new Date()), []);

  // Compute days of current active week
  const weekDays = useMemo(() => {
    const monday = getMondayOfDate(anchorDate);
    let count = 6; // mon-sat
    if (daysMode === "mon-fri") count = 5;
    if (daysMode === "mon-sun") count = 7;

    const days = [];
    for (let i = 0; i < count; i++) {
      const dayDate = new Date(monday);
      dayDate.setDate(monday.getDate() + i);
      const iso = formatISO(dayDate);
      const dayIdx = dayDate.getDay();
      days.push({
        iso,
        dateObj: dayDate,
        dayName: t.weekdayNames[dayIdx],
        dayNum: dayDate.getDate(),
        monthName: t.monthNames[dayDate.getMonth()],
        isToday: iso === todayStr,
      });
    }
    return days;
  }, [anchorDate, daysMode, t, todayStr]);

  // Compute time slots from startHour to endHour
  const timeSlots = useMemo(() => {
    const slots = [];
    const [startH, startM] = startHourStr.split(":").map(Number);
    const [endH, endM] = endHourStr.split(":").map(Number);

    let curMinutes = startH * 60 + startM;
    const endMinutes = endH * 60 + endM;

    while (curMinutes <= endMinutes) {
      const h = String(Math.floor(curMinutes / 60)).padStart(2, "0");
      const m = String(curMinutes % 60).padStart(2, "0");
      slots.push(`${h}:${m}`);
      curMinutes += intervalMinutes;
    }
    return slots;
  }, [startHourStr, endHourStr, intervalMinutes]);

  const startDate = weekDays[0]?.iso;
  const endDate = weekDays[weekDays.length - 1]?.iso;

  // Fetch appointments for the entire active week
  const loadWeekAppointments = useCallback(async () => {
    if (!startDate || !endDate) return;
    setLoading(true);
    try {
      const data = await api.getAppointmentsRange(startDate, endDate);
      setAppointments(data);
    } catch (err) {
      console.error("Failed to load weekly appointments:", err);
      setAppointments([]);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    loadWeekAppointments();
  }, [loadWeekAppointments, refreshKey]);

  // Fast map lookup: date + "_" + time -> array of appointments
  const appointmentSlotsMap = useMemo(() => {
    const map = {};
    appointments.forEach((appt) => {
      const key = `${appt.appointment_date}_${appt.appointment_time}`;
      if (!map[key]) map[key] = [];
      map[key].push(appt);
    });
    return map;
  }, [appointments]);

  // Week navigation
  const prevWeek = () => {
    setAnchorDate((prev) => {
      const d = new Date(prev);
      d.setDate(d.getDate() - 7);
      return d;
    });
  };

  const nextWeek = () => {
    setAnchorDate((prev) => {
      const d = new Date(prev);
      d.setDate(d.getDate() + 7);
      return d;
    });
  };

  const goToToday = () => {
    setAnchorDate(new Date());
  };

  const headerTitle = useMemo(() => {
    if (!weekDays.length) return "";
    const first = weekDays[0];
    const last = weekDays[weekDays.length - 1];
    return `${first.dayNum} ${first.monthName} - ${last.dayNum} ${last.monthName} ${last.dateObj.getFullYear()}`;
  }, [weekDays]);

  return (
    <section className="agenda-weekly-container">
      {/* Top weekly controls */}
      <div className="weekly-header-bar">
        <div className="weekly-nav-group">
          <button
            type="button"
            className="btn-weekly-nav"
            onClick={prevWeek}
            title={t.prevWeek}
          >
            ←
          </button>
          <button
            type="button"
            className="btn-weekly-today"
            onClick={goToToday}
          >
            {t.thisWeek}
          </button>
          <button
            type="button"
            className="btn-weekly-nav"
            onClick={nextWeek}
            title={t.nextWeek}
          >
            →
          </button>
        </div>

        <h2 className="weekly-range-title">{headerTitle}</h2>

        <div className="weekly-count-badge">
          {appointments.length} {t.count.toLowerCase()}
        </div>
      </div>

      {/* Weekly Matrix Grid */}
      <div className="weekly-grid-wrapper">
        <table className="weekly-matrix-table">
          <thead>
            <tr>
              <th className="th-hour-col">
                <span className="th-hour-label">{t.labelTime}</span>
              </th>
              {weekDays.map((day) => (
                <th
                  key={day.iso}
                  className={`th-day-col ${day.isToday ? "today-column-header" : ""}`}
                >
                  <div className="th-day-wrapper">
                    <span className="th-day-name">{day.dayName}</span>
                    <span className="th-day-number">{day.dayNum}</span>
                    {day.isToday && (
                      <span className="today-pill-badge">{t.todayBadge}</span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {timeSlots.map((time) => (
              <tr key={time} className="matrix-time-row">
                <td className="matrix-time-cell">
                  <span className="time-row-label">{time}</span>
                </td>
                {weekDays.map((day) => {
                  const key = `${day.iso}_${time}`;
                  const slotAppts = appointmentSlotsMap[key] || [];

                  return (
                    <td
                      key={key}
                      className={`matrix-slot-cell ${
                        day.isToday ? "today-cell-highlight" : ""
                      }`}
                    >
                      {slotAppts.length > 0 ? (
                        slotAppts.map((appt) => {
                          const apptColor = appt.color || "#3b82f6";
                          return (
                            <div
                              key={appt.appointment_id}
                              className="matrix-appt-card"
                              style={{
                                borderLeftColor: apptColor,
                                background: `color-mix(in srgb, ${apptColor} 12%, var(--card-bg, #1a2234))`,
                              }}
                              onClick={() => onEdit(appt)}
                              title={`${appt.name || t.unnamedClient} - ${appt.service || ""}`}
                            >
                              <div className="matrix-appt-top">
                                <span
                                  className="matrix-color-indicator"
                                  style={{ backgroundColor: apptColor }}
                                ></span>
                                <span className="matrix-client-name">
                                  {appt.name || t.unnamedClient}
                                </span>
                              </div>

                              <div className="matrix-appt-bottom">
                                <span className="matrix-service-tag">
                                  {appt.service || t.defaultService}
                                </span>
                                {appt.price > 0 && (
                                  <span className="matrix-price-badge">
                                    {appt.price}€
                                  </span>
                                )}
                              </div>
                            </div>
                          );
                        })
                      ) : (
                        <button
                          type="button"
                          className="btn-matrix-empty-slot"
                          onClick={() => onBookSlot(day.iso, time)}
                          title={`${day.dayName} ${time}`}
                        >
                          +
                        </button>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
