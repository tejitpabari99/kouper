# Advanced Tier Implementation Plan
## Kouper Health Care Coordinator — ML Interview Submission

**Date:** 2026-03-24
**Status:** Pre-implementation planning document
**Scope:** All 7 Advanced Tier features (A1–A7) + demo readiness gaps

---

## Table of Contents

1. [Strategic Assessment](#strategic-assessment)
2. [Pre-Implementation Checklist](#pre-implementation-checklist)
3. [Implementation Priority Matrix](#implementation-priority-matrix)
4. [Recommended Build Order](#recommended-build-order)
5. [A4 — Graceful API Error Recovery](#a4--graceful-api-error-recovery)
6. [A1 — Structured Audit Log](#a1--structured-audit-log)
7. [A6 — Cross-Referral Scheduling Optimization](#a6--cross-referral-scheduling-optimization)
8. [A7 — Nurse Session Notes](#a7--nurse-session-notes)
9. [A5 — Transportation Resources Flag](#a5--transportation-resources-flag)
10. [A2 — Follow-Up Reminder Scheduling](#a2--follow-up-reminder-scheduling)
11. [A3 — Post-Appointment Status Tracking](#a3--post-appointment-status-tracking)
12. [Presentation Deck](#presentation-deck)
13. [Demo Script](#demo-script)
14. [Trade-offs and Shortcuts for Demo Context](#trade-offs-and-shortcuts-for-demo-context)

---

## Strategic Assessment

**Challenge coverage: ~85%.** The business logic, tool-calling architecture, edge case handling, and 7-screen UI are all strong. The remaining 15% is almost entirely presentation deck and unverified demo path — not feature gaps.

### What will impress in the room

- **Raw tool-calling loop with deterministic Python logic.** Every business rule is a testable function. The LLM decides; the code executes. This is the architecturally correct production pattern and the most demonstrable.
- **Five of seven data traps correctly handled:** no-show filtering, unnamed referral provider, multi-location provider (House), name normalization ("Dr. Gregory House" ↔ "House, Gregory MD"), 5-year vs 3-year rule awareness.
- **49 pytest tests + 37 frontend tests.** Having testable, deterministic business functions that you can point to in code review is what separates a senior submission.
- **Booking overwrite on edit.** Most candidates treat bookings as append-only.

### Critical gaps (blocking demo)

| Risk | Impact | Fix |
|---|---|---|
| No presentation deck | Deck is a stated deliverable — its absence is immediately visible | Build deck before demo |
| End-to-end demo not verified | Any screen break in front of interviewers is disqualifying | Do a dry-run, fix what breaks |
| 3 required chat questions untested | These are the verbatim questions from the challenge brief | Test them live, fix tool dispatch if needed |
| No audit log (A1) | Obvious gap in a healthcare context — interviewers will ask | 30-min build, high signal |

### Advanced tier ranked by interview impact (PM assessment)

| Rank | Item | Why it matters |
|---|---|---|
| 1 | **A4** — Error recovery | Flask crash during demo = demo failure. This is insurance. |
| 2 | **A1** — Audit log | 30 min to build, asked about in every healthcare AI review |
| 3 | **A6** — Co-location optimization | Jefferson easter egg — memorable, shows you read the data carefully |
| 4 | **A7** — Nurse session notes | Visible on every booking, trivial to build |
| 5 | **A2** — Reminder scheduling (mock) | Closes the "full loop" story in the deck |
| 6 | **A5** — Transport resources | Easy, closes the preference flag story |
| 7 | **A3** — Post-appointment tracking | Best to describe in deck; most invasive to implement |

---

## Pre-Implementation Checklist

**Do these before writing any advanced tier code.** They protect the demo.

### ☐ 1. Verify end-to-end demo path

Start all three services (Flask :5000, FastAPI :8000, Vite :5173) and walk through this exact path:

1. Step 1 — Search "John" → select John Doe → check identity → Confirm & Begin
2. Step 2 — See two referrals, note no-show warning
3. Step 3 — Select Dr. Gregory House (Orthopedics), note Brennan shown as alternative
4. Step 4 — See ESTABLISHED with reasoning, pick PPTH Orthopedics
5. Step 5 — Set preferences: Text, 8–10am, English, no transport
6. Step 6 — Review summary, confirm booking
7. Step 2 again — Book Referral 2 (Primary Care), select Dr. Meredith Grey
8. Step 3–6 — Repeat, verify NEW appointment type
9. Step 7 — Session complete, verify both bookings shown

**Fix anything that breaks before proceeding.**

### ☐ 2. Test the three required chat questions

These are verbatim from the challenge brief. Open the ChatPanel and send each:

1. *"If Dr. House is not available on a certain day, what other providers are available?"*
   - Expected: LLM calls `check_availability` or `get_providers`, returns Brennan as alternative with Jefferson Hospital details
2. *"Does the hospital accept Aetna? What should I do if not?"*
   - Expected: LLM calls `check_insurance("Aetna")`, returns accepted=True
   - Bonus test: ask about "Anthem" → should return self-pay rate for specialty
3. *"Has the patient booked with Dr. House before?"*
   - Expected: LLM uses patient appointment history, returns yes (8/12/2024, completed) → ESTABLISHED

If any of these fail, diagnose the tool dispatch before moving on.

### ☐ 3. Start the presentation deck

See the [Presentation Deck](#presentation-deck) section. The architecture diagram and state machine are the two most load-bearing slides — create them first.

---

## Implementation Priority Matrix

| Item | Interview Impact | Complexity | Dependencies | Build Order |
|------|-----------------|------------|--------------|-------------|
| A4 — Graceful API Error Recovery | **HIGH** — protects the demo | Low | None | 1st |
| A1 — Structured Audit Log | **HIGH** — PHI/HIPAA story, LLM transparency | Medium | None | 2nd |
| A6 — Cross-Referral Optimization | **HIGH** — easter egg, memorable demo moment | Medium | None | 3rd |
| A7 — Nurse Session Notes | **HIGH** — visible in every booking flow | Low | None | 4th |
| A5 — Transportation Resources | **MEDIUM** — closes the loop on preferences data | Low | None | 5th |
| A2 — Reminder Scheduling | **MEDIUM** — architecture story, no real sends | Medium | A7 (booking fields) | 6th |
| A3 — Post-Appointment Tracking | **MEDIUM** — closes the clinical loop | High | A2, data model changes | Last |

**Recommended order:** A4 → A1 → A6 → A7 → A5 → A2 → A3

---

## Recommended Build Order

**A4 first:** Error handling wraps all tool calls. Building it first means every subsequent feature automatically benefits from graceful errors. It requires zero schema changes — purely internal plumbing. Most importantly: it protects the demo.

**A1 second:** The audit log targets the `while True:` loop in `llm/client.py` — the single choke point for all tool calls. Once A4's structured errors are in place, logging them is natural. The `GET /audit-log` endpoint becomes a live demo moment.

**A6 third:** The Jefferson co-location easter egg is the single most memorable demo moment. It requires one pure function and a banner on Step 2. High value, medium effort, no dependencies.

**A7 fourth:** Nurse notes require two small additions (a field on `CompletedBooking`, a textarea on the confirm screen). It's visible on every booking in the session summary and in the print view. 30 minutes of work.

**A5 fifth:** Pure frontend add-on to the transportation section already built. Backend is a static data file. Shows patient-centered thinking, closes the transportation preferences story.

**A2 sixth:** Depends on `CompletedBooking` having a `scheduled_date` field (added in A7). Reminder records stored as JSON — no real sends. The architecture story matters more than execution.

**A3 last:** Most invasive change — new persistence file, updates to `determine_appointment_type()` (which has existing tests), and a new route. Safest to do after everything else is stable. Can be partially demoed (just the logging UI) even if the feedback loop isn't fully wired.

---

## A4 — Graceful API Error Recovery

**Complexity:** Low | **Files changed:** 4 backend | **Demo value:** High (protects against live failure)

### What to Build

Replace bare `except Exception as e: return json.dumps({"error": str(e)})` with a structured error contract that the LLM narrates gracefully. The UI already surfaces `err.detail` — once backend returns safe strings, they display correctly.

### Backend Changes

**1. `backend/app/llm/tool_executor.py`**

Define an `ErrorCode` enum and a `ToolErrorResult` response shape:

```python
class ErrorCode(str, Enum):
    PATIENT_NOT_FOUND = "PATIENT_NOT_FOUND"
    API_UNAVAILABLE = "API_UNAVAILABLE"
    PROVIDER_NOT_FOUND = "PROVIDER_NOT_FOUND"
    INVALID_INPUT = "INVALID_INPUT"
    UNKNOWN = "UNKNOWN_ERROR"

class ToolErrorResult(BaseModel):
    error: bool = True
    code: ErrorCode
    user_message: str   # safe, human-readable — LLM will relay this
    detail: str = ""    # internal, server-side only
```

In `execute_tool()`, replace the catch-all with specific handlers:
- `PatientNotFound` → `PATIENT_NOT_FOUND`, `user_message="No patient record found with that ID. Please verify and try again."`
- `APIUnavailable` → `API_UNAVAILABLE`, `user_message="The patient information system is temporarily unavailable. Please try again in a moment."`
- `ValueError("Provider not found")` → `PROVIDER_NOT_FOUND`
- All others → `UNKNOWN`, log `detail=str(e)` server-side, safe generic `user_message`

**2. `backend/app/llm/prompts.py`**

Add to `build_system_prompt()`:
```
## Tool Error Handling
When a tool returns {"error": true, "code": "...", "user_message": "..."},
relay the user_message to the nurse verbatim. Do not expose error codes or
stack traces. Offer the most appropriate next step.
```

**3. `backend/app/routes/chat.py`**

Change bare `except Exception` to:
```python
except Exception as e:
    import logging
    logging.error(f"Chat route error: {e}", exc_info=True)
    raise HTTPException(
        status_code=500,
        detail="The assistant encountered an unexpected error. Please try your message again."
    )
```

**4. `backend/app/routes/patient.py`**

Map `PatientNotFound` and `APIUnavailable` to appropriate 404/503 responses with safe `detail` strings.

### Demo Moment

Stop the Flask app. Try to look up a patient — UI shows "The patient information system is temporarily unavailable…" instead of a traceback. Restart Flask — recovery is automatic. Say: *"The LLM is the least reliable component in this system. We've structured everything around that assumption."*

---

## A1 — Structured Audit Log

**Complexity:** Medium | **Files changed:** 3 backend + 2 new | **Demo value:** High (HIPAA story, LLM transparency)

### What to Build

An append-only JSONL file (`.audit_log.jsonl`, alongside `.sessions.json`) recording every LLM tool call with full context. A `GET /audit-log` endpoint returns the last N entries. The key differentiator: capturing the LLM's `reasoning_hint` — the text blocks it generates before calling a tool — making this a genuine AI reasoning trace, not just an API call log.

### Data Schema

```python
class AuditLogEntry(BaseModel):
    timestamp: str           # ISO-8601 UTC
    session_id: str
    tool_name: str
    tool_input: dict         # exact input passed to the tool
    tool_output: str         # raw JSON string returned by tool
    reasoning_hint: str      # LLM text blocks before tool call (the reasoning)
    error: bool = False
    error_code: Optional[str] = None
```

### Backend Changes

**1. `backend/app/audit_log.py`** (new file)

```python
AUDIT_LOG_FILE = os.path.join(os.path.dirname(__file__), '../../.audit_log.jsonl')

def append_audit_entry(entry: AuditLogEntry) -> None:
    """Append one entry to the JSONL audit log. Silent on failure — never crash the tool call."""

def get_recent_entries(n: int = 50) -> List[AuditLogEntry]:
    """Read last N lines from the JSONL file and parse them."""
```

Both functions wrap all I/O in try/except — the audit log must never crash the main request path.

**2. `backend/app/llm/client.py`**

In the `while True:` tool-calling loop, after `execute_tool()` returns, call `append_audit_entry()`. Extract `reasoning_hint` from `{"type": "text"}` blocks that appear in `assistant_content` before the tool use block:

```python
result = execute_tool(block.name, block.input, session_patient=patient)
append_audit_entry(AuditLogEntry(
    timestamp=datetime.utcnow().isoformat() + "Z",
    session_id=session.session_id,
    tool_name=block.name,
    tool_input=block.input,
    tool_output=result,
    reasoning_hint=_extract_text_blocks(assistant_content),
    error='"error": true' in result,
))
```

Add `_extract_text_blocks(content_list) -> str` as a private helper that joins text-type blocks.

**3. `backend/app/routes/audit.py`** (new file)

```python
router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/log")
def get_audit_log(n: int = 50):
    return get_recent_entries(n)
```

**4. `backend/app/server.py`** — include the audit router.

### PHI De-identification Note (for presentation deck)

In production, `tool_input` and `tool_output` must be scrubbed of PHI before storage. Options:
- Route to a HIPAA BAA-covered log aggregator (AWS CloudWatch, Datadog with BAA)
- Field-level redaction in `append_audit_entry()` — replace names, DOBs, IDs with tokens
- Separate "what was called" log from "what data was returned" log

For the demo, flag this explicitly during the presentation.

### Demo Moment

After a full booking, open `/docs` Swagger UI, call `GET /audit-log?n=10`. Show entries for `determine_appointment_type`, `check_availability`, `check_insurance` — each with timestamp, session ID, input, and the LLM's reasoning_hint text. Say: *"Every LLM decision is traceable. This is the foundation of an auditable AI system — not a black box."*

---

## A6 — Cross-Referral Scheduling Optimization

**Complexity:** Medium | **Files changed:** 2 backend + 1 frontend | **Demo value:** High (the easter egg)

### What to Build

When a patient has multiple referrals, detect if any candidate providers share a physical location and surface a proactive banner on Step 2. The specific case: Dr. Gregory House (Orthopedics, Jefferson Th-F) and Dr. Temperance Brennan (Orthopedics, Jefferson Tu-Th) both practice at Jefferson Hospital. If the session has referrals that could use Jefferson, the banner fires automatically.

### Backend Changes

**1. `backend/app/logic/colocated_providers.py`** (new file)

```python
class ColocationSuggestion(BaseModel):
    location_name: str
    address: str
    providers: List[str]   # e.g. ["Dr. Gregory House", "Dr. Temperance Brennan"]
    specialties: List[str]
    message: str           # human-readable suggestion for the UI

def find_colocated_providers(provider_names: List[str]) -> List[ColocationSuggestion]:
    """
    Given a list of provider display names, find any that share a department name.
    Returns one ColocationSuggestion per shared location with 2+ providers.
    Pure function — reads only from in-memory PROVIDERS list.
    """
```

Implementation: for each provider name, look up their departments in `PROVIDERS`. Build a dict keyed by `department.name` → list of providers. Any key with 2+ entries is a co-location hit.

**2. `backend/app/routes/session.py`** — add to existing router:

```python
@router.get("/{session_id}/colocated-suggestions")
def get_colocated_suggestions(session_id: str):
    """Return co-location suggestions for providers in this session's referrals."""
```

Logic:
1. Load session. No patient → return `[]`.
2. Collect provider names from `session.patient["referred_providers"]` (the `provider` field, if set) plus `session.bookings` (the `provider_name` field).
3. Call `find_colocated_providers(provider_names)`.
4. Return the list.

Also add to `build_system_prompt()` in `prompts.py`:
```
## Co-location Tip
Dr. Gregory House and Dr. Temperance Brennan both practice at Jefferson Hospital,
Claremont, NC. If this patient has referrals to both, proactively suggest same-day
scheduling at Jefferson to minimize patient trips.
```

### Frontend Changes

**`frontend/src/routes/session/[id]/+page.svelte`** (Step 2)

Add a second `onMount` fetch to `GET /session/{id}/colocated-suggestions`. If non-empty, render an indigo banner above the referral cards:

```
💡 Scheduling Tip
Dr. Gregory House and Dr. Temperance Brennan both practice at Jefferson Hospital
(202 Maple St, Claremont, NC). Consider booking both appointments on the same day
to minimize trips for the patient.   [×]
```

Banner is dismissible (close button, dismissed state stored in `sessionStorage`).

Add `getColocatedSuggestions: (sessionId) => request('GET', `/session/${sessionId}/colocated-suggestions`)` to `api/client.js`.

### Demo Moment

The banner appears automatically on Step 2. Say: *"Notice this — the system detected that two of the patient's potential providers both practice at Jefferson Hospital. Without this, a nurse might book two separate trips. This relationship is hidden in raw data — the system surfaces it automatically. One suggestion like this could eliminate a trip for a patient who may already be struggling post-discharge."*

---

## A7 — Nurse Session Notes

**Complexity:** Low | **Files changed:** 3 backend + 2 frontend | **Demo value:** High (visible on every booking)

### What to Build

A free-text notes field on each individual `CompletedBooking` (distinct from `PatientPreferences.notes` which captures patient logistics). Booking-scoped: *"Patient concerned about self-pay cost, discussed sliding scale options."*

### Backend Changes

**1. `backend/app/models/session.py`**

Add to `CompletedBooking`:
```python
nurse_notes: str = ""
scheduled_date: Optional[str] = None  # also needed for A2
```

**2. `backend/app/routes/booking.py`**

Add `nurse_notes: str = ""` to `ConfirmBookingRequest`. Pass through to `CompletedBooking`. Existing sessions without the field deserialize with default `""` via Pydantic.

### Frontend Changes

**1. `frontend/src/routes/session/[id]/referral/[idx]/confirm/+page.svelte`**

Add a textarea between the Follow-Up Plan card and the nurse script:
```
Label: "Internal notes for care record (not sent to patient)"
Placeholder: "e.g., Patient concerned about copay, discussed self-pay options. Prefers morning calls."
Bind: let nurseNotes = ''
```

Pass `nurse_notes: nurseNotes` in the `confirmBooking` call.

**2. `frontend/src/routes/session/[id]/complete/+page.svelte`**

Inside the `{#each summary.bookings as booking}` block:
```svelte
{#if booking.nurse_notes}
  <div style="font-size:12px; color:#6b7280; margin-top:6px; font-style:italic; border-top:1px solid #f3f4f6; padding-top:6px">
    📝 Notes: {booking.nurse_notes}
  </div>
{/if}
```

Also apply print-safe styling so notes appear on printed summary.

### Demo Moment

During Dr. House's confirmation screen, type: *"Patient expressed concern about copay — confirmed $300 self-pay rate discussed, patient agreed to proceed."* Show it appear in Session Complete and in the print view. Say: *"Care coordination doesn't end with the booking. These notes become part of the clinical record."*

---

## A5 — Transportation Resources Flag

**Complexity:** Low | **Files changed:** 1 new backend + 1 route + 1 frontend | **Demo value:** Medium

### What to Build

When `transportation_needs: true` is set, surface a curated list of NC community transport resources on the preferences screen. Resources are mock data — log in `data-changes.md`.

### Backend Changes

**1. `backend/app/data/transport_resources.py`** (new file)

```python
class TransportResource(BaseModel):
    name: str
    type: Literal["rideshare", "medicaid_transport", "volunteer", "transit"]
    phone: Optional[str]
    url: Optional[str]
    service_area: str
    notes: str

TRANSPORT_RESOURCES: List[TransportResource] = [
    TransportResource(name="NC MedAssist Transport", type="medicaid_transport",
        phone="1-800-555-0101", url=None, service_area="Statewide NC",
        notes="For Medicaid recipients only. Requires 48-hour advance booking."),
    TransportResource(name="Greensboro Urban Transit", type="transit",
        phone="(336) 555-0210", url=None, service_area="Greensboro, NC",
        notes="Fixed route. PPTH Orthopedics is on Route 12."),
    TransportResource(name="Guilford County Senior Services", type="volunteer",
        phone="(336) 555-0185", url=None, service_area="Guilford County, NC",
        notes="Free volunteer driver program. Patients 60+."),
    TransportResource(name="Lyft Healthcare", type="rideshare",
        phone=None, url="https://healthcare.lyft.com", service_area="Most NC metro areas",
        notes="Nurse can schedule a ride via the Lyft Health portal."),
]
```

**2. `backend/app/routes/transport.py`** (new file) + include in `server.py`

```python
@router.get("/transport-resources")
def get_transport_resources():
    return TRANSPORT_RESOURCES
```

### Frontend Changes

**`frontend/src/routes/session/[id]/referral/[idx]/preferences/+page.svelte`**

The transportation section already shows a nurse script when `transportationNeeds === true`. Extend it to also fetch resources reactively:

```js
let transportResources = [];
$: if (transportationNeeds && transportResources.length === 0) {
  api.getTransportResources().then(r => transportResources = r).catch(() => {});
}
```

Add `getTransportResources: () => request('GET', '/transport-resources')` to `api/client.js`.

Render as a compact list inside the yellow banner, below the script text.

### Demo Moment

Select "Needs Ride Assistance" — the banner expands to show the script plus four NC transport resources. Say: *"Instead of the nurse searching Google, the system surfaces community resources by geography. In production, this pulls from the 211 NC database."*

---

## A2 — Follow-Up Reminder Scheduling

**Complexity:** Medium | **Files changed:** 3 backend + 1 frontend | **Dependencies:** A7 (needs `scheduled_date` on `CompletedBooking`)

### What to Build

When a booking is confirmed, automatically schedule three reminder touchpoints and store them as `ReminderRecord` objects on the session. Not actually sent — mocked with a queued record. A `GET /session/{id}/reminders` endpoint returns them.

Three touchpoints per booking:
1. **Booking confirmation** — immediate
2. **48-hour reminder** — pending actual appointment date
3. **Day-of reminder** — pending actual appointment date

### Data Model

**`backend/app/models/session.py`** — add new model:

```python
class ReminderRecord(BaseModel):
    booking_referral_index: int
    touchpoint: Literal["booking_confirmation", "48hr_reminder", "day_of_reminder"]
    channel: str           # mirrors PatientPreferences.contact_method
    contact_value: str     # phone or email from preferences
    status: Literal["queued", "sent", "failed"] = "queued"
    scheduled_for: Optional[str] = None   # ISO date or "pending_date"
    message_template: str  # fully rendered reminder text
```

Add `reminders: List[ReminderRecord] = []` to `BookingSession`.

### Backend Changes

**1. `backend/app/logic/reminders.py`** (new file)

```python
def schedule_reminders(
    booking: CompletedBooking,
    preferences: PatientPreferences,
    patient_name: str,
) -> List[ReminderRecord]:
    """Generate the three reminder records for a confirmed booking."""
```

Message templates:
- **booking_confirmation:** *"Hi {patient_name}, your referral to {provider_name} at {location} has been submitted. The office will contact you to confirm your appointment date. Arrive {arrival_minutes_early} minutes early for your {duration_minutes}-minute appointment."*
- **48hr_reminder:** *"Hi {patient_name}, you have an appointment with {provider_name} at {location} in 2 days. Please arrive {arrival_minutes_early} minutes early."*
- **day_of_reminder:** *"Hi {patient_name}, reminder: your appointment with {provider_name} is today at {location}. Arrive {arrival_minutes_early} minutes early."*

Touchpoints 2 and 3 use `scheduled_for = "pending_date"` until the office confirms.

**2. `backend/app/routes/booking.py`**

After appending the `CompletedBooking`, call `schedule_reminders()` if `session.patient_preferences` is set. Append to `session.reminders`.

**3. `backend/app/routes/session.py`** — add:

```python
@router.get("/{session_id}/reminders")
def get_reminders(session_id: str):
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"reminders": session.reminders}
```

### Frontend Changes

**`frontend/src/routes/session/[id]/complete/+page.svelte`**

Add a collapsible "Scheduled Touchpoints" section per booking on load. Timeline format:

```
Booking 1 — Dr. House, Orthopedics
  [✓] Booking confirmation — Text — Queued — (message preview)
  [•] 48-hour reminder — Text — Pending appointment date
  [•] Day-of reminder  — Text — Pending appointment date
```

### Demo Moment

Say: *"The system automatically scheduled three reminder touchpoints the moment the booking was confirmed. Research shows reminders reduce no-shows by 20–30%. The architecture — a queued reminder record connecting to Twilio or SendGrid — is the same whether we're sending one reminder or a million."*

---

## A3 — Post-Appointment Status Tracking

**Complexity:** High | **Files changed:** 3 backend + 2 new + 1 frontend + test updates | **Build last**

### What to Build

Log the outcome of a booked appointment (`completed`, `no-show`, `cancelled`) after the appointment date passes. Stored in a persistent `.appointment_outcomes.json` file. The `determine_appointment_type()` function is updated to also check this local store — closing the feedback loop.

### Data Model

**`backend/app/models/appointment.py`** (extend):

```python
class AppointmentOutcome(BaseModel):
    outcome_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    session_id: str
    referral_index: int
    provider_name: str
    specialty: str
    location: str
    appointment_date: str
    status: Literal["completed", "no-show", "cancelled"]
    logged_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    nurse_notes: str = ""
```

### Backend Changes

**1. `backend/app/outcome_store.py`** (new file) — mirrors `session_store.py` pattern, persists to `.appointment_outcomes.json`

**2. `backend/app/logic/appointment_type.py`** — add `additional_outcomes: Optional[List[AppointmentOutcome]] = None` parameter. After processing `patient.appointments`, also check local outcomes for the same specialty filtered to `status == "completed"`.

**3. `backend/app/routes/outcomes.py`** (new file):

```python
@router.post("")
def log_outcome(body: LogOutcomeRequest): ...

@router.get("/patient/{patient_id}")
def get_patient_outcomes(patient_id: str): ...
```

**4. `backend/app/server.py`** — include outcomes router.

### Frontend Changes

**`frontend/src/routes/session/[id]/complete/+page.svelte`**

Per booking, add "Update Outcome" button that expands inline form: appointment date picker, status (Completed / No-Show / Cancelled), notes textarea, Save button.

### Test Updates

Add to `tests/test_appointment_type.py`:
- `test_local_outcome_overrides_no_history()` — local completed outcome within 5 years → ESTABLISHED
- `test_local_noshows_dont_count()` — local no-show → still NEW
- `test_combined_api_and_local_outcomes()` — both sources, most recent wins

### Demo Moment

Can be partially demoed (just the logging UI) even if the full feedback loop isn't wired. Say: *"This closes the loop. The system doesn't just book appointments — it tracks whether they happened. And that outcome feeds directly back into the NEW/ESTABLISHED calculation for the next booking."*

---

## Presentation Deck

**This is a stated deliverable — build it before the demo.** Eight slides, prioritized by how much work they do in 20 minutes.

### Must-have slides (build first)

**Slide 1 — Architecture diagram**
The single most important slide. Shows: Nurse → SvelteKit UI → FastAPI → LLM (Claude Haiku) → Tool Layer → Deterministic Python Functions → Patient Flask API. Annotate: "LLM decides, code executes. Business logic is never inside the model."

**Slide 2 — Session state machine**
7-step flow as a state diagram with valid transitions and reset conditions (mid-flow provider change). Shows you thought about the problem as an engineer.

**Slide 3 — NEW vs. ESTABLISHED decision tree**
Walk through John Doe's two referrals explicitly:
- Orthopedics + House + 8/12/2024 completed → within 5 years → **ESTABLISHED**
- Primary Care + Grey + 3/5/2018 completed + 9/17/2024 no-show (doesn't count) + 11/25/2024 cancelled (doesn't count) → last completed > 5 years → **NEW**

**Slide 4 — Edge cases table**

| Trap | Where in data | Correct handling |
|---|---|---|
| Provider at 2 locations | House: PPTH + Jefferson | Show both upfront, nurse picks |
| Referral with no provider | `referred_providers[1]` has no name | Query by specialty, show options |
| No-shows don't count | Grey 9/17/24 | Filter to `status == "completed"` only |
| Cancelled doesn't count | Grey 11/25/24 | Same filter |
| Last completed > 5 years | Grey 3/5/18 | NEW even though she's the PCP |
| Name format mismatch | "Dr. Gregory House" ↔ "House, Gregory MD" | Normalize on load |
| 5yr vs 3yr rule | Challenge says 5yr; CMS/CPT is 3yr | Use 5yr per brief; call out in deck |

### Strong supporting slides

**Slide 5 — Tool schema example**
Show `determine_appointment_type` tool with annotated parameter descriptions. Explain: "Parameter `description` fields are prompt engineering inside the tool definition — they tell the model when and how to use each parameter."

**Slide 6 — Production considerations**
- HIPAA: PHI in LLM calls → need HIPAA BAA or de-identification layer
- EHR integration: FHIR R4 `Slot` (availability), `Appointment` (booking)
- Session state: Redis in production; current `SessionStore` is swap-ready
- 3-year vs 5-year CMS rule: used 5yr per brief; production would use 3yr CPT standard
- No-show reduction: audit log + reminder pipeline closes the care coordination loop

**Slide 7 — Problem statement**
Before/after: what a care coordinator does today manually vs. with this tool. Keep brief — the demo does this better than slides.

---

## Demo Script

### 20-minute flow

| Time | Screen / Topic | Feature highlighted |
|---|---|---|
| 0:00–2:00 | Architecture diagram | Explain tool-calling pattern; A1 audit log story: "every LLM decision is traceable" |
| 2:00–4:00 | Patient lookup with Flask stopped | A4: graceful error message; restart Flask, recovery is automatic |
| 4:00–6:00 | Referrals overview | A6: co-location banner appears automatically — Jefferson easter egg |
| 6:00–9:00 | Provider → Appointment Details | Show ESTABLISHED reasoning; ask chat Q1 ("what if House isn't available?") |
| 9:00–11:00 | Patient Preferences | A5: select transport needs, resources load; ask chat Q2 ("does it accept Aetna?") |
| 11:00–13:00 | Booking Confirmation | A7: type nurse notes live; ask chat Q3 ("has patient booked with House before?") |
| 13:00–15:00 | Session Complete | A2: expand scheduled touchpoints, show three reminders per booking |
| 15:00–16:00 | Swagger UI `/docs` | A1: call `GET /audit-log`, walk through reasoning_hint entries |
| 16:00–17:00 | Outcome logging | A3: log outcome, explain feedback loop into NEW/ESTABLISHED |
| 17:00–20:00 | Architecture Q&A | PHI de-identification, FHIR integration, Redis swap, 3yr vs 5yr rule |

### Three required chat questions (verbatim from brief)

These must be tested before demo day:

1. *"If Dr. House is not available on a certain day, what other providers are available?"*
   → Should trigger `check_availability` or `get_providers`, return Brennan at Jefferson

2. *"Does the hospital accept Aetna? What should I do if not?"*
   → Should trigger `check_insurance("Aetna")`, return accepted=True
   → Bonus: ask about "Anthem" → self-pay $300 (Orthopedics)

3. *"Has the patient booked with Dr. House before?"*
   → LLM uses patient history, returns 8/12/2024 completed → ESTABLISHED reasoning

---

## Trade-offs and Shortcuts for Demo Context

| Feature | Demo approach | Production replacement |
|---|---|---|
| A2 reminders | JSON records, no actual sends | Twilio SMS / SendGrid email |
| A2 appointment dates | "pending_date" placeholder | EHR FHIR `Appointment.start` |
| A3 outcome logging | Nurse manually logs in UI | Automated via EHR ADT feed |
| A5 transport resources | Static list in `transport_resources.py` | 211 NC API or community DB |
| A1 log file | Flat JSONL on local disk | HIPAA BAA-covered log aggregator |
| A1 PHI in logs | Full data logged | Field-level tokenization before write |
| A6 co-location | Static `PROVIDERS` analysis | Real-time cross-provider calendar query |
| Session store | `.sessions.json` file | Redis (`SessionStore` is swap-ready) |

### What not to cut

- **A4 error handling** — a crash during a live demo is worse than any missing feature
- **A7 notes in print view** — the print summary is a likely demo touchpoint
- **A1 `reasoning_hint` field** — without it the audit log is just an API call log, not a reasoning trace
- **The 3 required chat questions** — they are literally in the challenge brief; they will be asked

---

*Combined from: advanced tier implementation plan + PM strategic assessment. Last updated 2026-03-24.*
*For Basic Tier context: `PLAN.md`. For full data/business rules: `CONTEXT.md`.*
