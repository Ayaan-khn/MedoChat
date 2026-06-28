from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError

from back_end.extensions import db, socketio
from back_end.models import (
    Conversation,
    ConversationParticipant,
    FriendRequest,
    Friendship,
    Group,
    GroupMember,
    Message,
    Notification,
    User,
)
from back_end.validators import normalize_username

api_bp = Blueprint("api", __name__)


def _dt(value):
    return value.isoformat() if value else None


def _user_payload(user):
    return {
        "id": user.public_id,
        "username": user.username,
        "displayName": user.display_name,
        "email": user.email,
        "bio": user.bio,
        "status": user.status,
        "avatar": user.profile_picture,
        "coverPhoto": user.cover_photo,
        "emailVerified": user.is_email_verified,
        "joinedAt": _dt(user.created_at),
        "lastSeenAt": _dt(user.last_seen_at),
        "online": True,
    }


def _friend_payload(friend):
    latest_message = (
        Message.query.join(Conversation)
        .join(ConversationParticipant, ConversationParticipant.conversation_id == Conversation.id)
        .filter(ConversationParticipant.user_id == current_user.id)
        .filter(Message.sender_id.in_([current_user.id, friend.id]))
        .order_by(Message.created_at.desc())
        .first()
    )
    return {
        **_user_payload(friend),
        "lastMessage": latest_message.body if latest_message else "Start a conversation",
        "unread": 0,
    }


def _group_payload(group):
    return {
        "id": group.public_id,
        "name": group.name,
        "description": group.description,
        "icon": group.icon,
        "inviteCode": group.invite_code,
        "members": group.memberships.count(),
        "createdAt": _dt(group.created_at),
    }


def _conversation_payload(conversation):
    participants = [
        link.user for link in conversation.participants.order_by(ConversationParticipant.joined_at.asc()).all()
    ]
    other_users = [user for user in participants if user.id != current_user.id]
    title = conversation.title or (other_users[0].display_name if other_users else "Saved Messages")
    latest = conversation.messages.order_by(Message.created_at.desc()).first()
    return {
        "id": conversation.public_id,
        "title": title,
        "isGroup": conversation.is_group,
        "participants": [_user_payload(user) for user in participants],
        "lastMessage": latest.body if latest else "",
        "updatedAt": _dt(latest.created_at if latest else conversation.created_at),
    }


def _message_payload(message):
    return {
        "id": message.public_id,
        "conversationId": message.conversation.public_id,
        "senderId": message.sender.public_id,
        "senderName": message.sender.display_name,
        "body": "" if message.is_deleted else message.body,
        "isOwn": message.sender_id == current_user.id,
        "isEdited": message.is_edited,
        "isDeleted": message.is_deleted,
        "deliveredAt": _dt(message.delivered_at),
        "seenAt": _dt(message.seen_at),
        "createdAt": _dt(message.created_at),
    }


def _notification_payload(notification):
    return {
        "id": notification.public_id,
        "category": notification.category,
        "title": notification.title,
        "body": notification.body,
        "read": notification.is_read,
        "createdAt": _dt(notification.created_at),
    }


def _friendship_exists(user_id, friend_id):
    return Friendship.query.filter_by(user_id=user_id, friend_id=friend_id, status="active").first() is not None


def _create_notification(user_id, category, title, body=""):
    notification = Notification(user_id=user_id, category=category, title=title, body=body)
    db.session.add(notification)
    return notification


@api_bp.get("/me")
@login_required
def me():
    return jsonify({"user": _user_payload(current_user)})


