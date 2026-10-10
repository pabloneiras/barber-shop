import { useState, useEffect, useCallback } from "react";
import Header from "./components/Header";
import AgendaToday from "./components/AgendaToday";
import CalendarSidebar from "./components/CalendarSidebar";
import BookingModal from "./components/BookingModal";
import { api } from "./services/api";

// Returns current local date formatted as YYYY-MM-DD
function getTodayISO() {
  const today = new Date();
  const yyyy = today.getFullYear();
  const mm = String(today.getMonth() + 1).padStart(2, "0");
  const dd = String(today.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

export default function App() {
  const [selectedDate, setSelectedDate] = useState(getTodayISO);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalState, setModalState] = useState({
    isOpen: false,
    mode: "create",
    data: null,
  });

  // Fetch appointments for the selected date from FastAPI
  const loadAppointments = useCallback(async (date) => {
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

  // Reload appointments whenever the selected calendar date changes
  useEffect(() => {
    loadAppointments(selectedDate);
  }, [selectedDate, loadAppointments]);

  // Open modal to schedule a new appointment at a specific time slot
  const handleOpenNewModal = (time = "10:00") => {
    setModalState({
      isOpen: true,
      mode: "create",
      data: {
        phone: "",
        name: "",
        last_name: "",
        appointment_date: selectedDate,
        appointment_time: time,
        service: "Corte de pelo",
      },
    });
  };

  // Open modal in edit mode with existing appointment data
  const handleOpenEditModal = (appointment) => {
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
      },
    });
  };

  // Close the active modal dialog
  const handleCloseModal = () => {
    setModalState((prev) => ({ ...prev, isOpen: false }));
  };

  // Process form submission for both create and update operations
  const handleSubmitModal = async (formData) => {
    if (modalState.mode === "create") {
      await api.createAppointment(formData);
    } else if (modalState.mode === "edit" && modalState.data?.appointment_id) {
      await api.updateAppointment(modalState.data.appointment_id, {
        appointment_date: formData.appointment_date,
        appointment_time: formData.appointment_time,
        service: formData.service,
      });
    }

    // Refresh appointment list for the currently viewed date
    await loadAppointments(selectedDate);
  };

  // Delete an appointment after user confirmation
  const handleDeleteAppointment = async (id, clientName) => {
    const displayName = clientName || "este cliente";
    const confirmed = window.confirm(`¿Cancelar la cita de ${displayName}?`);
    if (!confirmed) return;

    try {
      await api.deleteAppointment(id);
      await loadAppointments(selectedDate);
    } catch (err) {
      console.error("Failed to delete appointment:", err);
      alert(err.message || "Error al eliminar la cita");
    }
  };

  return (
    <div className="app-shell">
      <Header onNewClick={() => handleOpenNewModal("10:00")} />

      <main className="workspace-grid">
        <AgendaToday
          appointments={appointments}
          selectedDate={selectedDate}
          onEdit={handleOpenEditModal}
          onDelete={handleDeleteAppointment}
          onBookSlot={(time) => handleOpenNewModal(time)}
        />

        <CalendarSidebar
          selectedDate={selectedDate}
          setSelectedDate={setSelectedDate}
          appointmentsCount={appointments.length}
        />
      </main>

      <BookingModal
        isOpen={modalState.isOpen}
        mode={modalState.mode}
        initialData={modalState.data}
        onClose={handleCloseModal}
        onSubmit={handleSubmitModal}
      />
    </div>
  );
}
