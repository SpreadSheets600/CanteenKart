from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from ...extensions import db
from ...models.user import User
from ...models.wallet import Wallet
from . import auth


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        phone = request.form.get("phone")
        password = request.form.get("password")

        if not phone or not password:
            flash("Phone And Password Are Required!", "warning")
            return render_template("auth/auth.html")

        user = User.query.filter_by(phone=phone).first()
        if (
            user
            and user.password_hash
            and check_password_hash(user.password_hash, password)
        ):
            login_user(user)
            flash("Logged In Successfully!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("index"))

        flash("Invalid Phone Or Password!", "danger")

    return render_template("auth/auth.html")


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged Out!", "info")
    return redirect(url_for("auth.login"))


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        phone = request.form.get("phone")
        name = request.form.get("name") or ""
        password = request.form.get("password")

        if not phone or not password:
            flash("Phone And Password Are Required!", "warning")
            return render_template("auth/auth.html")

        if User.query.filter_by(phone=phone).first():
            flash("Phone Already Registered!", "warning")
            return render_template("auth/auth.html")

        user = User(
            phone=phone,
            name=name or phone,
            role="student",
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()

        wallet = Wallet(user=user, balance=0.0)
        db.session.add(wallet)
        db.session.commit()

        flash("Registration Successfully Please Log In!", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/auth.html")
