"""
Small shared helpers used across route files.
"""

import os
import uuid
from functools import wraps
from flask import session, redirect, url_for, request, abort, current_app
from PIL import Image


def login_required(view_func):
    """
    Redirect to login if there's no user_id in session.
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
    """
    uid = session.get("user_id")
    is_owner = uid == listing.user_id
    is_the_other_participant = other_user_id == listing.user_id

    if not (is_owner or is_the_other_participant):
        abort(403)


def save_listing_image(file_storage):
    """
    Validate and save an uploaded listing photo to disk.
    Returns the new filename to store in the DB, or None if no file
    was submitted (i.e. the field was left blank — not an error).
    Raises ValueError with a user-facing message if a file WAS
    submitted but isn't a valid image, so the route can flash it.
    """
    if not file_storage or not file_storage.filename:
        return None

    filename = file_storage.filename
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        raise ValueError("Image must be a JPG, PNG, or WEBP file.")

    # This catches a disguised file (e.g. a script renamed to photo.jpg)
    # that would otherwise get saved and served straight to other users.
    try:
        file_storage.stream.seek(0)
        Image.open(file_storage.stream).verify()
        file_storage.stream.seek(0)
    except Exception:
        raise ValueError("That file doesn't look like a valid image.")

    new_filename = f"{uuid.uuid4().hex}.{ext}"
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    file_storage.save(os.path.join(upload_folder, new_filename))
    return new_filename


def delete_listing_image(filename):
    """Remove a listing's photo from disk, if it has one."""
    if not filename:
        return
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(path):
        os.remove(path)
