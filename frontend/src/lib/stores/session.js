/**
 * Global Svelte stores for shared session state.
 *
 * These stores live at the module level so any component in the tree can
 * read or write them without prop-drilling. They are deliberately kept thin —
 * they hold identifiers and raw API responses, not derived UI state.
 *
 * Lifetime: these stores persist for the duration of the browser tab. They are
 * NOT persisted to localStorage, so a hard refresh resets them. Navigation
 * between session pages re-hydrates from the URL param + API call instead.
 */
import { writable } from 'svelte/store';

// UUID of the active session, set at the dashboard after createSession()
export const sessionId = writable(null);

// Full patient object returned by startSession() / startSessionWithLocalPatient()
export const patient = writable(null);

// Latest snapshot of the backend session state (bookings, preferences, etc.)
export const sessionState = writable(null);

// Tracks which screen the coordinator is on — used by the old single-page flow,
// retained for any components that still reference it
export const currentScreen = writable('patient_lookup');

// Which referral index is currently being worked on in the multi-step booking flow
export const activeReferralIndex = writable(0);

/**
 * Per-session chat history, keyed by sessionId.
 * Shape: { [sessionId: string]: Array<{ role: 'user'|'assistant', text: string, error?: boolean, ... }> }
 *
 * Storing by sessionId means ChatPanel can render the correct thread even if
 * the user navigates across sessions in the same tab.
 */
export const chatMessages = writable({}); // keyed by sessionId: { [sessionId]: Message[] }
