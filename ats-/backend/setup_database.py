#!/usr/bin/env python3
"""
Database Setup Script for SynHireOne
This script will help you set up the database and create new admin credentials.
"""

import asyncio
import os
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import secrets
import string

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.security import hash_password

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_secure_password(length=12):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

async def setup_database(mongodb_uri):
    """Set up the database and create admin user"""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongodb_uri)
        
        # Test connection
        await client.admin.command('ping')
        print("✅ Connected to MongoDB successfully!")
        
        # Get database
        db = client.hirepy
        
        # Generate new admin credentials
        admin_email = "admin@hirepy.com"
        admin_password = generate_secure_password()
        
        print(f"\n🔐 New Admin Credentials:")
        print(f"   Email: {admin_email}")
        print(f"   Password: {admin_password}")
        print(f"\n⚠️  IMPORTANT: Save these credentials securely!")
        
        # Check if admin already exists
        existing_admin = await db.users.find_one({"email": admin_email})
        if existing_admin:
            print(f"\n⚠️  Admin user already exists. Updating password...")
            # Update existing admin password
            await db.users.update_one(
                {"email": admin_email},
                {
                    "$set": {
                        "password_hash": hash_password(admin_password),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            print("✅ Admin password updated successfully!")
        else:
            # Create new admin user
            admin_user = {
                "username": "admin",
                "email": admin_email,
                "password_hash": hash_password(admin_password),
                "role": "admin",
                "full_name": "System Administrator",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await db.users.insert_one(admin_user)
            print(f"✅ Admin user created successfully! ID: {result.inserted_id}")
        
        # Create indexes for better performance
        print("\n📊 Creating database indexes...")
        
        # Users collection indexes
        await db.users.create_index("email", unique=True)
        await db.users.create_index("username", unique=True)
        await db.users.create_index("role")
        await db.users.create_index("is_active")
        
        # Resumes collection indexes
        await db.resumes.create_index("uploaded_by")
        await db.resumes.create_index("created_at")
        await db.resumes.create_index("status")
        
        # Job descriptions collection indexes
        await db.job_descriptions.create_index("created_by")
        await db.job_descriptions.create_index("created_at")
        
        print("✅ Database indexes created successfully!")
        
        # Close connection
        client.close()
        
        return admin_email, admin_password
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return None, None

def main():
    print("🚀 SynHireOne Database Setup")
    print("=" * 40)
    
    # Get MongoDB URI from user
    mongodb_uri = input("\n📝 Enter your MongoDB Atlas connection string: ").strip()
    
    if not mongodb_uri:
        print("❌ MongoDB URI is required!")
        return
    
    # Validate URI format
    if not mongodb_uri.startswith("mongodb+srv://") and not mongodb_uri.startswith("mongodb://"):
        print("❌ Invalid MongoDB URI format!")
        return
    
    print(f"\n🔄 Setting up database...")
    
    # Run the setup
    admin_email, admin_password = asyncio.run(setup_database(mongodb_uri))
    
    if admin_email and admin_password:
        print("\n" + "=" * 50)
        print("🎉 SETUP COMPLETE!")
        print("=" * 50)
        print(f"📧 Admin Email: {admin_email}")
        print(f"🔑 Admin Password: {admin_password}")
        print("\n📋 Next Steps:")
        print("1. Update your .env file with the MongoDB URI")
        print("2. Start the backend server: python -m uvicorn app.main:app --reload")
        print("3. Start the frontend: npm run dev")
        print("4. Login at http://localhost:3000")
        print("\n⚠️  Remember to save these credentials securely!")
    else:
        print("\n❌ Setup failed. Please check your MongoDB URI and try again.")

if __name__ == "__main__":
    main()
