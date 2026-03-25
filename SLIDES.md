# Kouper — Slide Deck Content
> 10 slides. Each slide has a title, key points, and speaker notes.

---

## Slide 1 — Title

**Title:** Kouper: LLM-Assisted Care Coordination

**Subtitle:** A nurse-facing tool that guides post-discharge referral booking end-to-end

**Visual suggestion:** Simple logo/wordmark on a clean background. Tagline below:
> *"The right appointment, for the right patient, booked correctly — every time."*

---

## Slide 2 — The Problem

**Title:** Post-Discharge Booking Is Surprisingly Hard

**Key Points:**
- After hospital discharge, patients often have 1–3 specialist referrals to book
- Nurses must manually navigate: EHR systems, insurance rules, provider directories, and scheduling — simultaneously
- Common failure modes:
  - Wrong appointment type billed (NEW vs. ESTABLISHED) → claim rejection
  - Insurance mismatch not caught until day of appointment
  - Patient preferences not captured → no-shows
  - No audit trail if something goes wrong
- **Result:** Nurses spend 20–40 min per patient on coordination work that should take 10

**Speaker notes:**
The appointment type problem alone (NEW vs. ESTABLISHED) has a strict 5-year rule based on completed visit history — getting it wrong causes a billing rejection. Nurses shouldn't have to remember these rules.

---

## Slide 3 — What Kouper Does

**Title:** A Guided, Audited Booking Wizard with an LLM Co-Pilot

**Key Points — the 7-step workflow:**

1. **Search** — nurse searches patient by name; dashboard shows all active sessions
2. **Verify** — nurse verbally confirms patient identity (name + DOB); checks a box to proceed
3. **Session** — system loads all discharge referrals and appointment history from the EHR
4. **Insurance** — insurance is verified against each provider's accepted plans before provider selection
5. **Provider** — nurse picks from a filtered, specialty-matched provider list
6. **Schedule** — 3-week slot grid auto-generated; appointment type (NEW/ESTABLISHED) pre-determined
7. **Complete** — outcomes logged, reminders scheduled, summary sent to patient

**At every step:** a floating chat panel lets the nurse ask the LLM any question in natural language — it has full context of the current screen and session.

**Visual suggestion:** Horizontal flow diagram with 7 labeled steps

---

## Slide 4 — System Architecture

**Title:** Architecture Overview

**Visual suggestion:** Recreate this diagram:

```
Browser (Nurse)
     │
     ▼
SvelteKit Frontend  (Node, port 3002)
├── File-based routing (one route per wizard step)
├── Svelte stores (session state across pages)
└── hooks.server.js ── reverse proxy ──▶  FastAPI Backend (Python, port 8000)
                                          ├── 18 REST route modules
                                          ├── Business logic layer
                                          ├── LLM client (tool-use loop)
                                          ├── SQLite (.kouper.db)
                                          └── ──▶ Anthropic Claude API
                                              ──▶ Patient EHR API (Flask, port 5001)
```

**Key architectural properties:**
- **No separate reverse proxy** — SvelteKit's `hooks.server.js` strips `/api` and forwards to FastAPI, keeping the backend URL off the browser entirely
- **Two services in production** — `kouper` (frontend, PM2) + `kouper-backend` (uvicorn, PM2); both managed via `ecosystem.config.cjs`
- **Single database file** — `.kouper.db` (SQLite); schema auto-migrated on startup
- **External dependency** — patient EHR data comes from a separate Flask API (`MLChallenge`); URL configured via `PATIENT_API_URL` env var

---

## Slide 5 — Tech Stack

**Title:** Technology Choices

