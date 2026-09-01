from flask import Flask
from dotenv import load_dotenv
import os

from extensions import db
from models.job import Job
from api.jobs import jobs_bp

load_dotenv()

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

app.register_blueprint(jobs_bp)

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return "Job Application Tracker API is running!"


@app.route("/test-db")
def test_db():
    try:
        db.session.execute(db.text("SELECT 1"))
        return "Database connected successfully!"
    except Exception as e:
        return f"Database connection failed: {str(e)}"


if __name__ == "__main__":
    app.run(debug=True)