import os
import sys
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.mongo import get_client
from app.services.email_scan_scheduler import start_email_scheduler, stop_email_scheduler
# from app.scheduler import configure_scheduler_from_db, load_scheduled_jobs, start_scheduler, shutdown_scheduler
from app.middleware.logging_fixed import LoggingMiddleware
from app.middleware.logging_fixed import RequestContextMiddleware
from app.middleware.rate_limiting import RateLimitMiddleware, FileUploadRateLimitMiddleware
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
    starlette_exception_handler
)

# Ensure stdout/stderr can handle Unicode logs on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Import all routers
from app.routes.health import router as health_router
from app.routes.auth_simple import router as auth_router
from app.routes.auth_extended import router as auth_ext_router
from app.routes.admin import router as admin_router
from app.routes.superadmin import router as superadmin_router
from app.routes.resumes import router as resumes_router
from app.routes.jd import router as jd_router
from app.routes.ats import router as ats_router
from app.routes.inbox import router as inbox_router
from app.routes.parsed_profiles import router as parsed_router
from app.routes.me import router as me_router
from app.routes.resume_actions import router as resume_actions_router
from app.routes.offer_templates import router as offer_templates_router
from app.routes.resumes_shared import router as resumes_shared_router
from app.routes.websocket import router as ws_router
from app.routes.profile import router as profile_router
from app.routes.statistics import router as stats_router
from app.routes.candidate_onboarding import router as candidate_onboarding_router
from app.routes.clients import router as clients_router
from app.routes.invoice import router as invoice_router
from app.routes.business_types import router as business_types_router
from app.routes.ledger import router as ledger_router
from app.routes.expenses import router as expenses_router
from app.routes.offer_signatures import include_offer_signature_routes
from app.routes.msa import hr_router as msa_hr_router, public_router as msa_public_router
from app.routes.assessment import router as assessment_router, public_router as assessment_public_router
# Temporarily disabled due to dependency conflicts
# from app.routes.resume_matching import router as resume_matching_router
# from app.routes.skills import router as skills_router

# Initialize logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="AI-Powered Hiring Platform",
    description="Complete hiring platform with AI-powered resume parsing and ATS scoring",
    version="1.0.0"
)

# Re-enable all middleware with fixed LoggingMiddleware
app.add_middleware(RequestContextMiddleware)  # SAFE
app.add_middleware(LoggingMiddleware)  # FIXED - using logging_fixed.py
app.add_middleware(RateLimitMiddleware)  # SAFE
app.add_middleware(FileUploadRateLimitMiddleware)  # SAFE

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "https://ats.trihdiconsulting.com",
        "http://ats.trihdiconsulting.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, starlette_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Create uploads directory if it doesn't exist
os.makedirs(settings.local_upload_dir, exist_ok=True)

# Mount static files for local file serving
app.mount("/uploads", StaticFiles(directory=settings.local_upload_dir), name="uploads")

# Include all routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(auth_ext_router)
app.include_router(admin_router)
app.include_router(superadmin_router)
app.include_router(resumes_router)
app.include_router(jd_router)
app.include_router(ats_router)
app.include_router(inbox_router)
app.include_router(parsed_router)
app.include_router(me_router)
app.include_router(resume_actions_router)
app.include_router(offer_templates_router)
app.include_router(resumes_shared_router)
app.include_router(ws_router)
app.include_router(profile_router)
app.include_router(stats_router)
app.include_router(candidate_onboarding_router, prefix="/api/hr/candidate-onboarding", tags=["candidate-onboarding"])
app.include_router(candidate_onboarding_router, prefix="/api/candidate-onboarding", tags=["candidate-onboarding"])
app.include_router(clients_router)
app.include_router(invoice_router)
app.include_router(business_types_router)
app.include_router(ledger_router)
app.include_router(expenses_router)
include_offer_signature_routes(app)
app.include_router(msa_hr_router)
app.include_router(msa_public_router)
app.include_router(assessment_router)
app.include_router(assessment_public_router)
# Temporarily disabled due to dependency conflicts
# app.include_router(resume_matching_router)
# app.include_router(skills_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database and scheduler on startup"""
    # Minimal startup - initialize MongoDB connection
    # Models will be loaded lazily on first use to avoid startup delays
    try:
        client = await get_client()
        if client:
            print("[SUCCESS] Connected to MongoDB")
        else:
            print("[WARNING] MongoDB connection failed, but continuing...")
    except Exception as e:
        print(f"[WARNING] MongoDB connection error (non-fatal): {e}")
    
    start_email_scheduler()
    print("[SUCCESS] Application startup completed")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await stop_email_scheduler()
    print("App shutdown complete")


# Root endpoint
@app.get("/")
async def root():
    return {"message": "AI-Powered Hiring Platform API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
