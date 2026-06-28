from flask_login import current_user
from flask_socketio import emit


def register_socket_events(socketio):
    @socketio.on("connect")
    def handle_connect():
        if current_user.is_authenticated:
            emit("presence", {"status": "online", "userId": current_user.public_id})

    @socketio.on("typing")
    def handle_typing(data):
        if current_user.is_authenticated:
            emit(
                "typing",
                {"userId": current_user.public_id, "conversationId": data.get("conversationId")},
                broadcast=True,
                include_self=False,
            )
