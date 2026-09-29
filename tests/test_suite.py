import os
import sys
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import create_app


class MedTrackTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-secret-key"})
        self.client = self.app.test_client()
        self.repo = self.app.extensions["repository"]

    def test_landing_page(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Healthcare Management", res.data)

    def test_patient_login(self):
        res = self.client.post("/auth/login", data={"email": "aarav@medtrack.demo", "password": "Patient@12345"}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Aarav Sharma", res.data)

    def test_doctor_login(self):
        res = self.client.post("/auth/login", data={"email": "rohan@medtrack.demo", "password": "Doctor@12345"}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Doctor Portal", res.data)

    def test_admin_login(self):
        res = self.client.post("/auth/login", data={"email": "admin@medtrack.demo", "password": "Admin@12345"}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Administration Console", res.data)

    def test_invalid_login(self):
        res = self.client.post("/auth/login", data={"email": "aarav@medtrack.demo", "password": "WrongPassword!"})
        self.assertEqual(res.status_code, 401)
        self.assertIn(b"Invalid email or password", res.data)

    def test_patient_registration(self):
        res = self.client.post("/auth/register", data={
            "name": "Kavita Rao",
            "email": "kavita.rao@medtrack.demo",
            "phone": "+91 91234 56789",
            "dob": "1995-08-20",
            "gender": "female",
            "address": "Bangalore, Karnataka",
            "emergency_contact": "Ramesh Rao (+91 91234 00000)",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Kavita Rao", res.data)

    def test_book_appointment(self):
        self.client.post("/auth/login", data={"email": "aarav@medtrack.demo", "password": "Patient@12345"})
        # Book on next weekday
        day_offset = 1
        while (date.today() + timedelta(days=day_offset)).strftime("%A") in ["Saturday", "Sunday"]:
            day_offset += 1
        booking_date = (date.today() + timedelta(days=day_offset)).isoformat()

        res = self.client.post("/appointments/book/dr_rohan", data={
            "date": booking_date,
            "time": "14:00",
            "reason": "General health assessment",
            "mode": "In-person"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"General health assessment", res.data)

    def test_past_date_appointment_prevented(self):
        self.client.post("/auth/login", data={"email": "aarav@medtrack.demo", "password": "Patient@12345"})
        past_date = (date.today() - timedelta(days=2)).isoformat()
        res = self.client.post("/appointments/book/dr_rohan", data={
            "date": past_date,
            "time": "14:00",
            "reason": "Past date check",
            "mode": "In-person"
        })
        self.assertEqual(res.status_code, 400)

    def test_rbac_patient_cannot_access_admin(self):
        self.client.post("/auth/login", data={"email": "aarav@medtrack.demo", "password": "Patient@12345"})
        res = self.client.get("/admin/dashboard")
        self.assertIn(res.status_code, [302, 403])

    def test_doctor_patient_isolation(self):
        self.client.post("/auth/login", data={"email": "aditya@medtrack.demo", "password": "Doctor@12345"})
        res = self.client.get("/doctor/patients/pat_ananya", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"do not have access", res.data)

    def test_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json.get("status"), "healthy")


if __name__ == "__main__":
    unittest.main()
