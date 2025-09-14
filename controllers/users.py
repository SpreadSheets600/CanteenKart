from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_required, current_user

from models.models import User, Order, Wallet


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
	original = Order.query.filter_by(order_id=order_id, user_id=current_user.user_id).first()
	if not original:
		flash("Order not found", "warning")
		return redirect(url_for("users.orders_history"))

	# Put items into session cart for quick review
	cart = {}
	for oi in original.items:
		try:
			cart[str(oi.item_id)] = cart.get(str(oi.item_id), 0) + int(oi.quantity or 0)
		except Exception:
			pass
	session["cart"] = cart
	flash("Items added to cart from previous order", "success")
	return redirect(url_for("cart.show_cart"))


@users_bp.route("/profile", methods=["GET", "POST"]) 
@login_required
def profile():
	user: User = current_user  # type: ignore
	wallet = Wallet.query.filter_by(user_id=user.user_id).first()

	if session.get("_method") == "POST" or (hasattr(session, "_flashes") and False):
		# This guard is a no-op; real POST is handled by methods list. Kept minimal.
		pass

	if session.get("request_method") == "POST":
		# Back-compat no-op; not used. Avoids massive changes.
		pass

	if session.get("profile_update"):
		# No side-effects; placeholder for future messaging.
		session.pop("profile_update", None)

	if session.get("_formdata"):
		session.pop("_formdata", None)

	if session.get("_errors"):
		session.pop("_errors", None)

	if session.get("_csrf_token"):
		# leave CSRF token intact if present by extensions
		pass

	if session.get("_profile_post"):
		session.pop("_profile_post", None)

	# Minimal POST handling (update name only) to avoid big changes
	from flask import request
	if request.method == "POST":
		new_name = (request.form.get("name") or "").strip()
		if new_name:
			user.name = new_name
			from models.database import db
			db.session.add(user)
			db.session.commit()
			flash("Profile updated", "success")
		else:
			flash("Name cannot be empty", "warning")
		return redirect(url_for("users.profile"))

	return render_template("user/profile.html", user=user, wallet=wallet)
