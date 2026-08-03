"""
Custom exception classes for the application.

Provides structured exception hierarchy for better error handling
and consistent API error responses.
"""


from typing import Optional, Any, Dict


class AppException(Exception):
    """
    Base exception class for the application.
    
    All custom exceptions inherit from this class.
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = "APP_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize exception.
        
        Args:
            message: Error message
            error_code: Unique error code for client identification
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


# ============================================
# AUTHENTICATION EXCEPTIONS
# ============================================

class AuthenticationError(AppException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            status_code=401,
            details=details
        )


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid."""
    
    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(message)


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token is expired."""
    
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid."""
    
    def __init__(self, message: str = "Invalid or malformed token"):
        super().__init__(message)


class TokenRevokedError(AuthenticationError):
    """Raised when token has been revoked."""
    
    def __init__(self, message: str = "Token has been revoked"):
        super().__init__(message)


# ============================================
# AUTHORIZATION EXCEPTIONS
# ============================================

class AuthorizationError(AppException):
    """Raised when user lacks required permissions."""
    
    def __init__(
        self,
        message: str = "You do not have permission to access this resource",
        details: Optional[Dict] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHZ_ERROR",
            status_code=403,
            details=details
        )


# ============================================
# VALIDATION EXCEPTIONS
# ============================================

class ValidationError(AppException):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str = "Validation error",
        details: Optional[Dict] = None
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )


class InvalidInputError(ValidationError):
    """Raised when input format is invalid."""
    pass


class MissingRequiredFieldError(ValidationError):
    """Raised when required field is missing."""
    
    def __init__(self, field_name: str):
        super().__init__(
            message=f"Required field '{field_name}' is missing",
            details={"field": field_name}
        )


class InputTooLongError(ValidationError):
    """Raised when input exceeds maximum length."""
    
    def __init__(self, field_name: str, max_length: int):
        super().__init__(
            message=f"Field '{field_name}' exceeds maximum length of {max_length}",
            details={"field": field_name, "max_length": max_length}
        )


# ============================================
# RESOURCE EXCEPTIONS
# ============================================

class ResourceNotFoundError(AppException):
    """Raised when requested resource is not found."""
    
    def __init__(
        self,
        resource_type: str = "Resource",
        resource_id: Optional[str] = None
    ):
        message = f"{resource_type} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
        
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class ResourceAlreadyExistsError(AppException):
    """Raised when attempting to create duplicate resource."""
    
    def __init__(self, resource_type: str, identifier: str):
        super().__init__(
            message=f"{resource_type} with identifier '{identifier}' already exists",
            error_code="RESOURCE_CONFLICT",
            status_code=409,
            details={"resource_type": resource_type, "identifier": identifier}
        )


# ============================================
# EXTERNAL SERVICE EXCEPTIONS
# ============================================

class ExternalServiceError(AppException):
    """Raised when external service fails."""
    
    def __init__(
        self,
        service_name: str,
        message: str = None,
        details: Optional[Dict] = None
    ):
        if not message:
            message = f"{service_name} service unavailable"
        
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=503,
            details={"service": service_name, **(details or {})}
        )


class GLPIError(ExternalServiceError):
    """Raised when GLPI API fails."""
    
    def __init__(self, message: str = "GLPI service error", details: Optional[Dict] = None):
        super().__init__("GLPI", message, details)


class OllamaError(ExternalServiceError):
    """Raised when Ollama LLM fails."""
    
    def __init__(self, message: str = "Ollama service error", details: Optional[Dict] = None):
        super().__init__("Ollama", message, details)


# ============================================
# DATABASE EXCEPTIONS
# ============================================

class DatabaseError(AppException):
    """Raised when database operation fails."""
    
    def __init__(self, message: str = "Database error", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details=details
        )


# ============================================
# RATE LIMIT EXCEPTIONS
# ============================================

class RateLimitExceededError(AppException):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Too many requests",
        retry_after: Optional[int] = None
    ):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after": retry_after}
        )
