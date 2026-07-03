import uuid


def unique_email(prefix: str = "doctor") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def doctor_payload(**overrides) -> dict:
    payload = {
        "email": unique_email(),
        "password": "SecurePass1",
        "first_name": "Alice",
        "last_name": "Smith",
        "specialty": "Orthopedics",
        "license_number": "LIC-001",
        "clinic_name": "Spine Clinic",
        "country": "US",
        "city": "Boston",
    }
    payload.update(overrides)
    return payload


def patient_payload(**overrides) -> dict:
    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1990-01-15",
        "gender": "female",
        "height_cm": 165.0,
        "weight_kg": 60.0,
        "medical_record_number": f"MRN-{uuid.uuid4().hex[:6]}",
    }
    payload.update(overrides)
    return payload
