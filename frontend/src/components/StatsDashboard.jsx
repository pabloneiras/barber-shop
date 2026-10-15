import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useLanguage } from "../context/LanguageContext";
import { api } from "../services/api";

function formatISO(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export default function StatsDashboard() {
  const { t } = useLanguage();

  const [periodType, setPeriodType] = useState("month"); // 'week', 'month', 'year'
  const [selectedDate, setSelectedDate] = useState(() => new Date());
  const [stats, setStats] = useState({
    total_appointments: 0,
    total_revenue: 0,
    average_ticket: 0,
    services: [],
  });
  const [loading, setLoading] = useState(false);

  // Compute date range based on periodType and selectedDate
  const { startDate, endDate, periodLabel } = useMemo(() => {
    const d = new Date(selectedDate);
    const y = d.getFullYear();
    const m = d.getMonth();

    if (periodType === "week") {
      const day = d.getDay();
      const diff = d.getDate() - day + (day === 0 ? -6 : 1);
      const monday = new Date(d.setDate(diff));
      const sunday = new Date(monday);
      sunday.setDate(monday.getDate() + 6);

      const start = formatISO(monday);
      const end = formatISO(sunday);
      const label = `${monday.getDate()} ${t.monthNames[monday.getMonth()]} - ${sunday.getDate()} ${t.monthNames[sunday.getMonth()]} ${sunday.getFullYear()}`;
      return { startDate: start, endDate: end, periodLabel: label };
    }

    if (periodType === "year") {
      const start = `${y}-01-01`;
      const end = `${y}-12-31`;
      return { startDate: start, endDate: end, periodLabel: `${y}` };
    }

    // Default: 'month'
    const lastDay = new Date(y, m + 1, 0).getDate();
    const start = `${y}-${String(m + 1).padStart(2, "0")}-01`;
    const end = `${y}-${String(m + 1).padStart(2, "0")}-${String(lastDay).padStart(2, "0")}`;
    const label = `${t.monthNames[m]} ${y}`;
    return { startDate: start, endDate: end, periodLabel: label };
  }, [periodType, selectedDate, t]);

  const loadStats = useCallback(async () => {
    if (!startDate || !endDate) return;
    setLoading(true);
    try {
      const data = await api.getStats(startDate, endDate);
      setStats(data);
    } catch (err) {
      console.error("Failed to load statistics:", err);
      setStats({
        total_appointments: 0,
        total_revenue: 0,
        average_ticket: 0,
        services: [],
      });
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  // Navigation handlers
  const handlePrev = () => {
    setSelectedDate((prev) => {
      const d = new Date(prev);
      if (periodType === "week") d.setDate(d.getDate() - 7);
      else if (periodType === "month") d.setMonth(d.getMonth() - 1);
      else if (periodType === "year") d.setFullYear(d.getFullYear() - 1);
      return d;
    });
  };

  const handleNext = () => {
    setSelectedDate((prev) => {
      const d = new Date(prev);
      if (periodType === "week") d.setDate(d.getDate() + 7);
      else if (periodType === "month") d.setMonth(d.getMonth() + 1);
      else if (periodType === "year") d.setFullYear(d.getFullYear() + 1);
      return d;
    });
  };

  const handleCurrent = () => {
    setSelectedDate(new Date());
  };

  return (
    <section className="stats-dashboard-container">
      {/* Top Filter and Controls */}
      <div className="stats-header-bar">
        <div>
          <h2 className="stats-main-title">{t.statsTitle}</h2>
          <p className="stats-period-subtitle">{periodLabel}</p>
        </div>

        <div className="stats-controls-right">
          {/* Period selector pill tabs */}
          <div className="stats-period-tabs">
            <button
              type="button"
              className={`btn-period-tab ${periodType === "week" ? "active" : ""}`}
              onClick={() => setPeriodType("week")}
            >
              {t.periodWeek}
            </button>
            <button
              type="button"
              className={`btn-period-tab ${periodType === "month" ? "active" : ""}`}
              onClick={() => setPeriodType("month")}
            >
              {t.periodMonth}
            </button>
            <button
              type="button"
              className={`btn-period-tab ${periodType === "year" ? "active" : ""}`}
              onClick={() => setPeriodType("year")}
            >
              {t.periodYear}
            </button>
          </div>

          {/* Stepper buttons */}
          <div className="stats-nav-stepper">
            <button
              type="button"
              className="btn-weekly-nav"
              onClick={handlePrev}
            >
              ←
            </button>
            <button
              type="button"
              className="btn-weekly-today"
              onClick={handleCurrent}
            >
              {t.thisWeek}
            </button>
            <button
              type="button"
              className="btn-weekly-nav"
              onClick={handleNext}
            >
              →
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="stats-kpi-grid">
        <div className="stats-kpi-card highlight-revenue">
          <span className="kpi-label">{t.totalRevenue}</span>
          <span className="kpi-value">{stats.total_revenue.toFixed(2)} €</span>
          <span className="kpi-desc">{periodLabel}</span>
        </div>

        <div className="stats-kpi-card">
          <span className="kpi-label">{t.totalAppointments}</span>
          <span className="kpi-value">{stats.total_appointments}</span>
          <span className="kpi-desc">{t.appointmentsRegistered}</span>
        </div>

        <div className="stats-kpi-card">
          <span className="kpi-label">{t.averageTicket}</span>
          <span className="kpi-value">{stats.average_ticket.toFixed(2)} €</span>
          <span className="kpi-desc">Por cliente</span>
        </div>
      </div>

      {/* Breakdown by Service */}
      <div className="stats-breakdown-panel">
        <h3 className="breakdown-title">{t.serviceBreakdown}</h3>

        {stats.services.length === 0 ? (
          <div className="stats-empty-state">
            <p>{t.noDataPeriod}</p>
          </div>
        ) : (
          <div className="breakdown-list">
            {stats.services.map((svc) => {
              const pct = stats.total_appointments > 0
                ? Math.round((svc.count / stats.total_appointments) * 100)
                : 0;

              return (
                <div key={svc.service_name} className="breakdown-item-card">
                  <div className="breakdown-item-header">
                    <div className="breakdown-name-group">
                      <span
                        className="service-color-dot"
                        style={{ backgroundColor: svc.color || "#3b82f6" }}
                      ></span>
                      <span className="breakdown-service-name">
                        {svc.service_name}
                      </span>
                    </div>

                    <div className="breakdown-figures">
                      <span className="breakdown-count-badge">
                        {svc.count} {t.count.toLowerCase()} ({pct}%)
                      </span>
                      <span className="breakdown-revenue-badge">
                        {svc.revenue.toFixed(2)} €
                      </span>
                    </div>
                  </div>

                  <div className="breakdown-progress-track">
                    <div
                      className="breakdown-progress-bar"
                      style={{
                        width: `${pct}%`,
                        backgroundColor: svc.color || "#3b82f6",
                      }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
