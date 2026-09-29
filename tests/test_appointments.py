"""Appointment workflow unit and integration tests."""
from datetime import date, timedelta


def test_book_appointment_success(client):
    client.post("/auth/login", data={"email": "aarav@medtrack.demo", "password": "Patient@12345"})
    booking_date = (date.today() + timedelta(days=2)).isoformat()
    # Wednesday is available for Dr. Rohan (dr_rohan)
    res = client.post("/appointments/book/dr_rohan", data={
        "date": booking_date,
        "time": "14:00",
        "reason": "General health assessment",
        "mode": "In-person"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"General health assessment" in res.data


def test_book_appointment_past_date_fails(client):
    client.post("/auth/login", data={"email": "aarav@medtrack.demo", "password": "Patient@12345"})
    past_date = (date.today() - timedelta(days=2)).isoformat()
    res = client.post("/appointments/book/dr_rohan", data={
        "date": past_date,
        "time": "14:00",
        "reason": "Past date check",
        "mode": "In-person"
    })
    assert res.status_code == 400
    assert b"past" in res.data


def test_doctor_accept_appointment(client, app):
    # Patient books
    client.post("/auth/login", data={"email": "ananya@medtrack.demo", "password": "Patient@12345"})
    booking_date = (date.today() + timedelta(days=3)).isoformat()
    client.post("/appointments/book/dr_rohan", data={
        "date": booking_date,
        "time": "09:00",
        "reason": "Dermatology advice",
        "mode": "In-person"
    })
    repo = app.extensions["repository"]
    appt = next(a for a in repo.appointments.values() if a["patient_id"] == "pat_ananya" and a["time"] == "09:00")

    # Doctor logs in and accepts
    client.post("/auth/logout")
    client.post("/auth/login", data={"email": "rohan@medtrack.demo", "password": "Doctor@12345"})
    res = client.post(f"/appointments/{appt['id']}/accept", follow_redirects=True)
    assert res.status_code == 200
    assert repo.appointments[appt["id"]]["status"] == "confirmed"


def test_health_check_api(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json.get("status") == "healthy"


def test_get_slots_for_doctor(client):
    client.post("/auth/login", data={"email": "aarav@medtrack.demo", "password": "Patient@12345"})
    # Find next weekday
    day_offset = 1
    while (date.today() + timedelta(days=day_offset)).strftime("%A") in ["Saturday", "Sunday"]:
        day_offset += 1
    test_date = (date.today() + timedelta(days=day_offset)).isoformat()

    res = client.get(f"/appointments/slots/dr_rohan/{test_date}")
    assert res.status_code == 200
    slots = res.json
    assert isinstance(slots, list)
    assert len(slots) > 0
    assert "time" in slots[0]
    assert "display_time" in slots[0]
    assert "available" in slots[0]

