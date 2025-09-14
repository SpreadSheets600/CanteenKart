from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    flash,
    request,
    current_app,
)
from .utils import owner_only

from models.models import (
    User,
    MenuItem,
    SalesSummary,
    ItemPerformance,
    Feedback,
    UserActivity,
    Order,
    Wallet,
)
# db not required in this controller (queries use models directly)


owners_bp = Blueprint("owners", __name__, template_folder="../templates", url_prefix="")


@owners_bp.route("/owner/dashboard")
@owner_only
def owner_dashboard():
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

    # KPIs
    from datetime import date
    active_orders = (
        Order.query.filter(Order.status.in_(["pending", "preparing", "ready"]))
        .count()
    )
    # revenue today (simple python aggregation to avoid bigger SQL changes)
    from sqlalchemy import extract
    todays_orders = (
        Order.query.filter(
            extract('year', Order.created_at) == date.today().year,
            extract('month', Order.created_at) == date.today().month,
            extract('day', Order.created_at) == date.today().day,
        ).all()
    )
    revenue_today = 0.0
    for o in todays_orders:
        for oi in o.items:
            try:
                revenue_today += (oi.price or 0.0) * (oi.quantity or 0)
            except Exception:
                pass

    peak_hour = summaries[0].peak_hour if summaries else None
    low_stock_items = (
        MenuItem.query.filter(MenuItem.stock_qty <= 5)
        .order_by(MenuItem.stock_qty.asc())
        .limit(10)
        .all()
    )

    recent_orders = (
        Order.query.order_by(Order.created_at.desc()).limit(15).all()
    )

    canteen_open = current_app.config.get("CANTEEN_OPEN", True)
    announcement = current_app.config.get("ANNOUNCEMENT", "")

    return render_template(
        "owner/dashboard.html",
        summaries=summaries,
        top_items=top_items,
        recent_feedback=recent_feedback,
        recent_status=recent_status,
        active_orders=active_orders,
        revenue_today=revenue_today,
        peak_hour=peak_hour,
        low_stock_items=low_stock_items,
        recent_orders=recent_orders,
        canteen_open=canteen_open,
        announcement=announcement,
    )


@owners_bp.route("/owner/users")
@owner_only
def list_users():
    users = User.query.order_by(User.user_id).all()

    # attach simple stats including spending totals
    user_stats = []
    for u in users:
        orders_q = (
            Order.query.filter_by(user_id=u.user_id)
            .order_by(Order.created_at.desc())
        )
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

        user_stats.append(
            {
                "user": u,
                "orders_count": orders_count,
                "wallet": wallet,
                "total_spent": total_spent,
                "avg_order": avg_order,
                "last_order_date": last_order_date,
            }
        )

    return render_template("owner/users_list.html", user_stats=user_stats)


@owners_bp.route("/owner/users/<int:user_id>")
@owner_only
def user_detail(user_id: int):
    user = User.query.get_or_404(user_id)
    orders = (
        Order.query.filter_by(user_id=user.user_id)
        .order_by(Order.created_at.desc())
        .limit(20)
        .all()
    )
    wallet = Wallet.query.filter_by(user_id=user.user_id).first()
    activities = (
        UserActivity.query.filter_by(user_id=user.user_id)
        .order_by(UserActivity.created_at.desc())
        .limit(20)
        .all()
    )

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
    last_order_date = max(
        (o.created_at for o in all_orders if o.created_at), default=None
    )

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


@owners_bp.route("/owner/open", methods=["POST"])
@owner_only
def set_open_state():
    state = (request.form.get("state") or "").lower()
    current_app.config["CANTEEN_OPEN"] = state in ("open", "true", "1", "on")
    flash("Canteen state updated", "success")
    return redirect(url_for("owners.owner_dashboard"))


@owners_bp.route("/owner/announcement", methods=["POST"])
@owner_only
def set_announcement():
    text = (request.form.get("text") or "").strip()
    current_app.config["ANNOUNCEMENT"] = text
    flash("Announcement updated", "success")
    return redirect(url_for("owners.owner_dashboard"))


@owners_bp.route("/owner/scanner", methods=["GET", "POST"])
@owner_only
def scanner():
    from models.models import Order
    if request.method == "POST":
        token = (request.form.get("token") or "").strip()
        if not token:
            flash("Enter a token", "warning")
            return redirect(url_for("owners.scanner"))
        order = Order.query.filter_by(token_code=token).first()
        if not order:
            flash("No order with that token", "danger")
            return redirect(url_for("owners.scanner"))
        order.status = "completed"
        from models.database import db
        db.session.add(order)
        db.session.commit()
        try:
            socketio = current_app.extensions.get("socketio")
            if socketio:
                socketio.emit("order_update", {"order_id": order.order_id, "status": order.status})
        except Exception:
            pass
        flash(f"Order #{order.order_id} marked as collected", "success")
        return redirect(url_for("owners.scanner"))
    return render_template("owner/scanner.html")


@owners_bp.route("/owner/stock")
@owner_only
def stock_page():
    items = MenuItem.query.order_by(MenuItem.stock_qty.asc(), MenuItem.name.asc()).all()
    return render_template("owner/stock.html", items=items)


@owners_bp.route("/owner/stock/update/<int:item_id>", methods=["POST"])
@owner_only
def stock_update(item_id: int):
    item = MenuItem.query.get_or_404(item_id)
    try:
        new_qty = int(request.form.get("stock_qty") or item.stock_qty)
    except Exception:
        new_qty = item.stock_qty
    item.stock_qty = max(0, new_qty)
    # auto-toggle availability when hitting zero
    if item.stock_qty == 0:
        item.is_available = False
    from models.database import db
    db.session.add(item)
    db.session.commit()
    flash("Stock updated", "success")
    return redirect(url_for("owners.stock_page"))


@owners_bp.route("/owner/stock/auto_disable", methods=["POST"])
@owner_only
def stock_auto_disable():
    zero_items = MenuItem.query.filter_by(stock_qty=0, is_available=True).all()
    from models.database import db
    for it in zero_items:
        it.is_available = False
        db.session.add(it)
    db.session.commit()
    flash("Auto-disabled out-of-stock items", "info")
    return redirect(url_for("owners.stock_page"))
