"""Search routes for GLPI tickets."""

from fastapi import APIRouter, Request, HTTPException, status, Query, Path
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging

from config import settings
from core.exceptions import AppException, RateLimitExceededError
from services.glpi import glpi_client
from validators.input_validators import validate_search_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["Search"])


class TicketResult(BaseModel):
    """Single ticket search result."""
    
    id: int = Field(..., description="Ticket ID")
    name: str = Field(..., description="Ticket title")
    status: str = Field(..., description="Ticket status")
    priority: str = Field(..., description="Ticket priority")
    date: str = Field(..., description="Creation date")
    
    class Config:
        example = {
            "id": 123,
            "name": "Sistema de acceso lento",
            "status": "new",
            "priority": "high",
            "date": "2026-08-03"
        }


class SearchResponse(BaseModel):
    """Search response schema."""
    
    query: str = Field(..., description="Search query")
    total_results: int = Field(..., description="Total results found")
    results: List[TicketResult] = Field(default_factory=list, description="Search results")
    execution_time_ms: int = Field(default=0, description="Query execution time")
    
    class Config:
        example = {
            "query": "acceso",
            "total_results": 2,
            "results": [
                {
                    "id": 123,
                    "name": "Sistema de acceso lento",
                    "status": "new",
                    "priority": "high",
                    "date": "2026-08-03"
                }
            ],
            "execution_time_ms": 245
        }


class TicketDetail(BaseModel):
    """Detailed ticket information."""
    
    id: int = Field(..., description="Ticket ID")
    name: str = Field(..., description="Ticket title")
    status: str = Field(..., description="Ticket status")
    priority: str = Field(..., description="Ticket priority")
    urgency: str = Field(..., description="Urgency level")
    impact: str = Field(..., description="Impact level")
    date: str = Field(..., description="Creation date")
    description: Optional[str] = Field(None, description="Full description")
    assigned_to: Optional[str] = Field(None, description="Assigned to")
    
    class Config:
        example = {
            "id": 123,
            "name": "Sistema de acceso lento",
            "status": "new",
            "priority": "high",
            "urgency": "high",
            "impact": "high",
            "date": "2026-08-03",
            "description": "El sistema de acceso GLPI está respondiendo lentamente...",
            "assigned_to": "admin"
        }


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")


@router.get(
    "/tickets",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid query"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        429: {"model": ErrorResponse, "description": "Rate limited"}
    }
)
async def search_tickets(
    request: Request,
    q: str = Query(..., min_length=2, max_length=500, description="Search query"),
    limit: int = Query(default=10, ge=1, le=100, description="Max results")
):
    """
    Search GLPI tickets.
    
    Returns matching tickets with basic info.
    """
    
    request_id = getattr(request.state, 'request_id', 'unknown')
    user_id = getattr(request.state, 'user_id', None)
    client_ip = getattr(request.state, 'client_ip', 'unknown')
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "NOT_AUTHENTICATED", "message": "Authentication required"}
        )
    
    try:
        # Validate query
        if not validate_search_query(q):
            raise AppException(
                error_code="INVALID_QUERY",
                message="Search query contains invalid characters or patterns",
                status_code=400
            )
        
        logger.info(f"🔍 Search query: '{q}' (limit={limit}) by {user_id}")
        
        # Search GLPI
        import time
        start_time = time.time()
        
        raw_results = await glpi_client.search_tickets(q, limit)
        
        execution_time = int((time.time() - start_time) * 1000)
        
        # Transform results
        results = []
        for ticket in raw_results:
            if isinstance(ticket, dict):
                results.append(TicketResult(
                    id=ticket.get("id", 0),
                    name=ticket.get("name", "Unknown"),
                    status=ticket.get("status", "unknown"),
                    priority=ticket.get("priority", "low"),
                    date=ticket.get("date", datetime.utcnow().isoformat())
                ))
        
        logger.info(f"✅ Search completed: {len(results)} results in {execution_time}ms")
        
        return SearchResponse(
            query=q,
            total_results=len(results),
            results=results,
            execution_time_ms=execution_time
        )
        
    except AppException as e:
        logger.warning(f"⚠️ Search validation error: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.error_code, "message": e.message, "request_id": request_id}
        )
    except Exception as e:
        logger.error(f"❌ Search error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "SEARCH_ERROR", "message": "Search failed", "request_id": request_id}
        )


@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketDetail,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Ticket not found"},
        429: {"model": ErrorResponse, "description": "Rate limited"}
    }
)
async def get_ticket_detail(
    request: Request,
    ticket_id: int = Path(..., ge=1, description="Ticket ID")
):
    """
    Get detailed information about a specific ticket.
    """
    
    request_id = getattr(request.state, 'request_id', 'unknown')
    user_id = getattr(request.state, 'user_id', None)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "NOT_AUTHENTICATED", "message": "Authentication required"}
        )
    
    try:
        logger.info(f"📄 Get ticket details: {ticket_id} by {user_id}")
        
        # Get from GLPI
        ticket = await glpi_client.get_ticket(ticket_id)
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NOT_FOUND", "message": f"Ticket {ticket_id} not found", "request_id": request_id}
            )
        
        # Transform
        detail = TicketDetail(
            id=ticket.get("id", ticket_id),
            name=ticket.get("name", "Unknown"),
            status=ticket.get("status", "unknown"),
            priority=ticket.get("priority", "low"),
            urgency=ticket.get("urgency", "low"),
            impact=ticket.get("impact", "low"),
            date=ticket.get("date", datetime.utcnow().isoformat()),
            description=ticket.get("description", None),
            assigned_to=ticket.get("assigned_to", None)
        )
        
        logger.info(f"✅ Ticket details retrieved: {ticket_id}")
        
        return detail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get ticket error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "TICKET_ERROR", "message": "Failed to get ticket", "request_id": request_id}
        )


@router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"}
    }
)
async def search_stats(request: Request):
    """
    Get search statistics and metrics.
    """
    
    user_id = getattr(request.state, 'user_id', None)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "NOT_AUTHENTICATED", "message": "Authentication required"}
        )
    
    try:
        stats = {
            "user_id": user_id,
            "total_searches": 0,  # TODO: fetch from database
            "total_results": 0,
            "avg_execution_time_ms": 0,
            "last_search": None
        }
        
        logger.info(f"✅ Search stats retrieved for {user_id}")
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Search stats error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "STATS_ERROR", "message": "Failed to get stats"}
        )
