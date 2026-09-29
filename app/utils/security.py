import functools
import secrets
import time
from collections import defaultdict, deque

from flask import abort, current_app, flash, g, redirect, request, session, url_for


_attempts = defaultdict(deque)


def new_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def verify_csrf():
    if current_app.config.get("TESTING"):
        return
    # JSON clients must send X-CSRF-Token; HTML forms use the hidden input.
    token = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
    if not token or not secrets.compare_digest(token, session.get("csrf_token", "")):
        abort(400)


def get_current_user(repository):
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = repository.get_user(user_id)
    if not user or user.get("status") != "active":
        session.clear()
        return None
    return user


def login_required(roles=None):
    allowed = set(roles or [])
    def decorator(view):
        @functools.wraps(view)
        def wrapped(*args, **kwargs):
            if not g.get("current_user"):
                flash("Please sign in to access this page.", "warning")
                return redirect(url_for("auth.login"))
            if allowed and g.current_user["role"] not in allowed:
                current_app.extensions["repository"].audit(g.current_user["id"], "permission_denied", "route", request.path)
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def auth_rate_limited(key, limit=5, window=300):
    if current_app.config.get("TESTING"):
        return
    now = time.monotonic()
    entries = _attempts[key]
    while entries and now - entries[0] > window:
        entries.popleft()
    if len(entries) >= limit:
        abort(429)
    entries.append(now)


def can_access_patient_context(repository, user, patient_id):
    if user["role"] == "admin":
        return False  # Explicit workflows only; this application does not expose medical detail to admins.
    if user["role"] == "patient":
        return user.get("patient_id") == patient_id
    return repository.doctor_has_patient_context(user.get("doctor_id"), patient_id)


def allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions
