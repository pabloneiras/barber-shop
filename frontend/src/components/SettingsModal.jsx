import React, { useState, useEffect } from "react";
import { useLanguage } from "../context/LanguageContext";
import { api } from "../services/api";

const PRESET_COLORS = [
  { hex: "#3b82f6", name: "Azul" },
  { hex: "#f59e0b", name: "Dorado / VIP" },
  { hex: "#10b981", name: "Verde" },
  { hex: "#8b5cf6", name: "Púrpura" },
  { hex: "#ec4899", name: "Rosa" },
];

export default function SettingsModal({
  isOpen,
  onClose,
  config,
  onSaveConfig,
  onServicesChanged,
}) {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState("services"); // 'services' | 'weekly'

  // Services state
  const [services, setServices] = useState([]);
  const [loadingServices, setLoadingServices] = useState(false);
  const [newServiceName, setNewServiceName] = useState("");
  const [newServicePrice, setNewServicePrice] = useState("12");
  const [newServiceColor, setNewServiceColor] = useState("#3b82f6");

  // Weekly schedule config local state
  const [localDaysMode, setLocalDaysMode] = useState(config.daysMode || "mon-sat");
  const [localStartHour, setLocalStartHour] = useState(config.startHour || "09:30");
  const [localEndHour, setLocalEndHour] = useState(config.endHour || "20:30");
  const [localInterval, setLocalInterval] = useState(config.intervalMinutes || 30);

  const loadServices = async () => {
    setLoadingServices(true);
    try {
      const data = await api.getServices();
      setServices(data);
    } catch (err) {
      console.error("Error loading services:", err);
    } finally {
      setLoadingServices(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadServices();
      setLocalDaysMode(config.daysMode || "mon-sat");
      setLocalStartHour(config.startHour || "09:30");
      setLocalEndHour(config.endHour || "20:30");
      setLocalInterval(config.intervalMinutes || 30);
    }
  }, [isOpen, config]);

  if (!isOpen) return null;

  // Add new service
  const handleAddService = async (e) => {
    e.preventDefault();
    if (!newServiceName.trim()) return;
    try {
      await api.createService({
        name: newServiceName.trim(),
        price: parseFloat(newServicePrice) || 0,
        default_color: newServiceColor,
      });
      setNewServiceName("");
      setNewServicePrice("12");
      await loadServices();
      if (onServicesChanged) onServicesChanged();
    } catch (err) {
      alert("Error creando servicio: " + err.message);
    }
  };

  // Update existing service
  const handleUpdateService = async (svcId, newPrice, newColor) => {
    try {
      await api.updateService(svcId, {
        price: parseFloat(newPrice) || 0,
        default_color: newColor,
      });
      await loadServices();
      if (onServicesChanged) onServicesChanged();
    } catch (err) {
      alert("Error actualizando servicio: " + err.message);
    }
  };

  // Delete service
  const handleDeleteService = async (svcId, name) => {
    if (!window.confirm(`¿Eliminar el servicio "${name}"?`)) return;
    try {
      await api.deleteService(svcId);
      await loadServices();
      if (onServicesChanged) onServicesChanged();
    } catch (err) {
      alert("Error eliminando servicio: " + err.message);
    }
  };

  // Save weekly settings
  const handleSaveWeeklySettings = () => {
    const newConfig = {
      daysMode: localDaysMode,
      startHour: localStartHour,
      endHour: localEndHour,
      intervalMinutes: parseInt(localInterval, 10),
    };
    onSaveConfig(newConfig);
    onClose();
  };

  return (
    <div className="modal-backdrop modal-overlay" onClick={onClose}>
      <div
        className="modal-box modal-box-large"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-box-header modal-header-bar">
          <div>
            <h2 className="modal-box-title modal-title">{t.settingsTitle}</h2>
          </div>
          <button
            type="button"
            className="modal-close btn-close-modal"
            onClick={onClose}
          >
            ×
          </button>
        </div>

        {/* Modal Tab Switcher */}
        <div className="settings-tab-nav">
          <button
            type="button"
            className={`btn-settings-tab ${activeTab === "services" ? "active" : ""}`}
            onClick={() => setActiveTab("services")}
          >
            {t.tabServices}
          </button>
          <button
            type="button"
            className={`btn-settings-tab ${activeTab === "weekly" ? "active" : ""}`}
            onClick={() => setActiveTab("weekly")}
          >
            {t.tabWeeklyConfig}
          </button>
        </div>

        <div className="settings-tab-content">
          {/* TAB 1: Servicios y Precios */}
          {activeTab === "services" && (
            <div className="services-settings-pane">
              {/* Existing Services List */}
              <div className="services-table-wrapper">
                <table className="settings-services-table">
                  <thead>
                    <tr>
                      <th>{t.serviceName}</th>
                      <th style={{ width: "110px" }}>{t.servicePrice}</th>
                      <th style={{ width: "120px" }}>{t.serviceColor}</th>
                      <th style={{ width: "90px" }}>{t.actions}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {services.map((svc) => (
                      <tr key={svc.service_id}>
                        <td>
                          <span className="svc-table-name">{svc.name}</span>
                        </td>
                        <td>
                          <input
                            type="number"
                            step="0.5"
                            className="input-number-price"
                            defaultValue={svc.price}
                            onBlur={(e) =>
                              handleUpdateService(
                                svc.service_id,
                                e.target.value,
                                svc.default_color
                              )
                            }
                          />
                        </td>
                        <td>
                          <div className="color-picker-cell">
                            <input
                              type="color"
                              className="color-input-dot"
                              defaultValue={svc.default_color || "#3b82f6"}
                              onChange={(e) =>
                                handleUpdateService(
                                  svc.service_id,
                                  svc.price,
                                  e.target.value
                                )
                              }
                            />
                            <span className="color-hex-label">
                              {svc.default_color}
                            </span>
                          </div>
                        </td>
                        <td>
                          <button
                            type="button"
                            className="btn-danger-sm"
                            onClick={() =>
                              handleDeleteService(svc.service_id, svc.name)
                            }
                          >
                            {t.btnDelete}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Add New Service Form */}
              <form className="add-service-form" onSubmit={handleAddService}>
                <h4 className="add-service-title">{t.newService}</h4>
                <div className="add-service-inputs-row">
                  <input
                    type="text"
                    className="form-control"
                    placeholder={t.serviceName}
                    value={newServiceName}
                    onChange={(e) => setNewServiceName(e.target.value)}
                    required
                  />
                  <input
                    type="number"
                    step="0.5"
                    className="form-control input-price-short"
                    placeholder={t.servicePrice}
                    value={newServicePrice}
                    onChange={(e) => setNewServicePrice(e.target.value)}
                    required
                  />
                  <input
                    type="color"
                    className="color-input-dot"
                    value={newServiceColor}
                    onChange={(e) => setNewServiceColor(e.target.value)}
                    title={t.customColor}
                  />
                  <button type="submit" className="btn-primary">
                    +
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* TAB 2: Horario Semanal */}
          {activeTab === "weekly" && (
            <div className="weekly-settings-pane">
              <div className="form-group-setting">
                <label className="setting-label">{t.workDays}</label>
                <select
                  className="form-control"
                  value={localDaysMode}
                  onChange={(e) => setLocalDaysMode(e.target.value)}
                >
                  <option value="mon-fri">{t.optMonFri}</option>
                  <option value="mon-sat">{t.optMonSat}</option>
                  <option value="mon-sun">{t.optAllWeek}</option>
                </select>
              </div>

              <div className="form-row-two">
                <div className="form-group-setting">
                  <label className="setting-label">{t.startHour}</label>
                  <select
                    className="form-control"
                    value={localStartHour}
                    onChange={(e) => setLocalStartHour(e.target.value)}
                  >
                    <option value="08:00">08:00</option>
                    <option value="08:30">08:30</option>
                    <option value="09:00">09:00</option>
                    <option value="09:30">09:30</option>
                    <option value="10:00">10:00</option>
                  </select>
                </div>

                <div className="form-group-setting">
                  <label className="setting-label">{t.endHour}</label>
                  <select
                    className="form-control"
                    value={localEndHour}
                    onChange={(e) => setLocalEndHour(e.target.value)}
                  >
                    <option value="19:00">19:00</option>
                    <option value="19:30">19:30</option>
                    <option value="20:00">20:00</option>
                    <option value="20:30">20:30</option>
                    <option value="21:00">21:00</option>
                    <option value="21:30">21:30</option>
                    <option value="22:00">22:00</option>
                  </select>
                </div>
              </div>

              <div className="form-group-setting">
                <label className="setting-label">{t.timeInterval}</label>
                <select
                  className="form-control"
                  value={localInterval}
                  onChange={(e) => setLocalInterval(Number(e.target.value))}
                >
                  <option value={30}>{t.min30}</option>
                  <option value={60}>{t.min60}</option>
                </select>
              </div>

              <div className="modal-actions-bar" style={{ marginTop: "24px" }}>
                <button
                  type="button"
                  className="btn-primary"
                  onClick={handleSaveWeeklySettings}
                >
                  {t.btnSave}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
