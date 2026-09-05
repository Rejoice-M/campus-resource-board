"""
Small shared helpers used across route files.
"""

from functools import wraps
from flask import session, redirect, url_for, request


def login_required(view_func):
    """
    Redirect to login if there's no user_id in session.
    Also remembers where the user was trying to go, so login() can
    send them back there instead of always landing on the browse page.
    """
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapped
