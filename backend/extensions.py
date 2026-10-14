from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os


db = SQLAlchemy()

bcrypt = Bcrypt()

jwt = JWTManager()

cache = Cache()

mail = Mail()

# Shared limiter so individual blueprints can declare per-route limits
# without importing the application object.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[
        os.getenv("RATE_LIMIT_DEFAULT", "100 per minute")
    ]
)
