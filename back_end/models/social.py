from datetime import datetime, timezone
from uuid import uuid4

from back_end.extensions import db


class FriendRequest(db.Model):
    __tablename__ = "friend_requests"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    sender = db.relationship("User", foreign_keys=[sender_id], backref=db.backref("sent_friend_requests", lazy="dynamic"))
    receiver = db.relationship("User", foreign_keys=[receiver_id], backref=db.backref("received_friend_requests", lazy="dynamic"))

    __table_args__ = (
        db.UniqueConstraint("sender_id", "receiver_id", name="uq_friend_request_pair"),
    )


class Friendship(db.Model):
    __tablename__ = "friendships"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    friend_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="active", index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("friendship_links", lazy="dynamic"))
    friend = db.relationship("User", foreign_keys=[friend_id])

    __table_args__ = (
        db.UniqueConstraint("user_id", "friend_id", name="uq_friendship_pair"),
    )


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(300), nullable=False, default="")
    icon = db.Column(db.String(255), nullable=True)
    invite_code = db.Column(db.String(36), unique=True, nullable=False, default=lambda: uuid4().hex)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    owner = db.relationship("User", backref=db.backref("owned_groups", lazy="dynamic"))


class GroupMember(db.Model):
    __tablename__ = "group_members"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default="member")
    joined_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    group = db.relationship("Group", backref=db.backref("memberships", lazy="dynamic"))
    user = db.relationship("User", backref=db.backref("group_memberships", lazy="dynamic"))

    __table_args__ = (
        db.UniqueConstraint("group_id", "user_id", name="uq_group_member"),
    )


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    category = db.Column(db.String(40), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    body = db.Column(db.String(300), nullable=False, default="")
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", backref=db.backref("notifications", lazy="dynamic"))
