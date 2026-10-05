"""Idempotently seed the three Day 1 demonstration applications."""
import os
import secrets
from app import app
from extensions import bcrypt, db
from models.job import ApplicationStatus, JobApplication
from models.user import User


def seed_database():
    with app.app_context():
        user = User.query.filter_by(email="demo@example.com").first()
        if user is None:
            user = User(
                name="Demo User",
                email="demo@example.com",
                password=bcrypt.generate_password_hash(
                    os.getenv("DEMO_USER_PASSWORD") or "demopassword123"
                ).decode("utf-8"),
            )
            db.session.add(user)
            db.session.flush()

        hr_user = User.query.filter_by(email="hr@company.com").first()
        if hr_user is None:
            from models.user import Role
            hr_user = User(
                name="HR Manager",
                email="hr@company.com",
                role=Role.HR,
                password=bcrypt.generate_password_hash("hrpassword123").decode("utf-8"),
            )
            db.session.add(hr_user)
            db.session.flush()

        examples = [
            ("Google", "Software Engineer", ApplicationStatus.APPLIED),
            ("Microsoft", "Backend Developer", ApplicationStatus.PHONE_SCREEN),
            ("Amazon", "Python Developer", ApplicationStatus.INTERVIEW),
        ]
        created = 0
        for company, role, status in examples:
            if not JobApplication.query.filter_by(company=company, role=role, user_id=user.id).first():
                db.session.add(JobApplication(company=company, role=role, status=status, user_id=user.id))
                created += 1
        db.session.commit()
        return created


if __name__ == "__main__":
    created = seed_database()
    print(f"Seed complete: {created} application(s) inserted.")
