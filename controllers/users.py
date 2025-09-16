from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from flask_login import login_required, current_user

from models.models import Order, OrderItem
from app.extensions import db, logger


users_bp = Blueprint("users", __name__, template_folder="../templates", url_prefix="")


@users_bp.route("/orders/history")
@login_required
def orders_history():
    orders = (
        Order.query.options(
            db.selectinload(Order.items).selectinload(OrderItem.menu_item)
        )
        .filter_by(user_id=current_user.user_id)
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


@users_bp.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    profile_picture = request.form.get("profile_picture")

    if profile_picture:
        current_user.profile_picture = profile_picture
        db.session.commit()
        flash("Profile picture updated successfully!", "success")
        logger.info(f"User {current_user.user_id} updated profile picture")
    else:
        flash("Profile picture URL is required!", "warning")

    return redirect(url_for("users.profile"))
