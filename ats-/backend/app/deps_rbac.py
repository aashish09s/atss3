from fastapi import Depends, HTTPException, status
from app.deps import get_current_user
from typing import List


def require_roles(allowed_roles: List[str]):
    """Dependency factory for role-based access control"""
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker
