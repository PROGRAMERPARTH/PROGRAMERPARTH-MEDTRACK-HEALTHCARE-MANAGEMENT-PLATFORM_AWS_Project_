"""JSON API blueprint — RESTful endpoints for AJAX and external clients."""
from flask import Blueprint, current_app, g, jsonify, request

from ..utils.security import login_required

api_bp = Blueprint("api", __name__)


@api_bp.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "medtrack"})


@api_bp.route("/doctors")
@login_required(roles=["patient"])
def list_doctors():
    repo = current_app.extensions["repository"]
    filters = {k: request.args.get(k, "") for k in ("q", "specialization", "consultation_mode", "location", "min_experience")}
    doctors = repo.list_doctors(filters)
    return jsonify(doctors)


@api_bp.route("/doctors/<doctor_id>")
@login_required(roles=["patient"])
def get_doctor(doctor_id):
    repo = current_app.extensions["repository"]
    doctor = repo.get_doctor(doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404
    return jsonify(doctor)


@api_bp.route("/appointments")
@login_required(roles=["patient", "doctor"])
def list_appointments():
    repo = current_app.extensions["repository"]
    status = request.args.get("status", "")
    if g.current_user["role"] == "patient":
        return jsonify(repo.appointments_for_patient(g.current_user.get("patient_id"), status=status or None))
    return jsonify(repo.appointments_for_doctor(g.current_user.get("doctor_id"), status=status or None))


@api_bp.route("/notifications")
@login_required()
def list_notifications():
    repo = current_app.extensions["repository"]
    return jsonify(repo.notifications_for_user(g.current_user["id"]))


@api_bp.route("/notifications/<notification_id>/read", methods=["PUT"])
@login_required()
def mark_notification_read(notification_id):
    repo = current_app.extensions["repository"]
    result = repo.mark_notification_read(notification_id, g.current_user["id"])
    if not result:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"ok": True})


@api_bp.route("/notifications/unread-count")
@login_required()
def unread_count():
    repo = current_app.extensions["repository"]
    count = repo.unread_notification_count(g.current_user["id"])
    return jsonify({"count": count})
