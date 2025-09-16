import os
from flask import Flask, current_app
from pathlib import Path
from datetime import datetime

from .config import Config
from .extensions import db, login_manager, logger


def create_app(config_object: str | object = Config):
    project_root = Path(__file__).resolve().parents[1]
    templates_dir = project_root / "templates"
    static_dir = project_root / "static"

    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=str(templates_dir),
        static_folder=str(static_dir),
    )
    app.config.from_object(config_object)

    try:
        Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")

    if isinstance(uri, str) and uri.startswith("sqlite:///instance/"):
        rel_path = uri.split("sqlite:///instance/", 1)[1]
        abs_db_path = os.path.join(app.instance_path, rel_path)

        Path(os.path.dirname(abs_db_path)).mkdir(parents=True, exist_ok=True)

        try:
            logger.info("Creating DB File If Not Exists .... ")
            Path(abs_db_path).touch(exist_ok=True)
        except Exception:
            pass

        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + abs_db_path

    db.init_app(app)
    login_manager.init_app(app)

    def timeago(dt):
        if not dt:
            return ""

        now = datetime.utcnow()
        diff = now - dt.replace(tzinfo=None) if dt.tzinfo else now - dt

        seconds = diff.total_seconds()

        if seconds < 60:
            return "just now"
        minutes = seconds / 60
        if minutes < 60:
            return f"{int(minutes)} minute{'s' if int(minutes) != 1 else ''} ago"
        hours = minutes / 60
        if hours < 24:
            return f"{int(hours)} hour{'s' if int(hours) != 1 else ''} ago"
        days = hours / 24
        if days < 7:
            return f"{int(days)} day{'s' if int(days) != 1 else ''} ago"
        weeks = days / 7
        if weeks < 4:
            return f"{int(weeks)} week{'s' if int(weeks) != 1 else ''} ago"
        months = days / 30
        if months < 12:
            return f"{int(months)} month{'s' if int(months) != 1 else ''} ago"
        years = days / 365
        return f"{int(years)} year{'s' if int(years) != 1 else ''} ago"

    app.jinja_env.filters["timeago"] = timeago

    try:
        from flask_socketio import SocketIO, join_room

        socketio = SocketIO(cors_allowed_origins="*")
        socketio.init_app(app)

        app.extensions["socketio"] = socketio
        app.config["ENABLE_SOCKETIO"] = True

        @socketio.on("connect")
        def _socket_on_connect():
            from flask import session as _session

            try:
                user_id = _session.get("user_id")
                role = _session.get("role")

                if role == "owner":
                    logger.info(f"Owner With ID {user_id} Connected To SocketIO")
                    join_room("owners")

                if user_id:
                    logger.info(f"User With ID {user_id} Connected To SocketIO")
                    join_room(f"user_{user_id}")

            except Exception:
                pass

    except Exception:
        logger.warning("SocketIO Not Enabled")
        app.config["ENABLE_SOCKETIO"] = False

    from .models.user import User

    @login_manager.user_loader
    def load_user(user_id: str | int):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    from flask import session, render_template

    @app.route("/")
    def home():
        return render_template("home.html")

    from controllers.auth import auth as auth_bp
    from controllers.orders import orders_bp
    from controllers.owners import owners_bp
    from controllers.users import users_bp
    from controllers.menu import menu_bp
    from controllers.cart import cart_bp

    app.register_blueprint(orders_bp)
    app.register_blueprint(owners_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(cart_bp)

    @app.context_processor
    def inject_user():
        from .models.menu_item import MenuItem

        user_name = session.get("user_name")
        user = None
        if session.get("user_id"):
            try:
                user = User.query.get(int(session.get("user_id")))
                if user and not user_name:
                    session["user_name"] = user.name
                    user_name = user.name
            except Exception:
                pass

        cart = session.get("cart", {})

        cart_count = 0
        cart_subtotal = 0.0
        for item_id_str, qty in cart.items():
            try:
                item_id = int(item_id_str)
                qty = int(qty)
                item = MenuItem.query.get(item_id)
                if item:
                    price = item.price
                    if user and user.email and user.role == 'student':
                        price *= 0.9
                    cart_count += qty
                    cart_subtotal += price * qty
            except Exception:
                continue

        return {
            "user": user,
            "user_name": user_name,
            "cart_count": cart_count,
            "cart_subtotal": cart_subtotal,
            "announcement": current_app.config.get("ANNOUNCEMENT", ""),
        }

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    with app.app_context():
        db.create_all()

        try:
            from werkzeug.security import generate_password_hash

            from .models.wallet import Wallet
            from .models.user import User

            admin_password = app.config.get("ADMIN_PASSWORD")
            admin_phone = app.config.get("ADMIN_PHONE")

            if admin_phone and admin_password:
                admin = User.query.filter_by(phone=admin_phone).first()

                if not admin:
                    pw_hash = generate_password_hash(admin_password)
                    admin = User(
                        phone=admin_phone,
                        name="Admin",
                        role="owner",
                        password_hash=pw_hash,
                    )
                    db.session.add(admin)
                    db.session.commit()

                    logger.info(
                        f"Created Admin Creds : {admin_phone} : {admin_password}"
                    )

                else:
                    if admin.role != "owner":
                        admin.role = "owner"
                        db.session.add(admin)
                        db.session.commit()

                w = Wallet.query.filter_by(user_id=admin.user_id).first()

                if not w:
                    w = Wallet(user_id=admin.user_id, balance=0.0)
                    db.session.add(w)
                    db.session.commit()

        except Exception:
            pass

    return app


__all__ = ["create_app"]
