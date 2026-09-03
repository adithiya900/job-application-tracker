from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os

from extensions import db
from services.application_service import ApplicationService
from exceptions.application_exceptions import (
    ApplicationNotFound,
    DuplicateApplication
)
from models.job import ApplicationStatus


# ==========================================
# Blueprint
# ==========================================

jobs_bp = Blueprint("jobs", __name__)


# ==========================================
# Helper Function
# ==========================================

def serialize_application(application):

    return {
        "id": application.id,
        "company": application.company,
        "role": application.role,
        "status": application.status.value,
        "applied_date": (
            application.applied_date.isoformat()
            if application.applied_date
            else None
        ),
        "notes": application.notes,
        "user_id": application.user_id,
        "resume_path": application.resume_path
    }


# ==========================================
# Create Application
# POST /applications
# ==========================================

@jobs_bp.route("/applications", methods=["POST"])
@jwt_required()
def create_application():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "error": "No data provided"
            }), 400


        if not data.get("company"):

            return jsonify({
                "error": "Company is required"
            }), 400


        if not data.get("role"):

            return jsonify({
                "error": "Role is required"
            }), 400


        user_id = int(
            get_jwt_identity()
        )


        if data.get("status"):

            try:

                data["status"] = ApplicationStatus[
                    data["status"].upper()
                ]

            except KeyError:

                return jsonify({
                    "error": "Invalid status"
                }), 400


        application = (
            ApplicationService.create_application(
                data,
                user_id
            )
        )


        return jsonify({

            "message":
                "Application created successfully!",

            "application":
                serialize_application(application)

        }), 201


    except DuplicateApplication as e:

        return jsonify({
            "error": str(e)
        }), 409


    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ==========================================
# Get All Applications
# GET /applications
# ==========================================

@jobs_bp.route("/applications", methods=["GET"])
@jwt_required()
def get_all_applications():

    try:

        user_id = int(
            get_jwt_identity()
        )


        search = request.args.get("search")

        status = request.args.get("status")

        sort = request.args.get(
            "sort",
            "newest"
        ).lower()


        page = request.args.get(
            "page",
            1,
            type=int
        )

        per_page = request.args.get(
            "per_page",
            5,
            type=int
        )


        allowed_sorts = [
            "newest",
            "oldest",
            "company"
        ]


        if sort not in allowed_sorts:

            return jsonify({

                "error": (
                    "Invalid sort value. "
                    "Use newest, oldest, or company"
                )

            }), 400


        if page < 1:
            page = 1


        if per_page < 1:
            per_page = 5


        if per_page > 100:
            per_page = 100


        if status:

            try:

                status = ApplicationStatus[
                    status.upper()
                ]

            except KeyError:

                return jsonify({
                    "error": "Invalid status"
                }), 400


        pagination = (
            ApplicationService.get_all_applications(

                user_id=user_id,

                search=search,

                status=status,

                sort=sort,

                page=page,

                per_page=per_page

            )
        )


        applications = [

            serialize_application(application)

            for application in pagination.items

        ]


        return jsonify({

            "applications": applications,

            "pagination": {

                "page": pagination.page,

                "per_page": pagination.per_page,

                "total": pagination.total,

                "pages": pagination.pages,

                "has_next": pagination.has_next,

                "has_prev": pagination.has_prev

            }

        }), 200


    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ==========================================
# Dashboard Statistics
# GET /dashboard/statistics
# ==========================================

@jobs_bp.route(
    "/dashboard/statistics",
    methods=["GET"]
)
@jwt_required()
def get_dashboard_statistics():

    try:

        user_id = int(
            get_jwt_identity()
        )


        statistics = (
            ApplicationService.get_dashboard_statistics(
                user_id
            )
        )


        return jsonify(
            statistics
        ), 200


    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ==========================================
# Get Application By ID
# GET /applications/<id>
# ==========================================

