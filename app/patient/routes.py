"""Patient blueprint — Dashboard, Profile, Doctor discovery."""
from datetime import date

from flask import (
    Blueprint, current_app, flash, g, redirect, render_template,
    request, url_for,
)

from ..utils.security import login_required

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")


@patient_bp.route("/dashboard")
@login_required(roles=["patient"])
def dashboard():
    repo = current_app.extensions["repository"]
    patient_id = g.current_user.get("patient_id")
    patient = repo.get_patient(patient_id) if patient_id else None
    appointments = repo.appointments_for_patient(patient_id) if patient_id else []

    upcoming = [a for a in appointments if a["status"] in {"requested", "confirmed", "rescheduled"} and a["date"] >= date.today().isoformat()]
    completed = [a for a in appointments if a["status"] == "completed"]
    reports = repo.reports_for_patient(patient_id) if patient_id else []

    # Attach doctor names
    for appt in upcoming:
        doc = repo.get_doctor(appt["doctor_id"])
        appt["doctor_name"] = doc["name"] if doc else "Unknown"
        appt["doctor_specialization"] = doc["specialization"] if doc else ""

    next_appointment = upcoming[0] if upcoming else None

    stats = {
        "total_appointments": len(appointments),
        "completed": len(completed),
        "pending": len(upcoming),
        "reports": len(reports),
    }
    return render_template("patient/dashboard.html", patient=patient,
                           next_appointment=next_appointment, upcoming=upcoming[:5],
                           stats=stats)


@patient_bp.route("/profile", methods=["GET", "POST"])
@login_required(roles=["patient"])
def profile():
    repo = current_app.extensions["repository"]
    patient_id = g.current_user.get("patient_id")
    patient = repo.get_patient(patient_id)

    if request.method == "POST":
        updated = repo.update_patient(patient_id, {
            "name": request.form.get("name", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "address": request.form.get("address", "").strip(),
            "emergency_contact": request.form.get("emergency_contact", "").strip(),
            "gender": request.form.get("gender", "").strip(),
        })
        if updated:
            repo.audit(g.current_user["id"], "profile_updated", "patient", patient_id)
            flash("Profile updated successfully.", "success")
            patient = updated
        else:
            flash("Could not update profile.", "danger")

    return render_template("patient/profile.html", patient=patient)


@patient_bp.route("/doctors")
@login_required(roles=["patient"])
def find_doctors():
    repo = current_app.extensions["repository"]
    filters = {
        "q": request.args.get("q", ""),
        "specialization": request.args.get("specialization", ""),
        "consultation_mode": request.args.get("consultation_mode", ""),
        "location": request.args.get("location", ""),
        "min_experience": request.args.get("min_experience", ""),
    }
    doctors = repo.list_doctors(filters)

    # Unique filter options
    all_doctors = repo.list_doctors()
    specializations = sorted({d["specialization"] for d in all_doctors})
    locations = sorted({d["location"] for d in all_doctors})

    return render_template("patient/find_doctors.html", doctors=doctors,
                           filters=filters, specializations=specializations,
                           locations=locations)


@patient_bp.route("/doctors/<doctor_id>")
@login_required(roles=["patient"])
def doctor_profile(doctor_id):
    repo = current_app.extensions["repository"]
    doctor = repo.get_doctor(doctor_id)
    if not doctor:
        flash("Doctor not found.", "danger")
        return redirect(url_for("patient.find_doctors"))
    return render_template("patient/doctor_profile.html", doctor=doctor)
