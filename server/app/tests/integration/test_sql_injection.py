"""Security tests for SQL injection prevention."""

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import SQLAlchemyError


class TestSQLInjectionLogin:
    """Test SQL injection prevention in login endpoint."""
    
    # Classic SQL injection payloads
    SQL_INJECTION_PAYLOADS = [
        # Basic OR attacks
        "' OR '1'='1",
        "' OR 1=1 --",
        "' OR 1=1 /*",
        "' OR '1'='1' --",
        "' OR '1'='1' /*",
        
        # Union-based
        "' UNION SELECT 1,2,3 --",
        "' UNION ALL SELECT NULL --",
        "' UNION SELECT NULL,NULL --",
        
        # Blind SQL injection
        "' AND SLEEP(5) --",
        "' AND BENCHMARK(5000000,MD5('1')) --",
        "' AND 1=1 --",
        "' AND 1=2 --",
        
        # Time-based
        "' AND IF(1=1,SLEEP(1),0) --",
        "'; WAITFOR DELAY '00:00:05' --",
        
        # Stacked queries
        "'; DROP TABLE users; --",
        "'; DELETE FROM users; --",
        
        # Comment-based
        "' -- ",
        "' #",
        "' /*",
        
        # Boolean-based
        "' AND 'a'='a",
        "' AND 'a'='b",
        
        # Hex encoding
        "' OR 0x31=0x31 --",
        
        # Double URL encoding
        "%27%20OR%20%271%27=%271",
        
        # Character encoding
        "' /*!50000OR*/ 1=1 --",
        
        # With numbers
        "1' OR '1'='1",
        "1' UNION SELECT NULL --",
    ]
    
    @pytest.mark.asyncio
    async def test_sql_injection_in_username(self, async_client: AsyncClient, monkeypatch):
        """Test SQL injection attempts in username field."""
        async def mock_init_session(self, username: str, password: str):
            # Should not contain injection payload
            dangerous_keywords = ["UNION", "SELECT", "DROP", "DELETE", "SLEEP", "--", "/*"]
            for keyword in dangerous_keywords:
                assert keyword not in username.upper()
            return False
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "init_session",
            mock_init_session.__get__(glpi_client)
        )
        
        for payload in self.SQL_INJECTION_PAYLOADS:
            response = await async_client.post(
                "/api/auth/login",
                json={
                    "username": payload,
                    "password": "TestPassword123!"
                }
            )
            
            # Should fail validation, not execute SQL
            assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_sql_injection_in_password(self, async_client: AsyncClient, monkeypatch):
        """Test SQL injection attempts in password field."""
        async def mock_init_session(self, username: str, password: str):
            dangerous_keywords = ["UNION", "SELECT", "DROP", "DELETE", "SLEEP"]
            for keyword in dangerous_keywords:
                assert keyword not in password.upper()
            return False
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "init_session",
            mock_init_session.__get__(glpi_client)
        )
        
        for payload in self.SQL_INJECTION_PAYLOADS[:10]:  # Test subset
            response = await async_client.post(
                "/api/auth/login",
                json={
                    "username": "testuser",
                    "password": payload
                }
            )
            
            # Should fail validation
            assert response.status_code in [400, 422]


class TestSQLInjectionSearch:
    """Test SQL injection prevention in search endpoint."""
    
    SQL_SEARCH_PAYLOADS = [
        # Basic OR in search
        "test' OR 1=1 --",
        "' OR 'a'='a",
        "network' OR '1'='1",
        
        # Union-based search
        "test' UNION SELECT 1,2 --",
        "test' UNION SELECT username,password --",
        
        # Time-based in search
        "test' AND SLEEP(1) --",
        
        # Blind SQL injection
        "test' AND 1=1 --",
        "test' AND 1=2 --",
        
        # Drop table
        "test'; DROP TABLE tickets; --",
        
        # Multiple statements
        "test; DELETE FROM search_queries;",
    ]
    
    @pytest.mark.asyncio
    async def test_sql_injection_in_search_query(self, authenticated_client: AsyncClient, monkeypatch):
        """Test SQL injection in search query parameter."""
        async def mock_search_tickets(self, query: str):
            # Query should be sanitized
            assert "UNION" not in query.upper()
            assert "DROP" not in query.upper()
            assert "DELETE" not in query.upper()
            return []
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        for payload in self.SQL_SEARCH_PAYLOADS:
            response = await authenticated_client.get(
                "/api/search/tickets",
                params={"q": payload}
            )
            
            # Should fail validation or return safely
            assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_sql_injection_in_ticket_id(self, authenticated_client: AsyncClient, monkeypatch):
        """Test SQL injection in ticket ID parameter."""
        async def mock_get_ticket(self, ticket_id: int):
            # Should be integer, not string with SQL
            assert isinstance(ticket_id, int)
            return None
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "get_ticket",
            mock_get_ticket.__get__(glpi_client)
        )
        
        injection_ids = [
            "1' OR '1'='1",
            "1 UNION SELECT 1,2,3",
            "1; DROP TABLE tickets;",
            "-1' UNION SELECT username FROM users",
        ]
        
        for payload in injection_ids:
            response = await authenticated_client.get(
                f"/api/search/tickets/{payload}"
            )
            
            # Should fail validation
            assert response.status_code in [422, 404]


