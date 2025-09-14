from flask import (
    render_template,
    Blueprint,
    redirect,
    url_for,
    request,
    flash,
)

from ..app.extensions import logger
from models.models import MenuItem
from models.database import db
from .utils import owner_only


menu_bp = Blueprint("menu", __name__, template_folder="../templates", url_prefix="")


@menu_bp.route("/menu")
def menu():
    items = MenuItem.query.order_by(MenuItem.name).all()
    return render_template("user/menu.html", items=items)


@menu_bp.route("/owner/menu")
@owner_only
def owner_menu():
    items = MenuItem.query.order_by(MenuItem.item_id).all()
    return render_template("owner/owner_menu.html", items=items)


@menu_bp.route("/owner/menu/add", methods=["POST"])
@owner_only
def add_item():
    name = (request.form.get("name") or "").strip()
    description = request.form.get("description") or ""

    try:
        price = float(request.form.get("price") or 0)
    except Exception:
        price = 0.0

    try:
        stock_qty = int(request.form.get("stock_qty") or 0)
    except Exception:
        stock_qty = 0

    is_available = bool(request.form.get("is_available"))

    if not name:
        flash("Name Is Required", "danger")
        logger.warning("Attempted To Add Menu Item Without A Name")

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

    flash("Item Added", "success")
    logger.info(f"Menu Item Added : {name} At {price}")

    return redirect(url_for("menu.owner_menu"))


@menu_bp.route("/owner/menu/edit/<int:item_id>", methods=["POST"])
@owner_only
def edit_item(item_id: int):
    item = MenuItem.query.get_or_404(item_id)

    item.name = (request.form.get("name") or item.name).strip()

    try:
        item.price = float(request.form.get("price") or item.price)
    except Exception:
        pass

    item.description = request.form.get("description") or item.description

    try:
        item.stock_qty = int(request.form.get("stock_qty") or item.stock_qty)
    except Exception:
        pass

    item.is_available = bool(request.form.get("is_available"))

    db.session.add(item)
    db.session.commit()

    flash("Item Updated", "success")
    logger.info(f"Menu Item Updated : {item.name} At {item.price}")

    return redirect(url_for("menu.owner_menu"))


@menu_bp.route("/owner/menu/delete/<int:item_id>", methods=["POST"])
@owner_only
def delete_item(item_id: int):
    item = MenuItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()

    flash("Item Deleted", "info")
    logger.info(f"Menu Item Deleted : {item.name} At {item.price}")

    return redirect(url_for("menu.owner_menu"))
