import time
import asyncio
from typing import Dict, Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


class RateLimitStore:
    """In-memory rate limit store with sliding window."""
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.lock = asyncio.Lock()
    
    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed under rate limit."""
        async with self.lock:
            now = time.time()
            request_times = self.requests[key]
            
            # Remove old requests outside the window
            while request_times and request_times[0] <= now - window:
                request_times.popleft()
            
            # Check if under limit
            if len(request_times) < limit:
                request_times.append(now)
                return True
            
            return False
    
    async def get_reset_time(self, key: str, window: int) -> float:
        """Get time when rate limit resets."""
        async with self.lock:
            request_times = self.requests[key]
            if request_times:
                return request_times[0] + window
            return time.time()


# Global rate limit store
rate_limit_store = RateLimitStore()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with different limits per endpoint type."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Define rate limits: (requests, seconds)
        self.rate_limits = {
            # Authentication endpoints
            "/api/auth/issue-tokens": (5, 60),  # 5 requests per minute
            "/api/auth/forgot-password": (3, 300),  # 3 requests per 5 minutes
            "/api/auth/reset-password": (3, 300),  # 3 requests per 5 minutes
            
            # File upload endpoints
            "/api/hr/resumes/upload": (10, 60),  # 10 uploads per minute
            "/api/hr/resumes/bulk-upload": (5, 300),  # 5 bulk uploads per 5 minutes
            "/api/hr/resumes/bulk-upload-zip": (3, 300),  # 3 ZIP uploads per 5 minutes
            
            # AI-intensive endpoints
            "/api/hr/ats/score": (20, 60),  # 20 ATS scores per minute
            
            # Email endpoints
            "/api/hr/inbox/scan_now": (5, 300),  # 5 manual scans per 5 minutes
        }
        
        # Global rate limit for all other endpoints
        self.global_limit = (100, 60)  # 100 requests per minute per user
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)
        
        # Get client identifier
        client_id = await self.get_client_id(request)
        
        # Check rate limits
        if not await self.check_rate_limits(request, client_id):
            # Get reset time for headers
            window = self.get_rate_limit_window(request.url.path)
            reset_time = await rate_limit_store.get_reset_time(
                f"{client_id}:{request.url.path}", window
            )
            
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Reset": str(int(reset_time)),
                    "Retry-After": str(int(reset_time - time.time()))
                }
            )
        
        return await call_next(request)
    
    async def get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try to get user ID from authentication
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.get('id', 'unknown')}"
        
        # Fall back to IP address
        client_ip = "unknown"
        if request.client:
            client_ip = request.client.host
        
        return f"ip:{client_ip}"
    
    async def check_rate_limits(self, request: Request, client_id: str) -> bool:
        """Check if request is within rate limits."""
        path = request.url.path
        
        # Check specific endpoint rate limit
        if path in self.rate_limits:
            limit, window = self.rate_limits[path]
            key = f"{client_id}:{path}"
            
            if not await rate_limit_store.is_allowed(key, limit, window):
                logger.warning(f"Rate limit exceeded for {client_id} on {path}")
                return False
        
        # Check global rate limit
        global_limit, global_window = self.global_limit
        global_key = f"{client_id}:global"
        
        if not await rate_limit_store.is_allowed(global_key, global_limit, global_window):
            logger.warning(f"Global rate limit exceeded for {client_id}")
            return False
        
        return True
    
    def get_rate_limit_window(self, path: str) -> int:
        """Get rate limit window for a path."""
        if path in self.rate_limits:
            return self.rate_limits[path][1]
        return self.global_limit[1]


class FileUploadRateLimitMiddleware(BaseHTTPMiddleware):
    """Specific rate limiting for file uploads with size considerations."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.upload_limits = {
            "small_files": (20, 300),  # < 1MB: 20 files per 5 minutes
            "large_files": (5, 300),   # > 1MB: 5 files per 5 minutes
            "bulk_operations": (3, 600)  # Bulk: 3 operations per 10 minutes
        }
    
    async def dispatch(self, request: Request, call_next):
        # Only apply to upload endpoints
        if not any(upload_path in request.url.path for upload_path in 
                  ["/upload", "/bulk-upload"]):
            return await call_next(request)
        
        client_id = await self.get_client_id(request)
        
        # Determine file size category
        content_length = int(request.headers.get("content-length", "0"))
        
        if "bulk" in request.url.path:
            category = "bulk_operations"
        elif content_length > 1024 * 1024:  # 1MB
            category = "large_files"
        else:
            category = "small_files"
        
        # Check limit
        limit, window = self.upload_limits[category]
        key = f"{client_id}:upload:{category}"
        
        if not await rate_limit_store.is_allowed(key, limit, window):
            reset_time = await rate_limit_store.get_reset_time(key, window)
            raise HTTPException(
                status_code=429,
                detail=f"Upload rate limit exceeded for {category}",
                headers={
                    "X-RateLimit-Category": category,
                    "X-RateLimit-Reset": str(int(reset_time)),
                    "Retry-After": str(int(reset_time - time.time()))
                }
            )
        
        return await call_next(request)
    
    async def get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.get('id', 'unknown')}"
        
        client_ip = "unknown"
        if request.client:
            client_ip = request.client.host
        
        return f"ip:{client_ip}"
