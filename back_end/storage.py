from pathlib import Path

UPLOAD_FOLDERS = (
    "profile_pictures",
    "group_icons",
    "stories",
    "voice_notes",
    "images",
    "documents",
    "temp",
)


def ensure_upload_folders(app):
    root = Path(app.config["UPLOAD_ROOT"])
    if not root.is_absolute():
        root = Path(app.root_path).parent / root

    root.mkdir(parents=True, exist_ok=True)
    for folder in UPLOAD_FOLDERS:
        (root / folder).mkdir(parents=True, exist_ok=True)
