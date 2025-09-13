from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    flash,
)

from models.models import (
    SalesSummary,
    ItemPerformance,
    Feedback,
    UserActivity,
    Order,
    Wallet,
)
# db not required in this controller (queries use models directly)


owners_bp = Blueprint("owners", __name__, template_folder="../templates", url_prefix="")


def owner_required():
    return session.get("role") == "owner"


@owners_bp.route("/owner/dashboard")
def owner_dashboard():
    if not owner_required():
        flash("Owner Access Required", "danger")
        return redirect(url_for("menu.menu"))

    # aggregate recent sales summaries (last 7 days)
    summaries = SalesSummary.query.order_by(SalesSummary.date.desc()).limit(7).all()

    # top performing items
    top_items = (
        ItemPerformance.query.order_by(ItemPerformance.total_sold.desc())
        .limit(10)
        .all()
    )

    # recent feedback
    recent_feedback = (
        Feedback.query.order_by(Feedback.created_at.desc()).limit(10).all()
    )

    # recent order status changes
    recent_status = (
        UserActivity.query.order_by(UserActivity.created_at.desc()).limit(15).all()
    )

    # basic counts
    total_orders = Order.query.count()
    total_revenue = sum(s.total_revenue for s in summaries) if summaries else 0.0

    return render_template(
        "owner/dashboard.html",
        summaries=summaries,
        top_items=top_items,
        recent_feedback=recent_feedback,
        recent_status=recent_status,
        total_orders=total_orders,
        total_revenue=total_revenue,
    )


@owners_bp.route("/dashboard")
def user_dashboard():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please login to view dashboard", "warning")
        return redirect(url_for("auth.login"))

    # user's recent orders
    orders = (
        Order.query.filter_by(user_id=int(user_id))
        .order_by(Order.created_at.desc())
        .limit(10)
        .all()
    )

    # wallet balance if exists
    wallet = Wallet.query.filter_by(user_id=int(user_id)).first()

    # user recent activity
    activities = (
        UserActivity.query.filter_by(user_id=int(user_id))
        .order_by(UserActivity.created_at.desc())
        .limit(10)
        .all()
    )

    # analytics: compute total spent, avg order value, last order and its items
    all_orders = Order.query.filter_by(user_id=int(user_id)).order_by(Order.created_at.desc()).all()
    total_spent = 0.0
    for o in all_orders:
        for oi in o.items:
            try:
                total_spent += (oi.price or 0.0) * (oi.quantity or 0)
            except Exception:
                pass

    total_orders = len(all_orders)
    avg_order = (total_spent / total_orders) if total_orders else 0.0
    last_order = all_orders[0] if all_orders else None
    last_order_items = last_order.items if last_order else []

    return render_template(
        "user/dashboard.html",
        orders=orders,
        wallet=wallet,
        activities=activities,
        total_spent=total_spent,
        avg_order=avg_order,
        total_orders=total_orders,
        last_order=last_order,
        last_order_items=last_order_items,
    )
