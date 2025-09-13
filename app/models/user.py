from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.orm import relationship

from ..extensions import db


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
