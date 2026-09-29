import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, g, render_template, request

from .config import Config
from .services.repository import build_repository
from .services.storage import build_storage
from .services.notifications import NotificationService
from .utils.security import get_current_user, new_csrf_token


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.extensions["repository"] = build_repository(app.config)
    app.extensions["storage"] = build_storage(app.config)
    app.extensions["notifications_service"] = NotificationService(
        app.extensions["repository"], app.config
    )

    configure_logging(app)

    from .auth.routes import auth_bp
    from .patient.routes import patient_bp
    from .doctor.routes import doctor_bp
    from .admin.routes import admin_bp
    from .appointments.routes import appointments_bp
    from .medical_records.routes import records_bp
    from .reports.routes import reports_bp
    from .notifications.routes import notifications_bp
    from .api.routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(records_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.before_request
    def attach_request_context():
        g.current_user = get_current_user(app.extensions["repository"])
        g.csrf_token = new_csrf_token()
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            # Skip CSRF for JSON API endpoints that use X-CSRF-Token header
            from .utils.security import verify_csrf
            verify_csrf()

    @app.context_processor
    def shared_template_context():
        unread = 0
        if g.current_user:
            unread = app.extensions["repository"].unread_notification_count(g.current_user["id"])
        return {"current_user": g.current_user, "csrf_token": g.csrf_token, "unread_count": unread}

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Cache-Control"] = "no-store" if request.path.startswith("/api/") else response.headers.get("Cache-Control", "no-cache")
        return response

    @app.route("/")
    def landing():
        return render_template("landing.html")

    @app.route("/health")
    def health():
        return {"status": "healthy", "service": "medtrack"}

    register_errors(app)
    return app


def configure_logging(app):
    if not app.debug:
        handler = RotatingFileHandler("medtrack.log", maxBytes=1_000_000, backupCount=3)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


def register_errors(app):
    messages = {
        400: ("We couldn't process that request.", "Please check your details and try again."),
        401: ("Please sign in to continue.", "Your session may have expired."),
        403: ("You don't have access to this page.", "MedTrack protects your health information with role-based access."),
        404: ("We couldn't find that page.", "The page may have moved or the link may be outdated."),
        429: ("Too many attempts.", "Please wait a moment before trying again."),
        500: ("Something went wrong.", "Please try again. If the issue continues, contact support."),
    }
    for status, content in messages.items():
        def make_handler(code, copy):
            def handler(_error):
                return render_template("errors/error.html", code=code, title=copy[0], message=copy[1]), code
            return handler
        app.register_error_handler(status, make_handler(status, content))
