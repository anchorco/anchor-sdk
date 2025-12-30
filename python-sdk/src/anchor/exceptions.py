"""Custom exceptions for Anchor SDK."""

from typing import Dict, Any


class AnchorError(Exception):
    """Base exception for Anchor SDK."""

    def __init__(self, message: str, code: str = None):
        super().__init__(message)
        self.message = message
        self.code = code


class AnchorAPIError(AnchorError):
    """Base exception for API errors."""

    def __init__(
        self, message: str, status_code: int = None, response: Dict[str, Any] = None
    ):
        super().__init__(message, code="api_error")
        self.status_code = status_code
        self.response = response or {}


class AuthenticationError(AnchorAPIError):
    """Raised when authentication fails (401)."""

    def __init__(
        self,
        message: str = "Invalid API key",
        status_code: int = 401,
        response: Dict[str, Any] = None,
    ):
        super().__init__(message, status_code, response)
        self.code = "authentication_error"


class AuthorizationError(AnchorAPIError):
    """Raised when authorization fails (403)."""

    def __init__(
        self,
        message: str,
        status_code: int = 403,
        response: Dict[str, Any] = None,
        required_permission: str = None,
    ):
        super().__init__(message, status_code, response)
        self.code = "authorization_error"
        self.required_permission = required_permission


class NotFoundError(AnchorAPIError):
    """Raised when a resource is not found (404)."""

    def __init__(
        self, message: str, status_code: int = 404, response: Dict[str, Any] = None
    ):
        super().__init__(message, status_code, response)
        self.code = "not_found"


class ValidationError(AnchorAPIError):
    """Raised when input validation fails (400)."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        response: Dict[str, Any] = None,
        field: str = None,
    ):
        super().__init__(message, status_code, response)
        self.code = "validation_error"
        self.field = field


class PolicyViolationError(AnchorAPIError):
    """Raised when an operation is blocked by policy."""

    def __init__(
        self,
        message: str,
        policy_name: str,
        status_code: int = 403,
        response: Dict[str, Any] = None,
    ):
        super().__init__(message, status_code, response)
        self.code = "policy_violation"
        self.policy_name = policy_name


class RateLimitError(AnchorAPIError):
    """Raised when rate limited (429)."""

    def __init__(
        self,
        message: str,
        status_code: int = 429,
        response: Dict[str, Any] = None,
        retry_after: int = None,
    ):
        super().__init__(message, status_code, response)
        self.code = "rate_limit"
        self.retry_after = retry_after


class ServerError(AnchorAPIError):
    """Raised for server errors (5xx)."""

    def __init__(
        self, message: str, status_code: int = 500, response: Dict[str, Any] = None
    ):
        super().__init__(message, status_code, response)
        self.code = "server_error"


class NetworkError(AnchorError):
    """Raised for network connectivity issues."""

    def __init__(self, message: str):
        super().__init__(message, code="network_error")


class ChainIntegrityError(AnchorError):
    """Raised when audit chain integrity verification fails."""

    def __init__(self, message: str, entry_id: str = None):
        super().__init__(message, code="chain_integrity_error")
        self.entry_id = entry_id
