from models.job import JobApplication
from models.user import User
from models.token_blocklist import TokenBlocklist
from flask import Flask, jsonify
from dotenv import load_dotenv
import os

from flask_jwt_extended import get_jwt
from extensions import db, bcrypt, jwt, cache
from flask_migrate import Migrate
from flask_swagger_ui import get_swaggerui_blueprint

# Error Handlers
from errors.handlers import register_error_handlers

# Import Blueprints
from api.jobs import jobs_bp
from api.auth import auth_bp


# =========================
# Load Environment Variables
# =========================
load_dotenv()


# =========================
# Create Flask App
# =========================
app = Flask(__name__)


# =========================
# Database Configuration
# =========================
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# =========================
# JWT Configuration
# =========================
app.config["JWT_SECRET_KEY"] = os.getenv(
    "JWT_SECRET_KEY"
)


# =========================
# Flask-Caching Configuration
# =========================

app.config["CACHE_TYPE"] = "RedisCache"
app.config["CACHE_REDIS_URL"] = os.getenv(
    "REDIS_URL", "redis://localhost:6379/0"
)
app.config["CACHE_DEFAULT_TIMEOUT"] = 1800


# =========================
# Adzuna Configuration
# =========================

app.config["ADZUNA_APP_ID"] = os.getenv("ADZUNA_APP_ID")
app.config["ADZUNA_APP_KEY"] = os.getenv("ADZUNA_APP_KEY")
app.config["ADZUNA_COUNTRY"] = os.getenv("ADZUNA_COUNTRY", "in")


# =========================
# Initialize Extensions
# =========================
db.init_app(app)

bcrypt.init_app(app)

jwt.init_app(app)

cache.init_app(app)

migrate = Migrate(app, db)


# =========================
# JWT Custom Error Handlers
# =========================

@jwt.unauthorized_loader
def missing_token_callback(reason):

    return jsonify({
        "error": "Unauthorized",
        "message": "Authorization token is missing"
    }), 401


@jwt.invalid_token_loader
def invalid_token_callback(reason):

    return jsonify({
        "error": "Unauthorized",
        "message": "Invalid authentication token"
    }), 401


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):

    return jsonify({
        "error": "Unauthorized",
        "message": "Authentication token has expired"
    }), 401

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):

    jti = jwt_payload["jti"]

    token = TokenBlocklist.query.filter_by(
        jti=jti
    ).first()

    return token is not None


@jwt.needs_fresh_token_loader
def fresh_token_required_callback(jwt_header, jwt_payload):

    return jsonify({
        "error": "Unauthorized",
        "message": "Fresh authentication token required"
    }), 401


@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):

    return jsonify({
        "error": "Unauthorized",
        "message": "Authentication token has been revoked"
    }), 401


# =========================
# Register Error Handlers
# =========================
register_error_handlers(app)


# =========================
# Register API Blueprints
# =========================

app.register_blueprint(jobs_bp)

app.register_blueprint(auth_bp)


# =========================
# Swagger Configuration
# =========================

SWAGGER_URL = "/swagger"
API_URL = "/swagger.json"


swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        "app_name": "Job Application Tracker API"
    }
)


app.register_blueprint(
    swaggerui_blueprint,
    url_prefix=SWAGGER_URL
)


# =========================
# Swagger JSON Documentation
# =========================

# =========================
# Swagger JSON Documentation
# =========================

