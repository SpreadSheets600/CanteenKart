from flask import (
    render_template,
    current_app,
    Blueprint,
    redirect,
    request,
    session,
    url_for,
    flash,
    jsonify,
)
from flask_login import current_user, login_required
from sqlalchemy import extract
from datetime import date

from app.extensions import db, logger
from models.models import Order, OrderItem
from .utils import owner_only

from models.models import (
    ItemPerformance,
    SalesSummary,
    UserActivity,
    Feedback,
    MenuItem,
    Wallet,
    User,
    RawItems,
)
from .recommendations import get_top_orders


owners_bp = Blueprint("owners", __name__, template_folder="../templates", url_prefix="")


@owners_bp.route("/owner/dashboard")
@owner_only
def owner_dashboard():
    summaries = SalesSummary.query.order_by(SalesSummary.date.desc()).limit(7).all()

    top_items = (
        ItemPerformance.query.order_by(ItemPerformance.total_sold.desc())
        .limit(10)
        .all()
    )

    recent_feedback = (
        Feedback.query.order_by(Feedback.created_at.desc()).limit(10).all()
    )

    recent_status = (
        UserActivity.query.order_by(UserActivity.created_at.desc()).limit(15).all()
    )

    active_orders = Order.query.filter(
        Order.status.in_(["pending", "preparing", "ready"])
    ).count()

    todays_orders = Order.query.filter(
        extract("year", Order.created_at) == date.today().year,
        extract("month", Order.created_at) == date.today().month,
        extract("day", Order.created_at) == date.today().day,
    ).all()

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
        Order.query
        .options(db.selectinload(Order.user), db.selectinload(Order.items).selectinload(OrderItem.menu_item))
        .order_by(Order.created_at.desc())
        .limit(15)
        .all()
    )

    canteen_open = current_app.config.get("CANTEEN_OPEN", True)
    announcement = current_app.config.get("ANNOUNCEMENT", "")

    # Get top orders for visual display
    top_orders = get_top_orders(5)

    return render_template(
        "owner/dashboard.html",
        summaries=summaries,
        top_items=top_items,
        peak_hour=peak_hour,
        canteen_open=canteen_open,
        announcement=announcement,
        recent_status=recent_status,
        active_orders=active_orders,
        revenue_today=revenue_today,
        recent_orders=recent_orders,
        low_stock_items=low_stock_items,
        recent_feedback=recent_feedback,
        top_orders=top_orders,
        user=current_user,
    )


@owners_bp.route("/owner/users")
@owner_only
def list_users():
    users = User.query.order_by(User.user_id).all()

    user_stats = []
    for u in users:
        orders_q = (
            Order.query.options(
                db.selectinload(Order.items).selectinload(OrderItem.menu_item)
            )
            .filter_by(user_id=u.user_id)
            .order_by(Order.created_at.desc())
        )
        orders_count = orders_q.count()
        wallet = Wallet.query.filter_by(user_id=u.user_id).first()

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
                "wallet": wallet,
                "avg_order": avg_order,
                "total_spent": total_spent,
                "orders_count": orders_count,
                "last_order_date": last_order_date,
            }
        )

    return render_template("owner/users_list.html", user_stats=user_stats)


@owners_bp.route("/owner/users/<int:user_id>")
@owner_only
def user_detail(user_id: int):
    user = User.query.get_or_404(user_id)

    orders = (
        Order.query.options(
            db.selectinload(Order.items).selectinload(OrderItem.menu_item)
        )
        .filter_by(user_id=user.user_id)
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

    all_orders = (
        Order.query.options(
            db.selectinload(Order.items).selectinload(OrderItem.menu_item)
        )
        .filter_by(user_id=user.user_id)
        .all()
    )
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
        avg_order=avg_order,
        activities=activities,
        total_spent=total_spent,
        total_orders=total_orders,
        last_order_date=last_order_date,
    )


@owners_bp.route("/dashboard")
def user_dashboard():
    user_id = session.get("user_id")

    if not user_id:
        flash("Please Login In View Dashboard", "warning")
        logger.warning("Dashboard Access Attempt Without Login")

        return redirect(url_for("auth.login"))

    user_details = User.query.options(db.selectinload(User.transactions)).get(user_id)

    if user_details:
        user_details.transactions = sorted(
            user_details.transactions, key=lambda t: t.created_at, reverse=True
        )

    orders = (
        Order.query.options(
            db.selectinload(Order.items).selectinload(OrderItem.menu_item)
        )
        .filter_by(user_id=int(user_id))
        .order_by(Order.created_at.desc())
        .limit(10)
        .all()
    )

    wallet = Wallet.query.filter_by(user_id=int(user_id)).first()

    all_orders = (
        Order.query.options(
            db.selectinload(Order.items).selectinload(OrderItem.menu_item)
        )
        .filter_by(user_id=int(user_id))
        .order_by(Order.created_at.desc())
        .all()
    )

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
        user=user_details,
        orders=orders,
        wallet=wallet,
        avg_order=avg_order,
        last_order=last_order,
        total_spent=total_spent,
        total_orders=total_orders,
        last_order_items=last_order_items,
    )


@owners_bp.route("/owner/open", methods=["POST"])
@owner_only
def set_open_state():
    state = (request.form.get("state") or "").lower()
    current_app.config["CANTEEN_OPEN"] = state in ("open", "true", "1", "on")

    flash("Canteen State Updated", "success")
    logger.info(
        f"Canteen State Updated To {'Open' if current_app.config['CANTEEN_OPEN'] else 'Closed'}"
    )

    return redirect(url_for("owners.owner_dashboard"))


