import { useState, useEffect, useCallback } from "react";
import Header from "./components/Header";
import AgendaToday from "./components/AgendaToday";
import CalendarSidebar from "./components/CalendarSidebar";
import BookingModal from "./components/BookingModal";
import { api } from "./services/api";

// Returns the current local calendar date formatted as an ISO YYYY-MM-DD string
function getTodayLocalDateISOString() {
  const today = new Date();
  const yyyy = today.getFullYear();
  const mm = String(today.getMonth() + 1).padStart(2, "0");
  const dd = String(today.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

export default function App() {
  const [selectedDate, setSelectedDate] = useState(getTodayLocalDateISOString);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalState, setModalState] = useState({
    isOpen: false,
    mode: "create",
    data: null,
  });

  // Fetches appointments for a specific calendar date from FastAPI backend
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

  // Triggers backend fetch whenever the user selects a new calendar date
  useEffect(() => {
    fetchAppointmentsForDate(selectedDate);
  }, [selectedDate, fetchAppointmentsForDate]);

  // Launches modal in creation mode prefilled with the selected date and clicked time slot
  const openNewBookingModalForSlot = (time = "10:00") => {
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
      },
    });
  };

  // Hides the appointment dialog modal and clears its active state
  const closeBookingModal = () => {
    setModalState((prev) => ({ ...prev, isOpen: false }));
  };

  // Handles modal form submit: calls POST for new appointments or PUT for edits, then reloads day data
  const handleSaveAppointmentFromModal = async (formData) => {
    if (modalState.mode === "create") {
      await api.createAppointment(formData);
    } else if (modalState.mode === "edit" && modalState.data?.appointment_id) {
      await api.updateAppointment(modalState.data.appointment_id, {
        appointment_date: formData.appointment_date,
        appointment_time: formData.appointment_time,
        service: formData.service,
      });
    }

    // Refresh appointments list for the currently selected date
    await fetchAppointmentsForDate(selectedDate);
  };

  // Confirms deletion with the user, calls DELETE on FastAPI, and refreshes the timeline
  const cancelAppointmentWithConfirmation = async (id, clientName) => {
    const displayName = clientName || "este cliente";
    const confirmed = window.confirm(`¿Cancelar la cita de ${displayName}?`);
    if (!confirmed) return;

    try {
      await api.deleteAppointment(id);
      await fetchAppointmentsForDate(selectedDate);
    } catch (err) {
      console.error("Failed to delete appointment:", err);
      alert(err.message || "Error al eliminar la cita");
    }
  };

  return (
    <div className="app-shell">
      <Header onNewClick={() => openNewBookingModalForSlot("10:00")} />

      <main className="workspace-grid">
        <AgendaToday
          appointments={appointments}
          selectedDate={selectedDate}
          onEdit={openEditBookingModalForAppointment}
          onDelete={cancelAppointmentWithConfirmation}
          onBookSlot={(time) => openNewBookingModalForSlot(time)}
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
        onClose={closeBookingModal}
        onSubmit={handleSaveAppointmentFromModal}
      />
    </div>
  );
}
