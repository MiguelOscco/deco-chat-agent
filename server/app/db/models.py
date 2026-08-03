"""SQLAlchemy database models."""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    """User model - for authentication."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True, nullable=False)  # GLPI user_id
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_username', 'username'),
        Index('idx_email', 'email'),
        Index('idx_active', 'is_active'),
    )


class RefreshToken(Base):
    """Refresh token model - for JWT refresh mechanism."""
    
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token_jti = Column(String(100), unique=True, index=True, nullable=False)  # JWT JTI (unique ID)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False)
    is_revoked = Column(Boolean, default=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_user_id_revoked', 'user_id', 'is_revoked'),
    )


class SearchQuery(Base):
    """Search query model - for audit & analytics."""
    
    __tablename__ = "search_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(String(50), unique=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    query = Column(String(500), nullable=False)
    results_count = Column(Integer, default=0)
    execution_time_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_user_id_date', 'user_id', 'created_at'),
    )


class ChatMessage(Base):
    """Chat message model - for conversation history."""
    
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(50), unique=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(String(50), nullable=False, index=True)  # Group messages by conversation
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, default=0)
    execution_time_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_user_conversation', 'user_id', 'conversation_id'),
        Index('idx_conversation_date', 'conversation_id', 'created_at'),
    )


class RateLimitLog(Base):
    """Rate limit log model - for tracking rate limit hits."""
    
    __tablename__ = "rate_limit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    client_ip = Column(String(50), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    request_count = Column(Integer, default=1)
    limited = Column(Boolean, default=False, index=True)
    window_start = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_ip_window', 'client_ip', 'window_start'),
        Index('idx_limited', 'limited'),
    )


class AuditLog(Base):
    """Audit log model - for security and compliance."""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    client_ip = Column(String(50), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)  # 'login', 'search', 'chat', etc
    resource = Column(String(255), nullable=True)  # What resource was accessed
    status = Column(String(20), nullable=False)  # 'success', 'failed', 'rate_limited'
    details = Column(Text, nullable=True)  # Extra info
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_user_action', 'user_id', 'action'),
        Index('idx_ip_date', 'client_ip', 'created_at'),
        Index('idx_action_status', 'action', 'status'),
    )
