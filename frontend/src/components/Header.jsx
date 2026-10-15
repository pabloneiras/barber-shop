import React from "react";
import { useLanguage } from "../context/LanguageContext";

// Minimalist top bar with brand title, language toggle, live status pill, and quick booking action.
export default function Header({ activeView, setActiveView, onNewClick, onOpenSettings }) {
  const { language, setLanguage, t } = useLanguage();

  return (
    <header className="top-bar">
      <div className="brand">
        <div>
          <h1 className="brand-title">Barber Shop</h1>
          <span className="brand-tag">{t.brandTag}</span>
        </div>
      </div>

      <nav className="view-nav-tabs">
        <button
          type="button"
          className={`nav-tab ${activeView === "day" ? "active" : ""}`}
          onClick={() => setActiveView("day")}
        >
          {t.tabDay}
        </button>
        <button
          type="button"
          className={`nav-tab ${activeView === "week" ? "active" : ""}`}
          onClick={() => setActiveView("week")}
        >
          {t.tabWeek}
        </button>
        <button
          type="button"
          className={`nav-tab ${activeView === "stats" ? "active" : ""}`}
          onClick={() => setActiveView("stats")}
        >
          {t.tabStats}
        </button>
      </nav>

      <div className="top-bar-actions">
        <button
          type="button"
          className="btn-settings-header"
          onClick={onOpenSettings}
          title={t.btnSettings}
        >
          {t.btnSettings}
        </button>

        <div className="lang-selector">
          <button
            type="button"
            className={`btn-lang ${language === "es" ? "active" : ""}`}
            onClick={() => setLanguage("es")}
          >
            ES
          </button>
          <span className="lang-divider">/</span>
          <button
            type="button"
            className={`btn-lang ${language === "en" ? "active" : ""}`}
            onClick={() => setLanguage("en")}
          >
            EN
          </button>
        </div>

        <div className="status-badge">
          <span className="status-pulse"></span>
          <span>{t.serverOnline}</span>
        </div>

        <button className="btn-primary" onClick={onNewClick}>
          {t.newAppointment}
        </button>
      </div>
    </header>
  );
}
