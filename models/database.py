"""Compatibility shim: expose db for code importing models.database.db"""

from app.extensions import db

__all__ = ["db"]
