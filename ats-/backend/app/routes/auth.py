from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from app.db.mongo import get_db
from app.utils.security import hash_password, verify_password
from app.utils.tokens import create_access_token, create_refresh_token
from app.schemas.user import TokenOut, UserOut
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SeedAdminRequest(BaseModel):
    confirm: bool = True


@router.post("/seed-admin")
async def seed_admin(request: SeedAdminRequest):
    """Create hardcoded admin user for initial setup"""
    db = await get_db()
    
    # Check if admin already exists
    existing_admin = await db.users.find_one({"email": "admin@company.com"})
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Admin user already exists"
        )
    
    # Create admin user
    admin_user = {
        "username": "admin",
        "email": "admin@company.com",
        "password_hash": hash_password("Admin@4321"),
        "role": "admin",
        "full_name": "System Administrator",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(admin_user)
    return {"message": "Admin user created successfully", "user_id": str(result.inserted_id)}


@router.post("/test-login")
async def test_login(login_data: LoginRequest):
    """Test login endpoint for debugging"""
    try:
        db = await get_db()
        print(f"Database connected, looking for user: {login_data.email}")
        
        # Find user by email
        user = await db.users.find_one({"email": login_data.email})
        print(f"User found: {user is not None}")
        
        if not user:
            return {"error": "User not found", "email": login_data.email}
        
        password_valid = verify_password(login_data.password, user["password_hash"])
        print(f"Password valid: {password_valid}")
        
        return {
            "user_exists": True,
            "password_valid": password_valid,
            "user_active": user.get("is_active", False),
            "user_role": user.get("role", "unknown")
        }
    except Exception as e:
        print(f"Test login error: {e}")
        return {"error": str(e)}


@router.post("/issue-tokens", response_model=TokenOut)
async def login(login_data: LoginRequest):
    """User login and token issuance"""
    try:
        db = await get_db()
        print(f"Login attempt for: {login_data.email}")
        
        # Find user by email
        user = await db.users.find_one({"email": login_data.email})
        if not user or not verify_password(login_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )
    
    # Create tokens
    user_id = str(user["_id"])
    access_token = create_access_token({"sub": user_id, "role": user["role"]})
    refresh_token = create_refresh_token({"sub": user_id, "role": user["role"]})
    
    # Skip refresh token storage for now (was causing hangs)
    # TODO: Re-enable refresh token storage after debugging
    print("Refresh token storage disabled for testing")
    
    # Prepare user output
    user_out = UserOut(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        role=user["role"],
        full_name=user.get("full_name"),
        is_active=user["is_active"],
        created_at=user["created_at"],
        manager_id=user.get("manager_id")
    )
    
    return TokenOut(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_out
    )
