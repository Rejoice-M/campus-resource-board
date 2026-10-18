"""
SQLAlchemy models — mirrors the schema in the project plan doc.
Design these on paper first, then let this file be the implementation.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    # --- core fields ---
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # --- campus-context fields (MVP) ---
    university = db.Column(db.String(200), nullable=True)
    major = db.Column(db.String(100), nullable=True)
    year_of_study = db.Column(db.String(50), nullable=True)  # e.g. "2nd year"

    # --- future-proofing fields ---
    phone_number = db.Column(db.String(20), nullable=True)
    profile_picture = db.Column(db.String(200), nullable=True)  # URL or filename, not yet used in UI

    # --- timestamps ---
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- moderation ---
    # is_active=False means an admin deactivated the account: login is blocked and
    # the user's listings are hidden from browse. Nothing is deleted.
    is_active = db.Column(db.Boolean, default=True)
    # Set only via create_admin.py, never from the public signup form
    is_admin = db.Column(db.Boolean, default=False)

    listings = db.relationship("Listing", backref="owner", lazy=True)

    # --- password helpers, so routes never touch generate/check_password_hash directly ---
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    # e.g. "Textbooks", "Study Groups", "Tutoring"

    listings = db.relationship("Listing", backref="category", lazy=True)


class Listing(db.Model):
    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=True)  # null/0 = free
    status = db.Column(db.String(20), default="active")  # active / resolved
    image_filename = db.Column(db.String(255), nullable=True)  # stored on disk in static/uploads/
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Real messaging (was stretch — now built)
class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    # cascade: deleting a listing deletes its conversations too
    listing = db.relationship(
        "Listing", backref=db.backref("messages", cascade="all, delete-orphan")
    )
    sender = db.relationship("User", foreign_keys=[sender_id])
    receiver = db.relationship("User", foreign_keys=[receiver_id])


class Report(db.Model):
    """A user flagging a listing for an admin to review."""
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    # Becomes NULL if the listing is later removed; listing_title keeps the report readable
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id"), nullable=True)
    listing_title = db.Column(db.String(150), nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reason = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="open")  # open / dismissed / actioned
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    listing = db.relationship("Listing", backref="reports")
    reporter = db.relationship("User", foreign_keys=[reporter_id])
    resolved_by = db.relationship("User", foreign_keys=[resolved_by_id])


class AdminLog(db.Model):
    """Append-only record of what each admin did, and when."""
    __tablename__ = "admin_logs"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # e.g. remove_listing
    target_type = db.Column(db.String(20), nullable=True)  # listing / user / report
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship("User")
