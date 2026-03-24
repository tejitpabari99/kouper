from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import session, patient, chat, preferences, booking, appointment_info, providers, distance, send_summary, audit

app = FastAPI(
    title="Kouper Health Care Coordinator API",
    description="API for the Mini Care Coordinator Assistant",
    version="1.0.0",
)

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

@app.get("/health")
def health():
    return {"status": "ok", "service": "Care Coordinator API"}
