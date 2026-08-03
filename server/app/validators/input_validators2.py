"""Input validation and sanitization utilities (OWASP compliance)."""

from typing import Any, Dict, List
import re
from config import settings
from core.exceptions import ValidationError, InputTooLongError


class InputValidator:
    """OWASP-compliant input validator."""
    
    # Patterns for validation
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,32}$')
    PASSWORD_PATTERN = re.compile(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)",
        r"(--|#|/\*|\*/)",
        r"('|\")\s*(OR|AND)\s*('|\")",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'on\w+\s*=',  # onclick=, onload=, etc
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
    ]
    
    @staticmethod
    def validate_email(email: str, max_length: int = 255) -> str:
        """Validate email address."""
        if not email:
            raise ValidationError("Email cannot be empty")
        
        email = email.strip()
        
        if len(email) > max_length:
            raise InputTooLongError("email", max_length)
        
        if not InputValidator.EMAIL_PATTERN.match(email):
            raise ValidationError("Invalid email format")
        
        return email.lower()
    
    @staticmethod
    def validate_username(username: str) -> str:
        """Validate username (alphanumeric, underscore, hyphen)."""
        if not username:
            raise ValidationError("Username cannot be empty")
        
        username = username.strip()
        
        if not InputValidator.USERNAME_PATTERN.match(username):
            raise ValidationError("Username must be 3-32 chars, alphanumeric/underscore/hyphen only")
        
        return username
    
    @staticmethod
    def validate_password(password: str) -> str:
        """Validate password strength."""
        if not password:
            raise ValidationError("Password cannot be empty")
        
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            raise ValidationError(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters")
        
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain uppercase letter")
        
        if settings.PASSWORD_REQUIRE_DIGITS and not re.search(r'\d', password):
            raise ValidationError("Password must contain digit")
        
        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[@$!%*?&]', password):
            raise ValidationError("Password must contain special character (@$!%*?&)")
        
        return password
    
    @staticmethod
    def validate_string(value: str, field_name: str = "value", max_length: int = 1000, allow_special: bool = False) -> str:
        """Validate and sanitize string input."""
        if value is None:
            raise ValidationError(f"{field_name} cannot be None")
        
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be string")
        
        value = value.strip()
        
        if len(value) == 0:
            raise ValidationError(f"{field_name} cannot be empty")
        
        if len(value) > max_length:
            raise InputTooLongError(field_name, max_length)
        
        # Check for SQL injection
        if InputValidator._contains_sql_injection(value):
            raise ValidationError(f"{field_name} contains invalid characters (SQL injection detected)")
        
        # Check for XSS
        if InputValidator._contains_xss(value):
            raise ValidationError(f"{field_name} contains invalid HTML/script tags")
        
        # Sanitize if needed
        if not allow_special:
            value = InputValidator._sanitize_string(value)
        
        return value
    
    @staticmethod
    def validate_integer(value: Any, field_name: str = "value", min_val: int = None, max_val: int = None) -> int:
        """Validate integer input."""
        try:
            if isinstance(value, str):
                value = int(value.strip())
            else:
                value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be an integer")
        
        if min_val is not None and value < min_val:
            raise ValidationError(f"{field_name} must be >= {min_val}")
        
        if max_val is not None and value > max_val:
            raise ValidationError(f"{field_name} must be <= {max_val}")
        
        return value
    
    @staticmethod
    def validate_list(value: Any, field_name: str = "value", max_items: int = 100) -> list:
        """Validate list input."""
        if not isinstance(value, list):
            raise ValidationError(f"{field_name} must be a list")
        
        if len(value) == 0:
            raise ValidationError(f"{field_name} cannot be empty")
        
        if len(value) > max_items:
            raise ValidationError(f"{field_name} cannot have more than {max_items} items")
        
        return value
    
    @staticmethod
    def _contains_sql_injection(value: str) -> bool:
        """Check if string contains SQL injection patterns."""
        value_upper = value.upper()
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def _contains_xss(value: str) -> bool:
        """Check if string contains XSS patterns."""
        for pattern in InputValidator.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def _sanitize_string(value: str) -> str:
        """Sanitize string by escaping dangerous characters."""
        dangerous = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '&': '&amp;',
            '\x00': '',
        }
        
        for char, escaped in dangerous.items():
            value = value.replace(char, escaped)
        
        return value


# Export validator instance
validator = InputValidator()
