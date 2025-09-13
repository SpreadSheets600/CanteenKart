import os


class Config:
    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "secretkey")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///instance/canteenkart.sqlite3"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False