@app.route("/swagger.json")
def swagger_json():

    swagger_data = {

        "swagger": "2.0",

        "info": {
            "title": "Job Application Tracker API",
            "description": (
                "API documentation for the "
                "Job Application Tracker backend."
            ),
            "version": "1.0.0"
        },

        "basePath": "/",

        "schemes": [
            "http"
        ],

        # =========================
        # JWT Authorization
        # =========================

        "securityDefinitions": {

            "BearerAuth": {

                "type": "apiKey",

                "name": "Authorization",

                "in": "header",

                "description": (
                    "Enter your JWT token like this: "
                    "Bearer <your_token>"
                )

            }

        },

        "paths": {

            # =========================
            # Register
            # =========================

            "/register": {

                "post": {

                    "tags": [
                        "Authentication"
                    ],

                    "summary": "Register a new user",

                    "parameters": [

                        {
                            "name": "body",
                            "in": "body",
                            "required": True,

                            "schema": {

                                "type": "object",

                                "required": [
                                    "name",
                                    "email",
                                    "password"
                                ],

                                "properties": {

                                    "name": {
                                        "type": "string",
                                        "example": "Adithiya"
                                    },

                                    "email": {
                                        "type": "string",
                                        "example": "adithiya@email.com"
                                    },

                                    "password": {
                                        "type": "string",
                                        "example": "password123"
                                    }

                                }

                            }

                        }

                    ],

                    "responses": {

                        "201": {
                            "description":
                                "User registered successfully"
                        },

                        "400": {
                            "description":
                                "Name, email and password are required"
                        },

                        "409": {
                            "description":
                                "Email already registered"
                        }

                    }

                }

            },


            # =========================
            # Login
            # =========================

            "/login": {

                "post": {

                    "tags": [
                        "Authentication"
                    ],

                    "summary": "Login user",

                    "parameters": [

                        {
                            "name": "body",
                            "in": "body",
                            "required": True,

                            "schema": {

                                "type": "object",

                                "required": [
                                    "email",
                                    "password"
                                ],

                                "properties": {

                                    "email": {
                                        "type": "string",
                                        "example":
                                            "adithiya@email.com"
                                    },

                                    "password": {
                                        "type": "string",
                                        "example":
                                            "password123"
                                    }

                                }

                            }

                        }

                    ],

                    "responses": {

                        "200": {
                            "description":
                                "Login successful. Access and refresh tokens are returned."
                        },

                        "400": {
                            "description":
                                "Email and password are required"
                        },

                        "401": {
                            "description":
                                "Invalid email or password"
                        }

                    }

                }

            },


            # =========================
            # Refresh Access Token
            # =========================

            "/refresh": {

                "post": {

                    "tags": [
                        "Authentication"
                    ],

                    "summary":
                        "Refresh access token",

                    "description": (
                        "Generate a new access token using a valid "
                        "refresh token. Enter the refresh token "
                        "in the Authorization header as: "
                        "Bearer <refresh_token>"
                    ),

                    "security": [
                        {
                            "BearerAuth": []
                        }
                    ],

                    "responses": {

                        "200": {
                            "description":
                                "Access token refreshed successfully"
                        },

                        "401": {
                            "description":
                                "Refresh token missing, invalid, expired, or revoked"
                        }

                    }

                }

            },


            # =========================
            # Logout
            # =========================

            "/logout": {

                "post": {

                    "tags": [
                        "Authentication"
                    ],

                    "summary":
                        "Logout user",

                    "description": (
                        "Revoke the current access token and "
                        "logout the user. Enter the access token "
                        "in the Authorization header as: "
                        "Bearer <access_token>"
                    ),

                    "security": [
                        {
                            "BearerAuth": []
                        }
                    ],

                    "responses": {

                        "200": {
                            "description":
                                "Logout successful! Token revoked."
                        },

                        "401": {
                            "description":
                                "Authorization token is missing, invalid, expired, or revoked"
                        }

                    }

                }

            },


            # =========================
            # Applications
            # =========================

            "/applications": {

                "get": {

                    "tags": [
                        "Applications"
                    ],

                    "summary":
                        "Get all applications",

                    "security": [
                        {
                            "BearerAuth": []
                        }
                    ],

                    "parameters": [

                        {
                            "name": "search",
                            "in": "query",
                            "type": "string",
                            "description":
                                "Search company or role"
                        },

                        {
                            "name": "status",
                            "in": "query",
                            "type": "string",
                            "description":
                                "Application status"
                        },

                        {
                            "name": "sort",
                            "in": "query",
                            "type": "string",
                            "default": "newest"
                        },

                        {
                            "name": "page",
                            "in": "query",
                            "type": "integer",
                            "default": 1
                        },

                        {
                            "name": "per_page",
                            "in": "query",
                            "type": "integer",
                            "default": 5
                        }

                    ],

                    "responses": {

                        "200": {
                            "description":
                                "Applications retrieved successfully",
                            "headers": {
                                "X-Total-Count": {
                                    "type": "integer",
                                    "description": "Total number of applications matching query"
                                },
                                "X-Page": {
                                    "type": "integer",
                                    "description": "Current page number"
                                },
                                "X-Per-Page": {
                                    "type": "integer",
                                    "description": "Number of applications per page"
                                },
                                "X-Total-Pages": {
                                    "type": "integer",
                                    "description": "Total number of pages"
                                },
                                "X-Has-Next": {
                                    "type": "string",
                                    "description": "Whether a next page exists (true/false)"
                                },
                                "X-Has-Prev": {
                                    "type": "string",
                                    "description": "Whether a previous page exists (true/false)"
                                }
                            }
                        },

                        "401": {
                            "description":
                                "Unauthorized"
                        }

                    }

                },


                "post": {

                    "tags": [
                        "Applications"
                    ],

                    "summary":
                        "Create a new job application",

                    "security": [
                        {
                            "BearerAuth": []
                        }
                    ],

                    "parameters": [

                        {
                            "name": "body",
                            "in": "body",
                            "required": True,

                            "schema": {

                                "type": "object",

                                "required": [
                                    "company",
                                    "role"
                                ],

                                "properties": {

                                    "company": {
                                        "type": "string",
                                        "example": "Google"
                                    },

                                    "role": {
                                        "type": "string",
                                        "example":
                                            "Software Engineer"
                                    },

                                    "status": {
                                        "type": "string",
                                        "example": "APPLIED"
                                    },

                                    "notes": {
                                        "type": "string",
                                        "example":
                                            "Applied through careers page"
                                    }

                                }

                            }

                        }

                    ],

                    "responses": {

                        "201": {
                            "description":
                                "Application created successfully"
                        },

                        "400": {
                            "description":
                                "Invalid input"
                        },

                        "401": {
                            "description":
                                "Unauthorized"
                        },

                        "409": {
                            "description":
                                "Duplicate application"
                        }

                    }

                }

            },


            # =========================
            # Application By ID
            # =========================

            "/applications/{application_id}": {

                "get": {

                    "tags": [
                        "Applications"
                    ],

                    "summary":
                        "Get application by ID",

                    "security": [
                        {
                            "BearerAuth": []
                        }
                    ],

                    "parameters": [

                        {
                            "name":
                                "application_id",

                            "in": "path",

                            "required": True,

                            "type": "integer"

                        }

                    ],

                    "responses": {

                        "200": {
                            "description":
                                "Application found"
                        },

                        "401": {
                            "description":
                                "Unauthorized"
                        },

                        "404": {
                            "description":
                                "Application not found"
                        }

                    }

                },


                "put": {

                    "tags": [
                        "Applications"
                    ],

                    "summary":
                        "Update application",

                    "security": [
                        {
                            "BearerAuth": []
                        }
                    ],

                    "parameters": [

                        {
                            "name":
                                "application_id",

                            "in": "path",

                            "required": True,

                            "type": "integer"

                        },

                        {
                            "name": "body",

                            "in": "body",

                            "required": True,

                            "schema": {

                                "type": "object",

                                "properties": {

                                    "company": {
                                        "type": "string"
                                    },

                                    "role": {
                                        "type": "string"
                                    },

                                    "status": {
                                        "type": "string",
                                        "example":
                                            "INTERVIEW"
                                    },

                                    "notes": {
                                        "type": "string"
                                    }

                                }

                            }

                        }

                    ],

                    "responses": {

                        "200": {
                            "description":
                                "Application updated successfully"
                        },

                        "401": {
                            "description":
                                "Unauthorized"
                        },

                        "404": {
                            "description":
                                "Application not found"
                        }

                    }

                },


                "patch": {

                    "tags": [
                        "Applications"
                    ],

                    "summary":
                        "Partially update application",

                    "description":
                        "Partially update one or more fields of an existing application. Fields not included remain unchanged. Also available at /api/applications/{application_id}.",

                    "security": [
                        {
                            "BearerAuth": []
                        }
                    ],

                    "parameters": [

                        {
                            "name":
                                "application_id",

                            "in": "path",

                            "required": True,

                            "type": "integer"

                        },

                        {
                            "name": "body",

                            "in": "body",

                            "required": True,

                            "schema": {

                                "type": "object",

                                "properties": {

                                    "company": {
                                        "type": "string",
                                        "example": "Google"
                                    },

                                    "role": {
                                        "type": "string",
                                        "example": "Senior Software Engineer"
                                    },

                                    "status": {
                                        "type": "string",
                                        "example": "INTERVIEW"
                                    },

                                    "notes": {
                                        "type": "string",
                                        "example": "Round 1 passed"
                                    },

                                    "applied_date": {
                                        "type": "string",
                                        "format": "date",
                                        "example": "2026-09-04"
                                    }

                                }

                            }

                        }

                    ],

                    "responses": {

                        "200": {
                            "description":
                                "Application updated successfully"
                        },

                        "400": {
                            "description":
                                "Validation Error / Invalid input"
                        },

                        "401": {
                            "description":
                                "Unauthorized"
                        },

                        "404": {
                            "description":
                                "Application not found"
                        }

                    }

                },


                "delete": {

                    "tags": [
                        "Applications"
                    ],

                    "summary":
                        "Delete application",

                    "security": [
                        {
                            "BearerAuth": []
                        }
                    ],

                    "parameters": [

                        {
                            "name":
                                "application_id",

                            "in": "path",

                            "required": True,

                            "type": "integer"

                        }

                    ],

                    "responses": {

                        "200": {
                            "description":
                                "Application deleted successfully"
                        },

                        "401": {
                            "description":
                                "Unauthorized"
                        },

                        "404": {
                            "description":
                                "Application not found"
                        }

                    }

                }

            },


            # =========================
            # Resume Upload & Download
            # =========================

            "/applications/{application_id}/resume": {

                "post": {

                    "tags": [
                        "Resume"
                    ],

                    "summary":
                        "Upload resume for an application",

                    "consumes": [
                        "multipart/form-data"
                    ],

                    "security": [
                        {
                            "BearerAuth": []
                        }
                    ],

                    "parameters": [

                        {
                            "name":
                                "application_id",

                            "in": "path",

                            "required": True,

                            "type": "integer",

                            "description":
                                "Application ID"
                        },

                        {
                            "name": "resume",

                            "in": "formData",

                            "required": True,

                            "type": "file",

                            "description":
                                "Upload PDF resume"
                        }

                    ],

                    "responses": {

                        "200": {
                            "description":
                                "Resume uploaded successfully"
                        },

                        "400": {
                            "description":
                                "Invalid or missing resume file"
                        },

                        "401": {
                            "description":
                                "Unauthorized"
                        },

                        "404": {
                            "description":
                                "Application not found"
                        }

                    }

                },


                "get": {

                    "tags": [
                        "Resume"
                    ],

                    "summary":
                        "Download application resume",

                    "security": [
                        {
                            "BearerAuth": []
                        }
                    ],

                    "parameters": [

                        {
                            "name":
                                "application_id",

                            "in": "path",

                            "required": True,

                            "type": "integer",

                            "description":
                                "Application ID"
                        }

                    ],

                    "produces": [
                        "application/pdf"
                    ],

                    "responses": {

                        "200": {
                            "description":
                                "Resume downloaded successfully"
                        },

                        "401": {
                            "description":
                                "Unauthorized"
                        },

                        "404": {
                            "description":
                                "Resume or application not found"
                        }

                    }

                }

            },


            # =========================
            # Resume Text Extraction
            # =========================

            "/applications/{application_id}/resume/text": {

                "get": {

                    "tags": [
                        "Resume"
                    ],

                    "summary":
                        "Extract text from application resume",

                    "security": [
                        {
                            "BearerAuth": []
                        }
                    ],

                    "parameters": [

                        {
                            "name":
                                "application_id",

                            "in": "path",

                            "required": True,

                            "type": "integer",

                            "description":
                                "Application ID"
                        }

                    ],

                    "produces": [
                        "application/json"
                    ],

                    "responses": {

                        "200": {
                            "description":
                                "Resume text extracted successfully"
                        },

                        "401": {
                            "description":
                                "Unauthorized"
                        },

                        "404": {
                            "description":
                                "Resume or application not found"
                        }

                    }

                }

            },


            # =========================
            # Applications Statistics
            # =========================

            "/applications/stats": {

                "get": {

                    "tags": [
                        "Applications"
                    ],

                    "summary":
                        "Get application statistics (counts by status)",

                    "description":
                        "Returns total applications and counts broken down by status. Also available at /api/applications/stats.",

                    "security": [
                        {
                            "BearerAuth": []
                        }
                    ],

                    "responses": {

                        "200": {
                            "description":
                                "Application statistics retrieved successfully"
                        },

                        "401": {
                            "description":
                                "Unauthorized"
                        }

                    }

                }

            },


            # =========================
            # Dashboard Statistics
            # =========================

            "/dashboard/statistics": {

                "get": {

                    "tags": [
                        "Dashboard"
                    ],

                    "summary":
                        "Get dashboard statistics",

                    "security": [
                        {
                            "BearerAuth": []
                        }
                    ],

                    "responses": {

                        "200": {
                            "description":
                                "Statistics retrieved successfully"
                        },

                        "401": {
                            "description":
                                "Unauthorized"
                        }

                    }

                }

            },


            # =========================
            # Job Search (Day 9)
            # =========================

            "/api/jobs/search": {

                "get": {

                    "tags": [
                        "Job Search"
                    ],

                    "summary":
                        "Search external jobs via Adzuna API",

                    "description": (
                        "Search for jobs using the Adzuna API. "
                        "Results are cached in Redis for 30 minutes. "
                        "Requires JWT authentication."
                    ),

                    "security": [
                        {
                            "BearerAuth": []
                        }
                    ],

                    "parameters": [
                        {
                            "name": "q",
                            "in": "query",
                            "required": True,
                            "description": "Job search query (e.g. python, data engineer)",
                            "schema": {
                                "type": "string",
                                "example": "python"
                            }
                        },
                        {
                            "name": "location",
                            "in": "query",
                            "required": False,
                            "description": "Location filter (e.g. chennai, bangalore)",
                            "schema": {
                                "type": "string",
                                "example": "chennai"
                            }
                        },
                        {
                            "name": "page",
                            "in": "query",
                            "required": False,
                            "description": "Page number (default: 1)",
                            "schema": {
                                "type": "integer",
                                "default": 1
                            }
                        },
                        {
                            "name": "per_page",
                            "in": "query",
                            "required": False,
                            "description": "Results per page (default: 5, max: 50)",
                            "schema": {
                                "type": "integer",
                                "default": 5
                            }
                        }
                    ],

                    "responses": {

                        "200": {
                            "description": "Jobs retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "query": {"type": "string"},
                                            "location": {"type": "string"},
                                            "count": {"type": "integer"},
                                            "cached": {"type": "boolean"},
                                            "source": {"type": "string", "enum": ["cache", "api"]},
                                            "jobs": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "title": {"type": "string"},
                                                        "company": {"type": "string"},
                                                        "location": {"type": "string"},
                                                        "salary_min": {"type": "number"},
                                                        "salary_max": {"type": "number"},
                                                        "salary_range": {"type": "string"},
                                                        "description": {"type": "string"},
                                                        "redirect_url": {"type": "string"},
                                                        "created": {"type": "string"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },

                        "400": {
                            "description":
                                "Bad request - missing required parameter q"
                        },

                        "401": {
                            "description":
                                "Unauthorized - JWT token missing or invalid"
                        },

                        "502": {
                            "description":
                                "Bad Gateway - Adzuna API returned an error"
                        },

                        "503": {
                            "description":
                                "Service Unavailable - Adzuna credentials not configured"
                        }

                    }

                }

            }

        }

    }

    return jsonify(swagger_data)


# =========================
# Home Route
# =========================

@app.route("/")
def home():

    return jsonify({
        "message": "Job Application Tracker API is running!"
    }), 200


# =========================
# Database Test Route
# =========================

@app.route("/test-db")
def test_db():

    try:

        db.session.execute(
            db.text("SELECT 1")
        )

        return jsonify({
            "message": "Database connected successfully!"
        }), 200

    except Exception:

        return jsonify({
            "error": "Database connection failed"
        }), 500


# =========================
# Check User
# =========================

@app.route("/check-user/<int:user_id>")
def check_user(user_id):

    user = db.session.get(
        User,
        user_id
    )

    if user:

        return jsonify({
            "id": user.id,
            "name": user.name,
            "email": user.email
        }), 200

    return jsonify({
        "error": "User not found"
    }), 404


# =========================
# Run Application
# =========================

if __name__ == "__main__":

    app.run(debug=True)