from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId


class UserProfile(BaseModel):
    """User profile sub-document"""
    phone: Optional[str] = None
    company_name: Optional[str] = None
    address: Optional[str] = None
    profile_picture_url: Optional[str] = None
    company_logo_url: Optional[str] = None


class UserModel(BaseModel):
    """User document model for MongoDB"""
    id: Optional[str] = Field(None, alias="_id")
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    password_hash: str
    role: str  # "superadmin", "admin", "hr", "manager", "accountant"
    is_active: bool = True
    manager_id: Optional[str] = None  # For HR -> Manager linking
    created_by_admin_id: Optional[str] = None  # Track which admin created this user (for accountants, HR, managers)
    profile: Optional[UserProfile] = None
    
    # OTP fields for password reset
    otp_code: Optional[str] = None
    otp_expires_at: Optional[datetime] = None
    
    # Token management
    refresh_tokens: Optional[list] = []
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class AccountRequestModel(BaseModel):
    """Account request document model"""
    id: Optional[str] = Field(None, alias="_id")
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    requested_role: str = "hr"  # "hr" or "manager"
    message: Optional[str] = None
    status: str = "pending"  # "pending", "approved", "rejected"
    
    # Admin response
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
