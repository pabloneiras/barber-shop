// Bilingual dictionary (Spanish / English) for the Barber Shop user interface

export const translations = {
  es: {
    // Header
    brandTag: "Libro de Citas / Agenda",
    serverOnline: "Servidor Activo (127.0.0.1:8000)",
    newAppointment: "+ Nueva Cita",

    // Timeline Ledger (AgendaToday)
    noAppointments: "SIN CITAS REGISTRADAS",
    oneAppointment: "1 CITA REGISTRADA",
    appointmentsRegistered: "CITAS REGISTRADAS",
    bookForDay: "+ Agendar en este día",
    unnamedClient: "Cliente sin nombre",
    edit: "Editar",
    cancel: "Cancelar",
    availableSlot: "Hueco Disponible",
    bookSlot: "+ Reservar",
    confirmCancel: (name) => `¿Cancelar la cita de ${name}?`,
    cancelError: "Error al eliminar la cita",
    monthNames: [
      "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
      "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ],
    weekdayNames: [
      "Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"
    ],
    dateHeaderFormat: (dayName, day, monthName, year) =>
      `${dayName}, ${day} de ${monthName} de ${year}`,

    // Calendar Sidebar
    prevMonth: "Mes anterior",
    nextMonth: "Mes siguiente",
    weekdaysShort: ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
    sidebarInfoTitle: "Resumen de Agenda",
    statLabel: "Citas en el día",
    sidebarInfoDesc:
      "Selecciona cualquier fecha en el calendario para consultar o gestionar las citas.",

    // Booking Modal
    modalTitleCreate: "Nueva Cita / Agenda",
    modalTitleEdit: "Editar Cita",
    modalDescCreate: "Introduce los datos del cliente para reservar el hueco",
    modalDescEdit: "Modifica los datos de la reserva existente",
    clientRecognized: "Cliente habitual:",
    btnChangeClient: "Cambiar",
    labelPhone: "Teléfono *",
    placeholderPhone: "Teléfono del cliente (ej. 600112233)",
    phoneRequiredError: "El teléfono es obligatorio",
    errorProcessing: "Error al procesar la cita",
    labelName: "Nombre",
    placeholderName: "Nombre",
    labelLastName: "Apellidos",
    placeholderLastName: "Apellidos",
    labelDate: "Fecha",
    labelTime: "Hora",
    labelService: "Servicio",
    chipHaircut: "Corte",
    chipBeard: "Barba",
    chipHaircutBeard: "Corte + Barba",
    chipShave: "Afeitado",
    defaultService: "Corte de pelo",
    serviceHaircut: "Corte de pelo",
    serviceBeard: "Arreglo de barba",
    serviceHaircutBeard: "Corte y barba",
    serviceShave: "Afeitado clásico",
    btnCancelModal: "Cancelar",
    btnSaving: "Guardando...",
    btnSaveEdit: "Guardar Cambios",
    btnConfirmCreate: "Confirmar Cita",
    habitualVisits: "visitas",
    lastServicePrefix: "Último:",
  },

  en: {
    // Header
    brandTag: "Appointment Book / Ledger",
    serverOnline: "Server Online (127.0.0.1:8000)",
    newAppointment: "+ New Appointment",

    // Timeline Ledger (AgendaToday)
    noAppointments: "NO APPOINTMENTS REGISTERED",
    oneAppointment: "1 APPOINTMENT REGISTERED",
    appointmentsRegistered: "APPOINTMENTS REGISTERED",
    bookForDay: "+ Book on this day",
    unnamedClient: "Unnamed Client",
    edit: "Edit",
    cancel: "Cancel",
    availableSlot: "Available Slot",
    bookSlot: "+ Book",
    confirmCancel: (name) => `Cancel appointment for ${name}?`,
    cancelError: "Error deleting appointment",
    monthNames: [
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    ],
    weekdayNames: [
      "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
    ],
    dateHeaderFormat: (dayName, day, monthName, year) =>
      `${dayName}, ${monthName} ${day}, ${year}`,

    // Calendar Sidebar
    prevMonth: "Previous month",
    nextMonth: "Next month",
    weekdaysShort: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    sidebarInfoTitle: "Schedule Summary",
    statLabel: "Appointments today",
    sidebarInfoDesc:
      "Select any date on the calendar to view or manage appointments.",

    // Booking Modal
    modalTitleCreate: "New Appointment / Booking",
    modalTitleEdit: "Edit Appointment",
    modalDescCreate: "Enter client details to reserve the slot",
    modalDescEdit: "Modify details of the existing reservation",
    clientRecognized: "Regular client:",
    btnChangeClient: "Change",
    labelPhone: "Phone *",
    placeholderPhone: "Client phone number (e.g. 600112233)",
    phoneRequiredError: "Phone number is required",
    errorProcessing: "Error processing appointment",
    labelName: "First Name",
    placeholderName: "First Name",
    labelLastName: "Last Name",
    placeholderLastName: "Last Name",
    labelDate: "Date",
    labelTime: "Time",
    labelService: "Service",
    chipHaircut: "Haircut",
    chipBeard: "Beard",
    chipHaircutBeard: "Haircut + Beard",
    chipShave: "Shave",
    defaultService: "Haircut",
    serviceHaircut: "Haircut",
    serviceBeard: "Beard trim",
    serviceHaircutBeard: "Haircut and beard",
    serviceShave: "Classic shave",
    btnCancelModal: "Cancel",
    btnSaving: "Saving...",
    btnSaveEdit: "Save Changes",
    btnConfirmCreate: "Confirm Booking",
    habitualVisits: "visits",
    lastServicePrefix: "Last:",
  },
};
