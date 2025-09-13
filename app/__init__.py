from flask import Flask, render_template

from .config import Config
from .extensions import db, login_manager, migrate


def create_app(config_object: str | object = Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from .blueprints.auth.routes import auth as auth_blueprint

    app.register_blueprint(auth_blueprint)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    # Database tables are managed via Flask-Migrate (Alembic).
    # Use `flask db upgrade` to create or migrate the schema.

    return app


__all__ = ["create_app"]
