from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)

from models.models import Order
from models.database import db
from .utils import owner_only

orders_bp = Blueprint(
    "owner_orders", __name__, template_folder="../templates", url_prefix=""
)


@orders_bp.route("/owner/orders")
@owner_only
def list_orders():
    from flask import request
    q = Order.query
    status = (request.args.get("status") or "").strip()
    if status in {"pending", "preparing", "ready"}:
        q = q.filter_by(status=status)
    else:
        q = q.filter(Order.status.in_(["pending", "preparing", "ready"]))
    orders = q.order_by(Order.created_at.desc()).all()
    return render_template("owner/owner_orders.html", orders=orders)


@orders_bp.route("/owner/orders/<int:order_id>/status", methods=["POST"])
@owner_only
def update_status(order_id: int):
    order = Order.query.get_or_404(order_id)
    status = (request.form.get("status") or order.status).strip()

    if status not in {"pending", "preparing", "ready", "completed", "cancelled"}:
        flash("Invalid status", "warning")
        return redirect(url_for("owner_orders.list_orders"))

    order.status = status
    db.session.add(order)
    db.session.commit()

    try:
        socketio = current_app.extensions.get("socketio")
        if socketio:
            socketio.emit(
                "order_update", {"order_id": order.order_id, "status": order.status}
            )
    except Exception:
        pass

    flash("Order Status Updated", "success")
    return redirect(url_for("owner_orders.list_orders"))
