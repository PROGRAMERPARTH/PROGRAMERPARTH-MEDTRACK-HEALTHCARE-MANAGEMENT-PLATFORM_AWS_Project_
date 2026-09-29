"""Reports blueprint — Upload and view diagnosis reports."""
from flask import (
    Blueprint, current_app, flash, g, redirect, render_template,
    request, send_file, url_for,
)

from ..utils.security import allowed_file, login_required

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/")
@login_required(roles=["patient", "doctor"])
def list_reports():
    repo = current_app.extensions["repository"]

    if g.current_user["role"] == "patient":
        patient_id = g.current_user.get("patient_id")
        reports = repo.reports_for_patient(patient_id)
        for rpt in reports:
            if rpt.get("doctor_id"):
                doc = repo.get_doctor(rpt["doctor_id"])
                rpt["doctor_name"] = doc["name"] if doc else ""
    else:
        doctor_id = g.current_user.get("doctor_id")
        reports = repo.reports_for_doctor(doctor_id)
        for rpt in reports:
            pat = repo.get_patient(rpt["patient_id"])
            rpt["patient_name"] = pat["name"] if pat else "Unknown"

    return render_template("reports/list.html", reports=reports)


@reports_bp.route("/upload", methods=["GET", "POST"])
@login_required(roles=["patient"])
def upload():
    repo = current_app.extensions["repository"]
    notifier = current_app.extensions["notifications_service"]
    storage = current_app.extensions["storage"]
    patient_id = g.current_user.get("patient_id")

    # Get patient's appointments for the dropdown
    appointments = repo.appointments_for_patient(patient_id)
    appointment_choices = [a for a in appointments if a["status"] in {"confirmed", "completed", "requested"}]
    for appt in appointment_choices:
        doc = repo.get_doctor(appt["doctor_id"])
        appt["doctor_name"] = doc["name"] if doc else "Unknown"

    if request.method == "GET":
        return render_template("reports/upload.html", appointments=appointment_choices)

    title = request.form.get("title", "").strip()
    report_type = request.form.get("report_type", "").strip()
    description = request.form.get("description", "").strip()
    report_date = request.form.get("report_date", "").strip()
    appointment_id = request.form.get("appointment_id", "").strip()
    file = request.files.get("report_file")

    # Validation
    errors = []
    if not all([title, report_type, report_date]):
        errors.append("Title, report type, and date are required.")
    if not file or file.filename == "":
        errors.append("Please select a file to upload.")
    elif not allowed_file(file.filename, current_app.config["ALLOWED_REPORT_EXTENSIONS"]):
        errors.append("Only PDF, PNG, JPG files are allowed.")

    if errors:
        for err in errors:
            flash(err, "danger")
        return render_template("reports/upload.html", appointments=appointment_choices), 400

    # Save file
    try:
        file_reference = storage.save(file)
    except Exception:
        flash("File upload failed. Please try again.", "danger")
        return render_template("reports/upload.html", appointments=appointment_choices), 500

    report = repo.create_report(patient_id, appointment_id or None, title,
                                 report_type, description, report_date,
                                 file_reference, file.filename)
    repo.audit(g.current_user["id"], "report_uploaded", "report", report["id"])

    # Notify doctor if report is linked to an appointment
    if appointment_id:
        appointment = repo.get_appointment(appointment_id)
        if appointment:
            doctor = repo.get_doctor(appointment["doctor_id"])
            if doctor:
                patient = repo.get_patient(patient_id)
                notifier.send(doctor["user_id"], "report_submitted",
                              "New Report Submitted",
                              f"{patient['name'] if patient else 'A patient'} submitted a {report_type} report.")

    flash("Report uploaded successfully.", "success")
    return redirect(url_for("reports.list_reports"))


@reports_bp.route("/<report_id>/review", methods=["POST"])
@login_required(roles=["doctor"])
def review(report_id):
    repo = current_app.extensions["repository"]
    notifier = current_app.extensions["notifications_service"]
    report = repo.get_report(report_id)

    if not report:
        flash("Report not found.", "danger")
        return redirect(url_for("reports.list_reports"))

    doctor_id = g.current_user.get("doctor_id")
    if report.get("doctor_id") != doctor_id:
        flash("You do not have access to this report.", "danger")
        return redirect(url_for("reports.list_reports"))

    repo.update_report_status(report_id, "reviewed")
    repo.audit(g.current_user["id"], "report_reviewed", "report", report_id)

    patient = repo.get_patient(report["patient_id"])
    if patient:
        patient_user_id = patient.get("user_id")
        if patient_user_id:
            notifier.send(patient_user_id, "report_reviewed",
                          "Report Reviewed",
                          f"Your {report['report_type']} report has been reviewed by your doctor.")

    flash("Report marked as reviewed.", "success")
    return redirect(url_for("reports.list_reports"))


@reports_bp.route("/<report_id>/download")
@login_required(roles=["patient", "doctor"])
def download(report_id):
    repo = current_app.extensions["repository"]
    storage = current_app.extensions["storage"]
    report = repo.get_report(report_id)

    if not report:
        flash("Report not found.", "danger")
        return redirect(url_for("reports.list_reports"))

    # Authorization check
    if g.current_user["role"] == "patient" and report["patient_id"] != g.current_user.get("patient_id"):
        flash("Access denied.", "danger")
        return redirect(url_for("reports.list_reports"))
    if g.current_user["role"] == "doctor" and report.get("doctor_id") != g.current_user.get("doctor_id"):
        flash("Access denied.", "danger")
        return redirect(url_for("reports.list_reports"))

    file_path = storage.path(report["file_reference"])
    if not file_path or not file_path.exists():
        flash("File not found on server.", "danger")
        return redirect(url_for("reports.list_reports"))

    return send_file(file_path, download_name=report.get("original_filename", "report"),
                     as_attachment=True)
