"""
Security utilities for authentication, encryption, and JWT handling.

This module provides:
- JWT token generation and validation (HS256)
- Password hashing (bcrypt)
- HTTPS/TLS support
- CORS configuration
- Security headers
"""


from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import HTTPBearer
import secrets
import logging


from config import settings
#from core.logging import logger, setup_logging
from core.security import get_security_headers, get_cors_config
from core.exceptions import AppException, RateLimitExceededError




logger = logging.getLogger(__name__)

# ============================================
# PASSWORD HASHING
# ============================================
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Strong hashing: 12 rounds
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
        
    Raises:
        ValueError: If password is empty
    """
    if not password or len(password) < settings.PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters")
    
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False


# ============================================
# JWT TOKEN MANAGEMENT
# ============================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Dictionary of claims to encode
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
        
    Raises:
        ValueError: If data is invalid
    """
    if not data:
        raise ValueError("Token data cannot be empty")
    
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(16)  # JWT ID for token tracking
    })
    
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        logger.info(f"Token created for user: {data.get('sub', 'unknown')}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation error: {str(e)}")
        raise


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string to verify
        
    Returns:
        Dictionary of decoded claims
        
    Raises:
        JWTError: If token is invalid or expired
        ValueError: If token format is invalid
    """
    if not token:
        raise ValueError("Token cannot be empty")
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"Token verification failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected token error: {str(e)}")
        raise


def decode_token_unsafe(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode JWT token WITHOUT verification (for inspection only).
    
    WARNING: This does NOT verify the signature. Use only for inspection.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary of claims or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False}
        )
        return payload
    except Exception as e:
        logger.error(f"Token decode error: {str(e)}")
        return None


# ============================================
# SECURITY HEADERS
# ============================================

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=()"
}


def get_security_headers() -> Dict[str, str]:
    """
    Get security headers for HTTPS responses.
    
    Returns:
        Dictionary of security headers
    """
    return SECURITY_HEADERS.copy()


# ============================================
# CORS CONFIGURATION
# ============================================

def get_cors_config() -> Dict[str, Any]:
    """
    Get CORS configuration.
    
    Returns:
        Dictionary with CORS settings
    """
    return {
        "allow_origins": settings.CORS_ORIGINS,
        "allow_credentials": settings.CORS_ALLOW_CREDENTIALS,
        "allow_methods": settings.CORS_ALLOW_METHODS,
        "allow_headers": ["Content-Type", "Authorization", "Accept"],
        "expose_headers": ["Content-Type", "X-Total-Count"],
        "max_age": 3600
    }


# ============================================
# INPUT VALIDATION
# ============================================

def sanitize_input(value: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent XSS and injection.
    
    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
        
    Raises:
        ValueError: If input exceeds max length
    """
    if not value:
        return ""
    
    if len(value) > max_length:
        raise ValueError(f"Input exceeds maximum length of {max_length}")
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # HTML escape dangerous characters
    dangerous_chars = {
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '&': '&amp;'
    }
    
    for char, escaped in dangerous_chars.items():
        value = value.replace(char, escaped)
    
    return value.strip()


# ============================================
# RATE LIMITING (Redis-based)
# ============================================

async def check_rate_limit(
    redis_client,
    key: str,
    limit: int = settings.RATE_LIMIT_REQUESTS,
    window: int = settings.RATE_LIMIT_WINDOW_SECONDS
) -> bool:
    """
    Check if a request is within rate limit using sliding window algorithm.
    
    Args:
        redis_client: Redis connection
        key: Unique key for rate limiting (e.g., user_id or IP)
        limit: Maximum requests allowed
        window: Time window in seconds
        
    Returns:
        True if within limit, False if limit exceeded
    """
    if not settings.RATE_LIMIT_ENABLED:
        return True
    
    try:
        current = await redis_client.incr(key)
        
        if current == 1:
            await redis_client.expire(key, window)
        
        return current <= limit
    except Exception as e:
        logger.error(f"Rate limit check error: {str(e)}")
        # Fail open: allow request if redis is down
        return True


# ============================================
# CONSTANT DEFINITIONS
# ============================================

security_scheme = HTTPBearer()
