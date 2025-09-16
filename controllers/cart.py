from flask import (
    render_template,
    current_app,
    Blueprint,
    send_file,
    Response,
    redirect,
    request,
    session,
    url_for,
    flash,
)
import secrets
import qrcode
import io
from datetime import datetime, timedelta
from flask_login import current_user

from models.models import MenuItem, Order, OrderItem
from app.extensions import logger
from models.database import db


cart_bp = Blueprint("cart", __name__, template_folder="../templates", url_prefix="")


def get_cart():
    return session.setdefault("cart", {})


@cart_bp.route("/cart-data")
def cart_data():
    """Return a JSON representation of the current cart suitable for client-side scripts."""
    cart = get_cart()
    data = {}
    for item_id_str, qty in cart.items():
        try:
            item_id = int(item_id_str)
        except Exception:
            continue
        item = MenuItem.query.get(item_id)
        if not item:
            continue
        data[item_id_str] = {
            "name": item.name,
            "price": float(item.price or 0.0),
            "quantity": int(qty or 0),
        }
    from flask import jsonify

    return jsonify(data)


@cart_bp.route("/cart")
def show_cart():
    cart = get_cart()

    items = []
    total = 0.0

    for item_id_str, qty in cart.items():
        try:
            item_id = int(item_id_str)
        except Exception:
            continue

        item = MenuItem.query.get(item_id)

        if not item:
            continue

        price = item.price
        if current_user.is_authenticated and current_user.email and current_user.role == 'student':
            price *= 0.9

        subtotal = price * int(qty)
        total += subtotal

        items.append({"item": item, "qty": int(qty), "subtotal": subtotal})

    return render_template("user/cart.html", items=items, total=total)


@cart_bp.route("/cart/add/<int:item_id>", methods=["POST"])
def add_to_cart(item_id: int):
    item = MenuItem.query.get_or_404(item_id)

    qty = int(request.form.get("qty", 1))
    if qty <= 0:
        qty = 1

    if not item.is_available or item.stock_qty < qty:
        flash("Item Not Available or Insufficient Stock", "warning")
        logger.warning(f"Attempted to Add Unavailable Item to Cart : {item_id}")

        return redirect(url_for("menu.menu"))

    cart = get_cart()
    key = str(item_id)

    cart[key] = int(cart.get(key, 0)) + qty

    session["cart"] = cart

    flash("Added To Cart!", "success")
    logger.info(f"Item Added to Cart : {item_id} Qty: {qty}")

    return redirect(url_for("menu.menu"))


@cart_bp.route("/cart/remove/<int:item_id>", methods=["POST"])
def remove_from_cart(item_id: int):
    cart = get_cart()
    key = str(item_id)

    if key in cart:
        del cart[key]

        session["cart"] = cart

        flash("Removed From Cart!", "info")
        logger.info(f"Item Removed from Cart : {item_id}")

    return redirect(url_for("cart.show_cart"))


@cart_bp.route("/cart/update/<int:item_id>", methods=["POST"])
def update_cart(item_id: int):
    """Update cart quantity. Accepts form fields:
    - action: 'inc' or 'dec'
    - qty: integer to set exact quantity
    """
    cart = get_cart()
    key = str(item_id)

    item = MenuItem.query.get(item_id)
    if not item:
        flash("Item not found", "warning")
        return redirect(url_for("cart.show_cart"))

    action = (request.form.get("action") or "").strip().lower()
    qty_raw = request.form.get("qty")

    try:
        if qty_raw is not None:
            new_qty = max(0, int(qty_raw))
            if new_qty == 0:
                cart.pop(key, None)
            else:
                # cap to stock
                cart[key] = min(new_qty, item.stock_qty)
        elif action == "inc":
            cart[key] = int(cart.get(key, 0)) + 1
            if cart[key] > item.stock_qty:
                cart[key] = item.stock_qty
        elif action == "dec":
            if key in cart:
                cart[key] = int(cart.get(key, 0)) - 1
                if cart[key] <= 0:
                    cart.pop(key, None)
    except Exception:
        pass

    session["cart"] = cart
    return redirect(url_for("cart.show_cart"))


