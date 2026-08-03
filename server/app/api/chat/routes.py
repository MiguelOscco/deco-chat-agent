"""Chat routes for LLM integration."""

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging
import json

from config import settings
from core.exceptions import AppException
from services.ollama import ollama_client
from validators.input_validators import validate_chat_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


class ChatMessage(BaseModel):
    """Chat message schema."""
    
    role: str = Field(..., pattern="^(user|assistant|system)$", description="Message role")
    content: str = Field(..., min_length=1, max_length=5000, description="Message content")
    
    class Config:
        example = {
            "role": "user",
            "content": "¿Cuál es el estado de los tickets de acceso?"
        }


class ChatRequest(BaseModel):
    """Chat request schema."""
    
    conversation_id: str = Field(..., description="Conversation ID")
    messages: List[ChatMessage] = Field(..., min_items=1, description="Message history")
    model: Optional[str] = Field(default="mistral", description="Model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Temperature for generation")
    stream: bool = Field(default=False, description="Stream response")
    
    class Config:
        example = {
            "conversation_id": "conv-123",
            "messages": [
                {"role": "user", "content": "¿Cuál es el estado del ticket 456?"}
            ],
            "model": "mistral",
            "temperature": 0.7,
            "stream": False
        }


class ChatResponse(BaseModel):
    """Chat response schema."""
    
    conversation_id: str = Field(..., description="Conversation ID")
    message: ChatMessage = Field(..., description="Assistant response")
    tokens_used: int = Field(default=0, description="Tokens used")
    execution_time_ms: int = Field(default=0, description="Execution time")
    
    class Config:
        example = {
            "conversation_id": "conv-123",
            "message": {
                "role": "assistant",
                "content": "Los tickets de acceso están siendo procesados..."
            },
            "tokens_used": 150,
            "execution_time_ms": 2340
        }


class HealthResponse(BaseModel):
    """Health response schema."""
    
    status: str = Field(..., description="Service status")
    model: str = Field(..., description="Active model")
    available_models: List[str] = Field(default_factory=list, description="Available models")


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")


@router.post(
    "/message",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        503: {"model": ErrorResponse, "description": "LLM service unavailable"}
    }
)
async def send_message(
    request: Request,
    chat_request: ChatRequest
):
    """
    Send a message and get LLM response.
    
    Returns complete response or streaming if requested.
    """
    
    request_id = getattr(request.state, 'request_id', 'unknown')
    user_id = getattr(request.state, 'user_id', None)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "NOT_AUTHENTICATED", "message": "Authentication required"}
        )
    
    try:
        # Get last user message
        user_message = None
        for msg in reversed(chat_request.messages):
            if msg.role == "user":
                user_message = msg.content
                break
        
        if not user_message:
            raise AppException(
                error_code="NO_USER_MESSAGE",
                message="No user message in conversation",
                status_code=400
            )
        
        # Validate message
        if not validate_chat_message(user_message):
            raise AppException(
                error_code="INVALID_MESSAGE",
                message="Message contains invalid characters or patterns",
                status_code=400
            )
        
        logger.info(f"💬 Chat message from {user_id}: '{user_message[:50]}...'")
        
        # Check LLM health
        is_healthy = await ollama_client.health_check()
        if not is_healthy:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "LLM_UNAVAILABLE", "message": "LLM service is not available"}
            )
        
        # Prepare system prompt
        system_prompt = """Eres un asistente de soporte técnico especializado en GLPI y farmacia.
Tu rol es ayudar a resolver tickets de soporte, responder preguntas sobre sistemas de farmacia, y proporcionar información técnica.
Siempre responde en español.
Sé conciso y profesional.
Si no conoces la respuesta, indica que necesitas más información."""
        
        # Generate response
        import time
        start_time = time.time()
        
        # Convert messages to format expected by Ollama
        messages_for_ollama = []
        for msg in chat_request.messages:
            messages_for_ollama.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Get response from Ollama
        response_text = await ollama_client.chat(
            messages=messages_for_ollama,
            model=chat_request.model,
            temperature=chat_request.temperature
        )
        
        execution_time = int((time.time() - start_time) * 1000)
        
        if not response_text:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "LLM_ERROR", "message": "Failed to generate response"}
            )
        
        # Create response
        assistant_message = ChatMessage(
            role="assistant",
            content=response_text
        )
        
        chat_response = ChatResponse(
            conversation_id=chat_request.conversation_id,
            message=assistant_message,
            tokens_used=0,  # TODO: calculate from response
            execution_time_ms=execution_time
        )
        
        logger.info(f"✅ Chat response generated in {execution_time}ms")
        
        return chat_response
        
    except AppException as e:
        logger.warning(f"⚠️ Chat validation error: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.error_code, "message": e.message, "request_id": request_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "CHAT_ERROR", "message": "Chat failed", "request_id": request_id}
        )


