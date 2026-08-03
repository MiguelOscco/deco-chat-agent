from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
import os
import redis
import secrets
import logging

from config import settings
from core.security import get_security_headers, get_cors_config
from core.exceptions import AppException, RateLimitExceededError
from core.logging import setup_logging
from middleware.rate_limiter import IPRateLimiter

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    logger.info("🚀 Application starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Server ID: {settings.SERVER_ID}")
    logger.info("✅ Application ready")
    
    yield
    
    logger.info("🛑 Application shutting down...")


def create_app() -> FastAPI:
    """Create FastAPI application."""
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/api/docs" if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT
        )
        redis_client.ping()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {str(e)}")
        redis_client = None
    
    # ============================================
    # MIDDLEWARE - SECURITY HEADERS (inline)
    # ============================================
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        for header_name, header_value in get_security_headers().items():
            response.headers[header_name] = header_value
        return response
    
    # ============================================
    # MIDDLEWARE - SECURITY CONTEXT (inline)
    # ============================================
    @app.middleware("http")
    async def add_security_context(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID", secrets.token_urlsafe(8))
        
        client_ip = request.client.host if request.client else "unknown"
        if "X-Forwarded-For" in request.headers:
            forwarded_ips = request.headers["X-Forwarded-For"].split(",")
            client_ip = forwarded_ips[0].strip()
        
        request.state.client_ip = client_ip
        request.state.user_id = None
        request.state.user_roles = []
        
        response = await call_next(request)
        return response
    
    # ============================================
    # MIDDLEWARE - CORS
    # ============================================
    cors_config = get_cors_config()
    app.add_middleware(CORSMiddleware, **cors_config)
    
    # ============================================
    # MIDDLEWARE - RATE LIMITING
    # ============================================
    if redis_client:
        ip_limiter = IPRateLimiter(redis_client)
        
        @app.middleware("http")
        async def rate_limit_middleware(request: Request, call_next):
            if "/health" in request.url.path or "/api/docs" in request.url.path or "/openapi.json" in request.url.path:
                return await call_next(request)
            
            try:
                allowed, retry_after = await ip_limiter.check(request.state.client_ip)
                if not allowed:
                    logger.warning(f"Rate limit exceeded: {request.state.client_ip}")
                    response = JSONResponse(status_code=429, content={"error": "RATE_LIMIT_EXCEEDED", "message": "Too many requests", "retry_after": retry_after})
                    if retry_after:
                        response.headers["Retry-After"] = str(retry_after)
                    return response
            except Exception as e:
                logger.error(f"Rate limiter error: {str(e)}")
            
            return await call_next(request)
    
    # ============================================
    # MIDDLEWARE - LOGGING
    # ============================================
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({round(process_time * 1000, 2)}ms)")
            
            return response
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            raise
    
    # ============================================
    # EXCEPTION HANDLERS
    # ============================================
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        request_id = getattr(request.state, 'request_id', 'unknown')
        return JSONResponse(status_code=exc.status_code, content={"error": exc.error_code, "message": exc.message, "details": exc.details, "request_id": request_id})
    
    @app.exception_handler(RateLimitExceededError)
    async def rate_limit_handler(request: Request, exc: RateLimitExceededError):
        request_id = getattr(request.state, 'request_id', 'unknown')
        response = JSONResponse(status_code=429, content={"error": exc.error_code, "message": exc.message, "request_id": request_id})
        if exc.details.get("retry_after"):
            response.headers["Retry-After"] = str(exc.details["retry_after"])
        return response
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, 'request_id', 'unknown')
        return JSONResponse(status_code=422, content={"error": "VALIDATION_ERROR", "message": "Request validation failed", "details": exc.errors(), "request_id": request_id})
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, 'request_id', 'unknown')
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred" if settings.ENVIRONMENT == "production" else str(exc), "request_id": request_id})
    
    # ============================================
    # HEALTH CHECK ENDPOINTS
    # ============================================
    
    @app.get("/health")
    async def health():
        return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION, "server_id": settings.SERVER_ID}
    
    @app.get("/health/ready")
    async def readiness():
        checks = {"database": "ok", "redis": "ok" if redis_client else "offline"}
        return JSONResponse(status_code=200 if redis_client else 503, content={"status": "ready" if redis_client else "not_ready", "checks": checks})
    
    @app.get("/health/live")
    async def liveness():
        return {"status": "alive", "server_id": settings.SERVER_ID}
    
    @app.get("/")
    async def root():
        return {"name": settings.APP_NAME, "version": settings.APP_VERSION}
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, workers=settings.WORKERS)

