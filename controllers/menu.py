from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)

from models.models import MenuItem
from models.database import db


menu_bp = Blueprint("menu", __name__, template_folder="../templates", url_prefix="")


def owner_required():
    return session.get("role") == "owner"


@menu_bp.route("/menu")
def menu():
    items = MenuItem.query.order_by(MenuItem.name).all()
    return render_template("user/menu.html", items=items)


@menu_bp.route("/owner/menu")
def owner_menu():
    if not owner_required():
        flash("Owner access required", "danger")
        return redirect(url_for("menu.menu"))

    items = MenuItem.query.order_by(MenuItem.item_id).all()
    return render_template("owner/owner_menu.html", items=items)


@menu_bp.route("/owner/menu/add", methods=["POST"])
def add_item():
    if not owner_required():
        flash("Owner access required", "danger")
        return redirect(url_for("menu.owner_menu"))

    name = (request.form.get("name") or "").strip()
    price = float(request.form.get("price") or 0)

    description = request.form.get("description") or ""
    stock_qty = int(request.form.get("stock_qty") or 0)
    is_available = bool(request.form.get("is_available"))

    if not name:
        flash("Name is required", "danger")
        return redirect(url_for("menu.owner_menu"))

    item = MenuItem(
        name=name,
        price=price,
        description=description,
        stock_qty=stock_qty,
        is_available=is_available,
    )
    db.session.add(item)
    db.session.commit()

    flash("Item added", "success")
    return redirect(url_for("menu.owner_menu"))


@menu_bp.route("/owner/menu/edit/<int:item_id>", methods=["POST"])
def edit_item(item_id: int):
    if not owner_required():
        flash("Owner access required", "danger")
        return redirect(url_for("menu.owner_menu"))

    item = MenuItem.query.get_or_404(item_id)

    item.name = (request.form.get("name") or item.name).strip()
    item.price = float(request.form.get("price") or item.price)
    item.description = request.form.get("description") or item.description
    item.stock_qty = int(request.form.get("stock_qty") or item.stock_qty)
    item.is_available = bool(request.form.get("is_available"))

    db.session.add(item)
    db.session.commit()

    flash("Item updated", "success")
    return redirect(url_for("menu.owner_menu"))


@menu_bp.route("/owner/menu/delete/<int:item_id>", methods=["POST"])
def delete_item(item_id: int):
    if not owner_required():
        flash("Owner access required", "danger")
        return redirect(url_for("menu.owner_menu"))

    item = MenuItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()

    flash("Item deleted", "info")
    return redirect(url_for("menu.owner_menu"))
