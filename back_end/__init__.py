from flask import Flask
from flask import render_template

from back_end.config import get_config
from back_end.database_maintenance import ensure_sqlite_schema
from back_end.extensions import bcrypt, csrf, db, limiter, login_manager, migrate, socketio
from back_end.logging_config import configure_logging
from back_end.routes.api import api_bp
from back_end.routes.auth import auth_bp
from back_end.routes.main import main_bp
from back_end.socket_events import register_socket_events
from back_end.storage import ensure_upload_folders


def create_app(config_name=None):
    app = Flask(
        __name__,
        template_folder="../front_end/html",
        static_folder="../front_end",
        static_url_path="/front_end",
    )
    app.config.from_object(get_config(config_name))
    configure_logging(app)
    ensure_upload_folders(app)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    socketio.init_app(
        app,
        async_mode=app.config["SOCKETIO_ASYNC_MODE"],
        cors_allowed_origins=app.config["SOCKETIO_CORS_ORIGINS"],
        logger=False,
        engineio_logger=False,
    )

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp, url_prefix="/api")
    register_socket_events(socketio)
    register_security_headers(app)
    register_error_handlers(app)
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


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        app.logger.warning("Page not found: %s", error)
        return render_template("error.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        app.logger.exception("Unhandled server error: %s", error)
        return render_template("error.html"), 500


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        from back_end import models  # noqa: F401

        db.create_all()
        ensure_sqlite_schema(app, db)
        print("MedoChat database initialized.")
