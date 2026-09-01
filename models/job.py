from extensions import db


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default="Applied")
    location = db.Column(db.String(100))

    def __repr__(self):
        return f"<Job {self.company}>"