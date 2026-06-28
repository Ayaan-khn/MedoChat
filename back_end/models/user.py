from datetime import datetime, timezone
from uuid import uuid4

from flask_login import UserMixin

from back_end.extensions import bcrypt, db, login_manager


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    bio = db.Column(db.String(280), nullable=False, default="")
    profile_picture = db.Column(db.String(255), nullable=True)
    cover_photo = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(120), nullable=False, default="Available")
    is_email_verified = db.Column(db.Boolean, nullable=False, default=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_active_account = db.Column(db.Boolean, nullable=False, default=True)
    last_seen_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return self.is_active_account

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    if not user_id or not user_id.isdigit():
        return None
    return db.session.get(User, int(user_id))
