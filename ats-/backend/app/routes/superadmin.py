from fastapi import APIRouter, HTTPException, status, Depends
from app.db.mongo import get_db
from app.deps_rbac import require_roles
from app.schemas.admin import CreateUserRequest, UpdateUserRequest
from app.schemas.user import UserOut
from app.utils.security import hash_password
from bson import ObjectId
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/superadmin", tags=["Superadmin"])


class AdminCreateRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class AdminUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class SystemStatsResponse(BaseModel):
    total_admins: int
    total_hr_users: int
    total_managers: int
    total_users: int
    active_users: int
    inactive_users: int


@router.post("/admins", response_model=UserOut)
async def create_admin(
    admin_data: AdminCreateRequest,
    current_user: dict = Depends(require_roles(["superadmin"]))
):
    """Create a new admin user - Only Superadmin can create admins"""
    db = await get_db()
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": admin_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    
    # Check if username already exists
    existing_username = await db.users.find_one({"username": admin_data.username})
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken"
        )
    
    # Create new admin user
    new_admin = {
        "username": admin_data.username,
        "email": admin_data.email,
        "password_hash": hash_password(admin_data.password),
        "role": "admin",
        "full_name": admin_data.full_name,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": str(current_user["_id"])  # Track who created this admin
    }
    
    result = await db.users.insert_one(new_admin)
    
    # Return created user
    created_user = await db.users.find_one({"_id": result.inserted_id})
    return UserOut(
        id=str(created_user["_id"]),
        username=created_user["username"],
        email=created_user["email"],
        role=created_user["role"],
        full_name=created_user.get("full_name"),
        is_active=created_user["is_active"],
        created_at=created_user["created_at"],
        manager_id=created_user.get("manager_id")
    )


@router.get("/admins", response_model=List[UserOut])
async def list_admins(
    current_user: dict = Depends(require_roles(["superadmin"]))
):
    """List all admin users - Only Superadmin can view"""
    db = await get_db()
    
    users = await db.users.find({"role": "admin"}).sort("created_at", -1).to_list(None)
    
    return [
        UserOut(
            id=str(user["_id"]),
            username=user["username"],
            email=user["email"],
            role=user["role"],
            full_name=user.get("full_name"),
            is_active=user["is_active"],
            created_at=user["created_at"],
            manager_id=user.get("manager_id")
        )
        for user in users
    ]


@router.get("/admins/{admin_id}", response_model=UserOut)
async def get_admin(
    admin_id: str,
    current_user: dict = Depends(require_roles(["superadmin"]))
):
    """Get a specific admin user"""
    db = await get_db()
    
    try:
        user_object_id = ObjectId(admin_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid admin ID"
        )
    
    user = await db.users.find_one({"_id": user_object_id, "role": "admin"})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    return UserOut(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        role=user["role"],
        full_name=user.get("full_name"),
        is_active=user["is_active"],
        created_at=user["created_at"],
        manager_id=user.get("manager_id")
    )


@router.patch("/admins/{admin_id}", response_model=UserOut)
async def update_admin(
    admin_id: str,
    admin_data: AdminUpdateRequest,
    current_user: dict = Depends(require_roles(["superadmin"]))
):
    """Update an admin user - Only Superadmin can update admins"""
    db = await get_db()
    
    try:
        user_object_id = ObjectId(admin_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid admin ID"
        )
    
    # Check if admin exists
    user = await db.users.find_one({"_id": user_object_id, "role": "admin"})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    # Prevent self-deactivation
    if str(user["_id"]) == str(current_user["_id"]) and admin_data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Build update document
    update_data = {}
    if admin_data.username is not None:
        # Check if username is already taken by another user
        existing = await db.users.find_one({
            "username": admin_data.username,
            "_id": {"$ne": user_object_id}
        })
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken"
            )
        update_data["username"] = admin_data.username
    
    if admin_data.email is not None:
        # Check if email is already taken by another user
        existing = await db.users.find_one({
            "email": admin_data.email,
            "_id": {"$ne": user_object_id}
        })
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already taken"
            )
        update_data["email"] = admin_data.email
    
    if admin_data.password is not None:
        update_data["password_hash"] = hash_password(admin_data.password)
    
    if admin_data.full_name is not None:
        update_data["full_name"] = admin_data.full_name
    
    if admin_data.is_active is not None:
        update_data["is_active"] = admin_data.is_active
    
    update_data["updated_at"] = datetime.utcnow()
    
    # Update user
    await db.users.update_one(
        {"_id": user_object_id},
        {"$set": update_data}
    )
    
    # Return updated user
    updated_user = await db.users.find_one({"_id": user_object_id})
    return UserOut(
        id=str(updated_user["_id"]),
        username=updated_user["username"],
        email=updated_user["email"],
        role=updated_user["role"],
        full_name=updated_user.get("full_name"),
        is_active=updated_user["is_active"],
        created_at=updated_user["created_at"],
        manager_id=updated_user.get("manager_id")
    )


