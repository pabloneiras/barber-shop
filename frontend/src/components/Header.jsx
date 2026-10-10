import React from "react";
import logoImg from "../assets/logo.jpg";

// Minimalist top bar with brand mark, live status pill, and quick booking action.
export default function Header({ onNewClick }) {
  return (
    <header className="top-bar">
      <div className="brand">
        <img src={logoImg} alt="Barber Shop Logo" className="brand-logo" />
        <div>
          <h1 className="brand-title">Barber Shop</h1>
          <span className="brand-tag">Libro de Citas / Agenda</span>
        </div>
      </div>

      <div className="top-bar-actions">
        <div className="status-badge">
          <span className="status-pulse"></span>
          <span>Servidor Activo (127.0.0.1:8000)</span>
        </div>
        <button className="btn-primary" onClick={onNewClick}>
          + Nueva Cita
        </button>
      </div>
    </header>
  );
}
