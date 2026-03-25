# Mini Care Coordinator Assistant — Full Project Plan

> **Challenge:** Kouper Health ML Interview — Design & implement an LLM-powered assistant that helps a nurse book appointments and manage patient coordination.

---

## Table of Contents
1. [What We're Building](#what-were-building)
2. [Data Available](#data-available)
3. [Architecture Decision](#architecture-decision)
4. [Nurse Workflow — Screen by Screen](#nurse-workflow--screen-by-screen)
5. [Patient Metadata & Preferences Module](#patient-metadata--preferences-module)
6. [Proactive Edge Case Handling](#proactive-edge-case-handling)
7. [BASIC TIER — All Required Features](#basic-tier--all-required-features)
8. [ADVANCED TIER — Differentiating Features](#advanced-tier--differentiating-features)
9. [Basic Tier — Parallel Build Parts](#basic-tier--parallel-build-parts)
10. [Tech Stack](#tech-stack)
11. [Key Business Logic](#key-business-logic)
12. [Edge Cases Inventory](#edge-cases-inventory)
13. [Presentation Deck Outline](#presentation-deck-outline)

---

## What We're Building

An LLM-powered care coordination assistant for nurses. A nurse opens it after a patient's hospital discharge, and the assistant walks them step-by-step through booking all required referral appointments — while proactively surfacing alternatives, checking insurance, determining appointment types, and capturing patient preferences to maximize actual attendance.

**Primary goal:** Maximum bookings completed per session.
**Secondary goal:** Maximum follow-through (patient actually attends).

---

## Data Available

### Providers (from `data_sheet.txt`)

| Provider | Cert | Specialty | Locations | Hours |
|----------|------|-----------|-----------|-------|
| Grey, Meredith | MD | Primary Care | Sloan Primary Care, Winston-Salem | M-F 9am-5pm |
| House, Gregory | MD | Orthopedics | PPTH Orthopedics, Greensboro | M-W 9am-5pm |
| House, Gregory | MD | Orthopedics | Jefferson Hospital, Claremont | Th-F 9am-5pm |
| Yang, Cristina | MD | Surgery | Seattle Grace Cardiac Surgery, Charlotte | M-F 9am-5pm |
| Perry, Chris | FNP | Primary Care | Sacred Heart, Raleigh | M-W 9am-5pm |
| Brennan, Temperance | PhD, MD | Orthopedics | Jefferson Hospital, Claremont | Tu-Th 10am-4pm |

### Patient API (`GET /patient/{id}`)

Patient 1 — John Doe returns:
- DOB: 01/01/1975
- PCP: Dr. Meredith Grey
- Referred providers: `House, Gregory MD (Orthopedics)` + `[unnamed] (Primary Care)`
- Appointment history:
  - 3/5/2018 — Dr. Grey — **completed** ← over 5 years ago
  - 8/12/2024 — Dr. House — **completed** ← within 5 years
  - 9/17/2024 — Dr. Grey — **no-show**
  - 11/25/2024 — Dr. Grey — **cancelled**

### Accepted Insurances
Medicaid, United Health Care, Blue Cross Blue Shield of NC, Aetna, Cigna

### Self-Pay Rates
Primary Care: $150 | Orthopedics: $300 | Surgery: $1,000

### Appointment Rules
- **NEW** = 30 min | patient arrives **30 min early**
- **ESTABLISHED** = 15 min | patient arrives **10 min early**
- NEW/ESTABLISHED determined by last **completed** visit within 5 years (same specialty)

---

## Architecture Decision

**Chosen: Tool-calling LLM agent with explicit session state**

The LLM handles natural language understanding and generates responses. Every piece of business logic (appointment type, availability, insurance) lives in deterministic Python functions the LLM calls as tools. The LLM is the *least reliable* component — we structure everything around it.

```
Nurse Input
    │
    ▼
FastAPI Backend
    │
    ├── Session State (BookingSession)
    │       step, patient, provider, type, location, preferences
    │
    ├── LLM (Claude / GPT-4o)
    │       System prompt: all data sheet knowledge
    │       Patient context: injected from session
    │       Tools available: 5 structured functions
    │
    └── Tool Layer (deterministic)
            lookup_patient()
            get_providers()
            check_availability()
            determine_appointment_type()
            check_insurance()
            save_patient_preferences()
```

---

## Nurse Workflow — Screen by Screen

The UI is a simple step-by-step wizard. Each screen has a clear purpose, a **Next** button, and proactive information surfaced inline. The chat assistant is always available for questions at any screen.

---

### Screen 1 — Patient Lookup

**Purpose:** Load patient context and confirm identity.

```
┌─────────────────────────────────────────┐
│  PATIENT LOOKUP                         │
│                                         │
│  Patient ID: [_______]  [Load Patient]  │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ ✓ John Doe                      │    │
│  │   DOB: January 1, 1975          │    │
│  │   PCP: Dr. Meredith Grey        │    │
│  │   EHR ID: 1234abcd              │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Please confirm patient identity        │
│  verbally before proceeding.            │
│                              [Next →]   │
└─────────────────────────────────────────┘
```

**Behind the scenes:** Calls `GET /patient/1`, hydrates session, no LLM needed for this step.

---

### Screen 2 — Referrals Overview

**Purpose:** Show all referrals at a glance. Nurse picks which to book first.

```
┌─────────────────────────────────────────┐
│  REFERRALS FOR: John Doe                │
│                                         │
│  Following hospital discharge, the      │
│  following appointments need booking:   │
│                                         │
│  ○ Referral 1                           │
│    Dr. Gregory House — Orthopedics      │
│    Status: NOT BOOKED                   │
│    [Book This →]                        │
│                                         │
│  ○ Referral 2                           │
│    Primary Care (provider TBD)          │
│    Status: NOT BOOKED                   │
│    [Book This →]                        │
│                                         │
│  💬 Ask the assistant anything...       │
└─────────────────────────────────────────┘
```

**Notes:**
- Referral 2 has no named provider — assistant will recommend from available Primary Care providers on the next screen.
- Color-coded status badges (grey = not booked, green = booked, yellow = pending).

---

### Screen 3 — Provider Selection

**Purpose:** Confirm or select the provider. Surface availability and insurance proactively.

```
┌─────────────────────────────────────────┐
│  PROVIDER SELECTION                     │
│  Referral: Orthopedics                  │
│                                         │
│  Referred provider:                     │
│  ┌───────────────────────────────────┐  │
│  │ Dr. Gregory House, MD             │  │
│  │ Orthopedics                       │  │
│  │ ✓ Insurance accepted (if on file) │  │
│  │                                   │  │
│  │ Location A: PPTH Orthopedics      │  │
│  │   Mon-Wed, 9am-5pm                │  │
│  │ Location B: Jefferson Hospital    │  │
│  │   Thu-Fri, 9am-5pm                │  │
│  │                     [Select →]    │  │
│  └───────────────────────────────────┘  │
│                                         │
│  Other Orthopedics providers:           │
│  ┌───────────────────────────────────┐  │
│  │ Dr. Temperance Brennan, PhD, MD   │  │
│  │ Orthopedics                       │  │
│  │ Jefferson Hospital — Tue-Thu      │  │
│  │                     [Select →]    │  │
│  └───────────────────────────────────┘  │
│                                         │
│  💬 "What if House isn't available      │
│      on a certain day?" → ask below     │
└─────────────────────────────────────────┘
```

**Proactive:** Alternatives shown inline — nurse never hits a dead end.

---

### Screen 4 — Appointment Details

**Purpose:** Show appointment type (auto-determined), pick location, surface time guidance.

```
┌─────────────────────────────────────────┐
│  APPOINTMENT DETAILS                    │
│  Provider: Dr. Gregory House            │
│                                         │
│  Appointment Type                       │
│  ┌───────────────────────────────────┐  │
│  │ ✓ ESTABLISHED (15 minutes)        │  │
│  │   Last completed visit: 8/12/2024  │  │
│  │   (within 5 years — established)  │  │
│  └───────────────────────────────────┘  │
│                                         │
│  Select Location                        │
│  ○ PPTH Orthopedics                     │
│    101 Pine St, Greensboro, NC 27401    │
│    Available: Mon, Tue, Wed 9am–5pm     │
│                                         │
│  ○ Jefferson Hospital                   │
│    202 Maple St, Claremont, NC 28610    │
│    Available: Thu, Fri 9am–5pm          │
│                                         │
│  Preferred Day/Time (optional):         │
│  [___________]  Ask assistant for help  │
│                                         │
│                              [Next →]   │
└─────────────────────────────────────────┘
```

**Notes:**
- Appointment type shown with reasoning — nurse understands why, can correct if needed.
- If preferred time unavailable, assistant surfaces alternatives on the same screen.

---

### Screen 5 — Patient Preferences

**Purpose:** Capture contact and logistics preferences before confirming. Feeds into follow-up strategy.

```
┌─────────────────────────────────────────┐
│  PATIENT PREFERENCES                    │
│  These help with booking & follow-ups   │
│                                         │
│  Communication Preference               │
│  ○ Phone call  ○ Text  ○ Email          │
│                                         │
│  Best Contact Time                      │
│  ○ Morning  ○ Afternoon  ○ Evening      │
│                                         │
│  Preferred Location (if choosing        │
│  between options)                       │
│  ○ Closest to home                      │
│  ○ Closest to work                      │
│  ○ No preference                        │
│                                         │
│  Transportation Needs                   │
│  ○ Has own transport                    │
│  ○ Needs ride assistance                │
│                                         │
│  Language Preference                    │
│  [English ▾]                            │
│                                         │
│  Additional Notes                       │
│  [_________________________________]    │
│                                         │
│  [← Back]                   [Next →]   │
└─────────────────────────────────────────┘
```

**Why this matters:**
- Preferred contact method → reminder channel for appointment confirmations
- Transportation flag → proactively offer resources if needed, reduces no-shows
- Language → route to interpreter if needed
- All stored in session, logged for future visits

---

### Screen 6 — Booking Confirmation

**Purpose:** Full summary before committing. Explicit nurse confirmation required.

```
┌─────────────────────────────────────────┐
│  BOOKING SUMMARY                        │
│  Please review before confirming        │
│                                         │
│  Patient:    John Doe (DOB: 01/01/1975) │
│  Provider:   Dr. Gregory House, MD      │
│  Specialty:  Orthopedics                │
│  Type:       ESTABLISHED (15 min)       │
│  Location:   PPTH Orthopedics           │
│              101 Pine St, Greensboro    │
│              (445) 555-6205             │
│  Hours:      Mon–Wed 9am–5pm            │
│                                         │
│  ⏰ Arrival: Patient should arrive      │
│     10 minutes before appointment       │
│                                         │
│  Follow-up Contact: Text message        │
│  Contact Time: Afternoon                │
│                                         │
│  [← Edit]        [✓ Confirm Booking]   │
└─────────────────────────────────────────┘
```

After confirmation → return to Screen 2 (Referrals Overview) to book the next referral.

---

### Screen 7 — Session Complete

**Purpose:** Show all bookings made in this session. Export summary.

```
┌─────────────────────────────────────────┐
│  SESSION COMPLETE                       │
│  John Doe — 2 referrals processed       │
│                                         │
│  ✓ Orthopedics — Dr. House             │
│    PPTH Orthopedics — ESTABLISHED       │
│                                         │
│  ✓ Primary Care — Dr. Meredith Grey    │
│    Sloan Primary Care — NEW             │
│                                         │
│  Follow-up reminders scheduled via:    │
│  Text message (afternoon)               │
│                                         │
│  [Print Summary]  [Start New Session]  │
└─────────────────────────────────────────┘
```

---

## Patient Metadata & Preferences Module

All preferences captured on Screen 5 are stored as a **patient profile** that persists across sessions.

### Data Schema

```python
class PatientPreferences:
    patient_id: str

    # Communication
    contact_method: Literal["phone", "text", "email"]
    best_contact_time: Literal["morning", "afternoon", "evening"]
    language: str  # default "English"

    # Logistics
    location_preference: Literal["home", "work", "none"]
    transportation_needs: bool

    # Notes
    notes: str

    # Tracking
    created_at: datetime
    updated_at: datetime
    last_nurse_id: Optional[str]
```

### How Preferences Drive Bookings

| Preference | How It Helps |
|------------|-------------|
| Contact method | Reminder sent via preferred channel after booking |
| Best contact time | Schedule automated reminder calls/texts at right time |
| Location preference | Auto-rank location options by proximity |
| Transportation needs | Flag for care coordinator to arrange transport, reducing no-shows |
| Language | Route interpreter service if non-English |
| Notes | Carry context (e.g., "patient anxious about Orthopedics visit") |

### Follow-Up Touch Points (maximizing attendance)
1. **Booking confirmation** — immediate, via preferred channel
2. **48-hour reminder** — "Your appointment with Dr. House is in 2 days"
3. **Day-of reminder** — "Reminder: arrive 10 minutes early today at PPTH Orthopedics"
4. **Post-appointment check-in** — 24 hours after, confirm attendance, capture status for history

---

## Proactive Edge Case Handling

The assistant never lets a nurse hit a dead end. Every potential failure has a pre-surfaced alternative.

### Rule: Surface Alternatives Before Being Asked

| Situation | What the assistant does proactively |
|-----------|-------------------------------------|
| Provider has 2 locations | Shows both upfront with hours — nurse picks, no confusion |
| Preferred time outside office hours | "Dr. House is available Mon–Wed. Here are open days this week: [Mon 2pm, Tue 10am]" |
| Provider unavailable on preferred day | Immediately shows: (1) other days for same provider, (2) other providers same specialty |
| Insurance not accepted | Shows self-pay cost inline on provider card, not as an error after selection |
| Referral has no named provider | "No provider specified — here are available Primary Care providers:" + list with availability |
| No-show/cancelled in history | Surfaces note: "Note: previous no-show on 9/17/24. Consider confirming transportation." |
| Appointment type uncertain | Explains reasoning transparently with dates, allows nurse to override |

### Alternative Provider Logic (on unavailability)

```
Is requested provider unavailable?
    │
    ├── YES
    │    ├─ Step 1: Show other locations of same provider (if multiple)
    │    ├─ Step 2: Show other providers with same specialty
    │    └─ Step 3: If none match insurance → show self-pay options
    │
    └── NO → Proceed to location/time selection
```

### Insurance Check Flow

```
Nurse selects provider →
    System checks insurance (from patient record or nurse input) →
        ├── Accepted → ✓ shown on provider card, proceed
        └── Not accepted →
                Show: "This insurance is not accepted."
                Show: "Self-pay for [Specialty]: $[rate]"
                Show: "Would you like to check a different provider or proceed self-pay?"
```

---

## BASIC TIER — All Required Features

Everything here must be built and working for a passing submission.

### B1 — Patient API Integration
- Run provided Flask app at `localhost:5000`
- `GET /patient/1` called on session start
- Parse: name, DOB, PCP, referred_providers, appointments
- Handle: patient not found (404), API down (500)

### B2 — LLM Integration with System Prompt
- Connect to Claude or GPT-4o via API
- System prompt contains full data sheet (all providers, hours, insurance, rules)
- Patient context injected into each turn from session state
- Multi-turn conversation history maintained within a session

### B3 — Five Core Tools (LLM callable)

```python
def lookup_patient(patient_id: str) -> PatientData
def get_providers(specialty: str) -> List[Provider]
def check_availability(provider_name: str, day: str) -> AvailabilityResult
def determine_appointment_type(patient_id: str, provider_name: str) -> AppointmentTypeResult
def check_insurance(insurance_name: str) -> InsuranceResult
```

Each tool returns structured Pydantic objects, not raw strings.

### B4 — Appointment Type Logic
- Compare today vs. last **completed** appointment with same specialty
- 5-year window (NOT counting no-shows or cancellations)
- Return: type, duration, arrival guidance, reasoning string for display

### B5 — Provider Availability Checking
- Parse office hours strings into structured day sets
- Handle multi-location providers (House: M-W at PPTH, Th-F at Jefferson)
- Return available days, hours, location, phone

### B6 — Insurance Verification
- Check against accepted insurance list
- Return: accepted (bool), self-pay rate for specialty if not accepted

### B7 — Session State Machine

```python
class BookingSession:
    session_id: str
    step: str  # patient_lookup | referrals_overview | provider_selection |
               # appointment_details | preferences | confirmation | complete
    patient: Optional[PatientData]
    active_referral_index: int
    bookings: List[CompletedBooking]

    # Current booking in progress
    selected_provider: Optional[Provider]
    appointment_type: Optional[str]
    selected_location: Optional[Department]

    # Preferences
    patient_preferences: Optional[PatientPreferences]
```

### B8 — Step-by-Step UI (7 Screens)
- Screens as described in Nurse Workflow section above
- Each screen has Next/Back navigation
- Chat assistant embedded on every screen
- Booking state persists across screens (never re-ask confirmed info)

### B9 — Unnamed Referral Provider Recommendation
- Detect referral with no provider name (`provider` field absent)
- Query `get_providers(specialty="Primary Care")`
- Display available providers with hours for nurse to select

### B10 — Multi-Location Provider Handling
- When provider has >1 department, present location choice on Screen 3
- Show each location's hours and address
- Availability check is per-location

### B11 — Booking Confirmation Card (Screen 6)
- Full summary before any "write" action
- Explicit confirm button required
- Arrival time always included

### B12 — Patient Preferences Capture (Screen 5)
- Contact method, best time, language, transportation, location preference, notes
- Stored in session, included in session complete summary

### B13 — Session Complete Summary (Screen 7)
- All bookings in this session listed with details
- Follow-up plan noted
- Print/export summary

---

## ADVANCED TIER — Differentiating Features

Build these after Basic is complete.

### A1 — Structured Audit Log
Every tool call logged: `{timestamp, session_id, tool, input, output, reasoning}`. In deck: mention PHI de-identification for production.

### A2 — Follow-Up Reminder Scheduling
After booking confirmed: schedule 3 reminder touch points (booking confirm, 48hr, day-of) via preferred channel. Can be mocked for demo — the architecture matters.

### A3 — Post-Appointment Status Tracking
After appointment date passes: log as `completed`, `no-show`, or `cancelled`. Feeds back into NEW/ESTABLISHED calculation for future bookings. Closes the loop.

### A4 — Graceful API Error Recovery
Structured error codes returned to LLM. LLM narrates gracefully. No raw stack traces in UI.

### A5 — Transportation Resources Flag
If patient has transportation needs, surface community transport resources or flag for care coordinator follow-up.

### A6 — Cross-Referral Scheduling Optimization
If patient has multiple referrals, suggest booking same-day at co-located providers to minimize trips. (House and Brennan are both at Jefferson Hospital.)

### A7 — Nurse Session Notes
Free-text field for nurse to add notes per booking (e.g., "Patient concerned about cost, discussed self-pay"). Stored with booking record.

---

## Basic Tier — Parallel Build Parts

The Basic Tier is broken into **5 independent workstreams** designed for parallel development in separate git worktrees. Each part has a clear interface contract so they can be developed independently and wired together.

---

### Part 1 — Data Layer & Business Logic
**Branch:** `feature/data-layer`

Everything that touches the raw data — no LLM, no HTTP server.

**Files:**
```
app/
  models/
    patient.py        # PatientData, Appointment, ReferredProvider
    provider.py       # Provider, Department
    session.py        # BookingSession, PatientPreferences, CompletedBooking
    appointment.py    # AppointmentTypeResult, AvailabilityResult, InsuranceResult
  data/
    providers.py      # Parsed provider directory (from data_sheet.txt)
    insurance.py      # Accepted insurances list + self-pay rates
  logic/
    appointment_type.py   # determine_appointment_type()
    availability.py       # check_availability(), parse_hours()
    insurance.py          # check_insurance()
    provider_search.py    # get_providers(specialty)
```

**Deliverable:** All business logic functions working with unit tests. No external dependencies.

**Tests to write:**
- `test_appointment_type_new()` — Grey, last completed > 5 years
- `test_appointment_type_established()` — House, last completed < 5 years
- `test_noshows_dont_count()` — Grey has no-show, should still be NEW
- `test_availability_house_monday()` — should return PPTH location
- `test_availability_house_thursday()` — should return Jefferson
- `test_insurance_accepted()` — Aetna → True
- `test_insurance_rejected()` — Anthem → False + self-pay rate

---

### Part 2 — Patient API Client
**Branch:** `feature/patient-api`

HTTP client for the provided Flask API. Runs the Flask app as a subprocess or assumes it's running.

**Files:**
```
app/
  api/
    patient_client.py     # get_patient(patient_id) → PatientData
    exceptions.py         # PatientNotFound, APIUnavailable
```

**Deliverable:** `get_patient(1)` returns John Doe's full PatientData object. Handles 404 and 500 gracefully.

**Tests to write:**
- `test_get_patient_success()`
- `test_get_patient_not_found()` → raises `PatientNotFound`
- `test_api_unavailable()` → raises `APIUnavailable`

---

### Part 3 — LLM Tool Layer
**Branch:** `feature/llm-tools`

LLM client setup + all 5 tool definitions. Depends on Part 1 interfaces (use mock data if Part 1 not merged yet).

**Files:**
```
app/
  llm/
    client.py         # LLM client (Claude or OpenAI), tool call execution loop
    tools.py          # 5 tool schemas + dispatcher
    prompts.py        # System prompt template, patient context injector
    tool_executor.py  # Maps LLM tool calls → Part 1 logic functions
```

**Tool schemas (each has name, description, parameters — description written for the LLM):**
1. `lookup_patient` — "Use this to load a patient's record by ID at the start of a session"
2. `get_providers` — "Use this to find available providers for a given specialty"
3. `check_availability` — "Use this to check if a provider is available on a given day or time"
4. `determine_appointment_type` — "Use this to determine if a patient needs a NEW or ESTABLISHED appointment with a specific provider"
5. `check_insurance` — "Use this to verify whether a patient's insurance is accepted, and retrieve self-pay costs if not"

**Deliverable:** Given a mock patient + a natural-language nurse question, the LLM calls the right tool and returns a structured response.

**Tests to write:**
- `test_insurance_question_triggers_check_insurance_tool()`
- `test_availability_question_triggers_check_availability_tool()`
- `test_appointment_type_auto_determined_on_provider_select()`

---

### Part 4 — FastAPI Server & Session Management
**Branch:** `feature/api-server`

HTTP server, session state, and all endpoints. Wires together Parts 1, 2, 3.

**Files:**
```
app/
  server.py             # FastAPI app entry point
  session_store.py      # In-memory SessionStore (dict keyed by UUID)
  routes/
    session.py          # POST /session, GET /session/{id}
    chat.py             # POST /session/{id}/message
    patient.py          # GET /session/{id}/patient
    preferences.py      # POST /session/{id}/preferences
    booking.py          # POST /session/{id}/confirm-booking
```

**Endpoints:**
```
POST /session                           → create session, return session_id
POST /session/{id}/start/{patient_id}  → load patient, return PatientData
POST /session/{id}/message             → send message, return LLM response + session state
GET  /session/{id}/state               → return current BookingSession
POST /session/{id}/preferences         → save PatientPreferences
POST /session/{id}/confirm-booking     → finalize booking, return CompletedBooking
GET  /session/{id}/summary             → return all bookings in session
```

**Deliverable:** Full API running at `localhost:8000`. Postman/curl testable end-to-end.

---

### Part 5 — Frontend UI (7 Screens)
**Branch:** `feature/frontend`

Basic UI. Clean and functional — not polished. Can use plain HTML + JS or minimal React.

**Files:**
```
frontend/
  index.html          # or App.jsx
  screens/
    PatientLookup.jsx       # Screen 1
    ReferralsOverview.jsx   # Screen 2
    ProviderSelection.jsx   # Screen 3
    AppointmentDetails.jsx  # Screen 4
    PatientPreferences.jsx  # Screen 5
    BookingConfirmation.jsx # Screen 6
    SessionComplete.jsx     # Screen 7
  components/
    ChatPanel.jsx           # Chat assistant (embedded on all screens)
    ProviderCard.jsx        # Provider display with availability
    BookingSummaryCard.jsx  # Confirmation summary
  api/
    client.js               # Calls to FastAPI backend
```

**Deliverable:** Full 7-screen flow working against the FastAPI server. No-show history note displayed. Alternatives shown inline on Screen 3.

---

### Integration Order

```
Part 1 (Data Layer)
    ↓
Part 2 (API Client)  ←── (parallel with Part 3)
Part 3 (LLM Tools)   ←── (parallel with Part 2)
    ↓
Part 4 (FastAPI Server) ← wires 1 + 2 + 3
    ↓
Part 5 (Frontend) ← calls Part 4
```

Parts 2 and 3 can be built simultaneously. Parts 1 must be done first (or mocked). Part 4 integrates everything. Part 5 is frontend-only once Part 4's API contracts are defined.

---

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| LLM | Claude claude-sonnet-4-6 (Anthropic) | Tool calling, reliable structured output |
| Backend | FastAPI (Python) | Async, Pydantic-native, auto-docs |
| Data validation | Pydantic v2 | All models typed and validated |
| LLM orchestration | Raw tool-calling loop (no LangChain) | Readable, reviewable, easy to present |
| Patient API | Provided Flask app (run as-is) | Use what's given |
| State | In-memory dict + session UUID | Sufficient for demo; abstract as SessionStore |
| Frontend | Plain React + fetch or plain HTML | Basic but functional |
| Tests | pytest | Standard Python testing |

---

## Key Business Logic

### Appointment Type Determination

```python
def determine_appointment_type(patient_id, provider_name, specialty):
    history = get_patient_appointments(patient_id)

    # Only completed appointments count (not no-shows, cancellations)
    completed = [a for a in history if a.status == "completed"]

    # Check same specialty within 5-year window
    cutoff = date.today() - timedelta(days=5 * 365)
    recent = [a for a in completed
              if a.specialty == specialty and a.date >= cutoff]

    if recent:
        return AppointmentTypeResult(
            type="ESTABLISHED",
            duration_minutes=15,
            arrival_minutes_early=10,
            reason=f"Last completed visit: {max(a.date for a in recent)}"
        )
    else:
        last_completed = max((a.date for a in completed), default=None)
        return AppointmentTypeResult(
            type="NEW",
            duration_minutes=30,
            arrival_minutes_early=30,
            reason=f"Last completed visit in specialty: {last_completed or 'none on record'}"
        )
```

### John Doe's Appointment Types (Pre-calculated)

| Referral | Provider | Last Completed | Type | Duration |
|---------|---------|---------------|------|---------|
| Orthopedics | Dr. House | 8/12/2024 | **ESTABLISHED** | 15 min, arrive 10 min early |
| Primary Care | Dr. Grey or Perry | 3/5/2018 (Grey) | **NEW** | 30 min, arrive 30 min early |

> Note: Grey's 9/17/24 no-show and 11/25/24 cancellation do NOT count. Only the 3/5/18 completed visit counts, which is >5 years, making it NEW.

---

## Edge Cases Inventory

| Edge Case | Data Evidence | How Handled |
|-----------|--------------|-------------|
| Provider at 2 locations | House: PPTH + Jefferson | Show both upfront, nurse picks location first |
| Referral with no provider | `referred_providers[1]` has no name | Auto-query by specialty, show options |
| No-shows don't count for type | Grey 9/17/24 no-show | Filter to `status == "completed"` only |
| Last completed > 5 years = NEW | Grey 3/5/18 | NEW even though she's the PCP |
| Insurance not accepted | Nurse asks about unlisted insurance | Return self-pay rate + alternative prompt |
| Patient not found | `GET /patient/99` | `PatientNotFound` exception → friendly error |
| API down | Flask not running | `APIUnavailable` → graceful UI message |
| Mid-flow provider change | Nurse says "actually different provider" | Reset provider/type/location, keep patient confirmed |
| Concurrent sessions | Two nurses, same patient | Session IDs are independent; booking lock on confirm |
| Unknown insurance queried | "Does it accept Anthem?" | "Anthem is not in accepted list. Self-pay for [specialty] is $X." |

---

## Presentation Deck Outline

| Slide | Content |
|-------|---------|
| 1 | Problem statement — what a care coordinator does today vs. with this tool |
| 2 | Architecture diagram — nurse → UI → LLM → tool layer → deterministic logic |
| 3 | Session state machine — 7-step booking flow as a state diagram |
| 4 | Tool schema example — one tool with parameter descriptions written for the LLM |
| 5 | NEW vs ESTABLISHED decision tree — 5-year rule, completed-only, John Doe examples |
| 6 | Edge cases table — 6 cases + handling strategy |
| 7 | Patient preferences module — how it maximizes bookings + reduces no-shows |
| 8 | What's next — EHR/FHIR integration, real slot availability, multi-patient, PHI/HIPAA |

**Slide 8 talking points:**
- In production: de-identify PHI before sending to third-party LLM, or use HIPAA BAA-covered endpoint
- Real scheduling: integrate with EHR calendar (Epic, Cerner via FHIR R4 `Slot` resource)
- No-show reduction: automated reminder pipeline connected to patient preferences
- Multi-patient: same architecture scales — session per nurse session, not per patient

---

*Last updated: 2026-03-24*
