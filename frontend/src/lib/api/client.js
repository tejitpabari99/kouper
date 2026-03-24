const BASE_URL = '/api';

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${BASE_URL}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  createSession: () => request('POST', '/session'),
  startSession: (sessionId, patientId) => request('POST', `/session/${sessionId}/start/${patientId}`),
  getState: (sessionId) => request('GET', `/session/${sessionId}/state`),
  sendMessage: (sessionId, message, pageContext = '') => request('POST', `/session/${sessionId}/message`, { message, page_context: pageContext }),
  savePreferences: (sessionId, prefs) => request('POST', `/session/${sessionId}/preferences`, prefs),
  confirmBooking: (sessionId, data) => request('POST', `/session/${sessionId}/confirm-booking`, data),
  getSummary: (sessionId) => request('GET', `/session/${sessionId}/summary`),
  searchPatients: (q) => request('GET', `/patients?q=${encodeURIComponent(q)}`),
  getSessionByPatient: (patientId) => request('GET', `/session/by-patient/${patientId}`),
  getProviders: (specialty, q) => request('GET', `/providers?specialty=${encodeURIComponent(specialty)}${q ? '&q=' + encodeURIComponent(q) : ''}`),
  getAppointmentInfo: (sessionId, provider, specialty) => request('GET', `/session/${sessionId}/appointment-info?provider=${encodeURIComponent(provider)}&specialty=${encodeURIComponent(specialty)}`),
  deleteSession: (sessionId) => request('DELETE', `/session/${sessionId}`),
  getDistance: (fromAddress, providerAddress) => request('GET', `/distance?from_address=${encodeURIComponent(fromAddress)}&provider_address=${encodeURIComponent(providerAddress)}`),
  sendSummary: (sessionId, method, contact) => request('POST', `/session/${sessionId}/send-summary`, { method, contact }),
  getColocatedSuggestions: (sessionId) => request('GET', `/session/${sessionId}/colocated-suggestions`),
  getTransportResources: () => request('GET', '/transport-resources'),
  getReminders: (sessionId) => request('GET', `/session/${sessionId}/reminders`),
  logOutcome: (data) => request('POST', '/outcomes', data),
  getPatientOutcomes: (patientId) => request('GET', `/outcomes/patient/${patientId}`),
  getAuditLog: (n = 100) => request('GET', `/audit/log?n=${n}`),
  submitErrorFeedback: (data) => request('POST', '/feedback/error', data),
  submitBookingFeedback: (data) => request('POST', '/feedback/booking', data),
  setInsurance: (sessionId, insurance) => request('POST', `/session/${sessionId}/insurance`, { insurance }),
  checkInsurance: (sessionId, provider, specialty) => request('GET', `/session/${sessionId}/insurance-check?provider=${encodeURIComponent(provider)}&specialty=${encodeURIComponent(specialty)}`),
  logNurseEvent: (sessionId, action, detail = {}) => {
    // Fire-and-forget — never let audit failures block the UI
    request('POST', '/audit/event', { session_id: sessionId, action, detail }).catch(() => {});
  },
  getAppointmentSlots: (sessionId, provider, location) => request('GET', `/session/${sessionId}/appointment-slots?provider=${encodeURIComponent(provider)}&location=${encodeURIComponent(location)}`),
};
