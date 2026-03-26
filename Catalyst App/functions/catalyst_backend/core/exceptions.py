"""
Custom exception classes for Railway Ticketing System.
Provides structured error handling across service and route layers.
"""


class RailwayException(Exception):
    """Base exception for all Railway system errors."""
    def __init__(self, message: str, status_code: int = 400, details: str = None):
        super().__init__(message)
        self.message     = message
        self.status_code = status_code
        self.details     = details

    def to_response(self) -> dict:
        response = {"success": False, "error": self.message}
        if self.details:
            response["details"] = self.details
        return response


class TrainNotFoundError(RailwayException):
    def __init__(self, train_id: str = ""):
        super().__init__(f"Train not found{': ' + train_id if train_id else ''}", 404)


class BookingNotFoundError(RailwayException):
    def __init__(self, booking_id: str = ""):
        super().__init__(f"Booking not found{': ' + booking_id if booking_id else ''}", 404)


class UserNotFoundError(RailwayException):
    def __init__(self, identifier: str = ""):
        super().__init__(f"User not found{': ' + identifier if identifier else ''}", 404)


class SeatUnavailableError(RailwayException):
    def __init__(self, cls: str = ""):
        super().__init__(f"No seats available in class {cls}", 409)


class DuplicateBookingError(RailwayException):
    def __init__(self):
        super().__init__("Duplicate booking: you already have a booking on this train and date", 409)


class BookingLimitError(RailwayException):
    def __init__(self, limit: int):
        super().__init__(f"Monthly booking limit of {limit} reached", 429)


class InvalidDateError(RailwayException):
    def __init__(self, message: str = "Invalid journey date"):
        super().__init__(message, 400)


class BookingAlreadyCancelledError(RailwayException):
    def __init__(self):
        super().__init__("Booking is already cancelled", 400)


class AuthenticationError(RailwayException):
    def __init__(self, message: str = "Authentication failed", details: str = None):
        super().__init__(message, 401, details)


class AuthorizationError(RailwayException):
    def __init__(self):
        super().__init__("You do not have permission to perform this action", 403)


class ValidationError(RailwayException):
    def __init__(self, message: str, details: str = None):
        super().__init__(message, 400, details)


class ZohoServiceError(RailwayException):
    def __init__(self, message: str = "Database service error"):
        super().__init__(message, 503)


class AIServiceError(RailwayException):
    def __init__(self, message: str = "AI service unavailable"):
        super().__init__(message, 503)
