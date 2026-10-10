import React, { useState, useEffect, useRef } from "react";
import { api } from "../services/api";

// Modal dialog for booking new appointments and editing existing ones.
export default function BookingModal({
  isOpen,
  mode = "create",
  initialData = {},
  onClose,
  onSubmit,
}) {
  const [formData, setFormData] = useState({
    phone: "",
    name: "",
    last_name: "",
    appointment_date: new Date().toISOString().split("T")[0],
    appointment_time: "10:00",
    service: "Corte de pelo",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Client autocompletion state
  const [suggestions, setSuggestions] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [recognizedClient, setRecognizedClient] = useState(null);
  const dropdownRef = useRef(null);

  // Synchronizes internal form state with props whenever modal opens or initialData changes
  useEffect(() => {
    if (initialData) {
      setFormData({
        phone: initialData.phone || "",
        name: initialData.name || "",
        last_name: initialData.last_name || "",
        appointment_date:
          initialData.appointment_date || new Date().toISOString().split("T")[0],
        appointment_time: initialData.appointment_time || "10:00",
        service: initialData.service || "Corte de pelo",
      });
    }
    setSuggestions([]);
    setShowDropdown(false);
    setRecognizedClient(null);
    setError(null);
  }, [initialData, isOpen]);

  // Debounces keystrokes in phone field by 200ms to query FastAPI only when user pauses typing
  useEffect(() => {
    if (mode !== "create" || recognizedClient) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    const cleanQuery = formData.phone.trim();
    if (cleanQuery.length < 2) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const results = await api.searchClients(cleanQuery);
        setSuggestions(results);
        setShowDropdown(results.length > 0);
      } catch (err) {
        console.error("Failed to autocomplete clients:", err);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [formData.phone, mode, recognizedClient]);

  if (!isOpen) return null;

  const isEdit = mode === "edit";

  // Populates all form fields with selected client data and sets habitual client banner
  const populateFormWithSelectedClient = (client) => {
    setFormData((prev) => ({
      ...prev,
      phone: client.phone,
      name: client.name || "",
      last_name: client.last_name || "",
      service: client.last_service || prev.service,
    }));
    setRecognizedClient(client);
    setSuggestions([]);
    setShowDropdown(false);
  };

  // Clears recognized client banner to allow manual typing without autocomplete lock
  const resetRecognizedClientSelection = () => {
    setRecognizedClient(null);
  };

  // Validates required fields, sends payload to App handler, and handles API errors
  const handleAppointmentFormSubmit = async (e) => {
    e.preventDefault();
    if (!formData.phone.trim()) {
      setError("El teléfono es obligatorio");
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      await onSubmit(formData);
      onClose();
    } catch (err) {
      setError(err.message || "Error al procesar la cita");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Quick-selects a preset service name when clicking a service chip button
  const selectQuickServiceChip = (serviceName) => {
    setFormData((prev) => ({ ...prev, service: serviceName }));
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header-bar">
          <div>
            <h3 className="modal-title">
              {isEdit ? "Editar Cita" : "Nueva Cita / Agenda"}
            </h3>
            <p className="modal-desc">
              {isEdit
                ? "Modifica los datos de la reserva existente"
                : "Introduce los datos del cliente para reservar el hueco"}
            </p>
          </div>
          <button className="btn-close-modal" onClick={onClose} type="button">
            ✕
          </button>
        </div>

        {error && <div className="toast-bar">{error}</div>}

        <form onSubmit={handleAppointmentFormSubmit} className="modal-form-body">
          {recognizedClient && (
            <div className="client-recognized-banner">
              <span>
                Cliente habitual: <strong>{recognizedClient.name} {recognizedClient.last_name || ""}</strong>
              </span>
              <button
                type="button"
                className="btn-clear-recognized"
                onClick={resetRecognizedClientSelection}
              >
                Cambiar
              </button>
            </div>
          )}

          <div className="field-group">
            <label className="field-label">Teléfono *</label>
            <div className="autocomplete-container" ref={dropdownRef}>
              <input
                name="phone"
                type="tel"
                className="field-input"
                placeholder="Teléfono del cliente (ej. 600112233)"
                value={formData.phone}
                onChange={(e) => {
                  setFormData({ ...formData, phone: e.target.value });
                  if (recognizedClient) setRecognizedClient(null);
                }}
                onFocus={() => {
                  if (suggestions.length > 0) setShowDropdown(true);
                }}
                onBlur={() => {
                  // Delayed hide allows onMouseDown on suggestion item to register before blur
                  setTimeout(() => setShowDropdown(false), 200);
                }}
                required
                autoFocus
                autoComplete="off"
              />

              {showDropdown && suggestions.length > 0 && (
                <div className="autocomplete-dropdown">
                  {suggestions.map((client) => {
                    const clientFullName = (
                      client.name
                        ? `${client.name} ${client.last_name || ""}`
                        : "Cliente sin nombre"
                    ).trim();

                    return (
                      <div
                        key={client.client_id}
                        className="autocomplete-item"
                        onMouseDown={() => populateFormWithSelectedClient(client)}
                      >
                        <div className="ac-client-info">
                          <span className="ac-client-name">{clientFullName}</span>
                          <span className="ac-client-phone">{client.phone}</span>
                        </div>
                        <div className="ac-client-meta">
                          {client.visits_count > 0 && (
                            <span className="ac-visits-tag">
                              {client.visits_count} {client.visits_count === 1 ? "visita" : "visitas"}
                            </span>
                          )}
                          {client.last_service && (
                            <span className="ac-last-service">{client.last_service}</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          <div className="field-row-2">
            <div className="field-group">
              <label className="field-label">Nombre</label>
              <input
                name="name"
                type="text"
                className="field-input"
                placeholder="Nombre"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
              />
            </div>
            <div className="field-group">
              <label className="field-label">Apellidos</label>
              <input
                name="last_name"
                type="text"
                className="field-input"
                placeholder="Apellidos"
                value={formData.last_name}
                onChange={(e) =>
                  setFormData({ ...formData, last_name: e.target.value })
                }
              />
            </div>
          </div>

          <div className="field-row-2">
            <div className="field-group">
              <label className="field-label">Fecha</label>
              <input
                name="appointment_date"
                type="date"
                className="field-input"
                value={formData.appointment_date}
                onChange={(e) =>
                  setFormData({ ...formData, appointment_date: e.target.value })
                }
                required
              />
            </div>
            <div className="field-group">
              <label className="field-label">Hora</label>
              <input
                name="appointment_time"
                type="time"
                className="field-input"
                value={formData.appointment_time}
                onChange={(e) =>
                  setFormData({ ...formData, appointment_time: e.target.value })
                }
                required
              />
            </div>
          </div>

          <div className="field-group">
            <label className="field-label">Servicio</label>
            <input
              name="service"
              type="text"
              className="field-input"
              value={formData.service}
              onChange={(e) =>
                setFormData({ ...formData, service: e.target.value })
              }
            />
            <div className="quick-services-row">
              <button
                type="button"
                className="btn-chip-mono"
                onClick={() => selectQuickServiceChip("Corte de pelo")}
              >
                Corte
              </button>
              <button
                type="button"
                className="btn-chip-mono"
                onClick={() => selectQuickServiceChip("Arreglo de barba")}
              >
                Barba
              </button>
              <button
                type="button"
                className="btn-chip-mono"
                onClick={() => selectQuickServiceChip("Corte y barba")}
              >
                Corte + Barba
              </button>
              <button
                type="button"
                className="btn-chip-mono"
                onClick={() => selectQuickServiceChip("Afeitado clásico")}
              >
                Afeitado
              </button>
            </div>
          </div>

          <div className="modal-actions-bar">
            <button type="button" className="btn-ghost" onClick={onClose}>
              Cancelar
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={isSubmitting}
            >
              {isSubmitting
                ? "Guardando..."
                : isEdit
                ? "Guardar Cambios"
                : "Confirmar Cita"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
