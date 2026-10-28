"""
Week 3 focus: create/view/edit/delete listings (CRUD).
Week 4 focus: browse page + search/filter by category and keyword.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort, g
from models import db, Listing, Category, User, Report
from utils import (
    login_required,
    require_ownership,
    current_user_owns,
    save_listing_image,
    delete_listing_image,
)

listings_bp = Blueprint("listings", __name__)

REPORT_REASONS = [
    "Spam or scam",
    "Inappropriate content",
    "Misleading or fake listing",
    "Other",
]


@listings_bp.route("/")
def browse():
    # Listings from deactivated accounts never appear in browse
    query = Listing.query.join(User, Listing.user_id == User.id).filter(
        User.is_active.is_(True)
    )

    category_id = request.args.get("category")
    keyword = request.args.get("q")
    sort = request.args.get("sort", "newest")

    if category_id:
        # Explicit column: after the join above, filter_by() would look on User, not Listing
        query = query.filter(Listing.category_id == category_id)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            db.or_(Listing.title.ilike(like), Listing.description.ilike(like))
        )

    if sort == "price_low":
        # Free listings (price is NULL) sort first either way — nullsfirst keeps that explicit
        query = query.order_by(Listing.price.asc().nullsfirst())
    else:
        query = query.order_by(Listing.created_at.desc())

    listings = query.all()
    categories = Category.query.all()

    return render_template(
        "browse.html", listings=listings, categories=categories, sort=sort
    )


@listings_bp.route("/listing/<int:listing_id>")
def detail(listing_id):
    listing = Listing.query.get_or_404(listing_id)

    # A deactivated user's listings are hidden; only admins can still open them
    viewer = g.get("current_user")
    if not listing.owner.is_active and not (viewer and viewer.is_admin):
        abort(404)

    is_owner = current_user_owns(listing)
    return render_template("listing_detail.html", listing=listing, is_owner=is_owner)


@listings_bp.route("/listing/new", methods=["GET", "POST"])
@login_required
def create():
    categories = Category.query.all()

    if request.method == "POST":
        try:
            image_filename = save_listing_image(request.files.get("image"))
        except ValueError as e:
            flash(str(e))
            return render_template("listing_form.html", categories=categories, listing=None)

        listing = Listing(
            user_id=session["user_id"],
            category_id=request.form["category_id"],
            title=request.form["title"],
            description=request.form.get("description"),
            price=request.form.get("price") or None,
            image_filename=image_filename,
        )
        db.session.add(listing)
        db.session.commit()
        return redirect(url_for("listings.detail", listing_id=listing.id))

    return render_template("listing_form.html", categories=categories, listing=None)


@listings_bp.route("/listing/<int:listing_id>/edit", methods=["GET", "POST"])
@login_required
def edit(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    require_ownership(listing)
    categories = Category.query.all()

    if request.method == "POST":
        try:
            new_image = save_listing_image(request.files.get("image"))
        except ValueError as e:
            flash(str(e))
            return render_template("listing_form.html", categories=categories, listing=listing)

        remove_image = request.form.get("remove_image") == "1"

        if new_image:
            delete_listing_image(listing.image_filename)
            listing.image_filename = new_image
        elif remove_image:
            delete_listing_image(listing.image_filename)
            listing.image_filename = None

        listing.title = request.form["title"]
        listing.category_id = request.form["category_id"]
        listing.description = request.form.get("description")
        listing.price = request.form.get("price") or None
        db.session.commit()
        return redirect(url_for("listings.detail", listing_id=listing.id))

    return render_template("listing_form.html", categories=categories, listing=listing)


@listings_bp.route("/listing/<int:listing_id>/delete", methods=["POST"])
@login_required
def delete(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    require_ownership(listing)

    delete_listing_image(listing.image_filename)
    db.session.delete(listing)
    db.session.commit()
    return redirect(url_for("listings.browse"))


@listings_bp.route("/listing/<int:listing_id>/toggle-status", methods=["POST"])
@login_required
def toggle_status(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    require_ownership(listing)

    listing.status = "resolved" if listing.status == "active" else "active"
    db.session.commit()
    return redirect(url_for("listings.detail", listing_id=listing.id))


@listings_bp.route("/listing/<int:listing_id>/report", methods=["GET", "POST"])
@login_required
def report(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    if not listing.owner.is_active:
        abort(404)

    uid = session["user_id"]

    if current_user_owns(listing):
        flash("You can't report your own listing.")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    already_reported = Report.query.filter_by(
        listing_id=listing.id, reporter_id=uid, status="open"
    ).first()
    if already_reported:
        flash("You've already reported this listing — an admin will review it.")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    if request.method == "POST":
        reason = request.form.get("reason", "")
        if reason not in REPORT_REASONS:
            flash("Please choose a reason for the report.")
            return redirect(url_for("listings.report", listing_id=listing.id))

        details = request.form.get("details", "").strip()[:1000] or None
        db.session.add(Report(
            listing_id=listing.id,
            listing_title=listing.title,  # snapshot, in case the listing is removed later
            reporter_id=uid,
            reason=reason,
            details=details,
        ))
        db.session.commit()
        flash("Thanks — an admin will review this listing.", "success")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    return render_template("report.html", listing=listing, reasons=REPORT_REASONS)
