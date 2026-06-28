from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from flask_wtf.csrf import generate_csrf
from sqlalchemy.exc import IntegrityError

from back_end.extensions import db, limiter
from back_end.models.user import User
from back_end.tokens import generate_token, verify_token
from back_end.validators import normalize_email, normalize_username, validate_password

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/login")
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("main.chat"))
    return render_template("login.html")


@auth_bp.get("/csrf-token")
def csrf_token():
    return jsonify({"csrfToken": generate_csrf()})


@auth_bp.post("/login")
@limiter.limit("8 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.chat"))

    username_or_email = request.form.get("username_or_email", "").strip()
    password = request.form.get("password", "")
    remember = request.form.get("remember") == "on"

    user = User.query.filter(
        (User.username == normalize_username(username_or_email))
        | (User.email == normalize_email(username_or_email))
    ).first()

    if not user or not user.check_password(password):
        current_app.logger.warning("Failed login attempt for %s", username_or_email)
        return redirect(url_for("auth.login_page", error="Invalid username, email, or password."))

    login_user(user, remember=remember)
    current_app.logger.info("User logged in: %s", user.public_id)
    return redirect(url_for("main.chat"))


@auth_bp.get("/signup")
def signup_page():
    if current_user.is_authenticated:
        return redirect(url_for("main.chat"))
    return render_template("signup.html")


@auth_bp.get("/login.html")
def legacy_login_page():
    return redirect(url_for("auth.login_page"))


@auth_bp.get("/signup.html")
def legacy_signup_page():
    return redirect(url_for("auth.signup_page"))


@auth_bp.get("/forgot_password.html")
def legacy_forgot_password_page():
    return redirect(url_for("auth.forgot_password_page"))


@auth_bp.get("/reset_password.html")
def legacy_reset_password_page():
    return redirect(url_for("auth.forgot_password_page"))


@auth_bp.get("/index.html")
def legacy_index_page():
    return redirect(url_for("main.index"))


@auth_bp.post("/signup")
@limiter.limit("5 per minute")
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.chat"))

    username = normalize_username(request.form.get("username", ""))
    display_name = request.form.get("display_name", "").strip()
    email = normalize_email(request.form.get("email", ""))
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    errors = []
    if len(username) < 3 or len(username) > 32:
        errors.append("Username must be 3 to 32 characters.")
    if not display_name:
        errors.append("Display name is required.")
    if "@" not in email or "." not in email:
        errors.append("Enter a valid email address.")
    errors.extend(validate_password(password))
    if password != confirm_password:
        errors.append("Passwords do not match.")
    if User.query.filter_by(username=username).first():
        errors.append("That username is already taken.")
    if User.query.filter_by(email=email).first():
        errors.append("That email is already registered.")

    if errors:
        return redirect(url_for("auth.signup_page", error=errors[0]))

    user = User(username=username, display_name=display_name, email=email)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return redirect(url_for("auth.signup_page", error="Username or email is already registered."))
    verification_token = generate_token(current_app, "verify-email", user.public_id)
    current_app.logger.info("User signed up: %s", user.public_id)
    current_app.logger.info("Development email verification token for %s: %s", user.email, verification_token)
    login_user(user)
    return redirect(url_for("main.chat"))


@auth_bp.post("/logout")
def logout():
    if current_user.is_authenticated:
        current_user.last_seen_at = datetime.now(timezone.utc)
        db.session.commit()
        current_app.logger.info("User logged out: %s", current_user.public_id)
    logout_user()
    return redirect(url_for("main.index"))


@auth_bp.get("/forgot-password")
def forgot_password_page():
    return render_template("forgot_password.html")


@auth_bp.post("/forgot-password")
@limiter.limit("5 per minute")
def forgot_password():
    email = normalize_email(request.form.get("email", ""))
    user = User.query.filter_by(email=email).first()

    if user:
        token = generate_token(current_app, "reset-password", user.public_id)
        current_app.logger.info("Development password reset token for %s: %s", user.email, token)

    return redirect(
        url_for(
            "auth.forgot_password_page",
            notice="If that email exists, a reset link has been prepared.",
        )
    )


@auth_bp.get("/reset-password/<token>")
def reset_password_page(token):
    return render_template("reset_password.html", token=token)


@auth_bp.post("/reset-password/<token>")
@limiter.limit("5 per minute")
def reset_password(token):
    public_id = verify_token(current_app, token, "reset-password")
    if not public_id:
        return redirect(url_for("auth.forgot_password_page", error="Reset link is invalid or expired."))

    user = User.query.filter_by(public_id=public_id).first()
    if not user:
        return redirect(url_for("auth.forgot_password_page", error="Reset link is invalid or expired."))

    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")
    errors = validate_password(password)
    if password != confirm_password:
        errors.append("Passwords do not match.")

    if errors:
        return redirect(url_for("auth.reset_password_page", token=token, error=errors[0]))

    user.set_password(password)
    db.session.commit()
    current_app.logger.info("Password reset completed for user: %s", user.public_id)
    return redirect(url_for("auth.login_page", notice="Password reset complete. You can log in now."))


@auth_bp.get("/verify-email/<token>")
def verify_email(token):
    public_id = verify_token(current_app, token, "verify-email", max_age_seconds=86400)
    if not public_id:
        return redirect(url_for("auth.login_page", error="Verification link is invalid or expired."))

    user = User.query.filter_by(public_id=public_id).first()
    if not user:
        return redirect(url_for("auth.login_page", error="Verification link is invalid or expired."))

    user.is_email_verified = True
    db.session.commit()
    current_app.logger.info("Email verified for user: %s", user.public_id)
    return redirect(url_for("auth.login_page", notice="Email verified. You can log in now."))
