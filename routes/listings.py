"""
Create/view/edit/delete listings (CRUD).
Browse page + search/filter by category and keyword.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, Listing, Category
from utils import (
    login_required,
    require_ownership,
    current_user_owns,
    save_listing_image,
    delete_listing_image,
)

listings_bp = Blueprint("listings", __name__)


@listings_bp.route("/")
def browse():
    query = Listing.query

    category_id = request.args.get("category")
    keyword = request.args.get("q")
    sort = request.args.get("sort", "newest")

    if category_id:
        query = query.filter_by(category_id=category_id)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            db.or_(Listing.title.ilike(like), Listing.description.ilike(like))
        )

    if sort == "price_low":
        # Free listings (price is NULL) sort first either way, nullsfirst keeps that explicit
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
    is_owner = current_user_owns(listing)   # controls edit/delete UI in the template
    return render_template("listing_detail.html", listing=listing, is_owner=is_owner)


@listings_bp.route("/listing/new", methods=["GET", "POST"])
@login_required
def create():
    categories = Category.query.all()

    if request.method == "POST":
        try:
            image_filename = save_listing_image(request.files.get("image"))
        except ValueError as e:
            # Bad file type/size, re-render with the form intact rather than losing input
            flash(str(e))
            return render_template("listing_form.html", categories=categories, listing=None)

        listing = Listing(
            user_id=session["user_id"],
            category_id=request.form["category_id"],
            title=request.form["title"],
            description=request.form.get("description"),
            price=request.form.get("price") or None,    # empty string -> NULL (free)
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

        # New upload wins over a remove request; otherwise honour the checkbox
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

    delete_listing_image(listing.image_filename)    # don't orphan the file on disk
    db.session.delete(listing)
    db.session.commit()
    return redirect(url_for("listings.browse"))


@listings_bp.route("/listing/<int:listing_id>/toggle-status", methods=["POST"])
@login_required
def toggle_status(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    require_ownership(listing)

    # Flip between the only two valid states
    listing.status = "resolved" if listing.status == "active" else "active"
    db.session.commit()
    return redirect(url_for("listings.detail", listing_id=listing.id))
