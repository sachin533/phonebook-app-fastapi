"""Application error carrying an HTTP status, like Node's error.statusCode."""


class AppError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
