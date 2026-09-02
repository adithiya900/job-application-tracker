from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

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
        "user_id": application.user_id
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


        # Validate company
        if not data.get("company"):
            return jsonify({
                "error": "Company is required"
            }), 400


        # Validate role
        if not data.get("role"):
            return jsonify({
                "error": "Role is required"
            }), 400


        # Get logged-in user ID
        user_id = int(get_jwt_identity())


        # Convert status string to Enum
        if data.get("status"):

            try:

                data["status"] = ApplicationStatus[
                    data["status"].upper()
                ]

            except KeyError:

                return jsonify({
                    "error": "Invalid status"
                }), 400


        # Create application
        application = ApplicationService.create_application(
            data,
            user_id
        )


        return jsonify({

            "message": "Application created successfully!",

            "application": serialize_application(
                application
            )

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
# Search + Filter + Sorting + Pagination
# ==========================================

@jobs_bp.route("/applications", methods=["GET"])
@jwt_required()
def get_all_applications():

    try:

        # Logged-in user
        user_id = int(get_jwt_identity())


        # ==========================================
        # Query Parameters
        # ==========================================

        search = request.args.get("search")

        status = request.args.get("status")

        sort = request.args.get(
            "sort",
            "newest"
        ).lower()


        # ==========================================
        # Pagination
        # ==========================================

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
        # Validate Sorting
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
        # Validate Pagination
        # ==========================================

        if page < 1:
            page = 1


        if per_page < 1:
            per_page = 5


        if per_page > 100:
            per_page = 100


        # ==========================================
        # Convert Status to Enum
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
        # Get Applications
        # ==========================================

        pagination = ApplicationService.get_all_applications(

            user_id=user_id,

            search=search,

            status=status,

            sort=sort,

            page=page,

            per_page=per_page
        )


        # ==========================================
        # Serialize Applications
        # ==========================================

        applications = [

            serialize_application(application)

            for application in pagination.items

        ]


        # ==========================================
        # Response
        # ==========================================

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

        user_id = int(get_jwt_identity())


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

        user_id = int(get_jwt_identity())


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


        # Validate data
        if not data:

            return jsonify({
                "error": "No data provided"
            }), 400


        # Logged-in user
        user_id = int(
            get_jwt_identity()
        )


        # ==========================================
        # Convert Status String to Enum
        # ==========================================

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


        # ==========================================
        # Update Application
        # ==========================================

        application = (
            ApplicationService.update_application(

                application_id,

                data,

                user_id

            )
        )


        return jsonify({

            "message": (
                "Application updated successfully!"
            ),

            "application": serialize_application(
                application
            )

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

            "message": (
                "Application deleted successfully!"
            )

        }), 200


    except ApplicationNotFound as e:

        return jsonify({
            "error": str(e)
        }), 404


    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500