import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from '../lib/api/client.js';

// Mock fetch globally
global.fetch = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  global.fetch.mockResolvedValue({
    ok: true,
    json: async () => ({ session_id: 'test-123' }),
  });
});

describe('api.createSession', () => {
  it('calls POST /api/session', async () => {
    await api.createSession();
    expect(global.fetch).toHaveBeenCalledOnce();
    const [url, opts] = global.fetch.mock.calls[0];
    expect(url).toBe('/api/session');
    expect(opts.method).toBe('POST');
  });
});

describe('api.startSession', () => {
  it('calls POST /api/session/{id}/start/{patientId}', async () => {
    await api.startSession('sess-1', 'pat-42');
    const [url, opts] = global.fetch.mock.calls[0];
    expect(url).toBe('/api/session/sess-1/start/pat-42');
    expect(opts.method).toBe('POST');
  });
});

describe('api.getState', () => {
  it('calls GET /api/session/{id}/state', async () => {
    await api.getState('sess-1');
    const [url, opts] = global.fetch.mock.calls[0];
    expect(url).toBe('/api/session/sess-1/state');
    expect(opts.method).toBe('GET');
  });
});

describe('api.sendMessage', () => {
  it('calls POST with message and page_context fields', async () => {
    await api.sendMessage('sess-1', 'Hello', 'dashboard');
    const [url, opts] = global.fetch.mock.calls[0];
    expect(url).toBe('/api/session/sess-1/message');
    expect(opts.method).toBe('POST');
    const body = JSON.parse(opts.body);
    expect(body).toHaveProperty('message', 'Hello');
    expect(body).toHaveProperty('page_context', 'dashboard');
  });

  it('defaults page_context to empty string when not provided', async () => {
    await api.sendMessage('sess-1', 'Hi');
    const [, opts] = global.fetch.mock.calls[0];
    const body = JSON.parse(opts.body);
    expect(body.page_context).toBe('');
  });
});

describe('api.searchPatients', () => {
  it('calls GET /api/patients?q=encoded-query', async () => {
    await api.searchPatients('John Doe');
    const [url, opts] = global.fetch.mock.calls[0];
    expect(url).toBe('/api/patients?q=John%20Doe');
    expect(opts.method).toBe('GET');
  });
});

describe('api.getProviders', () => {
  it('calls GET /api/providers with specialty param', async () => {
    await api.getProviders('Cardiology');
    const [url, opts] = global.fetch.mock.calls[0];
    expect(url).toBe('/api/providers?specialty=Cardiology');
    expect(opts.method).toBe('GET');
  });

  it('appends optional q param when provided', async () => {
    await api.getProviders('Cardiology', 'Smith');
    const [url] = global.fetch.mock.calls[0];
    expect(url).toBe('/api/providers?specialty=Cardiology&q=Smith');
  });
});

describe('api.deleteSession', () => {
  it('calls DELETE /api/session/{id}', async () => {
    await api.deleteSession('sess-1');
    const [url, opts] = global.fetch.mock.calls[0];
    expect(url).toBe('/api/session/sess-1');
    expect(opts.method).toBe('DELETE');
  });
});

describe('api.getDistance', () => {
  it('calls GET /api/distance with from and provider params', async () => {
    await api.getDistance('123 Main St', '456 Oak Ave');
    const [url, opts] = global.fetch.mock.calls[0];
    expect(url).toBe('/api/distance?from_address=123%20Main%20St&provider_address=456%20Oak%20Ave');
    expect(opts.method).toBe('GET');
  });
});

describe('api.sendSummary', () => {
  it('calls POST /api/session/{id}/send-summary with method and contact', async () => {
    await api.sendSummary('sess-1', 'email', 'patient@example.com');
    const [url, opts] = global.fetch.mock.calls[0];
    expect(url).toBe('/api/session/sess-1/send-summary');
    expect(opts.method).toBe('POST');
    const body = JSON.parse(opts.body);
    expect(body).toHaveProperty('method', 'email');
    expect(body).toHaveProperty('contact', 'patient@example.com');
  });
});

describe('api error handling', () => {
  it('throws an Error when fetch returns ok: false', async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({ detail: 'Session not found' }),
    });
    await expect(api.getState('bad-id')).rejects.toThrow('Session not found');
  });

  it('falls back to HTTP status text when error body has no detail', async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: async () => ({}),
    });
    await expect(api.getState('bad-id')).rejects.toThrow('HTTP 500');
  });

  it('falls back to statusText when response body is not JSON', async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
      json: async () => { throw new SyntaxError('invalid json'); },
    });
    await expect(api.getState('bad-id')).rejects.toThrow('Service Unavailable');
  });
});
