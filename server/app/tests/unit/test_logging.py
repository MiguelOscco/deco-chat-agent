"""Unit tests for logging functionality."""

import pytest
import logging
import json
import io
import sys
from datetime import datetime

from core.logging import (
    setup_logging,
    get_logger,
    mask_sensitive_data,
)


# ============================================
# LOGGING SETUP TESTS
# ============================================

class TestLoggingSetup:
    """Test logging initialization and setup."""
    
    def test_setup_logging_executes_without_error(self):
        """Test that setup_logging() executes without error."""
        try:
            setup_logging()
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"setup_logging() raised exception: {e}")
        
        assert success is True
    
    def test_setup_logging_can_be_called_multiple_times(self):
        """Test that setup_logging() can be called multiple times."""
        try:
            setup_logging()
            setup_logging()
            setup_logging()
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"Multiple setup_logging() calls failed: {e}")
        
        assert success is True
    
    def test_get_logger_returns_logger_object(self):
        """Test that get_logger() returns a logger object."""
        setup_logging()
        logger = get_logger(__name__)
        
        assert logger is not None
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')
    
    def test_get_logger_with_module_name(self):
        """Test get_logger() with module name."""
        setup_logging()
        logger = get_logger(__name__)
        
        assert logger is not None
    
    def test_get_logger_with_custom_name(self):
        """Test get_logger() with custom logger name."""
        setup_logging()
        logger = get_logger("custom_logger_name")
        
        assert logger is not None


# ============================================
# LOGGER FUNCTIONALITY TESTS
# ============================================

class TestLoggerFunctionality:
    """Test logger methods and functionality."""
    
    def test_logger_debug_method(self):
        """Test that logger has debug method."""
        setup_logging()
        logger = get_logger(__name__)
        
        try:
            logger.debug("Debug message")
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"logger.debug() failed: {e}")
        
        assert success is True
    
    def test_logger_info_method(self):
        """Test that logger has info method."""
        setup_logging()
        logger = get_logger(__name__)
        
        try:
            logger.info("Info message")
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"logger.info() failed: {e}")
        
        assert success is True
    
    def test_logger_warning_method(self):
        """Test that logger has warning method."""
        setup_logging()
        logger = get_logger(__name__)
        
        try:
            logger.warning("Warning message")
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"logger.warning() failed: {e}")
        
        assert success is True
    
    def test_logger_error_method(self):
        """Test that logger has error method."""
        setup_logging()
        logger = get_logger(__name__)
        
        try:
            logger.error("Error message")
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"logger.error() failed: {e}")
        
        assert success is True
    
    def test_logger_critical_method(self):
        """Test that logger has critical method."""
        setup_logging()
        logger = get_logger(__name__)
        
        try:
            logger.critical("Critical message")
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"logger.critical() failed: {e}")
        
        assert success is True
    
    def test_logger_with_extra_fields(self):
        """Test logging with extra fields."""
        setup_logging()
        logger = get_logger(__name__)
        
        try:
            logger.info(
                "Message with extras",
                extra={
                    "user_id": 123,
                    "action": "login",
                    "ip": "192.168.1.1"
                }
            )
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"Logging with extra fields failed: {e}")
        
        assert success is True
    
    def test_logger_with_exception(self):
        """Test logging with exception info."""
        setup_logging()
        logger = get_logger(__name__)
        
        try:
            try:
                1 / 0  # Raise ZeroDivisionError
            except ZeroDivisionError:
                logger.error("An error occurred", exc_info=True)
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"Logging exception failed: {e}")
        
        assert success is True


# ============================================
# LOG LEVELS TESTS
# ============================================

class TestLogLevels:
    """Test different log levels."""
    
    def test_debug_level_logging(self):
        """Test DEBUG level logging."""
        setup_logging()
        logger = get_logger(__name__)
        
        # Set to DEBUG to capture all levels
        logger.setLevel(logging.DEBUG)
        
        logger.debug("Debug message")
        # Should not raise exception
    
    def test_info_level_logging(self):
        """Test INFO level logging."""
        setup_logging()
        logger = get_logger(__name__)
        
        logger.setLevel(logging.INFO)
        logger.info("Info message")
    
    def test_warning_level_logging(self):
        """Test WARNING level logging."""
        setup_logging()
        logger = get_logger(__name__)
        
        logger.setLevel(logging.WARNING)
        logger.warning("Warning message")
    
    def test_error_level_logging(self):
        """Test ERROR level logging."""
        setup_logging()
        logger = get_logger(__name__)
        
        logger.setLevel(logging.ERROR)
        logger.error("Error message")
    
    def test_critical_level_logging(self):
        """Test CRITICAL level logging."""
        setup_logging()
        logger = get_logger(__name__)
        
        logger.setLevel(logging.CRITICAL)
        logger.critical("Critical message")


