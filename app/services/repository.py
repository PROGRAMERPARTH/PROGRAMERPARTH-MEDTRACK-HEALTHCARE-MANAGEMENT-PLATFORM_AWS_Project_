"""Data access boundary for MedTrack.

The demo uses safe in-process data so it can run without cloud credentials.  Every
route only talks to this interface, which keeps the DynamoDB migration isolated.
See docs/dynamodb-access-patterns.md for the production single-table design.
"""
from __future__ import annotations

import copy
import json
import os
import uuid
from datetime import date, datetime, timedelta, timezone

from werkzeug.security import generate_password_hash


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def entity_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def format_time_display(time_str: str) -> str:
    """Format 24-hour time (e.g., '14:00') into friendly 12-hour format ('02:00 PM')."""
    try:
        time_clean = time_str.strip()
        if "AM" in time_clean.upper() or "PM" in time_clean.upper():
            return time_clean
        parts = time_clean.split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        suffix = "PM" if hour >= 12 else "AM"
        display_hour = 12 if hour in (0, 12) else hour % 12
        return f"{display_hour:02d}:{minute:02d} {suffix}"
    except Exception:
        return time_str


def get_slot_period(time_str: str) -> str:
    """Categorize time slot into Morning, Afternoon, or Evening."""
    try:
        time_clean = time_str.strip().upper()
        if "AM" in time_clean:
            return "Morning"
        if "PM" in time_clean:
            hour = int(time_clean.split(":")[0])
            return "Afternoon" if (hour < 5 or hour == 12) else "Evening"
        hour = int(time_clean.split(":")[0])
        if hour < 12:
            return "Morning"
        elif hour < 17:
            return "Afternoon"
        return "Evening"
    except Exception:
        return "General"