@owners_bp.route("/owner/announcement", methods=["POST"])
@owner_only
def set_announcement():
    text = (request.form.get("text") or "").strip()
    current_app.config["ANNOUNCEMENT"] = text

    flash("Announcement updated", "success")
    logger.info("Canteen Announcement Updated")

    return redirect(url_for("owners.owner_dashboard"))


@owners_bp.route("/api/announcements", methods=["GET"])
@login_required
def get_announcements():
    """API endpoint to fetch current announcements"""
    announcement = current_app.config.get("ANNOUNCEMENT", "")

    announcements = []
    if announcement:
        announcements.append({
            "id": "main_announcement",
            "title": "Canteen Announcement",
            "message": announcement,
            "type": "info",
            "timestamp": None  # Current announcement doesn't have a timestamp
        })

    return jsonify({
        "success": True,
        "announcements": announcements
    })


@owners_bp.route("/owner/scanner", methods=["GET", "POST"])
@owner_only
def scanner():
    from models.models import Order

    if request.method == "POST":
        token = (request.form.get("token") or "").strip()

        if not token:
            flash("Enter A Token", "warning")
            logger.warning("Attempted To Scan Without A Token")

            return redirect(url_for("owners.scanner"))

        order = Order.query.filter_by(token_code=token).first()

        if not order:
            flash("No order with that token", "danger")
            logger.warning(f"Invalid Token Scan Attempt : {token}")

            return redirect(url_for("owners.scanner"))

        order.status = "completed"
        from models.database import db

        db.session.add(order)
        db.session.commit()

        try:
            socketio = current_app.extensions.get("socketio")
            if socketio:
                socketio.emit(
                    "order_update",
                    {"order_id": order.order_id, "status": order.status},
                    room=f"user_{order.user_id}",
                )
        except Exception:
            pass

        flash(f"Order #{order.order_id} Marked As Collected!", "success")
        logger.info(f"Order {order.order_id} Marked As Collected Via Scanner")

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

    if item.stock_qty == 0:
        item.is_available = False

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

    flash("Auto-Disabled Out-Of-Stock Items", "info")
    logger.info("Auto-Disabled Out-Of-Stock Items")

    return redirect(url_for("owners.stock_page"))


# Raw Items Management Routes
@owners_bp.route("/owner/raw-items")
@owner_only
def raw_items_page():
    raw_items = RawItems.query.order_by(RawItems.name).all()
    return render_template("owner/raw_items.html", raw_items=raw_items)


@owners_bp.route("/owner/raw-items/add", methods=["GET", "POST"])
@owner_only
def add_raw_item():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        stock_qty = request.form.get("stock_qty", 0)

        if not name:
            flash("Item name is required!", "error")
            return redirect(url_for("owners.add_raw_item"))

        try:
            stock_qty = int(stock_qty) if stock_qty else 0
        except ValueError:
            stock_qty = 0

        raw_item = RawItems(
            name=name,
            description=description,
            stock_qty=stock_qty
        )
        db.session.add(raw_item)
        db.session.commit()

        flash(f"Raw item '{name}' added successfully!", "success")
        logger.info(f"Raw item '{name}' added by owner {current_user.user_id}")

        return redirect(url_for("owners.raw_items_page"))

    return render_template("owner/add_raw_item.html")


@owners_bp.route("/owner/raw-items/<int:raw_item_id>/edit", methods=["GET", "POST"])
@owner_only
def edit_raw_item(raw_item_id):
    raw_item = RawItems.query.get_or_404(raw_item_id)

    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        stock_qty = request.form.get("stock_qty", 0)

        if not name:
            flash("Item name is required!", "error")
            return redirect(url_for("owners.edit_raw_item", raw_item_id=raw_item_id))

        try:
            stock_qty = int(stock_qty) if stock_qty else 0
        except ValueError:
            stock_qty = 0

        raw_item.name = name
        raw_item.description = description
        raw_item.stock_qty = stock_qty

        db.session.commit()

        flash(f"Raw item '{name}' updated successfully!", "success")
        logger.info(f"Raw item '{name}' updated by owner {current_user.user_id}")

        return redirect(url_for("owners.raw_items_page"))

    return render_template("owner/edit_raw_item.html", raw_item=raw_item)


@owners_bp.route("/owner/raw-items/<int:raw_item_id>/delete", methods=["POST"])
@owner_only
def delete_raw_item(raw_item_id):
    raw_item = RawItems.query.get_or_404(raw_item_id)

    name = raw_item.name
    db.session.delete(raw_item)
    db.session.commit()

    flash(f"Raw item '{name}' deleted successfully!", "success")
    logger.info(f"Raw item '{name}' deleted by owner {current_user.user_id}")

    return redirect(url_for("owners.raw_items_page"))


@owners_bp.route("/owner/raw-items/<int:raw_item_id>/update-stock", methods=["POST"])
@owner_only
def update_raw_item_stock(raw_item_id):
    raw_item = RawItems.query.get_or_404(raw_item_id)

    action = request.form.get("action")
    quantity = request.form.get("quantity", 0)

    try:
        quantity = int(quantity) if quantity else 0
    except ValueError:
        quantity = 0

    if action == "add":
        raw_item.stock_qty += quantity
        flash(f"Added {quantity} units to {raw_item.name}", "success")
    elif action == "subtract":
        if raw_item.stock_qty >= quantity:
            raw_item.stock_qty -= quantity
            flash(f"Removed {quantity} units from {raw_item.name}", "success")
        else:
            flash("Cannot remove more than available stock!", "error")
            return redirect(url_for("owners.raw_items_page"))

    db.session.commit()
    logger.info(f"Stock updated for raw item '{raw_item.name}' by owner {current_user.user_id}")

    return redirect(url_for("owners.raw_items_page"))
