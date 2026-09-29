"""Notifications blueprint — List and mark as read."""
from flask import (
    Blueprint, current_app, g, jsonify, render_template, request,
)

from ..utils.security import login_required

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@notifications_bp.route("/")
@login_required()
def list_notifications():
    repo = current_app.extensions["repository"]
    notifications = repo.notifications_for_user(g.current_user["id"])
    return render_template("notifications/list.html", notifications=notifications)


@notifications_bp.route("/<notification_id>/read", methods=["POST"])
@login_required()
def mark_read(notification_id):
    repo = current_app.extensions["repository"]
    repo.mark_notification_read(notification_id, g.current_user["id"])

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True})

    return render_template("notifications/list.html",
                           notifications=repo.notifications_for_user(g.current_user["id"]))


@notifications_bp.route("/mark-all-read", methods=["POST"])
@login_required()
def mark_all_read():
    repo = current_app.extensions["repository"]
    for n in repo.notifications_for_user(g.current_user["id"]):
        if not n["read"]:
            repo.mark_notification_read(n["id"], g.current_user["id"])

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True})

    return render_template("notifications/list.html",
                           notifications=repo.notifications_for_user(g.current_user["id"]))
