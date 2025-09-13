from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    current_app,
)

from models.models import Order
from models.database import db

orders_bp = Blueprint(
    "owner_orders", __name__, template_folder="../templates", url_prefix=""
)


def owner_required():
    return session.get("role") == "owner"


@orders_bp.route("/owner/orders")
def list_orders():
    if not owner_required():
        flash("Owner Access Required", "danger")
        return redirect(url_for("menu.menu"))

    orders = Order.query.filter(Order.status.in_(["pending", "preparing"]))
    return render_template("owner/owner_orders.html", orders=orders)


@orders_bp.route("/owner/orders/<int:order_id>/status", methods=["POST"])
def update_status(order_id: int):
    if not owner_required():
        flash("Owner Access Required", "danger")
        return redirect(url_for("menu.menu"))

    order = Order.query.get_or_404(order_id)
    status = request.form.get("status") or order.status

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
