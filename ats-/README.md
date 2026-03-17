# SynHireOne - AI-Powered Hiring Platform

A comprehensive hiring platform with AI-powered resume parsing, job description matching, ATS scoring, and automated email scanning.

## 🚀 Features

### 🔐 Authentication & User Management
- **Role-based Access Control**: Admin, HR, Manager roles
- **Secure JWT Authentication** with refresh tokens
- **OTP-based Password Reset** via email
- **No self-signup** - Admin-controlled user creation

### 👥 User Roles & Capabilities

#### Admin Portal
- Create/Edit/Delete HR & Manager accounts
- Link HR to Manager accounts
- View account requests from login form
- User management dashboard

#### HR Dashboard
- **Resume Upload**: Single & bulk upload (.pdf, .doc, .docx)
- **AI Resume Parsing**: Extract contact info, skills, experience, education
- **Job Description Management**: Upload & parse JDs with AI
- **ATS Scoring**: AI-powered resume-to-JD matching with scores
- **Email Integration**: Link Gmail/Outlook for automatic resume extraction
- **Resume Actions**: Download, share, send interview emails, generate offers
- **Status Tracking**: Submission → Shortlisting → Interview → Select/Reject → Offer → Onboarding

#### Manager Dashboard
- **Review Shared Resumes**: Approve/reject candidates
- **Real-time Sync**: WebSocket updates from HR actions
- **Interview Scheduling**: Send interview emails
- **Offer Generation**: Create customizable offer letters
- **Status Management**: Update candidate status

### 🤖 AI Integration (Gemini AI + spaCy Fallback)
- **Resume Parsing**: Extract structured data from documents
- **JD Analysis**: Parse job requirements and skills
- **ATS Scoring**: Intelligent resume-to-JD matching (0-100 scale)
- **Quality Suggestions**: Improvement recommendations
- **Fallback System**: spaCy NLP when Gemini is unavailable

### 📧 Email Automation
- **Inbox Linking**: Gmail, Outlook, custom IMAP support
- **Scheduled Scanning**: Daily/Weekly/Monthly
- **Attachment Extraction**: Automatic resume detection
- **Background Processing**: Non-blocking email processing

### 📄 Document Management
- **File Storage**: AWS S3 or local filesystem
- **Multiple Formats**: PDF, DOC, DOCX support
- **Secure Access**: Role-based file access control

### 🎨 Modern UI/UX
- **Responsive Design**: Mobile-first approach
- **Beautiful Animations**: Framer Motion powered
- **Modern Components**: Tailwind CSS + Heroicons
- **Real-time Updates**: WebSocket integration

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.10)
- **Database**: MongoDB Atlas
- **Authentication**: JWT + bcrypt
- **AI/ML**: Google Gemini AI, spaCy NLP
- **Background Jobs**: APScheduler, FastAPI BackgroundTasks
- **File Processing**: pdfminer, python-docx, antiword
- **Email**: SMTP, IMAP integration
- **Storage**: AWS S3 or local filesystem

### Frontend
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS
- **Icons**: Heroicons
- **Animations**: Framer Motion
- **HTTP Client**: Axios
- **Routing**: React Router DOM

## 📋 Prerequisites

- Python 3.10+
- Node.js 16+
- MongoDB Atlas account
- Google Gemini AI API key (optional)
- SMTP email account
- AWS S3 bucket (optional)

## 🚀 Quick Start

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Copy environment file
cp env.example .env

# Edit .env with your configurations
# - MongoDB Atlas URI
# - JWT secret key
# - Gemini API key
# - SMTP settings
# - AWS S3 credentials (optional)
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
python -m spacy download en_core_web_sm

# Install dependencies
npm install

# Copy environment file
cp env .env

