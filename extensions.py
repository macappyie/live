from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

# Database
db = SQLAlchemy()

# Password Hashing
bcrypt = Bcrypt()

# Login Manager
login_manager = LoginManager()

login_manager.login_view = "auth.login"
login_manager.login_message = "Please login to continue."
login_manager.login_message_category = "warning"
