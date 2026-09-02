from flask import Flask
from dotenv import load_dotenv
import os

from extensions import db
from flask_migrate import Migrate

# Import models
from models.job import JobApplication
from models.user import User

# Import Blueprint
from api.jobs import jobs_bp


load_dotenv()

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# Initialize database
db.init_app(app)

# Initialize migrations
migrate = Migrate(app, db)

# Register Blueprint
app.register_blueprint(jobs_bp)


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