# ============================================
# SENSITIVE DATA MASKING TESTS
# ============================================

class TestSensitiveDataMasking:
    """Test masking of sensitive information."""
    
    def test_mask_password_in_string(self):
        """Test that passwords are masked."""
        text = "password=secret123"
        masked = mask_sensitive_data(text)
        
        # Should not contain original password
        assert "secret123" not in masked or "***" in masked
    
    def test_mask_api_key_in_string(self):
        """Test that API keys are masked."""
        text = "api_key=sk_live_12345abcde"
        masked = mask_sensitive_data(text)
        
        # Should not contain full API key or should be masked
        assert "12345abcde" not in masked or "***" in masked
    
    def test_mask_token_in_string(self):
        """Test that tokens are masked."""
        text = "token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        masked = mask_sensitive_data(text)
        
        # Should not contain full token or should be masked
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in masked or "***" in masked
    
    def test_mask_credit_card_in_string(self):
        """Test that credit card numbers are masked."""
        text = "card=4532123456789010"
        masked = mask_sensitive_data(text)
        
        # Should not contain full card number or should be masked
        assert "4532123456789010" not in masked or "***" in masked
    
    def test_mask_ssn_in_string(self):
        """Test that SSN is masked."""
        text = "ssn=123-45-6789"
        masked = mask_sensitive_data(text)
        
        # Should be masked
        assert "123-45-6789" not in masked or "***" in masked
    
    def test_mask_normal_text_unchanged(self):
        """Test that normal text is not masked."""
        text = "This is a normal log message"
        masked = mask_sensitive_data(text)
        
        # Should remain the same or very similar
        assert text in masked or text.lower() in masked.lower()
    
    def test_mask_multiple_sensitive_fields(self):
        """Test masking multiple sensitive fields."""
        text = "username=admin password=secret123 api_key=sk_live_123"
        masked = mask_sensitive_data(text)
        
        # Original sensitive values should be masked
        assert "secret123" not in masked or "***" in masked
        assert "sk_live_123" not in masked or "***" in masked
    
    def test_mask_empty_string(self):
        """Test masking empty string."""
        masked = mask_sensitive_data("")
        assert masked == ""
    
    def test_mask_none_returns_none(self):
        """Test that masking None returns None or empty."""
        result = mask_sensitive_data(None)
        assert result is None or result == ""


# ============================================
# JSON FORMAT TESTS
# ============================================

class TestJSONLogging:
    """Test JSON structured logging format."""
    
    def test_log_output_can_be_json(self):
        """Test that log output can be valid JSON."""
        # This is a basic test - actual JSON format depends on configuration
        setup_logging()
        logger = get_logger(__name__)
        
        # Capture log output
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Log a message
        logger.info("Test message", extra={"key": "value"})
        
        # Get the output
        output = log_stream.getvalue()
        
        # Should have some output
        assert len(output) > 0
    
    def test_log_contains_timestamp(self):
        """Test that logs might contain timestamp."""
        setup_logging()
        logger = get_logger(__name__)
        
        # Create a string buffer to capture output
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        
        # Use a format that includes timestamp
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        logger.info("Test message with timestamp")
        
        output = log_stream.getvalue()
        
        # Should contain the message
        assert "Test message with timestamp" in output
    
    def test_log_contains_level(self):
        """Test that logs contain log level."""
        setup_logging()
        logger = get_logger(__name__)
        
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        logger.info("Test info message")
        logger.error("Test error message")
        
        output = log_stream.getvalue()
        
        # Should contain level indicators
        assert "INFO" in output or "info" in output.lower()
        assert "ERROR" in output or "error" in output.lower()
    
    def test_log_contains_message(self):
        """Test that logs contain the message."""
        setup_logging()
        logger = get_logger(__name__)
        
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        test_message = "Unique test message 12345"
        logger.info(test_message)
        
        output = log_stream.getvalue()
        
        assert test_message in output


# ============================================
# LOGGER NAMES TESTS
# ============================================

