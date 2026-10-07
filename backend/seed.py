"""Create or refresh local demo accounts and seed sample applications."""
import os

from app import app
from extensions import bcrypt, db
from models.job import ApplicationStatus, JobApplication
from models.user import Role, User


DEMO_ACCOUNTS = (
    {
        "name": "Demo User",
        "email_env": "DEMO_USER_EMAIL",
        "email": "user@gmail.com",
        "password_env": "DEMO_USER_PASSWORD",
        "role": Role.USER,
    },
    {
        "name": "HR Manager",
        "email_env": "DEMO_HR_EMAIL",
        "email": "hr@gmail.com",
        "password_env": "DEMO_HR_PASSWORD",
        "role": Role.HR,
    },
    {
        "name": "Admin User",
        "email_env": "DEMO_ADMIN_EMAIL",
        "email": "admin@gmail.com",
        "password_env": "DEMO_ADMIN_PASSWORD",
        "role": Role.ADMIN,
    },
)


def _ensure_demo_account(account):
    email = os.getenv(account["email_env"]) or account["email"]
    password = os.getenv(account["password_env"])
    if not password:
        raise RuntimeError(
            f"{account['password_env']} must be set before seeding demo accounts."
        )
    user = User.query.filter_by(email=email).first()

    if user is None:
        user = User(name=account["name"], email=email)

    user.name = account["name"]
    user.role = account["role"]
    user.password = bcrypt.generate_password_hash(password).decode("utf-8")
    db.session.add(user)
    db.session.flush()
    return user


def seed_database():
    """Idempotently provision local demo logins and their sample applications.

    These credentials are for local development/demo environments. Override the
    corresponding DEMO_* environment variables before seeding elsewhere.
    """
    with app.app_context():
        missing_passwords = [
            account["password_env"]
            for account in DEMO_ACCOUNTS
            if not os.getenv(account["password_env"])
        ]
        if missing_passwords:
            raise RuntimeError(
                "Set demo account passwords before seeding: "
                + ", ".join(missing_passwords)
            )

        emails = [
            (os.getenv(account["email_env"]) or account["email"]).casefold()
            for account in DEMO_ACCOUNTS
        ]
        if len(set(emails)) != len(emails):
            raise ValueError("Demo account email addresses must be unique.")

        users = {
            account["role"]: _ensure_demo_account(account)
            for account in DEMO_ACCOUNTS
        }
        user = users[Role.USER]

        examples = [
            ("Google", "Software Engineer", ApplicationStatus.APPLIED),
            ("Microsoft", "Backend Developer", ApplicationStatus.PHONE_SCREEN),
            ("Amazon", "Python Developer", ApplicationStatus.INTERVIEW),
        ]
        created = 0
        for company, role, status in examples:
            if not JobApplication.query.filter_by(
                company=company,
                role=role,
                user_id=user.id,
            ).first():
                db.session.add(
                    JobApplication(
                        company=company,
                        role=role,
                        status=status,
                        user_id=user.id,
                    )
                )
                created += 1
        db.session.commit()
        return created


if __name__ == "__main__":
    created = seed_database()
    print(f"Seed complete: {created} application(s) inserted.")