@router.post(
    "/message/stream",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        503: {"model": ErrorResponse, "description": "LLM service unavailable"}
    }
)
async def send_message_stream(
    request: Request,
    chat_request: ChatRequest
):
    """
    Send a message and stream LLM response.
    
    Returns Server-Sent Events (SSE) stream.
    """
    
    request_id = getattr(request.state, 'request_id', 'unknown')
    user_id = getattr(request.state, 'user_id', None)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "NOT_AUTHENTICATED", "message": "Authentication required"}
        )
    
    async def event_generator():
        try:
            # Get last user message
            user_message = None
            for msg in reversed(chat_request.messages):
                if msg.role == "user":
                    user_message = msg.content
                    break
            
            if not user_message:
                yield f"data: {json.dumps({'error': 'NO_USER_MESSAGE'})}\n\n"
                return
            
            # Validate
            if not validate_chat_message(user_message):
                yield f"data: {json.dumps({'error': 'INVALID_MESSAGE'})}\n\n"
                return
            
            logger.info(f"💬 Streaming chat from {user_id}: '{user_message[:50]}...'")
            
            # Check health
            is_healthy = await ollama_client.health_check()
            if not is_healthy:
                yield f"data: {json.dumps({'error': 'LLM_UNAVAILABLE'})}\n\n"
                return
            
            # System prompt
            system_prompt = """Eres un asistente de soporte técnico especializado en GLPI y farmacia.
Tu rol es ayudar a resolver tickets de soporte, responder preguntas sobre sistemas de farmacia, y proporcionar información técnica.
Siempre responde en español.
Sé conciso y profesional."""
            
            # Stream response
            import time
            start_time = time.time()
            tokens_count = 0
            
            messages_for_ollama = []
            for msg in chat_request.messages:
                messages_for_ollama.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            async for chunk in ollama_client.generate_stream(
                prompt=user_message,
                model=chat_request.model,
                system=system_prompt,
                temperature=chat_request.temperature
            ):
                if chunk:
                    tokens_count += len(chunk.split())
                    event = {"content": chunk, "tokens": tokens_count}
                    yield f"data: {json.dumps(event)}\n\n"
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Final message
            final_event = {
                "done": True,
                "execution_time_ms": execution_time,
                "total_tokens": tokens_count,
                "request_id": request_id
            }
            yield f"data: {json.dumps(final_event)}\n\n"
            
            logger.info(f"✅ Stream completed in {execution_time}ms")
            
        except Exception as e:
            logger.error(f"❌ Stream error: {str(e)}", exc_info=True)
            error_event = {"error": "STREAM_ERROR", "message": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Request-ID": request_id
        }
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    responses={
        503: {"model": ErrorResponse, "description": "LLM service unavailable"}
    }
)
async def chat_health():
    """
    Check LLM service health.
    """
    
    try:
        is_healthy = await ollama_client.health_check()
        
        if not is_healthy:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"status": "unhealthy", "model": "mistral"}
            )
        
        return HealthResponse(
            status="healthy",
            model="mistral",
            available_models=["mistral", "llama2", "neural-chat"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Health check error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "error": str(e)}
        )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"}
    }
)
async def delete_conversation(
    request: Request,
    conversation_id: str
):
    """
    Delete a conversation and its history.
    """
    
    user_id = getattr(request.state, 'user_id', None)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "NOT_AUTHENTICATED", "message": "Authentication required"}
        )
    
    try:
        logger.info(f"🗑️ Delete conversation {conversation_id} for {user_id}")
        
        # TODO: Delete from database
        
        logger.info(f"✅ Conversation deleted: {conversation_id}")
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Delete conversation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "DELETE_ERROR", "message": "Failed to delete conversation"}
        )
