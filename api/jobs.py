from flask import Blueprint, request, jsonify

from services.application_service import ApplicationService
from exceptions.application_exceptions import (
    ApplicationNotFound,
    DuplicateApplication
)
from models.job import ApplicationStatus


jobs_bp = Blueprint("jobs", __name__)


# Create application
@jobs_bp.route("/applications", methods=["POST"])
def create_application():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        if "status" in data:
            data["status"] = ApplicationStatus[data["status"]]

        application = ApplicationService.create_application(data)

        return jsonify({
            "message": "Application created successfully!",
            "id": application.id
        }), 201

    except DuplicateApplication as e:
        return jsonify({"error": str(e)}), 409

    except KeyError as e:
        return jsonify({
            "error": f"Missing required field: {str(e)}"
        }), 400


# Get all applications
@jobs_bp.route("/applications", methods=["GET"])
def get_all_applications():

    applications = ApplicationService.get_all_applications()

    result = []

    for application in applications:
        result.append({
            "id": application.id,
            "company": application.company,
            "role": application.role,
            "status": application.status.value,
            "notes": application.notes,
            "user_id": application.user_id
        })

    return jsonify(result), 200


# Get application by ID
@jobs_bp.route("/applications/<int:application_id>", methods=["GET"])
def get_application(application_id):

    try:
        application = ApplicationService.get_application_by_id(
            application_id
        )

        return jsonify({
            "id": application.id,
            "company": application.company,
            "role": application.role,
            "status": application.status.value,
            "notes": application.notes,
            "user_id": application.user_id
        }), 200

    except ApplicationNotFound as e:
        return jsonify({"error": str(e)}), 404


# Update application
@jobs_bp.route("/applications/<int:application_id>", methods=["PUT"])
def update_application(application_id):

    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        if "status" in data:
            data["status"] = ApplicationStatus[data["status"]]

        application = ApplicationService.update_application(
            application_id,
            data
        )

        return jsonify({
            "message": "Application updated successfully!",
            "id": application.id
        }), 200

    except ApplicationNotFound as e:
        return jsonify({"error": str(e)}), 404


# Delete application
@jobs_bp.route("/applications/<int:application_id>", methods=["DELETE"])
def delete_application(application_id):

    try:
        ApplicationService.delete_application(application_id)

        return jsonify({
            "message": "Application deleted successfully!"
        }), 200

    except ApplicationNotFound as e:
        return jsonify({"error": str(e)}), 404