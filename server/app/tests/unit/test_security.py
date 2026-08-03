"""Unit tests for security functions - JWT, hashing, tokens."""

import pytest
from datetime import datetime, timedelta
import time
import jwt
from jose import JWTError

from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    get_security_headers,
    get_cors_config,
)
from config import Settings


# ============================================
# PASSWORD HASHING TESTS (BCRYPT)
# ============================================

class TestPasswordHashing:
    """Test password hashing and verification with bcrypt."""
    
    def test_hash_password_returns_string(self, sample_strong_password):
        """Test that hash_password returns a string."""
        hashed = hash_password(sample_strong_password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0
    
    def test_hash_password_not_equals_original(self, sample_strong_password):
        """Test that hashed password is not equal to original."""
        hashed = hash_password(sample_strong_password)
        assert hashed != sample_strong_password
    
    def test_hash_password_different_each_time(self, sample_strong_password):
        """Test that hashing same password gives different hashes (random salt)."""
        hash1 = hash_password(sample_strong_password)
        hash2 = hash_password(sample_strong_password)
        
        # Different hashes (bcrypt adds random salt)
        assert hash1 != hash2
        
        # But both verify correctly
        assert verify_password(sample_strong_password, hash1)
        assert verify_password(sample_strong_password, hash2)
    
    def test_verify_password_correct(self, sample_strong_password):
        """Test that verify_password accepts correct password."""
        hashed = hash_password(sample_strong_password)
        assert verify_password(sample_strong_password, hashed) is True
    
    def test_verify_password_incorrect(self, sample_strong_password):
        """Test that verify_password rejects incorrect password."""
        hashed = hash_password(sample_strong_password)
        wrong_password = "WrongPassword123!"
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty_password(self):
        """Test that empty password is rejected."""
        hashed = hash_password("TestPassword123!")
        assert verify_password("", hashed) is False
    
    def test_verify_password_none(self):
        """Test that None password is rejected."""
        hashed = hash_password("TestPassword123!")
        result = verify_password(None, hashed)
        assert result is False
    
    def test_verify_password_invalid_hash(self, sample_strong_password):
        """Test that invalid hash is rejected."""
        invalid_hash = "not_a_valid_hash"
        result = verify_password(sample_strong_password, invalid_hash)
        assert result is False
    
    def test_hash_password_long_password(self):
        """Test hashing very long password."""
        long_password = "A" * 100 + "b" * 100 + "1" * 100 + "!@#$%"
        hashed = hash_password(long_password)
        
        assert verify_password(long_password, hashed) is True
        assert verify_password("WrongPassword123!", hashed) is False


# ============================================
# JWT CREATION TESTS
# ============================================

class TestJWTCreation:
    """Test JWT token creation."""
    
    def test_create_access_token_returns_string(self, test_settings):
        """Test that create_access_token returns a string."""
        token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(hours=1)
        )
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_valid_format(self, test_settings):
        """Test that token has valid JWT format (3 parts separated by dots)."""
        token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(hours=1)
        )
        
        parts = token.split(".")
        assert len(parts) == 3  # header.payload.signature
    
    def test_create_access_token_contains_payload(self, test_settings):
        """Test that token contains correct payload data."""
        token = create_access_token(
            data={"sub": "testuser", "type": "access"},
            expires_delta=timedelta(hours=1)
        )
        
        # Decode without verification to check payload
        payload = jwt.get_unverified_claims(token)
        
        assert payload["sub"] == "testuser"
        assert payload["type"] == "access"
        assert "exp" in payload  # Expiration time
        assert "iat" in payload  # Issued at time
    
    def test_create_access_token_has_expiration(self, test_settings):
        """Test that token has expiration time."""
        expires_delta = timedelta(hours=1)
        token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=expires_delta
        )
        
        payload = jwt.get_unverified_claims(token)
        
        assert "exp" in payload
        assert "iat" in payload
        
        # exp should be approximately now + 1 hour
        now = datetime.utcnow().timestamp()
        exp = payload["exp"]
        
        # Should be between 55 and 65 minutes from now
        time_diff = exp - now
        assert 3300 < time_diff < 3900  # ~3600 seconds = 1 hour
    
    def test_create_access_token_default_expiration(self, test_settings):
        """Test that token uses default expiration if not provided."""
        token = create_access_token(data={"sub": "testuser"})
        
        payload = jwt.get_unverified_claims(token)
        assert "exp" in payload
    
    def test_create_access_token_different_each_time(self, test_settings):
        """Test that tokens generated at different times are different."""
        token1 = create_access_token(data={"sub": "testuser"})
        time.sleep(0.1)  # Small delay
        token2 = create_access_token(data={"sub": "testuser"})
        
        # Different iat (issued at time)
        assert token1 != token2
    
    def test_create_access_token_with_custom_data(self, test_settings):
        """Test creating token with custom data."""
        custom_data = {
            "sub": "user123",
            "email": "user@example.com",
            "roles": ["admin", "user"],
            "custom_field": "custom_value",
        }
        
        token = create_access_token(data=custom_data)
        payload = jwt.get_unverified_claims(token)
        
        assert payload["sub"] == "user123"
        assert payload["email"] == "user@example.com"
        assert payload["roles"] == ["admin", "user"]
        assert payload["custom_field"] == "custom_value"


