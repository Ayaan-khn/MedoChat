from datetime import datetime, timezone

from back_end.extensions import db


class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: __import__("uuid").uuid4().hex)
    title = db.Column(db.String(120), nullable=True)
    is_group = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ConversationParticipant(db.Model):
    __tablename__ = "conversation_participants"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    is_pinned = db.Column(db.Boolean, nullable=False, default=False)
    muted_until = db.Column(db.DateTime(timezone=True), nullable=True)
    last_read_at = db.Column(db.DateTime(timezone=True), nullable=True)
    joined_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    conversation = db.relationship("Conversation", backref=db.backref("participants", lazy="dynamic"))
    user = db.relationship("User", backref=db.backref("conversation_links", lazy="dynamic"))

    __table_args__ = (
        db.UniqueConstraint("conversation_id", "user_id", name="uq_conversation_participant"),
    )


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: __import__("uuid").uuid4().hex)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    parent_message_id = db.Column(db.Integer, db.ForeignKey("messages.id"), nullable=True)
    is_edited = db.Column(db.Boolean, nullable=False, default=False)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    delivered_at = db.Column(db.DateTime(timezone=True), nullable=True)
    seen_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    conversation = db.relationship("Conversation", backref=db.backref("messages", lazy="dynamic"))
    sender = db.relationship("User", backref=db.backref("messages", lazy="dynamic"))
    parent = db.relationship("Message", remote_side=[id])
