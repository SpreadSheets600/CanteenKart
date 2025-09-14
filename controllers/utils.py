from typing import Callable, Any
from functools import wraps

from flask import session, flash, redirect, url_for


def owner_only(view_func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view_func)
    def wrapper(*args: Any, **kwargs: Any):
        if session.get("role") != "owner":
            flash("Owner Access Required!", "danger")

            return redirect(url_for("menu.menu"))
        return view_func(*args, **kwargs)

    return wrapper


__all__ = ["owner_only"]