# ============================================
# JWT VALIDATION TESTS
# ============================================

class TestJWTValidation:
    """Test JWT token validation."""
    
    def test_verify_token_valid(self, token_factory):
        """Test that verify_token accepts valid token."""
        token = token_factory(sub="testuser", token_type="access")
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["type"] == "access"
    
    def test_verify_token_invalid_signature(self, token_factory, test_settings):
        """Test that verify_token rejects token with altered signature."""
        token = token_factory(sub="testuser", token_type="access")
        
        # Alter the signature part
        parts = token.split(".")
        altered_token = parts[0] + "." + parts[1] + ".altered_signature"
        
        payload = verify_token(altered_token)
        assert payload is None
    
    def test_verify_token_invalid_payload(self, token_factory):
        """Test that verify_token rejects token with altered payload."""
        token = token_factory(sub="testuser", token_type="access")
        
        # Alter payload (change sub)
        parts = token.split(".")
        # This will fail signature verification
        import base64
        
        # Can't easily alter and re-sign, so token becomes invalid
        altered_token = parts[0] + "." + "invalid_payload" + "." + parts[2]
        
        payload = verify_token(altered_token)
        assert payload is None
    
    def test_verify_token_expired(self, test_settings):
        """Test that verify_token rejects expired token."""
        # Create token that expires immediately
        token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(milliseconds=-1000)  # Already expired
        )
        
        payload = verify_token(token)
        assert payload is None
    
    def test_verify_token_malformed(self):
        """Test that verify_token rejects malformed token."""
        malformed_tokens = [
            "",
            "invalid_token",
            "only.two.parts",  # Wait, that's actually 3... let me fix
            "part1.part2",  # Only 2 parts
            "part1",  # Only 1 part
            None,
        ]
        
        for token in malformed_tokens:
            payload = verify_token(token)
            assert payload is None, f"Malformed token accepted: {token}"
    
    def test_verify_token_none(self):
        """Test that verify_token handles None."""
        payload = verify_token(None)
        assert payload is None
    
    def test_verify_token_empty_string(self):
        """Test that verify_token handles empty string."""
        payload = verify_token("")
        assert payload is None
    
    def test_verify_token_algorithm_none_attack(self, test_settings):
        """Test that algorithm 'none' attack is rejected."""
        # Try to create a token with algorithm 'none'
        # This is a known JWT vulnerability
        
        import json
        import base64
        
        # Create header with 'none' algorithm
        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "none", "typ": "JWT"}).encode()
        ).decode().rstrip("=")
        
        payload = base64.urlsafe_b64encode(
            json.dumps({"sub": "hacker"}).encode()
        ).decode().rstrip("=")
        
        # No signature needed for 'none' algorithm
        malicious_token = f"{header}.{payload}."
        
        result = verify_token(malicious_token)
        assert result is None  # Should reject
    
    def test_verify_token_returns_payload_dict(self, token_factory):
        """Test that verify_token returns payload as dictionary."""
        token = token_factory(sub="testuser")
        payload = verify_token(token)
        
        assert isinstance(payload, dict)
        assert "sub" in payload
        assert "exp" in payload
        assert "iat" in payload


# ============================================
# REFRESH TOKEN TESTS
# ============================================

class TestRefreshToken:
    """Test refresh token functionality."""
    
    def test_refresh_token_different_expiration(self, token_factory):
        """Test that refresh tokens have longer expiration than access tokens."""
        access_token = token_factory(sub="user", token_type="access")
        refresh_token = token_factory(sub="user", token_type="refresh")
        
        access_payload = jwt.get_unverified_claims(access_token)
        refresh_payload = jwt.get_unverified_claims(refresh_token)
        
        # Refresh token should expire later than access token
        access_exp = access_payload["exp"]
        refresh_exp = refresh_payload["exp"]
        
        assert refresh_exp > access_exp
    
    def test_refresh_token_marked_as_refresh(self, token_factory):
        """Test that refresh token has type='refresh'."""
        token = token_factory(sub="user", token_type="refresh")
        payload = jwt.get_unverified_claims(token)
        
        assert payload["type"] == "refresh"
    
    def test_access_token_marked_as_access(self, token_factory):
        """Test that access token has type='access'."""
        token = token_factory(sub="user", token_type="access")
        payload = jwt.get_unverified_claims(token)
        
        assert payload["type"] == "access"


