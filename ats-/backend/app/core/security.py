from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import JWTError, jwt
import secrets
import string
import hashlib
from app.core.config import settings
from app.core.logging import get_logger

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """Create a JWT refresh token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.refresh_token_expire_days
        )
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        
        # Check token type
        if payload.get("type") != token_type:
            return None
        
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        return user_id
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def generate_otp(length: int = 6) -> str:
    """Generate a random OTP."""
    digits = string.digits
    return ''.join(secrets.choice(digits) for _ in range(length))


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)


def generate_password(length: int = 12) -> str:
    """Generate a secure password."""
    # Ensure password has at least one of each type
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*")
    ]
    
    # Fill the rest with random characters
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))
    
    # Shuffle the password
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)


def create_api_key(user_id: str, prefix: str = "hpy") -> str:
    """Create an API key for a user."""
    # Create a unique identifier
    timestamp = str(int(datetime.utcnow().timestamp()))
    random_part = secrets.token_hex(16)
    
    # Combine user_id, timestamp, and random part
    key_data = f"{user_id}:{timestamp}:{random_part}"
    
    # Create hash
    key_hash = hashlib.sha256(key_data.encode()).hexdigest()[:32]
    
    return f"{prefix}_{key_hash}"


def verify_api_key(api_key: str) -> Optional[str]:
    """Verify an API key and return user_id if valid."""
    # This is a simple implementation
    # In production, you'd store API keys in database with expiration
    if not api_key or not api_key.startswith("hpy_"):
        return None
    
    # For now, just validate format
    parts = api_key.split("_")
    if len(parts) != 2 or len(parts[1]) != 32:
        return None
    
    # In production, lookup in database and return user_id
    return None


def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for storage."""
    return hashlib.sha256(data.encode()).hexdigest()


def is_strong_password(password: str) -> tuple[bool, list[str]]:
    """Check if password meets strength requirements."""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")
    
    # Check for common weak passwords
    weak_passwords = [
        "password", "123456", "password123", "admin", "letmein",
        "welcome", "monkey", "1234567890", "qwerty", "abc123"
    ]
    
    if password.lower() in weak_passwords:
        errors.append("Password is too common")
    
    return len(errors) == 0, errors


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    import re
    
    # Remove or replace dangerous characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    
    # Replace spaces with underscores
    filename = re.sub(r'\s+', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = f"{name[:250]}.{ext}" if ext else name[:255]
    
    return filename


def validate_file_type(filename: str, allowed_types: list[str]) -> bool:
    """Validate file type by extension."""
    if not filename:
        return False
    
    extension = filename.lower().split('.')[-1] if '.' in filename else ''
    return f".{extension}" in [t.lower() for t in allowed_types]


def generate_csrf_token() -> str:
    """Generate CSRF token."""
    return secrets.token_urlsafe(32)


def constant_time_compare(a: str, b: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    
    return result == 0
