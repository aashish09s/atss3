from cryptography.fernet import Fernet
from app.core.config import settings
import base64
import os


def get_encryption_key() -> str:
    """Get encryption key as base64 string"""
    print(f"DEBUG: settings.encryption_key = '{settings.encryption_key}'")
    print(f"DEBUG: settings.encryption_key type = {type(settings.encryption_key)}")
    print(f"DEBUG: settings.encryption_key length = {len(settings.encryption_key) if settings.encryption_key else 'None'}")
    
    if settings.encryption_key:
        try:
            # Validate the key format
            decoded_key = base64.urlsafe_b64decode(settings.encryption_key)
            print(f"DEBUG: Successfully validated key, decoded length: {len(decoded_key)}")
            return settings.encryption_key
        except Exception as e:
            print(f"Failed to validate encryption key: {e}")
            print(f"Key value: '{settings.encryption_key}'")
            pass
    
    # Generate a key for development (NOT for production)
    if settings.environment == "development":
        print("WARNING: Generating encryption key for development. Do not use in production!")
        key = Fernet.generate_key()
        return key.decode()
    
    raise ValueError("ENCRYPTION_KEY not configured properly")


def encrypt_value(value: str) -> str:
    """Encrypt a string value"""
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(value.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_value(encrypted_value: str) -> str:
    """Decrypt a string value"""
    key = get_encryption_key()
    f = Fernet(key)
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
    decrypted = f.decrypt(encrypted_bytes)
    return decrypted.decode()
