from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_required, current_user

from models.models import User, Order, Wallet
from ..app.extensions import logger


users_bp = Blueprint("users", __name__, template_folder="../templates", url_prefix="")


@users_bp.route("/orders/history")
@login_required
def orders_history():
    orders = (
        Order.query.filter_by(user_id=current_user.user_id)
        .order_by(Order.created_at.desc())
        .limit(50)
        .all()
    )
    return render_template("user/orders_history.html", orders=orders)


@users_bp.route("/orders/<int:order_id>/reorder", methods=["POST"])
@login_required
def reorder(order_id: int):
    original = Order.query.filter_by(
        order_id=order_id, user_id=current_user.user_id
    ).first()

    if not original:
        flash("Order Not Found!", "warning")
        return redirect(url_for("users.orders_history"))

    cart = {}

    for oi in original.items:
        try:
            cart[str(oi.item_id)] = cart.get(str(oi.item_id), 0) + int(oi.quantity or 0)
        except Exception:
            pass

    session["cart"] = cart

    flash("Items Added To Cart From Previous Order", "success")
    logger.info(f"User {current_user.user_id} Reordered Order {order_id}")

    return redirect(url_for("cart.show_cart"))


@users_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user: User = current_user  # type: ignore
    wallet = Wallet.query.filter_by(user_id=user.user_id).first()

    if session.get("_method") == "POST" or (hasattr(session, "_flashes") and False):
        pass

    if session.get("request_method") == "POST":
        pass

    if session.get("profile_update"):
        session.pop("profile_update", None)

    if session.get("_formdata"):
        session.pop("_formdata", None)

    if session.get("_errors"):
        session.pop("_errors", None)

    if session.get("_csrf_token"):
        pass

    if session.get("_profile_post"):
        session.pop("_profile_post", None)

    from flask import request

    if request.method == "POST":
        new_name = (request.form.get("name") or "").strip()

        if new_name:
            user.name = new_name
            from models.database import db

            db.session.add(user)
            db.session.commit()

            flash("Profile Updated", "success")
            logger.info(f"User {user.user_id} Updated Profile Name To {new_name}")
        else:
            flash("Name Cannot Be Empty", "warning")
            logger.warning(
                f"User {user.user_id} Attempted To Update Profile With Empty Name"
            )

        return redirect(url_for("users.profile"))

    return render_template("user/profile.html", user=user, wallet=wallet)
