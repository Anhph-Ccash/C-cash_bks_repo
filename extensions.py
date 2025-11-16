# Ensure a single instance of extensions is created here.
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel
from flask_wtf import CSRFProtect

# Single shared instances used across the app
db = SQLAlchemy()
login_manager = LoginManager()
babel = Babel()
csrf = CSRFProtect()
