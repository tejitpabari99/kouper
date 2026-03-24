"""
Persistent store for appointment outcomes. Mirrors session_store.py pattern,
persists to .appointment_outcomes.json alongside .sessions.json.
"""
import json
import os
from typing import List, Optional

from .models.appointment import AppointmentOutcome

OUTCOMES_FILE = os.path.join(os.path.dirname(__file__), "../../.appointment_outcomes.json")


def _load() -> List[dict]:
    try:
        with open(OUTCOMES_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save(outcomes: List[dict]) -> None:
    with open(OUTCOMES_FILE, "w") as f:
        json.dump(outcomes, f, indent=2)


def add_outcome(outcome: AppointmentOutcome) -> None:
    outcomes = _load()
    outcomes.append(outcome.model_dump())
    _save(outcomes)


def get_outcomes_for_patient(patient_id: str) -> List[AppointmentOutcome]:
    outcomes = _load()
    return [
        AppointmentOutcome(**o)
        for o in outcomes
        if o.get("patient_id") == patient_id
    ]


def get_all_outcomes() -> List[AppointmentOutcome]:
    return [AppointmentOutcome(**o) for o in _load()]
