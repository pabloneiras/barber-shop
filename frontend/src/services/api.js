/**
 * Centralized API client communicating with the local FastAPI backend.
 * All requests target http://127.0.0.1:8000 where Uvicorn serves the API.
 */
const API_BASE_URL =
  typeof window !== "undefined" && window.location.port === "5173"
    ? "http://127.0.0.1:8000"
    : "";

// Central wrapper function to handle network calls, headers, and error parsing.
// Prepends the base URL and deserializes JSON response payloads automatically.
async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  try {
    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
      let errorDetail = `HTTP Error ${response.status}`;
      try {
        const errorJson = await response.json();
        errorDetail = errorJson.detail || JSON.stringify(errorJson);
      } catch {
        errorDetail = await response.text();
      }
      throw new Error(errorDetail);
    }
    return await response.json();
  } catch (error) {
    console.error(`Request to ${endpoint} failed:`, error);
    throw error;
  }
}

// Fetches all appointments scheduled for the current day.
// Calls GET /appointments/today/ on the FastAPI server.
export async function getTodayAppointments() {
  return request("/appointments/today/");
}

// Fetches all appointments scheduled for a specific date (YYYY-MM-DD).
// Calls GET /appointments/date/{date} on the FastAPI server.
export async function getAppointmentsByDate(date) {
  return request(`/appointments/date/${date}`);
}

// Fetches appointments remaining from the current hour until the end of today.
// Calls GET /appointments/today/left on the FastAPI server.
export async function getTodayRemainingAppointments() {
  return request("/appointments/today/left");
}

// Fetches all pending appointments scheduled from now into the future.
// Calls GET /appointments/left on the FastAPI server.
export async function getUpcomingAppointments() {
  return request("/appointments/left");
}

// Fetches a single appointment details by its unique primary key ID.
// Calls GET /appointments/{id} on the FastAPI server.
export async function getAppointmentById(id) {
  return request(`/appointments/${id}`);
}

// Fetches appointment history records for a specific client ID.
// Calls GET /appointments/clients/{clientId} on the FastAPI server.
export async function getClientAppointments(clientId) {
  return request(`/appointments/clients/${clientId}`);
}

// Searches clients by phone or name substring for live autocompletion.
// Calls GET /clients/search?q={query} on the FastAPI server.
export async function searchClients(query) {
  if (!query || !query.trim()) return [];
  return request(`/clients/search?q=${encodeURIComponent(query.trim())}`);
}


// Sends new appointment payload to create a record in the database.
// Calls POST /appointments/ with JSON body matching AppointmentCreate schema.
export async function createAppointment(appointmentData) {
  return request("/appointments/", {
    method: "POST",
    body: JSON.stringify(appointmentData),
  });
}

// Modifies an existing appointment date, time, or service.
// Calls PUT /appointments/{id} with JSON body matching AppointmentUpdate schema.
export async function updateAppointment(id, updateData) {
  return request(`/appointments/${id}`, {
    method: "PUT",
    body: JSON.stringify(updateData),
  });
}

// Cancels and removes an appointment permanently from the database.
// Calls DELETE /appointments/{id} on the FastAPI server.
export async function deleteAppointment(id) {
  return request(`/appointments/${id}`, {
    method: "DELETE",
  });
}

// Bundled export object for convenience and compatibility with components.
// One only object that is made to "export" all functions in One object
export const api = {
  getTodayAppointments,
  getAppointmentsByDate,
  getTodayRemainingAppointments,
  getUpcomingAppointments,
  getAppointmentById,
  getClientAppointments,
  searchClients,
  createAppointment,
  updateAppointment,
  deleteAppointment,
};
