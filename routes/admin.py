"""
Admin area: dashboard, listing moderation, report queue, user management, action log.

Every route here is protected by one before_request guard (below), so a new
admin route can't be added and accidentally left open to everyone.
"""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, abort
from sqlalchemy import func, or_
from models import db, User, Listing, Category, Report, AdminLog
from utils import delete_listing_image, log_admin_action

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

ROW_LIMIT = 200  # keeps admin tables fast; use the search box to narrow down


@admin_bp.before_request
def require_admin():
    user = g.get("current_user")
    if user is None:
        return redirect(url_for("auth.login", next=request.path))
    if not user.is_admin:
        abort(403)


# ---------------------------------------------------------------- dashboard

@admin_bp.route("/")
def dashboard():
    week_ago = datetime.utcnow() - timedelta(days=7)

    stats = {
        "users_total": User.query.count(),
        "users_active": User.query.filter_by(is_active=True).count(),
        "new_users_week": User.query.filter(User.created_at >= week_ago).count(),
        "listings_total": Listing.query.count(),
        "listings_active": Listing.query.filter_by(status="active").count(),
        "listings_resolved": Listing.query.filter_by(status="resolved").count(),
        "open_reports": Report.query.filter_by(status="open").count(),
    }

    per_category = (
        db.session.query(Category.name, func.count(Listing.id))
        .outerjoin(Listing, Listing.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.id)
        .all()
    )
    recent_log = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(5).all()

    return render_template(
        "admin/dashboard.html", stats=stats, per_category=per_category, recent_log=recent_log
    )


# ----------------------------------------------------------------- listings

def _remove_listing(listing, note=None):
    """
    Delete a listing and its photo, mark any open reports on it as actioned,
    and log it. The caller commits. Reports survive (they keep a title snapshot);
    the listing's conversations are deleted along with it.
    """
    owner = listing.owner
    title = listing.title

    for r in Report.query.filter_by(listing_id=listing.id, status="open").all():
        r.status = "actioned"
        r.resolved_by_id = g.current_user.id
        r.resolved_at = datetime.utcnow()

    log_admin_action(
        "remove_listing", "listing", listing.id,
        f'"{title}" by {owner.name} ({owner.email})' + (f" — {note}" if note else ""),
    )

    delete_listing_image(listing.image_filename)
    db.session.delete(listing)
    db.session.commit()
    return title


@admin_bp.route("/listings")
def listings():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "")

    query = Listing.query.join(User, Listing.user_id == User.id)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            Listing.title.ilike(like),
            Listing.description.ilike(like),
            User.name.ilike(like),
            User.email.ilike(like),
        ))
    if category:
        query = query.filter(Listing.category_id == category)

    total = query.count()
    rows = query.order_by(Listing.created_at.desc()).limit(ROW_LIMIT).all()

    open_report_counts = dict(
        db.session.query(Report.listing_id, func.count(Report.id))
        .filter(Report.status == "open", Report.listing_id.isnot(None))
        .group_by(Report.listing_id)
        .all()
    )

    return render_template(
        "admin/listings.html",
        listings=rows,
        total=total,
        limit=ROW_LIMIT,
        categories=Category.query.all(),
        open_report_counts=open_report_counts,
        q=q,
        category=category,
    )


@admin_bp.route("/listings/<int:listing_id>/remove", methods=["POST"])
def remove_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    title = _remove_listing(listing)
    flash(f'Removed "{title}".', "success")
    return redirect(url_for("admin.listings"))


# ------------------------------------------------------------------ reports

@admin_bp.route("/reports")
def reports():
    status = request.args.get("status", "open")
    query = Report.query
    if status in ("open", "dismissed", "actioned"):
        query = query.filter_by(status=status)
    else:
        status = "all"

    rows = query.order_by(Report.created_at.desc()).limit(ROW_LIMIT).all()
    return render_template("admin/reports.html", reports=rows, status=status)


@admin_bp.route("/reports/<int:report_id>/dismiss", methods=["POST"])
def dismiss_report(report_id):
    report = Report.query.get_or_404(report_id)
    if report.status != "open":
        flash("That report has already been handled.")
        return redirect(url_for("admin.reports"))

    report.status = "dismissed"
    report.resolved_by_id = g.current_user.id
    report.resolved_at = datetime.utcnow()
    log_admin_action(
        "dismiss_report", "report", report.id,
        f'Report on "{report.listing_title}" ({report.reason})',
    )
    db.session.commit()
    flash("Report dismissed — the listing stays up.", "success")
    return redirect(url_for("admin.reports"))


@admin_bp.route("/reports/<int:report_id>/remove-listing", methods=["POST"])
def remove_reported_listing(report_id):
    report = Report.query.get_or_404(report_id)
    if report.status != "open":
        flash("That report has already been handled.")
        return redirect(url_for("admin.reports"))
    if report.listing is None:
        flash("That listing has already been removed.")
        return redirect(url_for("admin.reports"))

    title = _remove_listing(report.listing, note=f"reported for: {report.reason}")
    flash(f'Removed "{title}" and closed its reports.', "success")
    return redirect(url_for("admin.reports"))


# -------------------------------------------------------------------- users

@admin_bp.route("/users")
def users():
    q = request.args.get("q", "").strip()

    query = User.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            User.name.ilike(like), User.email.ilike(like), User.university.ilike(like)
        ))

    total = query.count()
    rows = query.order_by(User.created_at.desc()).limit(ROW_LIMIT).all()

    listing_counts = dict(
        db.session.query(Listing.user_id, func.count(Listing.id))
        .group_by(Listing.user_id)
        .all()
    )

    return render_template(
        "admin/users.html", users=rows, total=total, limit=ROW_LIMIT,
        listing_counts=listing_counts, q=q,
    )


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == g.current_user.id:
        flash("You can't deactivate your own account.")
        return redirect(url_for("admin.users"))
    if user.is_admin:
        flash("Admin accounts can't be deactivated here — remove their admin rights first with create_admin.py.")
        return redirect(url_for("admin.users"))

    if user.is_active:
        user.is_active = False
        log_admin_action("deactivate_user", "user", user.id, f"{user.name} ({user.email})")
        flash(f"{user.name} deactivated — their listings are now hidden.", "success")
    else:
        user.is_active = True
        log_admin_action("reactivate_user", "user", user.id, f"{user.name} ({user.email})")
        flash(f"{user.name} reactivated — their listings are visible again.", "success")

    db.session.commit()
    return redirect(url_for("admin.users"))


# --------------------------------------------------------------- action log

@admin_bp.route("/log")
def log():
    entries = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(ROW_LIMIT).all()
    return render_template("admin/log.html", entries=entries)