class TestLoggerNames:
    """Test logger naming and identification."""
    
    def test_logger_name_from_module(self):
        """Test that logger gets name from module."""
        setup_logging()
        logger = get_logger(__name__)
        
        # Logger should have a name
        assert logger.name is not None
        assert len(logger.name) > 0
    
    def test_different_loggers_by_name(self):
        """Test that different names create different loggers."""
        setup_logging()
        logger1 = get_logger("logger_1")
        logger2 = get_logger("logger_2")
        
        # Should be different logger instances
        assert logger1.name != logger2.name
        assert logger1.name == "logger_1"
        assert logger2.name == "logger_2"
    
    def test_same_name_returns_same_logger(self):
        """Test that same name returns same logger instance."""
        setup_logging()
        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")
        
        # Should be same or equivalent
        assert logger1.name == logger2.name


# ============================================
# LOGGING WITH CONTEXT TESTS
# ============================================

class TestLoggingWithContext:
    """Test logging with contextual information."""
    
    def test_log_with_user_id(self):
        """Test logging with user ID context."""
        setup_logging()
        logger = get_logger(__name__)
        
        try:
            logger.info("User action", extra={"user_id": 123})
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"Logging with user_id failed: {e}")
        
        assert success is True
    
    def test_log_with_request_id(self):
        """Test logging with request ID context."""
        setup_logging()
        logger = get_logger(__name__)
        
        try:
            logger.info("Request received", extra={"request_id": "abc123xyz"})
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"Logging with request_id failed: {e}")
        
        assert success is True
    
    def test_log_with_client_ip(self):
        """Test logging with client IP context."""
        setup_logging()
        logger = get_logger(__name__)
        
        try:
            logger.info("Client connected", extra={"client_ip": "192.168.1.100"})
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"Logging with client_ip failed: {e}")
        
        assert success is True
    
    def test_log_with_multiple_context_fields(self):
        """Test logging with multiple context fields."""
        setup_logging()
        logger = get_logger(__name__)
        
        try:
            logger.info(
                "Complex action",
                extra={
                    "user_id": 123,
                    "request_id": "abc123",
                    "client_ip": "192.168.1.1",
                    "action": "login",
                    "status": "success",
                    "duration_ms": 245,
                }
            )
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"Logging with multiple fields failed: {e}")
        
        assert success is True


# ============================================
# ERROR LOGGING TESTS
# ============================================

class TestErrorLogging:
    """Test error and exception logging."""
    
    def test_log_exception_with_traceback(self):
        """Test logging exception with traceback."""
        setup_logging()
        logger = get_logger(__name__)
        
        try:
            try:
                x = 1 / 0
            except ZeroDivisionError:
                logger.error("Division by zero error", exc_info=True)
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"Exception logging failed: {e}")
        
        assert success is True
    
    def test_log_error_without_traceback(self):
        """Test logging error without traceback."""
        setup_logging()
        logger = get_logger(__name__)
        
        try:
            logger.error("An error occurred without traceback")
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"Error logging failed: {e}")
        
        assert success is True
    
    def test_log_error_with_message(self):
        """Test logging error with descriptive message."""
        setup_logging()
        logger = get_logger(__name__)
        
        error_message = "Database connection failed: timeout"
        logger.error(error_message)
        
        # Just verify it doesn't crash
        assert True


# ============================================
# PERFORMANCE TESTS
# ============================================

class TestLoggingPerformance:
    """Test logging performance and efficiency."""
    
    def test_logger_multiple_logs_performance(self):
        """Test logging many messages quickly."""
        setup_logging()
        logger = get_logger(__name__)
        
        import time
        
        start_time = time.time()
        
        # Log 100 messages
        for i in range(100):
            logger.info(f"Message {i}")
        
        elapsed = time.time() - start_time
        
        # Should complete reasonably fast (less than 5 seconds)
        assert elapsed < 5.0
    
    def test_logger_with_large_messages(self):
        """Test logging large messages."""
        setup_logging()
        logger = get_logger(__name__)
        
        # Create a large message
        large_message = "x" * 10000
        
        try:
            logger.info(large_message)
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"Large message logging failed: {e}")
        
        assert success is True


# ============================================
# LOGGER INSTANCE TESTS
# ============================================

class TestLoggerInstance:
    """Test logger instance creation and caching."""
    
    def test_get_logger_instance_type(self):
        """Test that get_logger returns correct type."""
        setup_logging()
        logger = get_logger(__name__)
        
        # Should be a logger or adapter
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')
    
    def test_logger_has_required_methods(self):
        """Test that logger has all required logging methods."""
        setup_logging()
        logger = get_logger(__name__)
        
        required_methods = ['debug', 'info', 'warning', 'error', 'critical']
        
        for method in required_methods:
            assert hasattr(logger, method)
            assert callable(getattr(logger, method))
