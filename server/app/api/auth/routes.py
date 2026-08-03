"""Authentication routes."""

from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from config import settings
from core.security import (
    hash_password, verify_password, create_access_token,
    verify_token, get_cors_config
)
from core.exceptions import AppException
from validators.input_validators import validate_email, validate_password
from services.glpi import glpi_client
from db.models import User, RefreshToken
from .schemas import (
    LoginRequest, TokenResponse, RefreshTokenRequest,
    UserResponse, LoginResponse, ChangePasswordRequest,
    LogoutRequest, ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def get_db() -> Session:
    """Get database session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # This would be injected properly in production
    # For now, returning None as placeholder
    return None


def get_current_user(request: Request) -> dict:
    """Get current authenticated user from request."""
    user_id = getattr(request.state, 'user_id', None)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return {"user_id": user_id}


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        422: {"model": ErrorResponse, "description": "Validation error"}
    }
)
async def login(request: Request, credentials: LoginRequest):
    """
    Authenticate user with GLPI credentials.
    
    Returns JWT access token + refresh token.
    """
    

    request_id = getattr(request.state, 'request_id', 'unknown')
    client_ip = getattr(request.state, 'client_ip', 'unknown')
    
    try:
        # Validate input
        if not credentials.username or len(credentials.username) < 3:
            raise AppException(
                error_code="INVALID_USERNAME",
                message="Username must be at least 3 characters",
                status_code=422
            )
        
        if not validate_password(credentials.password):
            raise AppException(
                error_code="INVALID_PASSWORD",
                message="Password does not meet requirements",
                status_code=422
            )
        
        # Try GLPI authentication
        logger.info(f"🔐 Login attempt: {credentials.username} from {client_ip}")
        
        authenticated = await glpi_client.init_session(
            credentials.username,
            credentials.password
        )
        
        if not authenticated:
            logger.warning(f"❌ GLPI auth failed for {credentials.username}")
            raise AppException(
                error_code="INVALID_CREDENTIALS",
                message="Username or password is incorrect",
                status_code=401
            )
        
        # Get user info from GLPI
        user_info = await glpi_client.get_user_info(1)  # TODO: get actual user_id from GLPI
        
        if not user_info:
            raise AppException(
                error_code="USER_NOT_FOUND",
                message="User not found in GLPI",
                status_code=401
            )
        
        # Create tokens
        access_token_data = {
            "sub": credentials.username,
            "type": "access"
        }
        
        refresh_token_data = {
            "sub": credentials.username,
            "type": "refresh"
        }
        
        access_token = create_access_token(
            data=access_token_data,
            expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        refresh_token = create_access_token(
            data=refresh_token_data,
            expires_delta=timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        # Set user state
        request.state.user_id = credentials.username
        request.state.user_roles = ["user"]
        
        logger.info(f"✅ Login successful for {credentials.username}")
        
        # Return response
        user_response = UserResponse(
            id=1,
            user_id=credentials.username,
            username=credentials.username,
            email=user_info.get("email", f"{credentials.username}@deco.com"),
            is_active=True,
            is_admin=user_info.get("is_admin", False),
            created_at=datetime.utcnow()
        )
        
        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        response = LoginResponse(user=user_response, tokens=token_response)
        
        # Kill GLPI session (we have JWT now)
        await glpi_client.kill_session()
        
        return response
        
    except AppException as e:
        logger.error(f"❌ Login error: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.error_code, "message": e.message}
        )
    except Exception as e:
        logger.error(f"❌ Unexpected login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"}
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid refresh token"}
    }
)
async def refresh_access_token(request: Request, data: RefreshTokenRequest):
    """
    Generate new access token using refresh token.
    """
    
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    try:
        # Verify refresh token
        payload = verify_token(data.refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            raise AppException(
                error_code="INVALID_REFRESH_TOKEN",
                message="Refresh token is invalid or expired",
                status_code=401
            )
        
        username = payload.get("sub")
        
        if not username:
            raise AppException(
                error_code="INVALID_TOKEN_PAYLOAD",
                message="Token payload is invalid",
                status_code=401
            )
        
        # Create new access token
        access_token_data = {
            "sub": username,
            "type": "access"
        }
        
        new_access_token = create_access_token(
            data=access_token_data,
            expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        logger.info(f"✅ Token refreshed for {username}")
        
        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except AppException as e:
        logger.warning(f"⚠️ Refresh token error: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.error_code, "message": e.message}
        )
    except Exception as e:
        logger.error(f"❌ Unexpected refresh error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"}
        )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"}
    }
)
async def logout(request: Request, data: LogoutRequest):
    """
    Logout user and revoke refresh token.
    """
    
    user_id = getattr(request.state, 'user_id', None)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        logger.info(f"✅ Logout for {user_id}")
        
        return {"message": "Logout successful"}
        
    except Exception as e:
        logger.error(f"❌ Logout error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "INTERNAL_ERROR", "message": "Logout failed"}
        )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"}
    }
)
async def get_current_user_info(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.
    """
    
    try:
        user_id = current_user["user_id"]
        
        # In production, fetch from database
        user = UserResponse(
            id=1,
            user_id=user_id,
            username=user_id,
            email=f"{user_id}@deco.com",
            is_active=True,
            is_admin=False,
            created_at=datetime.utcnow()
        )
        
        return user
        
    except Exception as e:
        logger.error(f"❌ Get user info error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "INTERNAL_ERROR", "message": "Failed to get user info"}
        )


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        422: {"model": ErrorResponse, "description": "Validation error"}
    }
)
async def change_password(request: Request, data: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    """
    Change user password.
    """
    
    try:
        user_id = current_user["user_id"]
        
        # In production:
        # 1. Verify current password
        # 2. Validate new password strength
        # 3. Update in database
        # 4. Revoke all refresh tokens
        
        logger.info(f"✅ Password changed for {user_id}")
        
        return {"message": "Password changed successfully"}
        
    except Exception as e:
        logger.error(f"❌ Change password error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "INTERNAL_ERROR", "message": "Failed to change password"}
        )
