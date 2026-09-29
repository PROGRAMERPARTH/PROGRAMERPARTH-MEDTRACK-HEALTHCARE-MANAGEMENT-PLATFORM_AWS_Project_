"""Security and Role-Based Access Control (RBAC) tests."""


def test_patient_cannot_access_admin_dashboard(client):
    client.post("/auth/login", data={"email": "aarav@medtrack.demo", "password": "Patient@12345"})
    res = client.get("/admin/dashboard")
    # Patient role does not have admin permission
    assert res.status_code in [302, 403]


def test_patient_cannot_access_doctor_dashboard(client):
    client.post("/auth/login", data={"email": "aarav@medtrack.demo", "password": "Patient@12345"})
    res = client.get("/doctor/dashboard")
    assert res.status_code in [302, 403]


def test_unauthenticated_user_redirected_to_login(client):
    res = client.get("/patient/dashboard", follow_redirects=False)
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]


def test_doctor_cannot_view_unrelated_patient(client):
    client.post("/auth/login", data={"email": "aditya@medtrack.demo", "password": "Doctor@12345"})
    # Dr. Aditya has no active appointments with pat_ananya
    res = client.get("/doctor/patients/pat_ananya", follow_redirects=True)
    assert res.status_code == 200
    assert b"do not have access" in res.data
