# Campus Resource Board

A web platform where university students can post and browse listings across
three categories: secondhand textbooks, study groups, and tutoring.

## Problem

Students currently rely on scattered WhatsApp groups, Facebook posts, and word
of mouth to find or offload textbooks, study partners, or tutors. This makes
listings hard to search, easy to miss, and limited to your existing circle.

## Tech stack

- **Backend:** Python + Flask
- **Database:** SQLite (dev) — Flask-SQLAlchemy ORM
- **Frontend:** HTML, CSS, JavaScript (no framework for v1)

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
flask --app app run --debug
```

The app will be available at `http://127.0.0.1:5000`.

## Project structure

```
campus-resource-board/
├── app.py              # app factory, blueprint registration
├── config.py           # config (DB URI, secret key)
├── models.py           # User, Category, Listing, Message
├── routes/
│   ├── auth.py          # signup, login, logout
│   └── listings.py      # browse, create, detail, search/filter
├── templates/           # Jinja2 templates
├── static/
│   ├── css/style.css
│   └── js/main.js
└── requirements.txt
```

## Roadmap

| Phase | Focus | Deliverable |
|---|---|---|
| Week 1 | Schema design + environment setup | SQLite DB created, Flask skeleton running |
| Week 2 | Authentication | Working signup/login with hashing + sessions |
| Week 3 | Core CRUD | Create, view, edit, delete own listings |
| Week 4 | Browse + search/filter | Home page + filter by category/keyword |
| Week 5 | Polish + styling | Consistent CSS, responsive layout |
| Stretch | Messaging, status, sorting | In-app contact, mark resolved, sort options |

## MVP checklist

- [ ] User signup and login
- [ ] Create a listing
- [ ] Browse all listings
- [ ] Search and filter by category and keyword
- [ ] View a single listing's detail page
