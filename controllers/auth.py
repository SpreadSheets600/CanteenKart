from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask import session

from models.database import db
from app.extensions import logger
from models.models import User, Wallet

auth = Blueprint(
    "auth", __name__, template_folder="../templates/auth", url_prefix="/auth"
)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        phone = request.form.get("phone")
        password = request.form.get("password")

        if not phone or not password:
            flash("Phone And Password Are Required!", "warning")
            logger.warning("Login Attempt Missing Phone or Password")

            return render_template("auth/login.html")

        user = User.query.filter_by(phone=phone).first()
        if (
            user
            and user.password_hash
            and check_password_hash(user.password_hash, password)
        ):
            login_user(user)

            session["user_id"] = user.get_id()
            session["user_name"] = user.name
            session["role"] = user.role

            flash("Logged In Successfully!", "success")
            logger.info(f"User Logged In : {user.phone} ( {user.role} )")

            next_page = request.args.get("next")
            return redirect(next_page or url_for("home"))

        flash("Invalid Phone Or Password!", "danger")
        logger.warning(f"Invalid Login Attempt For Phone : {phone}")

    return render_template("auth/login.html")


@auth.route("/logout")
@login_required
def logout():
    try:
        logout_user()
    except Exception:
        pass

    session.pop("user_id", None)
    session.pop("user_name", None)
    session.pop("role", None)

    flash("Logged Out!", "info")
    logger.info("User Logged Out")

    return redirect(url_for("auth.login"))


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        phone = request.form.get("phone")
        name = request.form.get("name") or ""
        email = request.form.get("email") or ""
        password = request.form.get("password")

        if not phone or not password:
            flash("Phone And Password Are Required!", "warning")
            logger.warning("Registration Attempt Missing Phone or Password")

            return render_template("auth/signup.html")

        if User.query.filter_by(phone=phone).first():
            flash("Phone Already Registered!", "warning")
            logger.warning(
                f"Registration Attempt For Already Registered Phone : {phone}"
            )

            return render_template("auth/signup.html")

        if email and User.query.filter_by(email=email).first():
            flash("Email Already Registered!", "warning")
            logger.warning(
                f"Registration Attempt For Already Registered Email : {email}"
            )

            return render_template("auth/signup.html")

        user = User(
            phone=phone,
            name=name or phone,
            email=email or None,
            role="student",
            password_hash=generate_password_hash(password),
            profile_picture=f"https://api.dicebear.com/9.x/lorelei/svg?seed={name or phone}",
        )
        db.session.add(user)
        db.session.commit()

        logger.info(f"New User Registered : {user.phone} ( {user.role} )")

        wallet = Wallet(user=user, balance=0.0)
        db.session.add(wallet)
        db.session.commit()

        flash("Registration Successfully Please Log In!", "success")
        logger.info(f"Wallet Created For User : {user.phone} ( {user.role} )")

        return redirect(url_for("auth.login"))

    return render_template("auth/signup.html")
