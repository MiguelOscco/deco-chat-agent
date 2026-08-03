"""Pydantic schemas for authentication."""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """Login request schema."""
    
    username: str = Field(..., min_length=3, max_length=100, description="GLPI username")
    password: str = Field(..., min_length=8, max_length=255, description="GLPI password")
    
    class Config:
        example = {
            "username": "admin",
            "password": "SecurePassword123!"
        }


class TokenResponse(BaseModel):
    """JWT token response schema."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="Refresh token for getting new access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Expiration time in seconds")
    
    class Config:
        example = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 3600
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    
    refresh_token: str = Field(..., description="Refresh token")
    
    class Config:
        example = {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }


class UserResponse(BaseModel):
    """User response schema."""
    
    id: int = Field(..., description="User ID")
    user_id: str = Field(..., description="GLPI user ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    is_active: bool = Field(default=True, description="User is active")
    is_admin: bool = Field(default=False, description="User is admin")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True
        example = {
            "id": 1,
            "user_id": "glpi_123",
            "username": "admin",
            "email": "admin@deco.com",
            "is_active": True,
            "is_admin": True,
            "created_at": "2026-08-03T10:30:00"
        }


class LoginResponse(BaseModel):
    """Complete login response schema."""
    
    user: UserResponse = Field(..., description="User information")
    tokens: TokenResponse = Field(..., description="JWT tokens")
    
    class Config:
        example = {
            "user": {
                "id": 1,
                "user_id": "glpi_123",
                "username": "admin",
                "email": "admin@deco.com",
                "is_active": True,
                "is_admin": True,
                "created_at": "2026-08-03T10:30:00"
            },
            "tokens": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }


class LogoutRequest(BaseModel):
    """Logout request schema."""
    
    refresh_token: Optional[str] = Field(None, description="Refresh token to revoke")


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""
    
    current_password: str = Field(..., min_length=8, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Confirm new password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        if not any(c in "@$!%*?&" for c in v):
            raise ValueError("Password must contain special character (@$!%*?&)")
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Validate passwords match."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError("Passwords do not match")
        return v
    
    class Config:
        example = {
            "current_password": "OldPassword123!",
            "new_password": "NewPassword456!",
            "confirm_password": "NewPassword456!"
        }


class TokenPayload(BaseModel):
    """JWT token payload schema (for validation)."""
    
    sub: str = Field(..., description="Subject (user_id)")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    jti: str = Field(..., description="JWT ID (unique identifier)")
    type: str = Field(default="access", description="Token type (access or refresh)")
    
    class Config:
        example = {
            "sub": "1",
            "exp": 1691049000,
            "iat": 1691045400,
            "jti": "abc123def456",
            "type": "access"
        }


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional details")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    
    class Config:
        example = {
            "error": "INVALID_CREDENTIALS",
            "message": "Username or password is incorrect",
            "details": None,
            "request_id": "abc123xyz789"
        }
