from back_end import create_app
from back_end.extensions import socketio

app = create_app()


if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000, debug=app.config["DEBUG"])
