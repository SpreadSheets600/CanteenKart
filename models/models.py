"""Compatibility shim re-exporting models from the new app package."""

from app.models.user import User
from app.models.menu_item import MenuItem
from app.models.order import Order, OrderItem
from app.models.wallet import Wallet, Transaction
from app.models.analytics import (
    SalesSummary,
    ItemPerformance,
    Feedback,
    UserActivity,
    OrderStatusLog,
)

__all__ = [
    "User",
    "MenuItem",
    "Order",
    "OrderItem",
    "Wallet",
    "Transaction",
    "SalesSummary",
    "ItemPerformance",
    "Feedback",
    "UserActivity",
    "OrderStatusLog",
]
