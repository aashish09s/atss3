#!/usr/bin/env python3
"""
Environment Setup Script for SynHireOne
This script helps you create and configure the .env file.
"""

import os
import secrets
import string

def generate_jwt_secret():
    """Generate a secure JWT secret key"""
    return secrets.token_urlsafe(32)

def generate_encryption_key():
    """Generate a secure encryption key"""
    return secrets.token_urlsafe(32)

def create_env_file():
    """Create .env file with secure defaults"""
    
    print("🚀 SynHireOne Environment Setup")
    print("=" * 40)
    
    # Get MongoDB URI from user
    mongodb_uri = input("\n📝 Enter your MongoDB Atlas connection string: ").strip()
    
    if not mongodb_uri:
        print("❌ MongoDB URI is required!")
        return
    
    # Generate secure keys
    jwt_secret = generate_jwt_secret()
    jwt_refresh_secret = generate_jwt_secret()
    encryption_key = generate_encryption_key()
    secret_key = generate_jwt_secret()
    
    # Create .env content
    env_content = f"""# MongoDB Configuration
MONGODB_URI={mongodb_uri}

# JWT Configuration
JWT_SECRET_KEY={jwt_secret}
JWT_REFRESH_SECRET_KEY={jwt_refresh_secret}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Gemini AI Configuration (Optional)
GEMINI_API_KEY=AIzaSyBhN2Y4MSSg02n2SiGRbOnPUMg1EBnWw90

# Email Configuration (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=testv2vconnect@gmail.com
SMTP_PASSWORD=qakd alwu faiv vcrl
SMTP_FROM_EMAIL=testv2vconnect@gmail.com
SMTP_FROM_NAME=SynHireOne

# AWS S3 Configuration (Optional - if not set, uses local storage)
USE_S3=false
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=your-s3-bucket-name
AWS_REGION=us-east-1

# Local File Storage (used if S3 not configured)
LOCAL_UPLOAD_DIR=./uploads

# Encryption Key for sensitive data
ENCRYPTION_KEY={encryption_key}
SECRET_KEY={secret_key}

# spaCy Model
SPACY_MODEL=en_core_web_sm

# App Settings
DEBUG=true
ENVIRONMENT=development
"""
    
    # Write to .env file
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("\n✅ .env file created successfully!")
        print("\n📋 Next Steps:")
        print("1. Run: python setup_database.py")
        print("2. Start backend: python -m uvicorn app.main:app --reload")
        print("3. Start frontend: npm run dev")
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

if __name__ == "__main__":
    create_env_file()
