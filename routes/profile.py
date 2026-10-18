"""
Profile page: view/edit the logged-in user's own details, and change password.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User, Listing
from utils import login_required

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile")
@login_required
def view():
    user = User.query.get_or_404(session["user_id"])
    my_listings = (
        Listing.query.filter_by(user_id=user.id)
        .order_by(Listing.created_at.desc())
        .all()
    )
    return render_template("profile.html", user=user, my_listings=my_listings)


@profile_bp.route("/profile/edit", methods=["POST"])
@login_required
def edit():
    user = User.query.get_or_404(session["user_id"])

    university = request.form.get("university", "").strip()
    year_of_study = request.form.get("year_of_study", "").strip()
    phone_number = request.form.get("phone_number", "").strip()

    if not university or not year_of_study or not phone_number:
        flash("University, year of study, and phone number are required.")
        return redirect(url_for("profile.view"))

    user.name = request.form["name"].strip()
    user.university = university
    user.major = request.form.get("major", "").strip() or None
    user.year_of_study = year_of_study
    user.phone_number = phone_number

    db.session.commit()
    flash("Profile updated.", "success")
    return redirect(url_for("profile.view"))


@profile_bp.route("/profile/password", methods=["POST"])
@login_required
def change_password():
    user = User.query.get_or_404(session["user_id"])

    current_password = request.form["current_password"]
    new_password = request.form["new_password"]
    confirm_password = request.form["confirm_password"]

    if not user.check_password(current_password):
        flash("Current password is incorrect.")
        return redirect(url_for("profile.view"))

    if new_password != confirm_password:
        flash("New passwords don't match.")
        return redirect(url_for("profile.view"))

    if len(new_password) < 8:
        flash("New password must be at least 8 characters.")
        return redirect(url_for("profile.view"))

    user.set_password(new_password)
    db.session.commit()
    flash("Password changed.", "success")
    return redirect(url_for("profile.view"))
