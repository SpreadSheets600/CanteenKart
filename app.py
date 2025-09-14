from app import create_app

from app.extensions import logger

app = create_app()


if __name__ == "__main__":
    socketio = app.extensions.get("socketio")

    if socketio is not None:
        logger.info("Starting App With SocketIO Support")
        socketio.run(app, host="0.0.0.0", port=5000)

    else:
        logger.error("Starting App Without SocketIO Support")
        app.run(host="0.0.0.0", port=5000)
