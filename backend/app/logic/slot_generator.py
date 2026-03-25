"""
Appointment slot generator — produces a browsable grid of time slots.

Given a provider and location, generates all available appointment start times
across the next N weeks based on the provider's working days and hours.  Slots
are grouped by week for display in the UI's slot picker component.

Note: this is a purely computed schedule — there is no real availability/booking
system behind it.  Slots represent when the provider *could* see patients based
on their listed hours, not confirmed open slots.
"""
from datetime import date, timedelta
from typing import List, Dict, Tuple
from pydantic import BaseModel

from app.data.providers import PROVIDERS
from app.logic.availability import _find_provider, _parse_days, _parse_hours_time


DAY_NAME_TO_WEEKDAY = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2,
    "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6,
}


class AppointmentSlot(BaseModel):
    date: str
    day_name: str
    start_time: str
    end_time: str
    display: str


class SlotGroup(BaseModel):
    week_label: str
    slots: List[AppointmentSlot]


def _parse_hour(time_str: str) -> int:
    """Convert a 12-hour time string like '9am' or '5pm' to a 24-hour integer."""
    t = time_str.strip().lower()
    if t.endswith('am'):
        h = int(t[:-2])
        return 0 if h == 12 else h
    elif t.endswith('pm'):
        h = int(t[:-2])
        return h if h == 12 else h + 12
    return int(t)


def _fmt12(hour: int, minute: int) -> str:
    """Format a 24-hour hour/minute pair as a 12-hour display string (e.g. '9:00 AM')."""
    p = "AM" if hour < 12 else "PM"
    h = hour % 12 or 12
    return f"{h}:{minute:02d} {p}"


def generate_slots(
    provider_name: str,
    location_name: str,
    duration_minutes: int = 30,
    weeks_ahead: int = 3,
) -> List[SlotGroup]:
    """
    Generate appointment slots for a provider/location over the next N weeks.

    Walks each day in the window and generates back-to-back slots of
    duration_minutes from the provider's opening time to closing time.
    Slots are grouped into SlotGroup objects keyed by calendar week with
    human-readable labels ("This week", "Next week", or a date range).

    Falls back to the provider's first department if location_name is not matched,
    so the UI still gets results even with a loose location string.
    """
    provider = _find_provider(provider_name)
    if not provider:
        return []

    dept = next((d for d in provider.departments if d.name.lower() == location_name.lower()), None)
    if not dept and provider.departments:
        dept = provider.departments[0]
    if not dept:
        return []

    valid_day_names = _parse_days(dept.hours)
    time_range = _parse_hours_time(dept.hours)
    parts = time_range.split("-")
    if len(parts) != 2:
        return []

    open_h = _parse_hour(parts[0])
    close_h = _parse_hour(parts[1])
    valid_wds = {DAY_NAME_TO_WEEKDAY[d] for d in valid_day_names if d in DAY_NAME_TO_WEEKDAY}

    today = date.today()
    groups: List[Tuple[str, str, List[AppointmentSlot]]] = []  # (week_key, label, slots)
    week_index: Dict[str, int] = {}

    current = today + timedelta(days=1)
    end = today + timedelta(weeks=weeks_ahead)

    while current <= end:
        if current.weekday() in valid_wds:
            h, m = open_h, 0
            day_slots = []
            while True:
                end_total = h * 60 + m + duration_minutes
                eh, em = end_total // 60, end_total % 60
                if eh > close_h or (eh == close_h and em > 0):
                    break
                day_slots.append(AppointmentSlot(
                    date=current.isoformat(),
                    day_name=current.strftime("%A"),
                    start_time=f"{h:02d}:{m:02d}",
                    end_time=f"{eh:02d}:{em:02d}",
                    display=f"{current.strftime('%a %b %-d')} · {_fmt12(h, m)} – {_fmt12(eh, em)}",
                ))
                total = h * 60 + m + duration_minutes
                h, m = total // 60, total % 60

            if day_slots:
                wstart = current - timedelta(days=current.weekday())
                wend = wstart + timedelta(days=6)
                wkey = wstart.isoformat()
                if wkey not in week_index:
                    tw = today - timedelta(days=today.weekday())
                    if wstart == tw:
                        lbl = f"This week ({wstart.strftime('%b %-d')}–{wend.strftime('%-d')})"
                    elif wstart == tw + timedelta(weeks=1):
                        lbl = f"Next week ({wstart.strftime('%b %-d')}–{wend.strftime('%-d')})"
                    else:
                        lbl = f"{wstart.strftime('%b %-d')}–{wend.strftime('%b %-d')}"
                    week_index[wkey] = len(groups)
                    groups.append((wkey, lbl, []))
                groups[week_index[wkey]][2].extend(day_slots)

        current += timedelta(days=1)

    return [SlotGroup(week_label=lbl, slots=slots) for _, lbl, slots in groups]
