import React from "react";
import { useLanguage } from "../context/LanguageContext";

// Minimalist top bar with brand title, language toggle, live status pill, and quick booking action.
export default function Header({ onNewClick }) {
  const { language, setLanguage, t } = useLanguage();

  return (
    <header className="top-bar">
      <div className="brand">
        <div>
          <h1 className="brand-title">Barber Shop</h1>
          <span className="brand-tag">{t.brandTag}</span>
        </div>
      </div>

      <div className="top-bar-actions">
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
