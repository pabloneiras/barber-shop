import { useState, useEffect, useCallback } from "react";
import Header from "./components/Header";
import AgendaToday from "./components/AgendaToday";
import CalendarSidebar from "./components/CalendarSidebar";
import AgendaWeekly from "./components/AgendaWeekly";
import StatsDashboard from "./components/StatsDashboard";
import SettingsModal from "./components/SettingsModal";
import BookingModal from "./components/BookingModal";
import { api } from "./services/api";
import { LanguageProvider, useLanguage } from "./context/LanguageContext";

// Returns the current local calendar date formatted as an ISO YYYY-MM-DD string
function getTodayLocalDateISOString() {
  const today = new Date();
  const yyyy = today.getFullYear();
  const mm = String(today.getMonth() + 1).padStart(2, "0");
  const dd = String(today.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

const DEFAULT_WEEKLY_CONFIG = {
  daysMode: "mon-sat",
  startHour: "09:30",
  endHour: "20:30",
  intervalMinutes: 30,
};

function MainWorkspace() {
  const { t } = useLanguage();
  const [activeView, setActiveView] = useState(() => {
    return localStorage.getItem("barber_active_view") || "week";
  });

  const [selectedDate, setSelectedDate] = useState(getTodayLocalDateISOString);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  // Settings modal & config
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [weeklyConfig, setWeeklyConfig] = useState(() => {
    try {
      const stored = localStorage.getItem("barber_weekly_config");
      return stored ? JSON.parse(stored) : DEFAULT_WEEKLY_CONFIG;
    } catch {
      return DEFAULT_WEEKLY_CONFIG;
    }
  });

  const [modalState, setModalState] = useState({
    isOpen: false,
    mode: "create",
    data: null,
  });

  // Persist active view
  const handleViewChange = (view) => {
    setActiveView(view);
    localStorage.setItem("barber_active_view", view);
  };

  // Persist weekly config
  const handleSaveWeeklyConfig = (newCfg) => {
    setWeeklyConfig(newCfg);
    localStorage.setItem("barber_weekly_config", JSON.stringify(newCfg));
  };

  // Fetches appointments for daily view
  const fetchAppointmentsForDate = useCallback(async (date) => {
    setLoading(true);
    try {
      const data = await api.getAppointmentsByDate(date);
      setAppointments(data);
    } catch (err) {
      console.error("Failed to load appointments:", err);
      setAppointments([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeView === "day") {
      fetchAppointmentsForDate(selectedDate);
    }
  }, [selectedDate, activeView, fetchAppointmentsForDate, refreshKey]);

  // Launches modal in creation mode prefilled with date and time
  const openNewBookingModalForSlot = (time = "10:00", date = null) => {
    const targetDate = date || selectedDate || getTodayLocalDateISOString();
    setModalState({
      isOpen: true,
      mode: "create",
      data: {
        phone: "",
        name: "",
        last_name: "",
        appointment_date: targetDate,
        appointment_time: time,
        service: t.defaultService,
        price: 12.0,
        color: "#3b82f6",
      },
    });
  };

  // Launches modal in edit mode prefilled with an existing appointment's current data
  const openEditBookingModalForAppointment = (appointment) => {
    setModalState({
      isOpen: true,
      mode: "edit",
      data: {
        appointment_id: appointment.appointment_id,
        phone: appointment.phone || "",
        name: appointment.name || "",
        last_name: appointment.last_name || "",
        appointment_date: appointment.appointment_date,
        appointment_time: appointment.appointment_time,
        service: appointment.service || "",
        price: appointment.price !== undefined ? appointment.price : 12.0,
        color: appointment.color || "#3b82f6",
      },
    });
  };

  const closeBookingModal = () => {
    setModalState((prev) => ({ ...prev, isOpen: false }));
  };

  // Handles modal form submit: calls POST for new appointments or PUT for edits
  const handleSaveAppointmentFromModal = async (formData) => {
    if (modalState.mode === "create") {
      await api.createAppointment(formData);
    } else if (modalState.mode === "edit" && modalState.data?.appointment_id) {
      await api.updateAppointment(modalState.data.appointment_id, {
        appointment_date: formData.appointment_date,
        appointment_time: formData.appointment_time,
        service: formData.service,
        price: formData.price,
        color: formData.color,
      });
    }

    setRefreshKey((k) => k + 1);
  };

  // Confirms deletion with the user, calls DELETE on FastAPI
  const cancelAppointmentWithConfirmation = async (id, clientName) => {
    const displayName = clientName || t.unnamedClient;
    const confirmed = window.confirm(t.confirmCancel(displayName));
    if (!confirmed) return;

    try {
      await api.deleteAppointment(id);
      setRefreshKey((k) => k + 1);
    } catch (err) {
      console.error("Failed to delete appointment:", err);
      alert(err.message || t.cancelError);
    }
  };

  return (
    <div className="app-shell">
      <Header
        activeView={activeView}
        setActiveView={handleViewChange}
        onNewClick={() => openNewBookingModalForSlot("10:00")}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      <main className="workspace-main">
        {activeView === "day" && (
          <div className="workspace-grid">
            <AgendaToday
              appointments={appointments}
              selectedDate={selectedDate}
              onEdit={openEditBookingModalForAppointment}
              onDelete={cancelAppointmentWithConfirmation}
              onBookSlot={(time) => openNewBookingModalForSlot(time, selectedDate)}
            />

            <CalendarSidebar
              selectedDate={selectedDate}
              setSelectedDate={setSelectedDate}
              appointmentsCount={appointments.length}
            />
          </div>
        )}

        {activeView === "week" && (
          <AgendaWeekly
            config={weeklyConfig}
            refreshKey={refreshKey}
            onEdit={openEditBookingModalForAppointment}
            onBookSlot={(date, time) => openNewBookingModalForSlot(time, date)}
          />
        )}

        {activeView === "stats" && (
          <StatsDashboard key={refreshKey} />
        )}
      </main>

      <BookingModal
        isOpen={modalState.isOpen}
        mode={modalState.mode}
        initialData={modalState.data}
        onClose={closeBookingModal}
        onSubmit={handleSaveAppointmentFromModal}
      />

      <SettingsModal
        isOpen={isSettingsOpen}
        config={weeklyConfig}
        onClose={() => setIsSettingsOpen(false)}
        onSaveConfig={handleSaveWeeklyConfig}
        onServicesChanged={() => setRefreshKey((k) => k + 1)}
      />
    </div>
  );
}

export default function App() {
  return (
    <LanguageProvider>
      <MainWorkspace />
    </LanguageProvider>
  );
}
