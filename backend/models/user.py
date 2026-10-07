from extensions import db
from datetime import datetime
import enum


class Role(enum.Enum):
    USER = "USER"
    HR = "HR"
    ADMIN = "ADMIN"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    # Hashed password
    password = db.Column(
        db.String(255),
        nullable=False
    )

    # User role
    role = db.Column(
        db.Enum(Role),
        nullable=False,
        default=Role.USER
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    # User timezone (IANA timezone string, e.g., 'Asia/Kolkata', 'UTC')
    timezone = db.Column(
        db.String(50),
        nullable=False,
        default='UTC'
    )

    # Slack webhook URL for notifications
    webhook_url = db.Column(
        db.String(500),
        nullable=True
    )

    # One user can have many job applications
    applications = db.relationship(
        "JobApplication",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    blocklisted_tokens = db.relationship(
        "TokenBlocklist",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.name}>"
