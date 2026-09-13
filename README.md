# Campus Resource Board

A web platform where university students can post and browse listings across
three categories: secondhand textbooks, study groups, and tutoring — with
in-app messaging so students can connect without sharing personal contact
details up front.

## Problem

Students currently rely on scattered WhatsApp groups, Facebook posts, and word
of mouth to find or offload textbooks, study partners, or tutors. This makes
listings hard to search, easy to miss, and limited to your existing circle.

## Features

**Accounts**
- Sign up / log in / log out, with hashed passwords and session-based auth
- Profile page: view/edit your details (university, major, year of study,
  phone number), change your password
- University, year of study, and phone number are required at signup;
  major is optional

**Listings**
- Create, edit, and delete your own listings — enforced at the route level,
  not just hidden in the UI
- Optional photo per listing, validated server-side (not just by file
  extension) and capped at 5MB
- Browse all listings, search by keyword (matches title and description),
  filter by category, sort by newest or price
- Mark a listing as resolved once it's sold/filled — stays visible but
  clearly marked, rather than disappearing

**Messaging**
- Real in-app conversations between a listing's owner and an interested
  student, scoped per listing so multiple buyers don't see each other's
  messages
- Inbox showing all your conversations, with an unread-message badge in
  the nav

## Tech stack

- **Backend:** Python + Flask
- **Database:** SQLite (dev) — Flask-SQLAlchemy ORM
- **Frontend:** HTML, CSS, JavaScript (no framework)
- **Image handling:** Pillow, for validating uploaded photos are genuine
  images before they're saved

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python seed.py                # creates the DB and seeds categories — run once
flask --app app run --debug
```

The app will be available at `http://127.0.0.1:5000`.

If you pull changes that touch `models.py`, delete `campus_board.db` and
re-run `python seed.py` — this project doesn't use migrations yet, so
schema changes need a fresh database in dev.

## Project structure

```
campus-resource-board/
├── app.py                 # app factory, blueprint registration, unread-count context processor
├── config.py              # DB URI, secret key, upload folder, allowed image types
├── models.py              # User, Category, Listing, Message
├── utils.py                # login_required, ownership/participant checks, image upload helpers
├── seed.py                 # one-off script to populate starter categories
├── routes/
│   ├── auth.py              # signup, login, logout
│   ├── listings.py          # browse, create, edit, delete, search/filter, sort, mark resolved
│   ├── profile.py           # view/edit profile, change password, "my listings"
│   └── messages.py          # inbox, per-listing conversation threads
├── templates/                # Jinja2 templates
│   ├── _back_link.html        # shared back-navigation partial
│   └── _listing_card.html     # shared listing card (used on browse + profile)
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── uploads/                # listing photos (gitignored — user content, not source)
└── requirements.txt
```

## Database schema

| Table | Purpose |
|---|---|
| `users` | Registered students, including campus context (university, major, year) |
| `categories` | Fixed list: Textbooks, Study Groups, Tutoring |
| `listings` | Core postings — title, description, price, category, status, optional photo |
| `messages` | In-app messages between a listing's owner and one buyer at a time |

## Status: roadmap complete

Every item from the original MVP and stretch goals is built, tested, and
working:

- [x] User signup and login
- [x] Create, view, edit, delete listings
- [x] Browse, search, and filter by category
- [x] Listing detail page
- [x] In-app messaging
- [x] Mark listing as resolved
- [x] Sort listings (newest / price)
- [x] Profile page showing your own listings
- [ ] Admin view to remove flagged posts — intentionally not built yet;
      needs a proper admin/role system to do safely, rather than a bolted-on
      shortcut

Features built beyond the original scope: full profile editing, password
confirmation and validation, campus-context signup fields, back-navigation,
and photo uploads with real image validation.

## Known limitations

- **No CSRF protection yet** on forms (delete, message-send, etc.) — a
  real gap worth closing before any public deployment.
- **Messaging is refresh-based, not real-time** — you won't see a reply
  appear until you reload the page. A deliberate scope choice, not an
  oversight.
- **No migrations** — schema changes require deleting and recreating the
  local database. Fine for solo dev; would need Flask-Migrate for anything
  with real user data to preserve.