# Edit .env with backend URL
VITE_API_BASE=http://localhost:8000
```

### 3. Configuration

#### MongoDB Atlas Setup
1. Create a MongoDB Atlas account
2. Create a new cluster
3. Get connection string
4. Update `MONGODB_URI` in `.env`

#### Gemini AI Setup (Optional)
1. Get API key from Google AI Studio
2. Update `GEMINI_API_KEY` in `.env`

#### SMTP Setup
1. Use Gmail App Password or SMTP provider
2. Update SMTP settings in `.env`

### 4. Run the Application

```bash
# Start backend (from backend directory)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (from frontend directory)
npm run dev
```

### 5. Initial Setup

1. Access the application: `http://localhost:3000`
2. Use admin credentials to login:
   - Email: `admin@company.com`
   - Password: `Admin@4321`
3. Create HR and Manager accounts
4. Link HR to Manager accounts

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Clone the repository
git clone <repository-url>
cd synhireone

# Create .env file in backend directory
cp backend/env.example backend/.env
# Edit backend/.env with your configurations

# Build and run
docker-compose up --build

# Access the application
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

### Individual Docker Builds

```bash
# Backend
cd backend
docker build -t synhireone-backend .
docker run -p 8000:8000 --env-file .env synhireone-backend

# Frontend
cd frontend
docker build -t synhireone-frontend .
docker run -p 3000:3000 synhireone-frontend
```

## 📁 Project Structure

```
synhireone/
├── backend/
│   ├── app/
│   │   ├── core/           # Configuration
│   │   ├── db/             # Database connection
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   ├── utils/          # Utilities
│   │   ├── schemas/        # Pydantic models
│   │   └── main.py         # FastAPI app
│   ├── requirements.txt
│   ├── Dockerfile
│   └── env.example
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── store/          # State management
│   │   ├── utils/          # Utilities
│   │   └── styles/         # Styling
│   ├── package.json
│   └── env
└── docker-compose.yml
```

## 🔧 API Documentation

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🎯 Key API Endpoints

### Authentication
- `POST /api/auth/seed-admin` - Create admin user
- `POST /api/auth/issue-tokens` - Login
- `POST /api/auth/forgot-password` - Reset password
- `POST /api/auth/refresh` - Refresh token

### Admin
- `GET /api/admin/users` - List users
- `POST /api/admin/users` - Create user
- `POST /api/admin/link` - Link HR to Manager

### HR
- `POST /api/hr/resumes/upload` - Upload resume
- `GET /api/hr/resumes/` - List resumes
- `POST /api/hr/jds/` - Create job description
- `POST /api/hr/ats/score` - Calculate ATS score
- `POST /api/hr/inbox/link_imap` - Link email inbox

### Manager
- `GET /api/manager/resumes/shared` - Get shared resumes
- `PATCH /api/hr/resume/status` - Update resume status

## 🔄 Workflow

1. **Admin** creates HR and Manager accounts
2. **Admin** links HR to Manager
3. **HR** uploads resumes (manual or email scanning)
4. **AI** parses resumes automatically
5. **HR** creates job descriptions
6. **AI** calculates ATS scores
7. **HR** shares relevant resumes with Manager
8. **Manager** reviews and approves/rejects candidates
9. **Both** can send interview emails and generate offers
10. **Real-time** updates sync between HR and Manager

## 🔒 Security Features

- JWT authentication with refresh tokens
- Password hashing with bcrypt
- Role-based access control (RBAC)
- File type validation
- Input sanitization
- CORS protection
- Encrypted credential storage

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 🚀 Production Deployment

### Environment Variables (Production)
```bash
# Backend (.env)
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/synhireone
JWT_SECRET_KEY=your-super-secure-secret-key
GEMINI_API_KEY=your-gemini-api-key
DEBUG=false
ENVIRONMENT=production

# Frontend
VITE_API_BASE=https://your-backend-domain.com
```

### Deployment Platforms
- **Backend**: Render, Railway, DigitalOcean, AWS ECS
- **Frontend**: Vercel, Netlify, Cloudflare Pages
- **Database**: MongoDB Atlas
- **Storage**: AWS S3, Cloudinary

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review API docs at `/docs`

## 🎉 Acknowledgments

- Google Gemini AI for intelligent parsing
- MongoDB Atlas for database hosting
- FastAPI for the excellent web framework
- React ecosystem for frontend development
- Open source community for amazing libraries

---

**Built with ❤️ for modern hiring needs**
