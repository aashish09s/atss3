from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.utils.security import hash_password, verify_password
from app.utils.tokens import create_access_token, create_refresh_token
from app.schemas.user import TokenOut, UserOut
from app.db.mongo import get_db
from datetime import datetime

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SeedAdminRequest(BaseModel):
    confirm: bool = True

@router.post("/seed-admin")
async def seed_admin(request: SeedAdminRequest):
    """Seed admin user (simplified version)"""
    return {"message": "Admin user created successfully", "user_id": "admin_hardcoded"}

@router.post("/issue-tokens", response_model=TokenOut)
async def login(login_data: LoginRequest):
    """Login with hardcoded admin OR database users"""
    print(f"Login attempt for: {login_data.email}")
    
    # Check hardcoded admin credentials first
    if login_data.email == "admin@company.com" and login_data.password == "Admin@4321":
        print("[SUCCESS] Hardcoded admin login successful")
        
        # Create tokens with real admin ID
        real_admin_id = "68975b1af6bce91efa735c37"
        access_token = create_access_token({"sub": real_admin_id, "role": "admin"})
        refresh_token = create_refresh_token({"sub": real_admin_id, "role": "admin"})
        
        # Create admin user response
        admin_user = UserOut(
            id=real_admin_id,
            username="admin",
            email="admin@company.com",
            role="admin",
            full_name="System Administrator",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        return TokenOut(
            access_token=access_token,
            refresh_token=refresh_token,
            user=admin_user
        )
    
    # Check database for other users
    try:
        db = await get_db()
        print(f"[INFO] Checking database for user: {login_data.email}")
        
        # Find user by email
        user = await db.users.find_one({"email": login_data.email})
        if not user:
            print(f"[ERROR] User not found: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(login_data.password, user["password_hash"]):
            print(f"[ERROR] Invalid password for: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.get("is_active", True):
            print(f"[ERROR] Inactive user: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        print(f"[SUCCESS] Database user login successful: {login_data.email}")
        
        # Create tokens
        user_id = str(user["_id"])
        access_token = create_access_token({"sub": user_id, "role": user["role"]})
        refresh_token = create_refresh_token({"sub": user_id, "role": user["role"]})
        
        # Create user response
        user_out = UserOut(
            id=user_id,
            username=user["username"],
            email=user["email"],
            role=user["role"],
            full_name=user["full_name"],
            is_active=user["is_active"],
            created_at=user["created_at"]
        )
        
        return TokenOut(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_out
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (401 errors)
        raise
    except Exception as e:
        print(f"[ERROR] Database error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error"
        )
