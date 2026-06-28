from datetime import datetime, timezone

from flask_login import current_user
from flask_socketio import emit, join_room

from back_end.extensions import db
from back_end.models import Conversation, ConversationParticipant, Message


def _dt(value):
    return value.isoformat() if value else None


def _message_payload(message):
    return {
        "id": message.public_id,
        "conversationId": message.conversation.public_id,
        "senderId": message.sender.public_id,
        "senderName": message.sender.display_name,
        "body": "" if message.is_deleted else message.body,
        "isOwn": False,
        "isEdited": message.is_edited,
        "isDeleted": message.is_deleted,
        "deliveredAt": _dt(message.delivered_at),
        "seenAt": _dt(message.seen_at),
        "createdAt": _dt(message.created_at),
    }


def register_socket_events(socketio):
    @socketio.on("connect")
    def handle_connect(auth=None):
        if not current_user.is_authenticated:
            return False

        for link in current_user.conversation_links.all():
            join_room(link.conversation.public_id)

        emit(
            "connected",
            {
                "status": "ok",
                "userId": current_user.public_id,
                "username": current_user.username,
            },
        )
        emit(
            "presence_update",
            {"userId": current_user.public_id, "status": "online"},
            broadcast=True,
            include_self=False,
        )

    @socketio.on("test_message")
    def handle_test_message(data):
        if not current_user.is_authenticated:
            return

        emit(
            "test_message_echo",
            {
                "message": data.get("message", ""),
                "userId": current_user.public_id,
            },
        )

    @socketio.on("typing")
    def handle_typing(data):
        if not current_user.is_authenticated:
            return

        conversation_id = data.get("conversationId")
        conversation = Conversation.query.filter_by(public_id=conversation_id).first()
        if not conversation:
            return
        if not ConversationParticipant.query.filter_by(conversation_id=conversation.id, user_id=current_user.id).first():
            return

        emit(
            "typing",
            {
                "userId": current_user.public_id,
                "conversationId": conversation.public_id,
            },
            room=conversation.public_id,
            include_self=False,
        )

    @socketio.on("send_message")
    def handle_send_message(data):
        if not current_user.is_authenticated:
            return

        conversation_id = data.get("conversationId")
        body = data.get("body", "").strip()
        conversation = Conversation.query.filter_by(public_id=conversation_id).first()
        if not conversation or not body:
            return
        if not ConversationParticipant.query.filter_by(conversation_id=conversation.id, user_id=current_user.id).first():
            return

        message = Message(
            conversation_id=conversation.id,
            sender_id=current_user.id,
            body=body[:4000],
            delivered_at=datetime.now(timezone.utc),
        )
        db.session.add(message)
        db.session.commit()
        emit("message_created", _message_payload(message), room=conversation.public_id)

    @socketio.on("join_conversation")
    def handle_join_conversation(data):
        if not current_user.is_authenticated:
            return

        conversation_id = data.get("conversationId")
        conversation = Conversation.query.filter_by(public_id=conversation_id).first()
        if not conversation:
            return
        if ConversationParticipant.query.filter_by(conversation_id=conversation.id, user_id=current_user.id).first():
            join_room(conversation.public_id)
