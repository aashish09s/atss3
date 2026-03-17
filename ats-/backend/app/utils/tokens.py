from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings
import uuid
from typing import Optional


def create_access_token(data: dict) -> str:
    """Create access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({
        "exp": expire,
        "jti": str(uuid.uuid4()),  # Unique token ID
        "type": "access"
    })
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict) -> str:
    """Create refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({
        "exp": expire,
        "jti": str(uuid.uuid4()),  # Unique token ID
        "type": "refresh"
    })
    # Use refresh secret key if available, otherwise fall back to main secret
    secret_key = getattr(settings, 'jwt_refresh_secret_key', None) or settings.jwt_secret_key
    return jwt.encode(to_encode, secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate token"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.JWTError:
        return None