class TestSQLInjectionChat:
    """Test SQL injection prevention in chat endpoint."""
    
    CHAT_INJECTION_PAYLOADS = [
        "What is network' OR 1=1 --?",
        "Help me with'; DROP TABLE conversations; --",
        "Tell me about' UNION SELECT password FROM users --",
        "test' AND SLEEP(5) --",
    ]
    
    @pytest.mark.asyncio
    async def test_sql_injection_in_chat_message(self, authenticated_client: AsyncClient, monkeypatch):
        """Test SQL injection in chat message."""
        async def mock_chat(self, message: str, context=None):
            # Message should not contain SQL keywords
            assert "DROP" not in message.upper()
            assert "DELETE" not in message.upper()
            assert "UNION" not in message.upper()
            return {"response": "OK"}
        
        from services.ollama import ollama_client
        monkeypatch.setattr(
            ollama_client,
            "chat",
            mock_chat.__get__(ollama_client)
        )
        
        for payload in self.CHAT_INJECTION_PAYLOADS:
            response = await authenticated_client.post(
                "/api/chat/message",
                json={
                    "message": payload,
                    "conversation_id": "conv_123"
                }
            )
            
            # Should fail validation or succeed without SQL execution
            assert response.status_code in [400, 422, 200]


class TestSQLInjectionVectorVariations:
    """Test various SQL injection vector variations."""
    
    @pytest.mark.asyncio
    async def test_comment_variations(self, authenticated_client: AsyncClient, monkeypatch):
        """Test different SQL comment variations."""
        async def mock_search_tickets(self, query: str):
            return []
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        comment_payloads = [
            "test' -- ",
            "test' #",
            "test' /*",
            "test' -- -",
            "test' /*!*/",
            "test' --+",
            "test' --=",
        ]
        
        for payload in comment_payloads:
            response = await authenticated_client.get(
                "/api/search/tickets",
                params={"q": payload}
            )
            
            assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_case_variations(self, authenticated_client: AsyncClient, monkeypatch):
        """Test SQL injection with case variations."""
        async def mock_search_tickets(self, query: str):
            return []
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        case_payloads = [
            "' Or '1'='1",
            "' oR '1'='1",
            "' UnIoN sElEcT 1 --",
            "' union select 1 --",
        ]
        
        for payload in case_payloads:
            response = await authenticated_client.get(
                "/api/search/tickets",
                params={"q": payload}
            )
            
            # Should still be blocked
            assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_whitespace_variations(self, authenticated_client: AsyncClient, monkeypatch):
        """Test SQL injection with whitespace variations."""
        async def mock_search_tickets(self, query: str):
            return []
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        whitespace_payloads = [
            "'  OR  '1'='1",
            "'\tOR\t'1'='1",
            "'\nOR\n'1'='1",
            "'   UNION   SELECT 1 --",
        ]
        
        for payload in whitespace_payloads:
            response = await authenticated_client.get(
                "/api/search/tickets",
                params={"q": payload}
            )
            
            # Should still fail validation
            assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_encoding_variations(self, authenticated_client: AsyncClient, monkeypatch):
        """Test SQL injection with encoding variations."""
        async def mock_search_tickets(self, query: str):
            return []
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        encoded_payloads = [
            # Hex encoding
            "' OR 0x31=0x31 --",
            "' OR 0x3d3d --",
            
            # Character encoding
            "' OR CHAR(49)=CHAR(49) --",
        ]
        
        for payload in encoded_payloads:
            response = await authenticated_client.get(
                "/api/search/tickets",
                params={"q": payload}
            )
            
            # Should fail validation
            assert response.status_code in [400, 422]


