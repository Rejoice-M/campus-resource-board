"""
Week 3 focus: create/view/edit/delete listings (CRUD).
Week 4 focus: browse page + search/filter by category and keyword.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, Listing, Category

listings_bp = Blueprint("listings", __name__)


@listings_bp.route("/")
def browse():
    query = Listing.query

    category_id = request.args.get("category")
    keyword = request.args.get("q")

    if category_id:
        query = query.filter_by(category_id=category_id)
    if keyword:
        query = query.filter(Listing.title.ilike(f"%{keyword}%"))

    listings = query.order_by(Listing.created_at.desc()).all()
    categories = Category.query.all()

    return render_template("browse.html", listings=listings, categories=categories)


@listings_bp.route("/listing/<int:listing_id>")
def detail(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    return render_template("listing_detail.html", listing=listing)


@listings_bp.route("/listing/new", methods=["GET", "POST"])
def create():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        listing = Listing(
            user_id=session["user_id"],
            category_id=request.form["category_id"],
            title=request.form["title"],
            description=request.form.get("description"),
            price=request.form.get("price") or None,
        )
        db.session.add(listing)
        db.session.commit()
        return redirect(url_for("listings.detail", listing_id=listing.id))

    categories = Category.query.all()
    return render_template("listing_form.html", categories=categories)
