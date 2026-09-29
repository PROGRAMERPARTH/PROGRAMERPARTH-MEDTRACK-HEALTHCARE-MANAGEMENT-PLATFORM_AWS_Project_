"""Medical Records blueprint — View and create records."""
from flask import (
    Blueprint, current_app, flash, g, redirect, render_template,
    request, url_for,
)

from ..utils.security import can_access_patient_context, login_required

records_bp = Blueprint("records", __name__, url_prefix="/medical-records")


@records_bp.route("/")
@login_required(roles=["patient", "doctor"])
def list_records():
    repo = current_app.extensions["repository"]

    if g.current_user["role"] == "patient":
        patient_id = g.current_user.get("patient_id")
        records = repo.records_for_patient(patient_id)
        for rec in records:
            doc = repo.get_doctor(rec["doctor_id"])
            rec["doctor_name"] = doc["name"] if doc else "Unknown"
        return render_template("medical_records/list.html", records=records)

    # Doctor — show records for patients they have context for
    doctor_id = g.current_user.get("doctor_id")
    appointments = repo.appointments_for_doctor(doctor_id)
    patient_ids = {a["patient_id"] for a in appointments if a["status"] in {"confirmed", "completed", "requested"}}
    records = []
    for pid in patient_ids:
        for rec in repo.records_for_patient(pid):
            pat = repo.get_patient(rec["patient_id"])
            rec["patient_name"] = pat["name"] if pat else "Unknown"
            records.append(rec)
    records.sort(key=lambda r: r["record_date"], reverse=True)
    return render_template("medical_records/list.html", records=records)


@records_bp.route("/create/<appointment_id>", methods=["GET", "POST"], endpoint="create")
@records_bp.route("/create/<appointment_id>", methods=["GET", "POST"], endpoint="create_record")
@login_required(roles=["doctor"])
def create(appointment_id):
    repo = current_app.extensions["repository"]
    notifier = current_app.extensions["notifications_service"]
    appointment = repo.appointment_context(appointment_id, g.current_user)

    if not appointment:
        flash("Appointment not found or access denied.", "danger")
        return redirect(url_for("doctor.dashboard"))

    patient = repo.get_patient(appointment["patient_id"])
    doctor = repo.get_doctor(appointment["doctor_id"])

    if request.method == "GET":
        return render_template("medical_records/create.html",
                               appointment=appointment, patient=patient, doctor=doctor)

    clinical_notes = request.form.get("clinical_notes", "").strip()
    treatment_notes = request.form.get("treatment_notes", "").strip()
    follow_up = request.form.get("follow_up", "").strip()

    if not clinical_notes:
        flash("Clinical notes are required.", "danger")
        return render_template("medical_records/create.html",
                               appointment=appointment, patient=patient, doctor=doctor), 400

    record = repo.create_record(appointment["patient_id"], appointment["doctor_id"],
                                 appointment_id, clinical_notes, treatment_notes, follow_up)
    repo.audit(g.current_user["id"], "record_created", "medical_record", record["id"])

    # Notify patient
    if patient:
        patient_user_id = patient.get("user_id")
        if patient_user_id:
            notifier.send(patient_user_id, "record_updated",
                          "Medical Record Updated",
                          f"Dr. {doctor['name'] if doctor else 'Your doctor'} has added notes to your medical record.")

    flash("Medical record created successfully.", "success")
    return redirect(url_for("doctor.dashboard"))
