from extensions import db


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

    # One user can have many job applications
    applications = db.relationship(
        "JobApplication",
        backref="user",
        lazy=True
    )

    def __repr__(self):
        return f"<User {self.name}>"