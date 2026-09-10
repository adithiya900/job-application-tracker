
from models.job import JobApplication
from models.user import User
from models.token_blocklist import TokenBlocklist
from flask import Flask, jsonify
import json
from dotenv import load_dotenv
import os
import socket
import smtplib
import ssl
from pathlib import Path
from flask_mail import Message

from flask_jwt_extended import get_jwt
from extensions import db, bcrypt, jwt, cache, mail
from flask_migrate import Migrate
from flask_swagger_ui import get_swaggerui_blueprint

# Error Handlers
from errors.handlers import register_error_handlers

# Import Blueprints
from api.jobs import jobs_bp
from api.auth import auth_bp
from api.notifications import notifications_bp
from api.admin import admin_bp
from scheduler.reminder_scheduler import start_scheduler


# =========================
# Load Environment Variables
# =========================
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)


def safe_smtp_diagnostic_output():
    """Print only non-secret SMTP metadata for operators and debugging.

    Never prints client secrets or the SMTP password/key. The helper is
    intentionally written to support provider-agnostic diagnostics.
    """
    print(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
    print(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
    print(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
    print(f"MAIL_USE_SSL: {app.config.get('MAIL_USE_SSL')}")
    print(f"MAIL_USERNAME configured: {bool(app.config.get('MAIL_USERNAME'))}")
    print(f"MAIL_PASSWORD configured: {bool(app.config.get('MAIL_PASSWORD'))}")
    print(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")


def safe_smtp_diagnostic():
    """Diagnose the configured provider-agnostic SMTP flow safely.

    This helper never prints the actual SMTP username or password. It reports
    only safe metadata for DNS, TCP, STARTTLS, and AUTH stages.
    """
    server = os.getenv("MAIL_SERVER") or app.config.get("MAIL_SERVER")
    port = int(os.getenv("MAIL_PORT", app.config.get("MAIL_PORT", 587)))
    use_tls = parse_bool_env(os.getenv("MAIL_USE_TLS"), False)
    use_ssl = parse_bool_env(os.getenv("MAIL_USE_SSL"), False)
    username = os.getenv("MAIL_USERNAME") or app.config.get("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD") or app.config.get("MAIL_PASSWORD")
    sender = os.getenv("MAIL_DEFAULT_SENDER") or app.config.get("MAIL_DEFAULT_SENDER")

    print("SMTP DIAGNOSTIC")
    print(f"MAIL_SERVER: {server}")
    print(f"MAIL_PORT: {port}")
    print(f"MAIL_USE_TLS: {use_tls}")
    print(f"MAIL_USE_SSL: {use_ssl}")
    print(f"MAIL_USERNAME configured: {bool(username)}")
    print(f"MAIL_PASSWORD configured: {bool(password)}")
    print(f"MAIL_DEFAULT_SENDER: {sender}")

    if username:
        print(f"MAIL_USERNAME length: {len(username)}")
        print(f"MAIL_USERNAME strip whitespace: {username != username.strip()}")
        print(f"MAIL_USERNAME quotes/newlines: {bool(username.strip().startswith(('"', "'")) or '\n' in username or '\r' in username)}")
    if password:
        print(f"MAIL_PASSWORD length: {len(password)}")
        print(f"MAIL_PASSWORD strip whitespace: {password != password.strip()}")
        print(f"MAIL_PASSWORD quotes/newlines: {bool(password.strip().startswith(('"', "'")) or '\n' in password or '\r' in password)}")

    print("SMTP DNS resolution:")
    try:
        resolved = socket.gethostbyname(server)
        print(f"DNS_OK: {server} -> {resolved}")
    except Exception as exc:
        print(f"DNS_FAIL: {server} -> {type(exc).__name__}: {str(exc)}")
        return

    print("SMTP TCP connection:")
    try:
        with socket.create_connection((server, port), timeout=5) as sock:
            print(f"TCP_OK: {server}:{port}")
            print("STARTTLS check:")
            try:
                smtp = smtplib.SMTP(host=server, port=port, timeout=5)
                smtp.ehlo()
                if use_tls and not use_ssl:
                    smtp.starttls()
                    smtp.ehlo()
                    print("STARTTLS_OK: TLS handshake reached SMTP server")
                elif use_ssl:
                    print("SSL_MODE: SSL mode requested; Flask-Mail will use SSL socket path")
                else:
                    print("NO_TLS_SSL_MODE: configured for plain SMTP transport")
                print("SMTP AUTH attempt:")
                try:
                    smtp.login(username, password)
                    print("SMTP_AUTH_OK: authentication accepted")
                except smtplib.SMTPAuthenticationError as exc:
                    print("SMTP_AUTH_FAIL: authentication error returned by server")
                    print(f"SMTP_AUTH_SAFE_STATUS: {exc.smtp_code} {exc.smtp_error}")
                except Exception as exc:
                    print(f"SMTP_AUTH_FAIL: {type(exc).__name__}")
                finally:
                    try:
                        smtp.quit()
                    except Exception:
                        pass
            except Exception as exc:
                print(f"STARTTLS_FAIL: {type(exc).__name__}: {str(exc)}")
    except Exception as exc:
        print(f"TCP_FAIL: {server}:{port} -> {type(exc).__name__}: {str(exc)}")


# =========================
# Create Flask App
# =========================
app = Flask(__name__)


@app.after_request
def normalize_error_payload(response):
    """Ensure route, JWT, and HTTP errors share the documented shape."""
    if response.status_code < 400 or not response.is_json:
        return response
    payload = response.get_json(silent=True)
    if not isinstance(payload, dict) or "error" not in payload:
        return response
    normalized = {
        "error": payload["error"],
        "details": payload.get("details", payload.get("message", payload["error"])),
        "status_code": response.status_code,
    }
    response.set_data(json.dumps(normalized))
    response.content_type = "application/json"
    return response


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
# SMTP configuration helpers
# =========================

def parse_bool_env(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "t", "yes", "y")


def validate_smtp_settings(config=None):
    """Validate generic SMTP configuration without assuming a provider.

    Returns True when settings are structurally sound. Raises a clear
    ValueError when the configuration is contradictory or incomplete.
    """
    settings = config if config is not None else app.config

    if settings.get("MAIL_USE_TLS") and settings.get("MAIL_USE_SSL"):
        raise ValueError(
            "MAIL_USE_TLS and MAIL_USE_SSL cannot both be enabled simultaneously. "
            "Choose one transport security mode."
        )

    required = [
        "MAIL_SERVER",
        "MAIL_PORT",
        "MAIL_USERNAME",
        "MAIL_PASSWORD",
        "MAIL_DEFAULT_SENDER",
    ]
    missing = [key for key in required if not settings.get(key)]
    if missing:
        raise ValueError(
            "Missing required SMTP configuration: "
            + ", ".join(missing)
            + ". Configure MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, "
            + "MAIL_PASSWORD, and MAIL_DEFAULT_SENDER through environment variables."
        )

    try:
        port = int(settings.get("MAIL_PORT"))
        if port <= 0:
            raise ValueError("MAIL_PORT must be a positive integer.")
    except (TypeError, ValueError):
        raise ValueError("MAIL_PORT must be an integer SMTP port value.")

    return True


# =========================
# Flask-Mail Configuration
# =========================

app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = parse_bool_env(os.getenv("MAIL_USE_TLS"), False)
app.config["MAIL_USE_SSL"] = parse_bool_env(os.getenv("MAIL_USE_SSL"), False)
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")
app.config["SCHEDULER_ENABLED"] = os.getenv(
    "SCHEDULER_ENABLED",
    "True"
).lower() in ("true", "1", "t")

try:
    # Keep app import safe: warn on invalid or incomplete SMTP config instead
    # of crashing unrelated routes or services during import.
    validate_smtp_settings(app.config)
except ValueError as exc:
    # Do not expose SMTP secrets. Only log safe configuration metadata.
    print(f"SMTP configuration warning: {exc}")


# =========================
# Initialize Extensions
# =========================
db.init_app(app)

bcrypt.init_app(app)

jwt.init_app(app)

cache.init_app(app)

mail.init_app(app)

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

app.register_blueprint(notifications_bp)
app.register_blueprint(admin_bp)

if os.getenv("FLASK_RUN_FROM_CLI") == "true":
    start_scheduler(app)


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
            # CSV Export
            # =========================

            "/applications/export": {

                "get": {

                    "tags": [
                        "Applications / CSV Export"
                    ],

                    "summary":
                        "Export the authenticated user's applications as CSV",

                    "description": (
                        "Downloads all job applications belonging to the "
                        "authenticated user as a CSV file."
                    ),

                    "security": [
                        {
                            "BearerAuth": []
                        }
                    ],

                    "produces": [
                        "text/csv"
                    ],

                    "responses": {

                        "200": {
                            "description":
                                "Applications exported successfully as CSV",
                            "schema": {
                                "type": "string",
                                "format": "binary"
                            },
                            "headers": {
                                "Content-Disposition": {
                                    "type": "string",
                                    "description":
                                        "CSV download filename"
                                }
                            }
                        },

                        "401": {
                            "description":
                                "Unauthorized - JWT token missing or invalid"
                        }

                    }

                }

            },


            # =========================
            # CSV Import
            # =========================

            "/applications/import": {

                "post": {

                    "tags": [
                        "Applications / CSV Import"
                    ],

                    "summary":
                        "Import applications from CSV",

                    "description": (
                        "Uploads a CSV file for the authenticated user. "
                        "Valid rows are imported or updated, while invalid "
                        "rows are skipped and returned in the error summary."
                    ),

                    "security": [
                        {
                            "BearerAuth": []
                        }
                    ],

                    "consumes": [
                        "multipart/form-data"
                    ],

                    "produces": [
                        "application/json"
                    ],

                    "parameters": [

                        {
                            "name": "file",
                            "in": "formData",
                            "required": True,
                            "type": "file",
                            "description":
                                "CSV file containing application rows"
                        }

                    ],

                    "responses": {

                        "200": {
                            "description": (
                                "CSV import completed. The response includes "
                                "imported and failed row counts. Valid rows "
                                "are processed even when other rows fail."
                            ),
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "message": {
                                        "type": "string",
                                        "example": "CSV import completed"
                                    },
                                    "imported": {
                                        "type": "integer",
                                        "example": 3
                                    },
                                    "failed": {
                                        "type": "integer",
                                        "example": 1
                                    },
                                    "errors": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "row": {
                                                    "type": "integer"
                                                },
                                                "error": {
                                                    "type": "string"
                                                },
                                                "data": {
                                                    "type": "object"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },

                        "400": {
                            "description": (
                                "Validation error, missing CSV file, invalid "
                                "file type, or invalid CSV headers"
                            )
                        },

                        "401": {
                            "description":
                                "Unauthorized - JWT token missing or invalid"
                        },

                        "500": {
                            "description":
                                "CSV import failed unexpectedly"
                        }

                    }

                }

            },


            # =========================
            # CSV Import Error Log
            # =========================

            "/applications/import/errors": {

                "get": {

                    "tags": [
                        "Applications / CSV Import"
                    ],

                    "summary":
                        "Download CSV import error log",

                    "description": (
                        "Downloads the failed CSV import rows and their "
                        "validation messages for the authenticated user."
                    ),

                    "security": [
                        {
                            "BearerAuth": []
                        }
                    ],

                    "produces": [
                        "text/csv"
                    ],

                    "responses": {

                        "200": {
                            "description":
                                "CSV import error log downloaded successfully",
                            "schema": {
                                "type": "string",
                                "format": "binary"
                            },
                            "headers": {
                                "Content-Disposition": {
                                    "type": "string",
                                    "description":
                                        "CSV error-log download filename"
                                }
                            }
                        },

                        "401": {
                            "description":
                                "Unauthorized - JWT token missing or invalid"
                        }

                    }

                }

            },


            # =========================
            # Bulk Status Update
            # =========================

            "/applications/bulk-status": {

                "post": {

                    "tags": [
                        "Applications / Bulk Status Update"
                    ],

                    "summary":
                        "Bulk update application statuses",

                    "description": (
                        "Updates the status of applications owned by the "
                        "authenticated user. Missing or foreign application "
                        "IDs are reported as per-ID errors while valid IDs "
                        "continue to update."
                    ),

                    "security": [
                        {
                            "BearerAuth": []
                        }
                    ],

                    "consumes": [
                        "application/json"
                    ],

                    "produces": [
                        "application/json"
                    ],

                    "parameters": [

                        {
                            "name": "body",
                            "in": "body",
                            "required": True,
                            "schema": {
                                "type": "object",
                                "required": [
                                    "application_ids",
                                    "status"
                                ],
                                "properties": {
                                    "application_ids": {
                                        "type": "array",
                                        "minItems": 1,
                                        "items": {
                                            "type": "integer",
                                            "minimum": 1
                                        },
                                        "example": [1, 2, 3]
                                    },
                                    "status": {
                                        "type": "string",
                                        "enum": [
                                            "APPLIED",
                                            "PHONE_SCREEN",
                                            "INTERVIEW",
                                            "OFFER",
                                            "REJECTED"
                                        ],
                                        "example": "INTERVIEW"
                                    }
                                }
                            }
                        }

                    ],

                    "responses": {

                        "200": {
                            "description": (
                                "Bulk status update completed. Valid owned "
                                "IDs are updated and invalid or foreign IDs "
                                "are reported in errors."
                            ),
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "message": {
                                        "type": "string",
                                        "example": "Bulk status update completed"
                                    },
                                    "updated": {
                                        "type": "integer",
                                        "example": 2
                                    },
                                    "updated_ids": {
                                        "type": "array",
                                        "items": {
                                            "type": "integer"
                                        },
                                        "example": [1, 2]
                                    },
                                    "failed": {
                                        "type": "integer",
                                        "example": 1
                                    },
                                    "errors": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "id": {
                                                    "type": "integer"
                                                },
                                                "error": {
                                                    "type": "string"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },

                        "400": {
                            "description": (
                                "Invalid request body, application IDs, or "
                                "status value"
                            )
                        },

                        "401": {
                            "description":
                                "Unauthorized - JWT token missing or invalid"
                        },

                        "500": {
                            "description":
                                "Bulk status update failed unexpectedly"
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
# Run Application
# =========================

if __name__ == "__main__":

    start_scheduler(app)

    # Safe Mail Configuration Debug Output
    print("=" * 40)
    print("Email Configuration Status:")
    print(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
    print(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
    print(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
    print(f"MAIL_USE_SSL: {app.config.get('MAIL_USE_SSL')}")
    print(f"MAIL_USERNAME configured: {bool(app.config.get('MAIL_USERNAME'))}")
    print(f"MAIL_PASSWORD configured: {bool(app.config.get('MAIL_PASSWORD'))}")
    print(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
    print("=" * 40)

    app.run(debug=True)
