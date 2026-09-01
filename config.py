import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Swap this for a real secret (env var) before deploying anywhere public
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'campus_board.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
