from datetime import datetime

from extensions import db


class TokenBlocklist(db.Model):
    __tablename__ = "token_blocklist"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    jti = db.Column(
        db.String(36),
        unique=True,
        nullable=False
    )

    token_type = db.Column(
        db.String(20),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    revoked_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<TokenBlocklist {self.jti}>"