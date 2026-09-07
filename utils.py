"""
Small shared helpers used across route files.
"""

from functools import wraps
from flask import session, redirect, url_for, request, abort


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


def current_user_owns(resource):
    """
    True if the logged-in user's id matches resource.user_id.
    Use this before allowing any edit/delete action.
    """
    return session.get("user_id") == resource.user_id


def require_ownership(resource):
    """
    Abort with 403 Forbidden if the logged-in user doesn't own this resource.
    Call this at the top of any edit/delete route, after login_required
    has already confirmed someone is logged in.
    """
    if not current_user_owns(resource):
        abort(403)


def require_thread_participant(listing, other_user_id):
    """
    A message thread exists between the listing's owner and one other user.
    Valid only if the current user IS the owner (talking to some buyer),
    or the current user IS that buyer (talking to the owner).
    Anything else — e.g. trying to view someone else's conversation — is 403.
    """
    uid = session.get("user_id")
    is_owner = uid == listing.user_id
    is_the_other_participant = other_user_id == listing.user_id

    if not (is_owner or is_the_other_participant):
        abort(403)
