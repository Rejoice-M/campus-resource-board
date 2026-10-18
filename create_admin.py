"""
Give (or take away) admin rights. Admins are never created from the public
signup form, so this is the only way to become one.

Usage:
    python create_admin.py you@example.com            # make this user an admin
    python create_admin.py you@example.com --remove   # remove their admin rights

Sign up on the site normally first, then run this with the same email.
"""

import sys
from app import create_app
from models import db, User


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__)
        return 1

    email = args[0].strip().lower()
    remove = "--remove" in args[1:]

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"No account found for {email}. Sign up on the site first, then run this again.")
            return 1

        if remove:
            if not user.is_admin:
                print(f"{email} isn't an admin.")
                return 0
            if User.query.filter_by(is_admin=True).count() <= 1:
                print("Can't remove the last remaining admin — promote someone else first.")
                return 1
            user.is_admin = False
            db.session.commit()
            print(f"{email} is no longer an admin.")
            return 0

        if user.is_admin:
            print(f"{email} is already an admin.")
            return 0
        user.is_admin = True
        user.is_active = True  # an admin account must never be left deactivated
        db.session.commit()
        print(f"{email} is now an admin. Log in and use the Admin link in the nav.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
