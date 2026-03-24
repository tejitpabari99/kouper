class PatientNotFound(Exception):
    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        super().__init__(f"Patient {patient_id} not found")

class APIUnavailable(Exception):
    def __init__(self, message: str = "Patient API is unavailable"):
        super().__init__(message)
