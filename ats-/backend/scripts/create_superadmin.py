"""
Script to create a superadmin user
Run this from the backend directory: python scripts/create_superadmin.py
"""
import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.mongo import get_client
from app.utils.security import hash_password


async def create_superadmin():
    """Create a superadmin user"""
    client = await get_client()
    db = client.get_database()
    
    # Check if superadmin already exists
    existing = await db.users.find_one({"email": "superadmin@company.com"})
    if existing:
        print("Superadmin user already exists!")
        print(f"Email: superadmin@company.com")
        print(f"Username: {existing.get('username', 'superadmin')}")
        return
    
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
    print("✅ Superadmin user created successfully!")
    print("\n" + "="*50)
    print("SUPERADMIN CREDENTIALS")
    print("="*50)
    print(f"Email: superadmin@company.com")
    print(f"Password: SuperAdmin@123")
    print(f"User ID: {result.inserted_id}")
    print("="*50)
    print("\n⚠️  Please change the password after first login!")


if __name__ == "__main__":
    asyncio.run(create_superadmin())

