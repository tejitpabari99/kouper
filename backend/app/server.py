import time, re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .routes import session, patient, chat, preferences, booking, appointment_info, providers, distance, send_summary, audit, transport, outcomes, feedback, slots, insurance
from .database import init_db

app = FastAPI(
    title="Kouper Health Care Coordinator API",
    description="API for the Mini Care Coordinator Assistant",
    version="1.0.0",
)

init_db()

@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    try:
        # Extract session_id from paths like /session/{uuid}/...
        path = str(request.url.path)
        session_match = re.search(r'/session/([0-9a-f-]{36})', path)
        sid = session_match.group(1) if session_match else None
        # Skip audit log endpoint itself to avoid recursion
        if not path.startswith('/audit'):
            from .audit_log import append_audit_entry, AuditLogEntry
            append_audit_entry(AuditLogEntry(
                timestamp=__import__('datetime').datetime.utcnow().isoformat() + "Z",
                type="api",
                actor="api",
                session_id=sid,
                http_method=request.method,
                http_path=path,
                http_status=response.status_code,
                duration_ms=int((time.time() - start) * 1000),
            ))
    except Exception:
        pass  # audit must never crash requests
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session.router)
app.include_router(patient.router)
app.include_router(patient.router2)
app.include_router(chat.router)
app.include_router(preferences.router)
app.include_router(booking.router)
app.include_router(appointment_info.router)
app.include_router(providers.router)
app.include_router(distance.router)
app.include_router(send_summary.router)
app.include_router(audit.router)
app.include_router(transport.router)
app.include_router(outcomes.router)
app.include_router(feedback.router)
app.include_router(slots.router)
app.include_router(insurance.router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "Care Coordinator API"}
