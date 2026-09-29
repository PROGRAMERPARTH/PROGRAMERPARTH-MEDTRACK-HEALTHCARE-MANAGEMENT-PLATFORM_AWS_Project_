"""Appointments blueprint — Book, View, Cancel, Reschedule, Accept/Reject."""
from datetime import date

from flask import (
    Blueprint, current_app, flash, g, jsonify, redirect,
    render_template, request, url_for,
)

from ..utils.security import login_required

appointments_bp = Blueprint("appointments", __name__, url_prefix="/appointments")


@appointments_bp.route("/book/<doctor_id>", methods=["GET", "POST"])
@login_required(roles=["patient"])
def book(doctor_id):
    repo = current_app.extensions["repository"]
    notifier = current_app.extensions["notifications_service"]
    doctor = repo.get_doctor(doctor_id)
    if not doctor:
        flash("Doctor not found.", "danger")
        return redirect(url_for("patient.find_doctors"))

    today = date.today().isoformat()
    if request.method == "GET":
        return render_template("appointments/book.html", doctor=doctor, today=today)

    # POST — create appointment
    appt_date = request.form.get("date", "").strip()
    appt_time = request.form.get("time", "").strip()
    reason = request.form.get("reason", "").strip()
    mode = request.form.get("mode", doctor.get("consultation_mode", "In-person")).strip()

    if not all([appt_date, appt_time, reason]):
        flash("Please fill in all required fields.", "danger")
        return render_template("appointments/book.html", doctor=doctor, today=today), 400

    try:
        patient_id = g.current_user.get("patient_id")
        appointment = repo.create_appointment(patient_id, doctor_id, appt_date, appt_time, reason, mode)
    except ValueError as exc:
        flash(str(exc), "danger")
        return render_template("appointments/book.html", doctor=doctor, today=today), 400

    repo.audit(g.current_user["id"], "appointment_created", "appointment", appointment["id"])

    # Notify doctor
    doctor_user_id = doctor.get("user_id")
    if doctor_user_id:
        patient = repo.get_patient(patient_id)
        notifier.send(doctor_user_id, "appointment_requested",
                      "New Appointment Request",
                      f"{patient['name'] if patient else 'A patient'} has requested an appointment on {appt_date} at {appt_time}.")

    flash("Appointment requested successfully! You will be notified once the doctor confirms.", "success")
    return redirect(url_for("appointments.detail", appointment_id=appointment["id"]))


@appointments_bp.route("/")
@login_required(roles=["patient", "doctor"])
def list_appointments():
    repo = current_app.extensions["repository"]
    status_filter = request.args.get("status", "")

    if g.current_user["role"] == "patient":
        patient_id = g.current_user.get("patient_id")
        appointments = repo.appointments_for_patient(patient_id, status=status_filter or None)
        for appt in appointments:
            doc = repo.get_doctor(appt["doctor_id"])
            appt["doctor_name"] = doc["name"] if doc else "Unknown"
            appt["doctor_specialization"] = doc["specialization"] if doc else ""
    else:
        doctor_id = g.current_user.get("doctor_id")
        appointments = repo.appointments_for_doctor(doctor_id, status=status_filter or None)
        for appt in appointments:
            pat = repo.get_patient(appt["patient_id"])
            appt["patient_name"] = pat["name"] if pat else "Unknown"

    return render_template("appointments/list.html", appointments=appointments,
                           current_status=status_filter)


@appointments_bp.route("/<appointment_id>")
@login_required(roles=["patient", "doctor"])
def detail(appointment_id):
    repo = current_app.extensions["repository"]
    appointment = repo.appointment_context(appointment_id, g.current_user)
    if not appointment:
        flash("Appointment not found or access denied.", "danger")
        return redirect(url_for("appointments.list_appointments"))

    doctor = repo.get_doctor(appointment["doctor_id"])
    patient = repo.get_patient(appointment["patient_id"])
    return render_template("appointments/detail.html", appointment=appointment,
                           doctor=doctor, patient=patient)


@appointments_bp.route("/<appointment_id>/cancel", methods=["POST"])
@login_required(roles=["patient"])
def cancel(appointment_id):
    repo = current_app.extensions["repository"]
    notifier = current_app.extensions["notifications_service"]

    try:
        appointment = repo.update_appointment(appointment_id, "cancelled", "patient")
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("appointments.list_appointments"))

    repo.audit(g.current_user["id"], "appointment_cancelled", "appointment", appointment_id)

    # Notify doctor
    doctor = repo.get_doctor(appointment["doctor_id"])
    if doctor:
        patient = repo.get_patient(appointment["patient_id"])
        notifier.send(doctor["user_id"], "appointment_cancelled",
                      "Appointment Cancelled",
                      f"{patient['name'] if patient else 'A patient'} has cancelled the appointment on {appointment['date']}.")

    flash("Appointment cancelled.", "info")
    return redirect(url_for("appointments.list_appointments"))