| Layer | Technology | Why |
|---|---|---|
| Frontend | SvelteKit + adapter-node | File-based routing; SSR-capable; adapter produces a deployable Node server |
| Styling | Vanilla CSS (component-scoped) | No framework overhead; scoped by Svelte |
| Backend | FastAPI (Python) | Pydantic-native, auto docs, async-capable |
| LLM | Anthropic Claude Haiku | Fast enough for a tool-use loop (2–5 calls/message); cost-effective |
| Database | SQLite (`sqlite3` stdlib) | Zero setup; single machine; schema lives in code |
| Process mgmt | PM2 | Both frontend and backend managed as named processes |
| Patient data | MLChallenge Flask API | Pre-existing challenge scaffold; wrapped by `patient_client.py` |

**Notable "no" decisions:**
- No ORM (raw `sqlite3`) — schema is simple, migrations are cheap, no abstraction needed
- No LangChain / LlamaIndex — raw Anthropic SDK tool-use loop gives full control and is easier to trace
- No Redis / Postgres — single-machine deployment, SQLite is sufficient

---

## Slide 6 — The LLM Integration

**Title:** How the LLM Co-Pilot Works

**Key Points:**

**The tool-use loop** (`llm/client.py`):
1. Nurse sends a message → appended to conversation history
2. System prompt is rebuilt (includes patient data, session state, provider directory, current page context)
3. Claude is called with the full history + 5 available tools
4. If Claude returns `tool_use`, the tool is executed (deterministic Python), result injected as a `user` turn, loop continues
5. When Claude returns `end_turn` with no tool calls → response returned to nurse

**The 5 tools Claude can call:**
| Tool | What it does |
|---|---|
| `lookup_patient` | Retrieve patient details (usually already in context — acts as a no-op cache) |
| `search_providers` | Filter providers by specialty, insurance, location |
| `check_insurance` | Verify a specific plan against a provider's accepted list |
| `determine_appointment_type` | Compute NEW vs. ESTABLISHED from appointment history (5-year rule) |
| `get_available_slots` | Generate appointment slots for a provider over a 3-week window |

**Design decision:** The LLM never makes booking decisions. It surfaces information and answers questions. All state mutations (booking, session updates) are nurse-initiated via the UI.

**Visual suggestion:** Diagram of the loop: Nurse → Claude → Tool Call → Python → Result → Claude → Response

---

## Slide 7 — Business Logic

**Title:** The Hard Domain Logic (All Deterministic, No LLM)

**Insurance Verification** (`logic/insurance.py`):
- 4-part question: Does the patient *have* this plan? Does this provider *accept* it? Does it need *prior auth*? Is the *specific plan tier* covered?
- Bidirectional partial matching — `"Blue Cross PPO"` matches `"Blue Cross Blue Shield PPO"`
- If rejected: system surfaces self-pay rates automatically

**Appointment Type** (`logic/appointment_type.py`):
- NEW: no completed visit with this specialty in the past 5 years
- ESTABLISHED: completed visit exists within 5 years
- Completed = visit status is `completed` (not cancelled, no-show, or scheduled)
- This determination is passed into slot generation because NEW and ESTABLISHED have different duration slots

**Provider Search** (`logic/provider_search.py`):
- Filters by specialty (exact match)
- Filters by insurance acceptance (calls insurance logic)
- Scores by distance from patient zip code
- Returns ranked list with insurance badge per result

**Co-located Provider Detection** (`logic/colocated_providers.py`):
- When booking a second referral, checks if another provider in the session shares a location
- Surfaces a same-day scheduling suggestion to the nurse (dismissable via sessionStorage)

**Slot Generation** (`logic/slot_generator.py`):
- Generates a deterministic 3-week grid of slots
- Slot durations differ by appointment type (NEW = 60 min, ESTABLISHED = 30 min)
- Excludes times before "today" (configurable `TODAY` constant)

---

## Slide 8 — Frontend Design

**Title:** Frontend: A Multi-Step Wizard with Shared State

