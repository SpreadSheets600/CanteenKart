from flask import Blueprint, render_template, session, redirect, url_for, flash

from models.models import User, Order, Wallet, UserActivity


users_bp = Blueprint("users", __name__, template_folder="../templates", url_prefix="")


def owner_required():
    return session.get("role") == "owner"


@users_bp.route("/owner/users")
def list_users():
    if not owner_required():
        flash("Owner access required", "danger")
        return redirect(url_for("menu.menu"))

    users = User.query.order_by(User.user_id).all()

    # attach simple stats including spending totals
    user_stats = []
    for u in users:
        orders_q = Order.query.filter_by(user_id=u.user_id).order_by(Order.created_at.desc())
        orders_count = orders_q.count()
        wallet = Wallet.query.filter_by(user_id=u.user_id).first()

        # compute total spent and last order date
        total_spent = 0.0
        last_order_date = None
        for o in orders_q.all():
            if o.created_at and (not last_order_date or o.created_at > last_order_date):
                last_order_date = o.created_at
            for oi in o.items:
                try:
                    total_spent += (oi.price or 0.0) * (oi.quantity or 0)
                except Exception:
                    pass

        avg_order = (total_spent / orders_count) if orders_count else 0.0

        user_stats.append({
            "user": u,
            "orders_count": orders_count,
            "wallet": wallet,
            "total_spent": total_spent,
            "avg_order": avg_order,
            "last_order_date": last_order_date,
        })

    return render_template("owner/users_list.html", user_stats=user_stats)


@users_bp.route("/owner/users/<int:user_id>")
def user_detail(user_id: int):
    if not owner_required():
        flash("Owner access required", "danger")
        return redirect(url_for("menu.menu"))

    user = User.query.get_or_404(user_id)
    orders = Order.query.filter_by(user_id=user.user_id).order_by(Order.created_at.desc()).limit(20).all()
    wallet = Wallet.query.filter_by(user_id=user.user_id).first()
    activities = UserActivity.query.filter_by(user_id=user.user_id).order_by(UserActivity.created_at.desc()).limit(20).all()

    # compute spending stats for this user (all orders)
    all_orders = Order.query.filter_by(user_id=user.user_id).all()
    total_spent = 0.0
    for o in all_orders:
        for oi in o.items:
            try:
                total_spent += (oi.price or 0.0) * (oi.quantity or 0)
            except Exception:
                pass

    total_orders = len(all_orders)
    avg_order = (total_spent / total_orders) if total_orders else 0.0
    last_order_date = max((o.created_at for o in all_orders if o.created_at), default=None)

    return render_template(
        "owner/user_detail.html",
        user=user,
        orders=orders,
        wallet=wallet,
        activities=activities,
        total_spent=total_spent,
        avg_order=avg_order,
        total_orders=total_orders,
        last_order_date=last_order_date,
    )
