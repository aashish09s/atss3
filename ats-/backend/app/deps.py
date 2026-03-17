from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.tokens import decode_token
from app.db.mongo import get_db
from bson import ObjectId
from typing import Optional

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
            
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        # Check if token is blacklisted
        db = await get_db()
        blacklisted = await db.blacklisted_tokens.find_one({"jti": payload.get("jti")})
        if blacklisted:
            raise credentials_exception
            
    except Exception:
        raise credentials_exception
    
    # Get user from database
    db = await get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if user is None:
        # Check if this is the hardcoded admin user
        if user_id == "68975b1af6bce91efa735c37":
            # Return hardcoded admin user data
            return {
                "_id": ObjectId(user_id),
                "username": "admin",
                "email": "admin@company.com",
                "role": "admin",
                "full_name": "System Administrator",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00Z"
            }
        raise credentials_exception
        
    return user
