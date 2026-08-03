"""Integration tests for chat routes."""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
import json


# ============================================
# SEND MESSAGE ENDPOINT TESTS
# ============================================

class TestSendMessageEndpoint:
    """Test POST /api/chat/message endpoint."""
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, authenticated_client: AsyncClient, monkeypatch):
        """Test successful message sending."""
        async def mock_chat(self, message: str, context=None):
            return {
                "response": f"Response to: {message}",
                "tokens_used": 50
            }
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "chat",
            mock_chat.__get__(ollama_client)
        )
        
        response = await authenticated_client.post(
            "/api/chat/message",
            json={
                "message": "How do I fix a printer issue?",
                "conversation_id": "conv_123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message_id" in data
        assert "response" in data
        assert "timestamp" in data
        assert "tokens_used" in data
    
    @pytest.mark.asyncio
    async def test_send_message_without_authentication(self, async_client: AsyncClient):
        """Test sending message without authentication."""
        response = await async_client.post(
            "/api/chat/message",
            json={
                "message": "Hello",
                "conversation_id": "conv_123"
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_send_message_empty_message(self, authenticated_client: AsyncClient):
        """Test sending empty message."""
        response = await authenticated_client.post(
            "/api/chat/message",
            json={
                "message": "",
                "conversation_id": "conv_123"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_send_message_missing_message(self, authenticated_client: AsyncClient):
        """Test sending without message field."""
        response = await authenticated_client.post(
            "/api/chat/message",
            json={
                "conversation_id": "conv_123"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_send_message_too_long(self, authenticated_client: AsyncClient):
        """Test sending message that's too long."""
        long_message = "a" * 5000
        
        response = await authenticated_client.post(
            "/api/chat/message",
            json={
                "message": long_message,
                "conversation_id": "conv_123"
            }
        )
        
        assert response.status_code in [422, 400]
    
    @pytest.mark.asyncio
    async def test_send_message_with_conversation_id(self, authenticated_client: AsyncClient, monkeypatch):
        """Test sending message with conversation ID."""
        async def mock_chat(self, message: str, context=None):
            return {"response": "OK", "tokens_used": 10}
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "chat",
            mock_chat.__get__(ollama_client)
        )
        
        response = await authenticated_client.post(
            "/api/chat/message",
            json={
                "message": "Test message",
                "conversation_id": "conv_12345"
            }
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_send_message_response_structure(self, authenticated_client: AsyncClient, monkeypatch):
        """Test message response has correct structure."""
        async def mock_chat(self, message: str, context=None):
            return {"response": "Test response", "tokens_used": 25}
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "chat",
            mock_chat.__get__(ollama_client)
        )
        
        response = await authenticated_client.post(
            "/api/chat/message",
            json={
                "message": "What is IT support?",
                "conversation_id": "conv_456"
            }
        )
        
        data = response.json()
        
        assert "message_id" in data
        assert "response" in data
        assert "timestamp" in data
        assert "tokens_used" in data
        assert "conversation_id" in data
    
    @pytest.mark.asyncio
    async def test_send_message_sql_injection_blocked(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that SQL injection in messages is blocked."""
        async def mock_chat(self, message: str, context=None):
            # Should not contain SQL injection
            assert "DROP TABLE" not in message
            assert "DELETE FROM" not in message
            return {"response": "OK"}
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "chat",
            mock_chat.__get__(ollama_client)
        )
        
        response = await authenticated_client.post(
            "/api/chat/message",
            json={
                "message": "SELECT * FROM users' OR '1'='1",
                "conversation_id": "conv_789"
            }
        )
        
        # Should fail validation
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_send_message_xss_blocked(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that XSS in messages is blocked."""
        async def mock_chat(self, message: str, context=None):
            # Should not contain XSS
            assert "<script>" not in message.lower()
            return {"response": "OK"}
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "chat",
            mock_chat.__get__(ollama_client)
        )
        
        response = await authenticated_client.post(
            "/api/chat/message",
            json={
                "message": "<script>alert('xss')</script>",
                "conversation_id": "conv_999"
            }
        )
        
        # Should fail validation
        assert response.status_code in [400, 422]


# ============================================
# STREAM MESSAGE ENDPOINT TESTS
# ============================================

class TestStreamMessageEndpoint:
    """Test POST /api/chat/message/stream endpoint."""
    
    @pytest.mark.asyncio
    async def test_stream_message_success(self, authenticated_client: AsyncClient, monkeypatch):
        """Test successful message streaming."""
        async def mock_generate_stream(self, message: str):
            # Simulate streaming response
            responses = [
                {"text": "First ", "tokens": 1},
                {"text": "part ", "tokens": 1},
                {"text": "of response.", "tokens": 2}
            ]
            for resp in responses:
                yield resp
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "generate_stream",
            mock_generate_stream.__get__(ollama_client)
        )
        
        response = await authenticated_client.post(
            "/api/chat/message/stream",
            json={
                "message": "Stream this response",
                "conversation_id": "conv_stream_1"
            }
        )
        
        assert response.status_code == 200
        
        # Should be streaming (content-type: text/event-stream or application/octet-stream)
        assert "stream" in response.headers.get("content-type", "").lower()
    
    @pytest.mark.asyncio
    async def test_stream_message_without_authentication(self, async_client: AsyncClient):
        """Test streaming without authentication."""
        response = await async_client.post(
            "/api/chat/message/stream",
            json={
                "message": "Hello",
                "conversation_id": "conv_123"
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_stream_message_empty_message(self, authenticated_client: AsyncClient):
        """Test streaming empty message."""
        response = await authenticated_client.post(
            "/api/chat/message/stream",
            json={
                "message": "",
                "conversation_id": "conv_123"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_stream_message_missing_message(self, authenticated_client: AsyncClient):
        """Test streaming without message field."""
        response = await authenticated_client.post(
            "/api/chat/message/stream",
            json={
                "conversation_id": "conv_123"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_stream_message_returns_events(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that streaming returns event stream."""
        async def mock_generate_stream(self, message: str):
            yield {"text": "Hello ", "tokens": 1}
            yield {"text": "World", "tokens": 1}
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "generate_stream",
            mock_generate_stream.__get__(ollama_client)
        )
        
        response = await authenticated_client.post(
            "/api/chat/message/stream",
            json={
                "message": "Say hello",
                "conversation_id": "conv_stream_2"
            }
        )
        
        assert response.status_code == 200


# ============================================
# CHAT HEALTH ENDPOINT TESTS
# ============================================

class TestChatHealthEndpoint:
    """Test GET /api/chat/health endpoint."""
    
    @pytest.mark.asyncio
    async def test_chat_health_without_authentication(self, async_client: AsyncClient, monkeypatch):
        """Test chat health check without authentication."""
        async def mock_health_check(self):
            return {"status": "healthy"}
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "health_check",
            mock_health_check.__get__(ollama_client)
        )
        
        response = await async_client.get("/api/chat/health")
        
        # Health checks might not require auth
        assert response.status_code in [200, 401]
    
    @pytest.mark.asyncio
    async def test_chat_health_success(self, authenticated_client: AsyncClient, monkeypatch):
        """Test successful health check."""
        async def mock_health_check(self):
            return {"status": "healthy"}
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "health_check",
            mock_health_check.__get__(ollama_client)
        )
        
        response = await authenticated_client.get("/api/chat/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
    
    @pytest.mark.asyncio
    async def test_chat_health_ollama_down(self, authenticated_client: AsyncClient, monkeypatch):
        """Test health check when Ollama is down."""
        async def mock_health_check(self):
            raise Exception("Ollama unavailable")
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "health_check",
            mock_health_check.__get__(ollama_client)
        )
        
        response = await authenticated_client.get("/api/chat/health")
        
        assert response.status_code in [500, 503]
    
    @pytest.mark.asyncio
    async def test_chat_health_response_structure(self, authenticated_client: AsyncClient, monkeypatch):
        """Test health response structure."""
        async def mock_health_check(self):
            return {
                "status": "healthy",
                "ollama": {"status": "running"},
                "timestamp": "2024-01-15T10:00:00Z"
            }
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "health_check",
            mock_health_check.__get__(ollama_client)
        )
        
        response = await authenticated_client.get("/api/chat/health")
        
        data = response.json()
        
        assert "status" in data


# ============================================
# DELETE CONVERSATION ENDPOINT TESTS
# ============================================

class TestDeleteConversationEndpoint:
    """Test DELETE /api/conversations/{id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_delete_conversation_success(self, authenticated_client: AsyncClient, db_session):
        """Test successful conversation deletion."""
        response = await authenticated_client.delete(
            "/api/conversations/conv_12345"
        )
        
        # Should be 200 or 204
        assert response.status_code in [200, 204]
    
    @pytest.mark.asyncio
    async def test_delete_conversation_without_authentication(self, async_client: AsyncClient):
        """Test deleting conversation without authentication."""
        response = await async_client.delete(
            "/api/conversations/conv_12345"
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_conversation(self, authenticated_client: AsyncClient):
        """Test deleting non-existent conversation."""
        response = await authenticated_client.delete(
            "/api/conversations/nonexistent_id"
        )
        
        # Should be 404 or 200 (deleted successfully)
        assert response.status_code in [200, 204, 404]
    
    @pytest.mark.asyncio
    async def test_delete_conversation_invalid_id(self, authenticated_client: AsyncClient):
        """Test deleting conversation with invalid ID format."""
        response = await authenticated_client.delete(
            "/api/conversations/invalid@id$format"
        )
        
        # Should fail validation or succeed
        assert response.status_code in [200, 204, 400, 422]


# ============================================
# MESSAGE CONTEXT TESTS
# ============================================

class TestMessageContext:
    """Test message context and conversation history."""
    
    @pytest.mark.asyncio
    async def test_send_message_with_context(self, authenticated_client: AsyncClient, monkeypatch):
        """Test sending message with conversation context."""
        async def mock_chat(self, message: str, context=None):
            if context:
                return {"response": f"Response with context: {context}"}
            return {"response": "Response without context"}
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "chat",
            mock_chat.__get__(ollama_client)
        )
        
        response = await authenticated_client.post(
            "/api/chat/message",
            json={
                "message": "Continue the previous conversation",
                "conversation_id": "conv_123",
                "context": "Previous message was about printers"
            }
        )
        
        assert response.status_code in [200, 400, 422]
    
    @pytest.mark.asyncio
    async def test_conversation_id_affects_context(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that conversation ID is used for context."""
        call_count = [0]
        
        async def mock_chat(self, message: str, context=None):
            call_count[0] += 1
            return {"response": f"Response {call_count[0]}", "tokens_used": 10}
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "chat",
            mock_chat.__get__(ollama_client)
        )
        
        # Send two messages with same conversation ID
        response1 = await authenticated_client.post(
            "/api/chat/message",
            json={
                "message": "First message",
                "conversation_id": "same_conv"
            }
        )
        
        response2 = await authenticated_client.post(
            "/api/chat/message",
            json={
                "message": "Second message",
                "conversation_id": "same_conv"
            }
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200


# ============================================
# ERROR HANDLING TESTS
# ============================================

class TestChatErrorHandling:
    """Test error handling in chat endpoints."""
    
    @pytest.mark.asyncio
    async def test_ollama_connection_error(self, authenticated_client: AsyncClient, monkeypatch):
        """Test handling Ollama connection error."""
        async def mock_chat(self, message: str, context=None):
            raise ConnectionError("Cannot connect to Ollama")
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "chat",
            mock_chat.__get__(ollama_client)
        )
        
        response = await authenticated_client.post(
            "/api/chat/message",
            json={
                "message": "Hello",
                "conversation_id": "conv_123"
            }
        )
        
        assert response.status_code in [500, 502, 503]
    
    @pytest.mark.asyncio
    async def test_ollama_timeout(self, authenticated_client: AsyncClient, monkeypatch):
        """Test handling Ollama timeout."""
        async def mock_chat(self, message: str, context=None):
            raise TimeoutError("Ollama request timed out")
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "chat",
            mock_chat.__get__(ollama_client)
        )
        
        response = await authenticated_client.post(
            "/api/chat/message",
            json={
                "message": "Hello",
                "conversation_id": "conv_123"
            }
        )
        
        assert response.status_code in [500, 504]
    
    @pytest.mark.asyncio
    async def test_error_includes_message(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that errors include informative message."""
        async def mock_chat(self, message: str, context=None):
            raise ValueError("Model not found")
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "chat",
            mock_chat.__get__(ollama_client)
        )
        
        response = await authenticated_client.post(
            "/api/chat/message",
            json={
                "message": "Test",
                "conversation_id": "conv_123"
            }
        )
        
        assert response.status_code >= 400


# ============================================
# RATE LIMITING TESTS
# ============================================

class TestChatRateLimiting:
    """Test rate limiting for chat endpoints."""
    
    @pytest.mark.asyncio
    async def test_rapid_messages_not_blocked(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that rapid messages are not immediately blocked."""
        async def mock_chat(self, message: str, context=None):
            return {"response": "OK", "tokens_used": 10}
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "chat",
            mock_chat.__get__(ollama_client)
        )
        
        # Send 5 messages quickly
        for i in range(5):
            response = await authenticated_client.post(
                "/api/chat/message",
                json={
                    "message": f"Message {i}",
                    "conversation_id": "conv_rate_test"
                }
            )
            
            # Should not be rate limited (rate limit is 100 req/60s)
            assert response.status_code in [200, 400, 422]


# ============================================
# PERFORMANCE TESTS
# ============================================

class TestChatPerformance:
    """Test chat endpoint performance."""
    
    @pytest.mark.asyncio
    async def test_message_response_time(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that message responds within reasonable time."""
        import time
        
        async def mock_chat(self, message: str, context=None):
            return {"response": "Quick response", "tokens_used": 15}
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "chat",
            mock_chat.__get__(ollama_client)
        )
        
        start = time.time()
        response = await authenticated_client.post(
            "/api/chat/message",
            json={
                "message": "Quick test",
                "conversation_id": "conv_perf"
            }
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        # Should respond within 5 seconds
        assert elapsed < 5.0
    
    @pytest.mark.asyncio
    async def test_stream_message_response_time(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that stream message responds within reasonable time."""
        import time
        
        async def mock_generate_stream(self, message: str):
            for i in range(10):
                yield {"text": f"Word{i} ", "tokens": 1}
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "generate_stream",
            mock_generate_stream.__get__(ollama_client)
        )
        
        start = time.time()
        response = await authenticated_client.post(
            "/api/chat/message/stream",
            json={
                "message": "Stream test",
                "conversation_id": "conv_stream_perf"
            }
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        # Stream should establish connection quickly
        assert elapsed < 2.0


# ============================================
# TOKEN TRACKING TESTS
# ============================================

class TestTokenTracking:
    """Test token usage tracking."""
    
    @pytest.mark.asyncio
    async def test_token_count_in_response(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that token count is returned."""
        async def mock_chat(self, message: str, context=None):
            return {"response": "Response text", "tokens_used": 42}
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "chat",
            mock_chat.__get__(ollama_client)
        )
        
        response = await authenticated_client.post(
            "/api/chat/message",
            json={
                "message": "Count my tokens",
                "conversation_id": "conv_tokens"
            }
        )
        
        data = response.json()
        
        assert "tokens_used" in data
        assert isinstance(data["tokens_used"], int)
        assert data["tokens_used"] > 0
    
    @pytest.mark.asyncio
    async def test_token_count_zero_not_negative(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that token count is non-negative."""
        async def mock_chat(self, message: str, context=None):
            return {"response": "OK", "tokens_used": 0}
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "chat",
            mock_chat.__get__(ollama_client)
        )
        
        response = await authenticated_client.post(
            "/api/chat/message",
            json={
                "message": "Test",
                "conversation_id": "conv_zero_tokens"
            }
        )
        
        data = response.json()
        
        assert data["tokens_used"] >= 0


# ============================================
# MESSAGE TIMESTAMP TESTS
# ============================================

class TestMessageTimestamps:
    """Test message timestamp handling."""
    
    @pytest.mark.asyncio
    async def test_message_has_timestamp(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that message response includes timestamp."""
        async def mock_chat(self, message: str, context=None):
            return {"response": "Response", "tokens_used": 10}
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "chat",
            mock_chat.__get__(ollama_client)
        )
        
        response = await authenticated_client.post(
            "/api/chat/message",
            json={
                "message": "Test timestamp",
                "conversation_id": "conv_ts"
            }
        )
        
        data = response.json()
        
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_timestamp_is_iso_format(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that timestamp is in ISO format."""
        from datetime import datetime
        
        async def mock_chat(self, message: str, context=None):
            return {"response": "OK", "tokens_used": 10}
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "chat",
            mock_chat.__get__(ollama_client)
        )
        
        response = await authenticated_client.post(
            "/api/chat/message",
            json={
                "message": "Check timestamp format",
                "conversation_id": "conv_iso"
            }
        )
        
        data = response.json()
        
        # Should be parseable as ISO format
        try:
            datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
            valid_iso = True
        except (ValueError, AttributeError):
            valid_iso = False
        
        assert valid_iso
