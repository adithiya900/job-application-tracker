from flask import Blueprint, request, jsonify
from extensions import db
from models.job import Job

jobs_bp = Blueprint("jobs", __name__)


# Add a new job
@jobs_bp.route("/jobs", methods=["POST"])
def add_job():
    data = request.get_json()

    # Check if request contains JSON data
    if not data:
        return jsonify({
            "error": "No data provided"
        }), 400

    # Validate required fields
    if not data.get("company"):
        return jsonify({
            "error": "Company is required"
        }), 400

    if not data.get("position"):
        return jsonify({
            "error": "Position is required"
        }), 400

    try:
        new_job = Job(
            company=data["company"],
            position=data["position"],
            status=data.get("status", "Applied"),
            location=data.get("location")
        )

        db.session.add(new_job)
        db.session.commit()

        return jsonify({
            "message": "Job added successfully!",
            "id": new_job.id
        }), 201

    except Exception as e:
        db.session.rollback()

        return jsonify({
            "error": "Failed to add job",
            "details": str(e)
        }), 500


# Get all jobs with status filter and company search
@jobs_bp.route("/jobs", methods=["GET"])
def get_jobs():
    status = request.args.get("status")
    search = request.args.get("search")

    query = Job.query

    if status:
        query = query.filter_by(status=status)

    if search:
        query = query.filter(Job.company.ilike(f"%{search}%"))

    jobs = query.all()

    result = []

    for job in jobs:
        result.append({
            "id": job.id,
            "company": job.company,
            "position": job.position,
            "status": job.status,
            "location": job.location
        })

    return jsonify(result)


# Get a specific job by ID
@jobs_bp.route("/jobs/<int:id>", methods=["GET"])
def get_job(id):
    job = Job.query.get_or_404(id)

    return jsonify({
        "id": job.id,
        "company": job.company,
        "position": job.position,
        "status": job.status,
        "location": job.location
    })


# Update a job by ID
@jobs_bp.route("/jobs/<int:id>", methods=["PUT"])
def update_job(id):
    job = Job.query.get_or_404(id)

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No data provided"
        }), 400

    try:
        job.company = data.get("company", job.company)
        job.position = data.get("position", job.position)
        job.status = data.get("status", job.status)
        job.location = data.get("location", job.location)

        db.session.commit()

        return jsonify({
            "message": "Job updated successfully!",
            "id": job.id
        })

    except Exception as e:
        db.session.rollback()

        return jsonify({
            "error": "Failed to update job",
            "details": str(e)
        }), 500


# Delete a job by ID
@jobs_bp.route("/jobs/<int:id>", methods=["DELETE"])
def delete_job(id):
    job = Job.query.get_or_404(id)

    try:
        db.session.delete(job)
        db.session.commit()

        return jsonify({
            "message": "Job deleted successfully!"
        })

    except Exception as e:
        db.session.rollback()

        return jsonify({
            "error": "Failed to delete job",
            "details": str(e)
        }), 500