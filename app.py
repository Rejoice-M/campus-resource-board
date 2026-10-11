from flask import Flask
from config import Config
from models import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Imported inside create_app (not at module top) to avoid circular imports
    # between the app factory and the route modules
    from routes.auth import auth_bp
    from routes.listings import listings_bp
    from routes.profile import profile_bp
    from routes.messages import messages_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(messages_bp)

    with app.app_context():
        db.create_all()  

    # Runs on every render_template call, so the unread badge is available
    # in every template without each route passing it in
    @app.context_processor
    def inject_unread_count():
        from flask import session
        from models import Message
        uid = session.get("user_id")
        if not uid:
            return {"unread_message_count": 0}  # logged-out visitors see nothing
        count = Message.query.filter_by(receiver_id=uid, is_read=False).count()
        return {"unread_message_count": count}

    return app

# Module-level instance so `flask run` / WSGI servers can find it
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