@router.delete("/admins/{admin_id}", response_model=Dict[str, Any])
async def delete_admin(
    admin_id: str,
    current_user: dict = Depends(require_roles(["superadmin"]))
):
    """Delete (deactivate) an admin user - Only Superadmin can delete admins"""
    db = await get_db()
    
    try:
        user_object_id = ObjectId(admin_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid admin ID"
        )
    
    # Prevent self-deletion
    if str(user_object_id) == str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Check if admin exists
    user = await db.users.find_one({"_id": user_object_id, "role": "admin"})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    # Soft delete (deactivate)
    await db.users.update_one(
        {"_id": user_object_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"success": True, "message": "Admin deactivated successfully"}


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    current_user: dict = Depends(require_roles(["superadmin"]))
):
    """Get system-wide statistics - Only Superadmin can view"""
    db = await get_db()
    
    total_admins = await db.users.count_documents({"role": "admin"})
    total_hr_users = await db.users.count_documents({"role": "hr"})
    total_managers = await db.users.count_documents({"role": "manager"})
    total_users = await db.users.count_documents({"role": {"$in": ["admin", "hr", "manager"]}})
    active_users = await db.users.count_documents({"is_active": True, "role": {"$in": ["admin", "hr", "manager"]}})
    inactive_users = await db.users.count_documents({"is_active": False, "role": {"$in": ["admin", "hr", "manager"]}})
    
    return SystemStatsResponse(
        total_admins=total_admins,
        total_hr_users=total_hr_users,
        total_managers=total_managers,
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users
    )


@router.get("/all-users", response_model=List[UserOut])
async def get_all_users(
    current_user: dict = Depends(require_roles(["superadmin"]))
):
    """Get all users (admins, HR, managers) - Only Superadmin can view all"""
    db = await get_db()
    
    users = await db.users.find({"role": {"$in": ["admin", "hr", "manager"]}}).sort("created_at", -1).to_list(None)
    
    return [
        UserOut(
            id=str(user["_id"]),
            username=user["username"],
            email=user["email"],
            role=user["role"],
            full_name=user.get("full_name"),
            is_active=user["is_active"],
            created_at=user["created_at"],
            manager_id=user.get("manager_id")
        )
        for user in users
    ]


@router.post("/seed-superadmin")
async def seed_superadmin():
    """Create initial superadmin user (no auth required for initial setup)"""
    db = await get_db()
    
    # Check if superadmin already exists
    existing = await db.users.find_one({"role": "superadmin", "is_active": True})
    if existing:
        return {
            "message": "Superadmin already exists",
            "email": existing.get("email"),
            "username": existing.get("username")
        }
    
    # Create superadmin user
    superadmin_user = {
        "username": "superadmin",
        "email": "superadmin@company.com",
        "password_hash": hash_password("SuperAdmin@123"),
        "role": "superadmin",
        "full_name": "Super Administrator",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(superadmin_user)
    
    return {
        "success": True,
        "message": "Superadmin user created successfully",
        "credentials": {
            "email": "superadmin@company.com",
            "password": "SuperAdmin@123",
            "username": "superadmin"
        },
        "user_id": str(result.inserted_id),
        "warning": "Please change the password after first login!"
    }

