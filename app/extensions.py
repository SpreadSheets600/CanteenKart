from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Initializing Extensions .... ")

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
