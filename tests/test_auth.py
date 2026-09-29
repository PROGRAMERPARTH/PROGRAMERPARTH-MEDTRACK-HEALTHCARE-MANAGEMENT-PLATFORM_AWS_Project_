"""Authentication and authorization tests."""
import pytest


def test_landing_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Healthcare Management" in response.data


def test_login_patient(client):
    res = client.post("/auth/login", data={"email": "aarav@medtrack.demo", "password": "Patient@12345"}, follow_redirects=True)
    assert res.status_code == 200
    assert "Aarav Sharma" in response_text(res)


def test_login_doctor(client):
    res = client.post("/auth/login", data={"email": "rohan@medtrack.demo", "password": "Doctor@12345"}, follow_redirects=True)
    assert res.status_code == 200
    assert "Doctor Portal" in response_text(res)


def test_login_admin(client):
    res = client.post("/auth/login", data={"email": "admin@medtrack.demo", "password": "Admin@12345"}, follow_redirects=True)
    assert res.status_code == 200
    assert "Administration Console" in response_text(res)


def test_invalid_password(client):
    res = client.post("/auth/login", data={"email": "aarav@medtrack.demo", "password": "WrongPassword!"})
    assert res.status_code == 401
    assert b"Invalid email or password" in res.data


def test_patient_registration(client):
    new_email = "newpatient@medtrack.demo"
    res = client.post("/auth/register", data={
        "role": "patient",
        "name": "Kavita Rao",
        "email": new_email,
        "phone": "+91 91234 56789",
        "dob": "1995-08-20",
        "gender": "female",
        "address": "Bangalore, Karnataka",
        "emergency_contact": "Ramesh Rao (+91 91234 00000)",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert "Kavita Rao" in response_text(res)


def test_doctor_registration_and_admin_approval_workflow(client, app):
    doc_email = "dr.sharma@medtrack.demo"
    doc_pass = "DoctorPass123!"

    # 1. Doctor registers on portal
    res = client.post("/auth/register", data={
        "role": "doctor",
        "name": "Sunil Sharma",
        "email": doc_email,
        "phone": "+91 98765 11111",
        "specialization": "Cardiologist",
        "qualification": "MBBS, MD Cardiology",
        "experience": "10",
        "clinic": "Metro Heart Hospital",
        "location": "Bengaluru",
        "fee": "800",
        "consultation_mode": "In-person & Video",
        "available_days": ["Monday", "Wednesday", "Friday"],
        "bio": "Experienced cardiologist with focus on preventive care.",
        "password": doc_pass,
        "confirm_password": doc_pass
    }, follow_redirects=True)
    assert res.status_code == 200
    assert "pending admin review" in response_text(res) or "approved" in response_text(res)

    repo = app.extensions["repository"]
    user = repo.get_user_by_email(doc_email)
    assert user is not None
    assert user["status"] == "pending"
    doctor_id = user["doctor_id"]
    doc_obj = repo.doctors[doctor_id]
    assert doc_obj["verification_status"] == "Pending Approval"

    # 2. Doctor attempts to log in before approval -> 403 Forbidden
    login_res = client.post("/auth/login", data={"email": doc_email, "password": doc_pass}, follow_redirects=True)
    assert login_res.status_code == 403
    assert "pending admin approval" in response_text(login_res)

    # 3. Admin logs in and reviews doctor directory
    client.post("/auth/logout")
    client.post("/auth/login", data={"email": "admin@medtrack.demo", "password": "Admin@12345"})

    # Admin visits pending doctors list
    admin_docs_res = client.get("/admin/doctors?status=pending")
    assert admin_docs_res.status_code == 200
    assert "Dr. Sunil Sharma" in response_text(admin_docs_res)

    # Admin approves the doctor
    approve_res = client.post(f"/admin/doctors/{doctor_id}/approve", follow_redirects=True)
    assert approve_res.status_code == 200
    assert repo.doctors[doctor_id]["verification_status"] == "Verified"
    assert repo.users[user["id"]]["status"] == "active"

    # 4. Doctor logs in now and accesses Doctor Portal
    client.post("/auth/logout")
    doc_login_res = client.post("/auth/login", data={"email": doc_email, "password": doc_pass}, follow_redirects=True)
    assert doc_login_res.status_code == 200
    assert "Doctor Portal" in response_text(doc_login_res)
    assert "Dr. Sunil Sharma" in response_text(doc_login_res)


def test_logout(client):
    client.post("/auth/login", data={"email": "aarav@medtrack.demo", "password": "Patient@12345"})
    res = client.post("/auth/logout", follow_redirects=True)
    assert res.status_code == 200
    assert "Sign In" in response_text(res)


def response_text(response):
    return response.data.decode("utf-8")

