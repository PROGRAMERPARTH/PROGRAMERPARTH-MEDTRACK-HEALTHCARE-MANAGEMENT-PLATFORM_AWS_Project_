"""Authentication blueprint — Register, Login, Logout."""
from flask import (
    Blueprint, current_app, flash, g, redirect, render_template,
    request, session, url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from ..utils.security import auth_rate_limited, login_required

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if g.current_user:
        return _redirect_for_role(g.current_user["role"])

    repo = current_app.extensions["repository"]
    notifier = current_app.extensions["notifications_service"]
    requested_role = request.args.get("role", "").lower()
    if not requested_role and request.form.get("role"):
        requested_role = request.form.get("role", "").lower()
    active_tab = "doctor" if requested_role == "doctor" else "patient"

    if request.method == "GET":
        return render_template("auth/register.html", active_tab=active_tab)

    form = request.form
    role = form.get("role", "patient").strip().lower()

    # --- Doctor Registration ---
    if role == "doctor":
        errors = []
        name = form.get("name", "").strip()
        if not name.startswith("Dr.") and not name.startswith("dr."):
            name = f"Dr. {name}"
        email = form.get("email", "").strip().lower()
        phone = form.get("phone", "").strip()
        specialization = form.get("specialization", "").strip()
        qualification = form.get("qualification", "").strip()
        experience = form.get("experience", "1").strip()
        clinic = form.get("clinic", "").strip()
        location = form.get("location", "").strip()
        fee = form.get("fee", "500").strip()
        mode = form.get("consultation_mode", "In-person & Video").strip()
        days = form.getlist("available_days")
        if not days:
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        slots = [s.strip() for s in form.get("time_slots", "").split(",") if s.strip()]
        if not slots:
            slots = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
        bio = form.get("bio", "").strip()
        password = form.get("password", "")
        confirm = form.get("confirm_password", "")

        if not all([name, email, phone, specialization, qualification, clinic, location, password]):
            errors.append("Please fill in all required doctor credentials.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if "@" not in email or "." not in email:
            errors.append("Enter a valid email address.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("auth/register.html", active_tab="doctor"), 400

        try:
            user = repo.create_doctor_user(
                {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "specialization": specialization,
                    "qualification": qualification,
                    "experience": experience,
                    "clinic": clinic,
                    "hospital": clinic,
                    "location": location,
                    "fee": fee,
                    "consultation_mode": mode,
                    "available_days": days,
                    "time_slots": slots,
                    "bio": bio or f"Specialist in {specialization} with {experience} years experience.",
                },
                generate_password_hash(password),
                status="pending",
            )
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("auth/register.html", active_tab="doctor"), 400

        repo.audit(user["id"], "doctor_registered_pending", "user", user["id"])

        # Send notification to Admin users
        admin_users = repo.admin_users()
        for admin in admin_users:
            notifier.send(
                admin["id"],
                "doctor_registration_pending",
                "New Doctor Registration Awaiting Approval",
                f"{name} ({specialization}, {clinic}) has registered and is awaiting your review and approval.",
            )

        flash("Doctor registration submitted successfully! Your application is pending admin review. You will be able to log in once your medical credentials are approved.", "success")
        return redirect(url_for("auth.login"))

    # --- Patient Registration ---
    errors = []
    name = form.get("name", "").strip()
    email = form.get("email", "").strip().lower()
    phone = form.get("phone", "").strip()
    dob = form.get("dob", "").strip()
    gender = form.get("gender", "").strip()
    address = form.get("address", "").strip()
    emergency_contact = form.get("emergency_contact", "").strip()
    password = form.get("password", "")
    confirm = form.get("confirm_password", "")

    if not all([name, email, phone, dob, gender, address, emergency_contact, password]):
        errors.append("All fields are required.")
    if password != confirm:
        errors.append("Passwords do not match.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if "@" not in email or "." not in email:
        errors.append("Enter a valid email address.")

    if errors:
        for err in errors:
            flash(err, "danger")
        return render_template("auth/register.html", active_tab="patient"), 400

    try:
        user = repo.create_patient_user(
            {"name": name, "email": email, "phone": phone, "dob": dob,
             "gender": gender, "address": address, "emergency_contact": emergency_contact},
            generate_password_hash(password),
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return render_template("auth/register.html", active_tab="patient"), 400

    repo.audit(user["id"], "register", "user", user["id"])
    session.clear()
    session["user_id"] = user["id"]
    session.permanent = True
    flash("Welcome to MedTrack! Your account has been created.", "success")
    return redirect(url_for("patient.dashboard"))


@auth_bp.route("/register/doctor", methods=["GET"])
def register_doctor():
    if g.current_user:
        return _redirect_for_role(g.current_user["role"])
    return render_template("auth/register.html", active_tab="doctor")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.current_user:
        return _redirect_for_role(g.current_user["role"])

    if request.method == "GET":
        return render_template("auth/login.html")

    repo = current_app.extensions["repository"]
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    auth_rate_limited(email)

    user = repo.get_user_by_email(email, include_hash=True)
    if not user or not check_password_hash(user["password_hash"], password):
        repo.audit(email, "login_failed", "auth", email)
        flash("Invalid email or password.", "danger")
        return render_template("auth/login.html"), 401

    if user.get("status") == "pending":
        flash("Your doctor registration request is currently pending admin approval. You will be able to log in once verified and approved by an administrator.", "warning")
        return render_template("auth/login.html"), 403

    if user.get("status") == "rejected":
        flash("Your doctor registration application was declined. Please contact the administrator.", "danger")
        return render_template("auth/login.html"), 403

    if user.get("status") != "active":
        flash("Your account has been deactivated. Contact support.", "danger")
        return render_template("auth/login.html"), 403

    repo.audit(user["id"], "login", "user", user["id"])
    session.clear()
    session["user_id"] = user["id"]
    session.permanent = True
    return _redirect_for_role(user["role"])


@auth_bp.route("/logout", methods=["POST"])
def logout():
    repo = current_app.extensions["repository"]
    if g.current_user:
        repo.audit(g.current_user["id"], "logout", "user", g.current_user["id"])
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))


def _redirect_for_role(role):
    destinations = {
        "patient": "patient.dashboard",
        "doctor": "doctor.dashboard",
        "admin": "admin.dashboard",
    }
    return redirect(url_for(destinations.get(role, "auth.login")))
