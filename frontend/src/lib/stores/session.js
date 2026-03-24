import { writable } from 'svelte/store';

export const sessionId = writable(null);
export const patient = writable(null);
export const sessionState = writable(null);
export const currentScreen = writable('patient_lookup');
export const activeReferralIndex = writable(0);
export const chatMessages = writable({}); // keyed by sessionId: { [sessionId]: Message[] }
