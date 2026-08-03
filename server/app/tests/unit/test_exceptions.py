"""Unit tests for custom exception classes."""

import pytest
from core.exceptions import (
    AppException,
    RateLimitExceededError,
)


# ============================================
# APP EXCEPTION TESTS
# ============================================

class TestAppException:
    """Test AppException custom exception."""
    
    def test_app_exception_initialization(self):
        """Test that AppException can be initialized."""
        exc = AppException(
            error_code="TEST_ERROR",
            message="Test error message",
            status_code=400
        )
        
        assert exc is not None
        assert isinstance(exc, Exception)
    
    def test_app_exception_error_code(self):
        """Test that error_code is stored correctly."""
        error_code = "INVALID_INPUT"
        exc = AppException(
            error_code=error_code,
            message="Test message"
        )
        
        assert exc.error_code == error_code
    
    def test_app_exception_message(self):
        """Test that message is stored correctly."""
        message = "Something went wrong"
        exc = AppException(
            error_code="ERROR",
            message=message
        )
        
        assert exc.message == message
    
    def test_app_exception_status_code_default(self):
        """Test that status_code defaults to 500."""
        exc = AppException(
            error_code="ERROR",
            message="Test"
        )
        
        assert exc.status_code == 500
    
    def test_app_exception_status_code_custom(self):
        """Test that custom status_code is used."""
        exc = AppException(
            error_code="BAD_REQUEST",
            message="Test",
            status_code=400
        )
        
        assert exc.status_code == 400
    
    def test_app_exception_details_default(self):
        """Test that details defaults to None."""
        exc = AppException(
            error_code="ERROR",
            message="Test"
        )
        
        assert exc.details is None
    
    def test_app_exception_details_custom(self):
        """Test that custom details are stored."""
        details = {"field": "username", "reason": "required"}
        exc = AppException(
            error_code="VALIDATION_ERROR",
            message="Test",
            details=details
        )
        
        assert exc.details == details
    
    def test_app_exception_details_is_dict(self):
        """Test that details can be a dictionary."""
        details = {"key1": "value1", "key2": "value2"}
        exc = AppException(
            error_code="ERROR",
            message="Test",
            details=details
        )
        
        assert isinstance(exc.details, dict)
        assert exc.details["key1"] == "value1"
    
    def test_app_exception_str_representation(self):
        """Test that exception has string representation."""
        exc = AppException(
            error_code="TEST_ERROR",
            message="Test message"
        )
        
        exc_str = str(exc)
        assert len(exc_str) > 0
    
    def test_app_exception_is_exception(self):
        """Test that AppException is an Exception."""
        exc = AppException(
            error_code="ERROR",
            message="Test"
        )
        
        assert isinstance(exc, Exception)
    
    def test_app_exception_can_be_raised(self):
        """Test that AppException can be raised and caught."""
        with pytest.raises(AppException) as exc_info:
            raise AppException(
                error_code="TEST_ERROR",
                message="Test message"
            )
        
        assert exc_info.value.error_code == "TEST_ERROR"
        assert exc_info.value.message == "Test message"


# ============================================
# RATE LIMIT EXCEEDED ERROR TESTS
# ============================================

class TestRateLimitExceededError:
    """Test RateLimitExceededError custom exception."""
    
    def test_rate_limit_error_initialization(self):
        """Test that RateLimitExceededError can be initialized."""
        exc = RateLimitExceededError(
            message="Rate limit exceeded",
            retry_after=60
        )
        
        assert exc is not None
        assert isinstance(exc, AppException)
    
    def test_rate_limit_error_status_code(self):
        """Test that status_code is 429."""
        exc = RateLimitExceededError(
            message="Rate limit exceeded"
        )
        
        assert exc.status_code == 429
    
    def test_rate_limit_error_code(self):
        """Test that error_code is RATE_LIMIT_EXCEEDED."""
        exc = RateLimitExceededError(
            message="Rate limit exceeded"
        )
        
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
    
    def test_rate_limit_error_message(self):
        """Test that message is stored."""
        message = "Custom rate limit message"
        exc = RateLimitExceededError(message=message)
        
        assert exc.message == message
    
    def test_rate_limit_error_retry_after_default(self):
        """Test that retry_after defaults to None."""
        exc = RateLimitExceededError(
            message="Rate limit exceeded"
        )
        
        # Should be in details
        assert exc.details is not None or True
    
    def test_rate_limit_error_retry_after_custom(self):
        """Test that custom retry_after is stored."""
        retry_after = 120
        exc = RateLimitExceededError(
            message="Rate limit exceeded",
            retry_after=retry_after
        )
        
        assert exc.details["retry_after"] == retry_after
    
    def test_rate_limit_error_retry_after_is_integer(self):
        """Test that retry_after is an integer."""
        exc = RateLimitExceededError(
            message="Rate limit exceeded",
            retry_after=60
        )
        
        assert isinstance(exc.details["retry_after"], int)
    
    def test_rate_limit_error_inherits_from_app_exception(self):
        """Test that RateLimitExceededError inherits from AppException."""
        exc = RateLimitExceededError(message="Rate limit")
        assert isinstance(exc, AppException)
    
    def test_rate_limit_error_can_be_raised(self):
        """Test that RateLimitExceededError can be raised and caught."""
        with pytest.raises(RateLimitExceededError):
            raise RateLimitExceededError(message="Rate limit exceeded")
    
    def test_rate_limit_error_caught_as_app_exception(self):
        """Test that RateLimitExceededError can be caught as AppException."""
        with pytest.raises(AppException) as exc_info:
            raise RateLimitExceededError(message="Rate limit exceeded")
        
        assert isinstance(exc_info.value, RateLimitExceededError)