@cart_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = get_cart()
    if request.method == "GET":
        if not cart:
            flash("Cart Is Empty", "warning")
            return redirect(url_for("menu.menu"))

        items = []
        total = 0.0

        for item_id_str, qty in cart.items():
            try:
                item_id = int(item_id_str)
            except Exception:
                continue

            item = MenuItem.query.get(item_id)

            if not item:
                continue

            price = item.price
            if current_user.is_authenticated and current_user.email and current_user.role == 'student':
                price *= 0.9

            subtotal = price * int(qty)
            total += subtotal

            items.append({"item": item, "qty": int(qty), "subtotal": subtotal})

        now = datetime.now()
        offsets = [10, 30, 45, 60, 90]
        slots = []
        for minutes in offsets:
            slot_time = now + timedelta(minutes=minutes)

            if minutes < 60:
                rel = f"In {minutes} min"
            elif minutes == 60:
                rel = "In 1 hour"
            else:
                rel = f"In {minutes / 60:.1f} hrs"

            slots.append(
                (
                    slot_time.strftime("%H:%M"),
                    f"{rel} ({slot_time.strftime('%I:%M %p')})",
                )
            )

        return render_template(
            "user/checkout.html", items=items, total=total, slots=slots
        )

    if not cart:
        flash("Cart Is Empty", "warning")
        logger.warning("Checkout Attempt With Empty Cart")

        return redirect(url_for("menu.menu"))

    user_id = session.get("user_id")

    if not user_id:
        flash("Please Login To Place Order", "warning")
        logger.warning("Checkout Attempt Without Login")

        return redirect(url_for("auth.login"))

    token_code = secrets.token_hex(3)

    pickup_slot_str = request.form.get("pickup_slot")

    try:
        logger.info(
            f"Checkout POST received: user_id={user_id} pickup_slot={pickup_slot_str} cart_size={len(cart)}"
        )
    except Exception:
        pass
    pickup_slot = None
    if pickup_slot_str:
        try:
            slot_time = datetime.strptime(pickup_slot_str, "%H:%M").time()
            pickup_slot = datetime.combine(datetime.today(), slot_time)
        except Exception:
            pass

    order = Order(
        user_id=int(user_id),
        status="pending",
        token_code=token_code,
        pickup_slot=pickup_slot,
    )
    db.session.add(order)
    db.session.flush()

    for item_id_str, qty in cart.items():
        try:
            item_id = int(item_id_str)
            qty = int(qty)
        except Exception:
            continue

        item = MenuItem.query.get(item_id)

        if not item:
            continue

        price = item.price
        if current_user.is_authenticated and current_user.email and current_user.role == 'student':
            price *= 0.9
        oi = OrderItem(
            order_id=order.order_id, item_id=item.item_id, quantity=qty, price=price
        )
        db.session.add(oi)

        item.stock_qty = max(0, item.stock_qty - qty)
        db.session.add(item)

    db.session.commit()
    session["cart"] = {}

    try:
        socketio = current_app.extensions.get("socketio")
        if socketio:
            socketio.emit("new_order", {"order_id": order.order_id})
    except Exception:
        pass

    flash("Order Placed. Token : %s" % token_code, "success")
    logger.info(f"New Order Placed : {order.order_id} By User {user_id}")

    return redirect(url_for("cart.order_status", order_id=order.order_id))


@cart_bp.route("/order_status/<int:order_id>")
def order_status(order_id: int):
    order = (
        Order.query.options(
            db.selectinload(Order.items).selectinload(OrderItem.menu_item)
        )
        .filter_by(order_id=order_id)
        .first_or_404()
    )
    return render_template("user/order_status.html", order=order)


@cart_bp.route("/order_status/<int:order_id>/qr.png")
def order_status_qr(order_id: int):
    order = Order.query.get_or_404(order_id)

    try:
        base_url = request.url_root.rstrip("/")
        status_url = (
            f"{base_url}{url_for('cart.order_status', order_id=order.order_id)}"
        )
        payload = {
            "order_id": order.order_id,
            "token": order.token_code,
            "url": status_url,
        }

        qr = qrcode.QRCode(version=None, box_size=6, border=2)
        import json as _json

        qr.add_data(_json.dumps(payload, separators=(",", ":")))
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()

        img.save(buf, format="PNG")
        buf.seek(0)

        return send_file(
            buf, mimetype="image/png", download_name=f"order_{order.order_id}_qr.png"
        )

    except Exception:
        return Response("QR Unavailable", status=503, mimetype="text/plain")
