from werkzeug.security import generate_password_hash
from flask import Flask, render_template
from flask_login import LoginManager

from models.database import db
from models.models import User

from controllers.auth import auth as auth_blueprint


login_manager = LoginManager()
login_manager.login_view = "auth.login"


def create_app():
    app = Flask(__name__)
    app.debug = True

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///canteenkart.sqlite3"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "secretkey"

    db.init_app(app)
    login_manager.init_app(app)

    # -----------------------------
    # Blueprints
    # -----------------------------

    app.register_blueprint(auth_blueprint)

    with app.app_context():
        db.create_all()
        initialize_db()

    def register_error_handlers(app):
        @app.errorhandler(404)
        def page_not_found(e):
            return render_template("errors/404.html"), 404

        @app.errorhandler(500)
        def server_error(e):
            return render_template("errors/500.html"), 500

    register_error_handlers(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    return app


def initialize_db():
    if User.query.count() == 0:
        admin_user = User(
            phone="0000000000",
            name="Admin",
            role="admin",
            password_hash=generate_password_hash("adminpass"),
        )
        db.session.add(admin_user)
        from models.models import Wallet

        wallet = Wallet(user=admin_user, balance=0.0)
        db.session.add(wallet)
        db.session.commit()

        print("Admin User Created")


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
