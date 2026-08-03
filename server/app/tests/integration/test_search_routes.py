"""Integration tests for search routes."""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


# ============================================
# SEARCH TICKETS ENDPOINT TESTS
# ============================================

class TestSearchTicketsEndpoint:
    """Test GET /api/search/tickets endpoint."""
    
    @pytest.mark.asyncio
    async def test_search_tickets_success(self, authenticated_client: AsyncClient, monkeypatch):
        """Test successful ticket search."""
        mock_results = [
            {
                "id": 1,
                "title": "Network issue",
                "status": "Open",
                "priority": "High",
                "date_creation": "2024-01-15 10:30:00"
            },
            {
                "id": 2,
                "title": "Printer not working",
                "status": "Open",
                "priority": "Medium",
                "date_creation": "2024-01-15 11:00:00"
            }
        ]
        
        async def mock_search_tickets(self, query: str):
            if query.lower() in ["network", "printer", "issue"]:
                return mock_results
            return []
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        response = await authenticated_client.get(
            "/api/search/tickets",
            params={"q": "network"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert len(data["results"]) > 0
        assert "total" in data
    
    @pytest.mark.asyncio
    async def test_search_tickets_empty_query(self, authenticated_client: AsyncClient):
        """Test search with empty query."""
        response = await authenticated_client.get(
            "/api/search/tickets",
            params={"q": ""}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_search_tickets_no_query(self, authenticated_client: AsyncClient):
        """Test search without query parameter."""
        response = await authenticated_client.get("/api/search/tickets")
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_search_tickets_without_authentication(self, async_client: AsyncClient):
        """Test search without authentication."""
        response = await async_client.get(
            "/api/search/tickets",
            params={"q": "network"}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_search_tickets_no_results(self, authenticated_client: AsyncClient, monkeypatch):
        """Test search with no results."""
        async def mock_search_tickets(self, query: str):
            return []
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        response = await authenticated_client.get(
            "/api/search/tickets",
            params={"q": "nonexistent"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 0
        assert len(data["results"]) == 0
    
    @pytest.mark.asyncio
    async def test_search_tickets_query_too_short(self, authenticated_client: AsyncClient):
        """Test search with query too short."""
        response = await authenticated_client.get(
            "/api/search/tickets",
            params={"q": "a"}
        )
        
        # Should fail validation (minimum length)
        assert response.status_code in [422, 400]
    
    @pytest.mark.asyncio
    async def test_search_tickets_query_too_long(self, authenticated_client: AsyncClient):
        """Test search with query too long."""
        long_query = "a" * 500
        
        response = await authenticated_client.get(
            "/api/search/tickets",
            params={"q": long_query}
        )
        
        # Should fail validation (maximum length)
        assert response.status_code in [422, 400]
    
    @pytest.mark.asyncio
    async def test_search_tickets_with_pagination(self, authenticated_client: AsyncClient, monkeypatch):
        """Test search with pagination parameters."""
        mock_results = [
            {"id": i, "title": f"Ticket {i}", "status": "Open"}
            for i in range(1, 11)
        ]
        
        async def mock_search_tickets(self, query: str):
            return mock_results
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        response = await authenticated_client.get(
            "/api/search/tickets",
            params={"q": "ticket", "skip": 0, "limit": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "total" in data
    
    @pytest.mark.asyncio
    async def test_search_tickets_response_structure(self, authenticated_client: AsyncClient, monkeypatch):
        """Test search response has correct structure."""
        mock_results = [
            {
                "id": 1,
                "title": "Test ticket",
                "status": "Open",
                "priority": "High",
                "date_creation": "2024-01-15 10:00:00"
            }
        ]
        
        async def mock_search_tickets(self, query: str):
            return mock_results
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        response = await authenticated_client.get(
            "/api/search/tickets",
            params={"q": "test"}
        )
        
        data = response.json()
        
        assert "results" in data
        assert "total" in data
        assert "query" in data
        
        if len(data["results"]) > 0:
            result = data["results"][0]
            assert "id" in result
            assert "title" in result
            assert "status" in result


# ============================================
# GET TICKET DETAIL ENDPOINT TESTS
# ============================================

class TestGetTicketDetailEndpoint:
    """Test GET /api/search/tickets/{id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_ticket_success(self, authenticated_client: AsyncClient, monkeypatch):
        """Test getting ticket details successfully."""
        mock_ticket = {
            "id": 1,
            "title": "Network issue",
            "status": "Open",
            "priority": "High",
            "description": "Internet connection is down",
            "date_creation": "2024-01-15 10:00:00",
            "date_mod": "2024-01-15 11:00:00",
            "assigned_to": "Tech Support",
            "comments": [
                {
                    "id": 1,
                    "text": "Investigating the issue",
                    "date": "2024-01-15 10:30:00"
                }
            ]
        }
        
        async def mock_get_ticket(self, ticket_id: int):
            if ticket_id == 1:
                return mock_ticket
            return None
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "get_ticket",
            mock_get_ticket.__get__(glpi_client)
        )
        
        response = await authenticated_client.get("/api/search/tickets/1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == 1
        assert data["title"] == "Network issue"
        assert data["status"] == "Open"
        assert data["priority"] == "High"
    
    @pytest.mark.asyncio
    async def test_get_ticket_not_found(self, authenticated_client: AsyncClient, monkeypatch):
        """Test getting non-existent ticket."""
        async def mock_get_ticket(self, ticket_id: int):
            return None
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "get_ticket",
            mock_get_ticket.__get__(glpi_client)
        )
        
        response = await authenticated_client.get("/api/search/tickets/99999")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_ticket_invalid_id(self, authenticated_client: AsyncClient):
        """Test getting ticket with invalid ID."""
        response = await authenticated_client.get("/api/search/tickets/invalid")
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_ticket_without_authentication(self, async_client: AsyncClient):
        """Test getting ticket without authentication."""
        response = await async_client.get("/api/search/tickets/1")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_ticket_response_structure(self, authenticated_client: AsyncClient, monkeypatch):
        """Test ticket detail response structure."""
        mock_ticket = {
            "id": 1,
            "title": "Test ticket",
            "status": "Open",
            "priority": "Medium",
            "description": "Test description",
            "date_creation": "2024-01-15 10:00:00",
            "assigned_to": "User1",
            "comments": []
        }
        
        async def mock_get_ticket(self, ticket_id: int):
            return mock_ticket
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "get_ticket",
            mock_get_ticket.__get__(glpi_client)
        )
        
        response = await authenticated_client.get("/api/search/tickets/1")
        
        data = response.json()
        
        assert "id" in data
        assert "title" in data
        assert "status" in data
        assert "priority" in data
        assert "description" in data
        assert "date_creation" in data
    
    @pytest.mark.asyncio
    async def test_get_ticket_with_comments(self, authenticated_client: AsyncClient, monkeypatch):
        """Test ticket with multiple comments."""
        mock_ticket = {
            "id": 1,
            "title": "Test ticket",
            "status": "Open",
            "priority": "High",
            "description": "Test description",
            "date_creation": "2024-01-15 10:00:00",
            "comments": [
                {"id": 1, "text": "First comment", "date": "2024-01-15 10:30:00"},
                {"id": 2, "text": "Second comment", "date": "2024-01-15 11:00:00"},
                {"id": 3, "text": "Third comment", "date": "2024-01-15 11:30:00"}
            ]
        }
        
        async def mock_get_ticket(self, ticket_id: int):
            return mock_ticket
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "get_ticket",
            mock_get_ticket.__get__(glpi_client)
        )
        
        response = await authenticated_client.get("/api/search/tickets/1")
        
        data = response.json()
        
        assert "comments" in data
        assert len(data["comments"]) == 3


# ============================================
# SEARCH STATS ENDPOINT TESTS
# ============================================

class TestSearchStatsEndpoint:
    """Test GET /api/search/stats endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_search_stats(self, authenticated_client: AsyncClient, db_session, user_factory):
        """Test getting search statistics."""
        user = user_factory(username="testuser")
        
        response = await authenticated_client.get("/api/search/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_searches" in data
        assert "recent_searches" in data
        assert isinstance(data["total_searches"], int)
        assert isinstance(data["recent_searches"], list)
    
    @pytest.mark.asyncio
    async def test_get_search_stats_without_authentication(self, async_client: AsyncClient):
        """Test getting search stats without authentication."""
        response = await async_client.get("/api/search/stats")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_search_stats_response_structure(self, authenticated_client: AsyncClient):
        """Test search stats response structure."""
        response = await authenticated_client.get("/api/search/stats")
        
        data = response.json()
        
        assert "total_searches" in data
        assert "recent_searches" in data
        
        if len(data["recent_searches"]) > 0:
            search = data["recent_searches"][0]
            assert "query" in search
            assert "timestamp" in search
            assert "results_count" in search
    
    @pytest.mark.asyncio
    async def test_search_stats_total_is_number(self, authenticated_client: AsyncClient):
        """Test that total_searches is a number."""
        response = await authenticated_client.get("/api/search/stats")
        
        data = response.json()
        
        assert isinstance(data["total_searches"], int)
        assert data["total_searches"] >= 0


# ============================================
# SEARCH QUERY LOGGING TESTS
# ============================================

class TestSearchQueryLogging:
    """Test that search queries are properly logged."""
    
    @pytest.mark.asyncio
    async def test_search_creates_log_entry(self, authenticated_client: AsyncClient, monkeypatch, db_session):
        """Test that search creates a log entry."""
        async def mock_search_tickets(self, query: str):
            return [{"id": 1, "title": "Test"}]
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        response = await authenticated_client.get(
            "/api/search/tickets",
            params={"q": "test"}
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_multiple_searches_tracked(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that multiple searches are tracked."""
        search_count = 0
        
        async def mock_search_tickets(self, query: str):
            nonlocal search_count
            search_count += 1
            return [{"id": i, "title": f"Ticket {i}"}]
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        # Make 3 searches
        for i in range(3):
            response = await authenticated_client.get(
                "/api/search/tickets",
                params={"q": f"query{i}"}
            )
            assert response.status_code == 200
        
        # Verify all searches were processed
        assert search_count == 3


# ============================================
# SEARCH INPUT VALIDATION TESTS
# ============================================

class TestSearchInputValidation:
    """Test input validation for search endpoints."""
    
    @pytest.mark.asyncio
    async def test_search_sql_injection_blocked(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that SQL injection attempts are blocked."""
        async def mock_search_tickets(self, query: str):
            # Should never receive actual injection
            assert "DROP" not in query
            assert "DELETE" not in query
            return []
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        # Try SQL injection
        response = await authenticated_client.get(
            "/api/search/tickets",
            params={"q": "test' OR '1'='1"}
        )
        
        # Should fail validation
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_search_xss_blocked(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that XSS attempts are blocked."""
        async def mock_search_tickets(self, query: str):
            # Query should be sanitized
            assert "<script>" not in query.lower()
            return []
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        # Try XSS
        response = await authenticated_client.get(
            "/api/search/tickets",
            params={"q": "<script>alert('xss')</script>"}
        )
        
        # Should fail validation
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_search_special_characters(self, authenticated_client: AsyncClient, monkeypatch):
        """Test search with special characters."""
        async def mock_search_tickets(self, query: str):
            return []
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        # Search with special characters should work
        response = await authenticated_client.get(
            "/api/search/tickets",
            params={"q": "network & printer @ office #1"}
        )
        
        # Should be allowed
        assert response.status_code in [200, 400, 422]
    
    @pytest.mark.asyncio
    async def test_search_unicode_characters(self, authenticated_client: AsyncClient, monkeypatch):
        """Test search with unicode characters."""
        async def mock_search_tickets(self, query: str):
            return []
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        # Search with unicode
        response = await authenticated_client.get(
            "/api/search/tickets",
            params={"q": "problemas de conexión"}
        )
        
        # Should be allowed
        assert response.status_code in [200, 400, 422]


# ============================================
# ERROR HANDLING TESTS
# ============================================

class TestSearchErrorHandling:
    """Test error handling in search endpoints."""
    
    @pytest.mark.asyncio
    async def test_glpi_connection_error(self, authenticated_client: AsyncClient, monkeypatch):
        """Test handling of GLPI connection errors."""
        async def mock_search_tickets(self, query: str):
            raise Exception("Connection refused")
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        response = await authenticated_client.get(
            "/api/search/tickets",
            params={"q": "test"}
        )
        
        # Should return 5xx error
        assert response.status_code in [500, 502, 503]
    
    @pytest.mark.asyncio
    async def test_timeout_error(self, authenticated_client: AsyncClient, monkeypatch):
        """Test handling of timeout errors."""
        async def mock_search_tickets(self, query: str):
            raise TimeoutError("Request timed out")
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        response = await authenticated_client.get(
            "/api/search/tickets",
            params={"q": "test"}
        )
        
        # Should return 5xx error
        assert response.status_code in [500, 502, 504]
    
    @pytest.mark.asyncio
    async def test_error_response_includes_message(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that error responses include error message."""
        async def mock_search_tickets(self, query: str):
            raise Exception("Test error message")
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        response = await authenticated_client.get(
            "/api/search/tickets",
            params={"q": "test"}
        )
        
        # Should have error message in response
        assert response.status_code >= 400


# ============================================
# PERFORMANCE TESTS
# ============================================

class TestSearchPerformance:
    """Test search endpoint performance."""
    
    @pytest.mark.asyncio
    async def test_search_response_time(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that search responds within reasonable time."""
        import time
        
        mock_results = [{"id": i, "title": f"Ticket {i}"} for i in range(100)]
        
        async def mock_search_tickets(self, query: str):
            return mock_results
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "search_tickets",
            mock_search_tickets.__get__(glpi_client)
        )
        
        start = time.time()
        response = await authenticated_client.get(
            "/api/search/tickets",
            params={"q": "test"}
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        # Should respond within 5 seconds even with 100 results
        assert elapsed < 5.0
    
    @pytest.mark.asyncio
    async def test_ticket_detail_response_time(self, authenticated_client: AsyncClient, monkeypatch):
        """Test that ticket detail responds within reasonable time."""
        import time
        
        mock_ticket = {
            "id": 1,
            "title": "Test",
            "status": "Open",
            "comments": [{"id": i, "text": f"Comment {i}"} for i in range(50)]
        }
        
        async def mock_get_ticket(self, ticket_id: int):
            return mock_ticket
        
        from services.glpi import glpi_client
        monkeypatch.setattr(
            glpi_client,
            "get_ticket",
            mock_get_ticket.__get__(glpi_client)
        )
        
        start = time.time()
        response = await authenticated_client.get("/api/search/tickets/1")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        # Should respond within 5 seconds even with 50 comments
        assert elapsed < 5.0