@jobs_bp.route(
    "/applications/<int:application_id>",
    methods=["GET"]
)
@jwt_required()
def get_application(application_id):

    try:

        user_id = int(
            get_jwt_identity()
        )


        application = (
            ApplicationService.get_application_by_id(

                application_id,

                user_id

            )
        )


        return jsonify(

            serialize_application(application)

        ), 200


    except ApplicationNotFound as e:

        return jsonify({
            "error": str(e)
        }), 404


    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ==========================================
# Update Application
# PUT /applications/<id>
# ==========================================

@jobs_bp.route(
    "/applications/<int:application_id>",
    methods=["PUT"]
)
@jwt_required()
def update_application(application_id):

    try:

        data = request.get_json()


        if not data:

            return jsonify({
                "error": "No data provided"
            }), 400


        user_id = int(
            get_jwt_identity()
        )


        if data.get("status"):

            try:

                data["status"] = (
                    ApplicationStatus[
                        data["status"].upper()
                    ]
                )

            except KeyError:

                return jsonify({
                    "error": "Invalid status"
                }), 400


        application = (
            ApplicationService.update_application(

                application_id,

                data,

                user_id

            )
        )


        return jsonify({

            "message":
                "Application updated successfully!",

            "application":
                serialize_application(application)

        }), 200


    except ApplicationNotFound as e:

        return jsonify({
            "error": str(e)
        }), 404


    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ==========================================
# Delete Application
# DELETE /applications/<id>
# ==========================================

@jobs_bp.route(
    "/applications/<int:application_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_application(application_id):

    try:

        user_id = int(
            get_jwt_identity()
        )


        ApplicationService.delete_application(

            application_id,

            user_id

        )


        return jsonify({

            "message":
                "Application deleted successfully!"

        }), 200


    except ApplicationNotFound as e:

        return jsonify({
            "error": str(e)
        }), 404


    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ==========================================
# Upload Resume
# POST /applications/<id>/resume
# ==========================================

@jobs_bp.route(
    "/applications/<int:application_id>/resume",
    methods=["POST"]
)
@jwt_required()
def upload_resume(application_id):

    try:

        user_id = int(
            get_jwt_identity()
        )


        if "resume" not in request.files:

            return jsonify({
                "error": "Resume file is required"
            }), 400


        file = request.files["resume"]


        if file.filename == "":

            return jsonify({
                "error": "No file selected"
            }), 400


        if not file.filename.lower().endswith(".pdf"):

            return jsonify({
                "error": "Only PDF files are allowed"
            }), 400


        application = (
            ApplicationService.get_application_by_id(
                application_id,
                user_id
            )
        )


        upload_folder = "uploads"


        os.makedirs(
            upload_folder,
            exist_ok=True
        )


        original_filename = secure_filename(
            file.filename
        )


        filename = (
            f"{application_id}_{original_filename}"
        )


        file_path = os.path.join(
            upload_folder,
            filename
        )


        file.save(
            file_path
        )


        application.resume_path = file_path

        db.session.commit()


        return jsonify({

            "message":
                "Resume uploaded successfully!",

            "resume_path":
                file_path

        }), 200


    except ApplicationNotFound as e:

        return jsonify({
            "error": str(e)
        }), 404


    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ==========================================
# Download Resume
# GET /applications/<id>/resume
# ==========================================

@jobs_bp.route(
    "/applications/<int:application_id>/resume",
    methods=["GET"]
)
@jwt_required()
def download_resume(application_id):

    try:

        user_id = int(
            get_jwt_identity()
        )


        application = (
            ApplicationService.get_application_by_id(
                application_id,
                user_id
            )
        )


        if not application.resume_path:

            return jsonify({
                "error":
                    "No resume uploaded for this application"
            }), 404


        if not os.path.exists(
            application.resume_path
        ):

            return jsonify({
                "error":
                    "Resume file not found"
            }), 404


        return send_file(

            application.resume_path,

            as_attachment=True

        )


    except ApplicationNotFound as e:

        return jsonify({
            "error": str(e)
        }), 404


    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500