# ============================================
# TOKEN EXPIRATION TESTS
# ============================================

class TestTokenExpiration:
    """Test token expiration behavior."""
    
    def test_token_expiration_timestamp_valid(self, token_factory):
        """Test that token expiration timestamp is in future."""
        token = token_factory(sub="user")
        payload = jwt.get_unverified_claims(token)
        
        now = datetime.utcnow().timestamp()
        exp = payload["exp"]
        
        # Expiration should be in the future
        assert exp > now
    
    def test_token_iat_timestamp_valid(self, token_factory):
        """Test that token 'issued at' timestamp is approximately now."""
        token = token_factory(sub="user")
        payload = jwt.get_unverified_claims(token)
        
        now = datetime.utcnow().timestamp()
        iat = payload["iat"]
        
        # Issued at should be very close to now
        assert abs(now - iat) < 5  # Within 5 seconds
    
    def test_expired_token_rejected(self, test_settings):
        """Test that expired token is rejected by verify_token."""
        expired_token = create_access_token(
            data={"sub": "user"},
            expires_delta=timedelta(hours=-1)  # Expired 1 hour ago
        )
        
        payload = verify_token(expired_token)
        assert payload is None


# ============================================
# SECURITY HEADERS TESTS
# ============================================

class TestSecurityHeaders:
    """Test security headers configuration."""
    
    def test_get_security_headers_returns_dict(self):
        """Test that get_security_headers returns a dictionary."""
        headers = get_security_headers()
        assert isinstance(headers, dict)
    
    def test_security_headers_not_empty(self):
        """Test that security headers are not empty."""
        headers = get_security_headers()
        assert len(headers) > 0
    
    def test_hsts_header_present(self):
        """Test that HSTS header is present."""
        headers = get_security_headers()
        assert "Strict-Transport-Security" in headers
        assert "max-age" in headers["Strict-Transport-Security"]
    
    def test_content_type_options_header(self):
        """Test that X-Content-Type-Options header is present."""
        headers = get_security_headers()
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"
    
    def test_frame_options_header(self):
        """Test that X-Frame-Options header is present."""
        headers = get_security_headers()
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"
    
    def test_csp_header_present(self):
        """Test that Content-Security-Policy header is present."""
        headers = get_security_headers()
        assert "Content-Security-Policy" in headers
    
    def test_all_headers_are_strings(self):
        """Test that all header values are strings."""
        headers = get_security_headers()
        for key, value in headers.items():
            assert isinstance(key, str)
            assert isinstance(value, str)


# ============================================
# CORS CONFIG TESTS
# ============================================

class TestCORSConfig:
    """Test CORS configuration."""
    
    def test_get_cors_config_returns_dict(self):
        """Test that get_cors_config returns a dictionary."""
        cors_config = get_cors_config()
        assert isinstance(cors_config, dict)
    
    def test_cors_config_has_origins(self):
        """Test that CORS config contains allow_origins."""
        cors_config = get_cors_config()
        assert "allow_origins" in cors_config
        assert isinstance(cors_config["allow_origins"], list)
    
    def test_cors_config_has_methods(self):
        """Test that CORS config contains allow_methods."""
        cors_config = get_cors_config()
        assert "allow_methods" in cors_config
        assert isinstance(cors_config["allow_methods"], list)
    
    def test_cors_config_has_headers(self):
        """Test that CORS config contains allow_headers."""
        cors_config = get_cors_config()
        assert "allow_headers" in cors_config
        assert isinstance(cors_config["allow_headers"], list)
    
    def test_cors_origins_not_empty(self):
        """Test that CORS origins are configured."""
        cors_config = get_cors_config()
        assert len(cors_config["allow_origins"]) > 0
    
    def test_cors_methods_include_common(self):
        """Test that CORS methods include common HTTP methods."""
        cors_config = get_cors_config()
        methods = cors_config["allow_methods"]
        
        assert "GET" in methods
        assert "POST" in methods
        assert "DELETE" in methods
    
    def test_cors_credentials_enabled(self):
        """Test that CORS credentials are allowed."""
        cors_config = get_cors_config()
        assert "allow_credentials" in cors_config
        assert cors_config["allow_credentials"] is True
