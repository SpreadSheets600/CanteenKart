from app import create_app


app = create_app()


if __name__ == "__main__":
    socketio = app.extensions.get("socketio")
    if socketio is not None:
        # Run with Socket.IO server (supports WebSocket/long-polling)
        socketio.run(app, host="0.0.0.0", port=5000)
    else:
        # Fallback to plain Flask dev server
        app.run(host="0.0.0.0", port=5000)
