from flask import Flask

from back_end.config import get_config
from back_end.extensions import bcrypt, csrf, db, limiter, login_manager, migrate, socketio
from back_end.routes.auth import auth_bp
from back_end.routes.main import main_bp
from back_end.socket_events import register_socket_events


def create_app(config_name=None):
    app = Flask(
        __name__,
        template_folder="../front_end/html",
        static_folder="../front_end",
        static_url_path="/front_end",
    )
    app.config.from_object(get_config(config_name))

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app, cors_allowed_origins=app.config["SOCKETIO_CORS_ORIGINS"])

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    register_socket_events(socketio)
    register_security_headers(app)
    register_cli(app)

    with app.app_context():
        from back_end import models  # noqa: F401

    return app


def register_security_headers(app):
    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        from back_end import models  # noqa: F401

        db.create_all()
        print("MedoChat database initialized.")
