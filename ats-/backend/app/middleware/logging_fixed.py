import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
from datetime import datetime
from app.core.config import settings

# Configure logging
logger = logging.getLogger("api")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Fixed middleware for logging API requests and responses."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Use existing request ID if available, otherwise generate one
        if not hasattr(request.state, "request_id"):
            request_id = str(uuid.uuid4())
            request.state.request_id = request_id
        else:
            request_id = request.state.request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request (without consuming body)
        self.log_request_simple(request, request_id)
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log response
        self.log_response_simple(request, response, request_id, process_time)
        
        return response
    
    def log_request_simple(self, request: Request, request_id: str):
        """Log incoming request without consuming body."""
        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Get user info if available
        user_info = "anonymous"
        if hasattr(request.state, "user"):
            user = request.state.user
            user_info = f"{user.get('email', 'unknown')} ({user.get('role', 'unknown')})"
        
        # Log request details
        logger.info(
            f"REQUEST [{request_id}] "
            f"{request.method} {request.url.path} "
            f"from {client_ip} "
            f"user: {user_info} "
            f"agent: {user_agent[:50]}..."  # Truncate user agent
        )
        
        # Log query parameters if any
        if request.url.query:
            logger.debug(f"REQUEST [{request_id}] Query: {request.url.query}")
    
    def log_response_simple(self, request: Request, response: Response, request_id: str, process_time: float):
        """Log response without detailed analysis."""
        # Basic response logging
        status_code = response.status_code
        content_type = response.headers.get("content-type", "unknown")
        
        # Determine log level based on status code
        if status_code >= 500:
            log_level = logging.ERROR
        elif status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        logger.log(
            log_level,
            f"RESPONSE [{request_id}] "
            f"{status_code} {content_type} "
            f"in {process_time:.3f}s"
        )
        
        # Log errors for debugging
        if status_code >= 400:
            logger.warning(
                f"ERROR [{request_id}] "
                f"{request.method} {request.url.path} "
                f"returned {status_code}"
            )


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add request context to the request state."""
    
    async def dispatch(self, request: Request, call_next):
        # Add timestamp
        request.state.start_time = datetime.utcnow()
        
        # Add request ID if not already set
        if not hasattr(request.state, "request_id"):
            request.state.request_id = str(uuid.uuid4())
        
        response = await call_next(request)
        return response