@appointments_bp.route("/<appointment_id>/reschedule", methods=["POST"])
@login_required(roles=["patient"])
def reschedule(appointment_id):
    repo = current_app.extensions["repository"]
    notifier = current_app.extensions["notifications_service"]
    new_date = request.form.get("new_date", "").strip()
    new_time = request.form.get("new_time", "").strip()

    try:
        appointment = repo.update_appointment(appointment_id, "rescheduled", "patient",
                                               new_date=new_date, new_time=new_time)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("appointments.detail", appointment_id=appointment_id))

    repo.audit(g.current_user["id"], "appointment_rescheduled", "appointment", appointment_id)

    doctor = repo.get_doctor(appointment["doctor_id"])
    if doctor:
        patient = repo.get_patient(appointment["patient_id"])
        notifier.send(doctor["user_id"], "appointment_rescheduled",
                      "Appointment Rescheduled",
                      f"{patient['name'] if patient else 'A patient'} rescheduled to {new_date} at {new_time}.")

    flash("Appointment rescheduled successfully.", "success")
    return redirect(url_for("appointments.detail", appointment_id=appointment_id))


@appointments_bp.route("/<appointment_id>/accept", methods=["POST"])
@login_required(roles=["doctor"])
def accept(appointment_id):
    repo = current_app.extensions["repository"]
    notifier = current_app.extensions["notifications_service"]

    try:
        appointment = repo.update_appointment(appointment_id, "confirmed", "doctor")
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("doctor.dashboard"))

    repo.audit(g.current_user["id"], "appointment_confirmed", "appointment", appointment_id)

    patient = repo.get_patient(appointment["patient_id"])
    doctor = repo.get_doctor(appointment["doctor_id"])
    if patient:
        user = repo.get_user_by_email(patient.get("email", "")) or {}
        patient_user_id = patient.get("user_id")
        if patient_user_id:
            notifier.send(patient_user_id, "appointment_confirmed",
                          "Appointment Confirmed",
                          f"Your appointment with {doctor['name'] if doctor else 'your doctor'} on {appointment['date']} at {appointment['time']} has been confirmed.")

    flash("Appointment confirmed.", "success")
    return redirect(url_for("doctor.dashboard"))


@appointments_bp.route("/<appointment_id>/reject", methods=["POST"])
@login_required(roles=["doctor"])
def reject(appointment_id):
    repo = current_app.extensions["repository"]
    notifier = current_app.extensions["notifications_service"]

    try:
        appointment = repo.update_appointment(appointment_id, "rejected", "doctor")
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("doctor.dashboard"))

    repo.audit(g.current_user["id"], "appointment_rejected", "appointment", appointment_id)

    patient = repo.get_patient(appointment["patient_id"])
    if patient:
        patient_user_id = patient.get("user_id")
        if patient_user_id:
            notifier.send(patient_user_id, "appointment_rejected",
                          "Appointment Declined",
                          f"Your appointment request for {appointment['date']} was declined. Please try another time slot.")

    flash("Appointment declined.", "info")
    return redirect(url_for("doctor.dashboard"))


@appointments_bp.route("/<appointment_id>/complete", methods=["POST"])
@login_required(roles=["doctor"])
def complete(appointment_id):
    repo = current_app.extensions["repository"]
    notifier = current_app.extensions["notifications_service"]

    try:
        appointment = repo.update_appointment(appointment_id, "completed", "doctor")
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("doctor.dashboard"))

    repo.audit(g.current_user["id"], "appointment_completed", "appointment", appointment_id)

    patient = repo.get_patient(appointment["patient_id"])
    if patient:
        patient_user_id = patient.get("user_id")
        if patient_user_id:
            notifier.send(patient_user_id, "appointment_completed",
                          "Consultation Complete",
                          f"Your consultation on {appointment['date']} has been completed. Check your medical records for updates.")

    flash("Appointment marked as completed.", "success")
    return redirect(url_for("doctor.dashboard"))


@appointments_bp.route("/slots/<doctor_id>/<appt_date>")
@login_required(roles=["patient"])
def get_slots(doctor_id, appt_date):
    """AJAX endpoint — returns available time slots as JSON."""
    repo = current_app.extensions["repository"]
    slots = repo.slots_for_date(doctor_id, appt_date)
    return jsonify(slots)
