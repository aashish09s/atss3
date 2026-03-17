from fastapi import APIRouter, Depends
from app.deps import get_current_user
from app.schemas.user import UserOut

router = APIRouter(prefix="/api/me", tags=["User Profile"])


@router.get("/", response_model=UserOut)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user)
):
    """Get current user profile"""
    return UserOut(
        id=str(current_user["_id"]),
        username=current_user["username"],
        email=current_user["email"],
        role=current_user["role"],
        full_name=current_user.get("full_name"),
        is_active=current_user["is_active"],
        created_at=current_user["created_at"],
        manager_id=current_user.get("manager_id")
    )
