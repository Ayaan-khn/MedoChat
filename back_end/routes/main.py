from pathlib import Path

from flask import Blueprint, redirect, render_template, send_from_directory, url_for
from flask_login import login_required

main_bp = Blueprint("main", __name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@main_bp.get("/")
def index():
    return render_template("index.html")


@main_bp.get("/about")
def about():
    return render_template("about.html")


@main_bp.get("/chat")
@login_required
def chat():
    return render_template("chat.html")


@main_bp.get("/login.html")
def legacy_login():
    return redirect(url_for("auth.login_page"))


@main_bp.get("/signup.html")
def legacy_signup():
    return redirect(url_for("auth.signup_page"))


@main_bp.get("/about.html")
def legacy_about():
    return redirect(url_for("main.about"))


@main_bp.get("/css/<path:filename>")
def css(filename):
    return send_from_directory(PROJECT_ROOT / "front_end" / "css", filename)


@main_bp.get("/js/<path:filename>")
def js(filename):
    return send_from_directory(PROJECT_ROOT / "front_end" / "js", filename)


@main_bp.get("/images/<path:filename>")
def images(filename):
    return send_from_directory(PROJECT_ROOT / "images", filename)


@main_bp.get("/pdf/<path:filename>")
def pdf(filename):
    return send_from_directory(PROJECT_ROOT / "pdf", filename)
