from typing import Optional
from ..data.providers import PROVIDERS
from ..data.insurance import ACCEPTED_INSURANCES, SELF_PAY_RATES

def build_provider_directory() -> str:
    lines = []
    for p in PROVIDERS:
        lines.append(f"- {p.last_name}, {p.first_name} {p.certification} | {p.specialty}")
        for dept in p.departments:
            lines.append(f"  • {dept.name} | {dept.address} | {dept.phone} | {dept.hours}")
    return "\n".join(lines)

def build_system_prompt(patient_context: Optional[str] = None) -> str:
    insurances = "\n".join(f"- {ins}" for ins in ACCEPTED_INSURANCES)
    rates = "\n".join(f"- {spec}: ${rate:.0f}" for spec, rate in SELF_PAY_RATES.items())
    context = patient_context or "No patient loaded yet."
    return f"""You are a Care Coordinator Assistant helping nurses book appointments for patients following hospital discharge.

## Provider Directory
{build_provider_directory()}

## Appointment Rules
- NEW: 30 minutes, patient arrives 30 minutes early
- ESTABLISHED: 15 minutes, patient arrives 10 minutes early
- ESTABLISHED if patient had a COMPLETED visit in the same specialty within 5 years
- No-shows and cancellations do NOT count — only completed visits

## Accepted Insurances
{insurances}

## Self-Pay Rates (when insurance not accepted)
{rates}

## Your Role
Guide the nurse step by step. Use tools for accurate data — never guess. Proactively surface alternatives. Always include arrival time guidance. Flag any no-show history.

## Current Patient Context
{context}"""

def build_patient_context(patient: Optional[dict]) -> str:
    if not patient:
        return "No patient loaded."
    lines = [f"Patient: {patient.get('name')} | DOB: {patient.get('dob')} | PCP: {patient.get('pcp')}"]
    lines.append("Referred providers:")
    for r in patient.get("referred_providers", []):
        lines.append(f"  - {r.get('provider') or 'TBD'} ({r.get('specialty')})")
    lines.append("Appointment history:")
    for a in patient.get("appointments", []):
        lines.append(f"  - {a.get('date')} | {a.get('provider')} | {a.get('status')}")
    return "\n".join(lines)
