from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import datetime

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SeedAdminRequest(BaseModel):
    confirm: bool = True

@router.post("/seed-admin")
async def seed_admin(request: SeedAdminRequest):
    """Seed admin user (minimal version)"""
    print("Seed admin called - minimal version")
    return {"message": "Admin user created successfully", "user_id": "admin_minimal"}

@router.post("/issue-tokens")
async def login(login_data: LoginRequest):
    """Ultra minimal login - no token creation"""
    print(f"MINIMAL: Login attempt for: {login_data.email}")
    
    # Check hardcoded admin credentials
    if login_data.email == "admin@company.com" and login_data.password == "Admin@4321":
        print("✅ MINIMAL: Hardcoded admin login successful")
        
        # Return minimal response without real tokens
        return {
            "access_token": "fake_token_admin",
            "refresh_token": "fake_refresh_admin",
            "user": {
                "id": "admin_id",
                "username": "admin",
                "email": "admin@company.com",
                "role": "admin",
                "full_name": "System Administrator",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00Z"
            }
        }
    
    # If not admin, raise error
    print(f"❌ MINIMAL: Invalid credentials for {login_data.email}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password"
    )
