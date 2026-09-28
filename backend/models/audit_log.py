from datetime import datetime

from extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    admin_id = db.Column(
        db.Integer,
        nullable=False
    )

    action = db.Column(
        db.String(100),
        nullable=False
    )

    target_user_id = db.Column(
        db.Integer,
        nullable=True
    )

    details = db.Column(
        db.JSON,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<AuditLog {self.action}>"
