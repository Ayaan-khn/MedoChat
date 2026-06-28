import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(app):
    log_path = Path(app.config["LOG_FILE"])
    if not log_path.is_absolute():
        log_path = Path(app.root_path).parent / log_path
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(app.config["LOG_LEVEL"])

    app.logger.setLevel(app.config["LOG_LEVEL"])
    if not any(isinstance(handler, RotatingFileHandler) for handler in app.logger.handlers):
        app.logger.addHandler(file_handler)