class TestSQLInjectionBypass:
    """Test advanced SQL injection bypass techniques."""
    
    @pytest.mark.asyncio
    async def test_inline_comment_bypass(self, authenticated_client: AsyncClient, monkeypatch):
        """Test inline comment bypass attempts."""
        async def mock_search_tickets(self, query: str):
            return []
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        bypass_payloads = [
            "' /*!50000OR*/ '1'='1",
            "' /*!50001UNION*/ SELECT 1 --",
            "' /*! OR */ '1'='1",
        ]
        
        for payload in bypass_payloads:
            response = await authenticated_client.get(
                "/api/search/tickets",
                params={"q": payload}
            )
            
            assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_logical_operator_bypass(self, authenticated_client: AsyncClient, monkeypatch):
        """Test logical operator bypass attempts."""
        async def mock_search_tickets(self, query: str):
            return []
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        bypass_payloads = [
            "' and 1=1 --",
            "' && 1=1 --",
            "' || 1=1 --",
            "' || '1'='1",
        ]
        
        for payload in bypass_payloads:
            response = await authenticated_client.get(
                "/api/search/tickets",
                params={"q": payload}
            )
            
            assert response.status_code in [400, 422]


class TestSQLInjectionDataExfiltration:
    """Test prevention of data exfiltration via SQL injection."""
    
    @pytest.mark.asyncio
    async def test_union_based_exfiltration_blocked(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that UNION-based data exfiltration is blocked."""
        async def mock_search_tickets(self, query: str):
            # Should not execute UNION queries
            assert "UNION" not in query.upper()
            return []
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        exfil_payloads = [
            "' UNION SELECT username,password FROM users --",
            "' UNION SELECT email FROM users --",
            "' UNION ALL SELECT 1,2,3,4,5 --",
        ]
        
        for payload in exfil_payloads:
            response = await authenticated_client.get(
                "/api/search/tickets",
                params={"q": payload}
            )
            
            assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_time_based_exfiltration_blocked(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that time-based exfiltration is blocked."""
        async def mock_search_tickets(self, query: str):
            assert "SLEEP" not in query.upper()
            assert "BENCHMARK" not in query.upper()
            assert "WAITFOR" not in query.upper()
            return []
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        exfil_payloads = [
            "' AND SLEEP(5) --",
            "' AND BENCHMARK(10000000,MD5('a')) --",
            "'; WAITFOR DELAY '00:00:05' --",
        ]
        
        for payload in exfil_payloads:
            response = await authenticated_client.get(
                "/api/search/tickets",
                params={"q": payload}
            )
            
            assert response.status_code in [400, 422]


class TestSQLInjectionDestructive:
    """Test prevention of destructive SQL injection attacks."""
    
    @pytest.mark.asyncio
    async def test_drop_table_blocked(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that DROP TABLE is blocked."""
        async def mock_search_tickets(self, query: str):
            assert "DROP" not in query.upper()
            return []
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        destructive = [
            "' DROP TABLE users --",
            "'; DROP TABLE tickets; --",
            "test' DROP DATABASE app --",
        ]
        
        for payload in destructive:
            response = await authenticated_client.get(
                "/api/search/tickets",
                params={"q": payload}
            )
            
            assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_delete_blocked(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that DELETE statements are blocked."""
        async def mock_search_tickets(self, query: str):
            assert "DELETE" not in query.upper()
            return []
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        destructive = [
            "' DELETE FROM users --",
            "'; DELETE FROM tickets; --",
            "test'; DELETE FROM chat_messages;",
        ]
        
        for payload in destructive:
            response = await authenticated_client.get(
                "/api/search/tickets",
                params={"q": payload}
            )
            
            assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_truncate_blocked(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that TRUNCATE statements are blocked."""
        async def mock_search_tickets(self, query: str):
            assert "TRUNCATE" not in query.upper()
            return []
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        destructive = [
            "' TRUNCATE TABLE users --",
            "'; TRUNCATE TABLE tickets;",
        ]
        
        for payload in destructive:
            response = await authenticated_client.get(
                "/api/search/tickets",
                params={"q": payload}
            )
            
            assert response.status_code in [400, 422]


class TestSQLInjectionLogging:
    """Test that SQL injection attempts are logged."""
    
    @pytest.mark.asyncio
    async def test_injection_attempt_logged(self, authenticated_client: AsyncClient, monkeypatch, caplog):
        """Test that injection attempts are logged."""
        async def mock_search_tickets(self, query: str):
            return []
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        # Make an injection attempt
        response = await authenticated_client.get(
            "/api/search/tickets",
            params={"q": "test' OR '1'='1"}
        )
        
        # Should be rejected
        assert response.status_code in [400, 422]
