import os


class Config:
    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "secretkey")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///instance/canteenkart.sqlite3"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADMIN_PHONE = os.environ.get("ADMIN_PHONE", "0000000000")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "adminpass")

    GEMINI_API_KEY = os.environ.get("AIzaSyDDimhXMBQPuhXCfu0EINGGkUPH6Fjr9ww")
    