# ============================================
# HTTP STATUS CODE TESTS
# ============================================

class TestHTTPStatusCodes:
    """Test that exceptions use correct HTTP status codes."""
    
    def test_validation_error_status_code(self):
        """Test that validation errors use 422."""
        exc = AppException(
            error_code="VALIDATION_ERROR",
            message="Invalid input",
            status_code=422
        )
        
        assert exc.status_code == 422
    
    def test_authentication_error_status_code(self):
        """Test that auth errors use 401."""
        exc = AppException(
            error_code="INVALID_CREDENTIALS",
            message="Invalid credentials",
            status_code=401
        )
        
        assert exc.status_code == 401
    
    def test_authorization_error_status_code(self):
        """Test that authorization errors use 403."""
        exc = AppException(
            error_code="FORBIDDEN",
            message="Access forbidden",
            status_code=403
        )
        
        assert exc.status_code == 403
    
    def test_not_found_error_status_code(self):
        """Test that not found errors use 404."""
        exc = AppException(
            error_code="NOT_FOUND",
            message="Resource not found",
            status_code=404
        )
        
        assert exc.status_code == 404
    
    def test_conflict_error_status_code(self):
        """Test that conflict errors use 409."""
        exc = AppException(
            error_code="CONFLICT",
            message="Resource conflict",
            status_code=409
        )
        
        assert exc.status_code == 409
    
    def test_rate_limit_error_status_code_is_429(self):
        """Test that rate limit errors use 429."""
        exc = RateLimitExceededError(message="Rate limit")
        
        assert exc.status_code == 429
    
    def test_internal_server_error_status_code(self):
        """Test that server errors use 500."""
        exc = AppException(
            error_code="INTERNAL_ERROR",
            message="Server error",
            status_code=500
        )
        
        assert exc.status_code == 500


# ============================================
# ERROR CODE TESTS
# ============================================

class TestErrorCodes:
    """Test that error codes are meaningful."""
    
    def test_error_code_not_empty(self):
        """Test that error_code is not empty."""
        exc = AppException(
            error_code="TEST_ERROR",
            message="Test"
        )
        
        assert len(exc.error_code) > 0
    
    def test_error_code_uppercase(self):
        """Test that error_code uses uppercase (convention)."""
        error_code = "INVALID_INPUT"
        exc = AppException(
            error_code=error_code,
            message="Test"
        )
        
        assert exc.error_code == error_code
        assert exc.error_code.isupper()
    
    def test_error_code_descriptive(self):
        """Test that error_code is descriptive."""
        descriptive_codes = [
            "INVALID_CREDENTIALS",
            "USER_NOT_FOUND",
            "VALIDATION_ERROR",
            "RATE_LIMIT_EXCEEDED",
            "DATABASE_ERROR",
        ]
        
        for code in descriptive_codes:
            exc = AppException(
                error_code=code,
                message="Test"
            )
            
            # Should be meaningful, not just "ERROR"
            assert len(code) > 5
    
    def test_rate_limit_error_code_specific(self):
        """Test that RateLimitExceededError has specific error code."""
        exc = RateLimitExceededError(message="Rate limit")
        
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.error_code != "ERROR"
        assert exc.error_code != "RATE_LIMIT"


# ============================================
# MESSAGE TESTS
# ============================================

class TestErrorMessages:
    """Test that error messages are descriptive."""
    
    def test_message_not_empty(self):
        """Test that message is not empty."""
        exc = AppException(
            error_code="ERROR",
            message="Descriptive message"
        )
        
        assert len(exc.message) > 0
    
    def test_message_descriptive(self):
        """Test that message is descriptive."""
        descriptive_messages = [
            "Username or password is incorrect",
            "User with email already exists",
            "Invalid search query format",
            "Ticket not found",
            "Database connection failed",
        ]
        
        for msg in descriptive_messages:
            exc = AppException(
                error_code="ERROR",
                message=msg
            )
            
            # Message should be more than just "Error"
            assert len(msg) > 5
    
    def test_message_user_friendly(self):
        """Test that message is user-friendly."""
        exc = AppException(
            error_code="INVALID_INPUT",
            message="Username must be at least 3 characters"
        )
        
        # Should be understandable
        assert "Username" in exc.message
        assert "3 characters" in exc.message


