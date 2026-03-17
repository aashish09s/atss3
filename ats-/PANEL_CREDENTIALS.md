# SynHireOne - Project Overview & Panel Credentials

## 📋 Project Overview

**SynHireOne** is an AI-powered hiring platform built with:
- **Backend**: FastAPI (Python 3.10+)
- **Frontend**: React 18 + Vite
- **Database**: MongoDB Atlas
- **AI Integration**: Google Gemini AI + spaCy NLP (fallback)

### Key Features:
- AI-powered resume parsing and job description matching
- ATS (Applicant Tracking System) scoring
- Automated email scanning for resumes
- Role-based access control (RBAC)
- Real-time WebSocket updates
- Document management with AWS S3 or local storage

---

## 🔐 Panel Credentials

### 1. **Admin Panel Credentials**
**Role**: Admin (System Administrator)
- **Email**: `admin@company.com`
- **Password**: `Admin@4321`
- **Access**: Full system access, can create/edit/delete HR & Manager accounts
- **Endpoint**: `POST /api/auth/seed-admin` (to create this user)

### 2. **Superadmin Panel Credentials**
**Role**: Superadmin (Highest level access)
- **Email**: `superadmin@company.com`
- **Password**: `SuperAdmin@123`
- **Access**: Full system access with superadmin privileges
- **Endpoint**: `POST /api/superadmin/seed-superadmin` (to create this user)
- **Script**: `python backend/scripts/create_superadmin.py`

### 3. **Database Setup Admin** (Alternative)
**Role**: Admin
- **Email**: `admin@hirepy.com`
- **Password**: *Generated randomly* (run `python backend/setup_database.py`)
- **Access**: Full admin access
- **Note**: This credential is generated when running the database setup script

---

## 👥 User Roles & Access Levels

### Role Hierarchy:
1. **Superadmin** - Highest level, full system control
2. **Admin** - System administrator, user management
3. **HR** - Resume management, job descriptions, ATS scoring
4. **Manager** - Review resumes, approve/reject candidates, interview scheduling
5. **Accountant** - Financial management (invoices, expenses, payments)

### Role Capabilities:

#### **Superadmin**
- All admin capabilities
- System-wide configuration
- User management across all roles
- Database management

#### **Admin**
- Create/Edit/Delete HR & Manager accounts
- Link HR to Manager accounts
- View account requests
- User management dashboard
- System statistics

#### **HR**
- Upload resumes (single & bulk)
- AI resume parsing
- Job description management
- ATS scoring (resume-to-JD matching)
- Email integration (Gmail/Outlook)
- Share resumes with managers
- Send interview emails
- Generate offer letters
- Status tracking

#### **Manager**
- Review shared resumes
- Approve/reject candidates
- Real-time sync via WebSocket
- Interview scheduling
- Offer generation
- Status management

#### **Accountant**
- Invoice management
- Expense tracking
- Payment processing
- Financial reporting

---

## 🚀 Quick Access Guide

### Initial Setup:
1. **Create Admin User**:
   ```bash
   # Via API endpoint
   POST http://localhost:8000/api/auth/seed-admin
   
   # Or via script
   python backend/scripts/create_superadmin.py
   ```

2. **Create Superadmin User**:
   ```bash
   # Via API endpoint
   POST http://localhost:8000/api/superadmin/seed-superadmin
   
   # Or via script
   python backend/scripts/create_superadmin.py
   ```

### Login URLs:
- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **API Documentation**: 
  - Swagger UI: `http://localhost:8000/docs`
  - ReDoc: `http://localhost:8000/redoc`

---

## 🔑 Default Credentials Summary

| Role | Email | Password | Access Level |
|------|-------|----------|-------------|
| **Admin** | `admin@company.com` | `Admin@4321` | Full Admin Access |
| **Superadmin** | `superadmin@company.com` | `SuperAdmin@123` | Highest Access |
| **Admin (DB Setup)** | `admin@hirepy.com` | *Generated* | Full Admin Access |

---

## ⚠️ Security Notes

1. **Change Default Passwords**: All default credentials should be changed after first login
2. **No Self-Signup**: Users can only be created by Admin/Superadmin
3. **JWT Authentication**: All API calls require valid JWT tokens
4. **Role-Based Access**: Each endpoint is protected by role requirements
5. **Password Hashing**: All passwords are hashed using bcrypt

---

## 📝 Additional Information

### Hardcoded Admin ID (for development):
- **User ID**: `68975b1af6bce91efa735c37`
- Used in some authentication routes for development/testing

### API Endpoints for User Creation:
- `POST /api/auth/seed-admin` - Create admin user
- `POST /api/superadmin/seed-superadmin` - Create superadmin user
- `POST /api/admin/users` - Create HR/Manager/Accountant users (requires admin auth)

### Database:
- **Database Name**: `hirepy` (as seen in setup_database.py)
- **Connection**: MongoDB Atlas (configured via `.env` file)

---

## 🛠️ Environment Setup

### Backend Environment Variables:
- `MONGODB_URI` - MongoDB connection string
- `JWT_SECRET_KEY` - Secret key for JWT tokens
- `GEMINI_API_KEY` - Google Gemini AI API key (optional)
- `SMTP_*` - Email server configuration
- `AWS_*` - AWS S3 credentials (optional)

### Frontend Environment Variables:
- `VITE_API_BASE` - Backend API URL (default: `http://localhost:8000`)

---

**⚠️ IMPORTANT**: These are default credentials. For production deployment, ensure all default passwords are changed and proper security measures are in place.

