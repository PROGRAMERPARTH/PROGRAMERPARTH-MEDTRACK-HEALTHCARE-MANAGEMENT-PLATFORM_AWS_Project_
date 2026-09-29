"""Doctor blueprint — Dashboard, Profile, Patient records management."""
from datetime import date

from flask import (
    Blueprint, current_app, flash, g, redirect, render_template,
    request, url_for,
)

from ..utils.security import login_required

doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")


@doctor_bp.route("/dashboard")
@login_required(roles=["doctor"])
def dashboard():
    repo = current_app.extensions["repository"]
    doctor_id = g.current_user.get("doctor_id")
    doctor = repo.get_doctor(doctor_id) if doctor_id else None
    appointments = repo.appointments_for_doctor(doctor_id) if doctor_id else []

    today = date.today().isoformat()
    today_appointments = [a for a in appointments if a["date"] == today and a["status"] in {"confirmed", "requested"}]
    pending = [a for a in appointments if a["status"] == "requested"]
    completed = [a for a in appointments if a["status"] == "completed"]
    reports = repo.reports_for_doctor(doctor_id) if doctor_id else []
    pending_reports = [r for r in reports if r["status"] == "submitted"]

    # Attach patient names
    for appt in today_appointments + pending:
        pat = repo.get_patient(appt["patient_id"])
        appt["patient_name"] = pat["name"] if pat else "Unknown"

    stats = {
        "today": len(today_appointments),
        "pending": len(pending),
        "completed": len(completed),
        "reports_pending": len(pending_reports),
    }
    return render_template("doctor/dashboard.html", doctor=doctor,
                           today_appointments=today_appointments,
                           pending=pending[:10], stats=stats)


@doctor_bp.route("/profile", methods=["GET", "POST"])
@login_required(roles=["doctor"])
def profile():
    repo = current_app.extensions["repository"]
    doctor_id = g.current_user.get("doctor_id")
    doctor = repo.get_doctor(doctor_id)

    if request.method == "POST":
        days = request.form.getlist("available_days")
        slots = [s.strip() for s in request.form.get("time_slots", "").split(",") if s.strip()]
        updated = repo.update_doctor(doctor_id, {
            "specialization": request.form.get("specialization", "").strip(),
            "qualification": request.form.get("qualification", "").strip(),
            "experience": int(request.form.get("experience", 0)),
            "clinic": request.form.get("clinic", "").strip(),
            "consultation_mode": request.form.get("consultation_mode", "").strip(),
            "fee": int(request.form.get("fee", 0)),
            "location": request.form.get("location", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "bio": request.form.get("bio", "").strip(),
            "available_days": days,
            "time_slots": slots or doctor.get("time_slots", []),
        })
        if updated:
            repo.audit(g.current_user["id"], "profile_updated", "doctor", doctor_id)
            flash("Profile updated successfully.", "success")
            doctor = updated
        else:
            flash("Could not update profile.", "danger")

    return render_template("doctor/profile.html", doctor=doctor)


@doctor_bp.route("/appointments")
@login_required(roles=["doctor"])
def appointments():
    repo = current_app.extensions["repository"]
    doctor_id = g.current_user.get("doctor_id")
    status_filter = request.args.get("status", "")
    appointments = repo.appointments_for_doctor(doctor_id, status=status_filter or None)

    for appt in appointments:
        pat = repo.get_patient(appt["patient_id"])
        appt["patient_name"] = pat["name"] if pat else "Unknown"

    return render_template("doctor/appointments.html", appointments=appointments,
                           current_status=status_filter)


@doctor_bp.route("/patients/<patient_id>")
@login_required(roles=["doctor"])
def patient_detail(patient_id):
    repo = current_app.extensions["repository"]
    doctor_id = g.current_user.get("doctor_id")

    if not repo.doctor_has_patient_context(doctor_id, patient_id):
        flash("You do not have access to this patient's information.", "danger")
        return redirect(url_for("doctor.dashboard"))

    patient = repo.get_patient(patient_id)
    records = repo.records_for_patient(patient_id)
    reports = [r for r in repo.reports_for_patient(patient_id) if r.get("doctor_id") == doctor_id]

    return render_template("doctor/patient_detail.html", patient=patient,
                           records=records, reports=reports)
