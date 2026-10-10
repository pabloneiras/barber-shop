import { useState, useEffect, useCallback } from "react";
import Header from "./components/Header";
import AgendaToday from "./components/AgendaToday";
import { api } from "./services/api";

export default function App() {
  const [currentTab, setCurrentTab] = useState("agenda");
  const [appointments, setAppointments] = useState([]);
  const [filterMode, setFilterMode] = useState("today-all");
  const [customDate, setCustomDate] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [loading, setLoading] = useState(false);

  // Load appointments from FastAPI backend based on selected filter mode
  const loadAppointments = useCallback(async () => {
    setLoading(true);
    try {
      if (filterMode === "today-all") {
        const data = await api.getTodayAppointments();
        setAppointments(data);
      } else if (filterMode === "today-left") {
        const data = await api.getTodayRemainingAppointments();
        setAppointments(data);
      } else if (filterMode === "custom-date") {
        const data = await api.getTodayAppointments();
        setAppointments(data);
      }
    } catch (err) {
      console.error("Failed to load appointments:", err);
    } finally {
      setLoading(false);
    }
  }, [filterMode, customDate]);

  // Fetch appointments on mount and when filter changes
  useEffect(() => {
    loadAppointments();
  }, [loadAppointments]);

  // Handle appointment deletion and refresh list
  const handleDeleteAppointment = async (id) => {
    try {
      await api.deleteAppointment(id);
      await loadAppointments();
    } catch (err) {
      console.error("Failed to delete appointment:", err);
      alert(err.message || "Error al eliminar la cita");
    }
  };

  return (
    <div className="app-container">
      <Header
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        onRefresh={loadAppointments}
      />

      <main className="main-content">
        {currentTab === "agenda" && (
          <AgendaToday
            appointments={appointments}
            filterMode={filterMode}
            setFilterMode={setFilterMode}
            customDate={customDate}
            setCustomDate={setCustomDate}
            onEdit={(appt) => console.log("Editar cita:", appt)}
            onDelete={handleDeleteAppointment}
            onNewAppointmentClick={() => setCurrentTab("new")}
          />
        )}

        {currentTab === "new" && (
          <div className="tab-placeholder">
            <p>Formulario de Nueva Cita (siguiente paso)</p>
          </div>
        )}

        {currentTab === "upcoming" && (
          <div className="tab-placeholder">
            <p>Vista de Todas las Citas Futuras (siguiente paso)</p>
          </div>
        )}
      </main>
    </div>
  );
}
