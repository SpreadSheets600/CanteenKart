"""Controller utilities: common decorators and helpers.

Minimal, low-risk improvements to keep controllers tidy without large changes.
"""

from functools import wraps
from typing import Callable, Any

from flask import session, flash, redirect, url_for


def owner_only(view_func: Callable[..., Any]) -> Callable[..., Any]:
    """Require the logged-in user to be an owner.

    If the session does not indicate an owner, flash a message and redirect
    to the public menu.
    """

    @wraps(view_func)
    def wrapper(*args: Any, **kwargs: Any):
        if session.get("role") != "owner":
            flash("Owner Access Required", "danger")
            return redirect(url_for("menu.menu"))
        return view_func(*args, **kwargs)

    return wrapper


__all__ = ["owner_only"]
