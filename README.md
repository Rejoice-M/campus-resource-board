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

**Moderation and admin**
- Any signed-in user can report a listing (spam, inappropriate, misleading,
  other); one open report per user per listing
- Admin area at `/admin`, protected by a single guard on the whole blueprint:
  - **Dashboard** — user and listing counts, listings per category, new
    signups this week, open reports
  - **Listings** — search everything (title, description, poster name/email)
    and remove any listing, including its photo and conversations
  - **Reports** — a queue of open reports; dismiss, or remove the listing
    (reports keep a title snapshot, so the history survives the removal)
  - **Users** — search, deactivate and reactivate accounts. Deactivating signs
    the user out immediately, blocks login, hides all their listings from
    browse/search/detail, and closes their conversations. Nothing is deleted,
    so reactivating restores everything
  - **Action log** — every admin action, who did it, and when
- Admins can't deactivate themselves or other admins, and the last remaining
  admin can't be demoted

**Security**
- CSRF protection on every form (Flask-WTF)
- Ownership and admin checks enforced on the server, not just hidden in the UI
- Login `next` redirects only allowed to paths on this site

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

### Becoming an admin

Admins can't be created from the signup form. Sign up normally, then promote
that account from the command line:

```bash
python create_admin.py you@example.com            # grant admin rights
python create_admin.py you@example.com --remove   # take them away again
```

Log in again and an **Admin** link appears in the nav.

### Upgrading an existing database

If you pull changes that touch `models.py`, delete `campus_board.db` and
re-run `python seed.py` — this project doesn't use migrations yet, so
schema changes need a fresh database in dev.

To keep your existing data when upgrading to the admin features, add the one
new column instead (the new `reports` and `admin_logs` tables are created
automatically on startup):

```bash
python -c "import sqlite3; c=sqlite3.connect('campus_board.db'); c.execute('ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0'); c.commit()"
```

## Project structure

```
campus-resource-board/
├── app.py                 # app factory, blueprint registration, unread-count context processor
├── config.py              # DB URI, secret key, upload folder, allowed image types
├── models.py              # User, Category, Listing, Message
├── utils.py                # login_required, ownership checks, safe-redirect check, admin log, image helpers
├── seed.py                 # one-off script to populate starter categories
├── create_admin.py         # grant/remove admin rights from the command line
├── routes/
│   ├── auth.py              # signup, login, logout
│   ├── listings.py          # browse, create, edit, delete, search/filter, sort, mark resolved
│   ├── profile.py           # view/edit profile, change password, "my listings"
│   ├── messages.py          # inbox, per-listing conversation threads
│   └── admin.py             # dashboard, listing/report/user moderation, action log
├── templates/                # Jinja2 templates
│   ├── _back_link.html        # shared back-navigation partial
│   ├── _listing_card.html     # shared listing card (used on browse + profile)
│   ├── _csrf.html             # CSRF token field, included in every POST form
│   ├── report.html            # report-a-listing form
│   └── admin/                 # dashboard, listings, reports, users, action log
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
| `reports` | User reports against listings, with a status (open / dismissed / actioned) |
| `admin_logs` | Append-only record of admin actions |

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
- [x] Admin view to remove flagged posts — report system, moderation queue,
      user management, and an action log

Features built beyond the original scope: full profile editing, password
confirmation and validation, campus-context signup fields, back-navigation,
photo uploads with real image validation, and CSRF protection.

## Known limitations

- **Logging out is a plain link (GET request)**, so it isn't CSRF-protected;
  the impact is low (it only signs you out) but it should become a POST form.
- **Deactivation hides data, it doesn't erase it.** A deactivated user's
  listings, photos and messages stay in the database and on disk. There is
  no "delete account and all data" action yet.
- **Admin tables show the newest 200 rows**; use the search boxes to narrow
  down. There's no pagination yet.
- **No automated test suite in the repo** — behaviour was verified with
  throwaway scripts, which isn't the same as tests you can re-run.
- **Messaging is refresh-based, not real-time** — you won't see a reply
  appear until you reload the page. A deliberate scope choice, not an
  oversight.
- **No migrations** — schema changes require deleting and recreating the
  local database. Fine for solo dev; would need Flask-Migrate for anything
  with real user data to preserve.
