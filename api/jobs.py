from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from marshmallow import ValidationError
from PyPDF2 import PdfReader
import os

from extensions import db
from services.application_service import ApplicationService
from exceptions.application_exceptions import (
    ApplicationNotFound,
    DuplicateApplication
)
from models.job import ApplicationStatus
from schemas.application_schema import (
    CreateApplicationSchema,
    UpdateApplicationSchema
)


# ==========================================
# Blueprint
# ==========================================

jobs_bp = Blueprint("jobs", __name__)


# ==========================================
# Schemas
# ==========================================

create_application_schema = CreateApplicationSchema()
update_application_schema = UpdateApplicationSchema()


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
@jobs_bp.route("/api/applications", methods=["POST"])
@jwt_required()
def create_application():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "error": "No data provided"
            }), 400

        # ==========================================
        # Marshmallow Validation
        # ==========================================

        data = create_application_schema.load(data)

        # ==========================================
        # Convert status string to Enum
        # ==========================================

        if data.get("status"):

            data["status"] = ApplicationStatus[
                data["status"]
            ]

        # ==========================================
        # Logged-in user
        # ==========================================

        user_id = int(
            get_jwt_identity()
        )

        # ==========================================
        # Create application
        # ==========================================

        application = ApplicationService.create_application(
            data,
            user_id
        )

        return jsonify({

            "message":
                "Application created successfully!",

            "application":
                serialize_application(application)

        }), 201

    except ValidationError as e:

        # Return the first Marshmallow validation
        # message in the existing API error format

        error_messages = []

        for field_errors in e.messages.values():
            error_messages.extend(field_errors)

        return jsonify({

            "error":
                error_messages[0]
                if error_messages
                else "Validation Error"

        }), 400

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
# Search + Filter + Sorting + Pagination
# ==========================================

@jobs_bp.route("/applications", methods=["GET"])
@jobs_bp.route("/api/applications", methods=["GET"])
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

        # ==========================================
        # Validate sorting
        # ==========================================

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

        # ==========================================
        # Validate pagination
        # ==========================================

        if page < 1:
            page = 1

        if per_page < 1:
            per_page = 5

        if per_page > 100:
            per_page = 100

        # ==========================================
        # Convert status to Enum
        # ==========================================

        if status:

            try:

                status = ApplicationStatus[
                    status.upper()
                ]

            except KeyError:

                return jsonify({
                    "error": "Invalid status"
                }), 400

        # ==========================================
        # Get applications
        # ==========================================

        pagination = ApplicationService.get_all_applications(

            user_id=user_id,

            search=search,

            status=status,

            sort=sort,

            page=page,

            per_page=per_page

        )

        applications = [

            serialize_application(application)

            for application in pagination.items

        ]

        response = jsonify({

            "applications": applications,

            "pagination": {

                "page": pagination.page,

                "per_page": pagination.per_page,

                "total": pagination.total,

                "pages": pagination.pages,

                "has_next": pagination.has_next,

                "has_prev": pagination.has_prev

            }

        })

        response.headers["X-Total-Count"] = str(pagination.total)
        response.headers["X-Page"] = str(pagination.page)
        response.headers["X-Per-Page"] = str(pagination.per_page)
        response.headers["X-Total-Pages"] = str(pagination.pages)
        response.headers["X-Has-Next"] = str(pagination.has_next).lower()
        response.headers["X-Has-Prev"] = str(pagination.has_prev).lower()

        return response, 200

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ==========================================
# Dashboard Statistics
# GET /dashboard/statistics
# ==========================================

@jobs_bp.route("/applications/stats", methods=["GET"])
@jobs_bp.route("/api/applications/stats", methods=["GET"])
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
@jobs_bp.route(
    "/api/applications/<int:application_id>",
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
    methods=["PUT", "PATCH"]
)
@jobs_bp.route(
    "/api/applications/<int:application_id>",
    methods=["PUT", "PATCH"]
)
@jwt_required()
def update_application(application_id):

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "error": "No data provided"
            }), 400

        # ==========================================
        # Marshmallow Validation
        # ==========================================

        data = update_application_schema.load(data)

        # ==========================================
        # Convert status string to Enum
        # ==========================================

        if data.get("status"):

            data["status"] = ApplicationStatus[
                data["status"]
            ]

        # ==========================================
        # Logged-in user
        # ==========================================

        user_id = int(
            get_jwt_identity()
        )

        # ==========================================
        # Update application
        # ==========================================

        application = ApplicationService.update_application(

            application_id,

            data,

            user_id

        )

        return jsonify({

            "message":
                "Application updated successfully!",

            "application":
                serialize_application(application)

        }), 200

    except ValidationError as e:

        # Return the first Marshmallow validation
        # message in the existing API error format

        error_messages = []

        for field_errors in e.messages.values():
            error_messages.extend(field_errors)

        return jsonify({

            "error":
                error_messages[0]
                if error_messages
                else "Validation Error"

        }), 400

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
@jobs_bp.route(
    "/api/applications/<int:application_id>",
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
@jobs_bp.route(
    "/api/applications/<int:application_id>/resume",
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

        file.save(file_path)

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
@jobs_bp.route(
    "/api/applications/<int:application_id>/resume",
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


# ==========================================
# Extract Resume Text
# GET /applications/<id>/resume/text
# ==========================================

@jobs_bp.route(
    "/applications/<int:application_id>/resume/text",
    methods=["GET"]
)
@jobs_bp.route(
    "/api/applications/<int:application_id>/resume/text",
    methods=["GET"]
)
@jwt_required()
def extract_resume_text(application_id):

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

        reader = PdfReader(
            application.resume_path
        )

        resume_text = ""

        for page in reader.pages:

            text = page.extract_text()

            if text:
                resume_text += text + "\n"

        resume_text = resume_text.strip()

        if not resume_text:

            return jsonify({

                "message":
                    "Resume PDF contains no extractable text",

                "application_id":
                    application_id,

                "resume_text":
                    ""

            }), 200

        return jsonify({

            "message":
                "Resume text extracted successfully!",

            "application_id":
                application_id,

            "resume_text":
                resume_text

        }), 200

    except ApplicationNotFound as e:

        return jsonify({
            "error": str(e)
        }), 404

    except Exception as e:

        return jsonify({

            "error":
                f"Failed to extract resume text: {str(e)}"

        }), 500