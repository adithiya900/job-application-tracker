from flask import Flask, jsonify
from dotenv import load_dotenv
import os

from extensions import db, bcrypt, jwt
from flask_migrate import Migrate
from flask_swagger_ui import get_swaggerui_blueprint

# Error Handlers
from errors.handlers import register_error_handlers

# Import models
from models.job import JobApplication
from models.user import User

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
# Initialize Extensions
# =========================
db.init_app(app)

bcrypt.init_app(app)

jwt.init_app(app)

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
                                "Invalid input"
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
                                "Login successful"
                        },

                        "401": {
                            "description":
                                "Invalid credentials"
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
                                "Applications retrieved successfully"
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

                        "404": {
                            "description":
                                "Application not found"
                        },

                        "401": {
                            "description":
                                "Unauthorized"
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

                        "404": {
                            "description":
                                "Application not found"
                        },

                        "401": {
                            "description":
                                "Unauthorized"
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

                        "404": {
                            "description":
                                "Application not found"
                        },

                        "401": {
                            "description":
                                "Unauthorized"
                        }

                    }

                }

            },


            # =========================
            # Resume Upload & Download
            # =========================

            "/applications/{application_id}/resume": {

                # Upload Resume
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


                # Download Resume
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

            }

        },


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