**Route structure:**
```
/                          → Dashboard (patient search + session list)
/patient/new               → Create a new local patient
/session/[id]              → Session detail (referral overview, insurance status)
/session/[id]/insurance    → Insurance capture/verify
/session/[id]/referral/[idx]/details      → Referral details
/session/[id]/referral/[idx]/provider     → Provider selection
/session/[id]/referral/[idx]/preferences  → Patient preferences
/session/[id]/referral/[idx]/schedule     → Slot picker
/session/[id]/referral/[idx]/confirm      → Booking confirmation
/session/[id]/complete                    → Outcomes + reminders + summary
/audit                     → Audit log viewer
```

**State management — three layers:**
| Layer | What's stored | Why |
|---|---|---|
| Svelte stores (`session.js`) | sessionId, patient, chatMessages | Needs to survive navigation across all routes |
| `sessionStorage` | Provider data, slot lists, pre-fetched details | Page-scoped; large payloads; cleared on tab close |
| URL params | `?next=` routing, referral index `[idx]` | Shareable/bookmarkable step state |

**ChatPanel** (`lib/components/ChatPanel.svelte`):
- Floating panel present on every booking step
- Dual-timer design: 5s → shows "thinking slowly" warning; 15s → hard abort with user message
- Each LLM response tagged with an `incident_id` for per-message thumbs-up/down feedback
- LLM responses rendered as markdown via `marked`

---

## Slide 9 — Key Design Decisions

**Title:** 9 Decisions Worth Knowing

1. **Raw tool-use loop, not LangChain** — Full visibility into every Claude API call; easier to debug; no hidden abstractions between business logic and LLM
2. **System prompt rebuilt every turn** — Session state changes between messages (new bookings, insurance updates); a stale prompt would give Claude wrong context
3. **LLM informs, UI decides** — Claude never triggers a booking. All writes come from explicit nurse actions. The LLM is advisory only.
4. **Insurance before provider selection** — Surfacing insurance status first prevents the nurse from selecting a provider and then discovering insurance doesn't match
5. **`hooks.server.js` as reverse proxy** — Keeps FastAPI URL off the browser; no nginx required; content-encoding bug fixed here (strips `gzip` header from already-decompressed responses)
6. **Fire-and-forget audit events** — Audit calls from the frontend never block the UI. The audit layer on the backend also silently absorbs failures — it must never break a request.
7. **sessionStorage for slot/provider data** — Slots and provider lists are large and ephemeral. Svelte stores are global and persistent across navigations; sessionStorage is per-tab and cleared on close — the right scope for this data.
8. **SQLite, no Postgres** — Single-machine deployment; schema is simple; zero ops overhead; migrations run on startup via `database.py`
9. **No-show exclusion in appointment type** — A cancelled or no-show visit does not count as "established" for billing purposes. The 5-year rule uses only `status == "completed"` visits.

---

## Slide 10 — Current State & Next Steps

**Title:** Where We Are and Where We're Going

**What's working today:**
- Full end-to-end booking flow (search → verify → schedule → confirm)
- LLM chat assistant with tool-use on every step
- Insurance verification with self-pay fallback
- Appointment type auto-determination (NEW/ESTABLISHED)
- Co-located provider same-day scheduling suggestions
- Outcome logging, reminder capture, patient summary send
- Full audit log with LLM reasoning traces

**Known limitations (honest):**
- Provider directory is static (5 providers in `data/providers.py`) — needs EHR/directory integration
- `TODAY` is a hardcoded constant in slot generator — needs to read system clock for production
- No real reminder dispatch — reminders are captured but not sent
- No FHIR integration — patient data comes from a mock Flask API (MLChallenge scaffold)
- No auth/login — intended for single-nurse demo use; production needs role-based access
- PHI is stored in SQLite plaintext — encryption at rest required before any real patient data

**Immediate next steps:**
- Connect to a real provider directory API
- Plug in a real patient EHR (replace MLChallenge with FHIR R4 client)
- Add nurse authentication (session login + role model)
- Encrypt `.kouper.db` or migrate to Postgres with encryption at rest

---

*Full technical reference: see `ARCHITECTURE.md`*
