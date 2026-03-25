/**
 * Centralised API client.
 *
 * All HTTP calls go through the `request()` wrapper, which:
 *  - Points at `/api` (the SvelteKit proxy in hooks.server.js, not the backend directly)
 *  - Always sends/expects JSON
 *  - Throws a meaningful Error on non-2xx so call sites only need a try/catch
 *
 * Every public method on `api` maps 1-to-1 to a FastAPI route. Adding a new
 * endpoint means adding one line here and nowhere else.
 */
const BASE_URL = '/api';

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${BASE_URL}${path}`, opts);
  if (!res.ok) {
    // Prefer the `detail` field that FastAPI puts in error responses
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  // --- Session lifecycle ---
  createSession: () => request('POST', '/session'),
  startSession: (sessionId, patientId) => request('POST', `/session/${sessionId}/start/${patientId}`),
  startSessionWithLocalPatient: (sessionId, patientId) => request('POST', `/session/${sessionId}/start-local/${patientId}`),
  getState: (sessionId) => request('GET', `/session/${sessionId}/state`),
  deleteSession: (sessionId) => request('DELETE', `/session/${sessionId}`),
  getSummary: (sessionId) => request('GET', `/session/${sessionId}/summary`),

  // --- Booking flow ---
  savePreferences: (sessionId, prefs) => request('POST', `/session/${sessionId}/preferences`, prefs),
  confirmBooking: (sessionId, data) => request('POST', `/session/${sessionId}/confirm-booking`, data),
  setInsurance: (sessionId, insurance) => request('POST', `/session/${sessionId}/insurance`, { insurance }),
  checkInsurance: (sessionId, provider, specialty) => request('GET', `/session/${sessionId}/insurance-check?provider=${encodeURIComponent(provider)}&specialty=${encodeURIComponent(specialty)}`),

  // --- Patients ---
  searchPatients: (q) => request('GET', `/patients?q=${encodeURIComponent(q)}`),
  getSessionByPatient: (patientId) => request('GET', `/session/by-patient/${patientId}`),
  createLocalPatient: (data) => request('POST', '/patients/local', data),

  // --- Providers & scheduling ---
  getProviders: (specialty, q) => request('GET', `/providers?specialty=${encodeURIComponent(specialty)}${q ? '&q=' + encodeURIComponent(q) : ''}`),
  getAppointmentInfo: (sessionId, provider, specialty) => request('GET', `/session/${sessionId}/appointment-info?provider=${encodeURIComponent(provider)}&specialty=${encodeURIComponent(specialty)}`),
  getAppointmentSlots: (sessionId, provider, location) => request('GET', `/session/${sessionId}/appointment-slots?provider=${encodeURIComponent(provider)}&location=${encodeURIComponent(location)}`),
  getDistance: (fromAddress, providerAddress) => request('GET', `/distance?from_address=${encodeURIComponent(fromAddress)}&provider_address=${encodeURIComponent(providerAddress)}`),
  getColocatedSuggestions: (sessionId) => request('GET', `/session/${sessionId}/colocated-suggestions`),
  getTransportResources: () => request('GET', '/transport-resources'),

  // --- LLM chat ---
  sendMessage: (sessionId, message, pageContext = '') => request('POST', `/session/${sessionId}/message`, { message, page_context: pageContext }),

  // --- Post-session ---
  sendSummary: (sessionId, method, contact) => request('POST', `/session/${sessionId}/send-summary`, { method, contact }),
  getReminders: (sessionId) => request('GET', `/session/${sessionId}/reminders`),
  logOutcome: (data) => request('POST', '/outcomes', data),
  getPatientOutcomes: (patientId) => request('GET', `/outcomes/patient/${patientId}`),

  // --- Audit & feedback ---
  getAuditLog: (n = 100) => request('GET', `/audit/log?n=${n}`),
  submitErrorFeedback: (data) => request('POST', '/feedback/error', data),
  submitBookingFeedback: (data) => request('POST', '/feedback/booking', data),

  /**
   * Fire-and-forget audit event logger.
   * Errors are swallowed intentionally — a failed audit write must never
   * block or crash the nurse's booking workflow.
   */
  logNurseEvent: (sessionId, action, detail = {}) => {
    // Fire-and-forget — never let audit failures block the UI
    request('POST', '/audit/event', { session_id: sessionId, action, detail }).catch(() => {});
  },
};
