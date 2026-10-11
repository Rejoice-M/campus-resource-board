
from app import create_app
from models import db, Category

CATEGORIES = ["Textbooks", "Study Groups", "Tutoring"]

app = create_app()

with app.app_context():
    for name in CATEGORIES:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))
    db.session.commit()
    print("Categories seeded:", [c.name for c in Category.query.all()])