@api_bp.get("/bootstrap")
@login_required
def bootstrap():
    friends = [
        _friend_payload(link.friend)
        for link in current_user.friendship_links.filter_by(status="active").order_by(Friendship.created_at.desc()).all()
    ]
    requests = FriendRequest.query.filter(
        or_(FriendRequest.sender_id == current_user.id, FriendRequest.receiver_id == current_user.id)
    ).order_by(FriendRequest.created_at.desc()).all()
    conversations = (
        Conversation.query.join(ConversationParticipant)
        .filter(ConversationParticipant.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
        .all()
    )
    groups = [
        _group_payload(link.group)
        for link in current_user.group_memberships.order_by(GroupMember.joined_at.desc()).all()
    ]
    notifications = current_user.notifications.order_by(Notification.created_at.desc()).limit(20).all()

    return jsonify(
        {
            "user": _user_payload(current_user),
            "friends": friends,
            "friendRequests": [
                {
                    "id": item.public_id,
                    "status": item.status,
                    "direction": "incoming" if item.receiver_id == current_user.id else "outgoing",
                    "user": _user_payload(item.sender if item.receiver_id == current_user.id else item.receiver),
                    "createdAt": _dt(item.created_at),
                }
                for item in requests
            ],
            "groups": groups,
            "conversations": [_conversation_payload(item) for item in conversations],
            "notifications": [_notification_payload(item) for item in notifications],
        }
    )


@api_bp.get("/users/search")
@login_required
def search_users():
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify({"users": []})

    normalized = normalize_username(query)
    users = (
        User.query.filter(User.id != current_user.id)
        .filter(or_(User.username.ilike(f"%{normalized}%"), User.public_id == query))
        .order_by(User.username.asc())
        .limit(12)
        .all()
    )
    return jsonify({"users": [_user_payload(user) for user in users]})


@api_bp.post("/friend-requests")
@login_required
def send_friend_request():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    target = User.query.filter(or_(User.username == normalize_username(query), User.public_id == query)).first()

    if not target or target.id == current_user.id:
        return jsonify({"error": "User not found."}), 404
    if _friendship_exists(current_user.id, target.id):
        return jsonify({"error": "You are already friends."}), 409

    existing = FriendRequest.query.filter(
        or_(
            and_(FriendRequest.sender_id == current_user.id, FriendRequest.receiver_id == target.id),
            and_(FriendRequest.sender_id == target.id, FriendRequest.receiver_id == current_user.id),
        )
    ).first()
    if existing and existing.status == "pending":
        return jsonify({"error": "A friend request is already pending."}), 409

    if existing:
        existing.sender_id = current_user.id
        existing.receiver_id = target.id
        existing.status = "pending"
    else:
        existing = FriendRequest(sender_id=current_user.id, receiver_id=target.id)
        db.session.add(existing)
    _create_notification(target.id, "friend_request", "New friend request", f"{current_user.display_name} sent you a request.")
    db.session.commit()
    return jsonify({"requestId": existing.public_id, "status": "pending"}), 201


@api_bp.post("/friend-requests/<request_id>/<action>")
@login_required
def handle_friend_request(request_id, action):
    friend_request = FriendRequest.query.filter_by(public_id=request_id).first_or_404()
    if action not in {"accept", "reject", "cancel"}:
        return jsonify({"error": "Unsupported action."}), 400

    if action == "cancel":
        if friend_request.sender_id != current_user.id:
            return jsonify({"error": "Only the sender can cancel this request."}), 403
        friend_request.status = "cancelled"
    elif action == "reject":
        if friend_request.receiver_id != current_user.id:
            return jsonify({"error": "Only the receiver can reject this request."}), 403
        friend_request.status = "rejected"
    else:
        if friend_request.receiver_id != current_user.id:
            return jsonify({"error": "Only the receiver can accept this request."}), 403
        friend_request.status = "accepted"
        for user_id, friend_id in (
            (friend_request.sender_id, friend_request.receiver_id),
            (friend_request.receiver_id, friend_request.sender_id),
        ):
            if not Friendship.query.filter_by(user_id=user_id, friend_id=friend_id).first():
                db.session.add(Friendship(user_id=user_id, friend_id=friend_id))
        _create_notification(friend_request.sender_id, "friend_request", "Friend request accepted", f"{current_user.display_name} accepted your request.")

    db.session.commit()
    return jsonify({"status": friend_request.status})


@api_bp.post("/friends/<user_id>/<action>")
@login_required
def handle_friend(user_id, action):
    friend = User.query.filter_by(public_id=user_id).first_or_404()
    if action not in {"remove", "block"}:
        return jsonify({"error": "Unsupported action."}), 400

    links = Friendship.query.filter(
        or_(
            and_(Friendship.user_id == current_user.id, Friendship.friend_id == friend.id),
            and_(Friendship.user_id == friend.id, Friendship.friend_id == current_user.id),
        )
    ).all()
    for link in links:
        link.status = "blocked" if action == "block" and link.user_id == current_user.id else "removed"
    db.session.commit()
    return jsonify({"status": "blocked" if action == "block" else "removed"})


@api_bp.post("/groups")
@login_required
def create_group():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    description = data.get("description", "").strip()
    if len(name) < 2:
        return jsonify({"error": "Group name must be at least 2 characters."}), 400

    group = Group(name=name[:120], description=description[:300], owner_id=current_user.id)
    db.session.add(group)
    db.session.flush()
    db.session.add(GroupMember(group_id=group.id, user_id=current_user.id, role="admin"))
    db.session.commit()
    return jsonify({"group": _group_payload(group)}), 201


@api_bp.get("/conversations/<conversation_id>/messages")
@login_required
def get_messages(conversation_id):
    conversation = Conversation.query.filter_by(public_id=conversation_id).first_or_404()
    if not ConversationParticipant.query.filter_by(conversation_id=conversation.id, user_id=current_user.id).first():
        return jsonify({"error": "Conversation unavailable."}), 403

    messages = conversation.messages.order_by(Message.created_at.asc()).limit(80).all()
    return jsonify({"messages": [_message_payload(message) for message in messages]})


@api_bp.post("/conversations")
@login_required
def create_conversation():
    data = request.get_json(silent=True) or {}
    participant_id = data.get("participantId")
    participant = User.query.filter_by(public_id=participant_id).first_or_404()
    if participant.id == current_user.id:
        return jsonify({"error": "Choose another user."}), 400

    existing = (
        Conversation.query.join(ConversationParticipant)
        .filter(Conversation.is_group.is_(False), ConversationParticipant.user_id == current_user.id)
        .all()
    )
    for conversation in existing:
        participant_ids = {link.user_id for link in conversation.participants.all()}
        if participant_ids == {current_user.id, participant.id}:
            return jsonify({"conversation": _conversation_payload(conversation)})

    conversation = Conversation(is_group=False)
    db.session.add(conversation)
    db.session.flush()
    db.session.add(ConversationParticipant(conversation_id=conversation.id, user_id=current_user.id))
    db.session.add(ConversationParticipant(conversation_id=conversation.id, user_id=participant.id))
    db.session.commit()
    return jsonify({"conversation": _conversation_payload(conversation)}), 201


@api_bp.post("/conversations/<conversation_id>/messages")
@login_required
def send_message(conversation_id):
    conversation = Conversation.query.filter_by(public_id=conversation_id).first_or_404()
    if not ConversationParticipant.query.filter_by(conversation_id=conversation.id, user_id=current_user.id).first():
        return jsonify({"error": "Conversation unavailable."}), 403

    data = request.get_json(silent=True) or {}
    body = data.get("body", "").strip()
    if not body:
        return jsonify({"error": "Message cannot be empty."}), 400
    if len(body) > 4000:
        return jsonify({"error": "Message is too long."}), 400

    message = Message(
        conversation_id=conversation.id,
        sender_id=current_user.id,
        body=body,
        delivered_at=datetime.now(timezone.utc),
    )
    db.session.add(message)
    db.session.commit()
    payload = _message_payload(message)
    socketio.emit("message_created", payload, room=conversation.public_id)
    return jsonify({"message": payload}), 201


@api_bp.post("/notifications/<notification_id>/read")
@login_required
def read_notification(notification_id):
    notification = Notification.query.filter_by(public_id=notification_id, user_id=current_user.id).first_or_404()
    notification.is_read = True
    db.session.commit()
    return jsonify({"status": "read"})
