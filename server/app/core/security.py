
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt
from jose.exceptions import JWTError
from passlib.context import CryptContext
import secrets
from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12)

def hash_password(password: str) -> str:
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        raise ValueError("Password too short")
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except:
        return False

def create_access_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "jti": secrets.token_urlsafe(16)})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def verify_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])

def get_security_headers() -> Dict[str, str]:
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
    }

def get_cors_config() -> Dict[str, Any]:
    return {
        "allow_origins": settings.CORS_ORIGINS,
        "allow_credentials": settings.CORS_ALLOW_CREDENTIALS,
        "allow_methods": settings.CORS_ALLOW_METHODS,
        "allow_headers": ["Content-Type", "Authorization"],
    }
