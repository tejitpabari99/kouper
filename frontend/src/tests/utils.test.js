import { describe, it, expect, vi } from 'vitest';
import { api } from '../lib/api/client.js';

// Stub fetch so importing the module never makes real requests
global.fetch = vi.fn();

describe('api module shape', () => {
  const requiredMethods = [
    'createSession',
    'startSession',
    'getState',
    'sendMessage',
    'savePreferences',
    'confirmBooking',
    'getSummary',
    'searchPatients',
    'getSessionByPatient',
    'getProviders',
    'getAppointmentInfo',
    'deleteSession',
    'getDistance',
    'sendSummary',
  ];

  it('exports an api object', () => {
    expect(api).toBeDefined();
    expect(typeof api).toBe('object');
  });

  requiredMethods.forEach((method) => {
    it(`api has method: ${method}`, () => {
      expect(typeof api[method]).toBe('function');
    });
  });
});

describe('api URL construction edge cases', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });
  });

  it('encodes special characters in searchPatients query', async () => {
    await api.searchPatients('O\'Brien & Sons');
    const [url] = global.fetch.mock.calls[0];
    expect(url).toContain('/api/patients?q=');
    // The query must not contain a raw ampersand that would break the URL
    const qs = url.split('?q=')[1];
    expect(qs).not.toContain(' ');
  });

  it('encodes specialty with spaces in getProviders', async () => {
    await api.getProviders('Internal Medicine');
    const [url] = global.fetch.mock.calls[0];
    expect(url).toContain('specialty=Internal%20Medicine');
  });

  it('getProviders omits q param when not supplied', async () => {
    await api.getProviders('Oncology');
    const [url] = global.fetch.mock.calls[0];
    expect(url).not.toContain('&q=');
  });

  it('getAppointmentInfo includes provider and specialty query params', async () => {
    await api.getAppointmentInfo('sess-9', 'Dr. Adams', 'Neurology');
    const [url] = global.fetch.mock.calls[0];
    expect(url).toContain('/api/session/sess-9/appointment-info');
    expect(url).toContain('provider=Dr.%20Adams');
    expect(url).toContain('specialty=Neurology');
  });

  it('getSummary calls GET /api/session/{id}/summary', async () => {
    await api.getSummary('sess-7');
    const [url, opts] = global.fetch.mock.calls[0];
    expect(url).toBe('/api/session/sess-7/summary');
    expect(opts.method).toBe('GET');
  });

  it('getSessionByPatient calls GET /api/session/by-patient/{patientId}', async () => {
    await api.getSessionByPatient('pat-5');
    const [url, opts] = global.fetch.mock.calls[0];
    expect(url).toBe('/api/session/by-patient/pat-5');
    expect(opts.method).toBe('GET');
  });

  it('savePreferences calls POST /api/session/{id}/preferences with prefs body', async () => {
    const prefs = { language: 'es', notifications: true };
    await api.savePreferences('sess-3', prefs);
    const [url, opts] = global.fetch.mock.calls[0];
    expect(url).toBe('/api/session/sess-3/preferences');
    expect(opts.method).toBe('POST');
    expect(JSON.parse(opts.body)).toEqual(prefs);
  });

  it('confirmBooking calls POST /api/session/{id}/confirm-booking with data body', async () => {
    const data = { provider_id: 'prov-1', time_slot: '10:00' };
    await api.confirmBooking('sess-4', data);
    const [url, opts] = global.fetch.mock.calls[0];
    expect(url).toBe('/api/session/sess-4/confirm-booking');
    expect(opts.method).toBe('POST');
    expect(JSON.parse(opts.body)).toEqual(data);
  });
});
