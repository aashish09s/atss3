from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
from pydantic import BaseModel, EmailStr
from app.db.mongo import get_db
from app.utils.security import hash_password
from app.utils.tokens import create_access_token, decode_token
from app.services.email_service import send_email
from bson import ObjectId
from datetime import datetime, timedelta
import random
import string

router = APIRouter(prefix="/api/auth", tags=["Authentication Extended"])


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


def generate_otp(length: int = 6) -> str:
    """Generate random OTP"""
    return ''.join(random.choices(string.digits, k=length))


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    """Send OTP for password reset"""
    db = await get_db()
    
    # Check if user exists
    user = await db.users.find_one({"email": request.email})
    if not user:
        # Don't reveal if email exists
        return {"message": "If email exists, OTP has been sent"}
    
    # Generate OTP
    otp = generate_otp()
    expire_at = datetime.utcnow() + timedelta(minutes=10)  # 10 minutes expiry
    
    # Store OTP in database
    await db.password_otps.insert_one({
        "email": request.email,
        "otp": otp,
        "expire_at": expire_at,
        "used": False,
        "created_at": datetime.utcnow()
    })
    
    # Send OTP email in background
    background_tasks.add_task(
        send_email,
        to_email=request.email,
        subject="Password Reset OTP",
        body=f"Your password reset OTP is: {otp}. Valid for 10 minutes."
    )
    
    return {"message": "If email exists, OTP has been sent"}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password using OTP"""
    db = await get_db()
    
    # Find valid OTP
    otp_record = await db.password_otps.find_one({
        "email": request.email,
        "otp": request.otp,
        "used": False,
        "expire_at": {"$gt": datetime.utcnow()}
    })
    
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    # Update user password
    new_password_hash = hash_password(request.new_password)
    await db.users.update_one(
        {"email": request.email},
        {
            "$set": {
                "password_hash": new_password_hash,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Mark OTP as used
    await db.password_otps.update_one(
        {"_id": otp_record["_id"]},
        {"$set": {"used": True}}
    )
    
    return {"message": "Password reset successfully"}


@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token"""
    db = await get_db()
    
    # Validate refresh token
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Check if refresh token exists in database
    stored_token = await db.refresh_tokens.find_one({
        "token": request.refresh_token,
        "user_id": payload.get("sub")
    })
    
    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    # Create new access token
    new_access_token = create_access_token({
        "sub": payload.get("sub"),
        "role": payload.get("role")
    })
    
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(request: LogoutRequest):
    """Logout user and revoke tokens"""
    db = await get_db()
    
    # Decode refresh token to get user_id
    payload = decode_token(request.refresh_token)
    if payload:
        # Remove refresh token
        await db.refresh_tokens.delete_one({
            "token": request.refresh_token,
            "user_id": payload.get("sub")
        })
    
    # Blacklist current access token (get from request headers)
    # Note: In a real implementation, you'd extract the JTI from the current request
    
    return {"message": "Logged out successfully"}
