# app.py
from flask import Flask, jsonify, request

app = Flask(__name__)

PATIENTS = {
    1: {
        "id": 1,
        "name": "John Doe",
        "dob": "01/01/1975",
        "phone": "(555) 201-4837",
        "email": "john.doe@example.com",
        "pcp": "Dr. Meredith Grey",
        "ehrId": "1234abcd",
        "referred_providers": [
            {"provider": "House, Gregory MD", "specialty": "Orthopedics"},
            {"specialty": "Primary Care"},
        ],
        "appointments": [
            {"date": "3/05/18", "time": "9:15am", "provider": "Dr. Meredith Grey", "status": "completed"},
            {"date": "8/12/24", "time": "2:30pm", "provider": "Dr. Gregory House", "status": "completed"},
            {"date": "9/17/24", "time": "10:00am", "provider": "Dr. Meredith Grey", "status": "noshow"},
            {"date": "11/25/24", "time": "11:30am", "provider": "Dr. Meredith Grey", "status": "cancelled"}
        ],
        "insurance": "Blue Cross Blue Shield",
    },
    2: {
        "id": 2,
        "name": "Maria Santos",
        "dob": "06/14/1988",
        "phone": "(555) 374-9102",
        "email": "maria.santos@example.com",
        "pcp": "Dr. Chris Perry",
        "ehrId": "5678efgh",
        "referred_providers": [
            {"provider": "Yang, Cristina MD", "specialty": "Surgery"},
            {"specialty": "Primary Care"},
        ],
        "appointments": [
            {"date": "1/10/22", "time": "11:00am", "provider": "Dr. Cristina Yang", "status": "completed"},
            {"date": "7/22/23", "time": "9:00am", "provider": "Dr. Chris Perry", "status": "completed"},
            {"date": "2/14/25", "time": "3:00pm", "provider": "Dr. Cristina Yang", "status": "noshow"},
        ],
        "insurance": "Aetna",
    },
    3: {
        "id": 3,
        "name": "Robert Kim",
        "dob": "11/30/1960",
        "phone": "(555) 489-7263",
        "email": "robert.kim@example.com",
        "pcp": "Dr. Meredith Grey",
        "ehrId": "9012ijkl",
        "referred_providers": [
            {"provider": "Brennan, Temperance PhD, MD", "specialty": "Orthopedics"},
            {"specialty": "Surgery"},
        ],
        "appointments": [
            {"date": "5/03/15", "time": "10:30am", "provider": "Dr. Temperance Brennan", "status": "completed"},
            {"date": "4/19/20", "time": "2:00pm", "provider": "Dr. Meredith Grey", "status": "completed"},
            {"date": "8/08/24", "time": "8:45am", "provider": "Dr. Temperance Brennan", "status": "cancelled"},
        ],
        "insurance": "Self-Pay",
    },
}


@app.route('/', methods=['GET'])
def healthcheck():
    return jsonify("Hello World")


@app.route('/patient/<patient_id>', methods=['GET'])
def get_data(patient_id):
    pid = int(patient_id)
    patient = PATIENTS.get(pid)
    if patient:
        return jsonify(patient)
    return jsonify({"error": f"Patient {patient_id} not found"}), 404


@app.route('/patients', methods=['GET'])
def search_patients():
    q = request.args.get('q', '').strip()

    results = []
    for patient in PATIENTS.values():
        if not q:
            match = True
        elif q.isdigit() and int(q) == patient['id']:
            match = True
        else:
            q_lower = q.lower()
            match = (
                q_lower in patient['name'].lower()
                or q_lower in patient.get('phone', '').lower()
                or q_lower in patient.get('email', '').lower()
            )

        if match:
            results.append({
                "id": patient['id'],
                "name": patient['name'],
                "dob": patient['dob'],
                "phone": patient.get('phone'),
                "email": patient.get('email'),
            })

    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True)
