# Mini Care Coordinator Assistant — Full Context

> This file is a single source of truth for anyone starting a new conversation on this project.
> It contains: the challenge brief, all raw data, API details, business rules, research findings, and architectural decisions.
> Read this file before writing any code or making any decisions.

---

## Table of Contents
1. [Challenge Brief](#challenge-brief)
2. [Raw Data: Provider Directory](#raw-data-provider-directory)
3. [Raw Data: Appointment Rules](#raw-data-appointment-rules)
4. [Raw Data: Insurance & Self-Pay](#raw-data-insurance--self-pay)
5. [Patient API Specification](#patient-api-specification)
6. [John Doe — Full Patient Record](#john-doe--full-patient-record)
7. [Pre-Computed Business Logic for John Doe](#pre-computed-business-logic-for-john-doe)
8. [Hidden Complexity / Data Traps](#hidden-complexity--data-traps)
9. [Architecture Decision & Rationale](#architecture-decision--rationale)
10. [LLM Tool Design](#llm-tool-design)
11. [Session State Design](#session-state-design)
12. [Nurse Workflow — 7-Screen Flow](#nurse-workflow--7-screen-flow)
13. [Patient Preferences Module](#patient-preferences-module)
14. [Industry Research Findings](#industry-research-findings)
15. [Tech Stack Decisions](#tech-stack-decisions)
16. [Parallel Build Structure](#parallel-build-structure)
17. [Edge Cases Registry](#edge-cases-registry)
18. [What NOT to Do](#what-not-to-do)
19. [Production Considerations (for Presentation)](#production-considerations-for-presentation)

---

## Challenge Brief

**Source:** `MLChallenge/KouperHealthMLChallenge.pdf`

Build a **Care Coordinator Assistant** — an LLM-powered chatbot that helps a nurse book referral appointments for a patient following a hospital visit.

### What the assistant must do:
- Guide the nurse through booking appointments step by step
- Answer natural language questions
- Handle exceptions and real-world edge cases
- Collect 4 pieces of info per booking: patient identity, provider, appointment type, location

### Questions it must be able to answer:
- "If [provider] is not available at [time], what other providers are available?"
- "Does the hospital accept [insurance]? What should I do if not?"
- "Has the patient booked with this provider before?"

### Materials provided:
- `data_sheet.txt` — provider directory, appointment rules, insurances, self-pay rates
- Flask API at `api/flask-app.py` — serves patient data at `GET /patient/{id}`

### Deliverables:
- Code (zip or GitHub repo)
- Presentation deck (design choices, implementation decisions, tools used, cited sources)
- Live 20-minute demo + technical walkthrough

---

## Raw Data: Provider Directory

From `MLChallenge/data_sheet.txt`:

### Grey, Meredith
- Certification: MD
- Specialty: Primary Care
- Department: Sloan Primary Care
  - Phone: (710) 555-2070
  - Address: 202 Maple St, Winston-Salem, NC 27101
  - Hours: M-F 9am-5pm

### House, Gregory
- Certification: MD
- Specialty: Orthopedics
- Department 1: PPTH Orthopedics
  - Phone: (445) 555-6205
  - Address: 101 Pine St, Greensboro, NC 27401
  - Hours: M-W 9am-5pm
- Department 2: Jefferson Hospital
  - Phone: (215) 555-6123
  - Address: 202 Maple St, Claremont, NC 28610
  - Hours: Th-F 9am-5pm

### Yang, Cristina
- Certification: MD
- Specialty: Surgery
- Department: Seattle Grace Cardiac Surgery
  - Phone: (710) 555-3082
  - Address: 456 Elm St, Charlotte, NC 28202
  - Hours: M-F 9am-5pm

### Perry, Chris
- Certification: FNP
- Specialty: Primary Care
- Department: Sacred Heart Surgical Department
  - Phone: (339) 555-7480
  - Address: 123 Main St, Raleigh, NC 27601
  - Hours: M-W 9am-5pm

### Brennan, Temperance
- Certification: PhD, MD
- Specialty: Orthopedics
- Department: Jefferson Hospital
  - Phone: (215) 555-6123
  - Address: 202 Maple St, Claremont, NC 28610
  - Hours: Tu-Th 10am-4pm

---

## Raw Data: Appointment Rules

From `MLChallenge/data_sheet.txt`:

### Timing
- Appointments can only be booked within office hours

### Types
- **NEW appointment:** 30 minutes long
- **ESTABLISHED appointment:** 15 minutes long
- An appointment is ESTABLISHED if the patient has been seen by the provider **in the last 5 years**
- Otherwise the appointment type is NEW

### Arrival
- New patients should arrive **30 minutes early**
- Established patients are encouraged to arrive **10 minutes** before appointment

> **CRITICAL NOTE on the 5-year rule:** The data sheet says "5 years." Real-world CMS/CPT billing standard is 3 years. For this challenge, use **5 years** as stated in the data sheet. In the presentation deck, mention the production discrepancy to show domain research.

> **CRITICAL NOTE on what counts:** Only **completed** appointments count toward the NEW/ESTABLISHED determination. No-shows and cancellations do NOT establish the patient relationship. This is not stated explicitly in the data sheet but is correct medical billing practice. Calling this out in the presentation demonstrates domain research.

---

## Raw Data: Insurance & Self-Pay

### Accepted Insurances
1. Medicaid
2. United Health Care
3. Blue Cross Blue Shield of North Carolina
4. Aetna
5. Cigna

### Self-Pay Rates (if insurance not accepted)
- Primary Care: $150
- Orthopedics: $300
- Surgery: $1,000

---

## Patient API Specification

**Source:** `MLChallenge/api/flask-app.py`

### Running the API
```bash
cd MLChallenge/api
pip install flask
python flask-app.py
# Starts at http://localhost:5000
```

### Endpoints

#### `GET /`
Health check. Returns `"Hello World"`.

#### `GET /patient/{patient_id}`
Returns patient data as JSON.

**Only patient_id = 1 is implemented.** Any other ID returns nothing (implicit 404).

**Response schema for patient 1:**
```json
{
  "id": 1,
  "name": "John Doe",
  "dob": "01/01/1975",
  "pcp": "Dr. Meredith Grey",
  "ehrId": "1234abcd",
  "referred_providers": [
    {"provider": "House, Gregory MD", "specialty": "Orthopedics"},
    {"specialty": "Primary Care"}
  ],
  "appointments": [
    {"date": "3/05/18", "time": "9:15am", "provider": "Dr. Meredith Grey", "status": "completed"},
    {"date": "8/12/24", "time": "2:30pm", "provider": "Dr. Gregory House", "status": "completed"},
    {"date": "9/17/24", "time": "10:00am", "provider": "Dr. Meredith Grey", "status": "noshow"},
    {"date": "11/25/24", "time": "11:30am", "provider": "Dr. Meredith Grey", "status": "cancelled"}
  ]
}
```

### Important API observations:
- `referred_providers[1]` has no `provider` field — only a `specialty`. This is intentional. The assistant must handle this by recommending from available providers of that specialty.
- Date format in appointments is `M/DD/YY` (e.g., `3/05/18`) — needs careful parsing.
- `pcp` field uses "Dr. Meredith Grey" but provider directory uses "Grey, Meredith". Need name normalization.

---

## John Doe — Full Patient Record

| Field | Value |
|-------|-------|
| ID | 1 |
| Name | John Doe |
| DOB | January 1, 1975 (age ~51 as of 2026) |
| PCP | Dr. Meredith Grey |
| EHR ID | 1234abcd |

### Referred Providers (from this hospital visit)
1. **House, Gregory MD** — Orthopedics (named provider)
2. **[No provider specified]** — Primary Care (nurse must be guided to select)

### Full Appointment History
| Date | Provider | Time | Status |
|------|---------|------|--------|
| March 5, 2018 | Dr. Meredith Grey | 9:15am | ✅ completed |
| August 12, 2024 | Dr. Gregory House | 2:30pm | ✅ completed |
| September 17, 2024 | Dr. Meredith Grey | 10:00am | ❌ no-show |
| November 25, 2024 | Dr. Meredith Grey | 11:30am | ❌ cancelled |

---

## Pre-Computed Business Logic for John Doe

These are the correct answers the system must produce. Use these for testing.

### Referral 1: Orthopedics with Dr. Gregory House
- Last completed appointment with Orthopedics specialty: **August 12, 2024**
- Today (as of challenge context): 2026
- 5-year window: Must be after ~2021
- August 2024 is within 5 years → **ESTABLISHED**
- Duration: **15 minutes**
- Arrival: **10 minutes early**
- Location options: PPTH Orthopedics (M-W) OR Jefferson Hospital (Th-F)

### Referral 2: Primary Care (provider TBD)
- Available Primary Care providers: Grey (M-F) or Perry (M-W)
- Last completed appointment with Primary Care: **March 5, 2018** (Grey)
- 5-year window: Must be after ~2021
- March 2018 is NOT within 5 years → **NEW**
- Duration: **30 minutes**
- Arrival: **30 minutes early**
- NOTE: Grey's no-show (9/17/24) and cancellation (11/25/24) do NOT count

### Why Grey's no-show doesn't reset the clock:
The last *completed* Primary Care visit is 3/5/2018. The 2024 interactions are not completed visits. The 5-year lookback from 2026 goes to ~2021. 2018 is before 2021, so this is a NEW appointment. This distinction must be explicit in code and explained to the nurse.

---

## Hidden Complexity / Data Traps

These are intentional traps in the data that most candidates will miss. Handling these distinguishes a senior submission.

| Trap | Location in Data | What Most Candidates Do | What You Should Do |
|------|-----------------|------------------------|-------------------|
| House has 2 locations | data_sheet.txt | Pick one arbitrarily | Ask nurse to choose; show both with hours |
| Referral with no provider | `referred_providers[1]` | Crash or skip | Detect missing `provider` field; recommend from specialty |
| No-shows don't count | appointment history | Count all visits for 5-year rule | Filter to `status == "completed"` only |
| Name format mismatch | API vs data sheet | String comparison fails | Normalize: "Dr. Gregory House" ↔ "House, Gregory MD" |
| Grey has recent cancelled visits | appointment history | Mark as ESTABLISHED | Last *completed* is 2018 → NEW |
| 5yr vs 3yr rule discrepancy | Challenge vs real world | Use one without acknowledging | Use 5yr (challenge), mention 3yr in deck |
| Brennan + House both at Jefferson | data_sheet.txt | Ignored | Mention as optimization (book same-day at same location) |

---

## Architecture Decision & Rationale

### Chosen: Tool-calling LLM agent + explicit session state

**The LLM is the least reliable component.** All business logic lives in deterministic Python. The LLM handles only: understanding natural language, deciding which tool to call, and narrating results back to the nurse.

### Why not Option A (stuff everything in system prompt)?
- Works for demo, fails in code review
- No separation of logic from language
- Can't test business rules independently
- Interviewer can't see engineering skill

### Why not Option C (LangChain / LangGraph)?
- Adds framework complexity you have to explain
- Over-engineered for a 5-tool, linear booking flow
- LangGraph state graph is impressive but harder to demo in 20 minutes

### Why Option B (raw tool-calling loop)?
- Every tool is a testable Python function
- Clear separation: LLM decides, deterministic code executes
- Easy to show in code review
- Scales to more tools without framework dependency
- The architecture diagram is clean and explainable

```
Nurse input
    ↓
FastAPI endpoint (POST /session/{id}/message)
    ↓
Session state loaded
    ↓
LLM called with: system prompt + patient context + conversation history + available tools
    ↓
LLM returns: tool call OR text response
    ↓
If tool call:
    → Execute tool (deterministic Python function)
    → Return structured result to LLM
    → LLM narrates result to nurse
If text response:
    → Return directly to nurse
    ↓
Session state updated
    ↓
Response returned to UI
```

---

## LLM Tool Design

Five tools. Each is a typed Python function. The LLM receives JSON schemas for each.

### Tool 1: `lookup_patient`
```python
def lookup_patient(patient_id: str) -> PatientData:
    """Call GET /patient/{id} from provided Flask API. Returns full patient record."""
```
LLM description: *"Use this to load a patient's complete record at the start of a session. Required before any other action."*

### Tool 2: `get_providers`
```python
def get_providers(specialty: str, insurance: Optional[str] = None) -> List[Provider]:
    """Returns providers from data sheet matching the given specialty."""
```
LLM description: *"Use this when a referral has no specific provider, or when the nurse asks who else is available for a specialty."*

### Tool 3: `check_availability`
```python
def check_availability(provider_name: str, day: Optional[str] = None, location: Optional[str] = None) -> AvailabilityResult:
    """Returns whether the provider is available, at which locations, on which days."""
```
LLM description: *"Use this when the nurse asks about a provider's schedule or wants to know if they're available on a specific day."*

### Tool 4: `determine_appointment_type`
```python
def determine_appointment_type(patient_id: str, provider_name: str, specialty: str) -> AppointmentTypeResult:
    """Returns NEW or ESTABLISHED based on 5-year completed-visit rule."""
```
LLM description: *"Use this automatically when a provider is selected to determine appointment type. Returns type, duration, arrival guidance, and the reasoning to show the nurse."*

### Tool 5: `check_insurance`
```python
def check_insurance(insurance_name: str, specialty: Optional[str] = None) -> InsuranceResult:
    """Returns whether insurance is accepted. If not, returns self-pay rate for the specialty."""
```
LLM description: *"Use this when the nurse asks about insurance, or before confirming a booking to proactively verify coverage."*

### Tool 6: `save_patient_preferences`
```python
def save_patient_preferences(patient_id: str, preferences: PatientPreferences) -> bool:
    """Saves patient contact and logistics preferences to the session."""
```
LLM description: *"Use this when the nurse fills out the preferences screen to save communication and logistics preferences for follow-up coordination."*

### Key principle: Tool parameter descriptions are written FOR the LLM
Every parameter in each tool's schema must include a `description` field that tells the LLM *when* to set it and *what values are valid*. This is prompt engineering inside the tool definition.

---

## Session State Design

```python
class BookingSession:
    # Identity
    session_id: str                      # UUID
    created_at: datetime
    nurse_id: Optional[str]

    # Current step in the workflow
    step: Literal[
        "patient_lookup",
        "referrals_overview",
        "provider_selection",
        "appointment_details",
        "preferences",
        "confirmation",
        "complete"
    ]

    # Patient context (loaded from API)
    patient: Optional[PatientData]

    # Multi-referral tracking
    referrals: List[ReferralStatus]      # one per referred_provider
    active_referral_index: int           # which referral is being booked now
    completed_bookings: List[CompletedBooking]

    # Current booking in progress (reset between referrals)
    selected_provider: Optional[Provider]
    appointment_type: Optional[str]      # "NEW" or "ESTABLISHED"
    appointment_type_reasoning: Optional[str]
    selected_location: Optional[Department]

    # Patient preferences (captured once, reused)
    patient_preferences: Optional[PatientPreferences]

    # Conversation history (for LLM context)
    messages: List[ChatMessage]
```

### State transitions:
- `patient_lookup` → `referrals_overview` (after patient confirmed)
- `referrals_overview` → `provider_selection` (nurse clicks "Book This")
- `provider_selection` → `appointment_details` (provider selected)
- `appointment_details` → `preferences` (location chosen)
- `preferences` → `confirmation` (preferences saved)
- `confirmation` → `referrals_overview` (booking confirmed, back for next referral)
- `referrals_overview` → `complete` (all referrals processed)

### Mid-flow "change provider":
Reset: `selected_provider`, `appointment_type`, `appointment_type_reasoning`, `selected_location`
Keep: `patient`, `patient_preferences`, `completed_bookings`, conversation history

---

## Nurse Workflow — 7-Screen Flow

The UI is a step-by-step wizard. The chat assistant is always available on every screen.

1. **Screen 1 — Patient Lookup:** Enter patient ID → load and confirm patient identity
2. **Screen 2 — Referrals Overview:** See all referrals at a glance, pick which to book
3. **Screen 3 — Provider Selection:** Confirm or select provider; alternatives shown inline proactively
4. **Screen 4 — Appointment Details:** Auto-determined type shown with reasoning; location selection
5. **Screen 5 — Patient Preferences:** Contact method, best time, transportation, language, notes
6. **Screen 6 — Booking Confirmation:** Full summary card; explicit confirm required
7. **Screen 7 — Session Complete:** All bookings listed; follow-up plan noted

### Proactive alternative surfacing rule:
The assistant never lets a nurse hit a dead end. On every screen where failure is possible, alternatives are shown *before* the nurse asks.

---

## Patient Preferences Module

```python
class PatientPreferences:
    patient_id: str
    contact_method: Literal["phone", "text", "email"]
    best_contact_time: Literal["morning", "afternoon", "evening"]
    language: str                        # default "English"
    location_preference: Literal["home", "work", "none"]
    transportation_needs: bool
    notes: str
    created_at: datetime
    updated_at: datetime
    last_nurse_id: Optional[str]
```

### Why this module exists (business justification):
The primary goal is **maximum bookings that are actually attended**. Preferences drive:
- Reminder channel (text vs. phone vs. email) → personalized follow-up
- Transportation flag → proactively offer transport resources, reducing no-shows
- Language preference → route interpreter if needed
- Location preference → auto-rank location options for multi-location providers
- Notes → carry care coordination context across sessions

### Follow-up touch points (maximizing attendance):
1. Immediately after booking: confirmation via preferred channel
2. 48 hours before: reminder with location details
3. Day-of: "Arrive X minutes early at [address]"
4. 24 hours after: status check, update appointment history

---

## Industry Research Findings

*Sources gathered during project planning on 2026-03-24.*

### LLM Booking Agent Patterns
- **Production pattern:** Hybrid orchestration. LLM handles language; deterministic tools handle all state mutations. LLM never directly writes data.
- **Tool schemas as prompts:** Parameter `description` fields in tool schemas are critical — they tell the LLM when and how to use each parameter. This is often overlooked.
- **Confirmation before write:** Every production booking system requires an explicit confirmation step before any write operation. This is the single highest-signal indicator of production thinking.

Sources:
- [Building an AI-Powered Appointment Chatbot for a Children's Healthcare Clinic](https://medium.com/@roger.richards07/building-an-ai-powered-appointment-chatbot-for-a-childrens-healthcare-clinic-using-java-b80c7b3cdbe0)
- [Appointment Booking Assistant — Azure AI Foundry Blog](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/appointment-booking-assistant%E2%80%94an-ai-powered-voice-agent/4408554)
- [Enhancing patient experience: AI-driven healthcare scheduling on AWS](https://aws.amazon.com/blogs/industries/enhancing-patient-experience-ai-driven-healthcare-scheduling-on-aws/)
- [Voice AI for Healthcare Appointment Scheduling: The Complete Guide (2026)](https://droidal.com/blog/voice-ai-healthcare-appointment-scheduling-guide/)

### NEW vs. ESTABLISHED — Real World Standard
- **Challenge rule:** 5 years (as stated in data_sheet.txt — use this for implementation)
- **Real world CMS/CPT standard:** 3 years — a new patient is one who has *not* received professional services from the physician, or another physician of the exact same specialty/subspecialty in the same group practice, within the past **3 years**
- **Key nuances (for presentation deck, not implementation):**
  - Rule is per specialty, not per individual provider
  - Only face-to-face professional services count (not lab results, phone consults)
  - Same group practice (same tax ID) = same practice for this determination
  - Billing codes: New = 99202–99205, Established = 99211–99215. Mismatch causes claim denials.

Sources:
- [AAPC: New vs. Established Patients](https://www.aapc.com/blog/41276-new-vs-established-patients-whos-new-to-you/)
- [Noridian Medicare: New vs Established Patient Visit](https://med.noridianmedicare.com/web/jeb/specialties/em/new-vs-established-patient)

### Multi-Step LLM Conversation State
- Keep explicit state object; don't rely on conversation history alone
- State object injected into system prompt or tool context every turn
- State updated by tool results, not by LLM text parsing
- For session persistence: Redis in production, in-memory dict for demo (name the abstraction `SessionStore` to signal intent)

Sources:
- [Multi-Step LLM Chains: Best Practices](https://deepchecks.com/orchestrating-multi-step-llm-chains-best-practices/)

### Structured LLM Output
- `instructor` library + Pydantic is industry standard for typed LLM outputs
- Alternative: native structured outputs from Claude or OpenAI

Sources:
- [Instructor — Structured LLM Outputs](https://python.useinstructor.com/)

### What Interviewers Look For in LLM Take-Home Challenges
1. **Structured tool/function calling** — not just prompting
2. **Business logic separation** — deterministic code, not LLM guessing
3. **Domain research** — did you read the data carefully? Did you find the traps?
4. **Confirmation step** — do you understand write operations need explicit confirmation?
5. **Error handling** — what happens when things go wrong?
6. **Presentation deck quality** — architecture diagram, state machine, edge case table

---

## Tech Stack Decisions

| Layer | Choice | Why |
|-------|--------|-----|
| LLM | Claude claude-sonnet-4-6 (Anthropic) | Excellent tool calling, well-documented, reliable structured output |
| LLM alternative | OpenAI GPT-4o | Equally good tool calling; either is acceptable |
| Backend | FastAPI (Python) | Async, auto-docs, Pydantic-native, type-safe |
| Data validation | Pydantic v2 | All models typed; validation at boundaries |
| LLM orchestration | Raw tool-calling loop | No framework overhead; readable; easy to present |
| Patient API | Provided Flask app (run as-is) | Use what was given; shows you respected the materials |
| State | In-memory dict + session UUID | Sufficient for demo; name it `SessionStore` for Redis-swap intent |
| Frontend | Plain React + fetch | Functional; not the focus of the challenge |
| Tests | pytest | Standard |

**Avoid:** LangChain chains — too much abstraction for a linear 5-tool flow. Hard to explain in a 20-minute demo.

---

## Parallel Build Structure

The basic tier is split into 5 independent git worktree branches:

### Part 1 — Data Layer & Business Logic
Branch: `feature/data-layer`

All Pydantic models + deterministic business logic. No HTTP, no LLM.
- `app/models/` — PatientData, Provider, Department, BookingSession, PatientPreferences
- `app/data/` — hardcoded provider directory, insurance list (parsed from data_sheet.txt)
- `app/logic/` — appointment_type.py, availability.py, insurance.py, provider_search.py

Key tests:
- House + 8/12/24 → ESTABLISHED
- Grey + 3/5/18 (no-shows don't count) → NEW
- House Monday → PPTH Orthopedics available
- House Thursday → Jefferson Hospital available
- Aetna → accepted
- Anthem → not accepted + $300 self-pay (Orthopedics)

### Part 2 — Patient API Client
Branch: `feature/patient-api`

HTTP client for the Flask API.
- `app/api/patient_client.py` — `get_patient(id)` → `PatientData`
- `app/api/exceptions.py` — `PatientNotFound`, `APIUnavailable`

### Part 3 — LLM Tool Layer
Branch: `feature/llm-tools`

LLM client + 6 tool definitions + system prompt.
- `app/llm/client.py` — LLM client, tool call execution loop
- `app/llm/tools.py` — 6 tool schemas + dispatcher
- `app/llm/prompts.py` — system prompt template + patient context injector
- `app/llm/tool_executor.py` — maps LLM tool calls → Part 1 functions

### Part 4 — FastAPI Server & Session Management
Branch: `feature/api-server`

HTTP server wiring together Parts 1, 2, 3.
Endpoints:
- `POST /session` — create session
- `POST /session/{id}/start/{patient_id}` — load patient
- `POST /session/{id}/message` — send message, get response
- `GET /session/{id}/state` — get current session state
- `POST /session/{id}/preferences` — save preferences
- `POST /session/{id}/confirm-booking` — finalize booking
- `GET /session/{id}/summary` — all bookings in session

### Part 5 — Frontend UI
Branch: `feature/frontend`

7-screen wizard in plain React or HTML.
- All 7 screens as described in Nurse Workflow
- ChatPanel component on all screens
- ProviderCard component with availability + insurance status
- BookingSummaryCard for Screen 6
- Calls FastAPI backend via `fetch`

### Integration order:
```
Part 1 (Data Layer)  ←── must be first (or mocked)
    ↓
Part 2 (API Client)  ←── parallel with Part 3
Part 3 (LLM Tools)   ←── parallel with Part 2
    ↓
Part 4 (FastAPI)     ←── integrates 1 + 2 + 3
    ↓
Part 5 (Frontend)    ←── calls Part 4
```

---

## Edge Cases Registry

| # | Edge Case | Data Evidence | Correct Behavior |
|---|-----------|--------------|-----------------|
| 1 | Provider at 2 locations | House: PPTH + Jefferson | Show both upfront with hours; nurse picks first |
| 2 | Referral with no provider | `referred_providers[1].provider` missing | Query by specialty; recommend options |
| 3 | No-shows don't count | Grey 9/17/24 noshow | Filter `status == "completed"` only |
| 4 | Cancellations don't count | Grey 11/25/24 cancelled | Same filter |
| 5 | Last completed > 5 years | Grey 3/5/18 | NEW even though she's PCP |
| 6 | Name format mismatch | "Dr. Gregory House" vs "House, Gregory MD" | Normalize on load |
| 7 | Insurance not in list | Any insurance not in the 5 listed | Return self-pay rate + clear message |
| 8 | Patient not found | Any ID other than 1 | Friendly error, don't crash |
| 9 | Flask API down | If not running | `APIUnavailable` error → graceful UI |
| 10 | Mid-flow provider change | Nurse says "actually different doctor" | Reset provider/type/location; keep patient |
| 11 | Preferred time outside hours | Nurse asks for weekend | "Dr. X is not available then. Available: [list]" |
| 12 | Same building, two providers | House + Brennan both at Jefferson | (Advanced) Suggest booking same day |

---

## What NOT to Do

- **Don't use LangChain chains** — over-engineered for this use case; hard to present
- **Don't trust LLM to remember state** — inject session state explicitly every turn
- **Don't count no-shows/cancellations** toward the 5-year rule
- **Don't hard-code "House is at PPTH"** — parse location from provider data dynamically
- **Don't skip the confirmation step** — any write action needs explicit nurse confirm
- **Don't send raw PHI to third-party LLM without noting the HIPAA consideration** (mention in deck)
- **Don't build an overly complex UI** — the challenge is about LLM + business logic, not UI polish
- **Don't skip explaining appointment type to the nurse** — show the reasoning, not just the label

---

## Production Considerations (for Presentation)

These are not implemented in the demo but must be mentioned in the presentation deck to demonstrate senior thinking:

### PHI / HIPAA
- Patient names, DOBs, appointment histories are **PHI under HIPAA**
- Production options: (a) Use a HIPAA BAA-covered LLM API endpoint, or (b) de-identify data before sending to third-party LLM
- For this demo: noted as a trade-off, not implemented

### EHR Integration
- Real scheduling would integrate with EHR calendar via **HL7 FHIR R4**
- Relevant FHIR resources: `Slot` (availability), `Appointment` (booking), `Patient`, `Practitioner`
- The `booking confirmation` step in demo would call `POST /Appointment` in production

### Slot Availability
- The demo doesn't have real calendar data — only office hours
- Production: query real calendar slots, show specific available times (e.g., Mon 10am, Mon 2pm)

### No-Show Reduction
- After appointment date passes: flag unconfirmed appointments for follow-up call
- Track no-show patterns (Grey has 1 no-show) → proactive intervention

### Multi-Patient / Multi-Nurse
- Current design: one session per nurse session
- Production: session keyed by nurse ID + patient ID, concurrent session handling, Redis for state

### Audit Logging
- Every tool call logged: `{timestamp, session_id, nurse_id, tool, input, output}`
- Healthcare requires audit trails for all patient data access

### Real-World 3-Year Rule
- Challenge says 5 years; CMS/CPT standard is 3 years
- Note this discrepancy in the deck to show domain research and production awareness

---

*Context compiled: 2026-03-24*
*Challenge: Kouper Health ML Interview — Mini Care Coordinator Assistant*
*All raw data from: `MLChallenge/data_sheet.txt`, `MLChallenge/api/flask-app.py`, `MLChallenge/KouperHealthMLChallenge.pdf`*
