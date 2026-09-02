from app import app
from extensions import db
from models.user import User
from models.job import JobApplication, ApplicationStatus


with app.app_context():

    # Find existing user first
    user = User.query.filter_by(
        email="adithiya@example.com"
    ).first()

    # Create user only if not already exists
    if not user:
        user = User(
            name="Adithiya",
            email="adithiya@example.com"
        )

        db.session.add(user)
        db.session.commit()

        print("User created successfully!")
    else:
        print("User already exists!")

    # Add 3 applications only if none exist for this user
    existing_jobs = JobApplication.query.filter_by(
        user_id=user.id
    ).count()

    if existing_jobs == 0:

        job1 = JobApplication(
            company="Google",
            role="Software Engineer",
            status=ApplicationStatus.APPLIED,
            notes="Applied through careers page",
            user_id=user.id
        )

        job2 = JobApplication(
            company="Microsoft",
            role="Backend Developer",
            status=ApplicationStatus.PHONE_SCREEN,
            notes="Phone interview scheduled",
            user_id=user.id
        )

        job3 = JobApplication(
            company="Amazon",
            role="Python Developer",
            status=ApplicationStatus.INTERVIEW,
            notes="Technical interview",
            user_id=user.id
        )

        db.session.add_all([job1, job2, job3])
        db.session.commit()

        print("3 job applications added successfully!")

    else:
        print("Job applications already exist!")

    # Query applications by status
    applied_jobs = JobApplication.query.filter_by(
        status=ApplicationStatus.APPLIED
    ).all()

    print("\nApplications with APPLIED status:")

    for job in applied_jobs:
        print(f"{job.company} - {job.role}")

    # Update one application status
    job_to_update = JobApplication.query.filter_by(
        company="Google"
    ).first()

    if job_to_update:
        print(
            f"\nBefore update: "
            f"{job_to_update.company} - {job_to_update.status.value}"
        )

        job_to_update.status = ApplicationStatus.INTERVIEW

        db.session.commit()

        print(
            f"After update: "
            f"{job_to_update.company} - {job_to_update.status.value}"
        )