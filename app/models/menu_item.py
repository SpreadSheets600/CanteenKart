from sqlalchemy.orm import relationship

from ..extensions import db


class MenuItem(db.Model):
    __tablename__ = "menu_items"

    item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    price = db.Column(db.Float, nullable=False, default=0.0)
    stock_qty = db.Column(db.Integer, nullable=False, default=0)
    is_available = db.Column(db.Boolean, nullable=False, default=True)

    order_items = relationship(
        "OrderItem", back_populates="menu_item", cascade="all, delete-orphan"
    )