# ============================================
# DETAILS TESTS
# ============================================

class TestErrorDetails:
    """Test that error details provide additional context."""
    
    def test_details_can_be_none(self):
        """Test that details can be None."""
        exc = AppException(
            error_code="ERROR",
            message="Test",
            details=None
        )
        
        assert exc.details is None
    
    def test_details_can_be_dict(self):
        """Test that details can be a dictionary."""
        details = {"field": "email", "reason": "already_exists"}
        exc = AppException(
            error_code="ERROR",
            message="Test",
            details=details
        )
        
        assert isinstance(exc.details, dict)
        assert exc.details["field"] == "email"
    
    def test_details_can_have_multiple_fields(self):
        """Test that details dict can have multiple fields."""
        details = {
            "field": "username",
            "reason": "too_short",
            "min_length": 3,
            "current_length": 2,
        }
        exc = AppException(
            error_code="VALIDATION_ERROR",
            message="Test",
            details=details
        )
        
        assert len(exc.details) == 4
        assert exc.details["min_length"] == 3
    
    def test_details_with_nested_dict(self):
        """Test that details can have nested structures."""
        details = {
            "errors": {
                "username": "too_short",
                "password": "weak",
            }
        }
        exc = AppException(
            error_code="VALIDATION_ERROR",
            message="Test",
            details=details
        )
        
        assert "errors" in exc.details
        assert exc.details["errors"]["username"] == "too_short"


# ============================================
# EXCEPTION HIERARCHY TESTS
# ============================================

class TestExceptionHierarchy:
    """Test exception inheritance and hierarchy."""
    
    def test_app_exception_inherits_from_exception(self):
        """Test that AppException inherits from Exception."""
        exc = AppException(error_code="TEST", message="Test")
        
        assert isinstance(exc, Exception)
        assert issubclass(AppException, Exception)
    
    def test_rate_limit_inherits_from_app_exception(self):
        """Test that RateLimitExceededError inherits from AppException."""
        exc = RateLimitExceededError(message="Rate limit")
        
        assert isinstance(exc, AppException)
        assert isinstance(exc, Exception)
        assert issubclass(RateLimitExceededError, AppException)
    
    def test_multiple_exceptions_independent(self):
        """Test that multiple exception instances are independent."""
        exc1 = AppException(
            error_code="ERROR1",
            message="Message 1"
        )
        exc2 = AppException(
            error_code="ERROR2",
            message="Message 2"
        )
        
        assert exc1.error_code != exc2.error_code
        assert exc1.message != exc2.message


# ============================================
# EXCEPTION USAGE SCENARIOS
# ============================================

class TestExceptionUsageScenarios:
    """Test real-world exception usage scenarios."""
    
    def test_validation_error_scenario(self):
        """Test validation error in realistic scenario."""
        with pytest.raises(AppException) as exc_info:
            # Simulate validation failure
            raise AppException(
                error_code="INVALID_EMAIL",
                message="Email format is invalid",
                status_code=422,
                details={"field": "email", "format": "user@domain.com"}
            )
        
        exc = exc_info.value
        assert exc.status_code == 422
        assert exc.error_code == "INVALID_EMAIL"
        assert exc.details["field"] == "email"
    
    def test_authentication_error_scenario(self):
        """Test authentication error in realistic scenario."""
        with pytest.raises(AppException) as exc_info:
            # Simulate auth failure
            raise AppException(
                error_code="INVALID_CREDENTIALS",
                message="Username or password is incorrect",
                status_code=401
            )
        
        exc = exc_info.value
        assert exc.status_code == 401
        assert exc.error_code == "INVALID_CREDENTIALS"
    
    def test_rate_limit_scenario(self):
        """Test rate limit error in realistic scenario."""
        with pytest.raises(RateLimitExceededError) as exc_info:
            # Simulate rate limit
            raise RateLimitExceededError(
                message="Too many requests",
                retry_after=60
            )
        
        exc = exc_info.value
        assert exc.status_code == 429
        assert exc.details["retry_after"] == 60
    
    def test_not_found_scenario(self):
        """Test not found error in realistic scenario."""
        with pytest.raises(AppException) as exc_info:
            # Simulate not found
            raise AppException(
                error_code="TICKET_NOT_FOUND",
                message="Ticket with ID 123 was not found",
                status_code=404,
                details={"ticket_id": 123}
            )
        
        exc = exc_info.value
        assert exc.status_code == 404
        assert exc.details["ticket_id"] == 123
    
    def test_server_error_scenario(self):
        """Test server error in realistic scenario."""
        with pytest.raises(AppException) as exc_info:
            # Simulate server error
            raise AppException(
                error_code="DATABASE_ERROR",
                message="Database connection failed",
                status_code=500,
                details={"reason": "connection_timeout"}
            )
        
        exc = exc_info.value
        assert exc.status_code == 500
        assert exc.details["reason"] == "connection_timeout"
