from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from flask_wtf.csrf import generate_csrf

from back_end.extensions import db, limiter
from back_end.models.user import User
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
        return redirect(url_for("auth.login_page", error="Invalid username, email, or password."))

    login_user(user, remember=remember)
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
    db.session.commit()
    login_user(user)
    return redirect(url_for("main.chat"))


@auth_bp.post("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@auth_bp.get("/forgot-password")
def forgot_password_page():
    return render_template("forgot_password.html")


@auth_bp.get("/reset-password/<token>")
def reset_password_page(token):
    return render_template("reset_password.html", token=token)
