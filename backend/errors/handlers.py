from flask import jsonify


def error_response(error, status_code, details=None):
    """Return the documented error payload used by every API failure."""
    return jsonify({
        "error": error,
        "details": details if details is not None else error,
        "status_code": status_code,
    }), status_code


def register_error_handlers(app):

    # =========================
    # Bad Request - 400
    # =========================
    @app.errorhandler(400)
    def bad_request(error):

        return error_response("Bad Request", 400, str(error.description))


    # =========================
    # Unauthorized - 401
    # =========================
    @app.errorhandler(401)
    def unauthorized(error):

        return error_response("Unauthorized", 401, "Authentication is required")


    # =========================
    # Forbidden - 403
    # =========================
    @app.errorhandler(403)
    def forbidden(error):

        return error_response("Forbidden", 403, "You do not have permission to access this resource")


    # =========================
    # Not Found - 404
    # =========================
    @app.errorhandler(404)
    def not_found(error):

        return error_response("Not Found", 404, "The requested resource was not found")


    # =========================
    # Method Not Allowed - 405
    # =========================
    @app.errorhandler(405)
    def method_not_allowed(error):

        return error_response("Method Not Allowed", 405, "This HTTP method is not allowed for this endpoint")


    # =========================
    # Internal Server Error - 500
    # =========================
    @app.errorhandler(500)
    def internal_server_error(error):

        return error_response("Internal Server Error", 500, "Something went wrong on the server")
