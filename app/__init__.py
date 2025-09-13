from flask import Flask

from .config import Config
from .extensions import db, login_manager


def create_app(config_object: str | object = Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)

    db.init_app(app)
    login_manager.init_app(app)

    from .blueprints.auth.routes import auth as auth_blueprint

    # Register auth blueprint at root so routes like /signup, /login, /logout work
    app.register_blueprint(auth_blueprint, url_prefix="")

    # simple home route
    from flask import session, render_template
    from .models.user import User

    @app.route("/")
    def home():
        return render_template("home.html")

    @app.context_processor
    def inject_user():
        # ensure session has user_name for templates
        user_name = session.get("user_name")
        if session.get("user_id") and not user_name:
            try:
                user = User.query.get(int(session.get("user_id")))
                if user:
                    session["user_name"] = user.name
            except Exception:
                pass
        return {}

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    with app.app_context():
        db.create_all()

    return app


__all__ = ["create_app"]
