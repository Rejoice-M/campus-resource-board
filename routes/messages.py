"""
In-app messaging. A "conversation" is derived, not stored as its own row —
it's just every Message with the same (listing_id, the two participants),
in either direction. Every conversation has exactly one buyer and the
listing's owner as its two participants.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from sqlalchemy import or_, and_
from models import db, Message, Listing, User
from utils import login_required, require_thread_participant

messages_bp = Blueprint("messages", __name__)


@messages_bp.route("/messages")
@login_required
def inbox():
    uid = session["user_id"]

    all_messages = (
        Message.query.filter(or_(Message.sender_id == uid, Message.receiver_id == uid))
        .order_by(Message.sent_at.desc())
        .all()
    )

    # Collapse into one row per (listing, other participant), keeping only
    # the most recent message in each — relies on the query above already
    # being sorted newest-first, so the first one seen per key wins.
    conversations = []
    seen = set()
    unread_count = 0

    for m in all_messages:
        other_id = m.receiver_id if m.sender_id == uid else m.sender_id
        other = m.sender if m.sender_id != uid else m.receiver

        # Conversations with deactivated accounts are closed, so they drop out of the inbox
        if not other.is_active:
            continue

        key = (m.listing_id, other_id)

        if m.receiver_id == uid and not m.is_read:
            unread_count += 1

        if key in seen:
            continue
        seen.add(key)

        conversations.append({
            "listing": m.listing,
            "other_user": m.sender if m.sender_id != uid else m.receiver,
            "last_message": m,
            "unread": m.receiver_id == uid and not m.is_read,
        })

    return render_template("inbox.html", conversations=conversations, unread_count=unread_count)


@messages_bp.route("/messages/<int:listing_id>/<int:other_user_id>", methods=["GET", "POST"])
@login_required
def thread(listing_id, other_user_id):
    uid = session["user_id"]
    listing = Listing.query.get_or_404(listing_id)
    other_user = User.query.get_or_404(other_user_id)

    if not other_user.is_active:
        flash("That user is no longer available.")
        return redirect(url_for("messages.inbox"))

    if other_user_id == uid:
        flash("You can't message yourself about your own listing.")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    require_thread_participant(listing, other_user_id)

    if request.method == "POST":
        body = request.form.get("body", "").strip()
        if body:
            db.session.add(Message(
                listing_id=listing.id,
                sender_id=uid,
                receiver_id=other_user_id,
                body=body,
            ))
            db.session.commit()
        return redirect(url_for("messages.thread", listing_id=listing.id, other_user_id=other_user_id))

    thread_messages = (
        Message.query.filter(
            Message.listing_id == listing.id,
            or_(
                and_(Message.sender_id == uid, Message.receiver_id == other_user_id),
                and_(Message.sender_id == other_user_id, Message.receiver_id == uid),
            ),
        )
        .order_by(Message.sent_at.asc())
        .all()
    )

    # Mark anything sent TO the current user in this thread as read
    unread = [m for m in thread_messages if m.receiver_id == uid and not m.is_read]
    for m in unread:
        m.is_read = True
    if unread:
        db.session.commit()

    return render_template(
        "thread.html",
        listing=listing,
        other_user=other_user,
        messages=thread_messages,
        current_user_id=uid,
    )
