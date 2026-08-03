"""Pytest configuration and shared fixtures."""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from datetime import datetime, timedelta
import os

# Database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Async
import httpx
from httpx import AsyncClient

# App
from fastapi import FastAPI
from main import create_app
from config import Settings
from core.security import create_access_token, hash_password
from db.models import Base, User

# Faker for test data
from faker import Faker
faker = Faker()


# ============================================
# DATABASE FIXTURE (SQLite in-memory)
# ============================================

@pytest.fixture(scope="session")
def database_url():
    """Return in-memory SQLite URL for testing."""
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine(database_url):
    """Create SQLAlchemy engine for tests."""
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    """Create a new database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


# ============================================
# SETTINGS OVERRIDE
# ============================================

@pytest.fixture
def test_settings() -> Settings:
    """Override settings for testing."""
    return Settings(
        ENVIRONMENT="testing",
        DEBUG=True,
        SERVER_ID="test-server",
        DATABASE_URL="sqlite:///:memory:",
        REDIS_HOST="localhost",
        REDIS_PORT=6379,
        GLPI_BASE_URL="http://test.glpi.local/apirest.php",
        GLPI_APP_TOKEN="test-app-token-12345",
        GLPI_USER="test_user",
        GLPI_PASSWORD="TestPassword123!",
        OLLAMA_BASE_URL="http://localhost:11434",
        OLLAMA_MODEL="mistral",
        JWT_SECRET="test-jwt-secret-at-least-32-characters-long-ok",
        LOG_LEVEL="DEBUG",
    )


# ============================================
# FASTAPI APP FIXTURE
# ============================================

@pytest.fixture
def app(test_settings, monkeypatch) -> FastAPI:
    """Create FastAPI app with test settings."""
    # Monkeypatch settings
    monkeypatch.setattr("config.settings", test_settings)
    
    # Create app
    app = create_app()
    return app


# ============================================
# HTTP CLIENT FIXTURE
# ============================================

@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ============================================
# SYNC CLIENT FOR PYTEST (non-async tests)
# ============================================

@pytest.fixture
def client(app: FastAPI):
    """Create sync HTTP client for testing."""
    from fastapi.testclient import TestClient
    return TestClient(app)


# ============================================
# EVENT LOOP (for async tests)
# ============================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================
# USER FACTORY
# ============================================

@pytest.fixture
def user_factory(db_session: Session):
    """Factory for creating test users."""
    
    def _create_user(
        username: str = None,
        email: str = None,
        password: str = "TestPassword123!",
        is_active: bool = True,
        is_admin: bool = False
    ) -> User:
        username = username or faker.user_name()
        email = email or faker.email()
        
        user = User(
            user_id=f"glpi_{faker.random_int(1000, 9999)}",
            username=username,
            email=email,
            password_hash=hash_password(password),
            is_active=is_active,
            is_admin=is_admin,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        return user
    
    return _create_user


# ============================================
# TOKEN FACTORY
# ============================================

@pytest.fixture
def token_factory(test_settings: Settings):
    """Factory for creating test JWT tokens."""
    
    def _create_token(
        sub: str = "testuser",
        token_type: str = "access",
        expires_delta: timedelta = None,
        is_expired: bool = False
    ) -> str:
        
        if expires_delta is None:
            if token_type == "access":
                expires_delta = timedelta(minutes=test_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            else:
                expires_delta = timedelta(days=test_settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
        # If expired, use negative delta
        if is_expired:
            expires_delta = timedelta(hours=-1)
        
        token_data = {
            "sub": sub,
            "type": token_type
        }
        
        token = create_access_token(
            data=token_data,
            expires_delta=expires_delta
        )
        
        return token
    
    return _create_token


# ============================================
# AUTHENTICATED CLIENT
# ============================================

@pytest.fixture
async def authenticated_client(async_client: AsyncClient, token_factory) -> AsyncClient:
    """Create HTTP client with valid JWT token."""
    access_token = token_factory(sub="testuser", token_type="access")
    async_client.headers.update({"Authorization": f"Bearer {access_token}"})
    return async_client


@pytest.fixture
def authenticated_sync_client(client, token_factory):
    """Create sync HTTP client with valid JWT token."""
    access_token = token_factory(sub="testuser", token_type="access")
    client.headers.update({"Authorization": f"Bearer {access_token}"})
    return client


# ============================================
# SAMPLE DATA
# ============================================

@pytest.fixture
def sample_user_data():
    """Sample user registration data."""
    return {
        "username": "testuser",
        "password": "TestPassword123!",
    }


@pytest.fixture
def sample_strong_password():
    """Sample strong password."""
    return "MySecurePass123!"


@pytest.fixture
def sample_weak_passwords():
    """Sample weak passwords for testing."""
    return [
        "weak",                      # Too short
        "UPPERCASE123!",             # No lowercase
        "lowercase123!",             # No uppercase
        "NoNumbers!",                # No digits
        "NoSpecial123",              # No special chars
        "",                          # Empty
    ]


@pytest.fixture
def sample_emails():
    """Sample emails for testing."""
    return {
        "valid": [
            "user@example.com",
            "test.user@domain.co.uk",
            "user+tag@example.com",
        ],
        "invalid": [
            "invalid",
            "invalid@",
            "@invalid.com",
            "invalid@.com",
            "invalid@domain",
            "a" * 250 + "@example.com",  # Too long
        ],
    }


@pytest.fixture
def sample_usernames():
    """Sample usernames for testing."""
    return {
        "valid": [
            "user",
            "test_user",
            "user-123",
            "Admin123",
        ],
        "invalid": [
            "ab",                      # Too short
            "user@email",              # Special char
            "user name",               # Space
            "user$special",            # Special char
            "",                        # Empty
        ],
    }


# ============================================
# SQL INJECTION PAYLOADS
# ============================================

@pytest.fixture
def sql_injection_payloads():
    """SQL injection payloads for security testing."""
    return [
        "' OR '1'='1",
        "'; DROP TABLE users--",
        "1; DELETE FROM tickets",
        "UNION SELECT * FROM passwords",
        "UNION ALL SELECT NULL,NULL,NULL",
        "'; EXEC xp_cmdshell 'whoami'--",
        "admin'--",
        "' OR 1=1--",
        "1' UNION ALL SELECT NULL--",
        "INSERT INTO users VALUES ('hack',1)",
        "UPDATE users SET admin=1",
        "/* comment */ SELECT * FROM",
    ]


# ============================================
# XSS PAYLOADS
# ============================================

@pytest.fixture
def xss_payloads():
    """XSS payloads for security testing."""
    return [
        "<script>alert('XSS')</script>",
        "javascript:alert('XSS')",
        "<img src=x onerror=alert('XSS')>",
        "<iframe src=\"javascript:alert('XSS')\">",
        "<embed src=\"javascript:alert('XSS')\">",
        "<object data=\"javascript:alert\">",
        "<svg/onload=alert('XSS')>",
        "<body onload=alert('XSS')>",
        "<input onfocus=alert('XSS')>",
        "<marquee onstart=alert('XSS')>",
        "<img src='' onclick=alert('XSS')>",
        "<style>@import 'javascript:alert'</style>",
    ]


# ============================================
# MOCK DATA FOR GLPI
# ============================================

@pytest.fixture
def mock_glpi_ticket():
    """Mock GLPI ticket data."""
    return {
        "id": 123,
        "name": "Sistema de acceso lento",
        "status": "new",
        "priority": "high",
        "urgency": "high",
        "impact": "high",
        "date": "2026-08-03",
        "description": "El sistema de acceso GLPI está respondiendo lentamente...",
        "assigned_to": "admin",
    }


@pytest.fixture
def mock_glpi_search_results():
    """Mock GLPI search results."""
    return [
        {
            "id": 123,
            "name": "Sistema de acceso lento",
            "status": "new",
            "priority": "high",
            "date": "2026-08-03",
        },
        {
            "id": 124,
            "name": "Error en base de datos",
            "status": "assigned",
            "priority": "medium",
            "date": "2026-08-02",
        },
    ]


# ============================================
# MOCK DATA FOR OLLAMA
# ============================================

@pytest.fixture
def mock_ollama_response():
    """Mock Ollama LLM response."""
    return "Los tickets de acceso están siendo procesados. El sistema está optimizando consultas."


@pytest.fixture
def mock_chat_messages():
    """Mock chat message history."""
    return [
        {"role": "user", "content": "¿Cuál es el estado del ticket 123?"},
        {"role": "assistant", "content": "El ticket 123 está en estado 'new' con prioridad alta."},
        {"role": "user", "content": "¿Cuánto tiempo tarda normalmente?"},
    ]


# ============================================
# CLEANUP
# ============================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Add cleanup code here if needed
