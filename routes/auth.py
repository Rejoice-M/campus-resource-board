"""
Signup, login, logout, password hashing, sessions.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        university = request.form.get("university", "").strip()
        major = request.form.get("major", "").strip() or None  
        year_of_study = request.form.get("year_of_study", "").strip()
        phone_number = request.form.get("phone_number", "").strip()

        # Validate before touching the DB so we never write a half-valid user
        if not university or not year_of_study or not phone_number:
            flash("University, year of study, and phone number are required.")
            return redirect(url_for("auth.signup"))

        if password != confirm_password:
            flash("Passwords don't match.")
            return redirect(url_for("auth.signup"))

        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return redirect(url_for("auth.signup"))

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.")
            return redirect(url_for("auth.signup"))

        user = User(
            name=name,
            email=email,
            university=university,
            major=major,
            year_of_study=year_of_study,
            phone_number=phone_number,
        )
        user.set_password(password)   # hashes before storing
        db.session.add(user)
        db.session.commit()

        # Log the new user in immediately so signup isn't a dead-end
        session["user_id"] = user.id
        return redirect(url_for("listings.browse"))

    return render_template("signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        next_path = request.form.get("next") or url_for("listings.browse")

        user = User.query.filter_by(email=email).first()
        # Single generic error for both cases — don't leak which emails exist
        if user and user.check_password(password):
            session["user_id"] = user.id
            return redirect(next_path)

        flash("Invalid email or password.")
        return redirect(url_for("auth.login", next=next_path))

    # Preserve ?next=... from a login_required redirect through to the POST above
    next_path = request.args.get("next", "")
    return render_template("login.html", next=next_path)


@auth_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("auth.login"))
