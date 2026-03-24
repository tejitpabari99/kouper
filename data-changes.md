# Data Changes

This file documents all invented or assumed data added to the system.

## Patient Records (MLChallenge/api/flask-app.py)

### Patient 1 — John Doe (existing, augmented)
- Added `phone`: (555) 201-4837
- Added `email`: john.doe@example.com
- Added `insurance`: Blue Cross Blue Shield

### Patient 2 — Maria Santos (new)
- `dob`: 06/14/1988
- `phone`: (555) 374-9102
- `email`: maria.santos@example.com
- `pcp`: Dr. Chris Perry
- `ehrId`: 5678efgh
- `insurance`: Aetna
- Referred providers: Cristina Yang (Surgery), Primary Care (unnamed)
- Appointment history: completed Surgery visit (1/10/22), completed Primary Care (7/22/23), Surgery no-show (2/14/25)

### Patient 3 — Robert Kim (new)
- `dob`: 11/30/1960
- `phone`: (555) 489-7263
- `email`: robert.kim@example.com
- `pcp`: Dr. Meredith Grey
- `ehrId`: 9012ijkl
- `insurance`: Self-Pay
- Referred providers: Temperance Brennan (Orthopedics), Surgery (unnamed)
- Appointment history: completed Orthopedics visit (5/03/15, outside 5-year window → NEW), completed Primary Care (4/19/20), Orthopedics cancelled (8/08/24)

## Notes
- All phone numbers are fictional (555-xxxx format)
- All emails are fictional (@example.com domain)
- Patient 3's most recent completed Orthopedics appointment (5/03/15) is beyond the 5-year window from today (2026-03-24), so they would be classified as NEW for Orthopedics
