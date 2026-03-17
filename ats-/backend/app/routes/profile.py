from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from pydantic import BaseModel, EmailStr
from app.db.mongo import get_db
from app.deps import get_current_user
from app.services.storage import storage_service
from bson import ObjectId
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/api/profile", tags=["User Profile"])


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    address: Optional[str] = None


class ProfileResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    address: Optional[str] = None
    profile_picture_url: Optional[str] = None
    company_logo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


@router.get("/", response_model=ProfileResponse)
async def get_profile(
    current_user: dict = Depends(get_current_user)
):
    """Get current user profile"""
    profile = current_user.get("profile", {})
    
    return ProfileResponse(
        id=str(current_user["_id"]),
        username=current_user["username"],
        email=current_user["email"],
        role=current_user["role"],
        full_name=current_user.get("full_name"),
        phone=profile.get("phone"),
        company_name=profile.get("company_name"),
        address=profile.get("address"),
        profile_picture_url=profile.get("profile_picture_url"),
        company_logo_url=profile.get("company_logo_url"),
        created_at=current_user["created_at"],
        updated_at=current_user.get("updated_at", current_user["created_at"])
    )


@router.patch("/", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    db = await get_db()
    
    # Prepare update data
    update_data = {"updated_at": datetime.utcnow()}
    profile_updates = {}
    
    if profile_data.full_name is not None:
        update_data["full_name"] = profile_data.full_name
    
    if profile_data.phone is not None:
        profile_updates["phone"] = profile_data.phone
        
    if profile_data.company_name is not None:
        profile_updates["company_name"] = profile_data.company_name
        
    if profile_data.address is not None:
        profile_updates["address"] = profile_data.address
    
    if profile_updates:
        # Get existing profile
        existing_profile = current_user.get("profile", {})
        existing_profile.update(profile_updates)
        update_data["profile"] = existing_profile
    
    # Update user in database
    await db.users.update_one(
        {"_id": ObjectId(str(current_user["_id"]))},
        {"$set": update_data}
    )
    
    # Get updated user
    updated_user = await db.users.find_one({"_id": ObjectId(str(current_user["_id"]))})
    profile = updated_user.get("profile", {})
    
    return ProfileResponse(
        id=str(updated_user["_id"]),
        username=updated_user["username"],
        email=updated_user["email"],
        role=updated_user["role"],
        full_name=updated_user.get("full_name"),
        phone=profile.get("phone"),
        company_name=profile.get("company_name"),
        address=profile.get("address"),
        profile_picture_url=profile.get("profile_picture_url"),
        company_logo_url=profile.get("company_logo_url"),
        created_at=updated_user["created_at"],
        updated_at=updated_user["updated_at"]
    )


@router.post("/upload-profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload profile picture"""
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed"
        )
    
    try:
        # Save profile picture
        file_url = await storage_service.save_file(file.file, f"profile_{current_user['_id']}_{file.filename}")
        
        # Update user profile
        db = await get_db()
        existing_profile = current_user.get("profile", {})
        existing_profile["profile_picture_url"] = file_url
        
        await db.users.update_one(
            {"_id": ObjectId(str(current_user["_id"]))},
            {
                "$set": {
                    "profile": existing_profile,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "message": "Profile picture uploaded successfully",
            "file_url": file_url
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload profile picture: {str(e)}"
        )


@router.post("/upload-company-logo")
async def upload_company_logo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload company logo"""
    # Only HR and Admin can upload company logo
    if current_user["role"] not in ["hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR and Admin can upload company logo"
        )
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed"
        )
    
    try:
        # Save company logo
        file_url = await storage_service.save_file(file.file, f"company_logo_{current_user['_id']}_{file.filename}")
        
        # Update user profile
        db = await get_db()
        existing_profile = current_user.get("profile", {})
        existing_profile["company_logo_url"] = file_url
        
        await db.users.update_one(
            {"_id": ObjectId(str(current_user["_id"]))},
            {
                "$set": {
                    "profile": existing_profile,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "message": "Company logo uploaded successfully",
            "file_url": file_url
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload company logo: {str(e)}"
        )
