# =========================
# Application Exceptions
# =========================


class ApplicationNotFound(Exception):
    """
    Raised when a requested job application
    is not found.
    """

    def __init__(self, message):
        super().__init__(message)


class DuplicateApplication(Exception):
    """
    Raised when a duplicate job application
    is created.
    """

    def __init__(self, message):
        super().__init__(message)