from app import app
from extensions import db
from models.job import Job

with app.app_context():

    # Create 3 sample job applications
    job1 = Job(
        company="Google",
        position="Software Engineer",
        status="Applied",
        location="Chennai"
    )

    job2 = Job(
        company="Microsoft",
        position="Backend Developer",
        status="Interview",
        location="Bangalore"
    )

    job3 = Job(
        company="Amazon",
        position="Python Developer",
        status="Applied",
        location="Hyderabad"
    )

    db.session.add_all([job1, job2, job3])
    db.session.commit()

    print("3 sample job applications added successfully!")