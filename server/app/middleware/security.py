"""Enhanced security middleware (CSRF, security headers, etc)."""

from fastapi import Request
from fastapi.responses import JSONResponse
import secrets
import logging
from typing import Callable
from config import settings

logger = logging.getLogger(__name__)


class CSRFProtection:
    """CSRF token generation and validation."""
    
    TOKEN_LENGTH = 32
    HEADER_NAME = "X-CSRF-Token"
    COOKIE_NAME = "csrf_token"
    
    @staticmethod
    def generate_token() -> str:
        """Generate cryptographically secure CSRF token."""
        return secrets.token_urlsafe(CSRFProtection.TOKEN_LENGTH)
    
    @staticmethod
    def validate_token(request_token: str, session_token: str) -> bool:
        """Validate CSRF token using constant-time comparison."""
        if not request_token or not session_token:
            return False
        
        # Use constant-time comparison to prevent timing attacks
        return secrets.compare_digest(request_token, session_token)


class SecurityHeadersMiddleware:
    """Middleware for enhanced security headers."""
    
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next: Callable):
        """Add security headers to response."""
        response = await call_next(request)
        
        # Content Security Policy - strict by default
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        
        # Additional security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
        
        # HSTS - only in production with HTTPS
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        return response


class CSRFMiddleware:
    """Middleware for CSRF protection."""
    
    def __init__(self, app, excluded_paths: list = None):
        self.app = app
        self.excluded_paths = excluded_paths or [
            "/health",
            "/health/ready",
            "/health/live",
            "/api/docs",
            "/api/redoc",
            "/openapi.json"
        ]
    
    async def __call__(self, request: Request, call_next: Callable):
        """Validate CSRF token for state-changing requests."""
        
        # Skip for safe methods
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return await call_next(request)
        
        # Skip for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Skip for health checks
        if "/health" in request.url.path:
            return await call_next(request)
        
        # Get CSRF token from request
        csrf_token = None
        
        # 1. Check header
        csrf_token = request.headers.get("X-CSRF-Token")
        
        # 2. Check form data if header not found
        if not csrf_token:
            try:
                form_data = await request.form()
                csrf_token = form_data.get("csrf_token")
            except:
                pass
        
        # 3. Check query parameter (less secure, for special cases)
        if not csrf_token:
            csrf_token = request.query_params.get("csrf_token")
        
        if not csrf_token:
            logger.warning(f"Missing CSRF token for {request.method} {request.url.path}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "CSRF_TOKEN_MISSING",
                    "message": "CSRF token is required for this request"
                }
            )
        
        # Get session token from cookie (validated by auth middleware)
        session_csrf = request.cookies.get("csrf_token")
        
        if not session_csrf:
            logger.warning(f"Missing session CSRF token for {request.url.path}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "CSRF_SESSION_INVALID",
                    "message": "Invalid or expired CSRF session"
                }
            )
        
        # Validate token
        if not CSRFProtection.validate_token(csrf_token, session_csrf):
            logger.warning(f"Invalid CSRF token for {request.url.path}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "CSRF_TOKEN_INVALID",
                    "message": "CSRF token validation failed"
                }
            )
        
        # Token valid, proceed
        return await call_next(request)


class SecurityContextMiddleware:
    """Middleware to add security context to request."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next: Callable):
        """Add security context to request state."""
        
        # Add request ID if not present
        request.state.request_id = request.headers.get(
            "X-Request-ID",
            secrets.token_urlsafe(8)
        )
        
        # Add client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check for X-Forwarded-For (behind proxy)
        if "X-Forwarded-For" in request.headers:
            # Take first IP from list (trusted proxy)
            forwarded_ips = request.headers["X-Forwarded-For"].split(",")
            client_ip = forwarded_ips[0].strip()
        
        request.state.client_ip = client_ip
        
        # Add current user (will be set by auth middleware)
        request.state.user_id = None
        request.state.user_roles = []
        
        # Add CSRF token if GET request (for forms)
        if request.method == "GET":
            request.state.csrf_token = CSRFProtection.generate_token()
        
        response = await call_next(request)
        
        # Add CSRF token to cookie if generated
        if hasattr(request.state, "csrf_token"):
            response.set_cookie(
                key="csrf_token",
                value=request.state.csrf_token,
                httponly=False,  # JS needs to read it for headers
                secure=settings.ENVIRONMENT == "production",
                samesite="strict",
                max_age=3600  # 1 hour
            )
        
        return response


class IPWhitelistMiddleware:
    """Optional IP whitelist middleware for admin endpoints."""
    
    def __init__(self, app, allowed_ips: list = None, enabled: bool = False):
        self.app = app
        self.allowed_ips = set(allowed_ips or [])
        self.enabled = enabled
    
    async def __call__(self, request: Request, call_next: Callable):
        """Check if client IP is whitelisted."""
        
        if not self.enabled:
            return await call_next(request)
        
        # Skip for public endpoints
        if not request.url.path.startswith("/api/admin"):
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        
        if client_ip not in self.allowed_ips:
            logger.warning(f"IP {client_ip} not whitelisted for {request.url.path}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "IP_NOT_WHITELISTED",
                    "message": "Your IP address is not authorized to access this resource"
                }
            )
        
        return await call_next(request)
