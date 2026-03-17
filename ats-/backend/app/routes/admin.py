from fastapi import APIRouter, HTTPException, status, Depends
from app.db.mongo import get_db
from app.deps_rbac import require_roles
from app.schemas.admin import CreateUserRequest, UpdateUserRequest, LinkHRManagerRequest, AccountRequestCreate, AccountRequestStatusUpdate
from app.schemas.user import UserOut
from app.utils.security import hash_password
from bson import ObjectId
from datetime import datetime
from typing import List

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.post("/users", response_model=UserOut)
async def create_user(
    user_data: CreateUserRequest,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Create new HR, Manager, or Accountant user"""
    db = await get_db()
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    
    # Create new user
    new_user = {
        "username": user_data.username,
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "role": user_data.role,
        "full_name": user_data.full_name,
        "is_active": True,
        "created_by_admin_id": str(current_user["_id"]),  # Track which admin created this user
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(new_user)
    
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


@router.get("/users", response_model=List[UserOut])
async def get_users(
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Get all users (HR, Manager, and Accountant)"""
    db = await get_db()
    
    # Exclude admin and superadmin users from the list
    users = await db.users.find({"role": {"$in": ["hr", "manager", "accountant"]}}).to_list(None)
    
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


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: str,
    user_data: UpdateUserRequest,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Update user information"""
    db = await get_db()
    
    try:
        user_object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    # Check if user exists
    user = await db.users.find_one({"_id": user_object_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prepare update data
    update_data = {"updated_at": datetime.utcnow()}
    for field, value in user_data.dict(exclude_unset=True).items():
        if value is not None:
            update_data[field] = value
    
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


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Delete user"""
    db = await get_db()
    
    try:
        user_object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    # Check if user exists
    user = await db.users.find_one({"_id": user_object_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow deleting admin users
    if user["role"] == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete admin users"
        )
    
    # Delete user
    await db.users.delete_one({"_id": user_object_id})
    
    return {"message": "User deleted successfully"}


@router.post("/link")
async def link_hr_manager(
    link_data: LinkHRManagerRequest,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Link HR to Manager"""
    db = await get_db()
    
    try:
        hr_id = ObjectId(link_data.hr_id)
        manager_id = ObjectId(link_data.manager_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user IDs"
        )
    
    # Verify HR user exists and has HR role
    hr_user = await db.users.find_one({"_id": hr_id, "role": "hr"})
    if not hr_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HR user not found"
        )
    
    # Verify Manager user exists and has manager role
    manager_user = await db.users.find_one({"_id": manager_id, "role": "manager"})
    if not manager_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manager user not found"
        )
    
    # Link HR to Manager
    await db.users.update_one(
        {"_id": hr_id},
        {"$set": {"manager_id": str(manager_id), "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "HR linked to Manager successfully"}


@router.post("/account-requests")
async def create_account_request(request_data: AccountRequestCreate):
    """Create account request (from login form)"""
    db = await get_db()
    
    # Check if request already exists
    existing_request = await db.account_requests.find_one({"email": request_data.email})
    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account request already exists for this email"
        )
    
    # Create account request
    request_doc = {
        "name": request_data.name,
        "email": request_data.email,
        "phone": request_data.phone,
        "requested_role": request_data.requested_role,
        "message": request_data.message,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    await db.account_requests.insert_one(request_doc)
    
    return {"message": "Account request submitted successfully"}


@router.get("/account-requests")
async def get_account_requests(
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Get all account requests"""
    db = await get_db()
    
    requests = await db.account_requests.find().to_list(None)
    
    # Convert ObjectId to string
    for request in requests:
        request["id"] = str(request["_id"])
        del request["_id"]
    
    return requests


@router.patch("/account-requests/{request_id}")
async def update_account_request(
    request_id: str,
    status_update: AccountRequestStatusUpdate,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Update account request status"""
    db = await get_db()
    
    try:
        request_object_id = ObjectId(request_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request ID"
        )
    
    # Update request status
    result = await db.account_requests.update_one(
        {"_id": request_object_id},
        {"$set": {"status": status_update.status, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account request not found"
        )
    
    return {"message": "Account request updated successfully"}
