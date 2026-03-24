# Feature Plan v2 — Kouper Health Care Coordinator
**Date:** 2026-03-24
**Status:** Planning
**Scope:** Comprehensive audit logging · Appointment scheduling · Insurance · Supporting features

---

## Table of Contents
1. [Current State Snapshot](#1-current-state-snapshot)
2. [F1 — Comprehensive Audit Logging](#f1--comprehensive-audit-logging)
3. [F2 — Appointment Date/Time Selection](#f2--appointment-datetime-selection)
4. [F3 — Insurance Integration](#f3--insurance-integration)
5. [F4 — Provider Capacity & New Patient Acceptance](#f4--provider-capacity--new-patient-acceptance)
6. [F5 — Referral Urgency & Priority](#f5--referral-urgency--priority)
7. [F6 — Prior Authorization Flag](#f6--prior-authorization-flag)
8. [Implementation Order & Dependencies](#implementation-order--dependencies)
9. [Updated Session Flow (9 screens)](#updated-session-flow-9-screens)
10. [Data Changes Required](#data-changes-required)

---

## 1. Current State Snapshot

### What exists
| Layer | Status |
|---|---|
| Session flow | 7 screens: Lookup → Referrals → Provider → Details → Preferences → Confirm → Complete |
| Audit log | LLM tool calls only, no type tag, not shown in UI (broken — no LLM calls in test data) |
| Insurance | LLM tool only (`check_insurance`), global accept list, no per-provider or per-patient data |
| Appointment date | `scheduled_date` field in `CompletedBooking` exists but is never populated |
| Reminders | All say "pending_date" because no actual appointment date is ever set |
| Patient data | No insurance field, no address, no urgency on referrals |
| Provider data | No `accepted_insurances`, no `accepting_new_patients` flag |

### Why audit log shows nothing
The audit log only writes when the LLM executes a tool call. In most test flows the chat panel is never opened, so `.audit_log.jsonl` stays empty. The `/audit` page correctly renders an empty state, but users interpret this as broken.

**Fix**: Audit every API request (FastAPI middleware) and every significant nurse action (frontend event posts). LLM calls become one of several event types.

---

## F1 — Comprehensive Audit Logging

**Goal**: Every interaction recorded — nurse navigation, form submits, API calls, LLM decisions, system events — with a `type` tag so events can be filtered by source.

### Event Types

| Type | Produced by | Examples |
|---|---|---|
| `api` | FastAPI middleware | Every HTTP request: method, path, status, duration_ms |
| `system` | Backend route handlers | Session created, patient loaded, booking confirmed, session deleted |
| `llm` | LLM client loop (existing) | Tool call, reasoning hint, error code |
| `tool` | Tool executor functions | Function called, input, output, timing |
| `nurse` | Frontend POST to `/audit/event` | Step visited, provider selected, preference set, feedback submitted |

### Data Model Extension

```python
class AuditLogEntry(BaseModel):
    timestamp: str           # ISO-8601 UTC
    type: Literal["api", "system", "llm", "tool", "nurse"]  # NEW
    session_id: Optional[str] = None
    tool_name: Optional[str] = None       # llm/tool events
    tool_input: Optional[dict] = None
    tool_output: Optional[str] = None
    reasoning_hint: Optional[str] = None  # llm only
    error: bool = False
    error_code: Optional[str] = None
    # NEW fields:
    actor: Optional[str] = None           # "nurse", "llm", "system", "api"
    action: Optional[str] = None          # human-readable: "confirmed_booking", "selected_provider"
    detail: Optional[dict] = None         # free-form context
    http_method: Optional[str] = None     # api events
    http_path: Optional[str] = None       # api events
    http_status: Optional[int] = None     # api events
    duration_ms: Optional[int] = None     # api/tool events
```

### Backend Changes

**1. Extend `audit_log.py`**
- Update `AuditLogEntry` model with new fields
- `append_audit_entry()` unchanged — already handles the extended model
- Add `get_entries_by_type(type, n)` helper

**2. FastAPI middleware in `server.py`**
```python
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    append_audit_entry(AuditLogEntry(
        timestamp=..., type="api",
        http_method=request.method,
        http_path=str(request.url.path),
        http_status=response.status_code,
        duration_ms=int((time.time() - start) * 1000),
        session_id=extract_session_id(request.url.path),
    ))
    return response
```
Extract session ID from paths like `/session/{uuid}/...` via regex.

**3. System events in route handlers**
Add `append_audit_entry()` calls with `type="system"` at:
- `POST /session` → `action="session_created"`
- `POST /session/{id}/start/{patient_id}` → `action="patient_loaded"`, `detail={patient_name, patient_id}`
- `POST /session/{id}/confirm-booking` → `action="booking_confirmed"`, `detail={provider, specialty, type}`
- `DELETE /session/{id}` → `action="session_deleted"`
- `POST /session/{id}/preferences` → `action="preferences_saved"`

**4. New endpoint: `POST /audit/event`**
```python
class NurseEventRequest(BaseModel):
    session_id: Optional[str] = None
    action: str        # e.g. "step_visited", "provider_selected", "date_selected"
    detail: dict = {}  # page_name, provider_name, etc.

@router.post("/event")
def log_nurse_event(body: NurseEventRequest):
    append_audit_entry(AuditLogEntry(
        timestamp=..., type="nurse",
        session_id=body.session_id,
        action=body.action,
        detail=body.detail,
        actor="nurse",
    ))
    return {"logged": True}
```

**5. Tool-level timing in `tool_executor.py`**
Wrap each tool call with `type="tool"` entry including `duration_ms`.

### Frontend Changes

**Add `api.logNurseEvent(sessionId, action, detail)` to `client.js`**
Fire-and-forget (never blocks UI).

**Add `useAudit(sessionId)` thin helper used across pages:**
```js
// Called on onMount of each page
audit('step_visited', { step: 'provider_selection', referral_index: idx });
// Called on key actions
audit('provider_selected', { provider: name, specialty });
audit('booking_confirmed', { provider, location, appointment_type });
```

**Update `/audit` page**
- Add type filter tabs: All | API | System | LLM | Tool | Nurse
- Color-code by type:
  - `api` → grey
  - `system` → blue
  - `llm` → indigo (existing)
  - `tool` → purple
  - `nurse` → green
- Show `action` field prominently when present
- Show `duration_ms` on api/tool events

---

## F2 — Appointment Date/Time Selection

**Goal**: Nurse selects a specific appointment date and time from the provider's real availability. This populates `CompletedBooking.scheduled_date`, enabling reminder scheduling with actual dates instead of "pending_date".

### New Screen: Step 5 — Schedule Appointment

Inserted between **Appointment Details (Step 4)** and **Patient Preferences (Step 5, now Step 6)**.

Route: `/session/[id]/referral/[idx]/schedule?provider=...&location=...&specialty=...`

### Slot Generation Logic

**`backend/app/logic/slot_generator.py`** (new)

```python
def generate_slots(
    provider_name: str,
    location_name: str,
    appointment_type: str,        # NEW=30min, ESTABLISHED=15min
    weeks_ahead: int = 3,
) -> List[AppointmentSlot]:
    """
    Generate available slots for the next `weeks_ahead` weeks.
    - Parse provider's hours string for the selected location
    - Walk each day in [today+1 .. today+weeks_ahead*7]
    - If that weekday is in the provider's schedule, generate 30-min slots within hours
    - Slot duration matches appointment_type (NEW=30, ESTABLISHED=15)
    - Skip today (assume same-day is not bookable)
    - Return sorted list
    """
```

```python
class AppointmentSlot(BaseModel):
    date: str           # "2026-04-02"
    day_name: str       # "Thursday"
    start_time: str     # "09:00"
    end_time: str       # "09:30"
    display: str        # "Thu Apr 2 · 9:00 AM – 9:30 AM"
```

**Hour string parsing**: `"9am-5pm"` → start=9, end=17. Generate slots every 30 or 15 minutes. Last slot starts at `end - slot_duration`.

**`GET /session/{id}/appointment-slots?provider=...&location=...`**

Returns grouped slots:
```json
{
  "provider": "Dr. Gregory House",
  "location": "PPTH Orthopedics",
  "appointment_type": "ESTABLISHED",
  "duration_minutes": 15,
  "slots_by_week": [
    {
      "week_label": "This week (Mar 25–31)",
      "slots": [
        {"date": "2026-03-25", "day_name": "Wednesday", "start_time": "09:00", ...},
        ...
      ]
    }
  ]
}
```

### Frontend

**`/session/[id]/referral/[idx]/schedule/+page.svelte`**

- Grouped by week (accordion-style)
- Each day shows available time slots as pill buttons
- Selected slot highlighted; confirm button enabled
- On confirm → navigate to preferences with `slot` param in URL, or store in sessionStorage

### Booking Integration

**`ConfirmBookingRequest`**: Add `scheduled_datetime: Optional[str] = None` (ISO string)
**`CompletedBooking.scheduled_date`**: Already exists — populate it with the selected slot
**Reminders**: In `schedule_reminders()`, if `scheduled_date` is set:
- `48hr_reminder.scheduled_for` = ISO date 2 days before
- `day_of_reminder.scheduled_for` = the actual appointment date
- Replace "pending_date" with real dates

### Navigation Update

Old: `details` → `preferences` → `confirm`
New: `details` → **`schedule`** → `preferences` → `confirm`

Step labels update: Appointment Details (4) · **Schedule (5)** · Preferences (6) · Confirm (7) · Complete (8... but this is the existing "Session Complete" so stays as Step 7 on the overview)

---

## F3 — Insurance Integration

**Goal**: Patient's insurance is known upfront, checked against each provider's accepted list at provider selection, flagged in appointment details, and handled gracefully if not covered (self-pay rates, patient script, alternatives).

### Data Layer

**Patient insurance** — add to Flask patient data (`data-changes.md`):
```json
{ "insurance": "Blue Cross Blue Shield of North Carolina" }
```

Patients:
- John Doe → Blue Cross Blue Shield of North Carolina
- (add to patient 2, 3... as needed)

**Provider accepted insurances** — add to `Provider` model:
```python
class Provider(BaseModel):
    ...
    accepted_insurances: List[str] = []
    accepting_new_patients: bool = True
```

Provider insurance data (invented, logged in `data-changes.md`):

| Provider | Accepted |
|---|---|
| Dr. Meredith Grey | Medicaid, United Health Care, Blue Cross Blue Shield NC, Aetna, Cigna |
| Dr. Gregory House | Blue Cross Blue Shield NC, Aetna, United Health Care |
| Dr. Cristina Yang | Medicaid, Aetna, Cigna |
| Dr. Chris Perry | Medicaid, United Health Care, Blue Cross Blue Shield NC |
| Dr. Temperance Brennan | Aetna, Cigna, United Health Care |

**PatientData model** — add `insurance: Optional[str] = None`

### Logic Layer

**Update `check_insurance()`** to be provider-aware:
```python
def check_insurance(
    insurance_name: str,
    specialty: str,
    provider_name: Optional[str] = None,
) -> InsuranceResult:
```
If `provider_name` given, check against that provider's `accepted_insurances`. Fall back to global list if provider not found.

**New `get_alternative_providers(insurance, specialty)`** — returns providers in same specialty who accept the insurance. For use in "not covered" UI.

**New `GET /session/{id}/insurance-check?provider=...&specialty=...`**:
```json
{
  "patient_insurance": "Humana",
  "provider": "Dr. Gregory House",
  "accepted": false,
  "self_pay_rate": 300.0,
  "specialty": "Orthopedics",
  "alternatives": [
    {
      "name": "Dr. Temperance Brennan",
      "specialty": "Orthopedics",
      "accepts_insurance": true,
      "location": "Jefferson Hospital"
    }
  ],
  "patient_script": "Your insurance (Humana) is not in-network with Dr. House. Your estimated self-pay rate is $300 per visit. Alternatively, Dr. Temperance Brennan at Jefferson Hospital accepts your plan."
}
```

### UI Layer

**Step 3 (Provider Selection)**
- Add insurance badge per provider card:
  - `✓ Covered` (green) — patient's insurance accepted
  - `⚠ Verify` (yellow) — patient insurance unknown
  - `✗ Out of Network` (red) — insurance not accepted
- Patient's insurance shown at top of screen: "Patient insurance: Blue Cross Blue Shield NC"

**Step 4 (Appointment Details)**
- Insurance status card (auto-loaded, not LLM-triggered):
  - If covered: green "✓ Blue Cross Blue Shield NC accepted"
  - If not covered: red card with self-pay rate, patient script, alternative providers list
  - "Switch Provider" link back to Step 3 if not covered and alternatives exist

**Step 6 → Confirm**
- If insurance not covered: yellow warning in booking summary: "Insurance not confirmed — patient informed of $300 self-pay rate"
- Nurse checkbox: "Patient acknowledged self-pay rate" (required to confirm if not covered)

### Patient Script (not-covered case)

> "I want to let you know that [INSURANCE] is not currently accepted at [PROVIDER]'s practice. Your estimated out-of-pocket cost would be $[RATE] per visit. Would you like me to see if there's a covered provider available?"

Script auto-generated on backend, returned with insurance-check response.

---

## F4 — Provider Capacity & New Patient Acceptance

**Goal**: Surface when a provider is not accepting new patients so the nurse knows immediately at provider selection.

### Data
Add to `Provider`:
```python
accepting_new_patients: bool = True
waitlist_available: bool = False
```

Invented data (logged in `data-changes.md`):
- Dr. Gregory House: `accepting_new_patients=True`
- Dr. Meredith Grey: `accepting_new_patients=True`
- Dr. Cristina Yang: `accepting_new_patients=False, waitlist_available=True`
- Dr. Chris Perry: `accepting_new_patients=True`
- Dr. Temperance Brennan: `accepting_new_patients=True`

### UI
**Step 3 (Provider Selection)**: Badge "Not accepting new patients" in orange. Disabled if NEW appointment type. If `waitlist_available`, show "Waitlist available" with contact info.

Note: This interacts with F3 — if the preferred provider isn't accepting, show covered alternatives.

---

## F5 — Referral Urgency & Priority

**Goal**: Flag urgent referrals so nurses prioritize them.

### Data
Add to `ReferredProvider`:
```python
urgency: Literal["routine", "urgent", "stat"] = "routine"
priority_note: Optional[str] = None
```

Invented: John Doe's orthopedic referral → `urgency="urgent"` (post-discharge follow-up within 2 weeks)

### UI
**Step 2 (Referrals Overview)**: Orange "URGENT" badge on referral cards. Sort urgent first.

**Step 7 (Complete)**: Urgent items flag "book within 2 weeks" advisory.

---

## F6 — Prior Authorization Flag

**Goal**: Flag when a procedure likely requires prior authorization from the patient's insurance, so the nurse can initiate that process before the appointment.

### Data
Add `PRIOR_AUTH_REQUIRED` dict to `data/insurance.py`:
```python
PRIOR_AUTH_REQUIRED = {
    ("Surgery", "Cigna"): True,
    ("Surgery", "United Health Care"): True,
    ("Orthopedics", "Aetna"): True,
}
```

### Logic
New `check_prior_auth(specialty, insurance) -> bool`

### UI
**Step 4 / Step 6 (Confirm)**: If prior auth required, show yellow advisory:
"⚠ Prior authorization may be required for [SPECIALTY] with [INSURANCE]. Contact [INSURANCE] before the appointment date."

---

## Implementation Order & Dependencies

```
F1 (Audit) → No dependencies. Start here. Fixes the "no audit data" problem immediately.

F3 (Insurance) → Needs patient.insurance data + provider.accepted_insurances.
                  Update Flask data + backend model first, then logic, then UI.

F2 (Scheduling) → Needs slot generator + new route + new frontend step.
                   Can run parallel to F3.

F4 (Capacity) → Small add-on to provider model. Do alongside F3 data changes.

F5 (Urgency) → Small add-on to patient model. Do alongside F3.

F6 (Prior Auth) → Depends on F3 (insurance data). Do after F3 logic is in.
```

### Recommended Build Order

| Phase | Items | Why |
|---|---|---|
| 1 | F1 (Audit logging) | Fixes broken audit page; high demo value; no dependencies |
| 2 | F3-data + F4 + F5 | Pure data layer — extend Flask data, Provider model, PatientData model |
| 3 | F3-logic + F3-UI | Insurance check at provider selection + appointment details |
| 4 | F2 (Scheduling) | New step between details and preferences; updates reminders |
| 5 | F6 (Prior auth) | Quick add after F3 insurance data is in place |

---

## Updated Session Flow (9 screens)

```
Step 1 · Patient Lookup
  ↓  [patient selected, identity verified]
Step 2 · Referrals Overview
  ↓  [Book This →]  (urgent referrals sorted first — F5)
Step 3 · Provider Selection
  ↓  (shows insurance badge — F3; capacity badge — F4)
Step 4 · Appointment Details
  ↓  (NEW/ESTABLISHED reasoning; insurance status card — F3; prior auth flag — F6)
Step 5 · Schedule Appointment  ← NEW (F2)
  ↓  (date/time slot picker; grouped by week)
Step 6 · Patient Preferences
  ↓
Step 7 · Booking Confirmation
  ↓  (insurance warning + patient acknowledgment if not covered — F3)
  ↓  [post-booking feedback]
Step 8 → Step 2 (book next referral) or Step 8...
Step 8 · Session Complete
  ↓  (outcome logging; reminder touchpoints; nurse notes)
```

Steps on screen stay "Step 2–7" from the user's perspective (Step 2 = Referrals Overview as the start of booking flow). The scheduling step is inserted between the current Steps 4 and 5.

---

## Data Changes Required

All invented values must be added to `data-changes.md`.

### Flask patient data (`MLChallenge/` patients endpoint)
```json
{
  "id": 1,
  "name": "John Doe",
  "insurance": "Blue Cross Blue Shield of North Carolina",
  ...
}
```

### Provider model additions
```python
Provider(
    last_name="House", first_name="Gregory",
    accepted_insurances=["Blue Cross Blue Shield of North Carolina", "Aetna", "United Health Care"],
    accepting_new_patients=True,
    ...
)
```

### ReferredProvider additions
```python
ReferredProvider(
    provider="House, Gregory MD",
    specialty="Orthopedics",
    urgency="urgent",
    priority_note="Post-discharge follow-up required within 2 weeks",
)
```

---

## What This Adds to the Demo Story

| Feature | Demo moment |
|---|---|
| F1 audit | Open /audit during booking — show every nurse click, API call, and LLM decision in one timeline |
| F2 scheduling | "The nurse picks an actual time slot — not 'the office will call back'" |
| F3 insurance | Show provider list with green/red badges; trigger the not-covered flow with an alternative provider shown |
| F4 capacity | "Dr. Yang is not accepting new patients — system flags it before the nurse picks her" |
| F5 urgency | "Post-discharge orthopedics is flagged urgent — booked first" |
| F6 prior auth | "Aetna + Orthopedics triggers a prior authorization advisory automatically" |
