"""Admin blueprint — System dashboard, User/Doctor management."""
from flask import (
    Blueprint, current_app, flash, g, redirect, render_template,
    request, url_for,
)

from ..utils.security import login_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required(roles=["admin"])
def dashboard():
    repo = current_app.extensions["repository"]
    stats = repo.dashboard_stats()
    users = repo.all_users()
    appointments = repo.all_appointments()[:15]
    audit = repo.recent_audit()

    # Enrich appointments with names
    for appt in appointments:
        pat = repo.get_patient(appt["patient_id"])
        doc = repo.get_doctor(appt["doctor_id"])
        appt["patient_name"] = pat["name"] if pat else "Unknown"
        appt["doctor_name"] = doc["name"] if doc else "Unknown"

    return render_template("admin/dashboard.html", stats=stats, users=users,
                           appointments=appointments, audit=audit)


@admin_bp.route("/users")
@login_required(roles=["admin"])
def users():
    repo = current_app.extensions["repository"]
    all_users = repo.all_users()
    role_filter = request.args.get("role", "")
    if role_filter:
        all_users = [u for u in all_users if u["role"] == role_filter]
    return render_template("admin/users.html", users=all_users, current_role=role_filter)


@admin_bp.route("/users/<user_id>/toggle", methods=["POST"])
@login_required(roles=["admin"])
def toggle_user(user_id):
    repo = current_app.extensions["repository"]
    user = repo.users.get(user_id)
    if user and user["id"] != g.current_user["id"]:
        user["status"] = "inactive" if user["status"] == "active" else "active"
        repo.audit(g.current_user["id"], f"user_{user['status']}", "user", user_id)
        flash(f"User {user['name']} is now {user['status']}.", "success")
    else:
        flash("Cannot modify this account.", "danger")
    return redirect(url_for("admin.users"))


@admin_bp.route("/doctors")
@login_required(roles=["admin"])
def doctors():
    repo = current_app.extensions["repository"]
    status_filter = request.args.get("status", "").strip().lower()
    
    # Get all doctors including unverified
    all_doctors = repo.list_doctors(include_unverified=True)
    
    pending_count = sum(1 for d in all_doctors if d.get("verification_status") == "Pending Approval" or d.get("user_status") == "pending")
    verified_count = sum(1 for d in all_doctors if d.get("verification_status") == "Verified" and d.get("user_status") == "active")
    
    if status_filter == "pending":
        filtered_doctors = [d for d in all_doctors if d.get("verification_status") == "Pending Approval" or d.get("user_status") == "pending"]
    elif status_filter == "verified":
        filtered_doctors = [d for d in all_doctors if d.get("verification_status") == "Verified" and d.get("user_status") == "active"]
    elif status_filter == "rejected":
        filtered_doctors = [d for d in all_doctors if d.get("verification_status") == "Rejected" or d.get("user_status") == "rejected"]
    else:
        filtered_doctors = all_doctors

    return render_template(
        "admin/doctors.html",
        doctors=filtered_doctors,
        current_status=status_filter,
        total_count=len(all_doctors),
        pending_count=pending_count,
        verified_count=verified_count,
    )


@admin_bp.route("/doctors/<doctor_id>/approve", methods=["POST"])
@login_required(roles=["admin"])
def approve_doctor(doctor_id):
    repo = current_app.extensions["repository"]
    notifier = current_app.extensions["notifications_service"]
    try:
        doctor = repo.approve_doctor(doctor_id, g.current_user["id"])
        # Send approval notification to doctor
        user_id = doctor.get("user_id")
        if user_id:
            notifier.send(
                user_id,
                "doctor_account_approved",
                "Doctor Account Approved!",
                f"Congratulations {doctor['name']}! Your medical credentials have been verified and your MedTrack doctor portal is now active.",
            )
        flash(f"Doctor {doctor['name']} has been approved and activated successfully.", "success")
    except ValueError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("admin.doctors", status=request.args.get("status", "")))


@admin_bp.route("/doctors/<doctor_id>/reject", methods=["POST"])
@login_required(roles=["admin"])
def reject_doctor(doctor_id):
    repo = current_app.extensions["repository"]
    notifier = current_app.extensions["notifications_service"]
    try:
        doctor = repo.reject_doctor(doctor_id, g.current_user["id"])
        user_id = doctor.get("user_id")
        if user_id:
            notifier.send(
                user_id,
                "doctor_account_rejected",
                "Doctor Account Application Status",
                f"Your registration application for MedTrack could not be approved at this time.",
            )
        flash(f"Doctor {doctor['name']} application was declined.", "info")
    except ValueError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("admin.doctors", status=request.args.get("status", "")))


@admin_bp.route("/appointments")
@login_required(roles=["admin"])
def appointments():
    repo = current_app.extensions["repository"]
    appointments = repo.all_appointments()
    status_filter = request.args.get("status", "")
    if status_filter:
        appointments = [a for a in appointments if a["status"] == status_filter]

    for appt in appointments:
        pat = repo.get_patient(appt["patient_id"])
        doc = repo.get_doctor(appt["doctor_id"])
        appt["patient_name"] = pat["name"] if pat else "Unknown"
        appt["doctor_name"] = doc["name"] if doc else "Unknown"

    return render_template("admin/appointments.html", appointments=appointments,
                           current_status=status_filter)


@admin_bp.route("/audit")
@login_required(roles=["admin"])
def audit_logs():
    repo = current_app.extensions["repository"]
    logs = list(reversed(repo.audit_logs))
    return render_template("admin/audit.html", logs=logs)