class InMemoryRepository:
    def __init__(self, db_path=None):
        self.db_path = db_path
        self.users, self.patients, self.doctors = {}, {}, {}
        self.appointments, self.records, self.reports = {}, {}, {}
        self.notifications, self.audit_logs = {}, []
        if self.db_path and os.path.exists(self.db_path):
            self._load()
        else:
            self._seed()
            if self.db_path:
                self._save()

    def _save(self):
        if not self.db_path:
            return
        try:
            data = {
                "users": self.users,
                "patients": self.patients,
                "doctors": self.doctors,
                "appointments": self.appointments,
                "records": self.records,
                "reports": self.reports,
                "notifications": self.notifications,
                "audit_logs": self.audit_logs,
            }
            dir_name = os.path.dirname(self.db_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            tmp_path = f"{self.db_path}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            os.replace(tmp_path, self.db_path)
        except Exception as exc:
            print(f"Warning: Failed to persist database to {self.db_path}: {exc}")

    def _load(self):
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.users = data.get("users", {})
            self.patients = data.get("patients", {})
            self.doctors = data.get("doctors", {})
            self.appointments = data.get("appointments", {})
            self.records = data.get("records", {})
            self.reports = data.get("reports", {})
            self.notifications = data.get("notifications", {})
            self.audit_logs = data.get("audit_logs", [])
        except Exception as exc:
            print(f"Warning: Failed to load database from {self.db_path}: {exc}. Re-seeding.")
            self._seed()
            self._save()

    def _seed(self):
        self._add_seed_user("admin_demo", "admin@medtrack.demo", "Admin@12345", "admin", "MedTrack Administrator")
        p1 = self._add_seed_user("user_aarav", "aarav@medtrack.demo", "Patient@12345", "patient", "Aarav Sharma")
        p2 = self._add_seed_user("user_ananya", "ananya@medtrack.demo", "Patient@12345", "patient", "Ananya Patil")
        self.patients["pat_aarav"] = {"id": "pat_aarav", "user_id": p1["id"], "name": "Aarav Sharma", "dob": "1996-05-17", "gender": "Male", "phone": "+91 98765 43210", "address": "Pune, Maharashtra", "emergency_contact": "Meera Sharma · +91 98765 00112", "created_at": utcnow()}
        self.patients["pat_ananya"] = {"id": "pat_ananya", "user_id": p2["id"], "name": "Ananya Patil", "dob": "1993-11-02", "gender": "Female", "phone": "+91 98765 88776", "address": "Mumbai, Maharashtra", "emergency_contact": "Ravi Patil · +91 98765 11223", "created_at": utcnow()}
        p1["patient_id"], p2["patient_id"] = "pat_aarav", "pat_ananya"
        doctor_data = [
            ("dr_rohan", "doctor_rohan", "rohan@medtrack.demo", "Dr. Rohan Mehta", "General Physician", "MBBS, MD", 12, "CityCare Clinic, Pune", "In-person & Video", 600, "Pune"),
            ("dr_priya", "doctor_priya", "priya@medtrack.demo", "Dr. Priya Kulkarni", "Dermatologist", "MBBS, MD Dermatology", 9, "SkinWell Centre, Mumbai", "In-person & Video", 750, "Mumbai"),
            ("dr_aditya", "doctor_aditya", "aditya@medtrack.demo", "Dr. Aditya Shah", "Cardiologist", "MBBS, DM Cardiology", 15, "HeartFirst Hospital, Pune", "In-person", 1000, "Pune"),
        ]
        for did, uid, email, name, specialty, qualification, years, clinic, mode, fee, location in doctor_data:
            user = self._add_seed_user(uid, email, "Doctor@12345", "doctor", name)
            user["doctor_id"] = did
            self.doctors[did] = {"id": did, "user_id": uid, "name": name, "email": email, "specialization": specialty, "qualification": qualification, "experience": years, "clinic": clinic, "consultation_mode": mode, "fee": fee, "location": location, "phone": "+91 90000 00000", "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "time_slots": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"], "verification_status": "Verified", "photo": "", "bio": "Demo clinician profile for MedTrack demonstrations only.", "created_at": utcnow(), "updated_at": utcnow()}

        # Seed pending doctor application for admin verification review
        doc_pending_user = self._add_seed_user("usr_sachin", "sachin123@gmail.com", "Doctor@12345", "doctor", "Dr. Sachin Patil")
        doc_pending_user["status"] = "pending"
        doc_pending_user["doctor_id"] = "dr_sachin"
        self.doctors["dr_sachin"] = {
            "id": "dr_sachin",
            "user_id": "usr_sachin",
            "name": "Dr. Sachin Patil",
            "email": "sachin123@gmail.com",
            "specialization": "Ophthalmologist",
            "qualification": "MBBS,MS",
            "experience": 5,
            "clinic": "CityCare Clinic, Pune",
            "consultation_mode": "In-person",
            "fee": 600,
            "location": "Mumbai",
            "phone": "9632587410",
            "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "time_slots": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"],
            "verification_status": "Pending Approval",
            "photo": "",
            "bio": "Clinician profile registered on MedTrack.",
            "created_at": utcnow(),
            "updated_at": utcnow(),
        }
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        apt1_id = entity_id("apt")
        self.appointments[apt1_id] = {
            "id": apt1_id, "patient_id": "pat_aarav", "doctor_id": "dr_rohan",
            "date": tomorrow, "time": "10:00", "time_slot": "10:00",
            "reason": "Annual wellness consultation", "mode": "In-person",
            "consultation_mode": "In-person", "status": "confirmed",
            "created_at": utcnow(), "updated_at": utcnow()
        }
        past_date = (date.today() - timedelta(days=14)).isoformat()
        apt2_id = entity_id("apt")
        self.appointments[apt2_id] = {
            "id": apt2_id, "patient_id": "pat_aarav", "doctor_id": "dr_priya",
            "date": past_date, "time": "11:00", "time_slot": "11:00",
            "reason": "Follow-up consultation", "mode": "Video",
            "consultation_mode": "Video", "status": "completed",
            "created_at": utcnow(), "updated_at": utcnow()
        }
        self.create_record("pat_aarav", "dr_priya", apt2_id, "Routine consultation completed. Please discuss any new symptoms with your clinician.", "General care plan discussed.", "Follow up as advised by your clinician.")
        self.create_notification(p1["id"], "appointment_confirmed", "Appointment confirmed", f"Your appointment with Dr. Rohan Mehta is confirmed for {tomorrow} at 10:00.")

    def _add_seed_user(self, user_id, email, password, role, name):
        user = {"id": user_id, "email": email, "password_hash": generate_password_hash(password), "role": role, "name": name, "status": "active", "created_at": utcnow(), "updated_at": utcnow()}
        self.users[user_id] = user
        return user

    @staticmethod
    def _public(data):
        return copy.deepcopy(data) if data else None

    def get_user(self, user_id):
        user = self._public(self.users.get(user_id))
        if user:
            user.pop("password_hash", None)
        return user

    def get_user_by_email(self, email, include_hash=False):
        found = next((u for u in self.users.values() if u["email"] == email.lower()), None)
        if not found:
            return None
        user = self._public(found)
        if not include_hash:
            user.pop("password_hash", None)
        return user

    def create_patient_user(self, payload, password_hash):
        if self.get_user_by_email(payload["email"]):
            raise ValueError("An account already exists for that email address.")
        user_id, patient_id = entity_id("usr"), entity_id("pat")
        now = utcnow()
        self.users[user_id] = {"id": user_id, "email": payload["email"].lower(), "password_hash": password_hash, "role": "patient", "name": payload["name"], "patient_id": patient_id, "status": "active", "created_at": now, "updated_at": now}
        self.patients[patient_id] = {"id": patient_id, "user_id": user_id, "name": payload["name"], "dob": payload["dob"], "gender": payload["gender"], "phone": payload["phone"], "address": payload["address"], "emergency_contact": payload["emergency_contact"], "created_at": now, "updated_at": now}
        self._save()
        return self.get_user(user_id)

    def create_doctor_user(self, payload, password_hash, status="pending"):
        if self.get_user_by_email(payload["email"]):
            raise ValueError("An account already exists for that email address.")
        user_id, doctor_id = entity_id("usr"), entity_id("dr")
        now = utcnow()

        available_days = payload.get("available_days")
        if not available_days:
            available_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        elif isinstance(available_days, str):
            available_days = [d.strip() for d in available_days.split(",") if d.strip()]

        time_slots = payload.get("time_slots")
        if not time_slots:
            time_slots = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
        elif isinstance(time_slots, str):
            time_slots = [s.strip() for s in time_slots.split(",") if s.strip()]

        try:
            fee = int(payload.get("fee") or payload.get("consultation_fee") or 500)
        except (ValueError, TypeError):
            fee = 500

        try:
            experience = int(payload.get("experience") or payload.get("experience_years") or 1)
        except (ValueError, TypeError):
            experience = 1

        self.users[user_id] = {
            "id": user_id,
            "email": payload["email"].lower(),
            "password_hash": password_hash,
            "role": "doctor",
            "name": payload["name"],
            "doctor_id": doctor_id,
            "status": status,
            "created_at": now,
            "updated_at": now,
        }

        self.doctors[doctor_id] = {
            "id": doctor_id,
            "user_id": user_id,
            "name": payload["name"],
            "email": payload["email"].lower(),
            "specialization": payload.get("specialization", "General Physician").strip(),
            "qualification": payload.get("qualification", "MBBS").strip(),
            "experience": experience,
            "clinic": payload.get("clinic", "").strip() or payload.get("hospital", "Medical Clinic").strip(),
            "consultation_mode": payload.get("consultation_mode", "In-person & Video").strip(),
            "fee": fee,
            "location": payload.get("location", "City Center").strip(),
            "phone": payload.get("phone", "").strip(),
            "available_days": available_days,
            "time_slots": time_slots,
            "verification_status": "Verified" if status == "active" else "Pending Approval",
            "photo": "",
            "bio": payload.get("bio", "Clinician profile registered on MedTrack.").strip(),
            "created_at": now,
            "updated_at": now,
        }

        self._save()
        return self.get_user(user_id)

    def approve_doctor(self, doctor_id, admin_user_id):
        doctor = self.doctors.get(doctor_id)
        if not doctor:
            raise ValueError("Doctor not found.")
        user_id = doctor.get("user_id")
        user = self.users.get(user_id)
        if not user:
            raise ValueError("Doctor user record not found.")

        user["status"] = "active"
        user["updated_at"] = utcnow()
        doctor["verification_status"] = "Verified"
        doctor["updated_at"] = utcnow()

        self.audit(admin_user_id, "doctor_approved", "doctor", doctor_id)
        self._save()
        return self._public_doctor(doctor)

    def reject_doctor(self, doctor_id, admin_user_id, reason=""):
        doctor = self.doctors.get(doctor_id)
        if not doctor:
            raise ValueError("Doctor not found.")
        user_id = doctor.get("user_id")
        user = self.users.get(user_id)
        if user:
            user["status"] = "rejected"
            user["updated_at"] = utcnow()
        doctor["verification_status"] = "Rejected"
        doctor["updated_at"] = utcnow()

        self.audit(admin_user_id, "doctor_rejected", "doctor", doctor_id)
        self._save()
        return self._public_doctor(doctor)

    def get_patient(self, patient_id):
        return self._public(self.patients.get(patient_id))

    def update_patient(self, patient_id, values):
        if patient_id not in self.patients:
            return None
        safe = {key: values[key] for key in ("name", "phone", "address", "emergency_contact", "gender") if key in values}
        self.patients[patient_id].update(safe | {"updated_at": utcnow()})
        self.users[self.patients[patient_id]["user_id"]]["name"] = self.patients[patient_id]["name"]
        self._save()
        return self.get_patient(patient_id)

    def _public_doctor(self, data):
        if not data:
            return None
        doc = copy.deepcopy(data)
        doc.setdefault("consultation_fee", doc.get("fee", 500))
        doc.setdefault("hospital", doc.get("clinic", "Medical Center"))
        doc.setdefault("experience_years", doc.get("experience", 5))
        doc.setdefault("available_time_slots", doc.get("time_slots", ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]))
        user = self.users.get(doc.get("user_id"))
        if user:
            doc["user_status"] = user.get("status", "active")
            doc["email"] = user.get("email", doc.get("email", ""))
        return doc

    def list_doctors(self, filters=None, include_unverified=False):
        filters = filters or {}
        doctors = [self._public_doctor(d) for d in self.doctors.values()]
        if not include_unverified:
            doctors = [d for d in doctors if d.get("verification_status", "").lower() == "verified"]

        status_filter = filters.get("verification_status") or filters.get("status")
        if status_filter:
            doctors = [d for d in doctors if d.get("verification_status", "").lower() == status_filter.lower() or d.get("user_status", "").lower() == status_filter.lower()]

        query = filters.get("q", "").lower().strip()
        if query:
            doctors = [d for d in doctors if query in f"{d['name']} {d['specialization']} {d['location']}".lower()]
        for key in ("specialization", "consultation_mode", "location"):
            if filters.get(key):
                doctors = [d for d in doctors if d[key].lower() == filters[key].lower()]
        if filters.get("min_experience"):
            doctors = [d for d in doctors if d["experience"] >= int(filters["min_experience"])]
        return sorted(doctors, key=lambda d: d["name"])

    def get_doctor(self, doctor_id):
        return self._public_doctor(self.doctors.get(doctor_id))

    def update_doctor(self, doctor_id, values):
        if doctor_id not in self.doctors:
            return None
        fields = {"specialization", "qualification", "experience", "clinic", "consultation_mode", "fee", "location", "phone", "bio", "available_days", "time_slots"}
        self.doctors[doctor_id].update({k: v for k, v in values.items() if k in fields} | {"updated_at": utcnow()})
        self._save()
        return self.get_doctor(doctor_id)

    def slots_for_date(self, doctor_id, appointment_date):
        doctor = self.doctors.get(doctor_id)
        if not doctor:
            return []
        try:
            selected = date.fromisoformat(appointment_date)
        except ValueError:
            return []
        available_days = doctor.get("available_days", [])
        if selected < date.today() or selected.strftime("%A") not in available_days:
            return []
        booked = {a["time"] for a in self.appointments.values() if a["doctor_id"] == doctor_id and a["date"] == appointment_date and a["status"] not in {"cancelled", "rejected"}}
        raw_slots = doctor.get("time_slots", ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"])
        return [
            {
                "time": slot,
                "display_time": format_time_display(slot),
                "period": get_slot_period(slot),
                "available": slot not in booked
            }
            for slot in raw_slots
        ]

    def create_appointment(self, patient_id, doctor_id, appointment_date, appointment_time, reason, mode):
        if patient_id not in self.patients or doctor_id not in self.doctors:
            raise ValueError("The selected patient or doctor does not exist.")
        try:
            selected = date.fromisoformat(appointment_date)
        except ValueError as error:
            raise ValueError("Select a valid appointment date.") from error
        if selected < date.today():
            raise ValueError("Appointments cannot be booked in the past.")
        available = {slot["time"] for slot in self.slots_for_date(doctor_id, appointment_date) if slot["available"]}
        if appointment_time not in available:
            raise ValueError("That time slot is no longer available. Please select another slot.")
        item = {
            "id": entity_id("apt"), "patient_id": patient_id, "doctor_id": doctor_id,
            "date": appointment_date, "time": appointment_time, "time_slot": appointment_time,
            "reason": reason.strip(), "mode": mode, "consultation_mode": mode,
            "status": "requested", "created_at": utcnow(), "updated_at": utcnow()
        }
        self.appointments[item["id"]] = item
        self._save()
        return self._public(item)

    def get_appointment(self, appointment_id):
        return self._public(self.appointments.get(appointment_id))

    def appointments_for_patient(self, patient_id, status=None):
        result = [self._public(a) for a in self.appointments.values() if a["patient_id"] == patient_id]
        if status:
            result = [a for a in result if a["status"] == status]
        return sorted(result, key=lambda a: (a["date"], a["time"]), reverse=True)

    def appointments_for_doctor(self, doctor_id, status=None):
        result = [self._public(a) for a in self.appointments.values() if a["doctor_id"] == doctor_id]
        if status:
            result = [a for a in result if a["status"] == status]
        return sorted(result, key=lambda a: (a["date"], a["time"]))

    def update_appointment(self, appointment_id, status, actor_role, new_date=None, new_time=None):
        appointment = self.appointments.get(appointment_id)
        allowed = {"patient": {"cancelled", "rescheduled"}, "doctor": {"confirmed", "rejected", "completed", "no_show"}}
        if not appointment or status not in allowed.get(actor_role, set()):
            raise ValueError("This appointment cannot be updated in that way.")
        if appointment["status"] in {"cancelled", "rejected", "completed", "no_show"}:
            raise ValueError("This appointment is already closed.")
        if status == "rescheduled":
            if not new_date or not new_time:
                raise ValueError("Choose a new date and time slot.")
            # Ensure the old appointment does not occupy a slot during validation.
            appointment["status"] = "rescheduling"
            available = {s["time"] for s in self.slots_for_date(appointment["doctor_id"], new_date) if s["available"]}
            appointment["status"] = "rescheduled"
            if new_time not in available:
                raise ValueError("That new time slot is unavailable.")
            appointment["date"], appointment["time"] = new_date, new_time
        appointment["status"] = status
        appointment["updated_at"] = utcnow()
        self._save()
        return self._public(appointment)

    def doctor_has_patient_context(self, doctor_id, patient_id):
        return any(a["doctor_id"] == doctor_id and a["patient_id"] == patient_id and a["status"] in {"confirmed", "completed", "requested"} for a in self.appointments.values())

    def appointment_context(self, appointment_id, user):
        appointment = self.get_appointment(appointment_id)
        if not appointment:
            return None
        if user["role"] == "patient" and appointment["patient_id"] == user.get("patient_id"):
            return appointment
        if user["role"] == "doctor" and appointment["doctor_id"] == user.get("doctor_id"):
            return appointment
        return None

    def create_record(self, patient_id, doctor_id, appointment_id, clinical_notes, treatment_notes, follow_up):
        item = {"id": entity_id("rec"), "patient_id": patient_id, "doctor_id": doctor_id, "appointment_id": appointment_id, "record_date": date.today().isoformat(), "clinical_notes": clinical_notes.strip(), "treatment_notes": treatment_notes.strip(), "follow_up": follow_up.strip(), "created_at": utcnow(), "updated_at": utcnow()}
        self.records[item["id"]] = item
        self._save()
        return self._public(item)

    def records_for_patient(self, patient_id):
        return sorted([self._public(r) for r in self.records.values() if r["patient_id"] == patient_id], key=lambda r: r["record_date"], reverse=True)

    def create_report(self, patient_id, appointment_id, title, report_type, description, report_date, file_reference, original_filename):
        item = {"id": entity_id("rpt"), "patient_id": patient_id, "appointment_id": appointment_id or None, "doctor_id": self.appointments.get(appointment_id, {}).get("doctor_id") if appointment_id else None, "title": title.strip(), "report_type": report_type, "description": description.strip(), "report_date": report_date, "file_reference": file_reference, "original_filename": original_filename, "status": "submitted", "uploaded_at": utcnow()}
        self.reports[item["id"]] = item
        self._save()
        return self._public(item)

    def reports_for_patient(self, patient_id):
        return sorted([self._public(r) for r in self.reports.values() if r["patient_id"] == patient_id], key=lambda r: r["uploaded_at"], reverse=True)

    def reports_for_doctor(self, doctor_id):
        return sorted([self._public(r) for r in self.reports.values() if r["doctor_id"] == doctor_id], key=lambda r: r["uploaded_at"], reverse=True)

    def get_report(self, report_id):
        return self._public(self.reports.get(report_id))

    def update_report_status(self, report_id, status):
        if report_id not in self.reports:
            return None
        self.reports[report_id]["status"] = status
        self._save()
        return self.get_report(report_id)

    def create_notification(self, user_id, notification_type, title, message):
        item = {"id": entity_id("ntf"), "user_id": user_id, "type": notification_type, "title": title, "message": message, "read": False, "created_at": utcnow()}
        self.notifications[item["id"]] = item
        self._save()
        return self._public(item)

    def notifications_for_user(self, user_id):
        return sorted([self._public(n) for n in self.notifications.values() if n["user_id"] == user_id], key=lambda n: n["created_at"], reverse=True)

    def unread_notification_count(self, user_id):
        return sum(1 for n in self.notifications.values() if n["user_id"] == user_id and not n["read"])

    def mark_notification_read(self, notification_id, user_id):
        item = self.notifications.get(notification_id)
        if not item or item["user_id"] != user_id:
            return None
        item["read"] = True
        self._save()
        return self._public(item)

    def audit(self, actor_id, action, resource_type, resource_id):
        self.audit_logs.append({"id": entity_id("aud"), "actor_id": actor_id, "action": action, "resource_type": resource_type, "resource_id": resource_id, "timestamp": utcnow()})
        self._save()

    def dashboard_stats(self):
        appointments = list(self.appointments.values())
        pending_doctors = sum(1 for d in self.doctors.values() if d.get("verification_status") == "Pending Approval")
        return {
            "patients": len(self.patients),
            "doctors": len(self.doctors),
            "pending_doctors": pending_doctors,
            "appointments": len(appointments),
            "appointments_today": sum(a["date"] == date.today().isoformat() for a in appointments),
            "pending": sum(a["status"] == "requested" for a in appointments),
            "completed": sum(a["status"] == "completed" for a in appointments),
            "reports": len(self.reports),
            "audit_events": len(self.audit_logs),
        }

    def admin_users(self):
        return [self.get_user(uid) for uid, u in self.users.items() if u.get("role") == "admin"]

    def all_users(self):
        return [self.get_user(k) for k in self.users]

    def recent_audit(self):
        return list(reversed(self.audit_logs[-12:]))

    def all_appointments(self):
        return sorted([self._public(a) for a in self.appointments.values()], key=lambda a: a["created_at"], reverse=True)


def build_repository(config):
    db_path = config.get("DB_PATH")
    return InMemoryRepository(db_path=db_path)
