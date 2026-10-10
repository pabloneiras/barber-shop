import React from "react";
import logoImg from "../assets/logo.jpg";

// Top navigation bar component.
// Integrates physical brand seal, date indicator, server status, and tab navigation.
export default function Header({ currentTab, setCurrentTab, onRefresh }) {
  // Format current date in Spanish (e.g. "Sábado, 10 de octubre de 2026")
  const todayFormatted = new Intl.DateTimeFormat("es-ES", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date());

  // Capitalize first letter of formatted weekday
  const displayDate =
    todayFormatted.charAt(0).toUpperCase() + todayFormatted.slice(1);

  return (
    <header className="top-bar">
      <div className="top-bar-main">
        <div className="brand">
          <img src={logoImg} alt="Barber Shop Logo" className="brand-logo" />
          <div className="brand-text">
            <h1 className="brand-title">Barber Shop</h1>
            <span className="brand-tag">Peluquería · Barbería</span>
          </div>
        </div>

        <div className="top-bar-actions">
          <div className="date-badge">
            <span>{displayDate}</span>
          </div>
          <div className="status-badge">
            <span className="status-pulse"></span>
            <span>FastAPI :8000</span>
          </div>
          {onRefresh && (
            <button className="btn-ghost" onClick={onRefresh} title="Actualizar datos">
              Refrescar
            </button>
          )}
        </div>
      </div>

      <nav className="tab-navigation">
        <button
          className={`tab-btn ${currentTab === "agenda" ? "active" : ""}`}
          onClick={() => setCurrentTab("agenda")}
        >
          Agenda de Hoy
        </button>
        <button
          className={`tab-btn ${currentTab === "new" ? "active" : ""}`}
          onClick={() => setCurrentTab("new")}
        >
          Nueva Cita
        </button>
        <button
          className={`tab-btn ${currentTab === "upcoming" ? "active" : ""}`}
          onClick={() => setCurrentTab("upcoming")}
        >
          Todas las Citas
        </button>
      </nav>
    </header>
  );
}
