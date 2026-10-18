"""
Campus Resource Board - Flask app entry point.

Run with: flask --app app run --debug
"""

from flask import Flask, g, session, request, flash, redirect, url_for
from flask_wtf.csrf import CSRFProtect, CSRFError
from config import Config
from models import db, User, Message, Report

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    csrf.init_app(app)  # every POST must carry a valid csrf_token

    # Register blueprints (add these as you build each feature)
    from routes.auth import auth_bp
    from routes.listings import listings_bp
    from routes.profile import profile_bp
    from routes.messages import messages_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()  # fine for dev; use migrations later if this grows

    @app.before_request
    def load_current_user():
        """
        Load the signed-in user once per request into g.current_user.
        If the account was deactivated (or deleted) while they were signed in,
        end their session immediately rather than waiting for the next login.
        """
        g.current_user = None
        if request.endpoint == "static":
            return
        uid = session.get("user_id")
        if uid:
            user = db.session.get(User, uid)
            if user is None or not user.is_active:
                session.pop("user_id", None)
            else:
                g.current_user = user

    @app.context_processor
    def inject_globals():
        user = g.get("current_user")
        unread = 0
        open_reports = 0
        if user:
            # Messages from deactivated users don't count — their threads are closed
            unread = (
                Message.query.join(User, Message.sender_id == User.id)
                .filter(
                    Message.receiver_id == user.id,
                    Message.is_read.is_(False),
                    User.is_active.is_(True),
                )
                .count()
            )
            if user.is_admin:
                open_reports = Report.query.filter_by(status="open").count()
        return {
            "current_user": user,
            "unread_message_count": unread,
            "open_report_count": open_reports,
        }

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash("That form expired or couldn't be verified. Please try again.")
        return redirect(url_for("listings.browse"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
