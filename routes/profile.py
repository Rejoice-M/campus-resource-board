"""
Profile page: view/edit the logged-in user's own details, and change password.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User
from utils import login_required

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile")
@login_required
def view():
    user = User.query.get_or_404(session["user_id"])
    return render_template("profile.html", user=user)


@profile_bp.route("/profile/edit", methods=["POST"])
@login_required
def edit():
    user = User.query.get_or_404(session["user_id"])

    user.name = request.form["name"].strip()
    user.university = request.form.get("university", "").strip() or None
    user.major = request.form.get("major", "").strip() or None
    user.year_of_study = request.form.get("year_of_study", "").strip() or None
    user.phone_number = request.form.get("phone_number", "").strip() or None

    db.session.commit()
    flash("Profile updated.", "success")  # <-- success category
    return redirect(url_for("profile.view"))


@profile_bp.route("/profile/password", methods=["POST"])
@login_required
def change_password():
    user = User.query.get_or_404(session["user_id"])

    current_password = request.form["current_password"]
    new_password = request.form["new_password"]
    confirm_password = request.form["confirm_password"]

    if not user.check_password(current_password):
        flash("Current password is incorrect.", "danger")  # <-- error category
        return redirect(url_for("profile.view"))

    if new_password != confirm_password:
        flash("New passwords don't match.", "danger")
        return redirect(url_for("profile.view"))

    if len(new_password) < 8:
        flash("New password must be at least 8 characters.", "danger")
        return redirect(url_for("profile.view"))

    user.set_password(new_password)
    db.session.commit()
    flash("Password changed.", "success")  # <-- success category
    return redirect(url_for("profile.view"))