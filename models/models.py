from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.orm import relationship

from models.database import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False, default="student")
    password_hash = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    wallet = relationship(
        "Wallet", uselist=False, back_populates="user", cascade="all, delete-orphan"
    )
    transactions = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )

    def get_id(self):
        return str(self.user_id)


# -----------------------------
# Ordering System
# -----------------------------


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


class Order(db.Model):
    __tablename__ = "orders"

    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    status = db.Column(db.String, nullable=False, default="pending")
    pickup_slot = db.Column(db.DateTime)
    token_code = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(db.Model):
    __tablename__ = "order_items"

    order_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.order_id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.item_id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False, default=0.0)

    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="order_items")


# -----------------------------
# Financial System
# -----------------------------


class Wallet(db.Model):
    __tablename__ = "wallet"

    wallet_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    balance = db.Column(db.Float, nullable=False, default=0.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="wallet")


class Transaction(db.Model):
    __tablename__ = "transactions"

    txn_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    txn_type = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")


# -----------------------------
# Analytics
# -----------------------------


class SalesSummary(db.Model):
    __tablename__ = "sales_summary"

    summary_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False)
    total_orders = db.Column(db.Integer, nullable=False, default=0)
    total_revenue = db.Column(db.Float, nullable=False, default=0.0)
    peak_hour = db.Column(db.Integer)
    top_item_id = db.Column(db.Integer, db.ForeignKey("menu_items.item_id"))

    top_item = relationship("MenuItem")


class ItemPerformance(db.Model):
    __tablename__ = "item_performance"

    item_id = db.Column(
        db.Integer, db.ForeignKey("menu_items.item_id"), primary_key=True
    )
    total_sold = db.Column(db.Integer, nullable=False, default=0)
    total_revenue = db.Column(db.Float, nullable=False, default=0.0)
    average_rating = db.Column(db.Float)
    last_sold_at = db.Column(db.DateTime)

    menu_item = relationship("MenuItem")


# -----------------------------
# Reporting System
# -----------------------------


class Feedback(db.Model):
    __tablename__ = "feedback"

    feedback_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.item_id"), nullable=False)
    rating = db.Column(db.Integer)
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = relationship("User")
    menu_item = relationship("MenuItem")


# -----------------------------
# User Activity Logging
# -----------------------------


class UserActivity(db.Model):
    __tablename__ = "user_activity"

    activity_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.item_id"))
    action = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = relationship("User")
    menu_item = relationship("MenuItem")


# -----------------------------
# Order Status
# -----------------------------


class OrderStatusLog(db.Model):
    __tablename__ = "order_status_log"

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.order_id"), nullable=False)
    old_status = db.Column(db.String)
    new_status = db.Column(db.String, nullable=False)
    changed_by = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # lightweight relationship back to Order (optional)
    order = relationship("Order")
