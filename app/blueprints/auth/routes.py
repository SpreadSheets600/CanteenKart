from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

from ...extensions import db
from ...models.user import User
from ...models.wallet import Wallet
from . import auth


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return wrapper


@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("confirm_password", "")

        # Basic validation
        if not phone or not password or not password2:
            flash("Phone and both password fields are required.", "warning")
            return render_template("signup.html")

        if len(phone) != 10 or not phone.isdigit():
            flash("Phone must be 10 digits.", "warning")
            return render_template("signup.html")

        if password != password2:
            flash("Passwords do not match.", "warning")
            return render_template("signup.html")

        # Check uniqueness
        if User.query.filter_by(phone=phone).first():
            flash("Phone already registered.", "warning")
            return render_template("signup.html")

        # Create user
        user = User(
            phone=phone,
            name=(name or phone),
            role="student",
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()

        # Create wallet
        wallet = Wallet(user=user, balance=0.0)
        db.session.add(wallet)
        db.session.commit()

        # Set session
        session["user_id"] = user.get_id()
        session["role"] = user.role

        flash("Signup successful.", "success")
        return redirect(url_for("home"))

    return render_template("signup.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        if not phone or not password:
            flash("Phone and password are required.", "warning")
            return render_template("login.html")

        user = User.query.filter_by(phone=phone).first()
        if (
            not user
            or not user.password_hash
            or not check_password_hash(user.password_hash, password)
        ):
            flash("Invalid phone or password.", "danger")
            return render_template("login.html")

        # Set session
        session["user_id"] = user.get_id()
        session["role"] = user.role

        flash("Logged in successfully.", "success")
        return redirect(url_for("home"))

    return render_template("login.html")


@auth.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("login"))
