"""
Custom Exception Classes - Smart Railway Ticketing System

Provides structured error handling across service and route layers.
All exceptions include status codes for consistent HTTP responses.
"""

from typing import Optional, Dict, Any


class RailwayException(Exception):
    """Base exception for all Railway system errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        details: Optional[str] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details
        self.error_code = error_code

    def to_response(self) -> Dict[str, Any]:
        """Convert exception to JSON response format."""
        response = {
            "status": "error",
            "message": self.message
        }
        if self.details:
            response["details"] = self.details
        if self.error_code:
            response["error_code"] = self.error_code
        return response


# ══════════════════════════════════════════════════════════════════════════════
#  AUTHENTICATION & AUTHORIZATION ERRORS (4xx)
# ══════════════════════════════════════════════════════════════════════════════

class AuthenticationError(RailwayException):
    """401 - Authentication failed or required."""

    def __init__(self, message: str = "Authentication failed", details: Optional[str] = None):
        super().__init__(message, 401, details, "AUTH_FAILED")


class AuthorizationError(RailwayException):
    """403 - User lacks required permissions."""

    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(message, 403, error_code="FORBIDDEN")


class InvalidTokenError(RailwayException):
    """401 - Token is invalid or expired."""

    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message, 401, error_code="INVALID_TOKEN")


class AccountBlockedError(RailwayException):
    """403 - User account is blocked or suspended."""

    def __init__(self, reason: str = ""):
        message = f"Account is blocked{': ' + reason if reason else ''}"
        super().__init__(message, 403, error_code="ACCOUNT_BLOCKED")


# ══════════════════════════════════════════════════════════════════════════════
#  VALIDATION ERRORS (400)
# ══════════════════════════════════════════════════════════════════════════════

class ValidationError(RailwayException):
    """400 - Input validation failed."""

    def __init__(self, message: str, details: Optional[str] = None, field: Optional[str] = None):
        error_code = f"INVALID_{field.upper()}" if field else "VALIDATION_ERROR"
        super().__init__(message, 400, details, error_code)


class InvalidDateError(RailwayException):
    """400 - Invalid date format or value."""

    def __init__(self, message: str = "Invalid journey date"):
        super().__init__(message, 400, error_code="INVALID_DATE")


class InvalidPasswordError(RailwayException):
    """400 - Password does not meet requirements."""

    def __init__(self, message: str = "Password must be at least 8 characters"):
        super().__init__(message, 400, error_code="INVALID_PASSWORD")


# ══════════════════════════════════════════════════════════════════════════════
#  NOT FOUND ERRORS (404)
# ══════════════════════════════════════════════════════════════════════════════

class NotFoundError(RailwayException):
    """404 - Generic resource not found."""

    def __init__(self, resource: str = "Resource", identifier: str = ""):
        message = f"{resource} not found{': ' + identifier if identifier else ''}"
        super().__init__(message, 404, error_code="NOT_FOUND")


class TrainNotFoundError(RailwayException):
    """404 - Train not found."""

    def __init__(self, identifier: str = ""):
        message = f"Train not found{': ' + identifier if identifier else ''}"
        super().__init__(message, 404, error_code="TRAIN_NOT_FOUND")


class BookingNotFoundError(RailwayException):
    """404 - Booking not found."""

    def __init__(self, identifier: str = ""):
        message = f"Booking not found{': ' + identifier if identifier else ''}"
        super().__init__(message, 404, error_code="BOOKING_NOT_FOUND")


class UserNotFoundError(RailwayException):
    """404 - User not found."""

    def __init__(self, identifier: str = ""):
        message = f"User not found{': ' + identifier if identifier else ''}"
        super().__init__(message, 404, error_code="USER_NOT_FOUND")


class StationNotFoundError(RailwayException):
    """404 - Station not found."""

    def __init__(self, identifier: str = ""):
        message = f"Station not found{': ' + identifier if identifier else ''}"
        super().__init__(message, 404, error_code="STATION_NOT_FOUND")


class RouteNotFoundError(RailwayException):
    """404 - Train route not found."""

    def __init__(self, identifier: str = ""):
        message = f"Route not found{': ' + identifier if identifier else ''}"
        super().__init__(message, 404, error_code="ROUTE_NOT_FOUND")


# ══════════════════════════════════════════════════════════════════════════════
#  CONFLICT ERRORS (409)
# ══════════════════════════════════════════════════════════════════════════════

class ConflictError(RailwayException):
    """409 - Resource conflict."""

    def __init__(self, message: str, error_code: str = "CONFLICT"):
        super().__init__(message, 409, error_code=error_code)


class DuplicateEmailError(RailwayException):
    """409 - Email already registered."""

    def __init__(self, email: str = ""):
        message = "Email already registered"
        super().__init__(message, 409, error_code="DUPLICATE_EMAIL")


class DuplicateBookingError(RailwayException):
    """409 - Duplicate booking exists."""

    def __init__(self):
        super().__init__(
            "Duplicate booking: you already have a booking on this train and date",
            409,
            error_code="DUPLICATE_BOOKING"
        )


class SeatUnavailableError(RailwayException):
    """409 - No seats available."""

    def __init__(self, travel_class: str = ""):
        message = f"No seats available{' in class ' + travel_class if travel_class else ''}"
        super().__init__(message, 409, error_code="SEAT_UNAVAILABLE")


# ══════════════════════════════════════════════════════════════════════════════
#  RATE LIMIT ERRORS (429)
# ══════════════════════════════════════════════════════════════════════════════

class RateLimitError(RailwayException):
    """429 - Rate limit exceeded."""

    def __init__(self, message: str = "Too many requests. Please try again later."):
        super().__init__(message, 429, error_code="RATE_LIMIT_EXCEEDED")


class BookingLimitError(RailwayException):
    """429 - Monthly booking limit reached."""

    def __init__(self, limit: int):
        super().__init__(
            f"Monthly booking limit of {limit} reached",
            429,
            error_code="BOOKING_LIMIT_EXCEEDED"
        )


# ══════════════════════════════════════════════════════════════════════════════
#  BUSINESS LOGIC ERRORS (400)
# ══════════════════════════════════════════════════════════════════════════════

class BookingAlreadyCancelledError(RailwayException):
    """400 - Booking is already cancelled."""

    def __init__(self):
        super().__init__("Booking is already cancelled", 400, error_code="ALREADY_CANCELLED")


class BookingNotCancellableError(RailwayException):
    """400 - Booking cannot be cancelled."""

    def __init__(self, reason: str = ""):
        message = f"Booking cannot be cancelled{': ' + reason if reason else ''}"
        super().__init__(message, 400, error_code="NOT_CANCELLABLE")


class PaymentRequiredError(RailwayException):
    """402 - Payment required to proceed."""

    def __init__(self, message: str = "Payment required"):
        super().__init__(message, 402, error_code="PAYMENT_REQUIRED")


# ══════════════════════════════════════════════════════════════════════════════
#  SERVICE ERRORS (5xx)
# ══════════════════════════════════════════════════════════════════════════════

class DatabaseError(RailwayException):
    """503 - Database service error."""

    def __init__(self, message: str = "Database service error"):
        super().__init__(message, 503, error_code="DATABASE_ERROR")


class AIServiceError(RailwayException):
    """503 - AI service unavailable."""

    def __init__(self, message: str = "AI service unavailable"):
        super().__init__(message, 503, error_code="AI_SERVICE_ERROR")


class ExternalServiceError(RailwayException):
    """503 - External service unavailable."""

    def __init__(self, service: str = "External service", message: str = ""):
        full_message = f"{service} unavailable{': ' + message if message else ''}"
        super().__init__(full_message, 503, error_code="SERVICE_UNAVAILABLE")
