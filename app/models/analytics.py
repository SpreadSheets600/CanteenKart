from datetime import datetime
from sqlalchemy.orm import relationship

from ..extensions import db


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


class UserActivity(db.Model):
    __tablename__ = "user_activity"

    activity_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.item_id"))
    action = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = relationship("User")
    menu_item = relationship("MenuItem")


class OrderStatusLog(db.Model):
    __tablename__ = "order_status_log"

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.order_id"), nullable=False)
    old_status = db.Column(db.String)
    new_status = db.Column(db.String, nullable=False)
    changed_by = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order = relationship("Order")
